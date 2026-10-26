# ITEMS automation

API-level tests that run against a **running ITEMS stack** (Identity, CMS and
Gateway), sending real requests and checking the responses. They sit alongside
the services' unit tests, not in place of them: unit tests prove each service
on its own, these prove the services work *together*.

## Layout

| Path | What |
|---|---|
| `api_core/` | A small, **generic** library: send a request, check the reply. It knows nothing about ITEMS and **never imports from `items`**. |
| `tests/core/` | Tests of `api_core` itself. They run against a tiny local server, so they need no ITEMS stack. |
| `tests/stack/` | Tests that need a running stack (marked `stack`). This is where ITEMS knowledge lives: the Gateway address, the administrator, what each route should do. |

Tests are **black-box**: they send literal URLs and bodies and import nothing
from `items`, so a test fails if the contract changes by accident.

## Running

Install (the repo's `venv` is fine):

```bash
pip install -r requirements/requirements_automation.txt
```

The library's own tests (no stack needed). Run from this folder:

```bash
cd automation
python -m pytest
```

The stack tests need Identity, CMS and the Gateway running with a database you
are happy to have test data added to:

```bash
ITEMS_ADMIN_PASSWORD=<the administrator's password> python -m pytest -m stack
```

| Setting | Default |
|---|---|
| `ITEMS_GATEWAY_URL` | `http://127.0.0.1:7050/` |
| `ITEMS_ADMIN_EMAIL` | `admin@localhost` |
| `ITEMS_ADMIN_PASSWORD` | none: the stack tests that need it are **skipped** without it |

`pytest.ini` leaves the `stack` tests out of a plain run (`-m "not stack"`), so
a plain `python -m pytest` never needs a stack.

## Writing a test

```python
from api_core import expect_json, expect_status

pytestmark = pytest.mark.stack

async def test_a_token_works_on_the_next_request(gateway, admin):
    login = await gateway.post("web/sessions", json=admin)
    expect_status(login, 200)
    token = expect_json(login, "token")        # keep it for the next request

    projects = await gateway.get("web/projects", headers={
        "X-Items-User": admin["email_address"], "X-Items-Token": token})
    expect_status(projects, 200)
```

- `expect_status(reply, 200)` and `expect_json(reply, "a.b.0.c", expected)`
  return what they checked, so a value can be used in the next request.
- A failed check says what was sent and what came back (method, URL, query,
  headers, body, status and response body), with tokens and passwords hidden.
- A service that cannot be reached comes back as a reply, not an exception
  (`expect_no_response(reply)` checks for it).
- Tests and fixtures are `async def`; they share one event loop and one HTTP
  session for the whole run (see `pytest.ini`).
