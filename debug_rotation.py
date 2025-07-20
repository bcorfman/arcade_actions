"""
Debug script to check rotation functionality.
"""

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


def debug_rotation():
    """Debug the rotation functionality."""

    # Create a simple formation
    formation = arrange_grid(rows=1, cols=1, start_x=400, start_y=300, spacing_x=50, visible=False)

    print(f"Initial sprite angle: {formation[0].angle}")
    print(f"Formation target position: ({formation[0].center_x}, {formation[0].center_y})")

    # Create the entry action
    entry_actions = create_galaga_style_entry(
        formation=formation,
        groups_per_formation=1,
        sprites_per_group=1,
        screen_bounds=(0, 0, 800, 600),
        path_speed=200.0,
    )

    action = entry_actions[0]
    action.apply(formation, tag="debug_rotation")
    action.start()

    # Track sprite angle over time
    for frame in range(100):
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()

        if frame % 10 == 0:
            angle = formation[0].angle
            pos_x, pos_y = formation[0].center_x, formation[0].center_y
            target_x, target_y = 400, 300  # Expected target position from formation
            distance = ((pos_x - target_x) ** 2 + (pos_y - target_y) ** 2) ** 0.5
            print(f"Frame {frame}: angle = {angle}, pos = ({pos_x:.1f}, {pos_y:.1f}), distance = {distance:.1f}")

            # Check if action is done
            if action.done:
                print(f"Action completed at frame {frame}")
                break

    final_angle = formation[0].angle
    print(f"Final angle: {final_angle}")
    print(f"Angle modulo 360: {final_angle % 360}")


if __name__ == "__main__":
    debug_rotation()
