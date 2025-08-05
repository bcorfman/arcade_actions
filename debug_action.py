#!/usr/bin/env python3

import arcade

from actions import arrange_grid, create_formation_entry_from_sprites

# Create a simple formation
target_formation = arrange_grid(
    sprites=[arcade.Sprite(":resources:images/items/star.png") for _ in range(16)],
    rows=4,
    cols=4,
    start_x=120,
    start_y=400,
    spacing_x=120,
    spacing_y=96,
    visible=False,
)

# Create entry actions
entry_actions = create_formation_entry_from_sprites(
    target_formation,
    window_bounds=(0, 0, 800, 600),
    speed=2.0,
    stagger_delay=1.0,
)

print(f"Total entry_actions: {len(entry_actions)}")

# Examine the first few actions
for i, (sprite, action) in enumerate(entry_actions[:8]):
    print(f"\nAction {i}: {type(action).__name__}")
    print(f"  Action attributes: {[attr for attr in dir(action) if not attr.startswith('_')]}")

    if hasattr(action, "duration"):
        print(f"  Has duration: {action.duration}")
    if hasattr(action, "_duration"):
        print(f"  Has _duration: {action._duration}")
    if hasattr(action, "elapsed_time"):
        print(f"  Has elapsed_time: {action.elapsed_time}")

    if hasattr(action, "actions"):
        print("  Has actions: True")
        print(f"  Number of actions: {len(action.actions)}")
        if len(action.actions) > 0:
            first_action = action.actions[0]
            print(f"  First action type: {type(first_action).__name__}")
            print(f"  First action attributes: {[attr for attr in dir(first_action) if not attr.startswith('_')]}")
            if hasattr(first_action, "duration"):
                print(f"  First action duration: {first_action.duration}")
            if hasattr(first_action, "_duration"):
                print(f"  First action _duration: {first_action._duration}")
    else:
        print("  Has actions: False")
