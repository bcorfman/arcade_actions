# Frame-Based ArcadeActions Alignment Plan

This plan blends the existing main-branch regression work with the new frame-driven overhaul. It is structured so another agent can pick it up and execute the refactor/test updates end‑to‑end. Tasks are ordered to enable test-first development, avoid dead branches, and keep regressions visible.

---

## 0. Branch Strategy & Baseline

- **Starting point:** Branch off `origin/main` (which already contains the frame-first infrastructure, axis-move rewrite, CI changes, etc.).
- **Keep from patternfix:** Preserve the working `Ease` implementation (frames-based constructor, no `easing_duration` bug) until upstream fixes the regression.
- **Cargo to drop:** Old visualizer integration tests, center-based axis bounds, time-based parametric motions, and duration helpers.

---

## 1. tests-update (first) – Define Desired Frame Behavior

1. **tests/test_conditional.py**

- Rework remaining duration-based expectations so they assert purely on frame counts.
- Add regression cases for `Action.current_frame()`, pause/resume/step determinism, and ensure conditions cloned by `_clone_condition` carry frame metadata.

2. **tests/test_action_instrumentation.py**

- Ensure instrumentation drives the new frame counter and `FrameClock` helper.
- Add coverage proving the debug store receives frame numbers and pauses snapshots when actions pause.

3. **Focused smoke/regression suites**

- Keep the slim versions from main (`tests/test_axis_move.py`, `tests/test_cycle_textures_smoke.py`, `tests/test_display_utils.py`, `tests/test_headless_sprite_list.py`, `tests/test_wave_pattern_timing.py`) but extend where needed to cover pause/resume + step scenarios.
- Add regression files if necessary (e.g., `tests/test_frame_clock.py`) to pin down FrameClock semantics.

Goal: All tests define the target frame-driven API before touching production code. Run `uv run pytest` to confirm failures document the missing functionality.

---

## 2. api-frame-core – Frame Counter & Primitives

1. **actions/base.py**

- Expose `Action.current_frame()` publicly, driven strictly by update calls.
- Introduce a lightweight `FrameClock`/`FrameTicker` (dependency-injected where needed) so helpers can observe/pause/resume consistently.

2. **actions/frame_timing.py**

- Keep `after_frames`, `every_frames`, `within_frames`, but thread FrameClock data through them.
- Ensure helper metadata (`_frame_count`, `_frame_duration_precise`) survives cloning.

3. **actions/helpers.py**

- Remove any legacy wall-clock helpers or aliases. Replace them with wrappers around the frame helpers.

4. **deps/init**

- Update any modules referencing `Action._frame_counter` directly to use the new API.

Dependencies: tests from Step 1 should now pass for the core API.

---

## 3. actions-frame-params – Convert Action Implementations

1. **Axis & motion actions**

- Keep `origin/main` versions of `MoveXUntil`, `MoveYUntil`, and `ParametricMotionUntil` (edge-based bounds, frame duration extraction, velocity-provider refresh).
- Ensure `create_wave_pattern` stores `_frame_duration_precise` for reference data.

2. **Other conditional actions**

- `BlinkUntil`, `CallbackUntil`, `CycleTexturesUntil`, `DelayUntil`, `TweenUntil`, shader/particle actions, easing wrappers, etc., should only accept frame counts (or use converters like `seconds_to_frames()` explicitly).
- Introduce `FrameIntervalCallback` / `FrameTicker` utilities for recurring work, powered by `Action.current_frame()`.
- Emit clear errors when callers pass time-based kwargs (validate inputs).

3. **Easing**

- Retain the working `patternfix` implementation (frame-count parameter) but update docs/tests to clarify usage until main’s regression is fixed.

4. **Cleanup**

- Remove any private wall-clock metadata now that frames are canonical.

---

## 4. Visualizer & Instrumentation

1. **tests/test_visualizer_smoke.py**

- Use the slim attach/detach smoke test from main (no env-var mutation, no sprite creation).

2. **actions/visualizer/** (if touched)

- Ensure instrumentation paths rely on `Action.set_debug_store()` and respect the frame counter.

3. **Debug store**

- Verify `FrameClock` data flows into `DebugDataStore.update_frame()` as expected.

---

## 5. examples-refresh

1. **examples/stars.py (or stars equivalent)**

- Replace blink/tween/ease scheduling with frame helpers so pause/resume/step behave deterministically.

2. **examples/invaders.py**

- Move enemy firing cadence into an action-based frame loop (e.g., `CallbackUntil` wrapping a `FrameIntervalCallback`).
- Confirm global pause stops bullet creation and FrameClock increments only when updates run.

3. **Other demos (optional)**

- Align `examples/space_clutter.py`, `easing_demo.py`, etc., with frame-first semantics where drift still exists.

---

## 6. docs-frame-shift (last)

1. **docs/api_usage_guide.md & docs/prd.md**

- Emphasize the frame-driven mindset, provide conversion tables (`seconds_to_frames`, etc.), and document debugger-friendly behavior.

2. **docs/testing_guide.md**

- Keep the concise frame-centric guide from main; expand only where new helpers (FrameClock, FrameIntervalCallback) need explanation.

3. **docs/VISUALIZER_GUIDE.md & README**

- Reference the new instrumentation patterns, mention snapshots, and clarify that durations are expressed in frames unless explicitly converted.

Only update docs after code/tests are green to avoid contradicting reality.

---

## 7. CI & Tooling Confirmation

- Ensure `.github/workflows/test.yml`, `pyproject.toml`, `uv.lock`, and `util/importing.py` stay aligned with `origin/main`.
- Verify the optional-deps job still passes (needs statemachine extra + Xvfb).

---

## 8. Final QA

1. Run `uv run pytest` (full suite).
2. If possible, run the examples that were modified (`uv run python examples/invaders.py`) to confirm runtime behavior.
3. Document remaining follow-ups (e.g., if upstream fixes `Ease`, schedule replacing the temporary patch).

Deliverables: All tests green, docs updated, and `frame_based.plan.md` can be deleted once tasks are complete.

---

## Verification Checklist

These are the guardrails to confirm the frame-based migration is behaving as expected.

1. **Core APIs**

- Inspect `actions/base.py` to ensure `Action.current_frame()` is public, increments inside `update_all()`, pauses when all actions are paused, and is advanced by `step_all()`.
- Check `actions/frame_timing.py` for `after_frames`, `every_frames`, metadata, and the frame/seconds helpers.
- Review `actions/conditional.py` to confirm all timing metadata is frame-based and no legacy wall-clock helpers remain.

2. **Public Interface**

- `actions/__init__.py` should export the frame helpers (`after_frames`, `every_frames`, `seconds_to_frames`, `frames_to_seconds`, etc.) and omit `duration` from `__all__`.

3. **Tests**

- `uv run pytest tests/test_frame_clock.py -v`
- `uv run pytest tests/test_visualizer_instrumentation.py::TestFrameCounterIntegration -v`
- `uv run pytest tests/test_frame_clock.py tests/test_visualizer_instrumentation.py::TestFrameCounterIntegration tests/test_composite.py::TestSequenceFunction::test_sequence_with_actions_initialization -v`
- `uv run python -m compileall tests`
- `uv run pytest tests/ --co -q | wc -l` (record the current collected-test count for awareness)
- `uv run python -c "from actions.frame_timing import after_frames, seconds_to_frames; from actions import Action; print('Imports OK')"`

4. **Docs & Examples**

- Audit docs and examples to ensure they only describe frame-based helpers (no legacy wall-clock references).

5. **Legacy Duration Removal**

- Confirm the source tree no longer references the legacy wall-clock helper API.

Document any deviations found during the checklist above directly in this plan (with links/paths) so follow-up work is obvious for the next contributor.