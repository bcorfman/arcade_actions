"""
Test to verify the bounce fix prevents rapid bouncing when sprites are removed.
"""

from actions import BoundedMove  # Import from the convenience function
from actions.base import ActionSprite
from actions.group import SpriteGroup
from actions.interval import MoveBy


def test_bounce_fix_prevents_rapid_bouncing():
    """Test that the bounce fix prevents rapid bouncing when sprites are removed."""
    # Create a sprite group
    enemies = SpriteGroup()
    for i in range(3):
        enemy = ActionSprite(":resources:images/enemies/bee.png")
        enemy.center_x = 100 + i * 80
        enemy.center_y = 400
        enemies.append(enemy)

    bounce_count = 0

    def on_bounce(sprite, axis):
        nonlocal bounce_count
        bounce_count += 1
        print(f"Bounce #{bounce_count}: sprite at ({sprite.center_x}, {sprite.center_y}), axis={axis}")

    # Set up bounded movement using NEW ARCHITECTURE
    get_bounds = lambda: (0, 0, 350, 600)
    move_action = MoveBy((300, 0), 2.0)
    bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

    # Apply bounded movement to the group
    group_action = enemies.do(bounded_move)

    print(f"Initial positions: {[s.center_x for s in enemies]}")

    # Update until bounce occurs
    for i in range(50):
        enemies.update(0.1)
        if bounce_count > 0:
            print(f"Bounce occurred at step {i}, positions: {[s.center_x for s in enemies]}")
            # Get the boundary action from the group action to check direction
            boundary_action = group_action.template if hasattr(group_action, "template") else None
            if boundary_action and hasattr(boundary_action, "_horizontal_direction"):
                print(f"Horizontal direction: {boundary_action._horizontal_direction}")
            break

    # Should have exactly 1 bounce
    assert bounce_count == 1, f"Expected 1 bounce, got {bounce_count}"

    # Remove the rightmost sprite
    rightmost_sprite = max(enemies, key=lambda s: s.center_x)
    print(f"Removing rightmost sprite at {rightmost_sprite.center_x}")
    rightmost_sprite.remove_from_sprite_lists()
    print(f"Positions after removal: {[s.center_x for s in enemies]}")

    # Get boundary action reference for direction checking
    boundary_action = group_action.template if hasattr(group_action, "template") else None
    if boundary_action and hasattr(boundary_action, "_horizontal_direction"):
        print(f"Horizontal direction after removal: {boundary_action._horizontal_direction}")

    # Continue updating - should not cause additional bounces immediately
    initial_bounce_count = bounce_count
    rapid_bounce_steps = 0
    for i in range(5):
        enemies.update(0.1)
        direction_info = ""
        if boundary_action and hasattr(boundary_action, "_horizontal_direction"):
            direction_info = f", direction: {boundary_action._horizontal_direction}"
        print(f"Step {i}: positions: {[s.center_x for s in enemies]}{direction_info}")
        if bounce_count > initial_bounce_count:
            print(f"Additional bounce at step {i}!")
            rapid_bounce_steps = i
            break

    # Should not have rapid bounces (bounces within first 2 steps would indicate rapid bouncing)
    additional_bounces = bounce_count - initial_bounce_count
    if additional_bounces > 0:
        assert rapid_bounce_steps >= 2, (
            f"Rapid bouncing detected: bounce occurred at step {rapid_bounce_steps}, expected >= 2"
        )
        print(f"✓ Bounce fix working: Additional bounce at step {rapid_bounce_steps} is not rapid bouncing")
    else:
        print(f"✓ Bounce fix working: {bounce_count} total bounces, no additional bounces after sprite removal")
