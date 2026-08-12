# User Roles & Permissions — Design

**Status:** Draft for review. Partially implemented (see §11).
**Scope:** v1 is users-only (no groups) and covers the General permission
grid, the `is_administrator` flag, the delete/purge lifecycle, and user
management (create, modify, deactivate).

**Note on scope:** this document has grown to cover user management as well
as roles and permissions. If it continues to expand it should be renamed
— `user_management_design.md` or `identity_design.md` are candidates.

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

## 4. The General grid (per role)

**The grid lives on named roles, not directly on a membership.** An
administrator defines a role once (e.g. "Tester"), sets its grid, and
*assigns* that role to memberships - editing the role updates everyone who
holds it, rather than needing to be repeated per person. See §7 for why:
raw per-membership checkboxes were the original design, revised after
comparing against how tools like TestRail actually work in practice - a
name you assign is far more maintainable at any real team size than
re-ticking the same boxes for every new membership.

For each **area**, a role is granted any combination of:

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
`Add/Modify` remains set**. This applies to a role's own grid - it says
nothing about the *effective* result once roles are combined via
membership and group union (§8), which can only ever add further access,
never remove it.

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
- **Per-area `Read`** (via the member's assigned role) — what is visible
  *inside* it.

A member with **no role assigned at all** sees the project shell and no
content. That is a valid (if unusual) state, not an error - see §7 for why
`project_members.role_id` is nullable rather than required.

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

### 5.3 User management

User management is an administrative capability — only users with
`is_administrator = 1` can create, modify, or deactivate other users.

#### 5.3.1 Create user

An administrator provides:

| Field | Notes |
| ----- | ----- |
| `email_address` | Unique; used as the login identifier. Not changeable after creation (see §5.3.4) |
| `full_name` | Display in reports and audit trails |
| `display_name` | Shown in the UI; may differ from full name |
| `password` | Optional. If omitted, a 16-character cryptographically secure password is generated server-side and returned once in the response — it is never stored in plaintext and cannot be retrieved again. The administrator communicates it to the user out of band. |
| `is_administrator` | Defaults to `false` |

`account_status` is set to `ACTIVE` on creation. `insertion_date` and
`logon_type` are set server-side and are not supplied by the form.

**Open:** is there a self-registration flow (user signs themselves up), or
is all account creation admin-only? v1 assumes admin-only.

#### 5.3.2 Modify user

An administrator may change:

| Field | Notes |
| ----- | ----- |
| `full_name` | Freely editable |
| `display_name` | Freely editable |
| `is_administrator` | Toggle; see constraint below |
| `account_status` | Active ↔ Disabled (see §5.3.3) |

**Constraint:** no change may leave zero active administrators. The server
rejects any update to `is_administrator` or `account_status` that would
reduce the count of active administrator accounts to zero — regardless of
which user is making the request and which user is the target. This is
enforced at the service layer via a `COUNT` query before writing. The UI
should surface the same constraint, but the endpoint is authoritative.

`email_address` is not editable after creation (see §5.3.4).
`password` is not modified here — it has its own flow (§5.3.5).

#### 5.3.3 Deactivate vs delete

| Action | Effect | Reversible? |
| ------ | ------ | ----------- |
| **Deactivate** (`account_status = DISABLED`) | User cannot log in; existing sessions are invalidated at next validate call; membership rows are retained | Yes — admin re-activates |
| **Delete** | User record and auth details removed; membership rows cascade-deleted via FK | No |

**v1 decision:** expose deactivation only. Hard delete of a user is
deferred — it raises questions about audit trails and orphaned data (test
case history authored by that user) that are out of scope for v1.

The `AccountStatus.DISABLED` value already exists; no schema change is
needed.

#### 5.3.4 Email address immutability

`email_address` doubles as the login identifier and is embedded in session
cookies (`items_user`). Allowing it to change mid-session would invalidate
the cookie without the user knowing. Keeping it immutable avoids that class
of problem entirely.

If a rename is ever needed in a future version, it requires a coordinated
change: new email, forced logout, re-login.

#### 5.3.5 Password management

Two flows:

1. **Admin resets password** — administrator sets a new password on behalf
   of a user (e.g. account recovery). The gateway sends a notification email
   to the user's registered address after a successful reset, including a
   direct link to the portal login page. Email delivery is best-effort —
   a failure to send does not roll back the password change.

   Email is delivered via the gateway's `SmtpEmailService`. For production,
   Brevo is the recommended relay: `host = smtp-relay.brevo.com`, `port = 587`,
   `use_tls = true`, `from_address` must be a verified Brevo sender address.
   For local development, a local `aiosmtpd` relay on `localhost:1025`
   (no TLS, no credentials) is used by default.

2. **User changes own password** — a user changes their own password after
   supplying their current password first. This does not require
   administrator access.

**Open:** force-change-on-first-login flag. Not in the current schema.
Deferred until there is a clear need.

#### 5.3.6 List users

The Users & Roles admin page shows all `user_profile` rows. v1 requires no
filtering or pagination — acceptable at low user counts. Add when needed.

Columns shown: display name, email address, account status, is_administrator.

#### 5.3.7 Identity service routes required

| Method | Route | Action |
| ------ | ----- | ------ |
| `GET` | `/users` | List all users |
| `POST` | `/users` | Create user |
| `GET` | `/users/<id>` | Get single user |
| `PATCH` | `/users/<id>` | Modify user (name, status, is_administrator) |
| `POST` | `/users/<id>/password` | Reset password (admin) |
| `POST` | `/users/me/password` | Change own password |

All routes except `POST /users/me/password` are admin-only and must be
enforced at the gateway. `POST /users/me/password` requires a valid session
and the current password in the request body.

**Note:** `POST /users/profile` (used by the gateway at login to retrieve
`is_administrator`) already exists. It is a separate, internal route and is
not part of this user-management surface.

---

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

-- Named, reusable permission bundles  [IMPLEMENTED on identity_roles_db_update]
CREATE TABLE roles (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

-- Per-area permissions for a role  [IMPLEMENTED on identity_roles_db_update]
-- Replaces an earlier, rejected design where this table was keyed by
-- member_id (i.e. raw permissions set directly per membership, no reusable
-- role in between). Revised before any code was built on it, after
-- comparing against how established tools (e.g. TestRail) actually manage
-- this at real team sizes: a name you assign and occasionally redefine
-- beats re-ticking the same boxes for every new membership.
CREATE TABLE role_permissions (
    role_id        INTEGER NOT NULL,
    area           TEXT    NOT NULL,   -- 'test_cases', 'milestones', ...
    can_read       BOOLEAN NOT NULL DEFAULT 0,
    can_add_modify BOOLEAN NOT NULL DEFAULT 0,
    can_delete     BOOLEAN NOT NULL DEFAULT 0,

    PRIMARY KEY (role_id, area),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,

    -- Invariant from §4.1, enforced at the database level
    CHECK (can_add_modify = 0 OR can_read = 1)
);

-- Project membership (the access gate) + assigned role
-- [IMPLEMENTED on identity_roles_db_update]
CREATE TABLE project_members (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    principal_type TEXT    NOT NULL CHECK (principal_type IN ('user','group')),
    principal_id   INTEGER NOT NULL,
    project_id     INTEGER NOT NULL,   -- cms.db prj_projects(id); no FK possible
    -- NULL = on the project, no role assigned yet (see §4.3) - deliberately
    -- not required, so onboarding-in-progress is representable rather than
    -- forcing a placeholder "no access" role into existence.
    role_id        INTEGER,
    UNIQUE (principal_type, principal_id, project_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
);
```

### 7.1 Three deliberate design hooks

**`principal_type` / `principal_id` instead of a bare `user_id`.** In v1
every row is `('user', <id>)`. This costs one column now and means groups can
be added later *without migrating the central membership table or touching
any query that reads it*.

**Areas are rows, not columns.** `area` as a text key means adding
Milestones, Test Runs and the rest requires no schema change — important
given only Test Cases exists today (§9).

**Membership and role assignment are separate tables, not one.**
`project_members` stays "am I on this project at all", `role_permissions`
stays "what does this role grant" - joined only through a nullable
`project_members.role_id`. Collapsing them into a single row from the
start would have made the "member, no role yet" state (§4.3) either
impossible to represent or dependent on a placeholder role existing,
neither of which is necessary given they cost nothing extra kept apart.

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

    role_ids = {m.role_id for m in memberships if m.role_id is not None}
    rows = role_permissions WHERE role_id IN role_ids AND area = area
    return union of flags across rows                          # most permissive wins
```

Rules, stated explicitly because these are where authorisation bugs live:

1. **Union, most-permissive-wins.** Effective permissions are the union of
   all matching grants. This explicitly includes the case of a direct
   membership and a group membership resolving to different roles on the
   same project: **neither supersedes or caps the other** - a narrower
   direct role never limits what a broader group role grants, and vice
   versa. The union happens on the *resolved grid* (each role's
   `can_read`/`can_add_modify`/`can_delete` per area, OR'd together), not on
   role names - "Tester ∪ Lead" isn't a third role, it's whatever their two
   grids combine to. One consequence worth being explicit about: there is
   **no way to cap a user below what a group they belong to already
   grants** - the only lever for that is not putting them in the group.
2. **No negative permissions.** There are no "deny" grants. They make
   effective access genuinely hard to reason about and are the classic source
   of "why can't this user do X". This is also why there is no "default
   role" concept (contrast with tools that apply a site-wide default access
   level, overridable per project) - a default would mean implicit access
   nobody explicitly granted, which is the same problem in a different
   shape.
3. **`account_status = DISABLED` short-circuits everything**, regardless of
   any grant.
4. **`is_administrator` implies everything** in v1.
5. **No membership means no access** — not "membership with empty
   permissions". A membership with no role assigned (`role_id IS NULL`) is
   the same as no matching rows in `role_permissions` - it resolves to no
   access for that source, same outcome as rule 5 already describes, just
   reached one step later.
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

### 9.2 Project scope must be in the request

For the gateway to authorise a project-scoped permission, it must know which
project the target entity belongs to — **without asking CMS**. Otherwise
every request costs an extra hop and an authorisation decision ends up
downstream of a data lookup.

Current route shapes are inconsistent on this point:

| Route | Project scope in the request? | Gateway can authorise? |
| ----- | ------------------------------ | ---------------------- |
| `/<int:project_id>/testcases` | Yes, in the path | Yes |
| `/testcases/<int:case_id>` | **No** | **No** — owning project unknown |
| `/testcase_custom_fields/<int:field_id>` | N/A (instance-level) | Yes, admin flag only |

**Decision: `project_id` travels as an explicit parameter on entity routes,
not nested in the path.** `GET /testcases/<case_id>?project_id=<id>` for
reads; a `project_id` body field for writes (`PATCH`/`DELETE`). The gateway
authorises from that parameter directly - no extra hop - and CMS verifies
only that the entity genuinely belongs to the stated project (an integrity
check, not an authorisation decision), 404ing on a mismatch rather than
trusting the caller's claim.

**Nested path (`/projects/<project_id>/testcases/<case_id>`) was
considered and rejected.** Nesting is the right call when a child's ID
isn't meaningful without its parent (GitHub issue numbers restart at 1 per
repo, so the repo *must* be in the path to identify one). It's not the
right call here: a testcase `id` is a single globally-unique primary key
across `tc_test_cases`, not scoped per project, so nesting would add a path
segment without adding anything needed to identify the resource. The
existing route shapes already draw this line correctly without anyone
having decided it on purpose - `/<project_id>/testcases` (a list, genuinely
scoped to its parent) is nested, `/testcases/<case_id>` (a single entity,
already globally identified) is flat. The explicit-parameter approach
extends that same line to authorisation instead of abandoning it.

This also matches precedent already in the codebase rather than
introducing a new mechanism: `POST /testcases` already requires
`project_id` in its body (`add_testcase_handler.py`), and
`DELETE /web/projects/<id>?hard_delete=true` already puts a meaningful
parameter on a `DELETE` request as a query string, not a body field.

`testcase_custom_fields` needs no change - those are instance-wide
definitions, not per-project, so "N/A" in the table above is correct as
is, not a gap to close.

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

Related: purging a project must also delete its `project_members` rows in
`identity.db` (no FK will do it - `project_id` isn't a real foreign key
across the database boundary, see §7). `role_permissions` rows are *not*
project-scoped and don't need cleaning up this way - a role is a reusable
definition, not tied to any one project, and deleting a membership row
doesn't touch the role it pointed to.

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

## 10.6 User accounts are deactivated, never deleted

**Decision: there is no hard delete for user accounts.** Accounts are
deactivated via `account_status`, which already models `DISABLED = 0` /
`ACTIVE = 1`. No `DELETE` route is offered, so the API never promises
something that would later have to be withdrawn.

### Why

Users are unlike other records: they are referenced by *history* — who
created a test case, who executed a run, who purged something (§10.5).
Removing the row does not remove the reference, it makes the record
unreadable.

Worse, every user reference outside `identity.db` is **cross-database and
unenforced**, so a hard delete would fail *silently* rather than loudly:

| Reference | Location | Enforced |
| --------- | -------- | -------- |
| `user_auth_details.user_id` | `identity.db` | Yes — foreign key, unique |
| `project_members.principal_id` | `identity.db` | No foreign key |
| `User`-type custom field values | `cms.db`, stored as `value TEXT` | No foreign key — impossible across databases |
| Test case ownership | — | Does not exist yet |

No constraint would catch the resulting dangling identifiers; they would
simply render as blanks.

### Erasure: anonymise in place

When a genuine right-to-erasure request must be honoured, the answer is to
**anonymise the existing row, not remove it**: keep the `id`, replace the
personal data (email becomes something like
`deleted-user-<id>@invalid`, names become "Deleted User"), mark the account
deleted and revoke its credentials.

This is preferred over reassigning the user's records to a shared
"Deleted User" tombstone account because:

- Referential integrity is automatic — the `id` never disappears, so nothing
  can dangle, and no cross-database sweep is required.
- History stays **attributable**. Under a shared tombstone, two different
  people's work both becomes "Deleted User" and the record becomes ambiguous.
- It is a single-row update in one database, rather than a rewrite of every
  referencing row across two.
- It frees the original email address for reuse in a controlled way.

To an administrator this looks like deletion; underneath, the identifier
survives.

A tombstone/system account is still worth having, but for a **different
purpose**: owning records that never had a real owner (imported data,
automation, system actions). Not for absorbing deleted users.

### Rejected: a background task that hard-deletes unused accounts

Considered and rejected — deleting a deactivated user after *N* days if they
"own nothing":

- **"Owns nothing" is not cheaply knowable.** Identity would have to query CMS
  (and every future service) for test cases, runs, results and `User`-typed
  field values, breaking the service separation described in §9.1.
- **It races.** The check can pass and a reference be created immediately
  afterwards, with no foreign key to prevent it — producing exactly the
  dangling references this section avoids.
- **It is non-deterministic to the operator.** Two accounts deactivated on the
  same day behave differently depending on whether either happened to author
  anything.
- **It does not satisfy erasure**, which must be acted on promptly when
  requested, not opportunistically. Anonymisation covers that immediately.
- The benefit is a negligible amount of disk, traded against the ability to
  answer "who was this account?" during a later security review.

**A narrower form may be worth revisiting:** permitting hard delete only for
an account that has **never been used** — no successful login and no
`project_members` rows. Both are checkable entirely within `identity.db`, and
a user who has never logged in cannot have authored content elsewhere, so
there is no cross-service query and no race. This requires a `last_login`
column, which does not currently exist, and should be an explicit
administrator action rather than a timed sweep.

Note this is distinct from the purge sweeper in §6, which applies to
soft-deleted projects and test cases. Those are not referenced by history in
the way user accounts are.

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

**Schema status:** `roles`, `role_permissions`, and `project_members`
(with `role_id`) exist in the database as of `identity_roles_db_update` -
but nothing reads or writes them yet. No repository, service, route, or
UI has been built on top of this schema. "Enforceable now" above is about
CMS having the backing tables for an *area*; it doesn't mean the
permission system itself is live.

Admin areas (future grid, §5.1):

| Area | Backing | Notes |
| ---- | ------- | ----- |
| Projects | `prj_projects` | Exists, incl. soft delete |
| Testcase Fields | `tc_custom_fields` | Exists; admin UI built |
| Site Settings | — | Portal page is a placeholder; no backend |
| Users | `user_profile` | **Implemented** — all six routes from §5.3.7 are live on the identity service (`identity_user_management` branch) |

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
| `project_id` is an explicit parameter, not a nested path segment (§9.2) | Testcase `id`s are already globally unique, so nesting adds a path segment without adding anything needed to identify the resource; matches precedent already in the codebase (`POST /testcases` body, `DELETE /projects/<id>?hard_delete=` query) |
| Permissions are granted via **named, reusable roles** (§4/§7), not raw checkboxes on each membership | Raw per-membership grants were the original design; revised before any code was built on it, after comparing against how real tools (TestRail) manage this at team scale - editing one role definition beats re-ticking the same boxes on every membership that needs it |
| `project_members` and role assignment stay **separate tables** (§7.1), joined by a nullable `role_id` | Keeps "am I on this project" distinct from "what can I do", and represents "member, no role assigned yet" as a natural state rather than requiring a placeholder role |
| No site-wide default/fallback role | Would mean implicit access nobody explicitly granted - the same problem as a deny-permission in a different shape (§8 rule 2), just inverted |
| Group and direct role grants are strictly additive - **neither supersedes the other** (§8 rule 1) | Consistent with "no negative permissions" - allowing one grant to cap another requires a deny concept, which was already rejected for making effective access hard to reason about |
