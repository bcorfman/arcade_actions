# Refactoring Priority Report

This report ranks modules by refactoring priority based on:
- Cyclomatic Complexity (CC)
- Test Coverage
- Source Lines of Code (SLOC)

**Score Formula:** `(ΣCC) × (1 + 4×U) × log(1 + SLOC)`
where U is the uncovered fraction (1 - coverage/100).

| Rank | Module | Score | SLOC | ΣCC | MaxCC | Funcs | Cov% |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `actions/dev/visualizer.py` | 5808.93 | 1520 | 387.0 | 55.0 | 40 | 73.8 |
| 2 | `actions/formation.py` | 1757.13 | 628 | 173.0 | 30.0 | 14 | 85.6 |
| 3 | `actions/visualizer/attach.py` | 1665.98 | 582 | 118.0 | 35.0 | 14 | 69.6 |
| 4 | `actions/base.py` | 1592.98 | 547 | 202.0 | 37.0 | 55 | 93.7 |
| 5 | `actions/visualizer/renderer.py` | 1182.96 | 496 | 103.0 | 35.0 | 16 | 78.8 |
| 6 | `actions/dev/sync.py` | 1106.08 | 395 | 110.0 | 41.0 | 14 | 83.0 |
| 7 | `actions/pattern.py` | 1002.23 | 670 | 127.0 | 23.0 | 20 | 94.7 |
| 8 | `actions/dev/palette_window.py` | 742.22 | 259 | 74.0 | 13.0 | 24 | 79.9 |
| 9 | `actions/dev/override_panel.py` | 721.46 | 172 | 70.0 | 12.0 | 18 | 75.0 |
| 10 | `actions/dev/reload.py` | 668.58 | 257 | 86.0 | 12.0 | 19 | 90.0 |
| 11 | `actions/dev/templates.py` | 664.72 | 194 | 52.0 | 13.0 | 6 | 64.4 |
| 12 | `actions/composite.py` | 640.70 | 253 | 91.0 | 11.0 | 34 | 93.2 |
| 13 | `actions/dev/boundary_overlay.py` | 631.74 | 174 | 59.0 | 31.0 | 11 | 73.2 |
| 14 | `actions/group_state.py` | 593.74 | 199 | 51.0 | 11.0 | 10 | 70.1 |
| 15 | `actions/_movement_bounds.py` | 548.46 | 289 | 65.0 | 14.0 | 12 | 87.8 |
| 16 | `actions/effects.py` | 503.23 | 299 | 61.0 | 14.0 | 24 | 88.8 |
| 17 | `actions/visualizer/event_window.py` | 489.81 | 252 | 53.0 | 9.0 | 17 | 83.2 |
| 18 | `actions/_movement_runtime.py` | 308.82 | 273 | 32.0 | 11.0 | 7 | 82.0 |
| 19 | `actions/visualizer/timeline.py` | 304.28 | 171 | 55.0 | 52.0 | 4 | 98.1 |
| 20 | `actions/transforms.py` | 286.09 | 180 | 40.0 | 10.0 | 18 | 90.6 |
| 21 | `actions/axis_move.py` | 277.77 | 274 | 34.0 | 8.0 | 10 | 88.6 |
| 22 | `actions/visualizer/instrumentation.py` | 276.23 | 268 | 44.0 | 11.0 | 17 | 96.9 |
| 23 | `actions/group.py` | 266.60 | 131 | 26.0 | 7.0 | 9 | 72.5 |
| 24 | `actions/display.py` | 234.56 | 139 | 34.0 | 6.0 | 10 | 90.1 |
| 25 | `actions/callbacks.py` | 231.28 | 132 | 36.0 | 14.0 | 12 | 92.2 |
| 26 | `actions/visualizer/guides.py` | 230.79 | 150 | 46.0 | 9.0 | 19 | 100.0 |
| 27 | `actions/movement.py` | 213.42 | 153 | 36.0 | 6.0 | 17 | 95.6 |
| 28 | `actions/visualizer/overlay.py` | 200.44 | 116 | 39.0 | 8.0 | 16 | 98.0 |
| 29 | `actions/dev/watch.py` | 198.50 | 124 | 37.0 | 7.0 | 13 | 97.2 |
| 30 | `actions/dev/create_level.py` | 193.49 | 177 | 27.0 | 12.0 | 6 | 90.4 |