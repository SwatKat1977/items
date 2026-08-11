# Future work

Running list of known, deliberately-deferred items — not urgent, but worth
tracking so they don't get lost.

## Gateway: admin-only routes are not actually enforced

**This one is a security issue rather than a tidy-up**, and is listed first
for that reason.

**Where:** every route under `items_gateway/routes/web/`. There is no
authorisation check anywhere in the Gateway — no session validation, no
`is_administrator` check, no decorator. The invites blueprint states the
position outright:

```python
"""All routes are admin-only and must be enforced at this layer or by the
caller (the web portal, which checks ``is_administrator`` before calling)."""
```

It is currently the second of those: the Gateway trusts that the caller was
the web portal and that the portal checked.

**Problem:** in production the Gateway is the *only* externally visible
service — CMS and Identity bind to `127.0.0.1`. So the Gateway is the public
attack surface, and nothing about a request proves it came from the portal.
`POST /web/users` is therefore a publicly reachable, unauthenticated
account-creation endpoint: anyone who can reach the Gateway can create
themselves an account, including an administrator one, with a single `curl`
and without ever loading the portal. The same applies to every other
admin-only route (project deletion, custom field changes, invites, user
modification).

The portal's `require_administrator` decorator is real and works, but it
guards the *portal's* pages. Hiding a button is a user-experience decision,
not a security boundary — exactly the point already made in §9.1 of
`design_docs/user_roles_design.md`, which names the Gateway as the
enforcement point. That part was never implemented.

**Fix:** enforce at the Gateway. It already holds the session table
(`sessions.py`), and `SessionEntry` already carries `is_administrator`, so
the pieces exist — what is missing is a check on the request path. Broadly:

- Require session credentials on `/web/*` requests and validate them against
  the session store.
- Gate admin-only routes on the session's `is_administrator` flag.
- Decide how the portal passes the caller's session to the Gateway; it
  currently forwards none, so this is the main design question.

**Two routes must be explicitly exempted**, and this is easy to get wrong
with a blanket rule:

- `GET  /web/invites/token/<token>`
- `POST /web/accept_invite`

Both are deliberately unauthenticated, because somebody redeeming an
invitation has no account yet — the invite token authorises them instead.
This is documented in the invites blueprint docstring so it is not
"corrected" by mistake.

## CMS: `linked_projects` encoding is ambiguous

**Where:** `items_cms.repositories.testcase_custom_fields_repository`'s
`get_custom_field`/`get_all_fields`/`get_fields_for_project` queries build a
field's linked-projects list via
`GROUP_CONCAT(p.id || ':' || p.name)`, producing a single string like
`"1:Alpha,2:Beta"`.

**Problem:** there's no escaping. If a project name itself contains a
comma (e.g. `"Acme, Inc"`), the resulting string is genuinely ambiguous —
there's no way, from the string alone, to tell whether `"1:Acme, Inc,2:Beta"`
means projects `"Acme, Inc"` and `"Beta"`, or `"Acme"` and `"Inc,2:Beta"`.
No amount of clever parsing on the consuming side (web portal or otherwise)
can recover the correct answer once that ambiguity exists.

**Fix:** CMS needs to return `linked_projects` as structured data (a JSON
array of `{id, name}`, or a nested field in the response) instead of a
flattened, comma-joined string. Found while building the Case Fields admin
page in the web portal
(`admin_customisations_page_handler.py::_row_to_field`), which currently
does its best with the string it's given and documents the limitation in a
code comment there.

## Docker: SQLite DB can end up read-only inside containers

**Where:** `docker-compose.yml` bind-mounts each service's SQLite file
directly from the host, e.g.

```yaml
volumes:
  - "${ITEMS_DOCKER_IDENTITY_SVC_DB_FILE}:/usr/local/items/identity.db"
```

but the corresponding Dockerfiles (`docker/Dockerfile.identity_svc`,
`docker/Dockerfile.cms_svc` — likely all of them, same template) run the
service as a non-root `items` user:

```dockerfile
RUN addgroup -S items && adduser -S items -G items && \
    mkdir /usr/local/items && chown items:items /usr/local/items
...
USER items
```

**Problem:** `chown items:items` only applies to the image's baked-in
filesystem at build time. A bind-mounted file's ownership/permissions come
from the *host* at runtime and can overlay right past that — if the host
file's owner/mode doesn't happen to be writable by the container's `items`
UID, SQLite opens it read-only and every write fails. Hit in practice
during manual testing of `gateway_user_invite` against the identity
container on devbox.

**Fix (not attempted yet, needs a design call):** a few standard options,
roughly in order of how much they change the setup:
- Quick/fragile: just ensure the host DB file is `chmod`-ed writable by
  whatever UID the container's `items` user ends up with.
- Docker-native: switch from a host bind-mount to a named Docker volume for
  the DB file — Docker manages ownership for named volumes consistently
  from the container side, sidestepping host UID/GID mismatches entirely.
- Most robust: add an entrypoint script that runs as root, `chown`/`chmod`s
  the mounted DB path to match `items`, then drops privileges (`gosu`/
  `su-exec`) before exec-ing the actual service — works regardless of host
  UID, standard pattern for this exact class of problem, but adds
  complexity (an entrypoint script per service).

Affects `identity_svc` and `cms_svc` for certain (identical bind-mount +
non-root-user pattern in both); worth checking `web_portal_svc` and
`gateway_svc` too if either persists local state the same way.

## Gateway: health check doesn't verify *which* service answered

**Where:** `Service._identity_svc_health_check` /
`_check_cms_svc_status` in `items_gateway/service.py` — each just GETs
`<configured_url>/system/health` and validates the response body against
a JSON schema (`SCHEMA_IDENTITY_SVC_HEALTH_RESPONSE` /
`SCHEMA_CMS_SVC_HEALTH_RESPONSE`).

**Problem:** those two schemas are nearly identical (`status`,
`dependencies`, `uptime_seconds`, `version` — CMS's is a strict subset of
Identity's). Neither includes anything identifying which service actually
produced the response. If a misconfigured port/URL means the Gateway ends
up talking to the wrong backend (e.g. CMS reachable on the port meant for
Identity), the health check would validate successfully and the Gateway
would treat the wrong service as healthy and proceed - the mismatch would
only surface later, confusingly, when an actual request 404s or behaves
oddly (this is close to what caused the multi-message stale-container
confusion earlier in the invite work, just via a different mechanism).

**Fix:** add a required `service` field (a string, e.g. `"identity"` /
`"cms"` / `"gateway"` / `"web_portal"`) to the shared health-check schema
and response, and have the Gateway check it matches the service it thinks
it's talking to - fail the health check (rather than silently proceeding)
if it doesn't. Touches the shared schema
(`items/shared/interfaces/*/health.py`) and every service's own health
handler, not just the Gateway, so this is a coordinated change across all
services rather than a Gateway-only fix.

## Identity: invite consumption has a narrow TOCTOU race (low priority)

**Where:** `InviteManagementService.uninvite()` (also used as the "consume"
step inside `accept_invite`'s flow) does a `SELECT` (existence check via
`get_invite_by_email`) followed by a separate `UPDATE` (soft-expire) as two
sequential DB round trips, rather than one atomic statement.

**Problem:** two concurrent callers submitting the same token/email within
the few-millisecond gap between the SELECT and the UPDATE could both pass
the existence check before either UPDATE lands, both believing they
successfully consumed the invite. In practice this requires the exact same
token submitted twice near-simultaneously (a double-click, a client retry,
or deliberate racing) - a narrow window, and even if hit, the failure is
already safe: `create_user`'s email-uniqueness constraint means the second
`accept_invite` attempt fails at account creation regardless, so there is no
duplicate account and no takeover - just a confusing "please ask for a new
invite" error for the losing request.

**Fix (not attempted - low priority, P4/P5):** no framework change needed -
`SqliteInterface.run_query(..., commit=True)` already returns
`cursor.rowcount`. Change `InviteRepository.uninvite()` to return that
rowcount instead of discarding it, and change
`InviteManagementService.uninvite()` to drop the separate
`get_invite_by_email()` pre-check, performing the atomic
`UPDATE ... WHERE is_expired = 0` directly and branching SUCCESS vs.
NO_PENDING_INVITE on whether the rowcount was 1 or 0. The Gateway's
`_consume_invite` (in `accept_invite_handler.py`) needs no changes - it
already just checks for a 200 status. Roughly a 30-45 minute change
including light test updates to `test_da_invite_data_access_layer.py` and
`test_services_invite_management_service.py`.

## Gateway: no way to configure "no mail server"

**Where:** `Service.initialise()` in `items_gateway/service.py` always
constructs a `SmtpEmailService` from `self._config.smtp_*` and injects it
into every route, regardless of whether SMTP has actually been configured.

**Problem:** an instance that hasn't set up a mail server (a fresh
install, a dev environment, someone who just doesn't want email invites)
still gets a live `SmtpEmailService` wired in. Invite create/resend/accept
will attempt to connect and send through it - not skip it - and the
attempt will simply fail against empty/default SMTP settings rather than
being recognised as "email is deliberately off".

**Fix:** add an explicit "no mail server" config state (e.g. `smtp_host`
unset/empty, or a dedicated `SMTP_ENABLED=0` flag) and branch on it in
`Service.initialise()`: when unset, skip constructing `SmtpEmailService`
and pass `email_service=None` instead. The invite handlers already treat
`email_service: EmailService | None = None` as a valid, no-op case
(`send_invite_email`/`send_welcome_email` both no-op on `None`), so the
call sites need no changes - this is purely a startup-wiring change plus a
config flag.

## Identity: no soft-delete for users (admin)

**Where:** `items_identity` has no delete path for users at all today -
only create, list/get, modify, reset/change password
(`services/user_management_service.py`, `routes/users/`). Projects already
have a soft-delete-plus-background-purge convention
(`is_deleted`/background expiry task); users have no equivalent.

**Problem:** an administrator who invites/creates the wrong person, or
needs to offboard someone, has no way to remove their account short of
direct database access. Given the existing soft-delete convention
elsewhere in the codebase, a hard delete would also be inconsistent with
how the rest of the system handles removal.

**Fix:** add a soft-delete column to the user table (mirroring the
project/invite `is_deleted`/`is_expired` pattern), a repository method,
a service method enforcing whatever business rules apply (e.g. can an
administrator delete themselves? the last remaining administrator?), a
Gateway route, and an admin-page action on Users & Roles. Sizeable enough
to be its own small PR rather than a squeeze-in - candidate for 0.3.0.
