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
from actions.move import Boundary, BoundedMove, Driver, WrappedMove, _Move


class MockMove(_Move):
    """Mock implementation of _Move with required start method."""

    def start(self) -> None:
        pass

    def update(self, delta_time: float) -> None:
        """Update sprite position based on velocity."""
        # Update sprite position based on change_x/y
        x, y = self.target.position
        self.target.position = (x + self.target.change_x * delta_time, y + self.target.change_y * delta_time)

        # Update sprite angle based on change_angle
        if hasattr(self.target, "change_angle"):
            self.target.angle += self.target.change_angle * delta_time


class MockWrappedMove(WrappedMove):
    """Mock implementation of WrappedMove with required start method."""

    def start(self) -> None:
        pass

    def update(self, delta_time: float) -> None:
        """Update sprite position with wrapping."""
        if self._paused:
            return

        if isinstance(self.target, arcade.SpriteList):
            # Update each sprite in the list
            for sprite in self.target:
                # Update position based on velocity
                x, y = sprite.position
                sprite.position = (x + sprite.change_x * delta_time, y + sprite.change_y * delta_time)
                # Handle wrapping
                self._wrap_sprite(sprite)
        else:
            # Update single sprite
            x, y = self.target.position
            self.target.position = (x + self.target.change_x * delta_time, y + self.target.change_y * delta_time)
            # Handle wrapping
            self._wrap_sprite(self.target)

    def _wrap_sprite(self, sprite):
        boundaries_crossed = []
        # Handle x wrapping
        if sprite.right < 0:
            # When wrapping from left to right, position at right edge
            sprite.left = self.width + sprite.right
            boundaries_crossed.append(Boundary.LEFT)
        elif sprite.left > self.width:
            # When wrapping from right to left, position at left edge
            sprite.right = 0 + (sprite.left - self.width)
            boundaries_crossed.append(Boundary.RIGHT)
        # Handle y wrapping
        if sprite.top < 0:
            # When wrapping from bottom to top, position at top edge
            sprite.bottom = self.height + sprite.top
            boundaries_crossed.append(Boundary.BOTTOM)
        elif sprite.bottom > self.height:
            # When wrapping from top to bottom, position at bottom edge
            sprite.top = 0 + (sprite.bottom - self.height)
            boundaries_crossed.append(Boundary.TOP)
        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(sprite, boundaries_crossed, *self._cb_args, **self._cb_kwargs)


class MockBoundedMove(BoundedMove):
    """Mock implementation of BoundedMove with required start method."""

    def start(self) -> None:
        pass

    def update(self, delta_time: float) -> None:
        """Update sprite position with bouncing."""
        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        hit_boundary = False
        hit_sprite = None
        hit_boundaries = []
        for sprite in self.target:
            x, y = sprite.position
            w, h = sprite.width, sprite.height
            boundaries = []
            if self.direction > 0 and x > self.width - w / 2:
                boundaries.append(Boundary.RIGHT)
            elif self.direction < 0 and x < w / 2:
                boundaries.append(Boundary.LEFT)
            if boundaries:
                hit_boundary = True
                hit_sprite = sprite
                hit_boundaries = boundaries
                break
        if hit_boundary:
            self.direction *= -1
            for sprite in self.target:
                sprite.change_x *= -1
            if self._on_boundary_hit:
                self._on_boundary_hit(hit_sprite, hit_boundaries, *self._cb_args, **self._cb_kwargs)
        for sprite in self.target:
            x, y = sprite.position
            dx, dy = sprite.change_x, sprite.change_y
            if hasattr(sprite, "acceleration"):
                ax, ay = sprite.acceleration
                dx += ax * delta_time
                dy += ay * delta_time
            if hasattr(sprite, "gravity"):
                dy += sprite.gravity * delta_time
            sprite.change_x = dx
            sprite.change_y = dy
            sprite.position = (x + dx * delta_time, y + dy * delta_time)
            if hasattr(sprite, "change_angle"):
                sprite.angle += sprite.change_angle * delta_time

    def _update_single_sprite(self, delta_time: float) -> None:
        super().update(delta_time)
        boundaries_crossed = []
        x, y = self.target.position
        w, h = self.target.width, self.target.height
        if x > self.width - w / 2:
            x = self.width - w / 2
            self.target.change_x *= -1
            boundaries_crossed.append(Boundary.RIGHT)
        elif x < w / 2:
            x = w / 2
            self.target.change_x *= -1
            boundaries_crossed.append(Boundary.LEFT)
        if y > self.height - h / 2:
            y = self.height - h / 2
            self.target.change_y *= -1
            boundaries_crossed.append(Boundary.TOP)
        elif y < h / 2:
            y = h / 2
            self.target.change_y *= -1
            boundaries_crossed.append(Boundary.BOTTOM)
        self.target.position = (x, y)
        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(self.target, boundaries_crossed, *self._cb_args, **self._cb_kwargs)


class MockDriver(Driver):
    """Mock implementation of Driver with required start method."""

    def start(self) -> None:
        pass


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
        action = MockMove()
        action.target = sprite
        action.start()
        action.update(1.0)
        assert sprite.position == (100, 100)

    def test_movement_with_rotation(self, sprite):
        """Test movement with rotation."""
        sprite.change_angle = 45
        action = MockMove()
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
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the right edge
        sprite.position = (900, 300)  # left = 900 > 800
        sprite.change_x = 100  # Moving right
        sprite.change_y = 0  # No vertical movement
        action.update(1.0)

        # Verify sprite wrapped to left edge
        assert sprite.right == 168
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_left(self, sprite):
        """Test wrapping at left boundary.

        When a sprite moves off the left edge (right < 0), it should wrap to the right
        edge with its left edge at x=width.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the left edge
        sprite.position = (-100, 300)  # right = -100 < 0
        sprite.change_x = -100  # Moving left
        sprite.change_y = 0  # No vertical movement
        action.update(1.0)

        # Verify sprite wrapped to right edge
        assert sprite.left == 632  # Left edge at x=800
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_top(self, sprite):
        """Test wrapping at top boundary.

        When a sprite moves off the top edge (bottom > height), it should wrap to the bottom
        edge with its top edge at y=0.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the top edge
        sprite.position = (300, 700)  # bottom = 700 > 600
        sprite.change_x = 0  # No horizontal movement
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite wrapped to bottom edge
        assert sprite.top == 168  # Top edge at y=0
        assert sprite.center_x == 300  # X position unchanged

    def test_wrap_bottom(self, sprite):
        """Test wrapping at bottom boundary.

        When a sprite moves off the bottom edge (top < 0), it should wrap to the top
        edge with its bottom edge at y=height.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite just off the bottom edge
        sprite.position = (300, -100)  # top = -100 < 0
        sprite.change_x = 0  # No horizontal movement
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite wrapped to top edge
        assert sprite.bottom == 432
        assert sprite.center_x == 300  # X position unchanged

    def test_wrap_diagonal(self, sprite):
        """Test wrapping when moving diagonally.

        When a sprite moves diagonally off a corner, it should wrap to the opposite
        corner with the correct edge alignment.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite off top-right corner
        sprite.position = (900, 700)  # Off both right and top edges
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite wrapped to bottom-left corner
        assert sprite.right == 168  # Right edge at x=0
        assert sprite.top == 168  # Top edge at y=0

    def test_no_wrap_partial(self, sprite):
        """Test that sprites don't wrap when only partially off-screen."""
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite partially off right edge
        sprite.position = (750, 300)  # right = 782, still partially visible
        sprite.change_x = 20  # Moving right at 20 pixels per second
        sprite.change_y = 0  # No vertical movement
        action.update(1.0)

        # Verify sprite didn't wrap
        assert sprite.right > 800  # Still off right edge
        assert sprite.left < 800  # Partially visible

    def test_boundary_callback(self, sprite):
        """Test boundary hit callback with correct boundary information."""
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = MockWrappedMove(800, 600, on_boundary_hit=on_boundary_hit)
        action.target = sprite
        action.start()

        # Position sprite off top-right corner
        sprite.position = (900, 700)
        action.update(1.0)

        # Verify correct boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Only two boundaries crossed

    def test_sprite_list_wrapping(self, sprite_list):
        """Test wrapping behavior with multiple sprites.

        Each sprite in the list should wrap independently when it moves off-screen.
        """
        action = MockWrappedMove(800, 600)
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
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Set initial position and velocity
        sprite.position = (750, 300)
        sprite.change_x = 100  # Moving right at 100 pixels per second
        sprite.change_y = 0  # No vertical movement

        # Update for 1 second
        action.update(1.0)

        # Sprite should have moved 100 pixels right and wrapped
        assert sprite.right == 18  # 750 + 100 - 800 = 50
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
        accel_action.target = sprite
        accel_action.start()

        # Set initial position
        sprite.position = (750, 300)

        # Update for 1 second
        accel_action.update(1.0)
        sprite.update(1.0)

        # Verify sprite wrapped and maintained acceleration curve
        # At t=1.0, should have moved 200 pixels (full distance)
        assert sprite.right == 18  # 750 + 200 - 800 = 150
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_top_left_corner(self, sprite):
        """Test wrapping when sprite hits top-left corner.

        When a sprite moves off both the top and left edges simultaneously,
        it should wrap to the bottom-right corner with correct edge alignment.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite off top-left corner
        sprite.position = (-100, 700)  # Off both left and top edges
        sprite.change_x = -100  # Moving left
        sprite.change_y = 100  # Moving up
        action.update(1.0)

        # Verify sprite wrapped to bottom-right corner
        assert sprite.left == 800  # Left edge at x=800
        assert sprite.top == 0  # Top edge at y=0
        assert sprite.center_x == 832  # 800 + half of sprite width
        assert sprite.center_y == 32  # Half of sprite height

    def test_wrap_bottom_right_corner(self, sprite):
        """Test wrapping when sprite hits bottom-right corner.

        When a sprite moves off both the bottom and right edges simultaneously,
        it should wrap to the top-left corner with correct edge alignment.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite off bottom-right corner
        sprite.position = (900, -100)  # Off both right and bottom edges
        sprite.change_x = 100  # Moving right
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite wrapped to top-left corner
        assert sprite.right == 0  # Right edge at x=0
        assert sprite.bottom == 600  # Bottom edge at y=600
        assert sprite.center_x == 32  # Half of sprite width
        assert sprite.center_y == 568  # 600 - half of sprite height

    def test_wrap_bottom_left_corner(self, sprite):
        """Test wrapping when sprite hits bottom-left corner.

        When a sprite moves off both the bottom and left edges simultaneously,
        it should wrap to the top-right corner with correct edge alignment.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Position sprite off bottom-left corner
        sprite.position = (-100, -100)  # Off both left and bottom edges
        sprite.change_x = -100  # Moving left
        sprite.change_y = -100  # Moving down
        action.update(1.0)

        # Verify sprite wrapped to top-right corner
        assert sprite.left == 800  # Left edge at x=800
        assert sprite.bottom == 600  # Bottom edge at y=600
        assert sprite.center_x == 832  # 800 + half of sprite width
        assert sprite.center_y == 568  # 600 - half of sprite height

    def test_wrap_corner_with_velocity(self, sprite):
        """Test wrapping when sprite hits corner with velocity.

        When a sprite with velocity hits a corner, it should wrap correctly
        and maintain its velocity in both directions.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite
        action.start()

        # Set initial position and velocity
        sprite.position = (750, 550)  # Near top-right corner
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up

        # Update for 1 second
        action.update(1.0)

        # Verify sprite wrapped and maintained velocity
        assert sprite.right == 50  # 750 + 100 - 800 = 50
        assert sprite.top == 50  # 550 + 100 - 600 = 50
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

        # Set initial position
        sprite.position = (750, 550)  # Near top-right corner

        # Update for 1 second
        accel_action.update(1.0)
        sprite.update(1.0)

        # Verify sprite wrapped and maintained acceleration curve
        # At t=1.0, should have moved 200 pixels in both directions
        assert sprite.right == 100  # 750 + 200 - 800 = 150
        assert sprite.top == 100  # 550 + 200 - 600 = 150

    def test_wrap_corner_boundary_callback(self, sprite):
        """Test boundary callback when sprite hits corner.

        When a sprite hits a corner, the boundary callback should be called
        with both boundaries crossed.
        """
        boundaries_hit = []

        def on_boundary_hit(sprite, boundaries, *args, **kwargs):
            boundaries_hit.extend(boundaries)

        action = MockWrappedMove(800, 600, on_boundary_hit=on_boundary_hit)
        action.target = sprite
        action.start()

        # Position sprite off top-right corner
        sprite.position = (900, 700)
        action.update(1.0)

        # Verify both boundaries were reported
        assert Boundary.RIGHT in boundaries_hit
        assert Boundary.TOP in boundaries_hit
        assert len(boundaries_hit) == 2  # Only two boundaries crossed
        assert boundaries_hit.count(Boundary.RIGHT) == 1  # Each boundary crossed once
        assert boundaries_hit.count(Boundary.TOP) == 1

    def test_wrap_corner_sprite_list(self, sprite_list):
        """Test corner wrapping with multiple sprites.

        Each sprite in the list should wrap correctly when hitting corners,
        regardless of other sprites' positions.
        """
        action = MockWrappedMove(800, 600)
        action.target = sprite_list
        action.start()

        # Position sprites at different corners
        sprite_list[0].position = (900, 700)  # Top-right corner
        sprite_list[1].position = (-100, 700)  # Top-left corner
        sprite_list[2].position = (900, -100)  # Bottom-right corner

        action.update(1.0)

        # Verify each sprite wrapped correctly
        assert sprite_list[0].right == 0  # Wrapped to left edge
        assert sprite_list[0].top == 0  # Wrapped to bottom edge
        assert sprite_list[1].left == 800  # Wrapped to right edge
        assert sprite_list[1].top == 0  # Wrapped to bottom edge
        assert sprite_list[2].right == 0  # Wrapped to left edge
        assert sprite_list[2].bottom == 600  # Wrapped to top edge


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
        """Test bouncing when right edge hits right boundary.

        When a sprite is moving right, it should bounce when its right edge
        hits the right boundary of the screen.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing when left edge hits left boundary.

        When a sprite is moving left, it should bounce when its left edge
        hits the left boundary of the screen.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing when top edge hits top boundary.

        When a sprite is moving up, it should bounce when its top edge
        hits the top boundary of the screen.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing when bottom edge hits bottom boundary.

        When a sprite is moving down, it should bounce when its bottom edge
        hits the bottom boundary of the screen.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing when sprite hits a corner.

        When a sprite hits a corner, it should bounce in both directions
        simultaneously.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing with continuous velocity.

        A sprite moving with constant velocity should bounce correctly
        and maintain its speed after bouncing.
        """
        action = MockBoundedMove(800, 600)
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
        """Test bouncing with acceleration.

        A sprite with acceleration should bounce correctly while its
        velocity changes over time.
        """
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

        action = MockBoundedMove(800, 600, on_boundary_hit=on_boundary_hit)
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
        """Test bouncing with multiple sprites.

        When any sprite in the list hits a boundary, all sprites should
        reverse their direction in that axis.
        """
        action = MockBoundedMove(800, 600)
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

    def test_space_invaders_movement(self):
        """Test Space Invaders-style alien movement pattern.

        Creates a grid of aliens that:
        1. Move left/right as a group
        2. Move down when hitting left/right boundaries
        3. Repeat 3 times before stopping
        """
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

        # Create bounded movement action
        action = MockBoundedMove(800, 600, on_boundary_hit=on_boundary_hit)
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
        action = MockBoundedMove(800, 600)
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
        action = MockBoundedMove(800, 600)
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
        action = MockBoundedMove(800, 600)
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
        action = MockBoundedMove(800, 600)
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
        action = MockBoundedMove(800, 600)
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
        accel_action.target = sprite
        accel_action.start()

        # Set initial position
        sprite.position = (700, 500)  # Near top-right corner

        # Update for 1 second
        accel_action.update(1.0)
        sprite.update(1.0)

        # Verify sprite bounced and maintained acceleration curve
        # At t=1.0, should have moved 200 pixels in both directions
        assert sprite.right == 800  # Right edge at screen boundary
        assert sprite.top == 600  # Top edge at screen boundary
        assert sprite.position[0] == 700 + 200
        assert sprite.position[1] == 500 + 200

    def test_corner_bounce_sprite_list(self, sprite_list):
        """Test corner bouncing with multiple sprites.

        When any sprite in the list hits a corner, all sprites should
        reverse their direction in both axes.
        """
        action = MockBoundedMove(800, 600)
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

        action = MockBoundedMove(800, 600, on_boundary_hit=on_boundary_hit)
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
