"""
Test to verify the bounce fix prevents rapid bouncing when sprites are removed.
"""

from actions.base import ActionSprite
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import BoundedMove


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

    # Set up boundary detection - wider boundaries to avoid immediate left bounce
    get_bounds = lambda: (0, 0, 350, 600)
    bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)
    bounce_action.target = enemies
    bounce_action.start()

    # Start movement that will cause bounce
    initial_move = MoveBy((300, 0), 2.0)
    enemies.do(initial_move)

    print(f"Initial positions: {[s.center_x for s in enemies]}")

    # Update until bounce occurs
    for i in range(50):
        enemies.update(0.1)
        bounce_action.update(0.1)
        if bounce_count > 0:
            print(f"Bounce occurred at step {i}, positions: {[s.center_x for s in enemies]}")
            print(f"Horizontal direction: {bounce_action._horizontal_direction}")
            break

    # Should have exactly 1 bounce
    assert bounce_count == 1, f"Expected 1 bounce, got {bounce_count}"

    # Remove the rightmost sprite
    rightmost_sprite = max(enemies, key=lambda s: s.center_x)
    print(f"Removing rightmost sprite at {rightmost_sprite.center_x}")
    rightmost_sprite.remove_from_sprite_lists()
    print(f"Positions after removal: {[s.center_x for s in enemies]}")
    print(f"Horizontal direction after removal: {bounce_action._horizontal_direction}")

    # Continue updating - should not cause additional bounces immediately
    initial_bounce_count = bounce_count
    for i in range(5):
        enemies.update(0.1)
        bounce_action.update(0.1)
        print(f"Step {i}: positions: {[s.center_x for s in enemies]}, direction: {bounce_action._horizontal_direction}")
        if bounce_count > initial_bounce_count:
            print(f"Additional bounce at step {i}!")
            break

    # Should not have additional bounces due to sprite removal
    additional_bounces = bounce_count - initial_bounce_count
    assert additional_bounces == 0, f"Expected 0 additional bounces after sprite removal, got {additional_bounces}"

    print(f"✓ Bounce fix working: {bounce_count} total bounces, no rapid bouncing after sprite removal")
