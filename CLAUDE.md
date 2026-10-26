# CLAUDE.md

Working notes for Claude Code on **ITEMS** (Integrated Test Management System).
Human-facing rules live in `CONTRIBUTING.md`; this file adds the practical
detail. Keep it short and correct - update it when a rule changes.

## Layout

| Path | What |
|---|---|
| `items/services/items_cms` | CMS: owns projects, folders, test cases, case types, custom fields |
| `items/services/items_identity` | Identity: users, roles, invites, project membership |
| `items/services/items_gateway` | Gateway: the only service the Portal talks to; authentication and authorisation |
| `items/services/items_web_portal` | Web Portal: server-rendered pages (Quart + Jinja) |
| `items/shared` | Code and the version shared by every service |
| `items/tool_cms_db_builder` | Builds a fresh CMS database |
| `unit_tests/<service>` | Tests, one folder per service, each with an explicit `main.py` entry point |
| `automation` | API tests (pytest) that run against a running stack; see `automation/README.md` |
| `design_docs` | API contracts and design decisions (see below) |
| `postman` | Postman collection (CMS, Identity, Gateway) |
| `databases/*.LATEST.db` | The checked-in database files |

## Branches and pull requests

- **One service per branch and PR.** Title prefix is the service:
  `[CMS] ...`, `[Gateway] ...`, `[Portal] ...`. Features span services as a
  series of branches in dependency order: CMS/Identity, then Gateway, then
  Portal. See `CONTRIBUTING.md`.
- **Keep changes small and deliberate.** Prefer a short series of verifiable
  branches over one large diff. If something is blocked on an undecided
  design question, raise it and defer; do not guess.
- **Bump the version when a PR changes something that ships:** service code,
  templates or static files, the shared package, or the database builder.
  Increment the `PRE_RELEASE` counter in `items/shared/__init__.py` by one
  (for example `"alpha4"` to `"alpha5"`); one shared version covers every
  service. **Don't bump** for docs, the Postman collection, automation, CI
  workflows or test-only changes. If in doubt, bump. A fix to a service that
  the automation uncovers is a service change, so it bumps as usual.
- **Choose the series when it starts:** a fix-only release is a patch
  (`0.5.1-alpha1`), a feature release a minor (`0.6.0-alpha1`). The alpha
  counter is mechanical; which series you are in is the judgement call.
- The maintainer commits and pushes. Prepare the change and a PR title and
  description; do not commit or push unless asked.

## Quality gates (CI enforces all of these)

For the service you changed:

- **All tests pass and coverage is 100%.**
- **pylint scores 10.00.** Read the messages, not just the score: they are
  printed above the rating line, and the score can still read 10.00 while
  `--fail-under` fails on a message.
- New test classes must be **registered in that service's `main.py`**; the
  entry points import classes explicitly, so an unregistered class silently
  does not run in CI.

Run from the repo root with the venv's Python. On Windows the `PYTHONPATH`
separator is `;` (CI on Linux uses `:`).

| Service | `PYTHONPATH` | Test file / `-m` | Coverage config |
|---|---|---|---|
| CMS | `unit_tests/items_cms` | `unit_tests/items_cms/main.py` | `.github/workflows/.coveragerc_cms_svc` |
| Gateway | `unit_tests/items_gateway` | `unit_tests/items_gateway/main.py` | `.github/workflows/.coveragerc_gateway_svc` |
| Identity | `.;items/services/items_identity;unit_tests/items_identity` | `unit_tests/items_identity/main.py` | `.github/workflows/.coveragerc_identity_svc` |
| Portal | `items/shared;unit_tests/web_portal_svc;.` | `unit_tests/web_portal_svc/main.py` | `.github/workflows/.coveragerc_web_portal_svc` |
| Shared | `items/shared;unit_tests/shared;.` | `unit_tests/shared/main.py` | `.github/workflows/.coveragerc_shared` |

```bash
PYTHONPATH="<paths>" venv/Scripts/python -m coverage run --rcfile=<coveragerc> -m unittest <main.py>
venv/Scripts/python -m coverage report --rcfile=<coveragerc> --fail-under=100
venv/Scripts/python -m pylint --fail-under=10.0 items/services/items_<service>
```

## Automation tests

`automation/` holds API-level tests that send real requests to a **running**
stack and check the responses. They complement the unit tests: unit tests
prove each service alone, these prove the services work together.

- `automation/api_core` is a small **generic** library (send a request, check
  the reply). It **never imports from `items`**; neither do the tests, which
  are black-box and use literal URLs and bodies.
- Tests and fixtures are `async def` under `pytest-asyncio`. Tests that need a
  stack are marked `stack` and left out of a plain run; run them with
  `pytest -m stack` and `ITEMS_ADMIN_PASSWORD` set. Full instructions are in
  `automation/README.md`.
- A feature is not done until the cross-service behaviour it adds has an
  automated check.

## Architecture rules

- **The Gateway is the authorisation point.** CMS and Identity are
  permission-agnostic and trust their caller; they only do integrity checks
  (for example confirming a test case belongs to the stated `project_id`). Do
  not write tests that claim to verify authorisation by calling CMS directly.
  Details: `design_docs/user_roles_design.md` section 9.
- **Layering in the CMS:** repository (SQL) -> service (rules, returns a
  `ServiceResult`) -> route handler (HTTP) -> Blueprint factory. Database
  exceptions are caught in the service, never in handlers.
- **Gateway handlers are thin forwarders.** Prefer returning the upstream
  status and body unchanged (the "pass-through" shape) and let the owning
  service validate. Access is set by a decorator on the route in the
  Blueprint: `require_administrator`, `require_session`,
  `require_project_member`, or `require_project_permission(injections, area,
  action)` for the per-area role grid. Write handlers must reject a missing
  `project_id` themselves (the member decorator skips the check when it
  cannot find one).
- **Permission checks ask Identity every time and fail closed.**
  `require_project_permission` calls Identity on each request (nothing is
  cached or copied into the session), so a change to a role, membership or
  account applies on the next request. It never skips the check: a missing or
  malformed `project_id` is a 400, and only a real boolean `true` from
  Identity lets a request through. Identity unreachable or answering oddly is
  a 500, never access. It does not special-case administrators. Details:
  `design_docs/user_roles_design.md` section 9.5.
- **`project_id` rules.** The Gateway authorises from the project named in
  the request; the CMS only checks the item really belongs to it.
  - CMS `PATCH`/`DELETE` on test cases and folders require a `project_id`
    query parameter (400 if missing, 404 if the item is in another project).
  - CMS creates take the project in the body; an optional `?project_id=` must
    match it (400 if not).
  - Gateway creates put the project in the **path**
    (`POST /web/<project_id>/testcases`, `.../folders`) and reject a
    `project_id` in the body (400). Gateway `PATCH`/`DELETE` use
    `?project_id=`.
  - The Portal never sends `project_id` in a request body.
- **Deletes are guarded.** Test cases and folders are **hard-deleted**
  (decision of 2026-10-15; only projects are soft-deleted). A folder delete is
  refused with a `409` and a `testcase_count` if the folder or any sub-folder
  holds test cases, unless `cascade=true` (only that exact value cascades).
  Deleting a case type moves its test cases to the default; the default case
  type is never deleted.
- **Moves are guarded too.** `POST /testcases/<id>/move` and
  `POST /folders/<id>/move` (CMS, and the same under `/web` on the Gateway)
  take `folder_id` / `parent_id`, which must always be present (`null` = top
  level, so an omitted value is a 400, never "top level"). Same project only;
  a clash in the destination is a 409; a section cannot go into itself or its
  own subtree (400). A move needs Add/Modify, not Delete. See
  `design_docs/moving_testcases_and_sections.md`.
- **Case types are the template** for new customisation lists (Priorities,
  Case Statuses): global to the instance, one default that can be moved but
  never unset or deleted, delete moves dependants to the default.
- **No database migrations before 1.0.** A schema change means rebuilding
  the database with `items/tool_cms_db_builder/db_builder.py -d <new file>`
  (it refuses to overwrite an existing file) and copying it over the
  tracked `databases/` file. Existing dev databases are rebuilt, not migrated.

- **Users reach ITEMS over HTTPS; only the Portal is user-facing.** In Docker
  a Caddy container terminates HTTPS in front of the Portal, and the Portal
  sets `[tls] secure_cookies=true` so its login cookies are `Secure`. Without
  Docker the Portal can serve HTTPS itself: set both `cert_file` and
  `key_file` in `[tls]` (only one of the two is a start-up error). Leaving
  `[tls]` out gives plain HTTP for development. The login cookies are always
  `HttpOnly` and `SameSite=Lax`. Service-to-service traffic stays HTTP on the
  internal Docker network.

## Portal UI conventions

The Portal is server-rendered: forms `POST`, and the page re-renders (or
redirects) with an error banner and the typed input kept.

- **Pop-ups only for small, fixed forms** (a case type, a section's name,
  delete confirmations). **Full pages for anything that will grow**: a test
  case's view, add and edit pages.
- The **view page and the edit page mirror each other**: same title bar,
  card, field order and button row.
- **Moving is its own action.** A test case moves from a separate "Move Test
  Case" box on its edit page (never a field in the edit form, so Save and Move
  cannot be confused); a section moves from a small pop-up on its row. Both
  View and Edit pages show the current section, so they keep mirroring. The
  section pop-up leaves out the section's own subtree as destinations.
- A delete **confirmation states what will be lost** (for example the number
  of test cases a section delete removes) in a single box. If a prompt
  surprises the person who designed it, it will surprise users.
- Buttons: `btn-header` (navy) is the primary, `btn-header-outline` the
  secondary, red for destructive actions.

## Releases

A release is cut from `main` once a feature is complete across every service
it touches (see `CONTRIBUTING.md`). Before tagging, all five services pass
their tests at 100% coverage with a clean pylint.

1. The **release PR** contains only the version change (`MINOR`/`PATCH` as
   appropriate and `PRE_RELEASE = None` in `items/shared/__init__.py`) and
   the README's "current release" line. Nothing else rides along with it.
2. Tag `V<major>.<minor>.<patch>` on `main` and publish the GitHub release;
   the Docker image builds run from it.
3. The release notes say whether any database needs rebuilding (there are no
   migrations before 1.0) and list the known limitations.

## Keep these in step with the code

When a route, request or response changes, update in the **same branch**:

- `design_docs/gateway_web_api.md` for any Gateway route (conventions and
  full route table).
- `design_docs/case_types_api.md` (or the matching contract) for CMS API
  changes.
- The Postman collection, for a route on **any** service (CMS, Identity or
  Gateway; each has its own folder). Make **targeted text edits** only; never
  re-serialise the whole JSON file.

## Code style

- PEP 8, about 79 columns. Every Python file starts with the Apache licence
  header; copy it from a neighbouring file.
- Google-style docstrings (`Args`, `Returns`, `Raises`), with the HTTP status
  codes listed on handlers. Match the surrounding code's naming and comment
  density.
- Services build URLs by concatenation, so configured base URLs must end in
  `/` (the Gateway normalises its own; the Portal's `gateway_svc` does not).

## Gotchas

- **Manual testing dirties `databases/items_cms.LATEST.db`**, which is
  tracked. Restore it with `git checkout -- databases/items_cms.LATEST.db`
  (CMS stopped) before committing. Stage files **by name**, never
  `git add .`: the `-wal` and `-shm` files and local `.bat` files are
  untracked and not ignored.
- A running service does not pick up merged code until it is restarted. A new
  route that returns **405** usually means a service on the dev server is
  running old code. Restart all services together; the Gateway logs a
  warning if its version differs from the CMS's or Identity's.
- Only the CMS and Identity databases exist; test data created in Postman
  lives in them.
- **Browsers cache the Portal's scripts and stylesheets.** After changing
  `static/` files, a hard refresh (Ctrl+F5) is needed. A pop-up that opens
  but is not filled in, or a button that stays disabled, usually means a
  stale cached script.
- **Test mocks must not hide mistakes.** A handler's broad
  `except Exception` (used so a failed optional fetch is non-fatal) will also
  swallow the "unexpected request" error a test helper raises, so a test can
  pass without exercising the new request. Give such tests URL-keyed mocks
  and assert the URL was actually requested.
- **Pylint's score hides messages.** A clean 10.00 can still carry messages
  (mixed line endings, too-many-locals): read the output, not just the score.
  Working copies are CRLF (the index is LF, `autocrlf=true`), so a new file
  must be CRLF too, or pylint reports mixed line endings.
- **Unit tests only check markup.** To verify JavaScript or a pop-up, render
  the real page with the real handler and templates (gateway mocked) to a
  scratch folder, serve it, and click through it in the built-in browser.

## Working with Claude Code in this repo

- The shell tool mangles backslashes and quotes inside heredocs. For anything
  non-trivial, write the edit script to a file and run that.
- Prefer the editor tools for source edits, and run the real test commands
  above rather than guessing.
- Two Quart apps driven in one process (for example a scratch script that
  calls the Portal, which calls the Gateway, which calls the CMS) share
  `contextvars`, so a nested request replaces the caller's request and its
  headers or form data vanish. Run each forwarded call in its own empty
  context (`create_task(coro, context=contextvars.Context())`). Separate
  services never do this.
- Never branch for the next ticket before the previous one is merged: the
  version number (`PRE_RELEASE`) and the base are both wrong. Wait for the
  merge, `git fetch`, check `main`'s version, then branch.
