"""
Test DelayUntil alone to verify it works correctly.
"""

import arcade

from actions.base import Action
from actions.conditional import DelayUntil, duration


def test_delay_alone():
    """Test DelayUntil by itself."""

    # Create a sprite
    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    print(f"Initial position: ({sprite.center_x}, {sprite.center_y})")

    # Create a simple DelayUntil action
    delay_action = DelayUntil(condition=duration(1.0))
    delay_action.apply(sprite, tag="delay_test")
    delay_action.start()

    print("DelayUntil created and started")
    print(f"Action done initially: {delay_action.done}")
    print(f"Active actions: {len(Action._active_actions)}")

    # Simulate frames
    for frame in range(120):  # 2 seconds at 60 FPS
        Action.update_all(0.016)  # 60 FPS

        # Check at specific intervals
        if frame in [0, 30, 60, 90]:
            time_elapsed = frame * 0.016
            print(f"Frame {frame} (time: {time_elapsed:.2f}s): DelayUntil.done = {delay_action.done}")

        # Check when it's done
        if delay_action.done:
            time_elapsed = frame * 0.016
            print(f"DelayUntil completed at frame {frame} (time: {time_elapsed:.2f}s)")
            break

    print(f"Final state: DelayUntil.done = {delay_action.done}")


if __name__ == "__main__":
    test_delay_alone()
