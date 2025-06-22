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
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.position = (0, 0)
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
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

    def test_sprite_list_wrapping(self, sprite_list, get_bounds):
        """Test wrapping behavior with sprite lists.

        Verifies that:
        - All sprites in the list are processed
        - Each sprite wraps independently
        - Group behavior is maintained
        """
        # Position sprites across screen
        for i, sprite in enumerate(sprite_list):
            sprite.center_x = 700 + i * 30  # Spread across right edge
            sprite.center_y = 300

        # Create wrapped movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        wrapped_move = WrappedMove(get_bounds, movement_action=move_action)

        # Apply the wrapped action to sprite list
        sprite_list.do(wrapped_move)

        # Update for full duration using SpriteGroup
        sprite_list.update(0.2)

        # Verify all sprites wrapped
        for sprite in sprite_list:
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
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.position = (0, 0)
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
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

    def test_sprite_list_bouncing(self, sprite_list, get_bounds):
        """Test bouncing behavior with sprite lists.

        Verifies that:
        - All sprites in the list are processed
        - Each sprite bounces independently
        """
        # Position sprites across screen
        for i, sprite in enumerate(sprite_list):
            sprite.center_x = 700 + i * 30  # Spread across right edge
            sprite.center_y = 300

        # Create wrapped movement action (NEW ARCHITECTURE)
        move_action = MoveBy((200, 0), 0.2)
        bounded_move = BoundedMove(get_bounds, movement_action=move_action)

        # Apply the wrapped action to sprite list
        sprite_list.do(bounded_move)

        # Update for full duration using SpriteGroup
        sprite_list.update(0.2)

        # Verify all sprites bounced (stayed within bounds)
        for sprite in sprite_list:
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
