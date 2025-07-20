"""
Debug script to understand the Galaga pattern behavior.
"""

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


def debug_galaga_pattern():
    """Debug the Galaga pattern to see what's happening."""
    # Create a simple formation
    formation = arrange_grid(rows=1, cols=4, start_x=350, start_y=400, spacing_x=50, visible=False)

    print("Formation sprites:")
    for i, sprite in enumerate(formation):
        print(f"  Sprite {i}: ({sprite.center_x}, {sprite.center_y})")

    # Force left spawn for S-curve
    entry_actions = create_galaga_style_entry(
        formation=formation,
        groups_per_formation=1,
        sprites_per_group=4,
        screen_bounds=(0, 0, 800, 600),
        path_speed=100.0,
        spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
    )

    print(f"\nEntry actions returned: {len(entry_actions)} actions")
    action = entry_actions[0]
    print(f"Action type: {type(action)}")

    # Apply and start the action
    action.apply(formation, tag="debug_test")
    action.start()

    print(f"\nAfter start, action.done: {action.done}")
    print(f"Active actions: {len(Action._active_actions)}")

    # Track when followers start moving
    follower_start_frames = [None, None, None, None]
    spawn_positions = [(-180.0, 225.0), (-180.0, 275.0), (-180.0, 325.0), (-180.0, 375.0)]

    # Track positions for many frames to see follower movement
    for frame in range(200):
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()

        # Check if followers have started moving
        for i, sprite in enumerate(formation):
            if follower_start_frames[i] is None:
                spawn_x, spawn_y = spawn_positions[i]
                if abs(sprite.center_x - spawn_x) > 2 or abs(sprite.center_y - spawn_y) > 2:
                    follower_start_frames[i] = frame
                    print(f"Follower {i} started moving at frame {frame}")

        if frame < 10 or frame % 20 == 0:
            print(f"\nFrame {frame}:")
            for i, sprite in enumerate(formation):
                print(f"  Sprite {i}: ({sprite.center_x:.1f}, {sprite.center_y:.1f}) angle={sprite.angle:.1f}")

        # Check if all followers have started
        if all(f is not None for f in follower_start_frames):
            print("\nAll followers have started moving!")
            break

    print(f"\nFollower start frames: {follower_start_frames}")

    # Calculate delays
    if follower_start_frames[0] is not None and follower_start_frames[1] is not None:
        delays = []
        for i in range(1, 4):
            if follower_start_frames[i] is not None:
                delay = follower_start_frames[i] - follower_start_frames[0]
                delays.append(delay)
        print(f"Delays from leader: {delays}")


if __name__ == "__main__":
    debug_galaga_pattern()
