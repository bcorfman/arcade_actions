# Refactor Plan (Module-by-Module)

This plan tracks refactoring in priority order with coverage gates and verification between modules.

## Principles
- Work one module at a time when possible; touch adjacent modules only for required interfaces.
- Add/adjust tests before refactoring if coverage is insufficient or behavior is unclear.
- After each module refactor: run module-focused tests, then run the full suite (CI=true).

## Status Overview
- Baseline captured: coverage report, radon report, refactor-priority-report.md.
- Current full suite status (CI=true): 1946 passed, 4 skipped.

## Module Plan
1) `arcadeactions/base.py`
   - Coverage gate: ensure action lifecycle and conflict detection are fully covered.
   - Refactor: extract repeated logic, reduce long methods.
   - Verify: base/action tests + full suite.

2) `arcadeactions/movement.py` + related conditional modules (`arcadeactions/paths.py`, `arcadeactions/transforms.py`, `arcadeactions/effects.py`, `arcadeactions/callbacks.py`, `arcadeactions/parametric.py`, `arcadeactions/frame_conditions.py`)
   - Coverage gate: add tests for high-CC branches (boundary handling, callbacks, path helpers).
   - Refactor: split complex update logic into small helpers; reduce condition parsing complexity.
   - Verify: conditional tests + full suite.

3) `arcadeactions/dev/visualizer.py`
   - Coverage gate: identify untested pathways and add tests for editor mode, action metadata, selection, and IO boundaries.
   - Refactor: extract long handlers into helpers; reduce cyclomatic complexity in event routing.
   - Verify: focused tests for dev visualizer + full suite.

4) `arcadeactions/visualizer/renderer.py`
   - Coverage gate: add headless rendering tests and shader setup tests using fakes.
   - Refactor: isolate layout, batching, and draw pipeline helpers.
   - Verify: renderer-focused tests + full suite.

5) `arcadeactions/visualizer/attach.py`
   - Coverage gate: strengthen attach/detach, metadata application, and error handling tests.
   - Refactor: split large attach workflows into helpers; limit side effects.
   - Verify: attach-focused tests + full suite.

6) Continue in priority order from `refactor-priority-report.md`:
   - `arcadeactions/dev/palette_window.py`
   - `arcadeactions/formation.py`
   - `arcadeactions/dev/override_panel.py`
   - `arcadeactions/visualizer/event_window.py`
   - `arcadeactions/dev/sync.py`
   - Next items in the report...

## TODOs
- [x] Map tests to `arcadeactions/base.py` and identify coverage gaps.
- [x] Add missing tests for `arcadeactions/base.py` before refactor.
- [x] Refactor `arcadeactions/base.py` in small, test-validated chunks.
- [ ] Map tests to `arcadeactions/dev/visualizer.py` and identify coverage gaps.
- [ ] Add missing tests for `arcadeactions/dev/visualizer.py` before refactor.
- [ ] Refactor `arcadeactions/dev/visualizer.py` in small, test-validated chunks.
- [x] Map tests to conditional action modules and identify coverage gaps.
- [x] Refactor conditional action modules in small, test-validated chunks.
- [ ] Repeat for `arcadeactions/visualizer/renderer.py` with coverage gate.
- [ ] Repeat for `arcadeactions/visualizer/attach.py` with coverage gate.
- [ ] Work through remaining modules in report order.
