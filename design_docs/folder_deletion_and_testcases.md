# Folder deletion vs. test case deletion

**Status:** The folder-delete safety is **implemented** in the CMS (see
"What was built" below). The soft-delete decision for test cases is still
open: the user currently prefers to keep test cases as hard delete.

## What was built

- `DELETE /folders/<id>?project_id=<id>` **refuses by default** if the folder
  or any descendant contains test cases: `409` with
  `{"error": "...", "testcase_count": <n>}`, and nothing is deleted. The count
  covers the whole subtree.
- `DELETE /folders/<id>?project_id=<id>&cascade=true` deletes the folder, its
  descendants and every test case beneath them. `cascade` must be `true` or
  `false` (any letter case); anything else is a `400` rather than being read as
  false, so a typo can't change what a delete means.
- An empty folder (no test cases anywhere beneath it) deletes with no flag.
- The refusal is **part of the delete, not a count followed by a delete**: the
  delete runs as one `BEGIN IMMEDIATE` transaction guarded on there being no
  test cases in the subtree. A test case added after the count therefore cannot
  be wiped out by a delete that was approved without it; the caller is told it
  was blocked instead.
- **No separate count endpoint was built.** The Portal learns the number from
  the `409` itself: it asks "delete section X?", and if the CMS answers 409 with
  a count it shows a second prompt naming the number before retrying with
  `cascade=true`. That avoids the count-then-delete race the original note
  worried about, with one fewer route.
- Test cases remain **hard delete**; the soft-delete idea below was not built.

## Context

CMS testcase folder CRUD (`items/services/items_cms/routes/folders/`)
currently deletes a folder unconditionally, relying on `ON DELETE CASCADE`
to remove any child folders and — once test case CRUD exists — any test
cases sitting in that subtree too (`tc_test_cases.folder_id` also cascades
from `tc_folders`).

This is fine today because there is no way to create a test case yet, so a
folder can never actually contain one. It stops being fine once test case
CRUD lands: a folder delete would then silently wipe out real work product
(test cases, and whatever custom field values or future test-run history
hang off them) with no warning and no way to undo it.

## Decision (agreed, not yet built)

- **Test cases get soft/hard delete**, mirroring the pattern already used
  by projects (`awaiting_purge` for soft delete, permanent removal for hard
  delete). Test cases represent real work product, so accidental loss
  matters more than it does for a folder.
- **Folders stay hard-delete-only.** A folder is pure organisation — there's
  nothing to lose by deleting the folder itself, only by deleting what's
  inside it.
- **`DELETE /folders/<id>` refuses by default if the folder contains any
  test cases, recursively** (i.e. in the folder itself or any descendant
  folder). Returns `409 Conflict` with the count in the body, e.g.
  `{"error": "...", "testcase_count": 12}`. No deletion happens.
- **`DELETE /folders/<id>?cascade=true` proceeds anyway**, deleting the
  folder, all descendant folders, and all test cases underneath. Mirrors the
  existing `?hard_delete=true` query param already used on project delete,
  so the shape is consistent with precedent elsewhere in this API.
- **A separate read-only "count" endpoint** (exact route TBD — something
  like `GET /folders/<id>/testcase_count`) is worth adding *in addition*,
  purely so the web portal can show "this folder contains 12 test cases"
  proactively in a confirmation dialog, before the user even attempts the
  delete. This is a UI convenience, not the actual safety mechanism — the
  409-by-default behaviour on `DELETE` is what actually prevents accidental
  data loss, since a separate count-then-delete flow has an inherent race
  condition (a test case could be added between the count call and the
  delete call).

## Why this wasn't built into the folder CRUD PR

A `cascade` query param on `DELETE /folders/<id>` is purely additive —
optional, defaults to today's behaviour — so there's no compatibility cost
to adding it later. Building it now would mean either:
- the 409/cascade logic never actually triggers (no folder can contain a
  test case yet), so it ships as untested dead code, or
- inventing a fake "testcase_count" concept ahead of the real test case
  schema/service work, which risks not matching what that work actually
  needs.

Better to pick this up once test case CRUD is underway and there's a real
`tc_test_cases` service to query against.

## Open questions for when this is picked up

- Exact route/shape for the count endpoint — dedicated route vs. a query
  param on `GET /folders/<id>` (e.g. `?include_testcase_count=true`).
- Whether the count should distinguish soft-deleted (awaiting purge) test
  cases from active ones, once test cases have that concept.
- Whether `cascade=true` on folder delete should hard-delete or soft-delete
  the test cases underneath — likely soft-delete by default, with a further
  `hard_delete=true` needed on top, matching how project delete already
  layers these two flags.
