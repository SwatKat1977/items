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
