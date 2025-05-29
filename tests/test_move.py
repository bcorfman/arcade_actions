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
import arcade.easing as easing
import pytest

from actions.base import ActionSprite
from actions.interval import Easing, MoveBy
from actions.move import Boundary, BoundedMove, WrappedMove, _Move


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
        sprite = ActionSprite(":resources:images/items/star.png")
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
    - Boundary callbacks
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    def test_wrap_right_edge(self, sprite):
        """Test wrapping when sprite moves off right edge.

        Verifies that:
        - Sprite wraps to left edge when moving right
        - Position is correctly aligned to boundary
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Position sprite off right edge
        sprite.position = (900, 300)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to left edge
        assert sprite.left == 0
        assert sprite.right == 64  # Sprite width

    def test_wrap_left_edge(self, sprite):
        """Test wrapping when sprite moves off left edge.

        Verifies that:
        - Sprite wraps to right edge when moving left
        - Position is correctly aligned to boundary
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Position sprite off left edge
        sprite.position = (-100, 300)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to right edge
        assert sprite.right == 800
        assert sprite.left == 736  # 800 - 64 (sprite width)

    def test_wrap_top_edge(self, sprite):
        """Test wrapping when sprite moves off top edge.

        Verifies that:
        - Sprite wraps to bottom edge when moving up
        - Position is correctly aligned to boundary
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Position sprite off top edge
        sprite.position = (300, 700)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to bottom edge
        assert sprite.bottom == 0
        assert sprite.top == 64  # Sprite height

    def test_wrap_bottom_edge(self, sprite):
        """Test wrapping when sprite moves off bottom edge.

        Verifies that:
        - Sprite wraps to top edge when moving down
        - Position is correctly aligned to boundary
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Position sprite off bottom edge
        sprite.position = (300, -100)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to top edge
        assert sprite.top == 600
        assert sprite.bottom == 536  # 600 - 64 (sprite height)

    def test_wrap_corner(self, sprite):
        """Test wrapping when sprite moves off a corner.

        Verifies that:
        - Sprite wraps correctly when hitting a corner
        - Position is correctly aligned to both boundaries
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Position sprite off top-right corner
        sprite.position = (900, 700)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to bottom-left corner
        assert sprite.left == 0
        assert sprite.bottom == 0

    def test_boundary_callback(self, sprite):
        """Test boundary hit callback with correct boundary information.

        Verifies that:
        - Callback is called with correct boundaries
        - Multiple boundaries are reported correctly
        """
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = WrappedMove((800, 600), on_boundary_hit=on_boundary_hit)
        sprite.do(action)

        # Position sprite off top-right corner
        sprite.position = (900, 700)
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify correct boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Only two boundaries crossed

    def test_sprite_list_wrapping(self, sprite_list):
        """Test wrapping behavior with multiple sprites.

        Verifies that:
        - Each sprite wraps independently
        - List-level updates work correctly
        - Positions are correctly aligned after wrapping
        """
        action = WrappedMove((800, 600))
        action.target = sprite_list
        action.start()

        # Position sprites at different off-screen locations
        sprite_list[0].position = (900, 300)  # Off right
        sprite_list[0].change_x = 100  # Moving right
        sprite_list[0].change_y = 0  # No vertical movement

        sprite_list[1].position = (-100, 300)  # Off left
        sprite_list[1].change_x = -100  # Moving left
        sprite_list[1].change_y = 0  # No vertical movement

        sprite_list[2].position = (300, 700)  # Off top
        sprite_list[2].change_x = 0  # No horizontal movement
        sprite_list[2].change_y = 100  # Moving up

        sprite_list.update(0.1)  # Update with 0.1s time step
        action.update(0.1)  # Update with 0.1s time step

        # Verify each sprite wrapped correctly
        assert sprite_list[0].right == 168  # Wrapped to left edge
        assert sprite_list[1].left == 632  # Wrapped to right edge
        assert sprite_list[2].top == 168  # Wrapped to bottom edge

    def test_wrap_with_acceleration(self, sprite):
        """Test wrapping behavior with easing.

        Verifies that:
        - Wrapping works with easing
        - Easing curve is maintained
        - Position is correctly aligned after wrapping
        """
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create easing modifier using ease_in for acceleration effect
        ease_action = Easing(move_action, ease_function=easing.ease_in)
        # Create wrapped movement action
        wrap_action = WrappedMove((800, 600))

        # Set up actions
        sprite.do(ease_action)
        sprite.do(wrap_action)

        # Set initial position
        sprite.position = (700, 300)  # Near right edge

        # Update for 0.1 seconds
        sprite.update(0.1)  # Updates position based on easing curve and handles wrapping

        # Verify sprite wrapped and maintained easing curve
        # At t=0.1, should have moved 20 pixels right
        assert sprite.left == 0  # Wrapped to left edge
        assert sprite.right == 64  # Sprite width
        assert sprite.center_y == 300  # Y position unchanged

    def test_custom_boundary_checker(self, sprite):
        """Test using a custom boundary checker function.

        Verifies that:
        - Custom boundary checker is called
        - Boundaries are correctly identified
        - Wrapping occurs at custom boundaries
        """

        def custom_checker(sprite: arcade.Sprite) -> list[Boundary]:
            boundaries = []
            if sprite.center_x > 400:  # Check center instead of edges
                boundaries.append(Boundary.RIGHT)
            elif sprite.center_x < 400:
                boundaries.append(Boundary.LEFT)
            return boundaries

        action = WrappedMove((800, 600), boundary_checker=custom_checker)
        sprite.do(action)

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped at center
        assert sprite.center_x == 400  # Center at boundary
        assert sprite.right > 400  # Wrapped to right side

    def test_custom_wrap_handler(self, sprite):
        """Test using a custom wrap handler function.

        Verifies that:
        - Custom wrap handler is called
        - Wrapping behavior is customized
        - Position is correctly set by handler
        """

        def custom_handler(sprite: arcade.Sprite, boundaries: list[Boundary]) -> None:
            if Boundary.RIGHT in boundaries:
                sprite.left = 0  # Always wrap to left edge
            elif Boundary.LEFT in boundaries:
                sprite.right = 800  # Always wrap to right edge

        action = WrappedMove((800, 600), wrap_handler=custom_handler)
        sprite.do(action)

        # Position sprite off right edge
        sprite.position = (900, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped using custom handler
        assert sprite.left == 0  # Wrapped to left edge
        assert sprite.right == 64  # Sprite width

    def test_custom_boundary_checker_and_handler(self, sprite):
        """Test using both custom boundary checker and wrap handler.

        Verifies that:
        - Both custom functions are called
        - Boundaries are correctly identified
        - Wrapping behavior is customized
        """

        def custom_checker(sprite: arcade.Sprite) -> list[Boundary]:
            boundaries = []
            if sprite.center_x > 400:  # Check center instead of edges
                boundaries.append(Boundary.RIGHT)
            elif sprite.center_x < 400:
                boundaries.append(Boundary.LEFT)
            return boundaries

        def custom_handler(sprite: arcade.Sprite, boundaries: list[Boundary]) -> None:
            if Boundary.RIGHT in boundaries:
                sprite.left = 0  # Always wrap to left edge
            elif Boundary.LEFT in boundaries:
                sprite.right = 800  # Always wrap to right edge

        action = WrappedMove((800, 600), boundary_checker=custom_checker, wrap_handler=custom_handler)
        sprite.do(action)

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped using both custom functions
        assert sprite.left == 0  # Wrapped to left edge using custom handler
        assert sprite.right == 64  # Sprite width

    def test_wrap_corner_with_velocity(self, sprite):
        """Test wrapping when sprite hits corner with velocity.

        Verifies that:
        - Sprite wraps correctly at corner
        - Velocity is maintained
        - Position is correctly aligned
        """
        action = WrappedMove((800, 600))
        sprite.do(action)

        # Set initial position and velocity
        sprite.position = (750, 550)  # Near top-right corner
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up

        # Update for 0.1 seconds
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped and maintained velocity
        # Initial right edge = 750 + 32 = 782
        # After moving 10 pixels right = 792
        # After wrapping = 792 - 800 = -8
        assert sprite.right == -8
        # Initial top edge = 550 + 32 = 582
        # After moving 10 pixels up = 592
        # After wrapping = 592 - 600 = -8
        assert sprite.top == -8
        assert sprite.change_x == 100  # Velocity unchanged
        assert sprite.change_y == 100  # Velocity unchanged

    def test_wrap_corner_with_acceleration(self, sprite):
        """Test wrapping when sprite hits corner with easing.

        Verifies that:
        - Sprite wraps correctly at corner
        - Easing curve is maintained
        - Position is correctly aligned
        """
        # Create base movement action
        move_action = MoveBy((200, 200), 1.0)
        # Create easing modifier using ease_in for acceleration effect
        ease_action = Easing(move_action, ease_function=easing.ease_in)
        # Create wrapped movement action
        wrap_action = WrappedMove((800, 600))

        # Set up actions
        sprite.do(ease_action)
        sprite.do(wrap_action)

        # Set initial position
        sprite.position = (750, 550)  # Near top-right corner

        # Update for 0.1 seconds
        sprite.update(0.1)  # Updates position based on easing curve and handles wrapping

        # Verify sprite wrapped and maintained easing curve
        # At t=0.1, should have moved 20 pixels in both directions
        assert sprite.right == -8  # Wrapped to left edge
        assert sprite.top == -8  # Wrapped to bottom edge

    def test_wrap_corner_sprite_list(self, sprite_list):
        """Test corner wrapping with multiple sprites.

        Verifies that:
        - Each sprite wraps correctly at corners
        - List-level updates work correctly
        - Positions are correctly aligned after wrapping
        """
        action = WrappedMove((800, 600))
        action.target = sprite_list
        action.start()

        # Position sprites at different corners
        sprite_list[0].position = (900, 700)  # Top-right corner
        sprite_list[1].position = (-100, 700)  # Top-left corner
        sprite_list[2].position = (900, -100)  # Bottom-right corner

        sprite_list.update(0.1)  # Update with 0.1s time step
        action.update(0.1)  # Update with 0.1s time step

        # Verify each sprite wrapped correctly
        # Sprite 0: right edge = 900 + 32 = 932, after wrapping = 932 - 800 = 132
        assert sprite_list[0].right == 132
        # Sprite 0: top edge = 700 + 32 = 732, after wrapping = 732 - 600 = 132
        assert sprite_list[0].top == 132

        # Sprite 1: right edge = -100 + 32 = -68, after wrapping = -68 + 800 = 732
        assert sprite_list[1].right == 732
        # Sprite 1: top edge = 700 + 32 = 732, after wrapping = 732 - 600 = 132
        assert sprite_list[1].top == 132

        # Sprite 2: right edge = 900 + 32 = 932, after wrapping = 932 - 800 = 132
        assert sprite_list[2].right == 132
        # Sprite 2: bottom edge = -100 - 32 = -132, after wrapping = -132 + 600 = 468
        assert sprite_list[2].bottom == 468


class TestBoundedMove:
    """Test suite for bounded movement.

    Tests the BoundedMove action's behavior when sprites hit screen boundaries.
    Focuses on:
    - Bouncing behavior at each boundary
    - Corner cases
    - Boundary callbacks
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    def test_bounce_right_edge(self, sprite):
        """Test bouncing when sprite hits right edge.

        Verifies that:
        - Sprite bounces at right edge
        - Velocity is reversed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600))
        sprite.do(action)

        # Position sprite at right edge
        sprite.position = (736, 300)  # right = 800
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.change_x == -100  # X direction reversed

    def test_bounce_left_edge(self, sprite):
        """Test bouncing when sprite hits left edge.

        Verifies that:
        - Sprite bounces at left edge
        - Velocity is reversed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600))
        sprite.do(action)

        # Position sprite at left edge
        sprite.position = (64, 300)  # left = 0
        sprite.change_x = -100  # Moving left
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.left == 0  # Left edge at screen boundary
        assert sprite.change_x == 100  # X direction reversed

    def test_bounce_top_edge(self, sprite):
        """Test bouncing when sprite hits top edge.

        Verifies that:
        - Sprite bounces at top edge
        - Velocity is reversed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600))
        sprite.do(action)

        # Position sprite at top edge
        sprite.position = (300, 536)  # top = 600
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_y == -100  # Y direction reversed

    def test_bounce_bottom_edge(self, sprite):
        """Test bouncing when sprite hits bottom edge.

        Verifies that:
        - Sprite bounces at bottom edge
        - Velocity is reversed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600))
        sprite.do(action)

        # Position sprite at bottom edge
        sprite.position = (300, 64)  # bottom = 0
        sprite.change_y = -100  # Moving down
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.bottom == 0  # Bottom edge at screen boundary
        assert sprite.change_y == 100  # Y direction reversed

    def test_bounce_corner(self, sprite):
        """Test bouncing when sprite hits a corner.

        Verifies that:
        - Sprite bounces in both directions
        - Velocities are reversed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600))
        sprite.do(action)

        # Position sprite at top-right corner
        sprite.position = (736, 536)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.change_y == -100  # Y direction reversed

    def test_boundary_callback(self, sprite):
        """Test boundary hit callback with correct boundary information.

        Verifies that:
        - Callback is called with correct boundaries
        - Multiple boundaries are reported correctly
        """
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = BoundedMove((800, 600), on_boundary_hit=on_boundary_hit)
        sprite.do(action)

        # Position sprite at top-right corner
        sprite.position = (736, 536)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify correct boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Only two boundaries hit

    def test_sprite_list_bouncing(self, sprite_list):
        """Test bouncing with multiple sprites.

        Verifies that:
        - All sprites bounce correctly
        - List-level updates work correctly
        - Velocities are reversed correctly
        """
        action = BoundedMove((800, 600))
        action.target = sprite_list
        action.start()

        # Position sprites at different locations
        sprite_list[0].position = (700, 300)  # Near right edge
        sprite_list[1].position = (300, 500)  # Near top edge
        sprite_list[2].position = (100, 300)  # Near left edge

        # Set velocities
        for sprite in sprite_list:
            sprite.change_x = 100  # All moving right
            sprite.change_y = 100  # All moving up

        action.update(0.1)  # Update with 0.1s time step

        # Verify all sprites reversed direction
        for sprite in sprite_list:
            assert sprite.change_x == -100  # All reversed X direction
            assert sprite.change_y == -100  # All reversed Y direction

    def test_independent_movement(self, sprite_list):
        """Test independent movement mode where sprites bounce independently.

        Verifies that:
        - Sprites bounce independently
        - Only sprites hitting boundaries reverse direction
        - Other sprites maintain their velocity
        """
        action = BoundedMove((800, 600), independent_movement=True)
        action.target = sprite_list
        action.start()

        # Position sprites at different locations
        sprite_list[0].position = (700, 300)  # Near right edge
        sprite_list[1].position = (300, 500)  # Near top edge
        sprite_list[2].position = (100, 300)  # Near left edge

        # Set velocities
        for sprite in sprite_list:
            sprite.change_x = 100  # All moving right
            sprite.change_y = 100  # All moving up

        action.update(0.1)  # Update with 0.1s time step

        # Verify only sprite 0 reversed direction (hit right edge)
        assert sprite_list[0].change_x == -100  # Reversed X direction
        assert sprite_list[0].change_y == -100  # Reversed Y direction
        assert sprite_list[1].change_x == 100  # Unchanged
        assert sprite_list[1].change_y == 100  # Unchanged
        assert sprite_list[2].change_x == 100  # Unchanged
        assert sprite_list[2].change_y == 100  # Unchanged

    def test_stop_behavior(self, sprite):
        """Test stop behavior when sprite hits a boundary.

        Verifies that:
        - Sprite stops at boundary
        - Velocity is zeroed
        - Position is correctly aligned
        """
        action = BoundedMove((800, 600), bounce_behavior="stop")
        sprite.do(action)

        # Position sprite at right edge
        sprite.position = (736, 300)  # right = 800
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite stopped
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.change_x == 0  # X velocity zeroed
        assert sprite.change_y == 100  # Y velocity unchanged

    def test_custom_boundary_checker(self, sprite):
        """Test using a custom boundary checker function.

        Verifies that:
        - Custom boundary checker is called
        - Boundaries are correctly identified
        - Bouncing occurs at custom boundaries
        """

        def custom_checker(sprite: arcade.Sprite) -> list[Boundary]:
            boundaries = []
            if sprite.center_x > 400:  # Check center instead of edges
                boundaries.append(Boundary.RIGHT)
            elif sprite.center_x < 400:
                boundaries.append(Boundary.LEFT)
            return boundaries

        action = BoundedMove((800, 600), boundary_checker=custom_checker)
        sprite.do(action)

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced at center
        assert sprite.center_x == 400  # Center at boundary
        assert sprite.change_x == -100  # X direction reversed

    def test_bounce_with_acceleration(self, sprite):
        """Test bouncing with easing.

        Verifies that:
        - Sprite bounces correctly with easing
        - Easing curve is maintained
        - Position is correctly aligned
        """
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create easing modifier using ease_in for acceleration effect
        ease_action = Easing(move_action, ease_function=easing.ease_in)
        # Create bounded movement action
        bound_action = BoundedMove((800, 600))

        # Set up actions
        sprite.do(ease_action)
        sprite.do(bound_action)

        # Set initial position
        sprite.position = (700, 300)  # Near right edge

        # Update for 0.1 seconds
        sprite.update(0.1)  # Updates position based on easing curve and handles boundary checking

        # Verify sprite bounced and maintained easing curve
        # At t=0.1, should have moved 20 pixels right
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.position[0] == 700 + 20
        assert sprite.center_y == 300  # Y position unchanged

    def test_corner_bounce_with_acceleration(self, sprite):
        """Test corner bouncing with easing.

        Verifies that:
        - Sprite bounces correctly at corner with easing
        - Easing curve is maintained
        - Position is correctly aligned
        """
        # Create base movement action
        move_action = MoveBy((200, 200), 1.0)
        # Create easing modifier using ease_in for acceleration effect
        ease_action = Easing(move_action, ease_function=easing.ease_in)
        # Create bounded movement action
        bound_action = BoundedMove((800, 600))

        # Set up actions
        sprite.do(ease_action)
        sprite.do(bound_action)

        # Set initial position
        sprite.position = (750, 550)  # Near top-right corner

        # Update for 0.1 seconds
        sprite.update(0.1)  # Updates position based on easing curve and handles boundary checking

        # Verify sprite bounced and maintained easing curve
        # At t=0.1, should have moved 20 pixels in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.position[0] == 750 + 20
        assert sprite.position[1] == 550 + 20

    def test_corner_bounce_sprite_list(self, sprite_list):
        """Test corner bouncing with multiple sprites.

        Verifies that:
        - All sprites bounce correctly at corners
        - List-level updates work correctly
        - Velocities are reversed correctly
        """
        action = BoundedMove((800, 600))
        action.target = sprite_list
        action.start()

        # Position sprites at different corners
        sprite_list[0].position = (736, 536)  # Top-right corner
        sprite_list[1].position = (64, 536)  # Top-left corner
        sprite_list[2].position = (736, 64)  # Bottom-right corner

        # Set velocities
        for sprite in sprite_list:
            sprite.change_x = 100  # All moving right
            sprite.change_y = 100  # All moving up

        action.update(0.1)  # Update with 0.1s time step

        # Verify all sprites reversed direction
        for sprite in sprite_list:
            assert sprite.change_x == -100  # All reversed X direction
            assert sprite.change_y == -100  # All reversed Y direction

    def test_corner_bounce_boundary_callback(self, sprite):
        """Test boundary callback when sprite hits corner.

        Verifies that:
        - Callback is called with correct boundaries
        - Multiple boundaries are reported correctly
        - Each boundary is reported only once
        """
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = BoundedMove((800, 600), on_boundary_hit=on_boundary_hit)
        sprite.do(action)

        # Print sprite dimensions for debugging
        print(f"Sprite dimensions: width={sprite.width}, height={sprite.height}")

        # Position sprite at top-right corner
        # Position so that right edge is at 800 and top edge is at 600
        sprite.position = (800 - sprite.width, 600 - sprite.height)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify both boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Both boundaries hit
        assert boundaries_hit.count(Boundary.RIGHT) == 1  # Each boundary hit once
        assert boundaries_hit.count(Boundary.TOP) == 1
