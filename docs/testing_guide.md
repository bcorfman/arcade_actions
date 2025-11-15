"""Testing Guide for arcade_actions

This guide describes how to exercise the frame-driven ArcadeActions test suite.
"""

# Testing Guide

## Philosophy

ArcadeActions treats `Action.update_all()` as the single metronome. Tests never depend
on wall-clock time; they advance discrete frames and assert on deterministic state.
The suite intentionally stays lean (≈700 tests) so every case either proves core frame
math or provides a smoke/regression check for a helper. When a behavior involves many
permutations (patterns, easing, visualizers) we keep one focused smoke test per
scenario instead of entire matrices.

## Core Fixtures

`tests/conftest.py` exposes shared helpers that keep the global frame counter
consistent:

```python
import pytest
import arcade

from actions import Action

@pytest.fixture(autouse=True)
def cleanup_actions():
    """Reset global action state between tests."""
    Action.stop_all()
    Action._frame_counter = 0
    yield
    Action.stop_all()
    Action._frame_counter = 0

@pytest.fixture
def test_sprite() -> arcade.Sprite:
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite
```

The cleanup fixture is autouse so individual tests rarely need teardown logic. If a
test mutates other global state (environment variables, debug observers, sprite pools)
it should perform its own cleanup and let `cleanup_actions` manage the Action system.

## Frame Helpers

Every timing assertion uses the primitives from `actions.frame_timing`:

- `after_frames(n)` returns a condition that completes once at frame `n`.
- `every_frames(n, callback)` wraps a callback that fires on frame multiples.
- `within_frames(start, end)` guards logic that must run only inside a band of frames.

Example assertions from `tests/test_frame_timing.py`:

```python
from actions import Action, move_until
from actions.frame_timing import after_frames

def test_after_frames_drives_move_until(test_sprite):
    action = move_until(
        test_sprite,
        velocity=(10, 0),
        condition=after_frames(5),
        tag="frame-check",
    )

    for _ in range(4):
        Action.update_all(1 / 60)
        test_sprite.update()

    assert not action.done
    assert test_sprite.center_x == 140  # 4 frames of motion

    Action.update_all(1 / 60)
    test_sprite.update()
    assert action.done
    assert test_sprite.center_x == 140  # frame 5 completed before movement
```

## Composition Tests

Sequence and parallel helpers are validated with the same primitives.
`tests/test_composite.py` uses short frame windows to prove ordering rather than
sleeping:

```python
from actions import Action, DelayUntil, MoveUntil, sequence
from actions.frame_timing import after_frames

def test_sequence_runs_actions_in_order(test_sprite):
    seq = sequence(
        DelayUntil(after_frames(3)),
        MoveUntil((5, 0), after_frames(4)),
    )

    seq.apply(test_sprite, tag="sequence-smoke")
    for _ in range(3):  # finish delay
        Action.update_all(1 / 60)

    assert seq.current_index == 1
    assert test_sprite.change_x == 5
```

Parallel behavior follows the same pattern with `parallel(...)` and checks that each
sub-action receives updates on the same frame.

## Specialized Suites

- `tests/test_frame_actions.py` covers `BlinkUntil`, `CallbackUntil`, `DelayUntil`,
  `Ease`, `TweenUntil`, and `CycleTexturesUntil` using explicit frame counts.
- `tests/test_frame_timing.py` exercises the primitives themselves along with
  `Action.current_frame()` semantics, including pause behavior.
- `tests/test_pattern_smoke.py` keeps a single regression test per pattern factory
  (`create_zigzag_pattern`, `create_wave_pattern`, `create_spiral_pattern`,
  `create_bounce_pattern`). These smoke tests verify the frame-first parameters
  (`velocity`, `width`, `height`, `after_frames`) without re-running the large matrix
  from the legacy suite.
- `tests/test_ease_smoke.py` replaces the legacy easing battery with a minimal check
  that guarantees easing curves read `frames_completed / total_frames`.

## Writing New Tests

1. **Drive behavior with frames.** Iteratively call `Action.update_all(1/60)` (or
   `Action.update_all(0)` if you only need to advance bookkeeping) and assert when the
   boundary frame hits.
2. **Favor smoke coverage for helpers.** If a helper accepts multiple optional flags,
   choose the most representative combination. Public API samples cover the rest, so
   the suite remains lean.
3. **Reset external state.** Any test that mutates globals beyond the Action system
   should patch or monkeypatch within the test and restore the previous value.
4. **Validate pause safety.** When testing pause/resume, wrap `Action.pause_all()` and
   `Action.resume_all()` inside the frame loop and assert `Action.current_frame()`
   advances only when updates run.

## Running the Suite

Always invoke tests through uv to ensure the managed environment is active:

```bash
uv run python -m pytest
```

Use `-k` filters or direct paths for faster iterations:

```bash
uv run python -m pytest tests/test_frame_timing.py -k after_frames
```

## Troubleshooting

- **Action counter drift:** confirm your test or fixture resets `Action._frame_counter`
  before and after execution.
- **Arcade resources:** when instantiating sprites in tight loops, create them with
  `arcade.SpriteSolidColor` to bypass texture IO.
- **Long-running sequences:** prefer `after_frames` conditions instead of explicit
  loops inside actions. This keeps assertions readable and gives the debugger
  deterministic stepping behavior.

The suite must remain deterministic under debugger pause/step. When adding new tests,
verify they complete successfully when breakpoints interrupt `Action.update_all()` so
the frame-based API remains intuitive during debugging.

