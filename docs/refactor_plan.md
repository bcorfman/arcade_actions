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
1) `actions/base.py`
   - Coverage gate: ensure action lifecycle and conflict detection are fully covered.
   - Refactor: extract repeated logic, reduce long methods.
   - Verify: base/action tests + full suite.

2) `actions/movement.py` + related conditional modules (`actions/paths.py`, `actions/transforms.py`, `actions/effects.py`, `actions/callbacks.py`, `actions/parametric.py`, `actions/frame_conditions.py`)
   - Coverage gate: add tests for high-CC branches (boundary handling, callbacks, path helpers).
   - Refactor: split complex update logic into small helpers; reduce condition parsing complexity.
   - Verify: conditional tests + full suite.

3) `actions/dev/visualizer.py`
   - Coverage gate: identify untested pathways and add tests for editor mode, action metadata, selection, and IO boundaries.
   - Refactor: extract long handlers into helpers; reduce cyclomatic complexity in event routing.
   - Verify: focused tests for dev visualizer + full suite.

4) `actions/visualizer/renderer.py`
   - Coverage gate: add headless rendering tests and shader setup tests using fakes.
   - Refactor: isolate layout, batching, and draw pipeline helpers.
   - Verify: renderer-focused tests + full suite.

5) `actions/visualizer/attach.py`
   - Coverage gate: strengthen attach/detach, metadata application, and error handling tests.
   - Refactor: split large attach workflows into helpers; limit side effects.
   - Verify: attach-focused tests + full suite.

6) Continue in priority order from `refactor-priority-report.md`:
   - `actions/dev/palette_window.py`
   - `actions/formation.py`
   - `actions/dev/override_panel.py`
   - `actions/visualizer/event_window.py`
   - `actions/dev/sync.py`
   - Next items in the report...

## TODOs
- [x] Map tests to `actions/base.py` and identify coverage gaps.
- [x] Add missing tests for `actions/base.py` before refactor.
- [x] Refactor `actions/base.py` in small, test-validated chunks.
- [ ] Map tests to `actions/dev/visualizer.py` and identify coverage gaps.
- [ ] Add missing tests for `actions/dev/visualizer.py` before refactor.
- [ ] Refactor `actions/dev/visualizer.py` in small, test-validated chunks.
- [x] Map tests to conditional action modules and identify coverage gaps.
- [x] Refactor conditional action modules in small, test-validated chunks.
- [ ] Repeat for `actions/visualizer/renderer.py` with coverage gate.
- [ ] Repeat for `actions/visualizer/attach.py` with coverage gate.
- [ ] Work through remaining modules in report order.
