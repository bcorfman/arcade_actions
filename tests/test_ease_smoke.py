"""Minimal smoke tests for the Ease wrapper."""

import arcade

from arcadeactions import move_until
from arcadeactions.easing import Ease


def _step_frames(count: int) -> None:
    from arcadeactions import Action

    for _ in range(count):
        Action.update_all(0.016)


def test_ease_wraps_action_and_completes_after_frames():
    sprite = arcade.Sprite()
    sprite.center_x = 0

    wrapped = move_until(sprite, velocity=(5, 0), condition=lambda: False)
    ease_action = Ease(wrapped, frames=4)
    ease_action.apply(sprite, tag="ease_smoke")

    # During easing, the wrapped action's factor should grow.
    _step_frames(2)
    assert wrapped.current_velocity[0] > 0
    assert not ease_action.done

    # After the configured frames the wrapper completes but the wrapped action keeps running.
    _step_frames(2)
    assert ease_action.done
    assert wrapped.done is False


def test_ease_rejects_invalid_frame_counts():
    wrapped = move_until(arcade.Sprite(), velocity=(5, 0), condition=lambda: False)

    try:
        Ease(wrapped, frames=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for non-positive frames")
