# CMS: Test case types (core)

**Branch:** `cms_case_types_core` (pushed, PR pending)
**PR title:** `[CMS] Test case types`
**Theme:** 0.4.0 - "Test Cases, properly". First piece: the Case Types
customisation (one of the three test-case-facing lists, alongside
Priorities and Case Statuses, that the Customisations page currently shows
as placeholder tabs). Result Fields and Result Statuses are deliberately
out of scope for 0.4.0.

## Summary

Adds test case types to the CMS: a fixed, admin-managed list of categories
(Functional, Regression, Security, ...) with exactly one **default** that
will become the fallback for new or orphaned test cases. This branch is the
CMS data layer and API only - no delete, no link from test cases to a type,
no Gateway routes, no Portal UI. Each of those is its own branch, following
the CMS -> Gateway -> Portal order used for roles in 0.3.0.

## Schema

`tc_case_types` (`id`, `name` UNIQUE, `description`, `is_default`), plus a
partial unique index `WHERE is_default = 1` so the database itself refuses
a second default, independent of the service logic. The index is a separate
DDL step in `db_builder.py` because `create_table()` runs one statement per
call.

The builder seeds 15 types - Accessibility, Compatibility, Destructive,
Functional, Integration, Performance, Regression, Security, Smoke, Sanity,
Usability, Recovery, Installation / Upgrade, Localization, Other - each
with a description (intended as a hover hint in the Portal). "Other" is the
initial default. This is our own list rather than TestRail's: Smoke and
Sanity are split, and Integration, Recovery, Installation / Upgrade and
Localization are added. `databases/items_cms.LATEST.db` was rebuilt;
there is no migration path, per the pre-1.0 policy.

## API (CMS, port 6050)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/case_types` | List, ordered by name |
| `GET` | `/case_types/<id>` | Get one |
| `POST` | `/case_types` | Add (never the default) |
| `PATCH` | `/case_types/<id>` | Change name and description |
| `POST` | `/case_types/<id>/set_default` | Make this the default |

The full contract (object shape, JSON Schema, status codes, invariants) is
in `design_docs/case_types_api.md`, which the Gateway and Portal branches
build against. Postman requests for all five endpoints are added to the
collection.

Design points worth knowing:

- **`set_default` is its own action**, not a field on `PATCH`. Making a
  type the default is a swap across two rows, not an edit of one, so
  `PATCH` does not accept `is_default` at all (it is absent from the
  schema). The Portal's edit form will present name and "is default"
  together and call both endpoints itself.
- **`set_default` is a single transaction** (`BEGIN IMMEDIATE ... COMMIT`
  via `run_script`), so there is never a moment with zero or two defaults,
  and a crash part-way cannot strip the default. The clear is guarded by
  an `EXISTS` check, so a request for a missing id cannot remove the
  current default. It is idempotent on the type that is already default.
  (My first version did two separate `UPDATE`s; this replaces it.)
- **Names are trimmed and unique ignoring case**, using
  `LOWER(name) = LOWER(?)` to match the existing Case Fields convention
  rather than introducing `COLLATE NOCASE`. Whitespace-only names are
  rejected with 400.
- **`PATCH` checks existence before name uniqueness**, so a missing id is
  always 404, even if the requested name belongs to another type (it would
  otherwise be reported as a 409 conflict). Covered by a service test.
- **Responses are objects, not positional rows**: `{id, name, description,
  is_default}` with `is_default` as a real JSON boolean. This differs from
  the Case Fields endpoints, which return raw positional arrays that the
  Portal maps itself; chosen deliberately so the Gateway and Portal don't
  inherit that.

## Tests

548 tests via the official entry point
(`python -m unittest unit_tests/items_cms/main.py`), 100% coverage
confirmed through it, pylint 10.00/10 on `items/services/items_cms`. New:
repository tests against a real SQLite file (including that the partial
index rejects a second default on its own, that a failed `set_default`
leaves the existing default alone, and idempotency), service tests with a
mocked repository, handler tests (including that `is_default` is rejected
by `POST`/`PATCH`), and route-wiring reachability for all five routes.

## Also in this branch

`README.md` and `CONTRIBUTING.md` were updated (current release, which
version to use, one-service-per-branch and PR title conventions). These are
not part of case types and could have been their own PR.

## Known limitations

- SQLite's `LOWER()` is ASCII-only, so `"Éxploratory"` and `"éxploratory"`
  are treated as different names. Same limitation as Case Fields today.
- The database `UNIQUE` on `name` is exact-match; case-insensitive
  uniqueness is enforced by the service only.

## Deliberately out of scope (later 0.4.0 branches)

- **Delete** - the default must never be deletable, and deleting any other
  type reassigns its test cases to the default.
- **Attaching a type to test cases** - needs `testcases.case_type_id`;
  required before delete can reassign anything.
- **Gateway proxy routes and Portal tab** for case types.
- **Priorities and Case Statuses** - same shape as Case Types.
