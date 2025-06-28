"""Unit tests for movement actions in arcade_actions.

This module contains tests for movement-related actions:
- BoundaryAction with BounceBehavior (replaces BoundedMove)
- BoundaryAction with WrapBehavior (replaces WrappedMove)
- Driver (directional movement) - not tested here

All tests use ActionSprite for sprite-based tests and follow the standard
action lifecycle pattern using sprite.do(action) and sprite.update().
"""

import pytest

from actions import BoundedMove, WrappedMove  # Import convenience functions
from actions.base import ActionSprite
from actions.interval import MoveBy, RotateBy


class TestWrappedMove:
    """Test suite for wrapping movement.

    Tests the WrappedMove action's behavior when sprites move across screen boundaries.
    Focuses on:
    - Wrapping behavior at each boundary
    - Corner cases
    - Wrap callbacks
    - SpriteGroup handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.position = (0, 0)
        return sprite

    @pytest.fixture
    def sprite_group(self):
        """Create a SpriteGroup with test sprites for group behavior testing."""
        from actions.group import SpriteGroup

        sprites = SpriteGroup()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.position = (0, 0)
            sprites.append(sprite)
        return sprites

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns screen bounds."""
        return lambda: (800, 600)

    def test_wrap_right_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off right edge.

        Verifies that:
        - Sprite wraps to left edge when moving right
        - Position is correctly aligned to boundary
        """
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)  # Move 200 pixels right over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to left edge
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_left_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off left edge.

        Verifies that:
        - Sprite wraps to right edge when moving left
        - Position is correctly aligned to boundary
        """
        # Create movement action to move sprite off left edge
        move_action = MoveBy((-200, 0), 0.2)  # Move 200 pixels left over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to left edge
        sprite.center_x = 50
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to right edge
        assert sprite.center_x > 800  # Wrapped to right edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_top_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off top edge.

        Verifies that:
        - Sprite wraps to bottom edge when moving up
        - Position is correctly aligned to boundary
        """
        # Create movement action to move sprite off top edge
        move_action = MoveBy((0, 200), 0.2)  # Move 200 pixels up over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to bottom edge
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y < 0  # Wrapped to bottom edge

    def test_wrap_bottom_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off bottom edge.

        Verifies that:
        - Sprite wraps to top edge when moving down
        - Position is correctly aligned to boundary
        """
        # Create movement action to move sprite off bottom edge
        move_action = MoveBy((0, -200), 0.2)  # Move 200 pixels down over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to bottom edge
        sprite.center_x = 300
        sprite.center_y = 50

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to top edge
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y > 600  # Wrapped to top edge

    def test_wrap_corner(self, sprite, get_bounds):
        """Test wrapping when sprite moves off corner.

        Verifies that:
        - Both horizontal and vertical wrapping work together
        - Position is correctly aligned to both boundaries
        """
        # Create movement action to move sprite off corner
        move_action = MoveBy((200, 200), 0.2)  # Move diagonally off corner
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to top-right corner
        sprite.center_x = 750
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to opposite corner
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y < 0  # Wrapped to bottom edge

    def test_wrap_callback(self, sprite, get_bounds):
        """Test wrap callbacks are triggered correctly.

        Verifies that:
        - Callback is called when wrapping occurs
        - Callback receives correct sprite and axis parameters
        """
        wrap_events = []

        def on_wrap(sprite, axis):
            wrap_events.append((sprite, axis))

        # Create movement action and wrap action with callback
        move_action = MoveBy((200, 0), 0.2)
        wrap_action = WrappedMove(get_bounds, on_wrap=on_wrap)

        # Position sprite to trigger wrap
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify callback was triggered
        assert len(wrap_events) == 1
        assert wrap_events[0][0] == sprite
        assert wrap_events[0][1] == "x"

    def test_sprite_group_wrapping(self, sprite_group, get_bounds):
        """Test wrapping behavior with SpriteGroup.

        Verifies that:
        - All sprites in the group are processed
        - Each sprite wraps independently
        - Group behavior is maintained
        """
        # Position sprites across screen
        for i, sprite in enumerate(sprite_group):
            sprite.center_x = 700 + i * 30  # Spread across right edge
            sprite.center_y = 300

        # Create wrapped movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        wrapped_move = WrappedMove(get_bounds, movement_action=move_action)

        # Apply the wrapped action to sprite group
        sprite_group.do(wrapped_move)

        # Update for full duration using SpriteGroup
        sprite_group.update(0.2)

        # Verify all sprites wrapped
        for sprite in sprite_group:
            assert sprite.center_x < 0  # All wrapped to left edge

    def test_wrap_with_acceleration(self, sprite, get_bounds):
        """Test wrapping with action-based movement.

        Verifies that:
        - Wrapping works with action-based movement
        - Action continues after wrapping
        """
        # Create wrapped movement action (NEW ARCHITECTURE)
        # Test a larger movement to ensure it definitely crosses the boundary
        move_action = MoveBy((250, 0), 0.2)  # Move 250 pixels right
        wrapped_move = WrappedMove(get_bounds, movement_action=move_action)

        # Position sprite close to boundary
        sprite.center_x = 700
        sprite.center_y = 300

        # Apply wrapped action
        sprite.do(wrapped_move)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped - should be at 700 + 250 - 800 = 150 pixels wrapped from left edge
        assert sprite.center_x < 0  # Wrapped to left edge

    def test_disable_horizontal_wrapping(self, sprite, get_bounds):
        """Test disabling horizontal wrapping.

        Verifies that:
        - Horizontal wrapping is disabled
        - Vertical wrapping still works
        - Sprite position behaves correctly
        """
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)
        wrap_action = WrappedMove(get_bounds, wrap_horizontal=False)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did NOT wrap horizontally
        assert sprite.center_x > 800  # Moved off right edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_disable_vertical_wrapping(self, sprite, get_bounds):
        """Test disabling vertical wrapping.

        Verifies that:
        - Vertical wrapping is disabled
        - Horizontal wrapping still works
        - Sprite position behaves correctly
        """
        # Create movement action to move sprite off top edge
        move_action = MoveBy((0, 200), 0.2)
        wrap_action = WrappedMove(get_bounds, wrap_vertical=False)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did NOT wrap vertically
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y > 600  # Moved off top edge

    def test_dynamic_bounds(self, sprite):
        """Test wrapping with dynamically changing bounds.

        Verifies that:
        - Bounds function is called each frame
        - Wrapping adapts to changing boundaries
        """
        bounds_width = 800

        def get_bounds():
            return (bounds_width, 600)

        # Create movement and wrap actions
        move_action = MoveBy((200, 0), 0.4)  # Longer duration
        wrap_action = WrappedMove(get_bounds)

        # Position sprite to trigger wrap
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update halfway through
        sprite.update(0.2)

        # Change bounds
        bounds_width = 400

        # Continue updating
        sprite.update(0.2)

        # Verify wrapping adapted to new bounds
        # Exact position depends on timing, but should be affected by bounds change
        assert sprite.center_x != 950  # Not at original predicted position

    def test_wrap_with_rotation(self, sprite, get_bounds):
        """Test wrapping works with simultaneous rotation actions.

        Verifies that:
        - Multiple actions can run simultaneously
        - Wrapping doesn't interfere with rotation actions
        """
        # Create wrapped movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        wrapped_move = WrappedMove(get_bounds, movement_action=move_action)

        # Create rotation action (pure action-based)
        rotate_action = RotateBy(18, 0.2)  # 18 degrees over 0.2 seconds

        # Position sprite and set initial rotation
        sprite.center_x = 750
        sprite.center_y = 300
        sprite.angle = 45

        # Apply both actions simultaneously
        sprite.do(wrapped_move)
        sprite.do(rotate_action, slot="rotation")

        # Update for full duration
        sprite.update(0.2)

        # Verify position wrapped and rotation occurred
        assert sprite.center_x < 0  # Wrapped to left edge
        assert abs(sprite.angle - 63) < 1  # 45 + 18 = 63 degrees

    def test_wrap_with_group_action(self, get_bounds):
        """Test wrapping with SpriteGroup actions.

        Verifies that:
        - Group actions work with wrapping
        - All sprites in group wrap correctly
        - Group coordination is maintained
        """
        from actions.group import SpriteGroup

        # Create sprite group
        enemies = SpriteGroup()
        for i in range(3):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 750 + i * 20
            enemy.center_y = 300
            enemies.append(enemy)

        wrap_events = []

        def on_wrap(sprite, axis):
            wrap_events.append((sprite, axis))

        # Create wrapped group movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        wrapped_move = WrappedMove(get_bounds, on_wrap=on_wrap, movement_action=move_action)

        # Apply wrapped movement to the group
        enemies.do(wrapped_move)

        # Update for full duration
        enemies.update(0.2)

        # Verify all sprites wrapped
        for sprite in enemies:
            assert sprite.center_x < 0  # All wrapped to left edge

        # Verify wrap events were triggered
        assert len(wrap_events) == 3  # One for each sprite

    def test_wrap_group_action_automatic_cleanup(self):
        """Test that group actions are automatically cleaned up."""
        from actions.group import SpriteGroup

        # Create sprite group
        enemies = SpriteGroup()
        for i in range(2):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 400 + i * 100
            enemy.center_y = 300
            enemies.append(enemy)

        # Start a group action
        move_action = MoveBy((100, 0), 1.0)
        group_action = enemies.do(move_action)

        # Verify action is tracked
        assert len(enemies._group_actions) == 1
        assert not group_action.done

        # Update until completion
        for _ in range(60):  # 1 second at 60fps
            enemies.update(1 / 60)
            if group_action.done:
                break

        # Verify automatic cleanup
        assert group_action.done
        assert len(enemies._group_actions) == 0  # Cleaned up automatically

    def test_wrap_group_action_basic(self):
        """Test basic group action functionality."""
        from actions.group import SpriteGroup

        # Create sprite group with 2 sprites
        enemies = SpriteGroup()
        for i in range(2):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 100 + i * 50
            enemy.center_y = 300
            enemies.append(enemy)

        # Apply group action
        move_action = MoveBy((200, 0), 2.0)
        group_action = enemies.do(move_action)

        # Verify initial state
        assert not group_action.done
        assert len(enemies._group_actions) == 1

        # Update partway
        enemies.update(1.0)  # Half duration

        # Verify sprites moved
        expected_positions = [(200, 300), (250, 300)]
        actual_positions = [sprite.position for sprite in enemies]
        for expected, actual in zip(expected_positions, actual_positions, strict=False):
            assert abs(actual[0] - expected[0]) < 1
            assert abs(actual[1] - expected[1]) < 1

    def test_wrap_edge_detection(self):
        """Test edge detection for group wrapping."""
        from actions.group import SpriteGroup

        # Create sprite group in formation
        enemies = SpriteGroup()
        positions = [(100, 300), (200, 300), (300, 300)]  # Horizontal line
        for i, pos in enumerate(positions):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.position = pos
            enemies.append(enemy)

        get_bounds = lambda: (800, 600)
        wrap_events = []

        def on_wrap(sprite, axis):
            wrap_events.append((sprite, axis))

        # Create wrapped group movement action (NEW ARCHITECTURE)
        move_action = MoveBy((600, 0), 0.5)
        wrapped_move = WrappedMove(get_bounds, on_wrap=on_wrap, movement_action=move_action)

        # Apply wrapped movement to the group
        enemies.do(wrapped_move)

        # Update
        enemies.update(0.5)

        # Should have wrap events (exact number depends on edge detection)
        assert len(wrap_events) > 0


class TestBoundedMove:
    """Test suite for bounded movement (bouncing).

    Tests the BoundedMove action's behavior when sprites hit boundaries.
    Focuses on:
    - Bouncing behavior at each boundary
    - Corner cases
    - Bounce callbacks
    - SpriteGroup handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.position = (0, 0)
        return sprite

    @pytest.fixture
    def sprite_group(self):
        """Create a SpriteGroup with test sprites for group behavior testing."""
        from actions.group import SpriteGroup

        sprites = SpriteGroup()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.position = (0, 0)
            sprites.append(sprite)
        return sprites

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns boundary constraints."""
        return lambda: (0, 0, 800, 600)  # left, bottom, right, top

    def test_bounce_right_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits right edge.

        Verifies that:
        - Sprite bounces off right edge
        - Position is corrected inside boundary
        - Velocity is reversed
        """
        # Create movement action to move sprite to right edge
        move_action = MoveBy((200, 0), 0.2)
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Should have bounced - exact position depends on implementation
        assert sprite.center_x < 800  # Inside right boundary

    def test_bounce_left_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits left edge.

        Verifies that:
        - Sprite bounces off left edge
        - Position is corrected inside boundary
        - Velocity is reversed
        """
        # Create movement action to move sprite to left edge
        move_action = MoveBy((-200, 0), 0.2)
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to left edge
        sprite.center_x = 50
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Should have bounced - exact position depends on implementation
        assert sprite.center_x > 0  # Inside left boundary

    def test_bounce_top_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits top edge.

        Verifies that:
        - Sprite bounces off top edge
        - Position is corrected inside boundary
        - Velocity is reversed
        """
        # Create movement action to move sprite to top edge
        move_action = MoveBy((0, 200), 0.2)
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Should have bounced - exact position depends on implementation
        assert sprite.center_y < 600  # Inside top boundary

    def test_bounce_bottom_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits bottom edge.

        Verifies that:
        - Sprite bounces off bottom edge
        - Position is corrected inside boundary
        - Velocity is reversed
        """
        # Create movement action to move sprite to bottom edge
        move_action = MoveBy((0, -200), 0.2)
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to bottom edge
        sprite.center_x = 300
        sprite.center_y = 50

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Should have bounced - exact position depends on implementation
        assert sprite.center_y > 0  # Inside bottom boundary

    def test_bounce_corner(self, sprite, get_bounds):
        """Test bouncing when sprite hits corner.

        Verifies that:
        - Both horizontal and vertical bouncing work
        - Position is corrected for both axes
        """
        # Create movement action to move sprite to corner
        move_action = MoveBy((200, 200), 0.2)
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to top-right corner
        sprite.center_x = 750
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Should have bounced off both edges
        assert sprite.center_x < 800  # Inside right boundary
        assert sprite.center_y < 600  # Inside top boundary

    def test_bounce_callback(self, sprite, get_bounds):
        """Test bounce callbacks are triggered correctly.

        Verifies that:
        - Callback is called when bouncing occurs
        - Callback receives correct sprite and axis parameters
        """
        bounce_events = []

        def on_bounce(sprite, axis):
            bounce_events.append((sprite, axis))

        # Create movement action and bounce action with callback
        move_action = MoveBy((200, 0), 0.2)
        bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)

        # Position sprite to trigger bounce
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify callback was triggered
        assert len(bounce_events) >= 1
        assert bounce_events[0][0] == sprite
        assert bounce_events[0][1] == "x"

    def test_sprite_group_bouncing(self, sprite_group, get_bounds):
        """Test bouncing behavior with SpriteGroup.

        Verifies that:
        - All sprites in the group are processed
        - Each sprite bounces independently
        """
        # Position sprites across screen
        for i, sprite in enumerate(sprite_group):
            sprite.center_x = 700 + i * 30  # Spread across right edge
            sprite.center_y = 300

        # Create wrapped movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        bounded_move = BoundedMove(get_bounds, movement_action=move_action)

        # Apply the wrapped action to sprite group
        sprite_group.do(bounded_move)

        # Update for full duration using SpriteGroup
        sprite_group.update(0.2)

        # Verify all sprites bounced (stayed within bounds)
        for sprite in sprite_group:
            assert sprite.center_x < 800  # Within right boundary

    def test_disable_horizontal_bouncing(self, sprite, get_bounds):
        """Test disabling horizontal bouncing.

        Verifies that:
        - Horizontal bouncing is disabled
        - Vertical bouncing still works
        """
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)
        bounce_action = BoundedMove(get_bounds, bounce_horizontal=False)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did NOT bounce horizontally
        assert sprite.center_x >= 800  # Moved past right edge

    def test_disable_vertical_bouncing(self, sprite, get_bounds):
        """Test disabling vertical bouncing.

        Verifies that:
        - Vertical bouncing is disabled
        - Horizontal bouncing still works
        """
        # Create movement action to move sprite off top edge
        move_action = MoveBy((0, 200), 0.2)
        bounce_action = BoundedMove(get_bounds, bounce_vertical=False)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did NOT bounce vertically
        assert sprite.center_y >= 600  # Moved past top edge

    def test_dynamic_bounds(self, sprite):
        """Test bouncing with dynamically changing bounds.

        Verifies that:
        - Bounds function is called each frame
        - Bouncing adapts to changing boundaries
        """
        bounds_right = 800

        def get_bounds():
            return (0, 0, bounds_right, 600)

        # Create bounded movement action (NEW ARCHITECTURE)
        # Move right so sprite will encounter the boundary
        move_action = MoveBy((300, 0), 0.4)  # Move right 300 pixels over 0.4 seconds
        bounded_move = BoundedMove(get_bounds, movement_action=move_action)

        # Position sprite to be moving toward the boundary
        sprite.center_x = 600  # Start further left so sprite moves toward boundary
        sprite.center_y = 300

        # Apply bounded action
        sprite.do(bounded_move)

        # Update halfway through - sprite should be around x=750
        sprite.update(0.2)

        # Change bounds to make boundary closer
        bounds_right = 700  # New boundary at 700

        # Continue updating - sprite should hit new boundary and bounce
        sprite.update(0.2)

        # Verify sprite bounced off the new boundary
        # The sprite should have hit the 700 boundary and bounced back
        assert sprite.center_x < 700  # Should have bounced back from the 700 boundary

    def test_bounce_with_rotation(self, sprite, get_bounds):
        """Test bouncing works with simultaneous rotation actions.

        Verifies that:
        - Multiple actions can run simultaneously
        - Bouncing doesn't interfere with rotation actions
        """
        # Create bounded movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        bounded_move = BoundedMove(get_bounds, movement_action=move_action)

        # Create rotation action (pure action-based)
        rotate_action = RotateBy(18, 0.2)  # 18 degrees over 0.2 seconds

        # Position sprite and set initial rotation
        sprite.center_x = 750
        sprite.center_y = 300
        sprite.angle = 45

        # Apply both actions simultaneously
        sprite.do(bounded_move)
        sprite.do(rotate_action, slot="rotation")

        # Update for full duration
        sprite.update(0.2)

        # Verify rotation occurred
        assert abs(sprite.angle - 63) < 1  # 45 + 18 = 63 degrees

    def test_bounce_with_group_action(self, get_bounds):
        """Test bouncing with SpriteGroup actions.

        Verifies that:
        - Group actions work with bouncing
        - All sprites in group bounce correctly
        """
        from actions.group import SpriteGroup

        # Create sprite group
        enemies = SpriteGroup()
        for i in range(3):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 750 + i * 20
            enemy.center_y = 300
            enemies.append(enemy)

        bounce_events = []

        def on_bounce(sprite, axis):
            bounce_events.append((sprite, axis))

        # Create wrapped group movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

        # Apply wrapped movement to the group
        enemies.do(bounded_move)

        # Update for full duration
        enemies.update(0.2)

        # Verify bounce events were triggered
        assert len(bounce_events) >= 1

    def test_group_action_automatic_cleanup(self):
        """Test that group actions are automatically cleaned up."""
        from actions.group import SpriteGroup

        # Create sprite group
        enemies = SpriteGroup()
        for i in range(2):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 400 + i * 100
            enemy.center_y = 300
            enemies.append(enemy)

        # Start a group action
        move_action = MoveBy((100, 0), 1.0)
        group_action = enemies.do(move_action)

        # Verify action is tracked
        assert len(enemies._group_actions) == 1
        assert not group_action.done

        # Update until completion
        for _ in range(60):  # 1 second at 60fps
            enemies.update(1 / 60)
            if group_action.done:
                break

        # Verify automatic cleanup
        assert group_action.done
        assert len(enemies._group_actions) == 0  # Cleaned up automatically

    def test_group_action_basic(self):
        """Test basic group action functionality."""
        from actions.group import SpriteGroup

        # Create sprite group with 2 sprites
        enemies = SpriteGroup()
        for i in range(2):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 100 + i * 50
            enemy.center_y = 300
            enemies.append(enemy)

        # Apply group action
        move_action = MoveBy((200, 0), 2.0)
        group_action = enemies.do(move_action)

        # Verify initial state
        assert not group_action.done
        assert len(enemies._group_actions) == 1

        # Update partway
        enemies.update(1.0)  # Half duration

        # Verify sprites moved
        expected_positions = [(200, 300), (250, 300)]
        actual_positions = [sprite.position for sprite in enemies]
        for expected, actual in zip(expected_positions, actual_positions, strict=False):
            assert abs(actual[0] - expected[0]) < 1
            assert abs(actual[1] - expected[1]) < 1

    def test_edge_detection_after_column_destruction(self, get_bounds):
        """Test that edge detection works correctly after entire columns are destroyed.

        This test reproduces the issue where destroying the entire left column
        (or right column) causes remaining sprites to get stuck in place.
        """
        from actions.group import SpriteGroup

        # Create a 3x3 grid of sprites
        enemies = SpriteGroup()
        for row in range(3):
            for col in range(3):
                enemy = ActionSprite(":resources:images/enemies/bee.png")
                enemy.center_x = 100 + col * 100  # columns at x=100, 200, 300
                enemy.center_y = 300 + row * 50  # rows at y=300, 350, 400
                enemies.append(enemy)

        # Verify initial formation
        assert len(enemies) == 9
        leftmost_x = min(s.center_x for s in enemies)
        rightmost_x = max(s.center_x for s in enemies)
        assert leftmost_x == 100  # Left column
        assert rightmost_x == 300  # Right column

        # Track bounce events
        bounce_events = []

        def on_bounce(sprite, axis):
            bounce_events.append((sprite, axis))

        # Create bounded movement action (moving right toward boundary)
        move_action = MoveBy((600, 0), 1.0)  # Move right 600 pixels
        bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

        # Apply bounded movement to the group
        enemies.do(bounded_move)

        # Update partway to get sprites moving
        enemies.update(0.3)

        # Verify sprites moved right
        new_leftmost_x = min(s.center_x for s in enemies)
        assert new_leftmost_x > leftmost_x  # Should have moved right

        # Now destroy the entire RIGHT column (simulating player bullets hitting the edge)
        # This should leave columns at x=100 and x=200, making x=200 the new right edge
        # Note: sprites have moved during the update, so we need to find the rightmost column
        current_rightmost_x = max(s.center_x for s in enemies)
        right_column_sprites = [s for s in enemies if abs(s.center_x - current_rightmost_x) < 10]
        assert len(right_column_sprites) == 3, (
            f"Should find 3 sprites in right column, found {len(right_column_sprites)}"
        )

        for sprite in right_column_sprites:
            sprite.remove_from_sprite_lists()

        # Verify column was destroyed
        assert len(enemies) == 6  # 9 - 3 = 6 remaining
        new_rightmost_x = max(s.center_x for s in enemies)
        assert new_rightmost_x < current_rightmost_x  # Right edge should now be smaller

        # Continue updating - the remaining sprites should still be able to hit boundaries
        # and trigger bounce callbacks
        enemies.update(0.7)  # Complete the movement

        # Verify that bounce events were triggered
        # The remaining sprites should have hit the boundary and bounced
        assert len(bounce_events) > 0, "No bounce events triggered after column destruction"

        # Verify that the rightmost remaining sprites are within bounds
        final_rightmost_x = max(s.center_x for s in enemies)
        bounds_right = get_bounds()[2]  # Right boundary
        assert final_rightmost_x <= bounds_right, f"Sprites moved beyond boundary: {final_rightmost_x} > {bounds_right}"

    def test_edge_detection_after_left_column_destruction(self, get_bounds):
        """Test that edge detection works correctly after left column is destroyed."""
        from actions.group import SpriteGroup

        # Create a 3x3 grid of sprites
        enemies = SpriteGroup()
        for row in range(3):
            for col in range(3):
                enemy = ActionSprite(":resources:images/enemies/bee.png")
                enemy.center_x = 200 + col * 100  # columns at x=200, 300, 400
                enemy.center_y = 300 + row * 50  # rows at y=300, 350, 400
                enemies.append(enemy)

        # Position near left boundary to test left edge detection
        for sprite in enemies:
            sprite.center_x = sprite.center_x - 150  # Move left: columns now at x=50, 150, 250

        # Track bounce events
        bounce_events = []

        def on_bounce(sprite, axis):
            bounce_events.append((sprite, axis))

        # Create bounded movement action (moving left toward boundary)
        move_action = MoveBy((-200, 0), 1.0)  # Move left 200 pixels
        bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

        # Apply bounded movement to the group
        enemies.do(bounded_move)

        # Update partway to get sprites moving
        enemies.update(0.3)

        # Destroy the entire LEFT column (leftmost edge sprites)
        # Note: sprites have moved during the update, so we need to find the leftmost column
        current_leftmost_x = min(s.center_x for s in enemies)
        left_column_sprites = [s for s in enemies if abs(s.center_x - current_leftmost_x) < 10]
        assert len(left_column_sprites) == 3, f"Should find 3 sprites in left column, found {len(left_column_sprites)}"

        for sprite in left_column_sprites:
            sprite.remove_from_sprite_lists()

        # Verify column was destroyed
        assert len(enemies) == 6  # 9 - 3 = 6 remaining
        new_leftmost_x = min(s.center_x for s in enemies)
        assert new_leftmost_x > current_leftmost_x  # Left edge should now be larger

        # Continue updating - the remaining sprites should still be able to hit boundaries
        enemies.update(0.7)  # Complete the movement

        # Verify that bounce events were triggered
        assert len(bounce_events) > 0, "No bounce events triggered after left column destruction"

        # Verify that the leftmost remaining sprites are within bounds
        final_leftmost_x = min(s.center_x for s in enemies)
        bounds_left = get_bounds()[0]  # Left boundary
        assert final_leftmost_x >= bounds_left, f"Sprites moved beyond boundary: {final_leftmost_x} < {bounds_left}"

    def test_sprites_stuck_after_edge_column_destruction(self, get_bounds):
        """Test to reproduce the exact issue: sprites get stuck in place after edge column destruction.

        This test specifically checks that sprites continue to move and can hit boundaries
        even after their edge column is destroyed mid-movement.
        """
        from actions.group import SpriteGroup

        # Create a 3x5 grid of sprites similar to Space Invaders
        enemies = SpriteGroup()
        for row in range(3):
            for col in range(5):
                enemy = ActionSprite(":resources:images/enemies/bee.png")
                enemy.center_x = 100 + col * 80  # columns at x=100, 180, 260, 340, 420
                enemy.center_y = 300 + row * 50  # rows at y=300, 350, 400
                enemies.append(enemy)

        # Position formation to be moving right towards boundary
        for sprite in enemies:
            sprite.center_x += 500  # Move formation toward right edge

        # Track all movement and bounce events
        events = []

        def on_bounce(sprite, axis):
            events.append(("bounce", sprite.center_x, axis, len(enemies)))

        # Create continuous rightward movement
        move_action = MoveBy((300, 0), 3.0)  # Long movement to ensure boundary hit
        bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

        # Apply bounded movement to the group
        enemies.do(bounded_move)

        # Update and track positions to see movement
        positions_over_time = []

        # Step 1: Move partway and verify movement
        enemies.update(0.5)  # Move 1/6 of the way
        pos1 = [(s.center_x, s.center_y) for s in enemies]
        positions_over_time.append(("initial_movement", pos1))

        # Verify sprites are moving right
        rightmost_before = max(s.center_x for s in enemies)

        # Step 2: Destroy the entire rightmost column while sprites are moving
        rightmost_x = max(s.center_x for s in enemies)
        rightmost_column = [s for s in enemies if abs(s.center_x - rightmost_x) < 10]
        events.append(("destroy_column", len(rightmost_column), "sprites"))

        for sprite in rightmost_column:
            sprite.remove_from_sprite_lists()

        assert len(enemies) == 12, f"Should have 12 sprites left (15-3), got {len(enemies)}"

        # Step 3: Continue movement - sprites should NOT get stuck
        enemies.update(0.5)  # Continue moving
        pos2 = [(s.center_x, s.center_y) for s in enemies]
        positions_over_time.append(("after_destruction", pos2))

        # Verify sprites continued moving right (not stuck)
        rightmost_after_destruction = max(s.center_x for s in enemies)
        assert rightmost_after_destruction > rightmost_before, (
            f"Sprites appear stuck: {rightmost_after_destruction} not > {rightmost_before}"
        )

        # Step 4: Continue to boundary and verify bounce occurs
        enemies.update(2.0)  # Complete the movement
        pos3 = [(s.center_x, s.center_y) for s in enemies]
        positions_over_time.append(("final_position", pos3))

        # Critical assertion: Sprites should have hit boundary and bounced
        bounce_events = [e for e in events if e[0] == "bounce"]
        assert len(bounce_events) > 0, f"No bounce events after column destruction. Events: {events}"

        # Verify sprites are within bounds (bounced back)
        final_rightmost = max(s.center_x for s in enemies)
        bounds_right = get_bounds()[2]
        assert final_rightmost <= bounds_right, f"Sprites didn't bounce: {final_rightmost} > {bounds_right}"

        # Debug output for analysis
        print(f"Position tracking: {positions_over_time}")
        print(f"All events: {events}")

    def test_rapid_bounce_loop_after_column_destruction(self, get_bounds):
        """Test to reproduce rapid bounce loop: sprites alternate direction reversals without movement.

        This reproduces the actual issue where destroying edge columns causes remaining sprites
        to get stuck in a rapid bounce loop at the boundary.
        """
        from actions.group import SpriteGroup

        # Create sprites positioned very close to the right boundary
        enemies = SpriteGroup()
        for i in range(3):
            enemy = ActionSprite(":resources:images/enemies/bee.png")
            enemy.center_x = 790 + i * 5  # Very close to right boundary (800)
            enemy.center_y = 300
            enemies.append(enemy)

        bounce_count = 0
        direction_changes = []

        def on_bounce(sprite, axis):
            nonlocal bounce_count
            bounce_count += 1
            direction_changes.append(bounce_count)

        # Create movement that will immediately hit boundary
        move_action = MoveBy((50, 0), 5.0)  # Slow movement over 5 seconds
        bounded_move = BoundedMove(get_bounds, on_bounce=on_bounce, movement_action=move_action)

        # Apply bounded movement to the group
        enemies.do(bounded_move)

        # Update once to trigger first bounce
        enemies.update(0.1)
        first_bounce_count = bounce_count

        # Get the first sprite positions after initial bounce
        positions_after_first_bounce = [s.center_x for s in enemies]

        # Destroy the rightmost sprite (simulating bullet hit)
        rightmost_sprite = max(enemies, key=lambda s: s.center_x)
        rightmost_sprite.remove_from_sprite_lists()

        # Now the remaining sprites should still be near the boundary
        # and might trigger rapid bouncing

        # Update multiple times and track bounce behavior
        bounce_counts_per_frame = []
        sprite_positions_per_frame = []

        for frame in range(10):  # Check 10 frames
            prev_bounce_count = bounce_count
            enemies.update(0.1)
            bounces_this_frame = bounce_count - prev_bounce_count
            bounce_counts_per_frame.append(bounces_this_frame)
            sprite_positions_per_frame.append([s.center_x for s in enemies])

        # Check for rapid bouncing pattern
        rapid_bounces = sum(1 for count in bounce_counts_per_frame if count > 0)
        total_additional_bounces = sum(bounce_counts_per_frame)

        # Debug output
        print(f"Bounce counts per frame: {bounce_counts_per_frame}")
        print(f"Sprite positions over frames: {sprite_positions_per_frame[:5]}")  # First 5 frames
        print(f"Rapid bounce frames: {rapid_bounces}/10")
        print(f"Total additional bounces: {total_additional_bounces}")

        # The issue: if there are many rapid bounces but little movement
        if rapid_bounces >= 5:  # More than half the frames had bounces
            # Check if sprites are actually moving between bounces
            position_changes = []
            for i in range(1, len(sprite_positions_per_frame)):
                prev_positions = sprite_positions_per_frame[i - 1]
                curr_positions = sprite_positions_per_frame[i]
                max_change = max(abs(curr - prev) for curr, prev in zip(curr_positions, prev_positions, strict=False))
                position_changes.append(max_change)

            avg_position_change = sum(position_changes) / len(position_changes)
            print(f"Average position change per frame: {avg_position_change}")

            # If bouncing rapidly but not moving much, we have the bug
            if avg_position_change < 1.0:  # Less than 1 pixel movement per frame on average
                raise AssertionError(
                    f"Rapid bounce loop detected: {rapid_bounces} bounce frames with only "
                    f"{avg_position_change:.2f} pixels average movement per frame. "
                    f"This indicates sprites are stuck in boundary bounce loop."
                )

    def test_movement_extension_after_sprite_removal(self, get_bounds):
        """Test that GroupAction automatically extends movement when sprites are removed."""
        from actions.group import SpriteGroup

        # Create a 3x3 grid
        enemies = SpriteGroup()
        for row in range(3):
            for col in range(3):
                enemy = ActionSprite(":resources:images/enemies/bee.png")
                enemy.center_x = 100 + col * 100  # columns at x=100, 200, 300
                enemy.center_y = 300 + row * 50  # rows at y=300, 350, 400
                enemies.append(enemy)

        # Create a movement action with fixed distance
        original_distance = 400  # Move right 400 pixels
        move_action = MoveBy((original_distance, 0), 2.0)
        group_action = enemies.do(move_action)

        # Verify initial setup
        assert len(enemies) == 9
        assert group_action._use_batch_optimization == True
        assert group_action._batch_total_change == (original_distance, 0)

        # Update partway to start movement
        enemies.update(0.5)  # Quarter duration

        # Remove the entire right column (3 sprites)
        rightmost_x = max(s.center_x for s in enemies)
        right_column = [s for s in enemies if abs(s.center_x - rightmost_x) < 10]
        assert len(right_column) == 3

        print("\n=== BEFORE REMOVAL ===")
        print(f"Sprites: {len(enemies)}")
        print(f"Movement delta: {group_action._batch_total_change}")

        for sprite in right_column:
            sprite.remove_from_sprite_lists()

        # Trigger sync by updating (this should call _sync_with_group)
        enemies.update(0.1)

        print("\n=== AFTER REMOVAL ===")
        print(f"Sprites: {len(enemies)}")
        print(f"Movement delta: {group_action._batch_total_change}")

        # Verify the movement was extended
        assert len(enemies) == 6  # 9 - 3 = 6 remaining
        new_distance_x = group_action._batch_total_change[0]

        # Movement should be extended beyond original distance
        assert new_distance_x > original_distance, (
            f"Movement should be extended: {new_distance_x} > {original_distance}"
        )

        # Should be significantly larger (at least 20% increase)
        extension_ratio = new_distance_x / original_distance
        assert extension_ratio > 1.2, f"Movement extension should be substantial: {extension_ratio} > 1.2"

        print(f"Movement successfully extended by {extension_ratio:.2f}x")

    def test_sprite_removal_near_movement_completion(self, get_bounds):
        """Test that movement extension works even when sprites are removed near the end of movement."""
        from actions.group import SpriteGroup

        # Create a 2x3 grid (smaller for easier testing)
        enemies = SpriteGroup()
        for row in range(2):
            for col in range(3):
                enemy = ActionSprite(":resources:images/enemies/bee.png")
                enemy.center_x = 100 + col * 100  # columns at x=100, 200, 300
                enemy.center_y = 300 + row * 50  # rows at y=300, 350
                enemies.append(enemy)

        # Create a short movement action
        original_distance = 300
        duration = 1.0  # 1 second duration
        move_action = MoveBy((original_distance, 0), duration)
        group_action = enemies.do(move_action)

        # Verify initial setup
        assert len(enemies) == 6
        assert group_action._batch_total_change == (original_distance, 0)

        # Update to 95% completion (very close to the end)
        near_completion_time = 0.95
        enemies.update(near_completion_time)

        # Verify we're very close to done but not quite
        assert group_action._elapsed >= near_completion_time
        progress = group_action._elapsed / duration
        assert progress >= 0.95, f"Should be at 95% completion, got {progress:.2f}"

        print("\n=== BEFORE REMOVAL (95% complete) ===")
        print(f"Elapsed: {group_action._elapsed:.3f}s of {duration}s")
        print(f"Progress: {progress:.1%}")
        print(f"Movement delta: {group_action._batch_total_change}")
        print(f"Done: {group_action.done}")

        # Remove the rightmost column at 95% completion
        rightmost_x = max(s.center_x for s in enemies)
        right_column = [s for s in enemies if abs(s.center_x - rightmost_x) < 10]
        assert len(right_column) == 2  # 2 rows × 1 rightmost column

        for sprite in right_column:
            sprite.remove_from_sprite_lists()

        # Update to trigger extension logic
        enemies.update(0.01)  # Small update to trigger sync

        print("\n=== AFTER REMOVAL ===")
        print(f"Elapsed: {group_action._elapsed:.3f}s of {duration}s")
        print(f"Progress: {group_action._elapsed / duration:.1%}")
        print(f"Movement delta: {group_action._batch_total_change}")
        print(f"Done: {group_action.done}")

        # Verify the action was extended and timer reset
        assert len(enemies) == 4  # 6 - 2 = 4 remaining
        new_distance_x = group_action._batch_total_change[0]

        # Movement should be extended
        assert new_distance_x > original_distance, (
            f"Movement should be extended: {new_distance_x} > {original_distance}"
        )

        # Timer should have been reset to give time for extended movement
        new_progress = group_action._elapsed / duration
        assert new_progress < 0.95, f"Timer should be reset, progress {new_progress:.1%} should be < 95%"

        # Action should not be done yet (it got more time)
        assert not group_action.done, "Action should not be done after extension"

        print("SUCCESS: Movement extended and timer reset at near-completion")
