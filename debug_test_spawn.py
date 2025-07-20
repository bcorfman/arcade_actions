"""
Debug the spawn side test issue.
"""

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


def debug_spawn_test():
    """Debug the spawn side test."""

    # Create formation
    formation = arrange_grid(rows=1, cols=2, start_x=400, start_y=300, spacing_x=50, visible=False)
    print(f"Initial formation: {[(s.center_x, s.center_y) for s in formation]}")

    # Create right spawn action
    right_entry = create_galaga_style_entry(
        formation=formation,
        groups_per_formation=1,
        sprites_per_group=2,
        screen_bounds=(0, 0, 800, 600),
        path_speed=100.0,
        spawn_areas={"left": False, "right": True, "top": False, "bottom": False},
    )[0]

    # Apply and start
    right_entry.apply(formation, tag="right_test")
    right_entry.start()

    # Allow spawn positioning to complete
    Action.update_all(0.016)
    for sprite in formation:
        sprite.update()

    print(f"After spawn positioning: {[(s.center_x, s.center_y) for s in formation]}")

    # Track positions for a few frames
    for frame in range(5):
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()
        positions = [(s.center_x, s.center_y) for s in formation]
        print(f"Frame {frame}: {positions}")


if __name__ == "__main__":
    debug_spawn_test()
