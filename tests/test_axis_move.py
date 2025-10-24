"""
Tests for axis-specific movement actions (MoveXUntil, MoveYUntil).

These tests verify that axis-specific actions only affect their respective axes
and can be safely composed via parallel() for orthogonal motion.
"""

import pytest
import arcade
from actions.base import Action
from actions.conditional import infinite
from actions.composite import parallel
from actions.axis_move import MoveXUntil, MoveYUntil


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


class TestMoveXUntil:
    """Test suite for MoveXUntil - X-axis only movement."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_x_until_constructor(self):
        """Test MoveXUntil constructor with all parameters."""
        bounds = (0, 0, 800, 600)
        on_stop_called = False

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        def velocity_provider():
            return (5, 0)

        def on_boundary_enter(sprite, axis, side):
            pass

        def on_boundary_exit(sprite, axis, side):
            pass

        action = MoveXUntil(
            velocity=(3, 0),
            condition=infinite,
            on_stop=on_stop,
            bounds=bounds,
            boundary_behavior="bounce",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )

        assert action.target_velocity == (3, 0)
        assert action.current_velocity == (3, 0)
        assert action.bounds == bounds
        assert action.boundary_behavior == "bounce"
        assert action.velocity_provider == velocity_provider
        assert action.on_boundary_enter == on_boundary_enter
        assert action.on_boundary_exit == on_boundary_exit

    def test_move_x_until_only_affects_x_axis(self, test_sprite):
        """Test that MoveXUntil only modifies change_x, not change_y."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveXUntil(velocity=(5, 0), condition=infinite)
        action.apply(test_sprite)

        # Should only set change_x, leave change_y untouched
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 0

    def test_move_x_until_preserves_existing_y_velocity(self, test_sprite):
        """Test that MoveXUntil preserves existing Y velocity."""
        test_sprite.change_x = 0
        test_sprite.change_y = 10  # Pre-existing Y velocity

        action = MoveXUntil(velocity=(5, 0), condition=infinite)
        action.apply(test_sprite)

        # Should set change_x but preserve change_y
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 10

    def test_move_x_until_clone(self):
        """Test MoveXUntil clone functionality."""
        bounds = (0, 0, 800, 600)
        action = MoveXUntil(velocity=(4, 0), condition=infinite, bounds=bounds, boundary_behavior="wrap")

        cloned = action.clone()

        assert isinstance(cloned, MoveXUntil)
        assert cloned.target_velocity == (4, 0)
        assert cloned.bounds == bounds
        assert cloned.boundary_behavior == "wrap"
        assert cloned is not action  # Different instance

    def test_move_x_until_reset(self, test_sprite):
        """Test MoveXUntil reset functionality."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveXUntil(velocity=(6, 0), condition=infinite)
        action.apply(test_sprite)

        # Modify velocity
        action.current_velocity = (2, 0)
        test_sprite.change_x = 2

        # Reset should restore original velocity
        action.reset()
        assert action.current_velocity == (6, 0)
        assert test_sprite.change_x == 6
        assert test_sprite.change_y == 0  # Still untouched

    def test_move_x_until_sprite_list(self, test_sprite_list):
        """Test MoveXUntil with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = MoveXUntil(velocity=(7, 0), condition=infinite)
        action.apply(test_sprite_list)

        # All sprites should have X velocity, no Y velocity
        for sprite in test_sprite_list:
            assert sprite.change_x == 7
            assert sprite.change_y == 0


class TestMoveYUntil:
    """Test suite for MoveYUntil - Y-axis only movement."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_y_until_constructor(self):
        """Test MoveYUntil constructor with all parameters."""
        bounds = (0, 0, 800, 600)
        on_stop_called = False

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        def velocity_provider():
            return (0, 5)

        def on_boundary_enter(sprite, axis, side):
            pass

        def on_boundary_exit(sprite, axis, side):
            pass

        action = MoveYUntil(
            velocity=(0, 3),
            condition=infinite,
            on_stop=on_stop,
            bounds=bounds,
            boundary_behavior="bounce",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )

        assert action.target_velocity == (0, 3)
        assert action.current_velocity == (0, 3)
        assert action.bounds == bounds
        assert action.boundary_behavior == "bounce"
        assert action.velocity_provider == velocity_provider
        assert action.on_boundary_enter == on_boundary_enter
        assert action.on_boundary_exit == on_boundary_exit

    def test_move_y_until_only_affects_y_axis(self, test_sprite):
        """Test that MoveYUntil only modifies change_y, not change_x."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 5), condition=infinite)
        action.apply(test_sprite)

        # Should only set change_y, leave change_x untouched
        assert test_sprite.change_x == 0
        assert test_sprite.change_y == 5

    def test_move_y_until_preserves_existing_x_velocity(self, test_sprite):
        """Test that MoveYUntil preserves existing X velocity."""
        test_sprite.change_x = 10  # Pre-existing X velocity
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 5), condition=infinite)
        action.apply(test_sprite)

        # Should set change_y but preserve change_x
        assert test_sprite.change_x == 10
        assert test_sprite.change_y == 5

    def test_move_y_until_clone(self):
        """Test MoveYUntil clone functionality."""
        bounds = (0, 0, 800, 600)
        action = MoveYUntil(velocity=(0, 4), condition=infinite, bounds=bounds, boundary_behavior="wrap")

        cloned = action.clone()

        assert isinstance(cloned, MoveYUntil)
        assert cloned.target_velocity == (0, 4)
        assert cloned.bounds == bounds
        assert cloned.boundary_behavior == "wrap"
        assert cloned is not action  # Different instance

    def test_move_y_until_reset(self, test_sprite):
        """Test MoveYUntil reset functionality."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 6), condition=infinite)
        action.apply(test_sprite)

        # Modify velocity
        action.current_velocity = (0, 2)
        test_sprite.change_y = 2

        # Reset should restore original velocity
        action.reset()
        assert action.current_velocity == (0, 6)
        assert test_sprite.change_x == 0  # Still untouched
        assert test_sprite.change_y == 6

    def test_move_y_until_sprite_list(self, test_sprite_list):
        """Test MoveYUntil with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 7), condition=infinite)
        action.apply(test_sprite_list)

        # All sprites should have Y velocity, no X velocity
        for sprite in test_sprite_list:
            assert sprite.change_x == 0
            assert sprite.change_y == 7


class TestAxisComposition:
    """Test suite for composing axis-specific actions via parallel()."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_x_and_y_movement(self, test_sprite):
        """Test composing MoveXUntil and MoveYUntil via parallel()."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        x_action = MoveXUntil(velocity=(-3, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, 2), condition=infinite)

        parallel(x_action, y_action).apply(test_sprite)

        # Should have both X and Y velocities
        assert test_sprite.change_x == -3
        assert test_sprite.change_y == 2

    def test_parallel_x_and_y_with_different_boundaries(self, test_sprite):
        """Test composing X and Y actions with different boundary behaviors."""
        test_sprite.center_x = 100  # At left boundary
        test_sprite.center_y = 100  # At bottom boundary
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        bounds = (100, 100, 800, 600)

        x_action = MoveXUntil(
            velocity=(-5, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",  # X limited
        )
        y_action = MoveYUntil(
            velocity=(0, -5),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",  # Y bounces
        )

        parallel(x_action, y_action).apply(test_sprite)

        # Both velocities should be set initially
        assert test_sprite.change_x == -5
        assert test_sprite.change_y == -5

        # Test that the actions were created with correct boundary behaviors
        assert x_action.boundary_behavior == "limit"
        assert y_action.boundary_behavior == "bounce"

    def test_parallel_with_sprite_list(self, test_sprite_list):
        """Test parallel composition with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        x_action = MoveXUntil(velocity=(4, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, -2), condition=infinite)

        parallel(x_action, y_action).apply(test_sprite_list)

        # All sprites should have both velocities
        for sprite in test_sprite_list:
            assert sprite.change_x == 4
            assert sprite.change_y == -2


class TestAxisMoveIntegration:
    """Integration tests for axis-specific movement actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_axis_move_action_contracts(self):
        """Test that axis-specific actions follow Action contracts."""
        x_action = MoveXUntil(velocity=(1, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, 1), condition=infinite)

        # Test that they have required Action methods
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
        assert x_clone.target_velocity == (1, 0)
        assert y_clone.target_velocity == (0, 1)
