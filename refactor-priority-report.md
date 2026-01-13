# Refactoring Priority Report

This report ranks modules by refactoring priority based on:
- Cyclomatic Complexity (CC)
- Test Coverage
- Source Lines of Code (SLOC)

**Score Formula:** `(ΣCC) × (1 + 4×U) × log(1 + SLOC)`
where U is the uncovered fraction (1 - coverage/100).

| Rank | Module | Score | SLOC | ΣCC | MaxCC | Funcs | Cov% |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `actions/dev/visualizer.py` | 6984.35 | 1515 | 386.0 | 55.0 | 39 | 63.2 |
| 2 | `actions/conditional.py` | 3669.24 | 1601 | 345.0 | 30.0 | 105 | 89.0 |
| 3 | `actions/visualizer/renderer.py` | 2907.57 | 496 | 103.0 | 35.0 | 16 | 11.3 |
| 4 | `actions/visualizer/attach.py` | 2576.64 | 557 | 116.0 | 35.0 | 13 | 37.2 |
| 5 | `actions/formation.py` | 1918.20 | 663 | 192.0 | 30.0 | 13 | 86.6 |
| 6 | `actions/base.py` | 1813.34 | 514 | 197.0 | 37.0 | 48 | 88.1 |
| 7 | `actions/visualizer/event_window.py` | 1306.66 | 252 | 53.0 | 9.0 | 17 | 13.6 |
| 8 | `actions/dev/tests/test_sync_cell_overrides.py` | 1243.42 | 159 | 49.0 | 12.0 | 9 | ? |
| 9 | `actions/dev/sync.py` | 1095.29 | 396 | 109.0 | 41.0 | 13 | 83.0 |
| 10 | `actions/pattern.py` | 1022.90 | 665 | 128.0 | 23.0 | 20 | 94.3 |