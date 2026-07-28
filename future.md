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

## ~~CMS: system custom fields can't have partial updates~~ (resolved)

Fixed on `cms_relax_system_field_edit`: `update_custom_field` now allows
`enabled` and project assignment to change for system fields, while
`field_name`/`description`/`system_name`/`field_type`/`is_required`/
`default_value` are silently overridden with the field's current stored
values regardless of what's submitted (enforced in the service layer, not
just trusted from the caller). The web portal's Case Fields admin page was
already built to this exact contract and needed no changes.
