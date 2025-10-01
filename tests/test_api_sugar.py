"""Test suite for API sugar - helper functions and operator overloading."""

import arcade
import pytest

from actions import Action, MoveUntil, RotateUntil, duration, move_until
from actions.conditional import (
    BlinkUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    ScaleUntil,
    TweenUntil,
)


# Fixtures for creating test sprites and lists
@pytest.fixture
def sprite() -> arcade.Sprite:
    """Return a simple sprite for testing."""
    return arcade.SpriteSolidColor(50, 50, color=arcade.color.RED)


@pytest.fixture
def sprite_list() -> arcade.SpriteList:
    """Return a simple sprite list for testing."""
    sprite_list = arcade.SpriteList()
    s1 = arcade.SpriteSolidColor(50, 50, color=arcade.color.GREEN)
    s2 = arcade.SpriteSolidColor(50, 50, color=arcade.color.BLUE)
    sprite_list.append(s1)
    sprite_list.append(s2)
    return sprite_list


class TestHelperFunctions:
    """Tests for helper function keyword/arg semantics (minimal smoke)."""

    def teardown_method(self):
        Action.stop_all()


class TestKeywordParameterSupport:
    """Tests for keyword parameter support in helper functions."""

    def teardown_method(self):
        Action.stop_all()

    def test_move_until_keyword_parameters(self, sprite):
        """Test move_until with keyword parameters as shown in docstring."""
        # Test the exact pattern shown in the docstring
        action = move_until(sprite, velocity=(5, 0), condition=lambda: sprite.center_x > 500)

        assert isinstance(action, MoveUntil)
        assert action.target == sprite
        assert action.target_velocity == (5, 0)
        assert len(Action._active_actions) == 1

    def test_move_until_keyword_only_parameters(self, sprite):
        """Test move_until with keyword-only parameters (new requirement)."""
        action = move_until(sprite, velocity=(5, 0), condition=lambda: False)

        assert isinstance(action, MoveUntil)
        assert action.target == sprite
        assert action.target_velocity == (5, 0)

    def test_move_until_with_optional_keywords(self, sprite):
        """Test move_until with optional keyword parameters."""
        action = move_until(sprite, velocity=(5, 0), condition=lambda: False, tag="optional_test")

        assert isinstance(action, MoveUntil)
        assert action.tag == "optional_test"

    def test_move_until_with_bounds_keyword(self, sprite):
        """Test move_until with bounds and boundary_behavior as keyword parameters."""
        bounds = (0, 0, 800, 600)
        action = move_until(sprite, velocity=(5, 0), condition=lambda: False, bounds=bounds, boundary_behavior="wrap")

        assert isinstance(action, MoveUntil)
        assert action.bounds == bounds
        assert action.boundary_behavior == "wrap"

    def test_move_until_sprite_list_keyword(self, sprite_list):
        """Test move_until with sprite list using keyword parameters."""
        action = move_until(sprite_list, velocity=(10, 5), condition=lambda: False)

        assert isinstance(action, MoveUntil)
        assert action.target == sprite_list
        assert action.target_velocity == (10, 5)

    def test_rotate_until_keyword_parameters(self, sprite):
        """Test rotate_until with keyword parameters as shown in docstring."""
        from actions import rotate_until

        action = rotate_until(sprite, angular_velocity=180, condition=duration(1.0))

        assert isinstance(action, RotateUntil)
        assert action.target == sprite
        assert action.target_angular_velocity == 180

    def test_follow_path_until_keyword_parameters(self, sprite):
        """Test follow_path_until with keyword parameters as shown in docstring."""
        from actions import follow_path_until

        path_points = [(100, 100), (200, 200), (300, 100)]
        action = follow_path_until(sprite, control_points=path_points, velocity=200, condition=duration(3.0))

        assert isinstance(action, FollowPathUntil)
        assert action.target == sprite
        assert action.control_points == path_points
        assert action.target_velocity == 200

    def test_blink_until_keyword_parameters(self, sprite):
        """Test blink_until with keyword parameters."""
        from actions import blink_until

        action = blink_until(sprite, seconds_until_change=0.5, condition=duration(2.0))

        assert isinstance(action, BlinkUntil)
        assert action.target == sprite
        assert action.target_seconds_until_change == 0.5

    def test_tween_until_keyword_parameters(self, sprite):
        """Test tween_until with keyword parameters."""
        from actions import tween_until

        action = tween_until(sprite, start_value=0, end_value=100, property_name="center_x", condition=duration(1.0))

        assert isinstance(action, TweenUntil)
        assert action.target == sprite
        assert action.start_value == 0
        assert action.end_value == 100
        assert action.property_name == "center_x"

    def test_scale_until_keyword_parameters(self, sprite):
        """Test scale_until with keyword parameters."""
        from actions import scale_until

        action = scale_until(sprite, velocity=0.5, condition=duration(2.0))

        assert isinstance(action, ScaleUntil)
        assert action.target == sprite
        assert action.target_scale_velocity == (0.5, 0.5)

    def test_fade_until_keyword_parameters(self, sprite):
        """Test fade_until with keyword parameters."""
        from actions import fade_until

        action = fade_until(sprite, velocity=-50, condition=duration(1.5))

        assert isinstance(action, FadeUntil)
        assert action.target == sprite
        assert action.target_fade_velocity == -50

    def test_delay_until_keyword_parameters(self, sprite):
        """Test delay_until with keyword parameters."""
        from actions import delay_until

        action = delay_until(sprite, condition=duration(1.0))

        assert isinstance(action, DelayUntil)
        assert action.target == sprite

    def test_keyword_parameter_error_handling(self, sprite):
        """Test that missing required keyword parameters raise appropriate errors."""
        from actions import move_until

        # Test with missing required parameters - these should raise TypeError for missing keyword arguments
        with pytest.raises(TypeError):
            move_until(sprite)  # Missing velocity and condition

        with pytest.raises(TypeError):
            move_until(sprite, velocity=(5, 0))  # Missing condition

        with pytest.raises(TypeError):
            move_until(sprite, condition=lambda: False)  # Missing velocity

    def test_keyword_parameter_with_callback(self, sprite):
        """Test keyword parameters with callback functions."""
        from actions import move_until

        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        action = move_until(sprite, velocity=(5, 0), condition=lambda: False, on_stop=on_stop, tag="callback_test")

        assert action.on_stop == on_stop
        assert action.tag == "callback_test"


class TestOperatorOverloading:
    """Covered comprehensively in tests/test_composite.py; keep none here."""

    def teardown_method(self):
        Action.stop_all()
