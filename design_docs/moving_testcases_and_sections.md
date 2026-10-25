# Moving test cases and sections

**Status:** implemented in 0.5.0 (CMS, Gateway and Portal). Decided
2026-10-15: both test cases **and** sections are movable. Moving a section
re-parents it; it takes everything beneath it along.

A move changes only where something sits. Nothing is created or destroyed, so
it needs **Test Cases: Add/Modify**, not Delete (see `user_roles_design.md`
section 9.5). It works **within one project** only.

## Routes

| Service | Route | Body |
| ------- | ----- | ---- |
| CMS | `POST /testcases/<id>/move?project_id=` | `{"folder_id": <section id or null>}` |
| CMS | `POST /folders/<id>/move?project_id=` | `{"parent_id": <section id or null>}` |
| Gateway | `POST /web/testcases/<id>/move?project_id=` | as CMS, passed straight through |
| Gateway | `POST /web/folders/<id>/move?project_id=` | as CMS, passed straight through |
| Portal | `POST /<project_id>/testcases/<id>/move` | form field `folder_id` (empty = top level) |
| Portal | `POST /<project_id>/folders/<id>/move` | form field `parent_id` (empty = top level) |

The Gateway routes are in `gateway_web_api.md`. `null` (or an empty form field)
means the **top level**.

### The destination is always required

`folder_id` / `parent_id` must be **present** in the CMS request, even when it
is `null`. A body without it is a `400`. This is deliberate: an omitted value
must never be read as "move to the top level", because a client that forgets
the field would silently flatten the tree.

### CMS rules and status codes

| Case | Result |
| ---- | ------ |
| Moved, or already in / under the destination | `200 {"status": 1}`; moving to where it already is changes nothing |
| `project_id` missing or not an integer | `400` |
| `folder_id` / `parent_id` missing, or not an integer or null | `400` |
| Destination belongs to a different project | `400` |
| A section moved into itself or into one of its own descendants | `400` ("A folder cannot be moved into itself or into one of its own sub-folders") |
| Test case / section unknown, or in a different project than `project_id` | `404` ("not found": a mismatch is reported exactly like a missing one) |
| Destination section does not exist | `404` |
| Destination already holds a test case / section with the same name | `409` ("... already exists in the destination") |
| Database failure | `500` |

- **The name-clash check is explicit** (a query before the update), because
  SQLite's `UNIQUE (project_id, parent_id, name)` ignores rows whose
  `parent_id` is `NULL`, so it would not catch a clash at the top level.
  Test cases are the same with `folder_id`.
- **Loop protection** asks whether the destination is the section itself or
  anywhere in its subtree (a recursive query, so it works at any depth). A
  loop would cut the whole subtree off from the rest of the tree.
- A moved section keeps its sub-sections and its test cases; they are not
  touched, because they point at the section, not at where it sits.

## Portal behaviour

- **A test case moves from its Edit page**, in a separate **Move Test Case**
  box below the edit form. It is its own action with its own button: the edit
  form is not sent, and Save does not move. The Edit and View pages both show
  the test case's current section as a path (for example `Regression / Smoke`,
  or `(No section)`), between Description and Type, so the two pages keep
  mirroring each other.
- **A section moves from a small pop-up** opened from a button on its row
  (sections are small, fixed forms, like rename). The destination list is
  **(Top level)** plus every section, indented by depth, starting on the
  current parent. It **leaves out the section itself and everything beneath
  it**, since those could only make a loop. The CMS still refuses a loop if a
  request is crafted or the page is stale.
- Both controls are **left out of the HTML** (not disabled) for a role without
  Add/Modify; the Gateway refuses the action regardless.
- A refused move shows the page again with a banner and keeps the chosen
  destination: a name clash, a destination or section that has gone, or a role
  that does not allow it (each in the Portal's own words).

## Not done

- Moving several items at once, drag and drop, and moving between projects.
- A Gateway route that returns one section: the View and Edit pages name the
  section by reading the whole section tree (one extra Gateway call), because
  the Gateway has no read route for a single section. See `future.md`.
