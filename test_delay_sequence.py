"""
Test DelayUntil functionality in sequences to identify the missing functionality.
"""

import arcade

from actions.base import Action
from actions.composite import sequence
from actions.conditional import DelayUntil, MoveUntil, duration


def test_delay_until_standalone():
    """Test that DelayUntil works by itself."""
    print("=== Testing DelayUntil standalone ===")

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create DelayUntil action with 0.5 second duration
    delay_action = DelayUntil(condition=duration(0.5))
    delay_action.apply(sprite, tag="delay_test")

    print(f"Initial: DelayUntil.done = {delay_action.done}")

    # Simulate frames for 1 second
    for frame in range(60):  # 1 second at 60 FPS
        Action.update_all(0.016)

        # Check completion around expected time
        if frame in [29, 30, 31]:  # Around 0.5 seconds
            time_elapsed = frame * 0.016
            print(f"Frame {frame} ({time_elapsed:.3f}s): DelayUntil.done = {delay_action.done}")

        if delay_action.done:
            time_elapsed = frame * 0.016
            print(f"DelayUntil completed at frame {frame} ({time_elapsed:.3f}s)")
            break

    assert delay_action.done, "DelayUntil should complete after 0.5 seconds"
    print("✅ DelayUntil standalone works\n")


def test_move_until_standalone():
    """Test that MoveUntil works by itself."""
    print("=== Testing MoveUntil standalone ===")

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create MoveUntil action with 0.5 second duration
    move_action = MoveUntil(velocity=(50, 0), condition=duration(0.5))
    move_action.apply(sprite, tag="move_test")

    print(f"Initial: sprite at ({sprite.center_x}, {sprite.center_y}), MoveUntil.done = {move_action.done}")

    # Simulate frames for 1 second
    for frame in range(60):
        Action.update_all(0.016)
        sprite.update()  # Apply velocity to position

        # Check at key frames
        if frame in [10, 20, 30, 31]:
            time_elapsed = frame * 0.016
            print(
                f"Frame {frame} ({time_elapsed:.3f}s): sprite at ({sprite.center_x:.1f}, {sprite.center_y:.1f}), done = {move_action.done}"
            )

        if move_action.done:
            time_elapsed = frame * 0.016
            print(f"MoveUntil completed at frame {frame} ({time_elapsed:.3f}s)")
            break

    assert move_action.done, "MoveUntil should complete after 0.5 seconds"
    assert sprite.center_x > 100, "Sprite should have moved right"
    print("✅ MoveUntil standalone works\n")


def test_sequence_without_delay():
    """Test that sequence works without DelayUntil."""
    print("=== Testing sequence without DelayUntil ===")

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create sequence: MoveUntil for 0.3s, then MoveUntil for 0.3s (different direction)
    move1 = MoveUntil(velocity=(50, 0), condition=duration(0.3))
    move2 = MoveUntil(velocity=(0, 50), condition=duration(0.3))
    seq = sequence(move1, move2)
    seq.apply(sprite, tag="seq_test")

    print(f"Initial: sprite at ({sprite.center_x}, {sprite.center_y}), sequence.done = {seq.done}")

    positions = []
    # Simulate frames for 1 second
    for frame in range(60):
        Action.update_all(0.016)
        sprite.update()

        # Record position every 5 frames
        if frame % 5 == 0:
            positions.append((frame, sprite.center_x, sprite.center_y))

        if seq.done:
            time_elapsed = frame * 0.016
            print(f"Sequence completed at frame {frame} ({time_elapsed:.3f}s)")
            break

    print("Position history:")
    for frame, x, y in positions:
        time_elapsed = frame * 0.016
        print(f"  Frame {frame} ({time_elapsed:.3f}s): ({x:.1f}, {y:.1f})")

    assert seq.done, "Sequence should complete"
    assert sprite.center_x > 100, "Sprite should have moved right (first action)"
    assert sprite.center_y > 100, "Sprite should have moved up (second action)"
    print("✅ Sequence without DelayUntil works\n")


def test_sequence_with_delay():
    """Test that sequence works WITH DelayUntil - this is the failing case."""
    print("=== Testing sequence WITH DelayUntil ===")

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create sequence: DelayUntil for 0.3s, then MoveUntil for 0.3s
    delay = DelayUntil(condition=duration(0.3))
    move = MoveUntil(velocity=(50, 0), condition=duration(0.3))
    seq = sequence(delay, move)
    seq.apply(sprite, tag="delay_seq_test")

    print(f"Initial: sprite at ({sprite.center_x}, {sprite.center_y}), sequence.done = {seq.done}")

    positions = []
    movement_started = False
    delay_completed_frame = None

    # Simulate frames for 1 second
    for frame in range(60):
        Action.update_all(0.016)
        sprite.update()

        # Check if movement has started
        if sprite.center_x > 100 and not movement_started:
            movement_started = True
            time_elapsed = frame * 0.016
            print(f"Movement started at frame {frame} ({time_elapsed:.3f}s)")

        # Check if delay completed
        if delay.done and delay_completed_frame is None:
            delay_completed_frame = frame
            time_elapsed = frame * 0.016
            print(f"DelayUntil completed at frame {frame} ({time_elapsed:.3f}s)")

        # Record position every 5 frames
        if frame % 5 == 0:
            positions.append((frame, sprite.center_x, sprite.center_y, delay.done, move.done, seq.done))

        if seq.done:
            time_elapsed = frame * 0.016
            print(f"Sequence completed at frame {frame} ({time_elapsed:.3f}s)")
            break

    print("Position and state history:")
    for frame, x, y, delay_done, move_done, seq_done in positions:
        time_elapsed = frame * 0.016
        print(
            f"  Frame {frame} ({time_elapsed:.3f}s): pos=({x:.1f}, {y:.1f}), delay={delay_done}, move={move_done}, seq={seq_done}"
        )

    print("Final state:")
    print(f"  DelayUntil.done = {delay.done}")
    print(f"  MoveUntil.done = {move.done}")
    print(f"  Sequence.done = {seq.done}")
    print(f"  Movement started = {movement_started}")
    print(f"  Delay completed at frame = {delay_completed_frame}")

    # This is where we expect the issue to be
    assert delay.done, "DelayUntil should complete"
    assert movement_started, "Movement should start after delay completes"  # This will likely fail
    assert sprite.center_x > 100, "Sprite should have moved after delay"  # This will likely fail
    print("✅ Sequence with DelayUntil works\n")


def main():
    """Run all tests to identify the issue."""
    print("Testing DelayUntil functionality...\n")

    try:
        test_delay_until_standalone()
    except Exception as e:
        print(f"❌ DelayUntil standalone failed: {e}\n")

    Action.clear_all()

    try:
        test_move_until_standalone()
    except Exception as e:
        print(f"❌ MoveUntil standalone failed: {e}\n")

    Action.clear_all()

    try:
        test_sequence_without_delay()
    except Exception as e:
        print(f"❌ Sequence without DelayUntil failed: {e}\n")

    Action.clear_all()

    try:
        test_sequence_with_delay()
    except Exception as e:
        print(f"❌ Sequence with DelayUntil failed: {e}")
        print("This identifies the missing functionality!\n")

    Action.clear_all()

    print("Test complete.")


if __name__ == "__main__":
    main()
