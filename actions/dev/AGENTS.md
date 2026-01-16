Scope: DevVisualizer tools.

Rules:
- Edit mode stores actions as metadata; no `action.apply()` in edit mode.
- Presets return unbound Actions; store `_action_configs` metadata.
- BoundaryGizmo edits MoveUntil bounds via `set_bounds()`.

Details: see `actions/dev/README.md`.
