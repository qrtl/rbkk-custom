This module adds a third layout option for the Locations report (*Inventory >
Reporting > Locations*), giving selected non-managers a read-only view of the
manager layout.

Depending on the user's groups, the Locations report list view resolves to:

- Stock managers: the existing editable manager layout (unchanged).
- Non-managers in the new group *Locations Report: Manager Layout (Read-only)*:
  a read-only copy of the manager layout, so they see the richer manager column
  set (and its extension columns, such as expiration date) without being able to
  create, edit or delete records.
- All other users: the standard read-only layout (unchanged).
