# Future work

Running list of known, deliberately-deferred items — not urgent, but worth
tracking so they don't get lost.

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

## Identity: no erasure path for users (deferred, not a gap)

**Where:** `items_identity` has no delete or anonymise path for users
today - only create, list/get, modify, reset/change password
(`services/user_management_service.py`, `routes/users/`).

**This entry originally proposed a soft-delete column for users, mirroring
the project/invite `is_deleted`/`is_expired` pattern.** That turned out to
be the wrong shape: `user_roles_design.md` §10.6 ("User accounts are
deactivated, never deleted") already made a considered decision against
any delete-like concept for users, for reasons that still hold - every
reference to a user outside `identity.db` is cross-database and
unenforced (no foreign key), so removing a row wouldn't remove the
references, it would just make them dangle silently. Deactivation
(`account_status = DISABLED`) already covers "this person shouldn't have
access any more" end to end (Identity, Gateway, and the Portal toggle in
`portal_admin_access_tab`), and was never a placeholder waiting for a
real delete to arrive later.

**Problem:** an administrator who invites/creates the wrong person, or
needs to offboard someone, has no way to remove their account short of
direct database access. Given the existing soft-delete convention
elsewhere in the codebase, a hard delete would also be inconsistent with
how the rest of the system handles removal

**If a genuine need appears** - a right-to-erasure request being the
likely trigger - the design doc's answer is **anonymise in place**: keep
the `id`, overwrite the personal data (email becomes
`deleted-user-<id>@invalid`, names become "Deleted User"), revoke
credentials. That preserves referential integrity automatically (the `id`
never disappears) and keeps history attributable, unlike a shared
tombstone account. Not scoped further than that - deliberately deferred,
no timeline.

## Gateway: deactivating a user does not touch their existing session

**Where:** `Sessions` (`items_gateway/sessions.py`) is a pure in-memory
`email_address -> SessionEntry` map. `ValidateSessionHandler.validate_session`
only checks that an entry exists and the token matches - it never asks
Identity whether the account is still active. `SessionEntry.session_expiry`
is declared but not read anywhere either, so today nothing ever
invalidates a session except an explicit logout or a server restart.

**Problem:** the design doc (`user_roles_design.md` §5.3.3) already commits
to different behaviour: "existing sessions are invalidated at next
validate call". That was never built. An administrator who deactivates a
user (the "Active" toggle added in `portal_admin_access_tab`) only blocks
*future* logins - anyone with an already-open session keeps working
normally until they happen to log out themselves.

**Fix:** proactive delete, not a lazy per-request check. A lazy check (ask
Identity "is this account still active" on every `validate_session` call)
would add a permanent Gateway->Identity round trip to every single
authenticated request, forever, to guard against something rare and
deliberate - a bad trade. Proactive delete costs nothing extra on the hot
path and can piggyback on a call that already happens:

- **Identity**: include `email_address` in the success response of
  `PATCH /users/<id>` (`modify_user_handler.py` /
  `UserManagementService.update_user`) - it doesn't today.
- **Gateway**: `ModifyUserHandler.modify_user` already sees both the
  outgoing request body (so it knows if `account_status` was set to `0`)
  and Identity's response for the same call. On a 200 with
  `account_status == 0` in the request, call
  `sessions.delete_session(response.body["email_address"])`. No new
  network call anywhere.

Small and well-defined - no open design questions - but deliberately not
folded into `portal_admin_access_tab` (which only added the UI checkbox)
or decided yet against the gateway admin-route enforcement piece. Both
touch Gateway session/authorization code, so worth doing whichever one
lands first.

## Web Portal: session cookies are missing HttpOnly and SameSite

**Where:** `login_post_page_handler.py:114-115` -
`login_response.set_cookie(self.COOKIE_USER, user_email)` and
`.set_cookie(self.COOKIE_TOKEN, response.body.get("token"))`, both called
with no extra arguments. Quart's `set_cookie` defaults every
security-relevant flag off: `secure=False`, `httponly=False`,
`samesite=None`.

**Problem:** the session token itself is fine - generated as
`uuid.uuid4().hex` (`new_session_password_handler.py:122`), 122 bits from
`os.urandom`, not predictable. The cookie carrying it isn't locked down
though:

- No `HttpOnly` - JavaScript can read `items_token` via `document.cookie`.
  Any XSS anywhere on the site hands over the session token outright.
- No explicit `SameSite` - left to browser default rather than a
  deliberate choice.

**Fix:** add `httponly=True` and `samesite="Lax"` to both `set_cookie`
calls. Neither depends on HTTPS or any environment detection - safe to do
immediately, independent of everything else here. (The third flag,
`Secure`, is deliberately not part of this item - see the HTTPS entry
below.)

## Move to HTTPS

**Where:** deployment-wide. Flagged while discussing session cookie
hardening (above) - `Secure` can't be set on the session cookies until
there's always a TLS connection to require it over, and setting it
unconditionally today would silently break login on any current non-HTTPS
setup (including local dev on `http://localhost`).

**Problem:** scope is genuinely unknown right now - "possibly massive" per
the conversation that raised it. At minimum it touches: the `Secure`
cookie flag (blocked on this), any hardcoded `http://` URLs, CORS/cookie
`SameSite` interactions once `Secure` is involved, and cert/reverse-proxy
setup for however this actually gets deployed. Likely more once someone
sits down and lists it properly.

**Fix:** not scoped yet - deliberately just a placeholder so it isn't
lost. Needs its own focused pass to turn "possibly massive" into an actual
list before any code changes. Do this before making `Secure` conditional
on an environment flag (above) - guessing at the environment-detection
shape now risks redoing it once the real migration is scoped.

## Gateway: project membership/role changes don't reach an existing session either

**Where:** `Sessions`/`SessionEntry` (`items_gateway/sessions.py`) now
caches `project_ids` (and `is_administrator`) at login only - see
`gateway_membership_enforcement`. Same root cause as "deactivating a user
does not touch their existing session" above: nothing proactively updates
or clears a live session when an admin changes something that session's
cached data claims about the user.

**Problem:** an admin adding/removing a user's project membership,
changing the role on a membership, or editing a role's own permission
grid, has no effect on anyone already logged in until they happen to log
out and back in. Seen firsthand while manually verifying
`gateway_membership_enforcement` - a project granted via the Portal
didn't show up for the affected user until a fresh login, which is
correct-per-design but easy to mistake for a bug (and did, mid-session).

**Fix:** same shape as the deactivation fix already designed above -
proactive update on the write, not a per-request check (same "don't add
a permanent round trip to every authenticated request" reasoning
applies). Two sub-cases:

- **Membership add/remove/role-change** (`AddUserProjectHandler`,
  `ModifyUserProjectHandler`, `RemoveUserProjectHandler` in
  `routes/web/users/`) - a 1:1 lookup, same shape as the deactivation
  fix: the affected user's email is already known to the handler: either
  delete their session (forces re-login) or live-patch
  `SessionEntry.project_ids` in place (seamless, no logout needed).
- **Role permission grid changes / role deletion**
  (`routes/web/roles/`) - not 1:1. A role's permissions changing (or the
  role being deleted, clearing affected memberships to "Unassigned")
  potentially affects every session belonging to a user who holds that
  role on *any* project. `Sessions` isn't indexed by role, so this means
  scanning all active sessions rather than a single lookup - trivial
  cost given it's an in-memory dict, just worth naming as the one part
  of this fix that isn't a direct lookup.

Roughly sized comparably to or smaller than `gateway_membership_enforcement`
itself, since `Sessions`/`SessionEntry` already carry the data needed -
this is about *reacting* to writes that already happen, not adding new
state.

## Web Portal: Projects tab's per-row Save button is easy to miss

**Where:** `instance_admin_modify_user.html`'s Projects tab - the
per-membership role `<select>` has its own small `<form>` with a
`type="submit"` button showing only a checkmark icon
(`<i class="bi bi-check-lg">`), with a `title="Save role"` hover tooltip
as the only affordance.

**Problem:** found during manual verification of
`gateway_membership_enforcement` - a role change appeared not to be
saving at all, and the actual cause was the icon-only Save button not
being clicked (attention going to the page's main "Save User" button
instead, which doesn't touch project/role data). The code was correct
throughout; the affordance wasn't clear enough. Same page's "Save
User"/"Cancel" buttons both already pair an icon with visible text -
this one button doesn't follow that existing convention.

**Fix:** give the row's Save button visible "Save" text too, matching
the convention already used elsewhere on the same page. Small,
low-risk, Portal-template-only change - deliberately not bundled into
the Gateway-only `gateway_membership_enforcement` branch it was found
on; wants its own tiny branch.

## Identity: password hashing blocks the event loop

**Where:** `user_management_service.py` - `PasswordHasher()` uses
library defaults (Argon2id), and `self._ph.hash(...)` (lines ~263, 380,
435 - registration, self-service change, admin reset) is called directly
inside `async def` methods, not offloaded via `asyncio.to_thread`.

**Problem:** found while diagnosing spurious 504s on password reset/user
creation during `gateway_membership_enforcement` verification (fixed
there by widening `RestClient` timeouts on the affected calls - see that
branch's `changes.md`). The timeout bump treats the symptom; this is the
actual mechanism: Argon2 is deliberately expensive by design, and running
it synchronously means it blocks Identity's *entire* event loop for its
full duration - not just the one request doing the hashing, but every
other concurrent request Identity is handling at that moment too. On a
loaded dev machine this is what pushed individual calls past the old 2s
default timeout in the first place.

**Fix:** wrap each `self._ph.hash(...)` call in `asyncio.to_thread(...)`
so the hash runs on a worker thread instead of blocking the loop. Doesn't
make hashing faster (that's a separate question of whether the default
cost parameters are appropriate for target hardware) - just stops one
password operation from stalling every other concurrent request while it
runs. Bigger and more careful than the timeout bump: touches core
authentication code in three places, wants proper test coverage of the
threaded path, not something to do under the time pressure that prompted
the timeout fix instead.
