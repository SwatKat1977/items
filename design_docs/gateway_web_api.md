# Gateway Web API

**Service:** Gateway (`items_gateway`). All routes below are served under the
`/web` prefix.
**Status:** First draft - the conventions and the route table. Per-area detail
(request/response schemas) lives in per-area documents, e.g.
`case_types_api.md`, and is added area by area. Response shapes below are
marked from reading the handlers; refine them as each area is written up.

The Gateway is the only service the Web Portal talks to. Almost every route is
a thin forwarder to Identity or the CMS; the Gateway adds session
authentication and authorisation, and in a few places reshapes the response.

If a route, its auth level, or its response shape changes, update this file in
the same branch.

---

## 1. Conventions

### 1.1 Authentication

Sessions live in Gateway memory (a Gateway restart invalidates every token).
They are created with `POST /web/sessions` and presented on every other
request as two headers:

| Header | Value |
|---|---|
| `X-Items-User` | the session's email address |
| `X-Items-Token` | the session token |

Auth levels used in the route table:

| Level | Meaning | Failure |
|---|---|---|
| **None** | No session needed | - |
| **Session** | Any valid session | 401 |
| **Member** | Administrator, or a member of the project named in the request (`project_id` path argument, else `project_id` query parameter) | 401, or 403 if not a member |
| **Permission: *area* *action*** | The caller holds that permission on the project named in the request (`project_id` path argument, else `project_id` query parameter), as answered by the Identity service on every request. For example *Test Cases Read*, *Test Cases Add/Modify*, *Test Cases Delete*. | 401; 400 if there is no usable `project_id`; 403 if not granted; 500 if Identity cannot be reached or answers unexpectedly |
| **Admin** | Administrator session | 401, or 403 if not an administrator |

- 401 body: `{"error": "Unauthorized"}`. 403 body: `{"error": "Forbidden"}`.
- Administrators bypass the project-membership check on **Member** routes.
- If a **Member** route is called with no parseable `project_id`, the check is
  skipped and the handler reports the missing parameter itself.
- **Permission** routes behave differently on purpose (see section 9.5 of
  `user_roles_design.md`):
  - Nothing is cached: a change to a role, a membership or an account applies
    on the very next request, with no re-login.
  - The check never skips. A missing or non-integer `project_id` is a `400`
    `{"error": "project_id query parameter is required"}` (or `... must be an
    integer`) before anything else happens.
  - Administrators are not special-cased; Identity grants them everything.
  - It fails closed: only an explicit grant from Identity lets a request
    through. If Identity cannot be reached, or answers with an error or
    anything unexpected, the route returns `500`
    `{"error": "Identity service unavailable"}` and never allows the request.
  - A user who is not a member of the project, a member with no role, and a
    disabled account all simply hold no permissions, so get `403`.

### 1.2 Response shapes

The Gateway does not yet use a single response envelope. These styles exist,
named in the **Shape** column of the table:

| Shape | Meaning |
|---|---|
| **pass-through** | The upstream status code and JSON body are returned unchanged. Errors are `{"error": "<message>"}`. |
| **envelope** | Successes are `{"status": 1, ...}` and failures `{"status": 0, "error": "<message>"}`, with a Gateway-chosen status code. |
| **mixed** | The success body is the upstream body; failures use the envelope (a missing project is a bare 404 with no body). |
| **plain text** | Not JSON; see the route's note. |

New routes should use **pass-through**.

### 1.3 Upstream failures

If the Gateway cannot reach Identity or the CMS it returns **500** with an
error message (the wording varies by handler, e.g. "Identity service
unavailable" or "Internal error!").

Request bodies must be valid JSON; most routes return **400** otherwise.
Validation of the body's fields is the upstream service's job on pass-through
routes.

### 1.4 Paths

`<id>` segments declared as integers (`<int:...>`) return a routing 404 for
anything else. The Custom Fields collection routes are registered **with** a
trailing slash (`/web/testcase_custom_fields/`); all other collection routes
have none.

---

## 2. Route table

Upstream paths are relative to the Identity or CMS base URL.

### 2.1 Sessions

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `POST` | `/web/sessions` | None | Identity `auth/login`, `users/profile`, `users/<id>/projects` | envelope | Password login. Success `{"status": 1, "token": ...}`. Bad credentials: 401, empty body. |
| `POST` | `/web/sessions/validate` | None | - | envelope | Body `{email_address, token}`. Returns `{"status": "VALID"}` or `{"status": "INVALID"}`. |
| `POST` | `/web/sessions/refresh` | None | - | envelope | Not implemented: 501. |
| `DELETE` | `/web/sessions` | None | - | plain text | Body `{email_address, token}`. Always 200 with the text `OK`, even if the session was invalid (logged, not reported). |

### 2.2 Webhook

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `GET` | `/web/webhook/metadata` | None (HMAC) | - | pass-through | Not session-authenticated. Requires a nonce and a valid HMAC signature, else 401. |

### 2.3 Invites

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `GET` | `/web/invites` | Admin | Identity `invites` | pass-through | |
| `POST` | `/web/invites` | Admin | Identity `invites` | pass-through | Also sends the invite email. |
| `POST` | `/web/invites/resend` | Admin | Identity `invites/resend` | pass-through | |
| `POST` | `/web/invites/uninvite` | Admin | Identity `invites/uninvite` | pass-through | |
| `GET` | `/web/invites/token/<token>` | None | Identity `invites/token/<token>` | pass-through | Used by the accept-invite page before login. |
| `POST` | `/web/accept_invite` | None | Identity `invites/token/<token>`, `users`, `invites/uninvite` | pass-through | Creates the user using the email from the invite, not from the form; 201 on success. |

### 2.4 Projects

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `GET` | `/web/projects` | Session | CMS `projects` | mixed | Result is filtered to the caller's projects unless administrator. |
| `GET` | `/web/projects/<project_id>` | Member | CMS `projects/<id>` | mixed | |
| `GET` | `/web/projects/<project_id>/permissions` | Session | Identity `users/<caller's id>/projects/<id>/permissions` | pass-through | What the **caller** may do in the project, per area: `200 {"project_id": n, "areas": {"test_cases": {"read": bool, "add_modify": bool, "delete": bool}, ...}}`, every area present. For the Portal to decide which controls to show; it is a convenience, not a security measure, because every write route enforces the same permissions itself. Always about the caller: the user comes from the session and nothing in the request can name anyone else. A non-member, a member with no role and a disabled account get `200` with every flag false (an answer, not an error). `403` if the session has no user id or Identity does not know the user; `500` if Identity cannot be reached or answers unexpectedly. Not cached, so a change shows on the next call. |
| `POST` | `/web/projects` | Admin | CMS `projects` | envelope | |
| `PATCH` | `/web/projects/<project_id>` | Admin | CMS `projects/<id>` | envelope | |
| `DELETE` | `/web/projects/<project_id>` | Admin | CMS `projects/<id>?hard_delete=` | envelope | Optional `hard_delete` query parameter. |

### 2.5 Users

All Admin.

| Method | Path | Upstream | Shape | Notes |
|---|---|---|---|---|
| `GET` | `/web/users` | Identity `users` | pass-through | |
| `POST` | `/web/users` | Identity `users` | pass-through | Longer upstream timeout (password hashing). |
| `GET` | `/web/users/<user_id>` | Identity `users/<id>` | pass-through | |
| `PATCH` | `/web/users/<user_id>` | Identity `users/<id>` | pass-through | |
| `POST` | `/web/users/<user_id>/password` | Identity `users/<id>/password` | pass-through | Longer upstream timeout. May send an email. |
| `GET` | `/web/users/<user_id>/projects` | Identity `users/<id>/projects` | pass-through | |
| `POST` | `/web/users/<user_id>/projects` | Identity `users/<id>/projects`; CMS `projects/<id>` | pass-through | Checks the project exists in the CMS first. |
| `PATCH` | `/web/users/<user_id>/projects/<project_id>` | Identity `users/<id>/projects/<pid>` | pass-through | Changes the member's role. |
| `DELETE` | `/web/users/<user_id>/projects/<project_id>` | Identity `users/<id>/projects/<pid>` | pass-through | |

`<user_id>` is a string (UUID), not an integer.

### 2.6 Roles

All Admin; all forwarded to Identity `roles`.

| Method | Path | Upstream | Shape |
|---|---|---|---|
| `GET` | `/web/roles` | `roles` | pass-through |
| `POST` | `/web/roles` | `roles` | pass-through |
| `GET` | `/web/roles/<role_id>` | `roles/<id>` | pass-through |
| `PATCH` | `/web/roles/<role_id>` | `roles/<id>` | pass-through |
| `DELETE` | `/web/roles/<role_id>` | `roles/<id>` | pass-through |

### 2.7 Test case types

Forwarded to CMS `case_types`. Case types are global to the instance, so reads
need only a session (testcase forms need the list and the default); writes are
admin-only. Contract, schemas and invariants: `case_types_api.md`.

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `GET` | `/web/case_types` | Session | `case_types` | pass-through | |
| `GET` | `/web/case_types/<type_id>` | Session | `case_types/<id>` | pass-through | |
| `POST` | `/web/case_types` | Admin | `case_types` | pass-through | Never creates the default. |
| `PATCH` | `/web/case_types/<type_id>` | Admin | `case_types/<id>` | pass-through | Name and description only; `is_default` is rejected. |
| `POST` | `/web/case_types/<type_id>/set_default` | Admin | `case_types/<id>/set_default` | pass-through | No body. Atomic and idempotent. |
| `DELETE` | `/web/case_types/<type_id>` | Admin | `case_types/<id>` | pass-through | Test cases using the type move to the current default. 404 if missing; 409 if it is the default. |

### 2.8 Testcases

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `GET` | `/web/<project_id>/testcases` | Test Cases Read | CMS `testcases?project_id=` | mixed | |
| `GET` | `/web/testcases/<case_id>?project_id=` | Test Cases Read | CMS `testcases/<id>?project_id=` | mixed | `project_id` query parameter is required. |
| `POST` | `/web/<project_id>/testcases` | Test Cases Add/Modify | CMS `testcases` | pass-through | Body: `folder_id` (int or null), `name`, `description`, optional `case_type_id` (omitted = the current default type). The project comes from the path only: the body must not contain a `project_id` (400). 200 `{"testcase_id": n}`; 404 unknown project, folder or case type; 409 duplicate sibling name. |
| `PATCH` | `/web/testcases/<case_id>?project_id=` | Test Cases Add/Modify | CMS `testcases/<id>?project_id=` | pass-through | Body: `name`, `description`, optional `case_type_id` (omitted = unchanged). `project_id` is required (400 if missing); 404 if the test case is in another project, or the type is unknown; 409 duplicate sibling name. |
| `POST` | `/web/testcases/<case_id>/move?project_id=` | Test Cases Add/Modify | CMS `testcases/<id>/move?project_id=` | pass-through | Body: `folder_id`, the destination section's id, or `null` for the top level; always required (400 if left out, so it is never read as the top level). `project_id` is required (400 if missing). 400 if the destination section is in another project; 404 if the test case is in another project or the section does not exist; 409 if the destination already has a test case with that name. Moving to where it already is succeeds. |
| `DELETE` | `/web/testcases/<case_id>?project_id=` | Test Cases Delete | CMS `testcases/<id>?project_id=` | pass-through | `project_id` is required (400 if missing); 404 if the test case is in another project. |

These routes enforce the per-area role grid (Test Cases: Read / Add/Modify /
Delete, see `user_roles_design.md` section 9.5): Read to browse, Add/Modify to
create or edit, Delete to delete. A read-only member can browse but any write
returns `403`. The check is made with the Identity service on every request,
so changing a role or membership takes effect immediately. See the
**Permission** level in section 1.1 for the full rules, including the `400` for
a missing `project_id` and the `500` if Identity cannot be asked.

### 2.9 Sections (folders)

Sections are read through the test case list (`GET /web/<project_id>/testcases`
returns the whole folder tree), so only the writes are routed. Sections belong
to the Test Cases area of the role grid, so these routes enforce it exactly as
the test case routes do (see the **Permission** level in section 1.1): Add/Modify
to create or rename a section, Delete to delete one. Deleting a section needs
**Delete** with or without `cascade=true`, because it can destroy the test
cases inside it (rule 6 of section 8 of `user_roles_design.md`), so a role that
can only create and rename sections cannot delete them. The CMS decides what the
`cascade` value means and rejects anything it does not understand.

| Method | Path | Auth | Upstream | Shape | Notes |
|---|---|---|---|---|---|
| `POST` | `/web/<project_id>/folders` | Test Cases Add/Modify | CMS `folders` | pass-through | Body: `parent_id` (int, or null for a top-level section) and `name`. The project comes from the path only: the body must not contain a `project_id` (400). 200 `{"folder_id": n}`; 404 unknown project or parent; 409 duplicate sibling name. |
| `PATCH` | `/web/folders/<folder_id>?project_id=` | Test Cases Add/Modify | CMS `folders/<id>?project_id=` | pass-through | Body: `name`. `project_id` is required (400 if missing); 404 if the section is in another project; 409 duplicate sibling name. |
| `POST` | `/web/folders/<folder_id>/move?project_id=` | Test Cases Add/Modify | CMS `folders/<id>/move?project_id=` | pass-through | Body: `parent_id`, the new parent section's id, or `null` for the top level; always required (400 if left out, so it is never read as the top level). `project_id` is required (400 if missing). 400 if the new parent is in another project, or is the section itself or one of its own sub-sections (a loop); 404 if the section is in another project or the new parent does not exist; 409 if the new parent already has a section with that name. Moving to the parent it already has succeeds. The section's sub-sections and test cases move with it. |
| `DELETE` | `/web/folders/<folder_id>?project_id=[&cascade=true]` | Test Cases Delete | CMS `folders/<id>?project_id=[&cascade=]` | pass-through | `project_id` is required (400 if missing). Refused with **409** `{"error": ..., "testcase_count": n}` if the section or a sub-section contains test cases, unless `cascade=true`, which also deletes them. 404 if the section is in another project. |

### 2.10 Testcase custom fields

All Admin; all forwarded to CMS `testcase_custom_fields`.

| Method | Path | Upstream | Shape | Notes |
|---|---|---|---|---|
| `GET` | `/web/testcase_custom_fields/` | `testcase_custom_fields` | pass-through | Optional integer `project_id` query parameter. |
| `GET` | `/web/testcase_custom_fields/<field_id>` | `testcase_custom_fields/<id>` | pass-through | |
| `POST` | `/web/testcase_custom_fields/` | `testcase_custom_fields` | envelope | |
| `PUT` | `/web/testcase_custom_fields/<field_id>` | `testcase_custom_fields/<id>` | envelope | Replaces the field definition. |
| `PATCH` | `/web/testcase_custom_fields/<field_id>` | `testcase_custom_fields/<id>` | envelope | Moves the field's position (`direction`). |
| `DELETE` | `/web/testcase_custom_fields/<field_id>` | `testcase_custom_fields/<id>` | envelope | |

---

## 3. Not yet covered

- Per-area request and response schemas. Test case types are covered by
  `case_types_api.md`; nothing else has a dedicated document yet.
- A test that compares this route table with the Gateway's registered routes.
