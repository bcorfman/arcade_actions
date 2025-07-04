"""Test suite for easing.py - Easing wrapper functionality."""

import math

import arcade
import pytest
from arcade import easing

from actions import (
    Action,
    BlinkUntil,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
)
from actions.easing import Easing


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    sprite.angle = 0
    sprite.scale = 1.0
    sprite.alpha = 255
    return sprite


def create_test_sprite_list():
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    sprite1 = create_test_sprite()
    sprite2 = create_test_sprite()
    sprite1.center_x = 50
    sprite2.center_x = 150
    sprite_list.append(sprite1)
    sprite_list.append(sprite2)
    return sprite_list


class TestSetFactor:
    """Test suite for set_factor functionality on all conditional actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_move_until_set_factor(self):
        """Test MoveUntil set_factor functionality."""
        sprite = create_test_sprite()
        action = MoveUntil((100, 50), lambda: False)
        action.apply(sprite)

        # Test factor scaling
        action.set_factor(0.5)
        assert action.current_velocity == (50.0, 25.0)
        assert sprite.change_x == 50.0
        assert sprite.change_y == 25.0

        # Test zero factor
        action.set_factor(0.0)
        assert action.current_velocity == (0.0, 0.0)
        assert sprite.change_x == 0.0
        assert sprite.change_y == 0.0

        # Test factor > 1
        action.set_factor(2.0)
        assert action.current_velocity == (200.0, 100.0)
        assert sprite.change_x == 200.0
        assert sprite.change_y == 100.0

        # Test negative factor
        action.set_factor(-1.0)
        assert action.current_velocity == (-100.0, -50.0)
        assert sprite.change_x == -100.0
        assert sprite.change_y == -50.0

    def test_rotate_until_set_factor(self):
        """Test RotateUntil set_factor functionality."""
        sprite = create_test_sprite()
        action = RotateUntil(90, lambda: False)
        action.apply(sprite)

        # Test factor scaling
        action.set_factor(0.5)
        assert action.current_angular_velocity == 45.0
        assert sprite.change_angle == 45.0

        # Test zero factor
        action.set_factor(0.0)
        assert action.current_angular_velocity == 0.0
        assert sprite.change_angle == 0.0

        # Test factor > 1
        action.set_factor(2.0)
        assert action.current_angular_velocity == 180.0
        assert sprite.change_angle == 180.0

    def test_scale_until_set_factor(self):
        """Test ScaleUntil set_factor functionality."""
        sprite = create_test_sprite()
        action = ScaleUntil((0.5, 0.3), lambda: False)
        action.apply(sprite)

        # Test factor scaling
        action.set_factor(0.5)
        assert action.current_scale_velocity == (0.25, 0.15)

        # Test zero factor
        action.set_factor(0.0)
        assert action.current_scale_velocity == (0.0, 0.0)

        # Test factor > 1
        action.set_factor(2.0)
        assert action.current_scale_velocity == (1.0, 0.6)

    def test_fade_until_set_factor(self):
        """Test FadeUntil set_factor functionality."""
        sprite = create_test_sprite()
        action = FadeUntil(-100, lambda: False)
        action.apply(sprite)

        # Test factor scaling
        action.set_factor(0.5)
        assert action.current_fade_velocity == -50.0

        # Test zero factor
        action.set_factor(0.0)
        assert action.current_fade_velocity == 0.0

        # Test factor > 1
        action.set_factor(2.0)
        assert action.current_fade_velocity == -200.0

    def test_blink_until_set_factor(self):
        """Test BlinkUntil set_factor functionality."""
        sprite = create_test_sprite()
        action = BlinkUntil(1.0, lambda: False)
        action.apply(sprite)

        # Test factor scaling (higher factor = faster blinking)
        action.set_factor(2.0)
        assert action.current_seconds_until_change == 0.5

        # Test factor < 1 (slower blinking)
        action.set_factor(0.5)
        assert action.current_seconds_until_change == 2.0

        # Test zero factor (stops blinking)
        action.set_factor(0.0)
        assert action.current_seconds_until_change == float("inf")

        # Test negative factor (should stop blinking)
        action.set_factor(-1.0)
        assert action.current_seconds_until_change == float("inf")

    def test_follow_path_until_set_factor(self):
        """Test FollowPathUntil set_factor functionality."""
        sprite = create_test_sprite()
        control_points = [(100, 100), (200, 200), (300, 100)]
        action = FollowPathUntil(control_points, 150, lambda: False)
        action.apply(sprite)

        # Test factor scaling
        action.set_factor(0.5)
        assert action.current_velocity == 75.0

        # Test zero factor
        action.set_factor(0.0)
        assert action.current_velocity == 0.0

        # Test factor > 1
        action.set_factor(2.0)
        assert action.current_velocity == 300.0

    def test_set_factor_with_sprite_list(self):
        """Test set_factor works with sprite lists."""
        sprite_list = create_test_sprite_list()
        action = MoveUntil((100, 0), lambda: False)
        action.apply(sprite_list)

        action.set_factor(0.5)
        for sprite in sprite_list:
            assert sprite.change_x == 50.0
            assert sprite.change_y == 0.0


class TestEasing:
    """Test suite for Easing wrapper functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_easing_initialization(self):
        """Test Easing wrapper initialization."""
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)

        assert easing_action.wrapped_action == move
        assert easing_action.easing_duration == 2.0
        assert easing_action.ease_function == easing.ease_in_out
        assert easing_action._elapsed == 0.0
        assert not easing_action._easing_complete

    def test_easing_invalid_duration(self):
        """Test Easing with invalid duration raises error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="seconds must be positive"):
            Easing(move, seconds=0.0)

        with pytest.raises(ValueError, match="seconds must be positive"):
            Easing(move, seconds=-1.0)

    def test_easing_apply(self):
        """Test Easing apply method applies both wrapper and wrapped action."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)

        easing_action.apply(sprite, tag="test")

        # Both actions should be in active list
        active_actions = Action._active_actions
        assert len(active_actions) == 2  # Easing wrapper + wrapped action
        assert easing_action in active_actions
        assert move in active_actions

    def test_easing_execution_ease_in_out(self):
        """Test Easing execution with ease_in_out function."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0, ease_function=easing.ease_in_out)
        easing_action.apply(sprite, tag="test")

        # At start, factor should be 0 (no movement)
        Action.update_all(0.0)
        assert sprite.change_x == 0.0

        # At t=0.25, ease_in_out(0.25) ≈ 0.125
        Action.update_all(0.25)
        expected_factor = easing.ease_in_out(0.25)
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

        # At t=0.5, ease_in_out(0.5) = 0.5
        Action.update_all(0.25)
        expected_factor = easing.ease_in_out(0.5)
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

        # At t=1.0, ease_in_out(1.0) = 1.0 and easing should be complete
        Action.update_all(0.5)
        assert sprite.change_x == 100.0
        assert easing_action.done

    def test_easing_execution_ease_in(self):
        """Test Easing execution with ease_in function."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0, ease_function=easing.ease_in)
        easing_action.apply(sprite, tag="test")

        # At t=0.5, ease_in(0.5) = 0.25
        Action.update_all(0.5)
        expected_factor = easing.ease_in(0.5)
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_easing_execution_ease_out(self):
        """Test Easing execution with ease_out function."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0, ease_function=easing.ease_out)
        easing_action.apply(sprite, tag="test")

        # At t=0.5, ease_out(0.5) = 0.75
        Action.update_all(0.5)
        expected_factor = easing.ease_out(0.5)
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_easing_with_different_actions(self):
        """Test Easing wrapper with different action types."""
        sprite = create_test_sprite()

        # Test with RotateUntil
        rotate = RotateUntil(90, lambda: False)
        eased_rotate = Easing(rotate, seconds=1.0)
        eased_rotate.apply(sprite, tag="rotate")

        Action.update_all(0.5)
        expected_factor = easing.ease_in_out(0.5)
        expected_angular_velocity = 90.0 * expected_factor
        assert abs(sprite.change_angle - expected_angular_velocity) < 0.1

        Action.clear_all()
        sprite.change_angle = 0

        # Test with FadeUntil
        fade = FadeUntil(-100, lambda: False)
        eased_fade = Easing(fade, seconds=1.0)
        eased_fade.apply(sprite, tag="fade")

        Action.update_all(0.5)
        # Fade doesn't set sprite properties directly in apply_effect,
        # so we test the action's internal state
        expected_factor = easing.ease_in_out(0.5)
        expected_fade_velocity = -100.0 * expected_factor
        assert abs(fade.current_fade_velocity - expected_fade_velocity) < 0.1

    def test_easing_completion_callback(self):
        """Test Easing completion callback."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        callback_called = False

        def on_complete():
            nonlocal callback_called
            callback_called = True

        easing_action = Easing(move, seconds=1.0, on_complete=on_complete)
        easing_action.apply(sprite, tag="test")

        # Complete the easing
        Action.update_all(1.0)

        assert easing_action.done
        assert callback_called

    def test_easing_stop(self):
        """Test Easing stop method stops both wrapper and wrapped action."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite, tag="test")

        # Both actions should be active
        assert len(Action._active_actions) == 2

        # Stop the easing
        easing_action.stop()

        # Both actions should be stopped
        assert move.done
        assert easing_action.done
        assert len(Action._active_actions) == 0

    def test_easing_nested_factors(self):
        """Test Easing can forward set_factor calls for nesting."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite, tag="test")

        # Set factor on the easing wrapper
        easing_action.set_factor(0.5)

        # Should forward to wrapped action
        assert move.current_velocity == (50.0, 0.0)
        assert sprite.change_x == 50.0

    def test_easing_clone(self):
        """Test Easing clone functionality."""
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=2.0, ease_function=easing.ease_in)

        cloned = easing_action.clone()

        assert cloned.easing_duration == 2.0
        assert cloned.ease_function == easing.ease_in
        assert cloned.wrapped_action is not move  # Should be a clone
        assert cloned.wrapped_action.target_velocity == (100, 0)

    def test_easing_repr(self):
        """Test Easing string representation."""
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)

        repr_str = repr(easing_action)
        assert "Easing(duration=2.0" in repr_str
        assert "ease_function=ease_in_out" in repr_str
        assert "wrapped=" in repr_str

    def test_easing_with_sprite_list(self):
        """Test Easing wrapper with sprite lists."""
        sprite_list = create_test_sprite_list()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite_list, tag="test")

        # At t=0.5, all sprites should have eased velocity
        Action.update_all(0.5)
        expected_factor = easing.ease_in_out(0.5)
        expected_velocity = 100.0 * expected_factor

        for sprite in sprite_list:
            assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_easing_after_completion(self):
        """Test wrapped action continues after easing completes."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)  # Never stops on its own
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite, tag="test")

        # Complete the easing
        Action.update_all(1.0)

        assert easing_action.done
        assert not move.done  # Wrapped action should still be running
        assert sprite.change_x == 100.0  # Should be at full velocity

        # Continue updating - wrapped action should keep running at full velocity
        Action.update_all(0.1)
        assert sprite.change_x == 100.0

    def test_easing_with_follow_path_until_rotation(self):
        """Test Easing wrapper with FollowPathUntil rotation functionality."""
        sprite = create_test_sprite()
        sprite.angle = 45  # Start with non-zero angle

        # Create path following action with rotation
        control_points = [(100, 100), (200, 200), (300, 100)]
        path_action = FollowPathUntil(control_points, 200, lambda: False, rotate_with_path=True, rotation_offset=-90)

        # Wrap with easing
        eased_path = Easing(path_action, seconds=1.0, ease_function=easing.ease_in_out)
        eased_path.apply(sprite, tag="test_eased_path_rotation")

        # At start, should have minimal movement and rotation
        Action.update_all(0.1)
        initial_angle = sprite.angle

        # At mid-point, should have significant movement and rotation
        Action.update_all(0.4)  # Total t=0.5

        # Sprite should be moving and rotating
        mid_angle = sprite.angle
        assert mid_angle != initial_angle  # Rotation should have changed

        # Complete the easing
        Action.update_all(0.5)  # Total t=1.0
        assert eased_path.done

        # Path action should continue at full velocity after easing
        assert not path_action.done
        assert path_action.current_velocity == 200.0

    def test_easing_multiple_concurrent_actions(self):
        """Test multiple concurrent eased actions on different sprites."""
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite3 = create_test_sprite()

        # Create different eased actions
        move1 = MoveUntil((100, 0), lambda: False)
        move2 = MoveUntil((0, 100), lambda: False)
        rotate3 = RotateUntil(180, lambda: False)

        eased1 = Easing(move1, seconds=1.0, ease_function=easing.ease_in)
        eased2 = Easing(move2, seconds=1.0, ease_function=easing.ease_out)
        eased3 = Easing(rotate3, seconds=1.0, ease_function=easing.ease_in_out)

        # Apply to different sprites with meaningful tags
        eased1.apply(sprite1, tag="move_ease_in")
        eased2.apply(sprite2, tag="move_ease_out")
        eased3.apply(sprite3, tag="rotate_ease_in_out")

        # Update at mid-point
        Action.update_all(0.5)

        # Verify different easing curves produce different results
        # ease_in(0.5) = 0.25, ease_out(0.5) = 0.75, ease_in_out(0.5) = 0.5
        assert abs(sprite1.change_x - 25.0) < 1.0  # ease_in slower start
        assert abs(sprite2.change_y - 75.0) < 1.0  # ease_out faster start
        assert abs(sprite3.change_angle - 90.0) < 1.0  # ease_in_out mid-speed

    def test_easing_with_zero_duration(self):
        """Test Easing with zero duration raises appropriate error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="seconds must be positive"):
            Easing(move, seconds=0.0)

    def test_easing_with_negative_duration(self):
        """Test Easing with negative duration raises appropriate error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="seconds must be positive"):
            Easing(move, seconds=-1.0)

    def test_easing_with_very_small_duration(self):
        """Test Easing with very small but positive duration."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=0.001)  # 1 millisecond
        easing_action.apply(sprite, tag="test_tiny_duration")

        # Should complete very quickly
        Action.update_all(0.001)
        assert easing_action.done
        assert sprite.change_x == 100.0  # Should reach full velocity

    def test_easing_with_custom_ease_function(self):
        """Test Easing with custom ease function."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        # Custom ease function that always returns 0.7
        def custom_ease(t):
            return 0.7

        easing_action = Easing(move, seconds=1.0, ease_function=custom_ease)
        easing_action.apply(sprite, tag="test_custom_ease")

        # At any point during easing, should have factor 0.7
        Action.update_all(0.3)
        assert abs(sprite.change_x - 70.0) < 0.1

        Action.update_all(0.4)
        assert abs(sprite.change_x - 70.0) < 0.1

    def test_easing_invalid_ease_function(self):
        """Test Easing behavior with ease function that returns invalid values."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        # Ease function that returns negative values
        def invalid_ease(t):
            return -0.5

        easing_action = Easing(move, seconds=1.0, ease_function=invalid_ease)
        easing_action.apply(sprite, tag="test_invalid_ease")

        # Should handle negative factors gracefully
        Action.update_all(0.5)
        assert sprite.change_x == -50.0  # Should accept negative factor

    def test_easing_rapid_completion_callback(self):
        """Test completion callback is called correctly for rapid easing."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        callback_count = 0

        def completion_callback():
            nonlocal callback_count
            callback_count += 1

        easing_action = Easing(move, seconds=0.1, on_complete=completion_callback)
        easing_action.apply(sprite, tag="test_rapid_completion")

        # Complete the easing in one large step
        Action.update_all(0.2)  # More than duration

        assert easing_action.done
        assert callback_count == 1  # Should only be called once

    def test_easing_nested_easing(self):
        """Test easing wrapped in another easing (nested easing)."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        # First level easing
        inner_easing = Easing(move, seconds=1.0, ease_function=easing.ease_in)

        # Second level easing
        outer_easing = Easing(inner_easing, seconds=2.0, ease_function=easing.ease_out)
        outer_easing.apply(sprite, tag="test_nested_easing")

        # Should forward set_factor calls through the chain
        Action.update_all(1.0)  # Half way through outer easing

        # Outer easing at t=0.5 with ease_out gives factor ~0.75
        # This factor is applied to inner easing, which applies it to move
        # The exact value depends on the compound easing effect
        assert sprite.change_x > 0  # Should have some movement
        assert not outer_easing.done  # Outer easing not complete

        # Complete outer easing
        Action.update_all(1.0)
        assert outer_easing.done

    def test_easing_stop_mid_execution(self):
        """Test stopping easing action mid-execution."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=2.0)
        easing_action.apply(sprite, tag="test_stop_mid_execution")

        # Start easing
        Action.update_all(0.5)  # Quarter way through
        assert not easing_action.done
        assert sprite.change_x > 0  # Should have some velocity

        # Stop the easing
        easing_action.stop()

        # Both should be stopped
        assert easing_action.done
        assert move.done
        assert len(Action.get_actions_for_target(sprite, "test_stop_mid_execution")) == 0

    def test_easing_with_complex_path_following(self):
        """Test easing with complex FollowPathUntil scenarios."""
        sprite = create_test_sprite()

        # Complex curved path
        control_points = [(100, 100), (150, 200), (250, 180), (300, 120), (350, 150), (400, 100)]

        path_action = FollowPathUntil(
            control_points,
            300,
            lambda: False,
            rotate_with_path=True,
            rotation_offset=45.0,  # Diagonal sprite artwork
        )

        # Apply easing with custom completion callback
        completion_called = False

        def on_easing_complete():
            nonlocal completion_called
            completion_called = True

        eased_path = Easing(path_action, seconds=2.0, ease_function=easing.ease_in_out, on_complete=on_easing_complete)
        eased_path.apply(sprite, tag="test_complex_path_easing")

        # Track position and angle changes during easing
        positions = []
        angles = []

        for i in range(20):  # 20 steps over 2 seconds
            Action.update_all(0.1)
            positions.append((sprite.center_x, sprite.center_y))
            angles.append(sprite.angle)

        # Should have moved along path with rotation
        assert len(set(positions)) > 1  # Position should change
        assert len(set(angles)) > 1  # Angle should change due to rotation

        # Easing should be complete
        assert eased_path.done
        assert completion_called

        # Path action should continue at full velocity
        assert not path_action.done
        assert path_action.current_velocity == 300.0


class TestSetFactorEdgeCases:
    """Test suite for set_factor edge cases and error conditions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_set_factor_before_apply(self):
        """Test set_factor works before action is applied."""
        action = MoveUntil((100, 0), lambda: False)

        # Should not raise error
        action.set_factor(0.5)
        assert action.current_velocity == (50.0, 0.0)

    def test_set_factor_after_done(self):
        """Test set_factor on completed action."""
        sprite = create_test_sprite()
        condition_met = False

        def condition():
            return condition_met

        action = MoveUntil((100, 0), condition)
        action.apply(sprite)

        # Complete the action
        condition_met = True
        Action.update_all(0.1)
        assert action.done

        # set_factor should still work but not apply to sprite
        action.set_factor(0.5)
        assert action.current_velocity == (50.0, 0.0)
        # Sprite velocity should be cleared (action is done)
        assert sprite.change_x == 0.0

    def test_blink_until_set_factor_edge_cases(self):
        """Test BlinkUntil set_factor edge cases."""
        sprite = create_test_sprite()
        action = BlinkUntil(1.0, lambda: False)
        action.apply(sprite)

        # Test very small positive factor
        action.set_factor(0.001)
        assert action.current_seconds_until_change == 1000.0

        # Test very large factor
        action.set_factor(1000.0)
        assert action.current_seconds_until_change == 0.001

    def test_base_action_set_factor_no_op(self):
        """Test base Action set_factor is a no-op."""
        from actions.base import Action

        action = Action()

        # Should not raise error
        action.set_factor(0.5)
        action.set_factor(-1.0)
        action.set_factor(1000.0)

    def test_scale_until_uniform_vs_tuple(self):
        """Test ScaleUntil set_factor with uniform vs tuple scale velocity."""
        sprite = create_test_sprite()

        # Test with uniform scale velocity
        action1 = ScaleUntil(0.5, lambda: False)
        action1.apply(sprite)
        action1.set_factor(0.5)
        assert action1.current_scale_velocity == (0.25, 0.25)

        Action.clear_all()

        # Test with tuple scale velocity
        action2 = ScaleUntil((0.5, 0.3), lambda: False)
        action2.apply(sprite)
        action2.set_factor(0.5)
        assert action2.current_scale_velocity == (0.25, 0.15)

    def test_move_until_boundary_with_factor(self):
        """Test MoveUntil boundary behavior preserves factor scaling."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((100, 0), lambda: False, bounds=bounds, boundary_behavior="bounce")
        action.apply(sprite)

        # Set factor before boundary hit
        action.set_factor(0.5)
        assert action.current_velocity == (50.0, 0.0)

        # Simulate boundary hit (this would normally happen in update_effect)
        action._check_boundaries(sprite)

        # After bounce, both target and current velocity should be reversed
        # and factor scaling should be maintained
        if action.target_velocity[0] < 0:  # If bounce occurred
            action.set_factor(0.5)  # Re-apply factor
            assert action.current_velocity[0] < 0  # Should be negative (bounced)
            assert abs(action.current_velocity[0]) == 50.0  # Should maintain factor scaling

    def test_easing_with_nan_ease_function(self):
        """Test Easing behavior with ease function that returns NaN."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        def nan_ease(t):
            return float("nan")

        easing_action = Easing(move, seconds=1.0, ease_function=nan_ease)
        easing_action.apply(sprite, tag="test_nan_ease")

        # Should handle NaN gracefully (behavior may vary by implementation)
        Action.update_all(0.5)
        # NaN factor should result in NaN velocity, but sprite should handle it
        assert math.isnan(sprite.change_x) or sprite.change_x == 0.0

    def test_easing_with_infinity_ease_function(self):
        """Test Easing behavior with ease function that returns infinity."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        def infinity_ease(t):
            return float("inf")

        easing_action = Easing(move, seconds=1.0, ease_function=infinity_ease)
        easing_action.apply(sprite, tag="test_infinity_ease")

        # Should handle infinity gracefully
        Action.update_all(0.5)
        # Infinity factor should result in infinity velocity
        assert math.isinf(sprite.change_x)

    def test_easing_exception_in_ease_function(self):
        """Test Easing behavior when ease function raises exception."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        def exception_ease(t):
            raise ValueError("Test exception in ease function")

        easing_action = Easing(move, seconds=1.0, ease_function=exception_ease)
        easing_action.apply(sprite, tag="test_exception_ease")

        # Should propagate exception
        with pytest.raises(ValueError, match="Test exception in ease function"):
            Action.update_all(0.5)

    def test_easing_with_none_ease_function(self):
        """Test Easing behavior with None ease function."""
        move = MoveUntil((100, 0), lambda: False)

        # Should raise error during update when trying to call None
        easing_action = Easing(move, seconds=1.0, ease_function=None)
        sprite = create_test_sprite()
        easing_action.apply(sprite, tag="test_none_ease")

        with pytest.raises(TypeError):
            Action.update_all(0.5)

    def test_easing_extremely_large_duration(self):
        """Test Easing with extremely large duration."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        # Very large duration
        easing_action = Easing(move, seconds=1e10)  # 10 billion seconds
        easing_action.apply(sprite, tag="test_large_duration")

        # After small update, should have very small progress
        Action.update_all(1.0)  # 1 second out of 10 billion

        # t = 1.0 / 1e10 = 1e-10, ease_in_out of very small value ≈ 0
        assert abs(sprite.change_x) < 1.0  # Should be very small

    def test_easing_multiple_stops(self):
        """Test calling stop multiple times on easing action."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite, tag="test_multiple_stops")

        # Stop multiple times - should not cause errors
        easing_action.stop()
        easing_action.stop()
        easing_action.stop()

        assert easing_action.done
        assert move.done

    def test_easing_completion_callback_exception(self):
        """Test easing behavior when completion callback raises exception."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)

        def error_callback():
            raise RuntimeError("Test callback error")

        easing_action = Easing(move, seconds=0.1, on_complete=error_callback)
        easing_action.apply(sprite, tag="test_callback_exception")

        # Should propagate callback exception
        with pytest.raises(RuntimeError, match="Test callback error"):
            Action.update_all(0.2)  # Complete the easing

    def test_easing_set_factor_extreme_values(self):
        """Test Easing set_factor with extreme values."""
        sprite = create_test_sprite()
        move = MoveUntil((100, 0), lambda: False)
        easing_action = Easing(move, seconds=1.0)
        easing_action.apply(sprite, tag="test_extreme_factors")

        # Test with extremely large factor
        easing_action.set_factor(1e6)
        assert move.current_velocity == (1e8, 0.0)  # 100 * 1e6

        # Test with extremely small factor
        easing_action.set_factor(1e-10)
        assert abs(move.current_velocity[0] - 1e-8) < 1e-15  # 100 * 1e-10

    def test_follow_path_until_rotation_with_easing_edge_cases(self):
        """Test FollowPathUntil rotation with easing edge cases."""
        sprite = create_test_sprite()

        # Path with sharp turns to test rotation handling
        control_points = [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)]

        path_action = FollowPathUntil(
            control_points,
            500,
            lambda: False,
            rotate_with_path=True,
            rotation_offset=720.0,  # Large offset
        )

        # Very fast easing
        eased_path = Easing(path_action, seconds=0.01)
        eased_path.apply(sprite, tag="test_rotation_edge_cases")

        # Should handle large rotation offsets
        Action.update_all(0.005)
        # Large offset (720°) plus movement direction should work
        assert sprite.angle is not None  # Should not crash

        # Complete quickly
        Action.update_all(0.01)
        assert eased_path.done
