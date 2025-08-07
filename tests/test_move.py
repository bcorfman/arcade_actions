"""Test suite for boundary functionality in MoveUntil action."""

import arcade

from actions import MoveUntil, move_until
from actions.base import Action
from actions.pattern import time_elapsed


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestMoveUntilBoundaries:
    """Test suite for MoveUntil boundary functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_until_with_bounce_boundaries(self):
        """Test MoveUntil with bouncing boundaries."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        # Create bounds (left, bottom, right, top)
        bounds = (0, 0, 800, 600)

        # Move right - should hit boundary and bounce
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have hit boundary and bounced
        assert sprite.change_x < 0  # Moving left now
        assert sprite.center_x <= 800  # Kept in bounds

    def test_move_until_with_wrap_boundaries(self):
        """Test MoveUntil with wrapping boundaries."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        bounds = (0, 0, 800, 600)

        # Move right - should wrap to left side
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to left side
        assert sprite.center_x == 0  # Wrapped to left

    def test_move_until_with_boundary_callback(self):
        """Test MoveUntil boundary callback functionality."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        boundary_hits = []

        def on_boundary_hit(hitting_sprite, axis):
            boundary_hits.append((hitting_sprite, axis))

        bounds = (0, 0, 800, 600)
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary=on_boundary_hit,
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have called boundary callback
        assert len(boundary_hits) == 1
        assert boundary_hits[0][0] == sprite
        assert boundary_hits[0][1] == "x"  # Hit X axis boundary

    def test_move_until_vertical_boundaries(self):
        """Test MoveUntil with vertical boundary interactions."""
        sprite = create_test_sprite()
        sprite.center_y = 599  # Very close to top boundary

        bounds = (0, 0, 800, 600)

        # Move up - should hit top boundary and bounce
        move_until(
            sprite,
            velocity=(0, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have bounced (reversed Y velocity)
        assert sprite.change_y < 0  # Moving down now
        assert sprite.center_y <= 600  # Kept in bounds

    def test_move_until_no_boundaries(self):
        """Test MoveUntil without boundary checking."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x

        # No bounds specified - should move normally
        move_until(sprite, velocity=(100, 0), condition=time_elapsed(1.0), tag="movement")

        Action.update_all(0.5)
        sprite.update()  # Apply velocity to position

        # Should move normally without boundary interference
        assert sprite.center_x > initial_x
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert sprite.change_x == 100  # Velocity unchanged

    def test_move_until_boundary_clone(self):
        """Test cloning MoveUntil action with boundary settings."""
        bounds = (0, 0, 800, 600)

        def on_boundary(sprite, axis):
            pass

        # Create unbound action for cloning test
        original = MoveUntil(
            (50, 25), time_elapsed(2.0), bounds=bounds, boundary_behavior="wrap", on_boundary=on_boundary
        )

        cloned = original.clone()

        assert cloned.target_velocity == original.target_velocity
        assert cloned.bounds == original.bounds
        assert cloned.boundary_behavior == original.boundary_behavior
        assert cloned.on_boundary == original.on_boundary

    def test_move_until_multiple_sprites_boundaries(self):
        """Test MoveUntil boundary checking with multiple sprites."""
        sprites = arcade.SpriteList()
        for i in range(3):
            sprite = create_test_sprite()
            sprite.center_x = 799 + i * 0.1  # All very close to right boundary
            sprites.append(sprite)

        bounds = (0, 0, 800, 600)

        move_until(
            sprites,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="group_movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprites to new positions
        for sprite in sprites:
            sprite.update()
        # Check boundaries on new positions
        Action.update_all(0.001)

        # All sprites should have bounced
        for sprite in sprites:
            assert sprite.change_x < 0  # All moving left now
            assert sprite.center_x <= 800  # All kept in bounds
