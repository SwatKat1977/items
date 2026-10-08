# Test Case Types - CMS API

**Service:** CMS (`items_cms`), default port 6050.
**Status:** Implemented in the CMS. Not yet proxied by the Gateway or used by
the Web Portal.

A test case type is a case's category (Functional, Regression, Security, ...).
It is a fixed, admin-managed list, not a per-project custom field. Exactly one
type is the **default** at any time; it is the fallback for new or orphaned
test cases. The database seeds 15 types, with "Other" as the default.

This document is the contract the Gateway and Portal build against. If the
CMS responses change, update this file in the same branch.

---

## 1. The case type object

Returned by both GET endpoints.

```json
{
  "id": 4,
  "name": "Functional",
  "description": "Core feature/business behaviour",
  "is_default": false
}
```

JSON Schema (draft 2020-12):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Case Type",
  "type": "object",
  "properties": {
    "id":          { "type": "integer", "minimum": 1 },
    "name":        { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "is_default":  { "type": "boolean" }
  },
  "required": ["id", "name", "description", "is_default"],
  "additionalProperties": false
}
```

Notes:

- `is_default` is a real JSON boolean. It is stored as 0/1 in SQLite and
  converted by the CMS service, so consumers never see an integer.
- `name` and `description` are returned already trimmed.
- `description` may be an empty string, never `null`.

## 2. Endpoints

All requests and responses are `application/json`. Failures always return
`{"error": "<message>"}` (see section 3).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/case_types` | List all case types, ordered by name |
| `GET` | `/case_types/<type_id>` | Get one case type |
| `POST` | `/case_types` | Add a case type (never the default) |
| `PATCH` | `/case_types/<type_id>` | Change name and description |
| `POST` | `/case_types/<type_id>/set_default` | Make this the default type |

`<type_id>` must be an integer; anything else is a routing 404.

### 2.1 `GET /case_types`

- **200** - JSON array of case type objects (section 1), ordered by `name`.
  Possibly empty.
- **500** - internal error.

### 2.2 `GET /case_types/<type_id>`

- **200** - a single case type object.
- **404** - no type with that ID.
- **500** - internal error.

### 2.3 `POST /case_types`

Request body (all fields required, no others allowed):

```json
{ "name": "Exploratory", "description": "Unscripted testing" }
```

- `name`: string, at least one non-whitespace character. Surrounding
  whitespace is trimmed. Must be unique, compared case-insensitively
  (`"smoke"` clashes with `"Smoke"`).
- `description`: string, may be empty. Trimmed.
- `is_default` is **not accepted**; a new type is never the default.

Responses:

- **200** - `{"case_type_id": <int>}`
- **400** - body fails validation (missing/extra field, empty or
  whitespace-only name, wrong type).
- **409** - the name is already in use.
- **500** - internal error.

### 2.4 `PATCH /case_types/<type_id>`

Same request body and validation as `POST /case_types`. Both fields are
required (this replaces name and description; it is not a partial update).
A type may be "renamed" to its own current name without conflict.
`is_default` is **not accepted** here.

Responses:

- **200** - `{}`
- **400** - body fails validation.
- **404** - no type with that ID.
- **409** - the name is used by a different type.
- **500** - internal error.

### 2.5 `POST /case_types/<type_id>/set_default`

No request body. Makes the type the default and un-defaults whichever type held
it, as a single database transaction, so there is never a moment with zero or
two defaults. Idempotent: calling it on the type that is already the default
succeeds.

Responses:

- **200** - `{}`
- **404** - no type with that ID. The current default is left unchanged.
- **500** - internal error.

## 3. Error format

```json
{ "error": "Case type name 'Smoke' already exists" }
```

| Status | Meaning |
|---|---|
| 400 | Invalid request body |
| 404 | Case type not found |
| 409 | Name conflict |
| 500 | Internal error, or the CMS database is unavailable |

## 4. Invariants

- At most one type has `is_default = true`, enforced by a partial unique index
  in the database as well as by the service.
- The default can only be changed with `set_default`, never through
  `POST` or `PATCH`.
- Type names are unique ignoring case.

## 5. Not yet implemented

- **Delete** - deferred to its own branch. The default type must never be
  deletable.
- **Attaching a type to test cases** - deferred, along with the fallback to the
  default type for orphaned test cases.
- **Gateway routes and Portal UI** - separate branches.
