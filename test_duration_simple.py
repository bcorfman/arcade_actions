"""
Simple test to verify duration function works correctly.
"""

import time

from actions.conditional import duration


def test_duration_timing():
    """Test duration function with real time."""
    print("Testing duration(0.5) function...")

    condition = duration(0.5)

    start_time = time.time()

    while True:
        current_time = time.time()
        elapsed = current_time - start_time

        result = condition()

        print(f"Time {elapsed:.3f}s: condition() = {result}")

        if result:
            print(f"Duration completed at {elapsed:.3f}s")
            break

        if elapsed > 1.0:  # Safety timeout
            print("Timeout - duration never completed!")
            break

        time.sleep(0.05)  # 50ms delay


def test_duration_with_action_timing():
    """Test how duration works in Action.update_all context."""
    import arcade

    from actions.base import Action
    from actions.conditional import DelayUntil

    print("\nTesting duration with Action.update_all timing...")

    sprite = arcade.Sprite()

    # Create DelayUntil with 0.5 second duration
    delay_action = DelayUntil(condition=duration(0.5))
    delay_action.apply(sprite, tag="test")

    start_time = time.time()

    # Simulate exactly what Action.update_all does
    frame = 0
    while True:
        # Update all actions (this calls delay_action.update(0.016))
        Action.update_all(0.016)

        current_time = time.time()
        elapsed = current_time - start_time

        if frame % 10 == 0:  # Every 10 frames
            print(f"Frame {frame}, time {elapsed:.3f}s: DelayUntil.done = {delay_action.done}")

        if delay_action.done:
            print(f"DelayUntil completed at frame {frame}, time {elapsed:.3f}s")
            break

        if frame > 100:  # Safety timeout
            print("Timeout - DelayUntil never completed!")
            break

        frame += 1
        time.sleep(0.016)  # 60 FPS timing


if __name__ == "__main__":
    test_duration_timing()
    test_duration_with_action_timing()
