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
    """Tests for thin wrapper helper functions."""

    def teardown_method(self):
        Action.stop_all()

    def test_move_until_helper_applies_action(self, sprite):
        """Test move_until helper creates and applies a MoveUntil action."""
        # This should create a MoveUntil action and apply it to the sprite
        action = move_until(sprite, velocity=(10, 0), condition=lambda: False, tag="test_move")

        assert isinstance(action, MoveUntil)
        assert len(Action._active_actions) == 1
        assert action in Action._active_actions
        assert action.tag == "test_move"
        assert action.target == sprite

    def test_move_until_helper_returns_action(self, sprite):
        """Test move_until helper returns the created action instance."""
        move_action = move_until(sprite, velocity=(5, 0), condition=lambda: False)
        assert isinstance(move_action, MoveUntil)
        # We can still interact with the returned action
        move_action.set_factor(0.5)
        assert move_action.current_velocity == (2.5, 0.0)

    def test_helper_unbound_action_creation(self):
        """Test that creating unbound actions uses the Action classes directly."""
        # For unbound actions, use the Action classes directly
        raw_action = MoveUntil((10, 0), lambda: False)

        assert isinstance(raw_action, MoveUntil)
        assert not raw_action.target  # Not bound to any sprite
        assert len(Action._active_actions) == 0  # Should not be in the active list


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
    """Tests for operator-based composition (+ for sequence, | for parallel)."""

    def teardown_method(self):
        Action.stop_all()

    def test_add_operator_for_sequence(self):
        """Test that the '+' operator creates a sequential action."""
        from actions.composite import _Sequence

        action1 = MoveUntil((10, 0), lambda: False)
        action2 = RotateUntil(5, lambda: False)

        sequence_action = action1 + action2

        assert isinstance(sequence_action, _Sequence)
        assert sequence_action.actions == [action1, action2]
        assert len(Action._active_actions) == 0  # Should not be active yet

    def test_or_operator_for_parallel(self):
        """Test that the '|' operator creates a parallel action."""
        from actions.composite import _Parallel

        action1 = MoveUntil((10, 0), lambda: False)
        action2 = RotateUntil(5, lambda: False)

        parallel_action = action1 | action2

        assert isinstance(parallel_action, _Parallel)
        assert parallel_action.actions == [action1, action2]
        assert len(Action._active_actions) == 0

    def test_right_hand_operators(self):
        """Test right-hand operators (__radd__, __ror__) for composition."""
        from actions.composite import _Parallel, _Sequence
        from actions.conditional import DelayUntil

        move = MoveUntil((10, 0), lambda: False)
        delay = DelayUntil(lambda: False)

        # Test __radd__
        seq = delay + move
        assert isinstance(seq, _Sequence)
        assert seq.actions == [delay, move]

        # Test __ror__
        par = delay | move
        assert isinstance(par, _Parallel)
        assert par.actions == [delay, move]

    def test_operator_precedence(self, sprite):
        """Test operator precedence and complex compositions."""
        from actions.composite import _Parallel, _Sequence
        from actions.conditional import DelayUntil

        a = MoveUntil((10, 0), lambda: False)
        b = RotateUntil(5, lambda: False)
        c = DelayUntil(lambda: False)

        # Test precedence: (a + b) | c should be different from a + (b | c)
        left_assoc = (a + b) | c
        right_assoc = a + (b | c)

        assert isinstance(left_assoc, _Parallel)
        assert isinstance(left_assoc.actions[0], _Sequence)
        assert left_assoc.actions[0].actions == [a, b]
        assert left_assoc.actions[1] == c

        assert isinstance(right_assoc, _Sequence)
        assert right_assoc.actions[0] == a
        assert isinstance(right_assoc.actions[1], _Parallel)
        assert right_assoc.actions[1].actions == [b, c]

    def test_complex_chaining_with_apply(self, sprite):
        """Test complex operator chaining with apply."""

        a = MoveUntil((10, 0), lambda: False)
        b = RotateUntil(5, lambda: False)
        c = DelayUntil(lambda: False)

        # Create complex composition
        complex_action = (a + b) | c
        complex_action.apply(sprite)

        assert len(Action._active_actions) == 1
        assert complex_action.target == sprite

    def test_repr_for_composite_actions(self):
        """Test that composite actions have meaningful repr."""
        from actions.conditional import DelayUntil

        a = MoveUntil((5, 0), lambda: False)
        b = RotateUntil(2, lambda: False)
        c = DelayUntil(lambda: False)

        # Create nested composition
        action = c + (a | b)

        expected_repr = "_Sequence(actions=[DelayUntil(condition=...), _Parallel(actions=[MoveUntil(target_velocity=(5, 0), ...), RotateUntil(angular_velocity=2, ...)])])"
        assert "_Sequence" in repr(action)
        assert "_Parallel" in repr(action)
