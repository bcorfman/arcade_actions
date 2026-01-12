# Refactoring Priority Report

This report ranks modules by refactoring priority based on:
- Cyclomatic Complexity (CC)
- Test Coverage
- Source Lines of Code (SLOC)

**Score Formula:** `(ΣCC) × (1 + 4×U) × log(1 + SLOC)`
where U is the uncovered fraction (1 - coverage/100).

| Rank | Module | Score | SLOC | ΣCC | MaxCC | Funcs | Cov% |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `actions/dev/visualizer.py` | 13952.91 | 1487 | 382.0 | 55.0 | 38 | ? |
| 2 | `actions/conditional.py` | 3669.24 | 1601 | 345.0 | 30.0 | 105 | 89.0 |
| 3 | `actions/visualizer/attach.py` | 3668.13 | 557 | 116.0 | 35.0 | 13 | ? |
| 4 | `actions/visualizer/renderer.py` | 3197.42 | 496 | 103.0 | 35.0 | 16 | ? |
| 5 | `actions/dev/palette_window.py` | 2023.99 | 255 | 73.0 | 13.0 | 24 | ? |
| 6 | `actions/formation.py` | 1918.20 | 663 | 192.0 | 30.0 | 13 | 86.6 |
| 7 | `actions/base.py` | 1813.34 | 514 | 197.0 | 37.0 | 48 | 88.1 |
| 8 | `actions/dev/override_panel.py` | 1803.65 | 172 | 70.0 | 12.0 | 18 | ? |
| 9 | `actions/dev/boundary_overlay.py` | 1575.26 | 174 | 61.0 | 31.0 | 12 | ? |
| 10 | `actions/visualizer/event_window.py` | 1466.35 | 252 | 53.0 | 9.0 | 17 | ? |
| 11 | `actions/dev/sync.py` | 1313.29 | 396 | 109.0 | 41.0 | 13 | 74.7 |
| 12 | `actions/dev/tests/test_sync_cell_overrides.py` | 1243.42 | 159 | 49.0 | 12.0 | 9 | ? |
| 13 | `actions/pattern.py` | 1022.90 | 665 | 128.0 | 23.0 | 20 | 94.3 |
| 14 | `actions/dev/tests/test_arrange_override_collision.py` | 934.57 | 106 | 40.0 | 26.0 | 4 | ? |
| 15 | `actions/dev/templates.py` | 864.13 | 194 | 52.0 | 13.0 | 6 | 46.2 |
| 16 | `actions/dev/create_level.py` | 692.54 | 168 | 27.0 | 10.0 | 6 | ? |
| 17 | `actions/composite.py` | 690.28 | 259 | 93.0 | 11.0 | 34 | 91.6 |
| 18 | `actions/dev/reload.py` | 677.26 | 257 | 86.0 | 12.0 | 19 | 89.5 |
| 19 | `actions/group_state.py` | 593.74 | 199 | 51.0 | 11.0 | 10 | 70.1 |
| 20 | `actions/dev/selection.py` | 540.56 | 109 | 23.0 | 6.0 | 9 | ? |
| 21 | `actions/visualizer/timeline.py` | 350.55 | 147 | 54.0 | 52.0 | 3 | 92.5 |
| 22 | `actions/visualizer/instrumentation.py` | 341.93 | 190 | 38.0 | 11.0 | 14 | 82.2 |
| 23 | `actions/axis_move.py` | 297.21 | 269 | 34.0 | 8.0 | 10 | 86.0 |
| 24 | `actions/group.py` | 266.60 | 131 | 26.0 | 7.0 | 9 | 72.5 |
| 25 | `actions/visualizer/guides.py` | 238.49 | 150 | 46.0 | 9.0 | 19 | 99.2 |
| 26 | `actions/display.py` | 234.56 | 139 | 34.0 | 6.0 | 10 | 90.1 |
| 27 | `actions/visualizer/overlay.py` | 222.50 | 116 | 39.0 | 8.0 | 16 | 95.0 |
| 28 | `actions/dev/watch.py` | 198.50 | 124 | 37.0 | 7.0 | 13 | 97.2 |
| 29 | `actions/presets/entry_paths.py` | 168.75 | 127 | 12.0 | 4.0 | 7 | 52.5 |
| 30 | `actions/visualizer/controls.py` | 144.31 | 118 | 28.0 | 10.0 | 9 | 98.0 |