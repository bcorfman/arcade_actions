"""
Tests for axis-aware pattern factories.

These tests verify that create_bounce_pattern and create_patrol_pattern
support the new axis parameter and return appropriate axis-specific actions.
"""

import pytest
import arcade
from actions.base import Action
from actions.conditional import infinite, MoveUntil
from actions.axis_move import MoveXUntil, MoveYUntil
from actions.pattern import create_bounce_pattern, create_patrol_pattern


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


class TestBouncePatternAxis:
    """Test suite for axis-aware create_bounce_pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_create_bounce_pattern_default_axis(self):
        """Test create_bounce_pattern with default axis="both" (legacy behavior)."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        pattern = create_bounce_pattern(velocity, bounds)

        # Should return standard MoveUntil (legacy behavior)
        assert isinstance(pattern, MoveUntil)
        assert pattern.target_velocity == velocity
        assert pattern.bounds == bounds
        assert pattern.boundary_behavior == "bounce"

    def test_create_bounce_pattern_x_axis(self):
        """Test create_bounce_pattern with axis="x"."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        pattern = create_bounce_pattern(velocity, bounds, axis="x")

        # Should return MoveXUntil
        assert isinstance(pattern, MoveXUntil)
        assert pattern.target_velocity == velocity
        assert pattern.bounds == bounds
        assert pattern.boundary_behavior == "bounce"

    def test_create_bounce_pattern_y_axis(self):
        """Test create_bounce_pattern with axis="y"."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        pattern = create_bounce_pattern(velocity, bounds, axis="y")

        # Should return MoveYUntil
        assert isinstance(pattern, MoveYUntil)
        assert pattern.target_velocity == velocity
        assert pattern.bounds == bounds
        assert pattern.boundary_behavior == "bounce"

    def test_create_bounce_pattern_invalid_axis(self):
        """Test create_bounce_pattern with invalid axis parameter."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        with pytest.raises(ValueError, match="axis must be one of"):
            create_bounce_pattern(velocity, bounds, axis="invalid")

    def test_create_bounce_pattern_x_axis_composition(self, test_sprite):
        """Test that X-axis bounce pattern composes with separate Y motion."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Create X-axis bounce pattern
        bounce_x = create_bounce_pattern(
            velocity=(150, 0),  # Only X velocity
            bounds=(0, 0, 800, 600),
            axis="x",
        )

        # Create separate Y-axis movement
        move_y = MoveYUntil(velocity=(0, 100), condition=infinite)

        # Apply both actions
        bounce_x.apply(test_sprite)
        move_y.apply(test_sprite)

        # X-axis should have bounce behavior, Y should have simple movement
        assert test_sprite.change_x == 150
        assert test_sprite.change_y == 100

    def test_create_bounce_pattern_y_axis_composition(self, test_sprite):
        """Test that Y-axis bounce pattern composes with separate X motion."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Create Y-axis bounce pattern
        bounce_y = create_bounce_pattern(
            velocity=(0, 100),  # Only Y velocity
            bounds=(0, 0, 800, 600),
            axis="y",
        )

        # Create separate X-axis movement
        move_x = MoveXUntil(velocity=(150, 0), condition=infinite)

        # Apply both actions
        bounce_y.apply(test_sprite)
        move_x.apply(test_sprite)

        # Y-axis should have bounce behavior, X should have simple movement
        assert test_sprite.change_x == 150
        assert test_sprite.change_y == 100

    def test_create_bounce_pattern_axis_validation(self):
        """Test axis parameter validation."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        # Valid axis values
        for axis in ["both", "x", "y"]:
            pattern = create_bounce_pattern(velocity, bounds, axis=axis)
            assert pattern is not None

        # Invalid axis values
        with pytest.raises(ValueError):
            create_bounce_pattern(velocity, bounds, axis="invalid")

        with pytest.raises(ValueError):
            create_bounce_pattern(velocity, bounds, axis="")

        with pytest.raises(ValueError):
            create_bounce_pattern(velocity, bounds, axis=None)

    def test_create_bounce_pattern_legacy_compatibility(self):
        """Test that existing code without axis parameter still works."""
        velocity = (150, 100)
        bounds = (0, 0, 800, 600)

        # Should work exactly like before
        pattern = create_bounce_pattern(velocity, bounds)

        assert isinstance(pattern, MoveUntil)
        assert pattern.target_velocity == velocity
        assert pattern.bounds == bounds
        assert pattern.boundary_behavior == "bounce"


class TestPatrolPatternAxis:
    """Test suite for axis-aware create_patrol_pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_create_patrol_pattern_default_axis(self):
        """Test create_patrol_pattern with default axis="both" (legacy behavior)."""
        start_pos = (100, 100)
        end_pos = (200, 200)
        speed = 50

        pattern = create_patrol_pattern(start_pos, end_pos, speed)

        # Should return standard MoveUntil (legacy behavior)
        assert isinstance(pattern, MoveUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"

    def test_create_patrol_pattern_x_axis(self):
        """Test create_patrol_pattern with axis="x"."""
        start_pos = (100, 100)
        end_pos = (200, 100)  # Only X movement
        speed = 50

        pattern = create_patrol_pattern(start_pos, end_pos, speed, axis="x")

        # Should return MoveXUntil
        assert isinstance(pattern, MoveXUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"

    def test_create_patrol_pattern_y_axis(self):
        """Test create_patrol_pattern with axis="y"."""
        start_pos = (100, 100)
        end_pos = (100, 200)  # Only Y movement
        speed = 50

        pattern = create_patrol_pattern(start_pos, end_pos, speed, axis="y")

        # Should return MoveYUntil
        assert isinstance(pattern, MoveYUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"

    def test_create_patrol_pattern_invalid_axis(self):
        """Test create_patrol_pattern with invalid axis parameter."""
        start_pos = (100, 100)
        end_pos = (200, 200)
        speed = 50

        with pytest.raises(ValueError, match="axis must be one of"):
            create_patrol_pattern(start_pos, end_pos, speed, axis="invalid")

    def test_create_patrol_pattern_x_axis_composition(self, test_sprite):
        """Test that X-axis patrol pattern composes with separate Y motion."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 100
        test_sprite.center_y = 100

        # Create X-axis patrol pattern
        patrol_x = create_patrol_pattern(
            start_pos=(100, 100),
            end_pos=(200, 100),  # Only X movement
            speed=50,
            axis="x",
        )

        # Create separate Y-axis movement
        move_y = MoveYUntil(velocity=(0, 25), condition=infinite)

        # Apply both actions
        patrol_x.apply(test_sprite)
        move_y.apply(test_sprite)

        # Both velocities should be set
        assert test_sprite.change_x != 0  # Patrol pattern sets X velocity
        assert test_sprite.change_y == 25

    def test_create_patrol_pattern_y_axis_composition(self, test_sprite):
        """Test that Y-axis patrol pattern composes with separate X motion."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 100
        test_sprite.center_y = 100

        # Create Y-axis patrol pattern
        patrol_y = create_patrol_pattern(
            start_pos=(100, 100),
            end_pos=(100, 200),  # Only Y movement
            speed=50,
            axis="y",
        )

        # Create separate X-axis movement
        move_x = MoveXUntil(velocity=(25, 0), condition=infinite)

        # Apply both actions
        patrol_y.apply(test_sprite)
        move_x.apply(test_sprite)

        # Both velocities should be set
        assert test_sprite.change_x == 25
        assert test_sprite.change_y != 0  # Patrol pattern sets Y velocity

    def test_create_patrol_pattern_axis_validation(self):
        """Test axis parameter validation."""
        start_pos = (100, 100)
        end_pos = (200, 200)
        speed = 50

        # Valid axis values
        for axis in ["both", "x", "y"]:
            pattern = create_patrol_pattern(start_pos, end_pos, speed, axis=axis)
            assert pattern is not None

        # Invalid axis values
        with pytest.raises(ValueError):
            create_patrol_pattern(start_pos, end_pos, speed, axis="invalid")

        with pytest.raises(ValueError):
            create_patrol_pattern(start_pos, end_pos, speed, axis="")

        with pytest.raises(ValueError):
            create_patrol_pattern(start_pos, end_pos, speed, axis=None)

    def test_create_patrol_pattern_legacy_compatibility(self):
        """Test that existing code without axis parameter still works."""
        start_pos = (100, 100)
        end_pos = (200, 200)
        speed = 50

        # Should work exactly like before
        pattern = create_patrol_pattern(start_pos, end_pos, speed)

        assert isinstance(pattern, MoveUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"

    def test_create_patrol_pattern_with_progress_parameters(self):
        """Test patrol pattern with start_progress and end_progress parameters."""
        start_pos = (100, 100)
        end_pos = (200, 200)
        speed = 50

        # Test with progress parameters
        pattern = create_patrol_pattern(start_pos, end_pos, speed, start_progress=0.2, end_progress=0.8, axis="x")

        assert isinstance(pattern, MoveXUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"

    def test_create_patrol_pattern_diagonal_with_axis(self):
        """Test patrol pattern with diagonal movement but axis restriction."""
        start_pos = (100, 100)
        end_pos = (200, 200)  # Diagonal movement
        speed = 50

        # Even with diagonal movement, axis="x" should only affect X
        pattern = create_patrol_pattern(start_pos, end_pos, speed, axis="x")

        assert isinstance(pattern, MoveXUntil)
        assert pattern.bounds is not None
        assert pattern.boundary_behavior == "bounce"


class TestPatternAxisIntegration:
    """Integration tests for axis-aware pattern factories."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_pattern_factories_with_parallel_composition(self, test_sprite):
        """Test composing axis-specific patterns with parallel actions."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 100
        test_sprite.center_y = 100

        # Create axis-specific patterns
        bounce_x = create_bounce_pattern(velocity=(150, 0), bounds=(0, 0, 800, 600), axis="x")
        patrol_y = create_patrol_pattern(
            start_pos=(100, 100),
            end_pos=(100, 200),
            speed=50,
            axis="y",
        )

        # Compose them with parallel
        combined = parallel(bounce_x, patrol_y)
        combined.apply(test_sprite)

        # Both velocities should be set
        assert test_sprite.change_x == 150
        assert test_sprite.change_y != 0  # Patrol pattern sets Y velocity

    def test_pattern_factories_with_sprite_list(self, test_sprite_list):
        """Test axis-specific patterns with sprite lists."""
        from actions.composite import parallel

        # Set initial positions
        for i, sprite in enumerate(test_sprite_list):
            sprite.center_x = 100 + i * 50
            sprite.center_y = 100 + i * 30
            sprite.change_x = 0
            sprite.change_y = 0

        # Create axis-specific patterns for the sprite list
        bounce_x = create_bounce_pattern(velocity=(100, 0), bounds=(0, 0, 800, 600), axis="x")
        bounce_y = create_bounce_pattern(velocity=(0, 75), bounds=(0, 0, 800, 600), axis="y")

        # Compose them
        combined = parallel(bounce_x, bounce_y)
        combined.apply(test_sprite_list)

        # All sprites should have both velocities set
        for sprite in test_sprite_list:
            assert sprite.change_x == 100
            assert sprite.change_y == 75

    def test_pattern_factories_example_usage(self, test_sprite):
        """Test the example usage pattern from the prompt."""
        from actions.composite import parallel

        test_sprite.change_x = 0
        test_sprite.change_y = 0
        test_sprite.center_x = 100
        test_sprite.center_y = 100

        # Example: scrolling background with bobbing sprites
        scroll = create_bounce_pattern(
            velocity=(-4, 0),
            bounds=(0, 0, 800, 600),
            axis="x",
        )

        bob = create_patrol_pattern(
            start_pos=(100, 100),
            end_pos=(100, 200),
            speed=2,
            axis="y",
        )

        # Compose the movements
        parallel(scroll, bob).apply(test_sprite)

        # Verify the result
        assert test_sprite.change_x == -4
        assert test_sprite.change_y != 0  # Patrol pattern sets Y velocity

    def test_pattern_factories_action_contracts(self):
        """Test that pattern factories return actions that follow the action contract."""
        # Test bounce pattern
        bounce_x = create_bounce_pattern(velocity=(150, 0), bounds=(0, 0, 800, 600), axis="x")
        bounce_y = create_bounce_pattern(velocity=(0, 100), bounds=(0, 0, 800, 600), axis="y")

        # Test patrol pattern
        patrol_x = create_patrol_pattern(start_pos=(100, 100), end_pos=(200, 100), speed=50, axis="x")
        patrol_y = create_patrol_pattern(start_pos=(100, 100), end_pos=(100, 200), speed=50, axis="y")

        # Test action contract methods
        for pattern in [bounce_x, bounce_y, patrol_x, patrol_y]:
            assert hasattr(pattern, "apply")
            assert hasattr(pattern, "clone")
            assert hasattr(pattern, "reset")
            assert hasattr(pattern, "update_effect")

        # Test cloning
        bounce_x_clone = bounce_x.clone()
        patrol_y_clone = patrol_y.clone()

        assert isinstance(bounce_x_clone, MoveXUntil)
        assert isinstance(patrol_y_clone, MoveYUntil)

    def test_pattern_factories_debug_system(self, test_sprite):
        """Test that axis-specific patterns integrate with the debug system."""
        from actions.config import set_debug_options

        test_sprite.change_x = 0
        test_sprite.change_y = 0

        # Enable debug logging
        set_debug_options(level=1, include=["MoveXUntil", "MoveYUntil"])

        # Create axis-specific patterns
        bounce_x = create_bounce_pattern(velocity=(150, 0), bounds=(0, 0, 800, 600), axis="x")
        bounce_y = create_bounce_pattern(velocity=(0, 100), bounds=(0, 0, 800, 600), axis="y")

        # Apply them
        bounce_x.apply(test_sprite)
        bounce_y.apply(test_sprite)

        # Verify they work
        assert test_sprite.change_x == 150
        assert test_sprite.change_y == 100

        # Reset debug options
        set_debug_options(level=0)
