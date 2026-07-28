# User Roles & Permissions — Design

**Status:** Draft for review. Nothing in here is implemented yet.
**Scope:** v1 is users-only (no groups) and covers the General permission
grid, the `is_administrator` flag, and the delete/purge lifecycle.

---

## 1. Why this document exists

ITEMS currently has **no authorisation model at all**. Verified across the
codebase:

- No role, group, permission or admin concept exists in any service. The
  only matches for "permission" are Apache licence headers.
- `admin@localhost` is an **ordinary `user_profile` row** — nothing marks it
  as privileged.
- Every route under `/admin/` in the web portal is guarded only by
  `@require_session`, so **any logged-in user can reach the admin pages**,
  including Customisations. This is an open privilege-escalation gap (see
  §9.1).

Everything below is therefore greenfield.

## 2. What exists to build onto

Two **separate SQLite databases**. This is the constraint that shapes the
design: no foreign key can span them.

| `identity.db` | `cms.db` |
| ------------- | -------- |
| `user_profile` — `id`, `email_address`, `full_name`, `display_name`, `insertion_date`, `account_status`, `logon_type` | `prj_projects` — `id`, `name`, `awaiting_purge`, `announcement`, `show_announcement_on_overview`, `creation_date` |
| `user_auth_details` — `password`, `user_id` | `tc_folders`, `tc_test_cases`, `tc_custom_fields` (+ types/options/project-link tables) |

`AccountStatus` is already defined as `DISABLED = 0`, `ACTIVE = 1`.

## 3. Core concepts

Three independent ideas, deliberately kept separate:

1. **Account status** — is the account usable at all? (already exists)
2. **Project membership** — which projects can this user see?
3. **Area permissions** — within a project they can see, what can they do?

Plus one orthogonal flag:

4. **`is_administrator`** — can this user reach the admin panels?

### 3.1 Project membership is the access gate

Membership is what lets you exclude a user from a project entirely. A user
with no membership row for a project cannot see that the project exists — it
is absent from listings, and direct access by ID is refused.

This is **not** the same as groups. Membership is per-(user, project) access;
groups are a convenience for assigning many users at once. Per-project
access works fine with users only — exclusion is simply the *absence* of a
membership row.

## 4. The General grid (per project)

For each **area**, a member is granted any combination of:

| Area | Read | Add/Modify | Delete |
| ---- | ---- | ---------- | ------ |
| Test Cases | | | |
| Milestones | | | |
| Test Runs | | | |
| Test Plans | | | |
| Test Reports | | | |
| Test Results | | | |

`Delete` means **soft delete** throughout (see §6). There is no hard-delete
column — that capability was deliberately removed from this grid.

### 4.1 Invariant: Add/Modify implies Read

If `Add/Modify` is granted, `Read` is granted and **cannot be revoked while
`Add/Modify` remains set**.

Enforced in **two** places — the UI half alone is not sufficient:

- **UI:** ticking `Add/Modify` auto-ticks `Read` and disables the `Read`
  checkbox. Unticking `Add/Modify` re-enables `Read`, leaving it ticked but
  now editable.
- **Server / schema:** any grant with `add_modify = true AND read = false` is
  rejected. A `CHECK` constraint enforces this at the database level so it
  cannot be bypassed by a caller that skips the UI.

### 4.2 Invariant: Delete implies Restore

There is no separate "restore" or "undo delete" permission. Anyone who can
soft-delete an item in an area can also restore it in that area.

Rationale: restoring destroys nothing, so it is strictly *less* dangerous
than deleting. Gating it more tightly than `Delete` would be backwards;
gating it identically would mean a fourth column that is always set the same
way as the third.

If a genuine need to separate them appears later, splitting is additive and
requires no migration of existing grants.

### 4.3 Membership vs per-area Read

Two layers:

- **Membership** — the project is visible and can be opened.
- **Per-area `Read`** — what is visible *inside* it.

A member with no `Read` anywhere sees the project shell and no content. That
is a valid (if unusual) state, not an error.

## 5. Administration

### 5.1 The `is_administrator` flag

A boolean on `user_profile`. It gates **access to the admin panels**.
Without it, every `/admin/` route is refused.

**v1 rule:** `is_administrator` grants *all* administrative capability, and
implies all General permissions on all projects. There is no admin sub-grid
yet.

**Future:** an Admin grid subdividing the flag, along these lines — recorded
here so the flag does not quietly become load-bearing in a way that blocks
it:

| Area | Add/Modify | Delete |
| ---- | ---------- | ------ |
| Projects | | |
| Testcase Fields | | |
| Site Settings | | |
| Users | | |

### 5.2 Purge now

One administrative capability, **not** per-area: immediately hard-delete
items that are awaiting purge, bypassing the retention period.

Per-area granularity was considered and rejected — "can purge test cases
immediately but not milestones" is a distinction with no real use case.

Routine purging is handled by the background sweeper (§6); this capability
exists only for the exceptional "this needs to be gone today" case.

## 6. Delete lifecycle

| Step | Actor | Effect |
| ---- | ----- | ------ |
| 1. Soft delete | `Delete` permission | Item flagged as awaiting purge; hidden from all reads |
| 2. Restore | `Delete` permission (§4.2) | Flag cleared; item visible again |
| 3. Automatic purge | Background sweeper | After the retention period, item is hard-deleted |
| 4. Manual purge | `is_administrator` + Purge now | Immediate hard delete, bypassing retention |

This is the pattern `prj_projects` already follows via its `awaiting_purge`
column, with `mark_project_for_purge()` (soft) and `hard_delete_project()`
(hard) in `project_repository`. The design generalises that existing pattern
rather than inventing a new one.

**Note:** the sweeper (step 3) does not exist. `mark_project_for_purge` and
`hard_delete_project` are called only from `project_service`, so projects
marked for purge currently remain hidden indefinitely and are never
collected. See §10.2.

## 7. Schema (in `identity.db`)

Roles data lives with identity, not CMS, because:

- Authorisation is an identity concern; CMS need not know users exist.
- The gateway **already** calls identity to validate the session on every
  request, so effective permissions can ride along in that same response —
  no extra hop, no cache to invalidate.

The cost accepted: `project_id` references `cms.db` with no FK integrity, so
purging a project must clean up its grants in the other database (§10.4).

```sql
-- Admin gate  [IMPLEMENTED on identity_user_roles]
-- Declared as `integer DEFAULT 0 NOT NULL` in the table definition, matching
-- the column style already used by user_profile (SQLite has no real boolean).
ALTER TABLE user_profile
    ADD COLUMN is_administrator integer DEFAULT 0 NOT NULL;

-- Project membership (the access gate)
CREATE TABLE project_members (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    principal_type TEXT    NOT NULL CHECK (principal_type IN ('user','group')),
    principal_id   INTEGER NOT NULL,
    project_id     INTEGER NOT NULL,   -- cms.db prj_projects(id); no FK possible
    UNIQUE (principal_type, principal_id, project_id)
);

-- Per-area permissions for a membership
CREATE TABLE project_permissions (
    member_id      INTEGER NOT NULL,
    area           TEXT    NOT NULL,   -- 'test_cases', 'milestones', ...
    can_read       BOOLEAN NOT NULL DEFAULT 0,
    can_add_modify BOOLEAN NOT NULL DEFAULT 0,
    can_delete     BOOLEAN NOT NULL DEFAULT 0,

    PRIMARY KEY (member_id, area),
    FOREIGN KEY (member_id) REFERENCES project_members(id) ON DELETE CASCADE,

    -- Invariant from §4.1, enforced at the database level
    CHECK (can_add_modify = 0 OR can_read = 1)
);
```

### 7.1 Two deliberate design hooks

**`principal_type` / `principal_id` instead of a bare `user_id`.** In v1
every row is `('user', <id>)`. This costs one column now and means groups can
be added later *without migrating the central membership table or touching
any query that reads it*.

**Areas are rows, not columns.** `area` as a text key means adding
Milestones, Test Runs and the rest requires no schema change — important
given only Test Cases exists today (§9).

### 7.2 Future: groups

Adding groups later requires:

- Two new tables: `groups`, `group_members`
- One extra lookup inside the resolver (§8) to gather group-derived grants
- UI for group management, and a way to display *effective* permissions when
  they arrive from multiple sources ("Author via QA-Team" vs "Author
  directly")

No migration of existing data, and no change to how permissions are checked
anywhere else.

## 8. Resolution rules

```
effective(user, project, area):
    if user.account_status != ACTIVE:      return {}          # short-circuit
    if user.is_administrator:              return ALL          # v1: implies everything

    principals = [('user', user.id)]
    # future: + [('group', g) for g in groups_of(user)]

    memberships = project_members WHERE project_id = project
                                   AND (principal_type, principal_id) IN principals
    if not memberships:                    return {}          # no access at all

    rows = project_permissions WHERE member_id IN memberships AND area = area
    return union of flags across rows                          # most permissive wins
```

Rules, stated explicitly because these are where authorisation bugs live:

1. **Union, most-permissive-wins.** Effective permissions are the union of
   all matching grants.
2. **No negative permissions.** There are no "deny" grants. They make
   effective access genuinely hard to reason about and are the classic source
   of "why can't this user do X".
3. **`account_status = DISABLED` short-circuits everything**, regardless of
   any grant.
4. **`is_administrator` implies everything** in v1.
5. **No membership means no access** — not "membership with empty
   permissions".
6. **Cascading operations are authorised against what they destroy, not just
   what they target.** Deleting a container must require the permission for
   every area it cascades into — otherwise a narrow grant becomes a wide one
   by going through the parent.

   Concretely: `DELETE /folders/<id>?cascade=true` destroys the test cases
   underneath it, so it requires **Test Cases → Delete**, not merely whatever
   permission covers folders. Likewise a project delete cascades into every
   area, so it requires administrator rather than any single area grant. See
   `folder_deletion_and_testcases.md` for the cascade semantics this rule
   applies to.

## 9. Enforcement

**The gateway is the enforcement point**, not the web portal.

The portal hiding a button is UX, not security — CMS and gateway endpoints
are reachable directly. Every authorisation decision must be made server-side
on the request path.

### 9.1 Trust boundary: how permissions reach CMS

**They do not.** CMS and Identity stay permission-agnostic and trust their
caller.

This works because of deployment topology: **in production only the gateway
is externally visible** — CMS and Identity bind to `127.0.0.1` rather than
`0.0.0.0`, so they are unreachable except via the gateway. The gateway is
therefore a genuine chokepoint, and authorisation decided there cannot be
bypassed.

Two consequences worth being explicit about:

- **In development this is not true.** `docker-compose.yml` publishes CMS on
  `6050` and Identity on `5050` (it also sets
  `ITEMS_ENVIRONMENT=development`), so both are directly reachable on a dev
  box. Gateway enforcement is therefore bypassable locally — do not write
  tests that claim to verify authorisation by calling CMS directly, and do
  not treat a dev environment as evidence the boundary holds.
- **The model assumes single-host deployment.** Loopback binding stops
  working the moment services are split across hosts or scaled out. At that
  point real service-to-service authentication becomes necessary.

If defence in depth is wanted before then, the machinery already exists:
`items.shared.api_signature.generate_api_signature` and the `X-Signature`
header are already used for the portal ↔ gateway webhook metadata call. The
same HMAC could be required on gateway → CMS calls, giving a second layer if
the network assumption is ever violated. CMS validates nothing today.

**What CMS should receive is identity, not permissions.** Authorisation stays
at the gateway, but CMS needs to know *who* acted in order to record it —
required by the audit concerns in §10.5 (who purged what, and when). That is
a distinct concern from enforcement and should not be conflated with it.

### 9.2 Project scope must be in the route

For the gateway to authorise a project-scoped permission, it must know which
project the target entity belongs to — **without asking CMS**. Otherwise
every request costs an extra hop and an authorisation decision ends up
downstream of a data lookup.

Current route shapes are inconsistent on this point:

| Route | Project scope in path? | Gateway can authorise? |
| ----- | ---------------------- | ---------------------- |
| `/<int:project_id>/testcases` | Yes | Yes, from the path |
| `/testcases/<int:case_id>` | **No** | **No** — owning project unknown |
| `/testcase_custom_fields/<int:field_id>` | N/A (instance-level) | Yes, admin flag only |

**Decision needed:** entity routes that are project-scoped should carry the
project in the path, e.g. `/projects/<project_id>/testcases/<case_id>`. The
gateway then authorises from the path alone, and CMS verifies only that the
entity genuinely belongs to that project — an integrity check, not an
authorisation decision.

This is cheap to change now and a breaking API change once clients depend on
the current shapes, so it is worth settling before further routes are added.

### 9.3 Immediate gap worth closing early

The `/admin/` routes currently have **no administrator check** — only
`@require_session`. This cannot be fixed before this design lands, because
there is nothing to check against.

**Recommendation:** land §5.1's flag as its own small change ahead of
everything else — a boolean on `user_profile`, set for `admin@localhost`, and
a decorator on the `/admin/` routes. That closes the privilege-escalation gap
without waiting for the full permission model.

### 9.4 Ordering constraint: reader tolerates before writer emits

The portal validates the gateway's session-validate response against a schema
with **`"additionalProperties": False`** (`portal_page_handler.py`). Adding
`is_administrator` to that response therefore **breaks the portal** — schema
validation raises, and every authenticated page renders the internal error
page.

So the rollout order is forced:

| # | Service | Change | Mergeable alone? |
| - | ------- | ------ | ---------------- |
| 1 | Identity | `is_administrator` column + admin seed | Yes |
| 2 | Identity | Report the flag to callers | Yes |
| 3 | Web Portal | *Tolerate* the optional field in the response schema | Yes — behaviour-neutral |
| 4 | Gateway | Capture at login; return it from validate | **Only after 3** |
| 5 | Web Portal | `require_administrator` on `/admin/` routes | Only after 4 |

Step 5 must follow step 4: if the portal enforces before the gateway emits
the flag, failing closed locks administrators out and failing open provides
no security. The `/admin/` gap therefore closes only when the whole chain has
landed, so the steps should not be left half-merged for long.

## 10. Dependencies and open decisions

### 10.1 Soft delete exists only for projects

`awaiting_purge` is on `prj_projects` alone. `tc_test_cases`, `tc_folders`
and `tc_custom_fields` have **hard delete only**. Making `Delete` mean
"soft" everywhere requires adding the flag *and* read-filtering to every
area.

Today this produces an inversion worth fixing: a normal user deleting a test
case is doing something *more* destructive than an admin soft-deleting an
entire project.

**Already agreed elsewhere:** `folder_deletion_and_testcases.md` records the
decision that **test cases get soft/hard delete mirroring projects**, and
that **folders stay hard-delete-only** (a folder is pure organisation —
nothing is lost by deleting the folder itself, only by deleting its
contents). So for the two areas that exist today, this dependency is a
matter of implementation rather than an open design question.

Folders are deliberately **not** an area in the §4 grid for that reason;
folder operations fall under Test Cases, with the cascade rule in §8.6
governing deletes that reach through them.

### 10.2 The sweeper does not exist

Nothing purges. The background task in §6 step 3 is new work, and until it
exists "soft delete" means "hidden forever".

There is also **no restore path** in the code — nothing clears
`awaiting_purge` back to `0`. §4.2 depends on that existing.

### 10.3 Retention period is unspecified

How long between soft delete and automatic purge? Needs a value and a home
(probably Site Settings). No default is proposed here deliberately.

### 10.4 Soft-delete cascade is partly undefined

If a project is soft-deleted, are its test cases hidden too? Currently they
would remain present but orphaned. Reads become inconsistent if this is not
decided.

For **folders**, `folder_deletion_and_testcases.md` already settles the
shape: delete refuses with `409 Conflict` if the folder contains test cases
recursively, and `?cascade=true` overrides. Its open question — whether
`cascade=true` soft- or hard-deletes the test cases underneath — is answered
by this document's model: **soft, with `hard_delete=true` layered on top and
gated by the Purge now capability (§5.2)**. That keeps one consistent rule
rather than two subsystems disagreeing.

What remains open here is the **project → children** case, which no document
yet covers.

Related: purging a project must also delete its `project_members` and
`project_permissions` rows in `identity.db` (no FK will do it).

### 10.5 OPEN: automatic purge vs audit retention

**This is the decision that most needs an answer.**

With an automatic sweeper, Test Results eventually vanish on a timer. For
regulated work the requirement is often the *opposite* — retention
**guarantees** rather than retention **limits**, with execution history kept
as evidence.

Options: exempt some areas (Test Results in particular) from automatic purge
entirely; make Test Results hard delete administrator-only regardless of
grid; and/or log who purged what and when.

Not decided. Needs a call before the sweeper is built.

## 11. Implementation status

The grid above is deliberately designed ahead of the data model. Only Test
Cases is enforceable today — **do not build enforcement for areas that have
no tables**.

| Area | Backing tables | Enforceable now? |
| ---- | -------------- | ---------------- |
| Test Cases | `tc_test_cases`, `tc_folders` | Yes |
| Milestones | — | No |
| Test Runs | — | No |
| Test Plans | — | No |
| Test Reports | — | No |
| Test Results | — | No |

Admin areas (future grid, §5.1):

| Area | Backing | Notes |
| ---- | ------- | ----- |
| Projects | `prj_projects` | Exists, incl. soft delete |
| Testcase Fields | `tc_custom_fields` | Exists; admin UI built |
| Site Settings | — | Portal page is a placeholder; no backend |
| Users | `user_profile` | Exists; identity exposes auth + health routes only, no user-management API |

Note: `Test Results` above means *test execution results*. It is unrelated to
`testcase_field_values`, which stores custom field values on test case
definitions.

## 12. Migration notes

- **There is no migration path at all.** `db_builder.open_db()` refuses to
  run if the target file already exists, and the table DDL uses
  `CREATE TABLE IF NOT EXISTS`. So an existing `identity.db` will neither be
  altered nor rebuilt — it simply keeps the old schema and any query
  referencing `is_administrator` will fail against it.

  **Project decision:** schema migration is deliberately out of scope until
  public beta. Until then, schema changes are applied by **deleting and
  rebuilding** the development database, and that is an accepted cost — the
  README already states ITEMS cannot be run from `main`.

  A real migration mechanism is required before the first release that
  upgrades an existing install in place. Not before.
- The db builder gives `admin@localhost` `is_administrator = 1` on a fresh
  install, otherwise nobody can administer it. New users default to `0`.

---

## Decisions log

Settled during design discussion:

| Decision | Rationale |
| -------- | --------- |
| Add and Modify are a **single** grant | A role that can add but not modify was not identifiable; splitting would double the matrix with a column always set the same way |
| Add/Modify implies Read (locked) | Prevents nonsensical write-without-read states |
| Delete means soft delete | Recoverable by default |
| Delete implies Restore | Restore destroys nothing, so gating it separately is backwards |
| Data Administration grid **dropped** | Purge becomes a background task, so per-area hard-delete ticks are unnecessary |
| Purge now is a **single** admin capability | Per-area purge granularity has no use case |
| `is_administrator` gates admin panel access | Simple bootstrap; sub-grid deferred |
| v1 is **users-only** | Groups are a scale convenience, not a capability requirement; hooks in place so they are additive |
| Roles live in `identity.db` | Rides along with existing session validation; no extra hop per request |
| No negative/deny permissions | Keeps effective access predictable |
