"""
Debug script to check spawn positioning.
"""

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


def debug_spawn_positioning():
    """Debug the spawn positioning to see what's happening."""

    # Create a simple formation
    formation = arrange_grid(rows=1, cols=2, start_x=400, start_y=300, spacing_x=50, visible=False)

    print(f"Formation positions: {[(s.center_x, s.center_y) for s in formation]}")

    # Create the entry action with right spawn
    entry_actions = create_galaga_style_entry(
        formation=formation,
        groups_per_formation=1,
        sprites_per_group=2,
        screen_bounds=(0, 0, 800, 600),
        path_speed=100.0,
        spawn_areas={"left": False, "right": True, "top": False, "bottom": False},
    )

    action = entry_actions[0]
    action.apply(formation, tag="debug_test")
    action.start()

    # Check spawn positions after first update
    Action.update_all(0.016)
    for sprite in formation:
        sprite.update()

    positions = [(sprite.center_x, sprite.center_y) for sprite in formation]
    print(f"After spawn positioning: {positions}")

    # Check if any sprite is positioned off-screen right
    for i, (x, y) in enumerate(positions):
        print(f"Sprite {i}: X={x}, Y={y}")
        if x > 700:
            print(f"  ✅ Sprite {i} is positioned off-screen right")
        else:
            print(f"  ❌ Sprite {i} is NOT positioned off-screen right")


if __name__ == "__main__":
    debug_spawn_positioning()
