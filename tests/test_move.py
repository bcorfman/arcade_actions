"""Unit tests for movement actions in arcade_actions.

This module contains tests for some movement-related actions:
- _Move (base movement class)
- WrappedMove (wrapping at screen bounds)
- BoundedMove (bouncing at screen bounds)
- Driver (directional movement) - not tested here
"""

import arcade
import pytest

from actions.interval import Accelerate, MoveBy
from actions.move import Boundary, BoundedMove, WrappedMove, _Move


class TestMove:
    """Test suite for base movement class."""

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = arcade.Sprite()
        sprite.position = (0, 0)
        sprite.change_x = 100
        sprite.change_y = 100
        return sprite

    def test_basic_movement(self, sprite):
        """Test basic movement without physics."""
        action = _Move()
        action.target = sprite
        action.start()
        action.update(1.0)
        assert sprite.position == (100, 100)

    def test_movement_with_rotation(self, sprite):
        """Test movement with rotation."""
        sprite.change_angle = 45
        action = _Move()
        action.target = sprite
        action.start()
        action.update(1.0)
        assert sprite.angle == 45


class TestWrappedMove:
    """Test suite for wrapping movement.

    Tests the WrappedMove action's behavior when sprites move across screen boundaries.
    The wrapping behavior requires sprites to move completely off-screen before wrapping
    to the opposite edge, where they appear with their appropriate edge aligned to the boundary.
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with explicit dimensions."""
        sprite = arcade.Sprite()
        sprite.width = 64  # Set explicit width
        sprite.height = 64  # Set explicit height
        sprite.position = (0, 0)
        sprite.change_x = 100
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a test sprite list with multiple sprites."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite()
            sprite.width = 64  # Set explicit width
            sprite.height = 64  # Set explicit height
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    def test_wrap_right(self, sprite):
        """Test wrapping at right boundary.

        When a sprite moves off the right edge (left > width), it should wrap to the left
        edge with its right edge at x=0.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the right edge
        sprite.position = (900, 300)  # left = 900 > 800
        sprite.change_x = 100  # Moving right
        sprite.change_y = 0  # No vertical movement

        # Update position based on velocity
        sprite.update(1.0)
        # Handle wrapping
        action.update(1.0)

        # Verify sprite wrapped to left edge
        # Initial position = (900, 300)
        # After moving 100 pixels right = (1000, 300)
        # After wrapping:
        #   - New wrapped position = 1000 - 800 [screen width] = 200
        #   - Right edge = 200 - 32 [sprite width / 2] = 168
        #   - Left edge = 168 - 64 [right edge - sprite width] = 104
        assert sprite.left == 104
        assert sprite.right == 168
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_left(self, sprite):
        """Test wrapping at left boundary.

        When a sprite moves off the left edge (right < 0), it should wrap to the right
        edge with its left edge at x=width.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the left edge
        sprite.position = (-100, 300)  # right = -100 + 64 = -36 < 0
        sprite.change_x = -100  # Moving left
        sprite.change_y = 0  # No vertical movement

        # Update position based on velocity
        sprite.update(1.0)
        # Handle wrapping
        action.update(1.0)
        # Verify sprite wrapped to right edge
        # Initial position = (-100, 300)
        # After moving 100 pixels left = (-200, 300)
        # After wrapping:
        #   - New wrapped position = 800 - (-200) = 1000
        #   - Left edge = 800 [screen width] - 168 [right edge] = 632
        #   - Right edge = 632 [left edge] + 64 [sprite width] = 696
        assert sprite.left == 632
        assert sprite.right == 696
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_top(self, sprite):
        """Test wrapping at top boundary.

        When a sprite moves off the top edge (bottom > height), it should wrap to the bottom
        edge with its top edge at y=0.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the top edge
        sprite.position = (300, 700)  # bottom = 700 > 600
        sprite.change_x = 0  # No horizontal movement
        sprite.change_y = 100  # Moving up
        # Update position based on velocity
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite wrapped to bottom edge
        assert sprite.top == 168
        assert sprite.bottom == 168 - 64
        assert sprite.center_x == 300  # X position unchanged

    def test_wrap_bottom(self, sprite):
        """Test wrapping at bottom boundary.

        When a sprite moves off the bottom edge (top > height), it should wrap to the top
        edge with its bottom edge at y=0.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the bottom edge
        sprite.position = (400, 700)  # top = 700 > 600
        sprite.change_x = 0  # No horizontal movement
        sprite.change_y = 100  # Moving down

        # Update position based on velocity
        sprite.update(1.0)
        # Handle wrapping
        action.update(1.0)

        # Verify sprite wrapped to top edge
        # Initial position = (400, 700)
        # After moving 100 pixels down = (400, 800)
        # Top edge = 800 + 32 = 832
        # Bottom edge = 800 - 32 = 768
        # After wrapping:
        #   - Top edge = 768 - 600 = 168
        #   - Bottom edge = 168 - 64 = 104
        assert sprite.top == 168
        assert sprite.bottom == 104
        assert sprite.center_x == 400  # X position unchanged

    def test_wrap_diagonal(self, sprite):
        """Test wrapping when moving diagonally.

        When a sprite moves diagonally and wraps, both x and y coordinates should be
        adjusted correctly.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite off both right and bottom edges
        sprite.position = (900, 700)  # right = 900 + 64 = 964 > 800, top = 700 > 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up

        # Update position based on velocity
        sprite.update(1.0)
        # Handle wrapping
        action.update(1.0)

        # Verify sprite wrapped correctly
        # Initial position = (900, 700)
        # After moving 100 pixels right and up = (1000, 800)
        assert sprite.bottom == 104
        assert sprite.top == 168
        assert sprite.left == 104
        assert sprite.right == 168

    def test_no_wrap_partial(self, sprite):
        """Test that sprites don't wrap when only partially off-screen."""
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite partially off right edge
        sprite.position = (750, 300)  # right = 782, still partially visible
        sprite.change_x = 20  # Moving right at 20 pixels per second
        sprite.change_y = 0  # No vertical movement
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite didn't wrap
        assert sprite.right > 800  # Still off right edge
        assert sprite.left < 800  # Partially visible

    def test_boundary_callback(self, sprite):
        """Test boundary hit callback with correct boundary information."""
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = WrappedMove(800, 600, on_boundary_hit=on_boundary_hit)
        action.target = sprite
        action.start()

        # Position sprite off top-right corner
        sprite.position = (900, 700)
        sprite.update(1.0)
        action.update(1.0)

        # Verify correct boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Only two boundaries crossed

    def test_sprite_list_wrapping(self, sprite_list):
        """Test wrapping behavior with multiple sprites.

        Each sprite in the list should wrap independently when it moves off-screen.
        """
        action = WrappedMove(800, 600)
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

        sprite_list.update(1.0)
        action.update(1.0)

        # Verify each sprite wrapped correctly
        assert sprite_list[0].right == 168  # Wrapped to left edge
        assert sprite_list[1].left == 632  # Wrapped to right edge
        assert sprite_list[2].top == 168  # Wrapped to bottom edge

    def test_wrap_with_velocity(self, sprite):
        """Test wrapping behavior with continuous velocity.

        A sprite moving with constant velocity should wrap smoothly when it moves
        off-screen and continue moving in the same direction.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Set initial position and velocity
        sprite.position = (750, 300)
        sprite.change_x = 100  # Moving right at 100 pixels per second
        sprite.change_y = 0  # No vertical movement

        # Update for 1 second
        sprite.update(1.0)
        action.update(1.0)

        assert sprite.right == 18
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_with_acceleration(self, sprite):
        """Test wrapping behavior with acceleration.

        A sprite with acceleration should wrap correctly while its velocity
        changes over time using proper acceleration curves.
        """
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create acceleration modifier
        accel_action = Accelerate(move_action, rate=2.0)
        # Create wrapping action
        wrap_action = WrappedMove(800, 600)

        # Set up actions
        accel_action.target = sprite
        wrap_action.target = sprite

        # Set initial position
        sprite.position = (750, 300)

        # Start actions
        accel_action.start()
        wrap_action.start()

        # Update for 1 second
        accel_action.update(1.0)  # Updates change_x/y based on acceleration curve
        sprite.update(1.0)  # Updates position based on change_x/y
        wrap_action.update(1.0)  # Only handles wrapping, position already updated

        # Verify sprite wrapped and maintained acceleration curve
        # Initial position = (750, 300)
        # After moving 200 pixels right = (950, 300)
        # After wrapping:
        #   - Right edge = 918 - 800 = 118
        #   - Left edge = 118 - 64 = 54
        assert sprite.left == 54
        assert sprite.center_y == 300  # Y position unchanged

    def test_custom_boundary_checker(self, sprite):
        """Test using a custom boundary checker function."""

        def custom_checker(sprite: arcade.Sprite) -> list[Boundary]:
            boundaries = []
            if sprite.center_x > 400:  # Check center instead of edges
                boundaries.append(Boundary.RIGHT)
            elif sprite.center_x < 400:
                boundaries.append(Boundary.LEFT)
            return boundaries

        action = WrappedMove(800, 600, boundary_checker=custom_checker)
        action.target = sprite
        action.start()

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite wrapped at center
        assert sprite.center_x == 400  # Center at boundary
        assert sprite.right > 400  # Wrapped to right side

    def test_custom_wrap_handler(self, sprite):
        """Test using a custom wrap handler function."""

        def custom_handler(sprite: arcade.Sprite, boundaries: list[Boundary]) -> None:
            if Boundary.RIGHT in boundaries:
                sprite.left = 0  # Always wrap to left edge
            elif Boundary.LEFT in boundaries:
                sprite.right = 800  # Always wrap to right edge

        action = WrappedMove(800, 600, wrap_handler=custom_handler)
        action.target = sprite
        action.start()

        # Position sprite off right edge
        sprite.position = (900, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite wrapped using custom handler
        assert sprite.left == 0  # Wrapped to left edge
        assert sprite.right == 64  # Sprite width

    def test_custom_boundary_checker_and_handler(self, sprite):
        """Test using both custom boundary checker and wrap handler."""

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

        action = WrappedMove(800, 600, boundary_checker=custom_checker, wrap_handler=custom_handler)
        action.target = sprite
        action.start()

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite wrapped using both custom functions
        assert sprite.left == 0  # Wrapped to left edge using custom handler
        assert sprite.right == 64  # Sprite width

    def test_wrap_corner_with_velocity(self, sprite):
        """Test wrapping when sprite hits corner with velocity.

        When a sprite with velocity hits a corner, it should wrap correctly
        and maintain its velocity in both directions.
        """
        action = WrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Set initial position and velocity
        sprite.position = (750, 550)  # Near top-right corner
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up

        # Update for 1 second
        sprite.update(1.0)
        action.update(1.0)

        # Verify sprite wrapped and maintained velocity
        # Initial right edge = 750 + 32 = 782
        # After moving 100 pixels right = 882
        # After wrapping = 882 - 800 = 82
        assert sprite.right == 82
        # Initial top edge = 550 + 32 = 582
        # After moving 100 pixels up = 682
        # After wrapping = 682 - 600 = 82
        assert sprite.top == 82
        assert sprite.change_x == 100  # Velocity unchanged
        assert sprite.change_y == 100  # Velocity unchanged

    def test_wrap_corner_with_acceleration(self, sprite):
        """Test wrapping when sprite hits corner with acceleration.

        When a sprite with acceleration hits a corner, it should wrap correctly
        and maintain its acceleration curve in both directions.
        """
        # Create base movement action
        move_action = MoveBy((200, 200), 1.0)
        # Create acceleration modifier
        accel_action = Accelerate(move_action, rate=2.0)
        accel_action.target = sprite
        accel_action.start()
        wrap_action = WrappedMove(800, 600)
        wrap_action.target = sprite
        wrap_action.start()

        # Set initial position
        sprite.position = (750, 550)  # Near top-right corner

        # Update for 1 second
        accel_action.update(1.0)
        sprite.update(1.0)
        wrap_action.update(1.0)
        # Verify sprite wrapped and maintained acceleration curve
        # Initial right edge = 750 + 32 = 782
        # After moving 200 pixels right = 982
        # After wrapping = 982 - 800 = 182
        assert sprite.right == 182
        # Initial top edge = 550 + 32 = 582
        # After moving 200 pixels up = 782
        # After wrapping = 782 - 600 = 182
        assert sprite.top == 182

    def test_wrap_corner_sprite_list(self, sprite_list):
        """Test corner wrapping with multiple sprites.

        Each sprite in the list should wrap correctly when hitting corners,
        regardless of other sprites' positions.
        """
        action = WrappedMove(800, 600)
        action.target = sprite_list
        action.start()

        # Position sprites at different corners
        sprite_list[0].position = (900, 700)  # Top-right corner
        sprite_list[1].position = (-100, 700)  # Top-left corner
        sprite_list[2].position = (900, -100)  # Bottom-right corner

        sprite_list.update(1.0)
        action.update(1.0)

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
    The bounce behavior is determined by the sprite's movement direction and its edges:
    - When moving right, the sprite bounces when its right edge hits the right boundary
    - When moving left, the sprite bounces when its left edge hits the left boundary
    - When moving up, the sprite bounces when its top edge hits the top boundary
    - When moving down, the sprite bounces when its bottom edge hits the bottom boundary
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with explicit dimensions."""
        sprite = arcade.Sprite()
        sprite.width = 64  # Set explicit width
        sprite.height = 64  # Set explicit height
        sprite.position = (0, 0)
        sprite.change_x = 100
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a test sprite list with multiple sprites."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite()
            sprite.width = 64  # Set explicit width
            sprite.height = 64  # Set explicit height
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    def test_bounce_right_edge(self, sprite):
        """Test bouncing when right edge hits right boundary."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near right edge, moving right
        sprite.position = (700, 300)  # 700 + 64 = 764 (right edge)
        sprite.change_x = 100  # Moving right
        action.update(1.0)

        # Verify sprite bounced
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.change_x == -100  # Direction reversed
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_left_edge(self, sprite):
        """Test bouncing when left edge hits left boundary."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near left edge, moving left
        sprite.position = (100, 300)
        sprite.change_x = -100  # Moving left
        action.update(1.0)

        # Verify sprite bounced
        assert sprite.left == 0  # Left edge at screen boundary
        assert sprite.change_x == 100  # Direction reversed
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_top_edge(self, sprite):
        """Test bouncing when top edge hits top boundary."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near top edge, moving up
        sprite.position = (300, 500)  # 500 + 64 = 564 (top edge)
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite bounced
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_y == -100  # Direction reversed
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_bottom_edge(self, sprite):
        """Test bouncing when bottom edge hits bottom boundary."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near bottom edge, moving down
        sprite.position = (300, 100)
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite bounced
        assert sprite.bottom == 0  # Bottom edge at screen boundary
        assert sprite.change_y == 100  # Direction reversed
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_corner(self, sprite):
        """Test bouncing when sprite hits a corner."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near top-right corner, moving up and right
        sprite.position = (700, 500)
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite bounced in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.change_y == -100  # Y direction reversed

    def test_bounce_with_velocity(self, sprite):
        """Test bouncing with continuous velocity."""
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Set initial position and velocity
        sprite.position = (700, 300)
        sprite.change_x = 100  # Moving right at 100 pixels per second
        action.update(1.0)

        # Verify sprite bounced and maintained speed
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.change_x == -100  # Direction reversed, speed maintained
        assert abs(sprite.change_x) == 100  # Speed unchanged

    def test_bounce_with_acceleration(self, sprite):
        """Test bouncing with acceleration."""
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create acceleration modifier
        accel_action = Accelerate(move_action, rate=2.0)
        accel_action.target = sprite
        accel_action.start()

        # Set initial position
        sprite.position = (700, 300)

        # Update for 1 second
        accel_action.update(1.0)
        sprite.update(1.0)

        # Verify sprite bounced and maintained acceleration curve
        assert sprite.right == 800  # Right edge at screen boundary
        # At t=1.0, should have moved 200 pixels
        assert sprite.position[0] == 700 + 200

    def test_boundary_callback(self, sprite):
        """Test boundary hit callback with correct boundary information."""
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = BoundedMove(800, 600, on_boundary_hit=on_boundary_hit)
        action.target = sprite
        action.start()

        # Position sprite to hit top-right corner
        sprite.position = (700, 500)
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify correct boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Both boundaries hit
        assert boundaries_hit.count(Boundary.RIGHT) == 1  # Each boundary hit once
        assert boundaries_hit.count(Boundary.TOP) == 1

    def test_sprite_list_bouncing(self, sprite_list):
        """Test bouncing with multiple sprites."""
        action = BoundedMove(800, 600)
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

        action.update(1.0)

        # Verify all sprites reversed direction
        for sprite in sprite_list:
            assert sprite.change_x == -100  # All reversed X direction
            assert sprite.change_y == -100  # All reversed Y direction

    def test_independent_movement(self, sprite_list):
        """Test independent movement mode where sprites bounce independently."""
        action = BoundedMove(800, 600, independent_movement=True)
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

        action.update(1.0)

        # Verify only sprite 0 reversed direction (hit right edge)
        assert sprite_list[0].change_x == -100  # Reversed X direction
        assert sprite_list[0].change_y == -100  # Reversed Y direction
        assert sprite_list[1].change_x == 100  # Unchanged
        assert sprite_list[1].change_y == 100  # Unchanged
        assert sprite_list[2].change_x == 100  # Unchanged
        assert sprite_list[2].change_y == 100  # Unchanged

    def test_stop_bounce_behavior(self, sprite):
        """Test stop bounce behavior where sprites stop at boundaries."""
        action = BoundedMove(800, 600, bounce_behavior="stop")
        action.target = sprite
        action.start()

        # Position sprite near right edge, moving right
        sprite.position = (700, 300)
        sprite.change_x = 100  # Moving right
        action.update(1.0)

        # Verify sprite stopped
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.change_x == 0  # Stopped
        assert sprite.center_y == 300  # Y position unchanged

    def test_custom_boundary_checker(self, sprite):
        """Test using a custom boundary checker function."""

        def custom_checker(sprite: arcade.Sprite) -> list[Boundary]:
            boundaries = []
            if sprite.center_x > 400:  # Check center instead of edges
                boundaries.append(Boundary.RIGHT)
            elif sprite.center_x < 400:
                boundaries.append(Boundary.LEFT)
            return boundaries

        action = BoundedMove(800, 600, boundary_checker=custom_checker)
        action.target = sprite
        action.start()

        # Position sprite near center, moving right
        sprite.position = (350, 300)
        sprite.change_x = 100  # Moving right
        action.update(1.0)

        # Verify sprite bounced at center
        assert sprite.center_x == 400  # Center at boundary
        assert sprite.change_x == -100  # Direction reversed

    def test_space_invaders_movement(self):
        """Test Space Invaders-style alien movement pattern."""
        # Create a 5x3 grid of aliens
        aliens = arcade.SpriteList()
        grid_width = 5
        grid_height = 3
        alien_size = 40
        spacing = 20
        start_x = 100
        start_y = 500

        # Create aliens in a grid pattern
        for row in range(grid_height):
            for col in range(grid_width):
                alien = arcade.Sprite()
                alien.width = alien_size
                alien.height = alien_size
                alien.position = (start_x + col * (alien_size + spacing), start_y - row * (alien_size + spacing))
                alien.change_x = 50  # Initial movement speed
                aliens.append(alien)

        # Track boundary hits and vertical movement
        boundary_hits = 0
        vertical_movement = 0

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            nonlocal boundary_hits, vertical_movement
            if boundary_hits < 3:  # Only move down 3 times
                if Boundary.LEFT in boundaries or Boundary.RIGHT in boundaries:
                    boundary_hits += 1
                    vertical_movement += 20
                    # Move all aliens down
                    for alien in aliens:
                        alien.position = (alien.position[0], alien.position[1] - 20)

        # Create bounded movement action with group movement
        action = BoundedMove(800, 600, on_boundary_hit=on_boundary_hit, independent_movement=False)
        action.target = aliens
        action.start()

        # Simulate movement until we've hit boundaries 3 times
        while boundary_hits < 3:
            action.update(1.0)

        # Verify final positions
        # All aliens should have moved down by 60 pixels (3 * 20)
        for alien in aliens:
            assert alien.position[1] == start_y - 60  # Compare against initial y position

        # Verify boundary hits
        assert boundary_hits == 3
        assert vertical_movement == 60

        # Verify all aliens are within screen bounds
        for alien in aliens:
            assert alien.left >= 0
            assert alien.right <= 800
            assert alien.bottom >= 0
            assert alien.top <= 600

    def test_bounce_top_right_corner(self, sprite):
        """Test bouncing when sprite hits top-right corner.

        When a sprite hits the top-right corner, it should bounce in both
        directions simultaneously, with its right edge at x=width and
        top edge at y=height.
        """
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite at top-right corner
        sprite.position = (736, 536)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite bounced in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.change_y == -100  # Y direction reversed

    def test_bounce_top_left_corner(self, sprite):
        """Test bouncing when sprite hits top-left corner.

        When a sprite hits the top-left corner, it should bounce in both
        directions simultaneously, with its left edge at x=0 and
        top edge at y=height.
        """
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite at top-left corner
        sprite.position = (64, 536)  # left = 0, top = 600
        sprite.change_x = -100  # Moving left
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite bounced in both directions
        assert sprite.left == 0  # Left edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.change_x == 100  # X direction reversed
        assert sprite.change_y == -100  # Y direction reversed

    def test_bounce_bottom_right_corner(self, sprite):
        """Test bouncing when sprite hits bottom-right corner.

        When a sprite hits the bottom-right corner, it should bounce in both
        directions simultaneously, with its right edge at x=width and
        bottom edge at y=0.
        """
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite at bottom-right corner
        sprite.position = (736, 64)  # right = 800, bottom = 0
        sprite.change_x = 100  # Moving right
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite bounced in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.bottom == 0  # Bottom edge at screen boundary
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.change_y == 100  # Y direction reversed

    def test_bounce_bottom_left_corner(self, sprite):
        """Test bouncing when sprite hits bottom-left corner.

        When a sprite hits the bottom-left corner, it should bounce in both
        directions simultaneously, with its left edge at x=0 and
        bottom edge at y=0.
        """
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite at bottom-left corner
        sprite.position = (64, 64)  # left = 0, bottom = 0
        sprite.change_x = -100  # Moving left
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite bounced in both directions
        assert sprite.left == 0  # Left edge at screen boundary
        assert sprite.bottom == 0  # Bottom edge at screen boundary
        assert sprite.change_x == 100  # X direction reversed
        assert sprite.change_y == 100  # Y direction reversed

    def test_corner_bounce_with_velocity(self, sprite):
        """Test corner bouncing with continuous velocity.

        When a sprite with velocity hits a corner, it should bounce correctly
        and maintain its speed in both directions.
        """
        action = BoundedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite near top-right corner with velocity
        sprite.position = (736, 536)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite bounced and maintained speed
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert abs(sprite.change_x) == 100  # Speed maintained
        assert abs(sprite.change_y) == 100  # Speed maintained

    def test_corner_bounce_with_acceleration(self, sprite):
        """Test corner bouncing with acceleration.

        When a sprite with acceleration hits a corner, it should bounce correctly
        and maintain its acceleration curve in both directions.
        """
        # Create base movement action
        move_action = MoveBy((200, 200), 1.0)
        # Create acceleration modifier
        accel_action = Accelerate(move_action, rate=2.0)
        # Create bounded movement action
        bound_action = BoundedMove(800, 600)

        # Set up actions
        accel_action.target = sprite
        bound_action.target = sprite

        # Set initial position
        sprite.position = (750, 550)  # Near top-right corner

        # Start actions
        accel_action.start()
        bound_action.start()

        # Update for 1 second
        accel_action.update(1.0)  # Updates change_x/y based on acceleration curve
        sprite.update(1.0)  # Updates position based on change_x/y
        bound_action.update(1.0)  # Handles boundary checking and bouncing

        # Verify sprite bounced and maintained acceleration curve
        # At t=1.0, should have moved 200 pixels in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.position[0] == 750 + 200
        assert sprite.position[1] == 550 + 200

    def test_corner_bounce_sprite_list(self, sprite_list):
        """Test corner bouncing with multiple sprites.

        When any sprite in the list hits a corner, all sprites should
        reverse their direction in both axes.
        """
        action = BoundedMove(800, 600)
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

        action.update(1.0)

        # Verify all sprites reversed direction
        for sprite in sprite_list:
            assert sprite.change_x == -100  # All reversed X direction
            assert sprite.change_y == -100  # All reversed Y direction

    def test_corner_bounce_boundary_callback(self, sprite):
        """Test boundary callback when sprite hits corner.

        When a sprite hits a corner, the boundary callback should be called
        with both boundaries hit.
        """
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = BoundedMove(800, 600, on_boundary_hit=on_boundary_hit)
        action.target = sprite
        action.start()

        # Position sprite at top-right corner
        sprite.position = (736, 536)  # right = 800, top = 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify both boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Both boundaries hit
        assert boundaries_hit.count(Boundary.RIGHT) == 1  # Each boundary hit once
        assert boundaries_hit.count(Boundary.TOP) == 1
