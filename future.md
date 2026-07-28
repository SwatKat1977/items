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

## CMS: system custom fields can't have partial updates

**Where:** `items_cms.repositories.testcase_custom_fields_repository.
update_custom_field` rejects *any* update to a field with
`entry_type == "system"` outright:

```python
if entry_type == "system":
    return None
```

**Context:** the web portal's Case Fields admin page
(`admin_customisations_page_handler.py`) already has UI and payload-building
logic (`case_field_modify`, `_build_system_field_payload`) written on the
assumption that a system field's `enabled` (active) state and project
assignment *can* be changed, while every other attribute (name, system
name, type, description, default value, required) stays locked. Right now
every such request fails with `400 "System custom fields cannot be
modified"` — the portal UI shows the error correctly, but the feature
itself can't succeed yet.

**Fix:** a teammate is picking this up as a separate CMS-side PR — allow
`update_custom_field` to accept changes to `enabled` and project
assignment for system fields specifically, while continuing to reject
changes to the immutable attributes. The portal side is already built to
match this contract and shouldn't need further changes once CMS supports it.
