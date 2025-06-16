#!/usr/bin/env python3

from actions.base import ActionSprite
from actions.group import SpriteGroup
from actions.interval import MoveBy

# Create test setup
sprite_group = SpriteGroup()
sprite1 = ActionSprite(":resources:images/items/star.png")
sprite2 = ActionSprite(":resources:images/items/star.png")
sprite_group.append(sprite1)
sprite_group.append(sprite2)

move_action = MoveBy((100, 0), 1.0)
group_action = sprite_group.do(move_action)

print("Initial state:")
print(f"  Group action done: {group_action.done}")
print(f"  Number of individual actions: {len(group_action.actions)}")
for i, action in enumerate(group_action.actions):
    print(f"    Action {i}: done={action.done}, elapsed={action._elapsed}")

print("\nAfter 0.5 seconds:")
group_action.update(0.5)
print(f"  Group action done: {group_action.done}")
for i, action in enumerate(group_action.actions):
    print(f"    Action {i}: done={action.done}, elapsed={action._elapsed}")

print("\nAfter another 0.5 seconds:")
group_action.update(0.5)
print(f"  Group action done: {group_action.done}")
for i, action in enumerate(group_action.actions):
    print(f"    Action {i}: done={action.done}, elapsed={action._elapsed}")
