"""Test suite for easing.py - Easing wrapper functionality."""

import math

import pytest
from arcade import easing

from actions import (
    Action,
    ease,
)
from actions.conditional import (
    BlinkUntil,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    duration,
)
from actions.easing import Ease
from tests.conftest import ActionTestBase
from tests.test_base import MockAction


class TestSetFactor(ActionTestBase):
    """Test suite for set_factor functionality on all conditional actions."""

    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "name": "move_until",
                "action_class": MoveUntil,
                "action_args": ((100, 50), lambda: False),
                "velocity_property": "current_velocity",
                "sprite_property": "change_x",
                "expected_values": {0.5: (50.0, 25.0), 0.0: (0.0, 0.0), 2.0: (200.0, 100.0), -1.0: (-100.0, -50.0)},
                "sprite_assertions": {
                    0.5: {"change_x": 50.0, "change_y": 25.0},
                    0.0: {"change_x": 0.0, "change_y": 0.0},
                    2.0: {"change_x": 200.0, "change_y": 100.0},
                    -1.0: {"change_x": -100.0, "change_y": -50.0},
                },
            },
            {
                "name": "rotate_until",
                "action_class": RotateUntil,
                "action_args": (90, lambda: False),
                "velocity_property": "current_angular_velocity",
                "sprite_property": "change_angle",
                "expected_values": {0.5: 45.0, 0.0: 0.0, 2.0: 180.0},
                "sprite_assertions": {
                    0.5: {"change_angle": 45.0},
                    0.0: {"change_angle": 0.0},
                    2.0: {"change_angle": 180.0},
                },
            },
            {
                "name": "scale_until",
                "action_class": ScaleUntil,
                "action_args": ((0.5, 0.3), lambda: False),
                "velocity_property": "current_scale_velocity",
                "sprite_property": None,  # Scale doesn't set sprite properties directly
                "expected_values": {0.5: (0.25, 0.15), 0.0: (0.0, 0.0), 2.0: (1.0, 0.6)},
                "sprite_assertions": {},
            },
            {
                "name": "fade_until",
                "action_class": FadeUntil,
                "action_args": (-100, lambda: False),
                "velocity_property": "current_fade_velocity",
                "sprite_property": None,  # Fade doesn't set sprite properties directly
                "expected_values": {0.5: -50.0, 0.0: 0.0, 2.0: -200.0},
                "sprite_assertions": {},
            },
            {
                "name": "blink_until",
                "action_class": BlinkUntil,
                "action_args": (1.0, lambda: False),
                "velocity_property": "current_seconds_until_change",
                "sprite_property": None,  # Blink doesn't set sprite properties directly
                "expected_values": {2.0: 0.5, 0.5: 2.0, 0.0: float("inf"), -1.0: float("inf")},
                "sprite_assertions": {},
            },
            {
                "name": "follow_path_until",
                "action_class": FollowPathUntil,
                "action_args": ([(100, 100), (200, 200), (300, 100)], 150, lambda: False),
                "velocity_property": "current_velocity",
                "sprite_property": None,  # Path doesn't set sprite properties directly
                "expected_values": {0.5: 75.0, 0.0: 0.0, 2.0: 300.0},
                "sprite_assertions": {},
            },
        ],
    )
    def test_set_factor_functionality(self, test_case, test_sprite):
        """Test set_factor functionality for all action types."""
        sprite = test_sprite
        action = test_case["action_class"](*test_case["action_args"])
        action.apply(sprite)

        # Test various factor values
        for factor, expected_value in test_case["expected_values"].items():
            action.set_factor(factor)
            actual_value = getattr(action, test_case["velocity_property"])

            if isinstance(expected_value, tuple):
                assert actual_value == expected_value
            else:
                assert actual_value == expected_value

            # Test sprite property assertions if they exist
            if test_case["sprite_property"] and factor in test_case["sprite_assertions"]:
                for prop, expected_val in test_case["sprite_assertions"][factor].items():
                    actual_val = getattr(sprite, prop)
                    assert abs(actual_val - expected_val) < 0.01

    def test_set_factor_with_sprite_list(self, test_sprite_list):
        """Test set_factor works with sprite lists."""
        sprite_list = test_sprite_list
        action = MoveUntil((100, 0), lambda: False)
        action.apply(sprite_list)

        action.set_factor(0.5)
        for sprite in sprite_list:
            # MoveUntil uses pixels per frame at 60 FPS semantics
            assert abs(sprite.change_x - 50.0) < 0.01
            assert sprite.change_y == 0.0


class TestEase(ActionTestBase):
    """Test suite for Ease wrapper - Smooth acceleration/deceleration for continuous actions."""

    def test_ease_initialization_for_continuous_actions(self, test_sprite):
        """Test Ease wrapper initialization for continuous movement actions."""
        # Ease wraps continuous actions like MoveUntil that run indefinitely
        continuous_move = MoveUntil((100, 0), lambda: False)  # Never stops on its own
        easing_wrapper = Ease(continuous_move, duration=2.0, ease_function=easing.ease_in_out)

        assert easing_wrapper.wrapped_action == continuous_move
        assert easing_wrapper.easing_duration == 2.0
        assert easing_wrapper.ease_function == easing.ease_in_out
        assert easing_wrapper._elapsed == 0.0
        assert not easing_wrapper._easing_complete

    def test_ease_invalid_duration(self, test_sprite):
        """Test Ease with invalid duration raises error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="duration must be positive"):
            Ease(move, duration=0.0)

        with pytest.raises(ValueError, match="duration must be positive"):
            Ease(move, duration=-1.0)

    def test_ease_apply(self, test_sprite):
        """Test Ease apply method applies both wrapper and wrapped action."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)

        ease_action.apply(sprite, tag="test")

        # Both actions should be in active list
        active_actions = Action._active_actions
        assert len(active_actions) == 2  # Ease wrapper + wrapped action
        assert ease_action in active_actions
        assert move in active_actions

    def test_ease_smooth_acceleration_for_missile_launch(self, test_sprite):
        """Test Ease for realistic missile launch - smooth acceleration to cruise speed."""
        sprite = test_sprite

        # Using the new ease() helper for clean API demonstration
        # Creates continuous movement and applies smooth acceleration
        missile_movement = MoveUntil((100, 0), lambda: False)  # Unbound continuous movement
        smooth_launch = ease(
            sprite, missile_movement, duration=1.0, ease_function=easing.ease_in_out, tag="missile_launch"
        )

        # At start, should have smooth acceleration from 0
        Action.update_all(0.0)
        assert sprite.change_x == 0.0

        # At t=0.25, should be accelerating smoothly
        Action.update_all(0.25)
        expected_factor = easing.ease_in_out(0.25)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

        # At t=0.5, should be at 50% of target velocity
        Action.update_all(0.25)
        expected_factor = easing.ease_in_out(0.5)
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

        # At t=1.0, should reach full cruise speed and easing completes
        Action.update_all(0.5)
        assert abs(sprite.change_x - 100.0) < 0.01
        assert smooth_launch.done

        # Missile continues at cruise speed after easing completes
        assert not missile_movement.done  # Underlying action continues

    def test_ease_execution_ease_in(self, test_sprite):
        """Test Ease execution with ease_in function."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0, ease_function=easing.ease_in)
        ease_action.apply(sprite, tag="test")

        # At t=0.5, ease_in(0.5) = 0.25
        Action.update_all(0.5)
        expected_factor = easing.ease_in(0.5)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_ease_execution_ease_out(self, test_sprite):
        """Test Ease execution with ease_out function."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0, ease_function=easing.ease_out)
        ease_action.apply(sprite, tag="test")

        # At t=0.5, ease_out(0.5) = 0.75
        Action.update_all(0.5)
        expected_factor = easing.ease_out(0.5)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        expected_velocity = 100.0 * expected_factor
        assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_ease_with_different_actions(self, test_sprite):
        """Test Easing wrapper with different action types."""
        sprite = test_sprite

        # Test with RotateUntil
        rotate = RotateUntil(90, lambda: False)
        eased_rotate = Ease(rotate, duration=1.0)
        eased_rotate.apply(sprite, tag="rotate")

        Action.update_all(0.5)
        expected_factor = easing.ease_in_out(0.5)
        # RotateUntil uses degrees per frame at 60 FPS semantics
        expected_angular_velocity = 90.0 * expected_factor
        assert abs(sprite.change_angle - expected_angular_velocity) < 0.1

        Action.stop_all()
        sprite.change_angle = 0

        # Test with FadeUntil
        fade = FadeUntil(-100, lambda: False)
        eased_fade = Ease(fade, duration=1.0)
        eased_fade.apply(sprite, tag="fade")

        Action.update_all(0.5)
        # Fade doesn't set sprite properties directly in apply_effect,
        # so we test the action's internal state
        expected_factor = easing.ease_in_out(0.5)
        expected_fade_velocity = -100.0 * expected_factor
        assert abs(fade.current_fade_velocity - expected_fade_velocity) < 0.1

    def test_ease_completion_callback(self, test_sprite):
        """Test Easing completion callback."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        callback_called = False

        def on_complete():
            nonlocal callback_called
            callback_called = True

        ease_action = Ease(move, duration=1.0, on_complete=on_complete)
        ease_action.apply(sprite, tag="test")

        # Complete the easing
        Action.update_all(1.0)

        assert ease_action.done
        assert callback_called

    def test_ease_stop(self, test_sprite):
        """Test Easing stop method stops both wrapper and wrapped action."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite, tag="test")

        # Both actions should be active
        assert len(Action._active_actions) == 2

        # Stop the easing
        ease_action.stop()

        # Both actions should be stopped
        assert move.done
        assert ease_action.done
        assert len(Action._active_actions) == 0

    def test_ease_nested_factors(self, test_sprite):
        """Test Easing can forward set_factor calls for nesting."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite, tag="test")

        # Set factor on the easing wrapper
        ease_action.set_factor(0.5)

        # Should forward to wrapped action
        assert move.current_velocity == (50.0, 0.0)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite.change_x - 50.0) < 0.01

    def test_ease_clone(self, test_sprite):
        """Test Easing clone functionality."""
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=2.0, ease_function=easing.ease_in)

        cloned = ease_action.clone()

        assert cloned.easing_duration == 2.0
        assert cloned.ease_function == easing.ease_in
        assert cloned.wrapped_action is not move  # Should be a clone
        assert cloned.wrapped_action.target_velocity == (100, 0)

    def test_ease_repr(self, test_sprite):
        """Test Easing string representation."""
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=2.0, ease_function=easing.ease_in_out)

        repr_str = repr(ease_action)
        assert "Ease(duration=2.0" in repr_str
        assert "ease_function=ease_in_out" in repr_str
        assert "wrapped=" in repr_str

    def test_ease_with_sprite_list(self, test_sprite_list):
        """Test Easing wrapper with sprite lists."""
        sprite_list = test_sprite_list
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite_list, tag="test")

        # At t=0.5, all sprites should have eased velocity
        Action.update_all(0.5)
        expected_factor = easing.ease_in_out(0.5)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        expected_velocity = 100.0 * expected_factor

        for sprite in sprite_list:
            assert abs(sprite.change_x - expected_velocity) < 0.1

    def test_ease_after_completion(self, test_sprite):
        """Test wrapped action continues after easing completes."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)  # Never stops on its own
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite, tag="test")

        # Complete the easing
        Action.update_all(1.0)

        assert ease_action.done
        assert not move.done  # Wrapped action should still be running
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite.change_x - 100.0) < 0.01  # Should be at full velocity

        # Continue updating - wrapped action should keep running at full velocity
        Action.update_all(0.1)
        assert abs(sprite.change_x - 100.0) < 0.01

    def test_ease_with_follow_path_until_rotation(self, test_sprite):
        """Test Easing wrapper with FollowPathUntil rotation functionality."""
        sprite = test_sprite
        sprite.angle = 45  # Start with non-zero angle

        # Create path following action with rotation
        control_points = [(100, 100), (200, 200), (300, 100)]
        path_action = FollowPathUntil(control_points, 200, lambda: False, rotate_with_path=True, rotation_offset=-90)

        # Wrap with easing
        eased_path = Ease(path_action, duration=1.0, ease_function=easing.ease_in_out)
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

    def test_ease_multiple_concurrent_actions(self, test_sprite):
        """Test multiple concurrent eased actions on different sprites."""
        sprite1 = test_sprite
        # Create additional sprites for comparison
        import arcade

        sprite2 = arcade.Sprite(":resources:images/items/star.png")
        sprite2.center_x = 0
        sprite2.center_y = 100  # Offset to avoid overlap
        sprite3 = arcade.Sprite(":resources:images/items/star.png")
        sprite3.center_x = 0
        sprite3.center_y = 200  # Offset to avoid overlap

        # Demonstrate different approaches: traditional and new helper API
        # Traditional approach for comparison
        move1 = MoveUntil((100, 0), lambda: False)
        eased1 = Ease(move1, duration=1.0, ease_function=easing.ease_in)
        eased1.apply(sprite1, tag="move_ease_in")

        # New helper API approach - more concise
        ease(
            sprite2,
            MoveUntil((0, 100), lambda: False),
            duration=1.0,
            ease_function=easing.ease_out,
            tag="move_ease_out",
        )
        ease(
            sprite3,
            RotateUntil(180, lambda: False),
            duration=1.0,
            ease_function=easing.ease_in_out,
            tag="rotate_ease_in_out",
        )

        # Update at mid-point
        Action.update_all(0.5)

        # Verify different easing curves produce different results
        # ease_in(0.5) = 0.25, ease_out(0.5) = 0.75, ease_in_out(0.5) = 0.5
        # All velocities use pixels/degrees per frame at 60 FPS semantics
        assert abs(sprite1.change_x - 25.0) < 1.0  # ease_in slower start
        assert abs(sprite2.change_y - 75.0) < 1.0  # ease_out faster start
        assert abs(sprite3.change_angle - 90.0) < 1.0  # ease_in_out mid-speed

    def test_ease_with_zero_duration(self, test_sprite):
        """Test Easing with zero duration raises appropriate error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="duration must be positive"):
            Ease(move, duration=0.0)

    def test_ease_with_negative_duration(self, test_sprite):
        """Test Easing with negative duration raises appropriate error."""
        move = MoveUntil((100, 0), lambda: False)

        with pytest.raises(ValueError, match="duration must be positive"):
            Ease(move, duration=-1.0)

    def test_ease_with_very_small_duration(self, test_sprite):
        """Test Easing with very small but positive duration."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=0.001)  # 1 millisecond
        ease_action.apply(sprite, tag="test_tiny_duration")

        # Should complete very quickly
        Action.update_all(0.001)
        assert ease_action.done
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite.change_x - 100.0) < 0.01  # Should reach full velocity

    def test_ease_with_custom_ease_function(self, test_sprite):
        """Test Easing with custom ease function."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        # Custom ease function that always returns 0.7
        def custom_ease(t):
            return 0.7

        ease_action = Ease(move, duration=1.0, ease_function=custom_ease)
        ease_action.apply(sprite, tag="test_custom_ease")

        # At any point during easing, should have factor 0.7
        Action.update_all(0.3)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite.change_x - 70.0) < 0.1

        Action.update_all(0.4)
        assert abs(sprite.change_x - 70.0) < 0.1

    def test_ease_invalid_ease_function(self, test_sprite):
        """Test Easing behavior with ease function that returns invalid values."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        # Ease function that returns negative values
        def invalid_ease(t):
            return -0.5

        ease_action = Ease(move, duration=1.0, ease_function=invalid_ease)
        ease_action.apply(sprite, tag="test_invalid_ease")

        # Should handle negative factors gracefully
        Action.update_all(0.5)
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite.change_x - (-50.0)) < 0.01  # Should accept negative factor

    def test_ease_rapid_completion_callback(self, test_sprite):
        """Test completion callback is called correctly for rapid easing."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        callback_count = 0

        def completion_callback():
            nonlocal callback_count
            callback_count += 1

        ease_action = Ease(move, duration=0.1, on_complete=completion_callback)
        ease_action.apply(sprite, tag="test_rapid_completion")

        # Complete the easing in one large step
        Action.update_all(0.2)  # More than duration

        assert ease_action.done
        assert callback_count == 1  # Should only be called once

    def test_ease_nested_easing(self, test_sprite):
        """Test easing wrapped in another easing (nested easing)."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        # First level easing
        inner_easing = Ease(move, duration=1.0, ease_function=easing.ease_in)

        # Second level easing
        outer_easing = Ease(inner_easing, duration=2.0, ease_function=easing.ease_out)
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

    def test_ease_stop_mid_execution(self, test_sprite):
        """Test stopping easing action mid-execution."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=2.0)
        ease_action.apply(sprite, tag="test_stop_mid_execution")

        # Start easing
        Action.update_all(0.5)  # Quarter way through
        assert not ease_action.done
        assert sprite.change_x > 0  # Should have some velocity

        # Stop the easing
        ease_action.stop()

        # Both should be stopped
        assert ease_action.done
        assert move.done
        assert len(Action.get_actions_for_target(sprite, "test_stop_mid_execution")) == 0

    def test_ease_with_complex_path_following(self, test_sprite):
        """Test easing with complex FollowPathUntil scenarios."""
        sprite = test_sprite

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

        def on_ease_complete():
            nonlocal completion_called
            completion_called = True

        eased_path = Ease(path_action, duration=2.0, ease_function=easing.ease_in_out, on_complete=on_ease_complete)
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


class TestSetFactorEdgeCases(ActionTestBase):
    """Test edge cases for set_factor, including no-op on base Action."""

    def test_base_action_set_factor_no_op(self, test_sprite):
        """Test base Action set_factor is a no-op."""
        action = MockAction(condition=lambda: False)

        # Should not raise error
        action.set_factor(0.5)
        action.set_factor(-1.0)
        action.set_factor(1000.0)

    def test_set_factor_before_apply(self, test_sprite):
        """Test set_factor works before action is applied."""
        action = MoveUntil((100, 0), lambda: False)

        # Should not raise error
        action.set_factor(0.5)
        assert action.current_velocity == (50.0, 0.0)

    def test_set_factor_after_done(self, test_sprite):
        """Test set_factor on completed action."""
        sprite = test_sprite
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

    def test_blink_until_set_factor_edge_cases(self, test_sprite):
        """Test BlinkUntil set_factor edge cases."""
        sprite = test_sprite
        action = BlinkUntil(1.0, lambda: False)
        action.apply(sprite)

        # Test very small positive factor
        action.set_factor(0.001)
        assert action.current_seconds_until_change == 1000.0

        # Test very large factor
        action.set_factor(1000.0)
        assert action.current_seconds_until_change == 0.001

    def test_scale_until_uniform_vs_tuple(self, test_sprite):
        """Test ScaleUntil set_factor with uniform vs tuple scale velocity."""
        sprite = test_sprite

        # Test with uniform scale velocity
        action1 = ScaleUntil(0.5, lambda: False)
        action1.apply(sprite)
        action1.set_factor(0.5)
        assert action1.current_scale_velocity == (0.25, 0.25)

        Action.stop_all()

        # Test with tuple scale velocity
        action2 = ScaleUntil((0.5, 0.3), lambda: False)
        action2.apply(sprite)
        action2.set_factor(0.5)
        assert action2.current_scale_velocity == (0.25, 0.15)

    def test_move_until_boundary_with_factor(self, test_sprite):
        """Test MoveUntil boundary behavior preserves factor scaling."""
        sprite = test_sprite
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

    def test_ease_with_nan_ease_function(self, test_sprite):
        """Test Easing behavior with ease function that returns NaN."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        def nan_ease(t):
            return float("nan")

        ease_action = Ease(move, duration=1.0, ease_function=nan_ease)
        ease_action.apply(sprite, tag="test_nan_ease")

        # Should handle NaN gracefully (behavior may vary by implementation)
        Action.update_all(0.5)
        # NaN factor should result in NaN velocity, but sprite should handle it
        assert math.isnan(sprite.change_x) or sprite.change_x == 0.0

    def test_ease_with_infinity_ease_function(self, test_sprite):
        """Test Easing behavior with ease function that returns infinity."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        def infinity_ease(t):
            return float("inf")

        ease_action = Ease(move, duration=1.0, ease_function=infinity_ease)
        ease_action.apply(sprite, tag="test_infinity_ease")

        # Should handle infinity gracefully
        Action.update_all(0.5)
        # Infinity factor should result in infinity velocity
        assert math.isinf(sprite.change_x)

    def test_ease_exception_in_ease_function(self, test_sprite):
        """Test Easing behavior when ease function raises exception."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        def exception_ease(t):
            raise ValueError("Test exception in ease function")

        ease_action = Ease(move, duration=1.0, ease_function=exception_ease)
        ease_action.apply(sprite, tag="test_exception_ease")

        # Should propagate exception
        with pytest.raises(ValueError, match="Test exception in ease function"):
            Action.update_all(0.5)

    def test_ease_with_none_ease_function(self, test_sprite):
        """Test Easing behavior with None ease function."""
        move = MoveUntil((100, 0), lambda: False)

        # Should use default easing function when None is provided
        ease_action = Ease(move, duration=1.0, ease_function=None)
        sprite = test_sprite
        ease_action.apply(sprite, tag="test_none_ease")

        # Should work normally with default easing function
        Action.update_all(0.5)
        # Should have some movement (default is ease_in_out)
        assert sprite.change_x > 0

    def test_ease_extremely_large_duration(self, test_sprite):
        """Test Easing with extremely large duration."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        # Very large duration
        ease_action = Ease(move, duration=1e10)  # 10 billion seconds
        ease_action.apply(sprite, tag="test_large_duration")

        # After small update, should have very small progress
        Action.update_all(1.0)  # 1 second out of 10 billion

        # t = 1.0 / 1e10 = 1e-10, ease_in_out of very small value ≈ 0
        assert abs(sprite.change_x) < 1.0  # Should be very small

    def test_ease_vs_tween_until_comparison(self, test_sprite):
        """Test demonstrating the key difference between Easing and TweenUntil."""
        sprite1 = test_sprite
        # Create a second sprite for comparison
        import arcade

        sprite2 = arcade.Sprite(":resources:images/items/star.png")
        sprite2.center_x = 0
        sprite2.center_y = 100  # Offset to avoid overlap
        sprite1.center_x = 0
        sprite2.center_x = 0

        # Easing: Smooth acceleration into continuous movement
        continuous_move = MoveUntil((100, 0), lambda: False)  # Never stops
        eased_move = Ease(continuous_move, duration=1.0, ease_function=easing.ease_out)
        eased_move.apply(sprite1, tag="eased_movement")

        # TweenUntil: Direct property animation from A to B
        from actions.conditional import TweenUntil

        direct_animation = TweenUntil(0, 100, "center_x", duration(1.0), ease_function=easing.ease_out)
        direct_animation.apply(sprite2, tag="direct_animation")

        # After 1 second, both should have similar positions
        Action.update_all(1.0)

        # But their behaviors are different:
        # - Easing completes but wrapped action continues (sprite1 keeps moving)
        # - TweenUntil completes and stops (sprite2 stops at target)
        assert eased_move.done  # Easing wrapper is done
        assert not continuous_move.done  # But wrapped action continues
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert abs(sprite1.change_x - 100.0) < 0.01  # Still has velocity

        assert direct_animation.done  # TweenUntil is done
        assert sprite2.center_x == 100  # At exact target position
        # Note: TweenUntil doesn't use velocity, it sets position directly

    def test_ease_multiple_stops(self, test_sprite):
        """Test calling stop multiple times on easing action."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite, tag="test_multiple_stops")

        # Stop multiple times - should not cause errors
        ease_action.stop()
        ease_action.stop()
        ease_action.stop()

        assert ease_action.done
        assert move.done

    def test_ease_completion_callback_exception(self, test_sprite):
        """Test easing behavior when completion callback raises exception."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)

        def error_callback():
            raise RuntimeError("Test callback error")

        ease_action = Ease(move, duration=0.1, on_complete=error_callback)
        ease_action.apply(sprite, tag="test_callback_exception")

        # Should propagate callback exception
        with pytest.raises(RuntimeError, match="Test callback error"):
            Action.update_all(0.2)  # Complete the easing

    def test_ease_set_factor_extreme_values(self, test_sprite):
        """Test Easing set_factor with extreme values."""
        sprite = test_sprite
        move = MoveUntil((100, 0), lambda: False)
        ease_action = Ease(move, duration=1.0)
        ease_action.apply(sprite, tag="test_extreme_factors")

        # Test with extremely large factor
        ease_action.set_factor(1e6)
        assert move.current_velocity == (1e8, 0.0)  # 100 * 1e6

        # Test with extremely small factor
        ease_action.set_factor(1e-10)
        assert abs(move.current_velocity[0] - 1e-8) < 1e-15  # 100 * 1e-10

    def test_follow_path_until_rotation_with_ease_edge_cases(self, test_sprite):
        """Test FollowPathUntil rotation with easing edge cases."""
        sprite = test_sprite

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
        eased_path = Ease(path_action, duration=0.01)
        eased_path.apply(sprite, tag="test_rotation_edge_cases")

        # Should handle large rotation offsets
        Action.update_all(0.005)
        # Large offset (720°) plus movement direction should work
        assert sprite.angle is not None  # Should not crash

        # Complete quickly
        Action.update_all(0.01)
        assert eased_path.done
