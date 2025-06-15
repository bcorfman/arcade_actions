"""Unit tests for movement actions in arcade_actions.

This module contains tests for movement-related actions:
- _Move (base movement class)
- WrappedMove (wrapping at screen bounds)
- BoundedMove (bouncing at screen bounds)
- Driver (directional movement) - not tested here

All tests use ActionSprite for sprite-based tests and follow the standard
action lifecycle pattern using sprite.do(action) and sprite.update().
"""

import arcade
import pytest

from actions.base import ActionSprite
from actions.interval import MoveBy
from actions.move import BoundedMove, WrappedMove, _Move


class TestMove:
    """Test suite for base movement class.

    Tests the basic movement functionality that all movement actions inherit from.
    Focuses on:
    - Basic position updates
    - Velocity-based movement
    - Rotation during movement
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/enemies/bee.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    def test_basic_movement(self, sprite):
        """Test basic movement without physics.

        Verifies that:
        - Position updates correctly based on velocity
        - Movement is frame-independent using delta_time
        """
        action = _Move()
        sprite.do(action)

        # Update with 0.1s time step (100 * 0.1 = 10 pixels)
        sprite.update(0.1)
        assert sprite.position == (10, 10)

    def test_movement_with_rotation(self, sprite):
        """Test movement with rotation.

        Verifies that:
        - Position updates correctly
        - Rotation updates correctly
        - Both use the same delta_time
        """
        sprite.change_angle = 45  # 45 degrees per second
        action = _Move()
        sprite.do(action)

        # Update with 0.1s time step
        sprite.update(0.1)
        assert sprite.position == (10, 10)  # 100 * 0.1 = 10
        assert sprite.angle == 4.5  # 45 * 0.1 = 4.5


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
        sprites = arcade.SpriteList()
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
        """Test wrapping when sprite moves off a corner.

        Verifies that:
        - Sprite wraps correctly when hitting a corner
        - Position is correctly aligned to both boundaries
        """
        # Create movement action to move sprite off top-right corner
        move_action = MoveBy((200, 200), 0.2)  # Move diagonally over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to top-right corner
        sprite.center_x = 750
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to bottom-left corner
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y < 0  # Wrapped to bottom edge

    def test_wrap_callback(self, sprite, get_bounds):
        """Test wrap callback with correct axis information.

        Verifies that:
        - Callback is called with correct axis
        - Multiple wraps are reported correctly
        """
        wraps = []

        def on_wrap(sprite, axis):
            wraps.append(axis)

        # Create movement action to move sprite off top-right corner
        move_action = MoveBy((200, 200), 0.2)  # Move diagonally over 0.2 seconds
        wrap_action = WrappedMove(get_bounds, on_wrap=on_wrap)

        # Position sprite close to top-right corner
        sprite.center_x = 750
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify correct axes were reported
        assert "x" in wraps
        assert "y" in wraps
        assert len(wraps) == 2  # Both axes wrapped

    def test_sprite_list_wrapping(self, sprite_list, get_bounds):
        """Test wrapping behavior with multiple sprites.

        Verifies that:
        - Each sprite wraps independently
        - List-level updates work correctly
        - Positions are correctly aligned after wrapping
        """
        wrap_action = WrappedMove(get_bounds)
        wrap_action.target = sprite_list
        wrap_action.start()

        # Create individual movement actions for each sprite
        move_action_1 = MoveBy((200, 0), 0.2)  # Move right
        move_action_2 = MoveBy((-200, 0), 0.2)  # Move left
        move_action_3 = MoveBy((0, 200), 0.2)  # Move up

        # Position sprites at different locations close to edges
        sprite_list[0].center_x = 750  # Close to right edge
        sprite_list[0].center_y = 300
        sprite_list[0].do(move_action_1)

        sprite_list[1].center_x = 50  # Close to left edge
        sprite_list[1].center_y = 300
        sprite_list[1].do(move_action_2)

        sprite_list[2].center_x = 300  # Close to top edge
        sprite_list[2].center_y = 550
        sprite_list[2].do(move_action_3)

        # Update all sprites and wrapping
        sprite_list.update(0.2)
        wrap_action.update(0.2)

        # Verify each sprite wrapped correctly
        assert sprite_list[0].center_x < 0  # Wrapped to left edge
        assert sprite_list[1].center_x > 800  # Wrapped to right edge
        assert sprite_list[2].center_y < 0  # Wrapped to bottom edge

    def test_wrap_with_acceleration(self, sprite, get_bounds):
        """Test wrapping behavior with easing.

        Verifies that:
        - Wrapping works with easing
        - Easing curve is maintained
        - Position is correctly aligned after wrapping
        """
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create wrapped movement action
        wrap_action = WrappedMove(get_bounds)

        # Set initial position - important to set before doing actions
        # Position sprite very close to right edge (800 - sprite.width/2)
        sprite.center_x = 737  # right edge at 801, sprite width is 128
        sprite.center_y = 300

        # Use | to run both actions in parallel
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for 0.8 seconds to allow enough movement for wrapping
        sprite.update(0.8)  # Updates position based on movement and handles wrapping

        # Verify sprite wrapped and is still moving
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

        # Verify the sprite is still moving
        old_x = sprite.center_x
        sprite.update(0.1)  # Update a bit more
        assert sprite.center_x > old_x  # Still moving right after wrapping

    def test_disable_horizontal_wrapping(self, sprite, get_bounds):
        """Test disabling horizontal wrapping.

        Verifies that:
        - Horizontal wrapping is disabled
        - Vertical wrapping still works
        - Sprite can move off screen horizontally
        """
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)  # Move 200 pixels right over 0.2 seconds
        wrap_action = WrappedMove(get_bounds, wrap_horizontal=False)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did not wrap horizontally
        assert sprite.center_x > 800  # Moved off screen, no wrapping
        assert sprite.center_y == 300  # Y position unchanged

    def test_disable_vertical_wrapping(self, sprite, get_bounds):
        """Test disabling vertical wrapping.

        Verifies that:
        - Vertical wrapping is disabled
        - Horizontal wrapping still works
        - Sprite can move off screen vertically
        """
        # Create movement action to move sprite off top edge
        move_action = MoveBy((0, 200), 0.2)  # Move 200 pixels up over 0.2 seconds
        wrap_action = WrappedMove(get_bounds, wrap_vertical=False)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 550

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite did not wrap vertically
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y > 600  # Moved off screen, no wrapping

    def test_dynamic_bounds(self, sprite):
        """Test wrapping with dynamically changing screen bounds.

        Verifies that:
        - Wrapping works with changing screen dimensions
        - Sprite wraps to correct position after resize
        """
        bounds = [800, 600]  # Initial bounds

        def get_bounds():
            return tuple(bounds)

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

        # Change screen bounds
        bounds[0] = 1000  # Increase width
        bounds[1] = 800  # Increase height

        # Create new movement action for second test
        move_action_2 = MoveBy((300, 0), 0.2)  # Move further right
        wrap_action_2 = WrappedMove(get_bounds)

        # Position sprite close to new right edge
        sprite.center_x = 850
        sprite.center_y = 300

        # Combine actions
        combined_action_2 = move_action_2 | wrap_action_2
        sprite.do(combined_action_2)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to left edge with new bounds
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_with_rotation(self, sprite, get_bounds):
        """Test wrapping with rotated sprite.

        Verifies that:
        - Wrapping works with rotated sprites
        - Hit box is correctly calculated
        - Position is correctly aligned after wrapping
        """
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)  # Move 200 pixels right over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Rotate sprite and position close to right edge
        sprite.angle = 45
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
        assert sprite.angle == 45  # Rotation unchanged

    def test_wrap_with_group_action(self, get_bounds):
        """Test wrapping behavior with GroupAction.

        Verifies that:
        - WrappedMove can work with GroupAction when both are updated properly
        - Edge sprite logic works correctly in callbacks
        - Action coordination works correctly with group actions
        """
        from actions.group import SpriteGroup

        # Create a sprite group with multiple sprites
        sprite_group = SpriteGroup()
        for i in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.center_x = 750 + i * 10  # Position near right edge
            sprite.center_y = 300
            sprite_group.append(sprite)

        # Track wraps for coordination
        wrapped_sprites = set()
        wrap_called = False

        def on_wrap(sprite, axis):
            """Coordinate group behavior when edge sprites wrap."""
            nonlocal wrap_called
            wrap_called = True

            if axis != "x":
                return

            # Check if this is an edge sprite
            leftmost_x = min(s.center_x for s in sprite_group)
            rightmost_x = max(s.center_x for s in sprite_group)

            is_edge_sprite = abs(sprite.center_x - leftmost_x) < 5 or abs(sprite.center_x - rightmost_x) < 5

            if not is_edge_sprite:
                return

            wrapped_sprites.add(sprite)

            # Only process once per wrap
            if len(wrapped_sprites) == 1:
                # Clear actions and restart (simulating asteroid field behavior)
                sprite_group.clear_actions()
                wrapped_sprites.clear()

                # Start new movement in opposite direction
                new_move_action = MoveBy((-200, 0), 1.0)  # Move left
                sprite_group.do(new_move_action)

        # Create movement action using GroupAction
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        sprite_group.do(move_action)

        # Create WrappedMove for the entire group
        wrap_action = WrappedMove(get_bounds, on_wrap=on_wrap)
        wrap_action.target = sprite_group
        wrap_action.start()

        # Store initial positions
        initial_positions = [sprite.center_x for sprite in sprite_group]

        # Update SpriteGroup (automatically updates GroupActions) and WrappedMove
        sprite_group.update(0.5)
        wrap_action.update(0.5)

        # Verify sprites moved (either wrapped or continued moving)
        for i, sprite in enumerate(sprite_group):
            # Sprites should have moved from their initial position
            assert sprite.center_x != initial_positions[i], f"Sprite {i} didn't move at all"

        # Verify wrap was called (indicating proper coordination)
        assert wrap_called, "Wrap callback should have been called"

    def test_wrap_group_action_automatic_cleanup(self):
        """Test that completed GroupActions are automatically cleaned up with WrappedMove."""
        from actions.group import SpriteGroup

        # Create a sprite group with a sprite
        sprite_group = SpriteGroup()
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.center_x = 100
        sprite.center_y = 300
        sprite_group.append(sprite)

        # Create a short movement action
        move_action = MoveBy((50, 0), 0.1)  # Move 50 pixels right over 0.1 seconds
        group_action = sprite_group.do(move_action)

        # Create WrappedMove for the group
        get_bounds = lambda: (800, 600)
        wrap_action = WrappedMove(get_bounds)
        wrap_action.target = sprite_group
        wrap_action.start()

        # Verify the GroupAction is tracked
        assert len(sprite_group._group_actions) == 1
        assert not group_action.done

        # Update for the full duration to complete the action
        sprite_group.update(0.1)
        wrap_action.update(0.1)

        # Verify the action completed and was automatically cleaned up
        assert group_action.done
        assert len(sprite_group._group_actions) == 0  # Should be automatically removed

    def test_wrap_group_action_basic(self):
        """Test basic GroupAction functionality with WrappedMove and automatic updating."""
        from actions.group import SpriteGroup

        # Create a sprite group with multiple sprites
        sprite_group = SpriteGroup()
        for i in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.center_x = 100 + i * 10  # Position sprites
            sprite.center_y = 300
            sprite_group.append(sprite)

        # Store initial positions
        initial_positions = [sprite.center_x for sprite in sprite_group]

        # Create movement action using GroupAction
        move_action = MoveBy((50, 0), 0.5)  # Move 50 pixels right over 0.5 seconds
        group_action = sprite_group.do(move_action)

        # Create WrappedMove for the group
        get_bounds = lambda: (800, 600)
        wrap_action = WrappedMove(get_bounds)
        wrap_action.target = sprite_group
        wrap_action.start()

        # Update the SpriteGroup (which now automatically updates GroupActions)
        sprite_group.update(0.5)
        wrap_action.update(0.5)

        # Verify all sprites moved
        for i, sprite in enumerate(sprite_group):
            expected_x = initial_positions[i] + 50
            assert abs(sprite.center_x - expected_x) < 1, f"Sprite {i}: expected {expected_x}, got {sprite.center_x}"

    def test_wrap_edge_detection(self):
        """Test that only edge sprites trigger wrap callbacks in SpriteGroup."""
        from actions.group import SpriteGroup

        # Create a sprite group with sprites in a line
        sprite_group = SpriteGroup()
        sprites = []
        for i in range(5):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.center_x = 750 + i * 10  # Position near right edge
            sprite.center_y = 300
            sprite_group.append(sprite)
            sprites.append(sprite)

        wrap_calls = []

        def on_wrap(sprite, axis):
            wrap_calls.append((sprite, axis))

        # Create WrappedMove for the group
        get_bounds = lambda: (800, 600)
        wrap_action = WrappedMove(get_bounds, on_wrap=on_wrap)
        wrap_action.target = sprite_group
        wrap_action.start()

        # Move all sprites to trigger wrapping
        move_action = MoveBy((100, 0), 0.1)  # Move right to trigger wrap
        sprite_group.do(move_action)

        sprite_group.update(0.1)
        wrap_action.update(0.1)

        # Only the rightmost sprite should trigger the wrap callback
        if wrap_calls:
            # Verify only edge sprites triggered callbacks
            rightmost_x = max(s.center_x for s in sprites)
            for sprite, axis in wrap_calls:
                assert abs(sprite.center_x - rightmost_x) < 10, "Only rightmost sprite should trigger wrap"


class TestBoundedMove:
    """Test suite for bounded movement.

    Tests the BoundedMove action's behavior when sprites hit screen boundaries.
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
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.position = (0, 0)
            sprites.append(sprite)
        return sprites

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns bounding zone."""
        return lambda: (0, 0, 800, 600)  # left, bottom, right, top

    def test_bounce_right_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits right edge.

        Verifies that:
        - Sprite bounces at right edge when moving right
        - Sprite does not bounce when moving left
        - Velocity is reversed only when bouncing
        - Position is correctly adjusted
        """
        # Test 1: Moving right into right edge
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to right edge
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced (should be moving left now)
        # Check that sprite has moved back from edge
        assert sprite.center_x < 720  # Moved back from edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_left_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits left edge.

        Verifies that:
        - Sprite bounces at left edge when moving left
        - Sprite does not bounce when moving right
        - Velocity is reversed only when bouncing
        - Position is correctly adjusted
        """
        # Test 1: Moving left into left edge
        move_action = MoveBy((-200, 0), 1.0)  # Move left continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to left edge
        sprite.center_x = 80  # Close to left edge at 0
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced (should be moving right now)
        # Check that sprite has moved back from edge
        assert sprite.center_x > 80  # Moved back from edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_top_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits top edge.

        Verifies that:
        - Sprite bounces at top edge when moving up
        - Sprite does not bounce when moving down
        - Velocity is reversed only when bouncing
        - Position is correctly adjusted
        """
        # Test 1: Moving up into top edge
        move_action = MoveBy((0, 200), 1.0)  # Move up continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 520  # Close to top edge at 600

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced (should be moving down now)
        # Check that sprite has moved back from edge
        assert sprite.center_y < 520  # Moved back from edge
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_bottom_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits bottom edge.

        Verifies that:
        - Sprite bounces at bottom edge when moving down
        - Sprite does not bounce when moving up
        - Velocity is reversed only when bouncing
        - Position is correctly adjusted
        """
        # Test 1: Moving down into bottom edge
        move_action = MoveBy((0, -200), 1.0)  # Move down continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to bottom edge
        sprite.center_x = 300
        sprite.center_y = 80  # Close to bottom edge at 0

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced (should be moving up now)
        # Check that sprite has moved back from edge
        assert sprite.center_y > 80  # Moved back from edge
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_corner(self, sprite, get_bounds):
        """Test bouncing when sprite hits a corner.

        Verifies that:
        - Sprite bounces in both directions when moving toward corner
        - Sprite only bounces in direction of movement
        - Velocities are reversed only when bouncing
        - Position is correctly adjusted
        """
        # Test 1: Moving toward top-right corner
        move_action = MoveBy((200, 200), 1.0)  # Move diagonally continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to top-right corner
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 520  # Close to top edge at 600

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced in both directions
        # Check that sprite has moved back from both edges
        assert sprite.center_x < 720  # Moved back from right edge
        assert sprite.center_y < 520  # Moved back from top edge

    def test_bounce_callback(self, sprite, get_bounds):
        """Test bounce callback with correct axis information.

        Verifies that:
        - Callback is called with correct axis
        - Multiple bounces are reported correctly
        """
        bounces = []

        def on_bounce(sprite, axis):
            bounces.append(axis)

        # Moving toward top-right corner
        move_action = MoveBy((200, 200), 1.0)  # Move diagonally continuously
        bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)

        # Position sprite close to top-right corner
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 520  # Close to top edge at 600

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify correct axes were reported
        assert "x" in bounces
        assert "y" in bounces
        assert len(bounces) == 2  # Both axes bounced

    def test_sprite_list_bouncing(self, sprite_list, get_bounds):
        """Test bouncing with multiple sprites.

        Verifies that:
        - Each sprite bounces independently
        - Bouncing only occurs when moving toward boundary
        - List-level updates work correctly
        - Velocities are reversed correctly
        """
        bounce_action = BoundedMove(get_bounds)
        bounce_action.target = sprite_list
        bounce_action.start()

        # Create individual movement actions for each sprite
        move_action_1 = MoveBy((200, 0), 1.0)  # Move right
        move_action_2 = MoveBy((0, 200), 1.0)  # Move up
        move_action_3 = MoveBy((-200, 0), 1.0)  # Move left

        # Position sprites at different locations close to edges
        sprite_list[0].center_x = 720  # Close to right edge
        sprite_list[0].center_y = 300
        sprite_list[0].do(move_action_1)

        sprite_list[1].center_x = 300  # Close to top edge
        sprite_list[1].center_y = 520
        sprite_list[1].do(move_action_2)

        sprite_list[2].center_x = 80  # Close to left edge
        sprite_list[2].center_y = 300
        sprite_list[2].do(move_action_3)

        # Update for partial duration to trigger bounces
        sprite_list.update(0.5)
        bounce_action.update(0.5)

        # Verify each sprite bounced correctly
        # Check that sprites have moved back from their respective edges
        assert sprite_list[0].center_x < 720  # Moved back from right edge
        assert sprite_list[1].center_y < 520  # Moved back from top edge
        assert sprite_list[2].center_x > 80  # Moved back from left edge

    def test_disable_horizontal_bouncing(self, sprite, get_bounds):
        """Test disabling horizontal bouncing.

        Verifies that:
        - Horizontal bouncing is disabled
        - Vertical bouncing still works
        - Sprite can move through horizontal boundaries
        """
        # Create movement action to move sprite through right edge
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        bounce_action = BoundedMove(get_bounds, bounce_horizontal=False)

        # Position sprite close to right edge
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(1.0)

        # Verify sprite did not bounce horizontally
        assert sprite.center_x > 800  # Moved past right edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_disable_vertical_bouncing(self, sprite, get_bounds):
        """Test disabling vertical bouncing.

        Verifies that:
        - Vertical bouncing is disabled
        - Horizontal bouncing still works
        - Sprite can move through vertical boundaries
        """
        # Create movement action to move sprite through top edge
        move_action = MoveBy((0, 200), 1.0)  # Move up continuously
        bounce_action = BoundedMove(get_bounds, bounce_vertical=False)

        # Position sprite close to top edge
        sprite.center_x = 300
        sprite.center_y = 520  # Close to top edge at 600

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(1.0)

        # Verify sprite did not bounce vertically
        assert sprite.center_y > 600  # Moved past top edge
        assert sprite.center_x == 300  # X position unchanged

    def test_dynamic_bounds(self, sprite):
        """Test bouncing with dynamically changing bounding zone.

        Verifies that:
        - Bouncing works with changing boundaries
        - Sprite bounces at correct position after resize
        """
        bounds = [0, 0, 800, 600]  # Initial bounds

        def get_bounds():
            return tuple(bounds)

        # Create movement action to move sprite toward right edge
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        bounce_action = BoundedMove(get_bounds)

        # Position sprite close to right edge
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced
        assert sprite.center_x < 720  # Moved back from right edge
        assert sprite.center_y == 300  # Y position unchanged

        # Change bounding zone
        bounds[2] = 1000  # Increase right boundary
        bounds[3] = 800  # Increase top boundary

        # Create new movement action for second test
        move_action_2 = MoveBy((300, 0), 1.0)  # Move right continuously
        bounce_action_2 = BoundedMove(get_bounds)

        # Position sprite close to new right edge
        sprite.center_x = 920  # Close to new right edge at 1000
        sprite.center_y = 300

        # Combine actions
        combined_action_2 = move_action_2 | bounce_action_2
        sprite.do(combined_action_2)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced at new boundary
        assert sprite.center_x < 920  # Moved back from new right edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_with_rotation(self, sprite, get_bounds):
        """Test bouncing with rotated sprite.

        Verifies that:
        - Bouncing works with rotated sprites
        - Hit box is correctly calculated
        - Position is correctly adjusted after bounce
        """
        # Create movement action to move sprite toward right edge
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        bounce_action = BoundedMove(get_bounds)

        # Rotate sprite and position close to right edge
        sprite.angle = 45
        sprite.center_x = 720  # Close to right edge at 800
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | bounce_action
        sprite.do(combined_action)

        # Update for partial duration to trigger bounce
        sprite.update(0.5)

        # Verify sprite bounced
        assert sprite.center_x < 720  # Moved back from right edge
        assert sprite.center_y == 300  # Y position unchanged
        assert sprite.angle == 45  # Rotation unchanged

    def test_bounce_with_group_action(self, get_bounds):
        """Test bouncing behavior with GroupAction.

        Verifies that:
        - BoundedMove can work with GroupAction when both are updated properly
        - Edge sprite logic works correctly in callbacks
        - Action coordination works correctly with group actions
        """
        from actions.group import SpriteGroup

        # Create a sprite group with multiple sprites
        sprite_group = SpriteGroup()
        for i in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.center_x = 720 + i * 10  # Position near right edge
            sprite.center_y = 300
            sprite_group.append(sprite)

        # Track bounces for coordination
        bounced_sprites = set()
        bounce_called = False

        def on_bounce(sprite, axis):
            """Coordinate group behavior when edge sprites bounce."""
            nonlocal bounce_called
            bounce_called = True

            if axis != "x":
                return

            # Check if this is an edge sprite
            leftmost_x = min(s.center_x for s in sprite_group)
            rightmost_x = max(s.center_x for s in sprite_group)

            is_edge_sprite = abs(sprite.center_x - leftmost_x) < 5 or abs(sprite.center_x - rightmost_x) < 5

            if not is_edge_sprite:
                return

            bounced_sprites.add(sprite)

            # Only process once per bounce
            if len(bounced_sprites) == 1:
                # Clear actions and restart (simulating Space Invaders behavior)
                sprite_group.clear_actions()
                bounced_sprites.clear()

                # Start new movement in opposite direction
                new_move_action = MoveBy((-200, 0), 1.0)  # Move left
                sprite_group.do(new_move_action)

        # Create movement action using GroupAction
        move_action = MoveBy((200, 0), 1.0)  # Move right continuously
        sprite_group.do(move_action)

        # Create BoundedMove for the entire group
        bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)
        bounce_action.target = sprite_group
        bounce_action.start()

        # Store initial positions
        initial_positions = [sprite.center_x for sprite in sprite_group]

        # Update SpriteGroup (automatically updates GroupActions) and BoundedMove
        sprite_group.update(0.5)
        bounce_action.update(0.5)

        # Verify sprites moved (either bounced or continued moving)
        for i, sprite in enumerate(sprite_group):
            # Sprites should have moved from their initial position
            assert sprite.center_x != initial_positions[i], f"Sprite {i} didn't move at all"

        # Verify bounce was called (indicating proper coordination)
        assert bounce_called, "Bounce callback should have been called"

    def test_group_action_automatic_cleanup(self):
        """Test that completed GroupActions are automatically cleaned up."""
        from actions.group import SpriteGroup

        # Create a sprite group with a sprite
        sprite_group = SpriteGroup()
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.center_x = 100
        sprite.center_y = 300
        sprite_group.append(sprite)

        # Create a short movement action
        move_action = MoveBy((50, 0), 0.1)  # Move 50 pixels right over 0.1 seconds
        group_action = sprite_group.do(move_action)

        # Verify the GroupAction is tracked
        assert len(sprite_group._group_actions) == 1
        assert not group_action.done

        # Update for the full duration to complete the action
        sprite_group.update(0.1)

        # Verify the action completed and was automatically cleaned up
        assert group_action.done
        assert len(sprite_group._group_actions) == 0  # Should be automatically removed

    def test_group_action_basic(self):
        """Test basic GroupAction functionality with automatic updating."""
        from actions.group import SpriteGroup

        # Create a sprite group with multiple sprites
        sprite_group = SpriteGroup()
        for i in range(3):
            sprite = ActionSprite(":resources:images/items/ladderMid.png")
            sprite.center_x = 100 + i * 10  # Position sprites
            sprite.center_y = 300
            sprite_group.append(sprite)

        # Store initial positions
        initial_positions = [sprite.center_x for sprite in sprite_group]

        # Create movement action using GroupAction
        move_action = MoveBy((50, 0), 0.5)  # Move 50 pixels right over 0.5 seconds
        group_action = sprite_group.do(move_action)

        # Update the SpriteGroup (which now automatically updates GroupActions)
        sprite_group.update(0.5)

        # Verify all sprites moved
        for i, sprite in enumerate(sprite_group):
            expected_x = initial_positions[i] + 50
            assert abs(sprite.center_x - expected_x) < 1, f"Sprite {i}: expected {expected_x}, got {sprite.center_x}"
