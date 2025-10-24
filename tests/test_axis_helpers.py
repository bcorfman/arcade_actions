"""
Tests for axis-specific helper functions (move_x_until, move_y_until).

These tests verify that the target-first helper functions work correctly
with keyword parameters and return the appropriate axis-specific actions.
"""

import pytest
import arcade
from actions.base import Action
from actions.conditional import infinite
from actions.axis_move import MoveXUntil, MoveYUntil
from actions.helpers import move_x_until, move_y_until


def create_test_sprite() -> arcade.Sprite:
    """Create a test sprite for movement tests."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


def create_test_sprite_list() -> arcade.SpriteList:
    """Create a test sprite list for movement tests."""
    sprites = arcade.SpriteList()
    for i in range(3):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite.center_y = 100 + i * 30
        sprites.append(sprite)
    return sprites


class TestMoveXUntilHelper:
    """Test suite for move_x_until helper function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_x_until_basic_usage(self, test_sprite):
        """Test basic move_x_until usage with keyword parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = move_x_until(target=test_sprite, dx=5, condition=infinite)

        assert isinstance(action, MoveXUntil)
        assert action.target_velocity == (5, 0)
        assert action.target == test_sprite
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 0  # Y should be unchanged

    def test_move_x_until_with_all_parameters(self, test_sprite):
        """Test move_x_until with all optional parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        def velocity_provider():
            return (3, 0)

        def on_stop(data):
            pass

        def on_boundary_enter(sprite, axis, behavior):
            pass

        def on_boundary_exit(sprite, axis, behavior):
            pass

        action = move_x_until(
            target=test_sprite,
            dx=5,
            condition=infinite,
            on_stop=on_stop,
            tag="test_tag",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
            bounds=(0, 0, 200, 200),
            boundary_behavior="bounce",
        )

        assert isinstance(action, MoveXUntil)
        assert action.target_velocity == (5, 0)
        assert action.target == test_sprite
        assert action.tag == "test_tag"
        assert action.bounds == (0, 0, 200, 200)
        assert action.boundary_behavior == "bounce"
        # When velocity_provider is provided, it takes precedence over dx parameter
        assert test_sprite.change_x == 3  # From velocity_provider
        assert test_sprite.change_y == 0

    def test_move_x_until_preserves_y_velocity(self, test_sprite):
        """Test that move_x_until preserves existing Y velocity."""
        test_sprite.change_x = 0
        test_sprite.change_y = 3  # Pre-existing Y velocity

        action = move_x_until(target=test_sprite, dx=5, condition=infinite)

        assert isinstance(action, MoveXUntil)
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 3  # Y velocity should be preserved

    def test_move_x_until_with_sprite_list(self, test_sprite_list):
        """Test move_x_until with a sprite list."""
        # Set initial velocities
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = move_x_until(target=test_sprite_list, dx=5, condition=infinite)

        assert isinstance(action, MoveXUntil)
        assert action.target == test_sprite_list
        assert action.target_velocity == (5, 0)

        # All sprites should have X velocity set
        for sprite in test_sprite_list:
            assert sprite.change_x == 5
            assert sprite.change_y == 0

    def test_move_x_until_with_bounds(self, test_sprite):
        """Test move_x_until with boundary behavior."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 0  # At left boundary

        action = move_x_until(
            target=test_sprite,
            dx=-5,
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="limit",
        )

        assert isinstance(action, MoveXUntil)
        assert action.bounds == (0, 0, 200, 200)
        assert action.boundary_behavior == "limit"
        assert test_sprite.change_x == -5

    def test_move_x_until_with_velocity_provider(self, test_sprite):
        """Test move_x_until with a velocity provider function."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        def velocity_provider():
            return (7, 0)

        action = move_x_until(target=test_sprite, dx=5, condition=infinite, velocity_provider=velocity_provider)

        assert isinstance(action, MoveXUntil)
        assert action.velocity_provider == velocity_provider
        # When velocity_provider is provided, it takes precedence over dx parameter
        assert test_sprite.change_x == 7  # From velocity_provider

    def test_move_x_until_keyword_only_parameters(self, test_sprite):
        """Test that move_x_until requires keyword-only parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # This should work with keyword parameters
        action = move_x_until(target=test_sprite, dx=5, condition=infinite)
        assert isinstance(action, MoveXUntil)

        # This should fail with positional parameters
        with pytest.raises(TypeError):
            move_x_until(test_sprite, 5, infinite)

    def test_move_x_until_with_kwargs(self, test_sprite):
        """Test that move_x_until passes through additional kwargs."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Test with valid kwargs that MoveXUntil accepts
        action = move_x_until(target=test_sprite, dx=5, condition=infinite, bounds=(0, 0, 200, 200))

        assert isinstance(action, MoveXUntil)
        assert action.bounds == (0, 0, 200, 200)

    def test_move_x_until_return_value(self, test_sprite):
        """Test that move_x_until returns the created action."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = move_x_until(target=test_sprite, dx=5, condition=infinite)

        assert isinstance(action, MoveXUntil)
        assert action.target == test_sprite
        assert action.target_velocity == (5, 0)


class TestMoveYUntilHelper:
    """Test suite for move_y_until helper function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_y_until_basic_usage(self, test_sprite):
        """Test basic move_y_until usage with keyword parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = move_y_until(target=test_sprite, dy=5, condition=infinite)

        assert isinstance(action, MoveYUntil)
        assert action.target_velocity == (0, 5)
        assert action.target == test_sprite
        assert test_sprite.change_x == 0  # X should be unchanged
        assert test_sprite.change_y == 5

    def test_move_y_until_with_all_parameters(self, test_sprite):
        """Test move_y_until with all optional parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        def velocity_provider():
            return (0, 3)

        def on_stop(data):
            pass

        def on_boundary_enter(sprite, axis, behavior):
            pass

        def on_boundary_exit(sprite, axis, behavior):
            pass

        action = move_y_until(
            target=test_sprite,
            dy=5,
            condition=infinite,
            on_stop=on_stop,
            tag="test_tag",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
            bounds=(0, 0, 200, 200),
            boundary_behavior="bounce",
        )

        assert isinstance(action, MoveYUntil)
        assert action.target_velocity == (0, 5)
        assert action.target == test_sprite
        assert action.tag == "test_tag"
        assert action.bounds == (0, 0, 200, 200)
        assert action.boundary_behavior == "bounce"
        assert test_sprite.change_x == 0
        # When velocity_provider is provided, it takes precedence over dy parameter
        assert test_sprite.change_y == 3  # From velocity_provider

    def test_move_y_until_preserves_x_velocity(self, test_sprite):
        """Test that move_y_until preserves existing X velocity."""
        test_sprite.change_x = 3  # Pre-existing X velocity
        test_sprite.change_y = 0

        action = move_y_until(target=test_sprite, dy=5, condition=infinite)

        assert isinstance(action, MoveYUntil)
        assert test_sprite.change_x == 3  # X velocity should be preserved
        assert test_sprite.change_y == 5

    def test_move_y_until_with_sprite_list(self, test_sprite_list):
        """Test move_y_until with a sprite list."""
        # Set initial velocities
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = move_y_until(target=test_sprite_list, dy=5, condition=infinite)

        assert isinstance(action, MoveYUntil)
        assert action.target == test_sprite_list
        assert action.target_velocity == (0, 5)

        # All sprites should have Y velocity set
        for sprite in test_sprite_list:
            assert sprite.change_x == 0
            assert sprite.change_y == 5

    def test_move_y_until_with_bounds(self, test_sprite):
        """Test move_y_until with boundary behavior."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_y = 0  # At bottom boundary

        action = move_y_until(
            target=test_sprite,
            dy=-5,
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="limit",
        )

        assert isinstance(action, MoveYUntil)
        assert action.bounds == (0, 0, 200, 200)
        assert action.boundary_behavior == "limit"
        assert test_sprite.change_y == -5

    def test_move_y_until_with_velocity_provider(self, test_sprite):
        """Test move_y_until with a velocity provider function."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        def velocity_provider():
            return (0, 7)

        action = move_y_until(target=test_sprite, dy=5, condition=infinite, velocity_provider=velocity_provider)

        assert isinstance(action, MoveYUntil)
        assert action.velocity_provider == velocity_provider
        # When velocity_provider is provided, it takes precedence over dy parameter
        assert test_sprite.change_y == 7  # From velocity_provider

    def test_move_y_until_keyword_only_parameters(self, test_sprite):
        """Test that move_y_until requires keyword-only parameters."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # This should work with keyword parameters
        action = move_y_until(target=test_sprite, dy=5, condition=infinite)
        assert isinstance(action, MoveYUntil)

        # This should fail with positional parameters
        with pytest.raises(TypeError):
            move_y_until(test_sprite, 5, infinite)

    def test_move_y_until_with_kwargs(self, test_sprite):
        """Test that move_y_until passes through additional kwargs."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Test with valid kwargs that MoveYUntil accepts
        action = move_y_until(target=test_sprite, dy=5, condition=infinite, bounds=(0, 0, 200, 200))

        assert isinstance(action, MoveYUntil)
        assert action.bounds == (0, 0, 200, 200)

    def test_move_y_until_return_value(self, test_sprite):
        """Test that move_y_until returns the created action."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = move_y_until(target=test_sprite, dy=5, condition=infinite)

        assert isinstance(action, MoveYUntil)
        assert action.target == test_sprite
        assert action.target_velocity == (0, 5)


class TestAxisHelperIntegration:
    """Integration tests for axis helper functions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_axis_helpers_with_parallel_composition(self, test_sprite):
        """Test composing axis helpers with parallel actions."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Create axis-specific movements
        x_action = move_x_until(target=test_sprite, dx=3, condition=infinite)
        y_action = move_y_until(target=test_sprite, dy=2, condition=infinite)

        # Compose them with parallel
        combined = parallel(x_action, y_action)
        combined.apply(test_sprite)

        # Both velocities should be set
        assert test_sprite.change_x == 3
        assert test_sprite.change_y == 2

    def test_axis_helpers_with_different_boundaries(self, test_sprite):
        """Test axis helpers with different boundary behaviors."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 100
        test_sprite.center_y = 100

        # X-axis with limit behavior
        x_action = move_x_until(
            target=test_sprite,
            dx=-5,
            condition=infinite,
            bounds=(100, 0, 200, 200),
            boundary_behavior="limit",
        )

        # Y-axis with bounce behavior
        y_action = move_y_until(
            target=test_sprite,
            dy=3,
            condition=infinite,
            bounds=(0, 100, 200, 200),
            boundary_behavior="bounce",
        )

        # Compose them
        combined = parallel(x_action, y_action)
        combined.apply(test_sprite)

        # Both velocities should be set
        assert test_sprite.change_x == -5
        assert test_sprite.change_y == 3

    def test_axis_helpers_with_sprite_list(self, test_sprite_list):
        """Test axis helpers with sprite lists."""
        from actions.composite import parallel

        # Set initial velocities
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        # Create axis-specific movements for the sprite list
        x_action = move_x_until(target=test_sprite_list, dx=4, condition=infinite)
        y_action = move_y_until(target=test_sprite_list, dy=1, condition=infinite)

        # Compose them
        combined = parallel(x_action, y_action)
        combined.apply(test_sprite_list)

        # All sprites should have both velocities set
        for sprite in test_sprite_list:
            assert sprite.change_x == 4
            assert sprite.change_y == 1

    def test_axis_helpers_example_usage(self, test_sprite):
        """Test the example usage pattern from the prompt."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Example: scrolling background with bobbing sprites
        scroll = move_x_until(
            target=test_sprite,
            dx=-4,
            condition=infinite,
            bounds=(0, 0, 800, 600),
            boundary_behavior="limit",
        )

        bob = move_y_until(
            target=test_sprite,
            dy=2,
            condition=infinite,
            bounds=(0, 0, 800, 600),
            boundary_behavior="bounce",
        )

        # Compose the movements
        parallel(scroll, bob).apply(test_sprite)

        # Verify the result
        assert test_sprite.change_x == -4
        assert test_sprite.change_y == 2

    def test_axis_helpers_with_velocity_providers(self, test_sprite):
        """Test axis helpers with velocity providers."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0

        def x_velocity_provider():
            return (2, 0)

        def y_velocity_provider():
            return (0, 3)

        x_action = move_x_until(target=test_sprite, dx=1, condition=infinite, velocity_provider=x_velocity_provider)
        y_action = move_y_until(target=test_sprite, dy=1, condition=infinite, velocity_provider=y_velocity_provider)

        # Compose them
        combined = parallel(x_action, y_action)
        combined.apply(test_sprite)

        # When velocity_provider is provided, it takes precedence over dx/dy parameters
        assert test_sprite.change_x == 2  # From x_velocity_provider
        assert test_sprite.change_y == 3  # From y_velocity_provider

    def test_axis_helpers_action_contracts(self, test_sprite):
        """Test that axis helpers return actions that follow the action contract."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        x_action = move_x_until(target=test_sprite, dx=5, condition=infinite)
        y_action = move_y_until(target=test_sprite, dy=3, condition=infinite)

        # Test action contract methods
        assert hasattr(x_action, "apply")
        assert hasattr(x_action, "clone")
        assert hasattr(x_action, "reset")
        assert hasattr(x_action, "update_effect")

        assert hasattr(y_action, "apply")
        assert hasattr(y_action, "clone")
        assert hasattr(y_action, "reset")
        assert hasattr(y_action, "update_effect")

        # Test cloning
        x_clone = x_action.clone()
        y_clone = y_action.clone()

        assert isinstance(x_clone, MoveXUntil)
        assert isinstance(y_clone, MoveYUntil)
        assert x_clone.target_velocity == (5, 0)
        assert y_clone.target_velocity == (0, 3)
