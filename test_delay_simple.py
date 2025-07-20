"""
Simple test to verify DelayUntil is working correctly.
"""

import arcade

from actions.base import Action
from actions.composite import sequence
from actions.conditional import DelayUntil, MoveUntil, duration


def test_delay_simple():
    """Test DelayUntil with simple movement."""

    # Create sprites
    sprites = []
    for i in range(3):
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100 + i * 50
        sprites.append(sprite)

    print("Initial positions:")
    for i, sprite in enumerate(sprites):
        print(f"  Sprite {i}: ({sprite.center_x}, {sprite.center_y})")

    # Create delayed movement sequences
    # Sprite 0: Start immediately
    seq0 = MoveUntil((50, 0), duration(2.0))
    seq0.apply(sprites[0], tag="move0")
    seq0.start()

    # Sprite 1: Wait 0.5 seconds, then move
    seq1 = sequence(DelayUntil(duration(0.5)), MoveUntil((50, 0), duration(2.0)))
    seq1.apply(sprites[1], tag="move1")
    seq1.start()

    # Sprite 2: Wait 1.0 seconds, then move
    seq2 = sequence(DelayUntil(duration(1.0)), MoveUntil((50, 0), duration(2.0)))
    seq2.apply(sprites[2], tag="move2")
    seq2.start()

    print(f"Active actions: {len(Action._active_actions)}")

    # Track movement start
    start_frames = [None, None, None]
    initial_positions = [(100, 100), (100, 150), (100, 200)]

    # Simulate frames
    for frame in range(180):  # 3 seconds
        Action.update_all(0.016)  # 60 FPS
        for sprite in sprites:
            sprite.update()

        # Check if sprites have started moving
        for i, sprite in enumerate(sprites):
            if start_frames[i] is None:
                init_x, init_y = initial_positions[i]
                if abs(sprite.center_x - init_x) > 2:
                    start_frames[i] = frame
                    print(f"Sprite {i} started moving at frame {frame} (time: {frame * 0.016:.2f}s)")

        # Print positions every 30 frames (0.5 seconds)
        if frame % 30 == 0:
            print(f"\nFrame {frame} (time: {frame * 0.016:.2f}s):")
            for i, sprite in enumerate(sprites):
                print(f"  Sprite {i}: ({sprite.center_x:.1f}, {sprite.center_y:.1f})")

    print(f"\nStart frames: {start_frames}")
    expected_delays = [0, 0.5, 1.0]
    actual_delays = [f * 0.016 if f is not None else None for f in start_frames]
    print(f"Expected delays: {expected_delays}")
    print(f"Actual delays: {actual_delays}")


if __name__ == "__main__":
    test_delay_simple()
