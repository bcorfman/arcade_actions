"""
Debug script to check path coordinates.
"""

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


def debug_path_coordinates():
    """Debug the path coordinates to see where they end."""

    # Create a simple formation
    formation = arrange_grid(rows=1, cols=3, start_x=375, start_y=400, spacing_x=50, visible=False)

    # Store expected final positions
    expected_positions = [(sprite.center_x, sprite.center_y) for sprite in formation]
    print(f"Expected positions: {expected_positions}")

    # Create the entry action
    entry_actions = create_galaga_style_entry(
        formation=formation,
        groups_per_formation=1,
        sprites_per_group=3,
        screen_bounds=(0, 0, 800, 600),
        path_speed=200.0,
    )

    action = entry_actions[0]
    action.apply(formation, tag="debug_test")
    action.start()

    # Print the path coordinates from the coordinator
    # We need to access the coordinator's shared_path
    print("Action structure:")
    print(f"Action type: {type(action)}")
    print(f"Action phases: {len(action.actions) if hasattr(action, 'actions') else 'No actions attribute'}")

    # Try to access the coordinator
    if hasattr(action, "actions") and len(action.actions) > 1:
        coordinator = action.actions[1]  # Second phase should be coordinator
        print(f"Coordinator type: {type(coordinator)}")
        if hasattr(coordinator, "shared_path"):
            print(f"Shared path: {coordinator.shared_path}")
        if hasattr(coordinator, "target_positions"):
            print(f"Target positions: {coordinator.target_positions}")

    # Run for a few frames to see what happens
    for frame in range(10):
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()

        if frame % 5 == 0:
            positions = [(sprite.center_x, sprite.center_y) for sprite in formation]
            print(f"Frame {frame}: {positions}")


if __name__ == "__main__":
    debug_path_coordinates()
