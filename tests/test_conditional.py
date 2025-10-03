"""Test suite for condition_actions.py - Conditional actions."""

import arcade
import pytest

from actions import (
    Action,
    blink_until,
    delay_until,
    duration,
    fade_until,
    follow_path_until,
    infinite,
    move_until,
    rotate_until,
    scale_until,
    tween_until,
)
from actions.conditional import CallbackUntil, MoveUntil
from tests.conftest import ActionTestBase


class TestMoveUntil(ActionTestBase):
    """Test suite for MoveUntil action."""

    def test_move_until_frame_based_semantics(self, test_sprite):
        """Test that MoveUntil uses pixels per frame at 60 FPS semantics."""
        sprite = test_sprite

        # 5 pixels per frame should move 5 pixels when sprite.update() is called
        action = move_until(sprite, velocity=(5, 0), condition=infinite, tag="test_frame_semantics")

        # Update action to apply velocity
        Action.update_all(0.016)
        assert sprite.change_x == 5  # Raw frame-based value

        # Move sprite using its velocity
        start_x = sprite.center_x
        sprite.update()  # Arcade applies change_x to position

        # Should have moved exactly 5 pixels
        distance_moved = sprite.center_x - start_x
        assert distance_moved == 5.0

    def test_move_until_callback(self, test_sprite):
        """Test MoveUntil with callback."""
        sprite = test_sprite
        callback_called = False
        callback_data = None

        def on_stop(data=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        def condition():
            return {"reason": "collision", "damage": 10}

        action = move_until(sprite, velocity=(100, 0), condition=condition, on_stop=on_stop, tag="test_callback")

        Action.update_all(0.016)

        assert callback_called
        assert callback_data == {"reason": "collision", "damage": 10}

    def test_move_until_sprite_list(self, test_sprite_list):
        """Test MoveUntil with SpriteList."""
        sprite_list = test_sprite_list

        action = move_until(sprite_list, velocity=(50, 25), condition=infinite, tag="test_sprite_list")

        Action.update_all(0.016)

        # Both sprites should have the same velocity
        for sprite in sprite_list:
            assert sprite.change_x == 50
            assert sprite.change_y == 25

    def test_move_until_set_current_velocity(self, test_sprite):
        """Test MoveUntil set_current_velocity method."""
        sprite = test_sprite
        action = move_until(sprite, velocity=(100, 0), condition=infinite, tag="test_set_velocity")

        # Initial velocity should be set
        Action.update_all(0.016)
        assert sprite.change_x == 100

        # Change velocity
        action.set_current_velocity((50, 25))
        assert sprite.change_x == 50
        assert sprite.change_y == 25

    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "name": "right_boundary",
                "start_pos": (50, 100),
                "velocity": (100, 0),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (200, 100),
                "expected_velocity": (0, 0),
                "description": "Test basic limit boundary behavior - sprite stops exactly at boundary",
            },
            {
                "name": "left_boundary",
                "start_pos": (150, 100),
                "velocity": (-100, 0),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (0, 100),
                "expected_velocity": (0, 0),
                "description": "Test limit boundary behavior when moving left",
            },
            {
                "name": "vertical_boundary",
                "start_pos": (100, 50),
                "velocity": (0, 100),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (100, 200),
                "expected_velocity": (0, 0),
                "description": "Test limit boundary behavior for vertical movement",
            },
            {
                "name": "diagonal_boundary",
                "start_pos": (50, 50),
                "velocity": (100, 100),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (200, 200),
                "expected_velocity": (0, 0),
                "description": "Test limit boundary behavior for diagonal movement",
            },
            {
                "name": "negative_bounds",
                "start_pos": (-50, 100),
                "velocity": (-10, 0),
                "bounds": (-100, 0, 100, 200),
                "expected_final_pos": (-100, 100),
                "expected_velocity": (0, 0),
                "description": "Test limit boundary behavior with negative bounds",
            },
            {
                "name": "multiple_axes",
                "start_pos": (199, 199),
                "velocity": (10, 10),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (200, 200),
                "expected_velocity": (0, 0),
                "description": "Test limit boundary behavior when hitting multiple boundaries",
            },
            {
                "name": "velocity_clearing",
                "start_pos": (50, 100),
                "velocity": (100, 50),
                "bounds": (0, 0, 200, 200),
                "expected_final_pos": (200, 200),
                "expected_velocity": (0, 0),
                "description": "Test that limit boundary properly clears velocity when stopping",
            },
        ],
    )
    def test_move_until_limit_boundaries(self, test_case, test_sprite):
        """Test limit boundary behavior for various directions and scenarios."""
        sprite = test_sprite
        sprite.center_x, sprite.center_y = test_case["start_pos"]

        action = move_until(
            sprite,
            velocity=test_case["velocity"],
            condition=infinite,
            bounds=test_case["bounds"],
            boundary_behavior="limit",
            tag=f"test_limit_{test_case['name']}",
        )

        # Apply velocity
        Action.update_all(0.016)

        # Move sprite and continue until boundary is hit
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Verify final position and velocity
        assert sprite.center_x == test_case["expected_final_pos"][0]
        assert sprite.center_y == test_case["expected_final_pos"][1]
        assert sprite.change_x == test_case["expected_velocity"][0]
        assert sprite.change_y == test_case["expected_velocity"][1]

    def test_move_until_limit_boundary_no_wiggling(self, test_sprite):
        """Test that limit boundary prevents wiggling across boundary."""
        sprite = test_sprite
        sprite.center_x = 199  # Very close to right boundary
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(10, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            tag="test_limit_no_wiggling",
        )

        Action.update_all(0.016)
        # For limit behavior, velocity should not be set if it would cross boundary
        assert sprite.change_x == 0
        assert sprite.center_x == 200  # Should be set to boundary

        # Try to move again - should stay at boundary
        Action.update_all(0.016)
        sprite.update()
        assert sprite.center_x == 200
        assert sprite.change_x == 0

    def test_move_until_limit_boundary_callback(self, test_sprite):
        """Test limit boundary behavior with callback."""
        sprite = test_sprite
        sprite.center_x = 50
        sprite.center_y = 100

        boundary_called = False
        boundary_sprite = None
        boundary_axis = None

        def on_boundary(sprite, axis, side):
            nonlocal boundary_called, boundary_sprite, boundary_axis
            boundary_called = True
            boundary_sprite = sprite
            boundary_axis = axis

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(100, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_boundary,
            tag="test_limit_callback",
        )

        Action.update_all(0.016)
        sprite.update()

        # Continue until boundary is hit
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Callback should have been called
        assert boundary_called
        assert boundary_sprite == sprite
        assert boundary_axis == "x"

    def test_move_until_limit_boundary_sprite_list(self, test_sprite_list):
        """Test limit boundary behavior with SpriteList."""
        sprite_list = test_sprite_list
        sprite_list[0].center_x = 50
        sprite_list[1].center_x = 150

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite_list,
            velocity=(100, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            tag="test_limit_sprite_list",
        )

        Action.update_all(0.016)
        assert sprite_list[0].change_x == 100
        # For limit behavior, velocity should not be set if it would cross boundary
        assert sprite_list[1].change_x == 0

        # Move sprites
        for sprite in sprite_list:
            sprite.update()

        # Continue until boundaries are hit
        for _ in range(10):
            for sprite in sprite_list:
                sprite.update()
            Action.update_all(0.016)

        # Both sprites should be stopped at boundaries
        assert sprite_list[0].center_x == 200
        assert sprite_list[1].center_x == 200
        assert sprite_list[0].change_x == 0
        assert sprite_list[1].change_x == 0

    def test_move_until_limit_boundary_already_at_boundary(self, test_sprite):
        """Test limit boundary behavior when sprite starts at boundary."""
        sprite = test_sprite
        sprite.center_x = 200  # Start at right boundary
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(10, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            tag="test_limit_at_boundary",
        )

        Action.update_all(0.016)
        # Should not set velocity since already at boundary
        assert sprite.change_x == 0

        # Try to move again
        Action.update_all(0.016)
        assert sprite.center_x == 200  # Should stay at boundary
        assert sprite.change_x == 0

    def test_move_until_limit_boundary_multiple_axes(self, test_sprite):
        """Test limit boundary behavior when hitting multiple boundaries."""
        sprite = test_sprite
        sprite.center_x = 199
        sprite.center_y = 199

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(10, 10),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            tag="test_limit_multiple_axes",
        )

        Action.update_all(0.016)
        sprite.update()

        # Should be stopped at both boundaries
        assert sprite.center_x == 200
        assert sprite.center_y == 200
        assert sprite.change_x == 0
        assert sprite.change_y == 0


class TestFollowPathUntil(ActionTestBase):
    """Test suite for FollowPathUntil action."""

    def test_follow_path_until_basic(self, test_sprite):
        """Test basic FollowPathUntil functionality."""
        sprite = test_sprite
        start_pos = sprite.position

        control_points = [(100, 100), (200, 200), (300, 100)]
        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = follow_path_until(
            sprite, control_points=control_points, velocity=100, condition=condition, tag="test_basic_path"
        )

        Action.update_all(0.016)

        # Sprite should start moving along the path
        assert sprite.position != start_pos

    def test_follow_path_until_completion(self, test_sprite):
        """Test FollowPathUntil completes when reaching end of path."""
        sprite = test_sprite
        control_points = [(100, 100), (200, 100)]  # Simple straight line

        action = follow_path_until(
            sprite, control_points=control_points, velocity=1000, condition=infinite, tag="test_path_completion"
        )  # High velocity

        # Update until path is complete
        for _ in range(100):
            Action.update_all(0.016)
            if action.done:
                break

        assert action.done

    def test_follow_path_until_requires_points(self, test_sprite):
        """Test FollowPathUntil requires at least 2 control points."""
        sprite = test_sprite
        with pytest.raises(ValueError):
            follow_path_until(sprite, control_points=[(100, 100)], velocity=100, condition=infinite)

    def test_follow_path_until_no_rotation_by_default(self, test_sprite):
        """Test FollowPathUntil doesn't rotate sprite by default."""
        sprite = test_sprite
        original_angle = sprite.angle

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite, control_points=control_points, velocity=100, condition=infinite, tag="test_no_rotation"
        )

        # Update several frames
        for _ in range(10):
            Action.update_all(0.016)

        # Sprite angle should not have changed
        assert sprite.angle == original_angle

    def test_follow_path_until_rotation_horizontal_path(self, test_sprite):
        """Test sprite rotation follows horizontal path correctly."""
        sprite = test_sprite
        sprite.angle = 45  # Start with non-zero angle

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            tag="test_horizontal_rotation",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing right (0 degrees)
        # Allow small tolerance for floating point math
        assert abs(sprite.angle) < 1.0

    def test_follow_path_until_rotation_vertical_path(self, test_sprite):
        """Test sprite rotation follows vertical path correctly."""
        sprite = test_sprite

        # Vertical path from bottom to top
        control_points = [(100, 100), (100, 200)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            tag="test_vertical_rotation",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing up (90 degrees)
        assert abs(sprite.angle - 90) < 1.0

    def test_follow_path_until_rotation_diagonal_path(self, test_sprite):
        """Test sprite rotation follows diagonal path correctly."""
        sprite = test_sprite

        # Diagonal path from bottom-left to top-right (45 degrees)
        control_points = [(100, 100), (200, 200)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            tag="test_diagonal_rotation",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing at 45 degrees
        assert abs(sprite.angle - 45) < 1.0

    def test_follow_path_until_rotation_with_offset(self, test_sprite):
        """Test sprite rotation with calibration offset."""
        sprite = test_sprite

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        # Use -90 offset (sprite artwork points up by default)
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            rotation_offset=-90,
            tag="test_rotation_offset",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing right but compensated for -90 offset
        # Expected angle: 0 (right direction) + (-90 offset) = -90
        assert abs(sprite.angle - (-90)) < 1.0

    def test_follow_path_until_rotation_offset_only_when_rotating(self, test_sprite):
        """Test rotation offset is only applied when rotate_with_path is True."""
        sprite = test_sprite
        original_angle = sprite.angle

        # Horizontal path with offset but rotation disabled
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=False,
            rotation_offset=-90,
            tag="test_no_rotation_with_offset",
        )

        # Update several frames
        for _ in range(10):
            Action.update_all(0.016)

        # Sprite angle should not have changed (rotation disabled)
        assert sprite.angle == original_angle

    def test_follow_path_until_rotation_curved_path(self, test_sprite):
        """Test sprite rotation follows curved path correctly."""
        sprite = test_sprite

        # Curved path - quadratic Bezier curve
        control_points = [(100, 100), (150, 200), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            tag="test_curved_rotation",
        )

        # Store initial angle after first update
        Action.update_all(0.016)
        Action.update_all(0.016)
        initial_angle = sprite.angle

        # Continue updating - angle should change as we follow the curve
        for _ in range(20):
            Action.update_all(0.016)

        # Angle should have changed as we follow the curve
        assert sprite.angle != initial_angle

    def test_follow_path_until_rotation_large_offset(self, test_sprite):
        """Test sprite rotation with large offset values."""
        sprite = test_sprite

        # Horizontal path with large offset
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            rotation_offset=450,
            tag="test_large_offset",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Large offset should work (450 degrees = 90 degrees normalized)
        # Expected: 0 (right direction) + 450 (offset) = 450 degrees
        assert abs(sprite.angle - 450) < 1.0

    def test_follow_path_until_rotation_negative_offset(self, test_sprite):
        """Test sprite rotation with negative offset values."""
        sprite = test_sprite

        # Vertical path with negative offset
        control_points = [(100, 100), (100, 200)]
        action = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            rotation_offset=-45,
            tag="test_negative_offset",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Expected: 90 (up direction) + (-45 offset) = 45 degrees
        assert abs(sprite.angle - 45) < 1.0


class TestRotateUntil(ActionTestBase):
    """Test suite for RotateUntil action."""

    def test_rotate_until_basic(self, test_sprite):
        """Test basic RotateUntil functionality."""
        sprite = test_sprite

        target_reached = False

        def condition():
            return target_reached

        action = rotate_until(sprite, angular_velocity=90, condition=condition, tag="test_basic")

        Action.update_all(0.016)

        # RotateUntil uses degrees per frame at 60 FPS semantics
        assert sprite.change_angle == 90

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done

    def test_rotate_until_frame_based_semantics(self, test_sprite):
        """Test that RotateUntil uses degrees per frame at 60 FPS semantics."""
        sprite = test_sprite

        # 3 degrees per frame should rotate 3 degrees when sprite.update() is called
        action = rotate_until(sprite, angular_velocity=3, condition=infinite, tag="test_frame_semantics")

        # Update action to apply angular velocity
        Action.update_all(0.016)
        assert sprite.change_angle == 3  # Raw frame-based value

        # Rotate sprite using its angular velocity
        start_angle = sprite.angle
        sprite.update()  # Arcade applies change_angle to angle

        # Should have rotated exactly 3 degrees
        angle_rotated = sprite.angle - start_angle
        assert angle_rotated == 3.0

    def test_rotate_until_angular_velocity_values(self, test_sprite):
        """Test that RotateUntil sets angular velocity values directly (degrees per frame at 60 FPS)."""
        sprite = test_sprite

        # Test various angular velocity values
        test_cases = [
            1,  # Should result in change_angle = 1.0
            2,  # Should result in change_angle = 2.0
            5,  # Should result in change_angle = 5.0
            -3,  # Should result in change_angle = -3.0
        ]

        for input_angular_velocity in test_cases:
            Action.stop_all()
            sprite.change_angle = 0

            action = rotate_until(
                sprite, angular_velocity=input_angular_velocity, condition=infinite, tag="test_velocity"
            )
            Action.update_all(0.016)

            assert sprite.change_angle == input_angular_velocity, f"Failed for input {input_angular_velocity}"


class TestScaleUntil(ActionTestBase):
    """Test suite for ScaleUntil action."""

    def test_scale_until_basic(self, test_sprite):
        """Test basic ScaleUntil functionality."""
        sprite = test_sprite
        start_scale = sprite.scale

        target_reached = False

        def condition():
            return target_reached

        action = scale_until(sprite, velocity=0.5, condition=condition, tag="test_basic")

        Action.update_all(0.016)

        # Should be scaling
        assert sprite.scale != start_scale

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestFadeUntil(ActionTestBase):
    """Test suite for FadeUntil action."""

    def test_fade_until_basic(self, test_sprite):
        """Test basic FadeUntil functionality."""
        sprite = test_sprite
        start_alpha = sprite.alpha

        target_reached = False

        def condition():
            return target_reached

        action = fade_until(sprite, velocity=-100, condition=condition, tag="test_basic")

        Action.update_all(0.016)

        # Should be fading
        assert sprite.alpha != start_alpha

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestBlinkUntil(ActionTestBase):
    """Test suite for BlinkUntil action."""

    def test_blink_until_basic(self, test_sprite):
        """Test basic BlinkUntil functionality."""
        sprite = test_sprite

        target_reached = False

        def condition():
            return target_reached

        action = blink_until(sprite, seconds_until_change=0.05, condition=condition, tag="test_basic")

        Action.update_all(0.016)

        # Update several times to trigger blinking
        for _ in range(10):
            Action.update_all(0.016)

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done

    def test_blink_until_visibility_callbacks(self, test_sprite):
        """Test BlinkUntil with on_blink_enter and on_blink_exit callbacks."""
        sprite = test_sprite
        sprite.visible = True  # Start visible

        enter_calls = []
        exit_calls = []

        def on_enter(sprite_arg):
            enter_calls.append(sprite_arg)

        def on_exit(sprite_arg):
            exit_calls.append(sprite_arg)

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=on_enter,
            on_blink_exit=on_exit,
            tag="test_callbacks",
        )

        # Initial state - sprite should be visible, no callbacks yet
        assert sprite.visible
        assert len(enter_calls) == 0
        assert len(exit_calls) == 0

        # Update enough to trigger first blink (to invisible)
        Action.update_all(0.06)  # More than 0.05 seconds

        # Should now be invisible and exit callback called
        assert not sprite.visible
        assert len(exit_calls) == 1
        assert exit_calls[0] == sprite
        assert len(enter_calls) == 0  # No enter call yet

        # Update enough to trigger second blink (back to visible)
        Action.update_all(0.06)  # More than 0.05 seconds again

        # Should now be visible and enter callback called
        assert sprite.visible
        assert len(enter_calls) == 1
        assert enter_calls[0] == sprite
        assert len(exit_calls) == 1  # Still only one exit call

    def test_blink_until_edge_triggered_callbacks(self, test_sprite):
        """Test that callbacks are edge-triggered (only fire on state changes)."""
        sprite = test_sprite
        sprite.visible = True

        callback_count = {"enter": 0, "exit": 0}

        def count_enter(sprite_arg):
            callback_count["enter"] += 1

        def count_exit(sprite_arg):
            callback_count["exit"] += 1

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=count_enter,
            on_blink_exit=count_exit,
            tag="test_edge_triggered",
        )

        # Multiple updates within the same blink period - no callbacks yet
        for _ in range(3):
            Action.update_all(0.01)  # Less than 0.05 threshold

        assert callback_count["enter"] == 0
        assert callback_count["exit"] == 0
        assert sprite.visible  # Still visible

        # Cross the threshold to invisible
        Action.update_all(0.03)  # Total now > 0.05

        assert callback_count["exit"] == 1  # One exit call
        assert callback_count["enter"] == 0
        assert not sprite.visible

        # Multiple updates while invisible - no additional callbacks
        for _ in range(3):
            Action.update_all(0.01)

        assert callback_count["exit"] == 1  # Still just one
        assert callback_count["enter"] == 0

        # Cross threshold back to visible
        Action.update_all(0.03)  # Total blink time > 0.05 again

        assert callback_count["exit"] == 1
        assert callback_count["enter"] == 1  # One enter call
        assert sprite.visible

    def test_blink_until_callback_exceptions_handled(self, test_sprite):
        """Test that callback exceptions are caught and don't break blinking."""
        sprite = test_sprite
        sprite.visible = True

        def failing_enter(sprite_arg):
            raise RuntimeError("Enter callback failed!")

        def failing_exit(sprite_arg):
            raise RuntimeError("Exit callback failed!")

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=failing_enter,
            on_blink_exit=failing_exit,
            tag="test_exception_handling",
        )

        # Should not crash despite callback exceptions
        Action.update_all(0.06)  # Trigger first transition (to invisible)
        assert not sprite.visible

        Action.update_all(0.06)  # Trigger second transition (to visible)
        assert sprite.visible

        # Blinking should continue to work normally
        Action.update_all(0.06)  # Trigger third transition (to invisible)
        assert not sprite.visible

    def test_blink_until_no_callbacks(self, test_sprite):
        """Test BlinkUntil works normally without callbacks (backward compatibility)."""
        sprite = test_sprite
        sprite.visible = True

        action = blink_until(sprite, seconds_until_change=0.05, condition=infinite, tag="test_no_callbacks")

        # Should work normally without callbacks
        Action.update_all(0.06)
        assert not sprite.visible

        Action.update_all(0.06)
        assert sprite.visible

    def test_blink_until_only_enter_callback(self, test_sprite):
        """Test BlinkUntil with only on_blink_enter callback."""
        sprite = test_sprite
        sprite.visible = True

        enter_calls = []

        def on_enter(sprite_arg):
            enter_calls.append(sprite_arg)

        action = blink_until(
            sprite, seconds_until_change=0.05, condition=infinite, on_blink_enter=on_enter, tag="test_only_enter"
        )

        # Go invisible (no callback)
        Action.update_all(0.06)
        assert not sprite.visible
        assert len(enter_calls) == 0

        # Go visible (enter callback)
        Action.update_all(0.06)
        assert sprite.visible
        assert len(enter_calls) == 1

    def test_blink_until_only_exit_callback(self, test_sprite):
        """Test BlinkUntil with only on_blink_exit callback."""
        sprite = test_sprite
        sprite.visible = True

        exit_calls = []

        def on_exit(sprite_arg):
            exit_calls.append(sprite_arg)

        action = blink_until(
            sprite, seconds_until_change=0.05, condition=infinite, on_blink_exit=on_exit, tag="test_only_exit"
        )

        # Go invisible (exit callback)
        Action.update_all(0.06)
        assert not sprite.visible
        assert len(exit_calls) == 1

        # Go visible (no callback)
        Action.update_all(0.06)
        assert sprite.visible
        assert len(exit_calls) == 1  # Still just one

    def test_blink_until_sprite_list_callbacks(self, test_sprite_list):
        """Test BlinkUntil callbacks work with sprite lists."""
        sprite_list = test_sprite_list
        for sprite in sprite_list:
            sprite.visible = True

        callback_calls = {"enter": [], "exit": []}

        def track_enter(target_arg):
            callback_calls["enter"].append(target_arg)

        def track_exit(target_arg):
            callback_calls["exit"].append(target_arg)

        action = blink_until(
            sprite_list,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=track_enter,
            on_blink_exit=track_exit,
            tag="test_sprite_list_callbacks",
        )

        # Trigger first blink (all go invisible)
        Action.update_all(0.06)

        for sprite in sprite_list:
            assert not sprite.visible
        # Callback should receive the SpriteList once, not individual sprites
        assert len(callback_calls["exit"]) == 1
        assert callback_calls["exit"][0] is sprite_list
        assert len(callback_calls["enter"]) == 0

        # Trigger second blink (all go visible)
        Action.update_all(0.06)

        for sprite in sprite_list:
            assert sprite.visible
        # Callback should receive the SpriteList once
        assert len(callback_calls["enter"]) == 1
        assert callback_calls["enter"][0] is sprite_list

    def test_blink_until_starts_invisible_callbacks(self, test_sprite):
        """Test callbacks when sprite starts invisible."""
        sprite = test_sprite
        sprite.visible = False  # Start invisible

        enter_calls = []
        exit_calls = []

        def on_enter(sprite_arg):
            enter_calls.append(sprite_arg)

        def on_exit(sprite_arg):
            exit_calls.append(sprite_arg)

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=on_enter,
            on_blink_exit=on_exit,
            tag="test_starts_invisible",
        )

        # Initial state - sprite invisible, no callbacks yet
        assert not sprite.visible
        assert len(enter_calls) == 0
        assert len(exit_calls) == 0

        # First blink should make it visible (enter callback)
        Action.update_all(0.06)

        assert sprite.visible
        assert len(enter_calls) == 1
        assert len(exit_calls) == 0

        # Second blink should make it invisible (exit callback)
        Action.update_all(0.06)

        assert not sprite.visible
        assert len(enter_calls) == 1
        assert len(exit_calls) == 1


class TestDelayUntil(ActionTestBase):
    """Test suite for DelayUntil action."""

    def test_delay_until_basic(self, test_sprite):
        """Test basic DelayUntil functionality."""
        sprite = test_sprite

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = delay_until(sprite, condition=condition, tag="test_basic")

        Action.update_all(0.016)
        assert not action.done

        # Trigger condition
        condition_met = True
        Action.update_all(0.016)
        assert action.done


class TestDuration:
    """Test suite for duration helper."""

    def test_duration_basic(self):
        """Test basic duration functionality."""
        condition = duration(1.0)

        # Should return False initially
        assert not condition()

        # Should return True after duration passes
        # This is a simplified test - in practice would need to simulate time passage

    def test_duration_zero(self):
        """Test duration with zero duration."""
        condition = duration(0.0)

        # Should return True immediately
        assert condition()

    def test_duration_negative(self):
        """Test duration with negative duration."""
        condition = duration(-1.0)

        # Should return True immediately for negative durations
        assert condition()


class TestTweenUntil(ActionTestBase):
    """Test suite for TweenUntil action - Direct property animation from start to end value."""

    def test_tween_until_basic_property_animation(self, test_sprite):
        """Test TweenUntil for precise A-to-B property animation."""
        sprite = test_sprite
        sprite.center_x = 0

        # Direct property animation from 0 to 100 over 1 second
        action = tween_until(
            sprite, start_value=0, end_value=100, property_name="center_x", condition=duration(1.0), tag="test_basic"
        )

        # At halfway point, should be partway through
        Action.update_all(0.5)
        assert 0 < sprite.center_x < 100

        # At completion, should be exactly at end value and done
        Action.update_all(0.5)
        assert sprite.center_x == 100
        assert action.done

    def test_tween_until_custom_easing(self, test_sprite):
        sprite = test_sprite
        sprite.center_x = 0

        def ease_quad(t):
            return t * t

        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(1.0),
            ease_function=ease_quad,
            tag="test_custom_easing",
        )
        Action.update_all(0.5)
        # Should be less than linear at t=0.5
        assert sprite.center_x < 50
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_tween_until_ui_and_effect_animations(self, test_sprite):
        """Test TweenUntil for typical UI and visual effect use cases."""
        sprite = test_sprite

        # Button rotation feedback animation
        sprite.angle = 0
        rotation_feedback = tween_until(
            sprite, start_value=0, end_value=90, property_name="angle", condition=duration(1.0), tag="test_ui_animation"
        )
        Action.update_all(1.0)
        assert sprite.angle == 90

        # Fade-in effect animation
        sprite.alpha = 0
        fade_in = tween_until(
            sprite, start_value=0, end_value=255, property_name="alpha", condition=duration(1.0), tag="test_fade_in"
        )
        Action.update_all(1.0)
        assert sprite.alpha == 255

    def test_tween_until_sprite_list(self, test_sprite_list):
        sprites = test_sprite_list
        for s in sprites:
            s.center_x = 0
        action = tween_until(
            sprites,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(1.0),
            tag="test_sprite_list",
        )
        Action.update_all(1.0)
        for s in sprites:
            assert s.center_x == 100

    def test_tween_until_set_factor(self, test_sprite):
        sprite = test_sprite
        sprite.center_x = 0
        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(1.0),
            tag="test_set_factor",
        )
        action.set_factor(0.0)  # Pause
        Action.update_all(0.5)
        assert sprite.center_x == 0
        action.set_factor(1.0)  # Resume
        Action.update_all(1.0)
        assert sprite.center_x == 100
        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(1.0),
            tag="test_set_factor_again",
        )
        action.set_factor(2.0)  # Double speed
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_tween_until_completion_and_callback(self, test_sprite):
        sprite = test_sprite
        sprite.center_x = 0
        called = {}

        def on_complete(data=None):
            called["done"] = True

        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(1.0),
            on_stop=on_complete,
            tag="test_on_complete",
        )

        # At halfway point, should be partway through
        Action.update_all(0.5)
        assert not called

        # At completion, should be exactly at end value and callback called
        Action.update_all(0.5)
        assert sprite.center_x == 100
        assert called["done"]

    def test_tween_until_invalid_property(self, test_sprite):
        """Test TweenUntil behavior with invalid property names."""
        sprite = test_sprite

        # Arcade sprites are permissive and allow setting arbitrary attributes
        # so this test demonstrates that TweenUntil can work with any property name
        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="custom_property",
            condition=duration(1.0),
            tag="test_invalid_property",
        )
        Action.update_all(1.0)

        # The sprite should now have the custom property set to the end value
        assert sprite.custom_property == 100
        assert action.done

    def test_tween_until_negative_duration(self, test_sprite):
        sprite = test_sprite
        with pytest.raises(ValueError):
            action = tween_until(
                sprite,
                start_value=0,
                end_value=100,
                property_name="center_x",
                condition=duration(-1.0),
                tag="test_negative_duration",
            )

    def test_tween_until_vs_ease_comparison(self, test_sprite):
        """Test demonstrating when to use TweenUntil vs Ease."""
        sprite1 = test_sprite
        # Create a second sprite for comparison
        import arcade

        sprite2 = arcade.Sprite(":resources:images/items/star.png")
        sprite2.center_x = 0
        sprite2.center_y = 100  # Offset to avoid overlap
        sprite1.center_x = 0

        # TweenUntil: Perfect for UI panel slide-in (precise A-to-B movement)
        ui_slide = tween_until(
            sprite1,
            start_value=0,
            end_value=200,
            property_name="center_x",
            condition=duration(1.0),
            tag="test_ui_animation",
        )

        # Ease: Perfect for missile launch (smooth acceleration to cruise speed)
        from actions.easing import Ease

        missile_move = move_until(sprite2, velocity=(200, 0), condition=infinite, tag="test_missile_move")
        missile_launch = Ease(missile_move, duration=1.0)
        missile_launch.apply(sprite2, tag="test_missile_launch")

        # After 1 second:
        Action.update_all(1.0)

        # UI panel: Precisely positioned and stopped
        assert ui_slide.done
        assert sprite1.center_x == 200  # Exact target position
        assert sprite1.change_x == 0  # No velocity (not moving)

        # Missile: Reached cruise speed and continues moving
        assert missile_launch.done  # Easing is done
        assert not missile_move.done  # But missile keeps flying
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert sprite2.change_x == 200  # At cruise velocity

        # Key difference: TweenUntil stops, Ease transitions to continuous action

    def test_tween_until_start_equals_end(self, test_sprite):
        sprite = test_sprite
        sprite.center_x = 42
        action = tween_until(
            sprite,
            start_value=42,
            end_value=42,
            property_name="center_x",
            condition=duration(1.0),
            tag="test_start_equals_end",
        )
        Action.update_all(1.0)
        assert sprite.center_x == 42
        assert action.done

    def test_tween_until_zero_duration(self, test_sprite):
        sprite = test_sprite
        sprite.center_x = 0
        action = tween_until(
            sprite,
            start_value=0,
            end_value=100,
            property_name="center_x",
            condition=duration(0.0),
            tag="test_zero_duration",
        )
        assert sprite.center_x == 100
        assert action.done


# ------------------ Repeat wallclock drift tests ------------------


def test_repeat_with_wallclock_drift_no_jump():
    """Test that _Repeat + ParametricMotionUntil does not produce position jumps when
    wall-clock time (used by duration()) diverges from simulation delta_time.
    """
    import sys

    import arcade

    from actions import Action, repeat
    from actions.pattern import create_wave_pattern

    def _run_frames(frames: int) -> None:
        for _ in range(frames):
            Action.update_all(1 / 60)

    # Save and monkeypatch time.time used by duration()
    import time as real_time_module

    original_time_fn = real_time_module.time

    # Controlled simulated wall clock
    sim_time = {"t": original_time_fn()}

    def fake_time():
        return sim_time["t"]

    # Monkeypatch the time module globally
    sys.modules["time"].time = fake_time

    try:
        # Setup sprite and repeating full-wave action
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
        rep = repeat(full_wave)
        rep.apply(sprite, tag="repeat_wallclock")

        last_pos = (sprite.center_x, sprite.center_y)
        # Run ~10 seconds, injecting wall-clock drift every 2 seconds
        for frame in range(10 * 60):
            # Advance simulated wall clock normally
            sim_time["t"] += 1 / 60
            # Every 120 frames (~2 s), inject 150 ms extra wall time to simulate hitches
            if frame and frame % 120 == 0:
                sim_time["t"] += 0.15

            Action.update_all(1 / 60)

            current = (sprite.center_x, sprite.center_y)
            # Detect sudden large position jumps within one frame
            dx = current[0] - last_pos[0]
            dy = current[1] - last_pos[1]
            step_dist = (dx * dx + dy * dy) ** 0.5
            # Allow generous per-frame distance for wave motion; disallow implausible jumps
            assert step_dist < 30.0, f"Unexpected jump {step_dist:.2f} at frame {frame}"
            last_pos = current

    finally:
        # Restore real time.time
        sys.modules["time"].time = original_time_fn


class TestMoveUntilExceptionHandling(ActionTestBase):
    """Test suite for MoveUntil exception handling and edge cases."""

    def test_velocity_provider_exception_fallback(self, test_sprite):
        """Test that velocity provider exceptions fall back to current velocity."""
        sprite = test_sprite

        def failing_provider():
            raise RuntimeError("Provider failed!")

        action = move_until(
            sprite,
            velocity=(10, 5),
            condition=infinite,
            velocity_provider=failing_provider,
            tag="test_provider_exception",
        )

        # Should fall back to current velocity (10, 5) when provider fails
        Action.update_all(0.016)
        assert sprite.change_x == 10
        assert sprite.change_y == 5

    def test_boundary_enter_callback_exception_handling(self, test_sprite):
        """Test that boundary enter callback exceptions are caught and ignored."""
        sprite = test_sprite
        sprite.center_x = 50
        sprite.center_y = 100

        def failing_callback(sprite, axis, side):
            raise RuntimeError("Callback failed!")

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(100, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=failing_callback,
            tag="test_callback_exception",
        )

        # Should not crash despite callback exception
        Action.update_all(0.016)
        sprite.update()

        # Continue until boundary is hit - should handle exception gracefully
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should reach boundary despite callback failure
        assert sprite.center_x == 200

    def test_boundary_exit_callback_exception_handling(self, test_sprite):
        """Test that boundary exit callback exceptions are caught and ignored."""
        sprite = test_sprite
        sprite.center_x = 200  # Start at boundary
        sprite.center_y = 100

        def failing_exit_callback(sprite, axis, side):
            raise RuntimeError("Exit callback failed!")

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(-10, 0),  # Move away from boundary
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_exit=failing_exit_callback,
            tag="test_exit_callback_exception",
        )

        # Should not crash despite callback exception
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.016)

        # Should be able to move away despite callback failure
        assert sprite.center_x < 200

    def test_wrap_boundary_behavior(self, test_sprite):
        """Test wrap boundary behavior coverage."""
        sprite = test_sprite
        sprite.center_x = 190
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(20, 0),  # Will cross right boundary
            condition=infinite,
            bounds=bounds,
            boundary_behavior="wrap",
            tag="test_wrap_boundary",
        )

        # Move multiple frames to ensure wrapping occurs
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Should wrap to left side - check that it wrapped around
        assert sprite.center_x != 190  # Position changed
        # Wrap behavior should set sprite to opposite boundary when crossing
        assert sprite.center_x <= 200  # Within bounds

    def test_bounce_boundary_behavior(self, test_sprite):
        """Test bounce boundary behavior coverage."""
        sprite = test_sprite
        sprite.center_x = 190
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite,
            velocity=(20, 0),  # Will hit right boundary
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",
            tag="test_bounce_boundary",
        )

        # Move multiple frames to ensure bouncing occurs
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Should bounce back with reversed velocity - check that velocity changed direction
        assert sprite.center_x != 190  # Position changed
        # After bouncing, sprite should be moving in opposite direction or stopped
        assert sprite.change_x <= 0  # Velocity should be zero or negative after bounce


class TestConditionalErrorCases:
    """Test error cases and edge conditions in conditional actions."""

    def test_move_until_invalid_velocity_not_tuple(self, test_sprite):
        """Test MoveUntil with invalid velocity type raises error."""
        with pytest.raises(ValueError, match="velocity must be a tuple or list of length 2"):
            move_until(test_sprite, velocity="invalid", condition=infinite)

    def test_move_until_invalid_velocity_wrong_length(self, test_sprite):
        """Test MoveUntil with wrong velocity length raises error."""
        with pytest.raises(ValueError, match="velocity must be a tuple or list of length 2"):
            move_until(test_sprite, velocity=(1,), condition=infinite)

    def test_move_until_invalid_velocity_too_long(self, test_sprite):
        """Test MoveUntil with too long velocity raises error."""
        with pytest.raises(ValueError, match="velocity must be a tuple or list of length 2"):
            move_until(test_sprite, velocity=(1, 2, 3), condition=infinite)

    def test_duration_with_invalid_seconds(self):
        """Test duration with invalid seconds parameter."""
        # Test with None - this should raise TypeError when called
        cond = duration(None)
        with pytest.raises(TypeError):
            cond()

    def test_duration_with_callable_seconds(self):
        """Test duration with callable seconds parameter."""

        def get_seconds():
            return 0.1

        cond = duration(get_seconds)
        # Should work with callable
        assert callable(cond)

    def test_conditional_action_exception_handling(self, test_sprite):
        """Test conditional action with exception during duration parsing."""

        # Create a mock object that raises exceptions when accessed
        class BadDuration:
            def __getitem__(self, key):
                raise TypeError("Bad duration")

            def __len__(self):
                raise IndexError("Bad length")

        # This should not crash, just fall back to default duration
        action = move_until(test_sprite, velocity=(10, 0), condition=duration(BadDuration()))
        assert action is not None

    def test_duration_condition_closure_detection(self, test_sprite):
        """Test duration condition closure detection coverage."""
        sprite = test_sprite

        # Test with a closure that contains seconds variable
        seconds = 0.1

        def make_condition():
            return duration(seconds)

        cond = make_condition()
        action = move_until(sprite, velocity=(10, 0), condition=cond)
        assert action is not None

        # Create a duration condition with closure
        condition = duration(2.0)

        action = move_until(sprite, velocity=(10, 0), condition=condition, tag="test_duration_closure")

        # Update to test the closure detection
        for _ in range(5):
            Action.update_all(0.016)

        assert sprite.change_x == 10

        # The action should detect the duration from the closure
        # This exercises the closure inspection code
        Action.update_all(0.016)
        assert sprite.change_x == 10

    def test_move_until_boundary_limit_with_events(self, test_sprite):
        """Test MoveUntil boundary limit behavior with enter/exit events."""
        sprite = test_sprite
        sprite.center_x = 180
        sprite.center_y = 150

        # Track boundary events
        boundary_enters = []
        boundary_exits = []

        def on_enter(sprite, axis, side):
            boundary_enters.append((sprite, axis, side))

        def on_exit(sprite, axis, side):
            boundary_exits.append((sprite, axis, side))

        action = move_until(
            sprite,
            velocity=(50, 0),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 200, 300),
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
            tag="test_boundary_events",
        )

        # Move sprite to trigger boundary
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Should have triggered boundary enter event
        assert len(boundary_enters) > 0
        assert boundary_enters[0][2] == "right"

        # Change direction to move away from boundary
        sprite.change_x = -50

        # Move away from boundary
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        # Should trigger boundary exit event
        assert len(boundary_exits) > 0
        assert boundary_exits[0][2] == "right"

    def test_move_until_boundary_vertical_limits(self, test_sprite):
        """Test MoveUntil boundary limit behavior for vertical movement."""
        sprite = test_sprite
        sprite.center_x = 100
        sprite.center_y = 280

        action = move_until(
            sprite,
            velocity=(0, 50),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 200, 300),
            tag="test_vertical_boundary",
        )

        # Move sprite to trigger top boundary
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Should be limited to boundary
        assert sprite.center_y <= 300
        assert sprite.change_y == 0  # Velocity should be stopped

    def test_move_until_boundary_initialization(self, test_sprite):
        """Test boundary state initialization for new sprites."""
        sprite = test_sprite
        sprite.center_x = 50
        sprite.center_y = 50

        action = move_until(
            sprite,
            velocity=(10, 10),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 200, 200),
            tag="test_boundary_init",
        )

        # Update once to initialize boundary state
        Action.update_all(0.016)

        # Boundary state should be initialized
        assert hasattr(action, "_boundary_state")
        sprite_id = id(sprite)
        assert sprite_id in action._boundary_state
        assert "x" in action._boundary_state[sprite_id]
        assert "y" in action._boundary_state[sprite_id]

    def test_move_until_exception_in_boundary_callback(self, test_sprite):
        """Test handling of exceptions in boundary callbacks."""
        sprite = test_sprite
        sprite.center_x = 180
        sprite.center_y = 150

        def bad_callback(sprite, side):
            raise RuntimeError("Test exception")

        action = move_until(
            sprite,
            velocity=(50, 0),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 200, 300),
            on_boundary_enter=bad_callback,
            tag="test_exception_handling",
        )

        # Should not crash even with exception in callback
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Sprite should still be properly limited
        assert sprite.center_x <= 200

    def test_move_until_with_sprite_list_boundary_mixed_states(self, test_sprite_list):
        """Test boundary behavior with sprite list where sprites are in different boundary states."""
        sprite_list = test_sprite_list
        sprite_list[0].center_x = 180  # Near right boundary
        sprite_list[1].center_x = 20  # Near left boundary
        sprite_list[0].center_y = 100
        sprite_list[1].center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite_list,
            velocity=(30, 0),  # Moving right
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",
            tag="test_mixed_boundary_states",
        )

        Action.update_all(0.016)
        sprite_list[0].update()
        sprite_list[1].update()

        # First sprite should hit boundary and stop
        assert sprite_list[0].change_x == 0
        assert sprite_list[0].center_x == 200

        # Second sprite should continue moving
        assert sprite_list[1].change_x == 30
        assert sprite_list[1].center_x >= 50  # Should have moved right


class TestConditionalAdditionalCoverage:
    """Additional tests to improve conditional.py coverage."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
        # Clear callback warning cache for clean tests
        Action._warned_bad_callbacks.clear()

    def test_duration_boundary_state_initialization(self):
        """Test boundary state initialization for different sprites."""
        from tests.test_base import create_test_sprite

        sprite1 = create_test_sprite()
        sprite1.center_x = 50
        sprite1.center_y = 50

        sprite2 = create_test_sprite()
        sprite2.center_x = 75
        sprite2.center_y = 75

        # Create MoveUntil actions for both sprites with boundary behavior
        move_until(
            sprite1,
            velocity=(10, 0),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
        )

        move_until(
            sprite2,
            velocity=(-10, 0),
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
        )

        # Both actions should be created successfully
        assert len(Action._active_actions) >= 2

    def test_move_until_boundary_enter_exception_handling(self):
        """Test that boundary enter callback exceptions are caught gracefully."""
        from tests.test_base import create_test_sprite

        sprite = create_test_sprite()
        sprite.center_x = 90  # Start close to right boundary
        sprite.center_y = 50

        def failing_boundary_callback(sprite, axis, side):
            """A callback that raises an exception."""
            raise ValueError("Test boundary exception")

        # Create MoveUntil with boundary limits and a failing callback
        move_until(
            sprite,
            velocity=(30, 0),  # Moving right
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
            on_boundary_enter=failing_boundary_callback,
        )

        # Update multiple times to ensure boundary collision
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Sprite should be stopped at boundary despite callback exception
        assert sprite.change_x == 0
        assert sprite.center_x == 100  # Should be at right boundary

    def test_move_until_boundary_exit_exception_handling(self):
        """Test that boundary exit callback exceptions are caught gracefully."""
        from tests.test_base import create_test_sprite

        sprite = create_test_sprite()
        sprite.center_x = 100  # Start at right boundary
        sprite.center_y = 50

        def failing_boundary_exit_callback(sprite, axis, side):
            """A callback that raises an exception."""
            raise ValueError("Test boundary exit exception")

        # Create MoveUntil with boundary limits and a failing exit callback
        move_until(
            sprite,
            velocity=(-50, 0),  # Moving left (away from right boundary)
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
            on_boundary_exit=failing_boundary_exit_callback,
        )

        # Update to trigger boundary exit - this should not crash
        # even though the callback raises an exception
        Action.update_all(0.016)
        sprite.update()

        # Sprite should continue moving despite callback exception
        assert sprite.change_x == -50
        assert sprite.center_x < 100  # Should have moved away from boundary

    def test_move_until_vertical_boundary_limits(self):
        """Test MoveUntil with vertical boundary limits (top/bottom)."""
        from tests.test_base import create_test_sprite

        sprite = create_test_sprite()
        sprite.center_x = 50
        sprite.center_y = 50

        boundary_events = []

        def track_boundary_enter(sprite, axis, side):
            boundary_events.append(f"enter_{axis}_{side}")

        # Test hitting top boundary
        move_until(
            sprite,
            velocity=(0, 60),  # Moving up
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
            on_boundary_enter=track_boundary_enter,
        )

        # Update until sprite hits top boundary
        Action.update_all(0.016)
        sprite.update()

        # Sprite should be stopped at top boundary
        assert sprite.change_y == 0
        assert sprite.center_y == 100  # Top boundary
        assert "enter_y_top" in boundary_events

        # Clear previous action and test bottom boundary
        Action.stop_all()
        boundary_events.clear()
        sprite.center_y = 50

        move_until(
            sprite,
            velocity=(0, -60),  # Moving down
            condition=infinite,
            boundary_behavior="limit",
            bounds=(0, 0, 100, 100),
            on_boundary_enter=track_boundary_enter,
        )

        # Update until sprite hits bottom boundary
        Action.update_all(0.016)
        sprite.update()

        # Sprite should be stopped at bottom boundary
        assert sprite.change_y == 0
        assert sprite.center_y == 0  # Bottom boundary
        assert "enter_y_bottom" in boundary_events


class TestCallbackSignatureWarnings:
    """Test callback signature mismatch warnings."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
        Action._warned_bad_callbacks.clear()

    def test_blink_until_bad_callback_signature_warnings(self, test_sprite, monkeypatch):
        """Test that BlinkUntil warns about bad callback signatures."""
        import warnings

        from actions import set_debug_options

        # Enable debug mode for warnings
        set_debug_options(level=1)

        sprite = test_sprite
        sprite.visible = True

        # Bad callbacks with wrong number of parameters
        def bad_enter():  # Missing sprite parameter
            pass

        def bad_exit():  # Missing sprite parameter
            pass

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")

            action = blink_until(
                sprite,
                seconds_until_change=0.05,
                condition=infinite,
                on_blink_enter=bad_enter,
                on_blink_exit=bad_exit,
                tag="test_bad_callbacks",
            )

            # Update multiple times to trigger blinking and callbacks
            for _ in range(10):
                Action.update_all(0.016)

            action.stop()

        # Should have exactly 2 warnings (one for each bad callback)
        warning_messages = [str(w.message) for w in caught_warnings if issubclass(w.category, RuntimeWarning)]
        assert len(warning_messages) == 2

        # Check warning content
        assert any("bad_enter" in msg and "TypeError" in msg for msg in warning_messages)
        assert any("bad_exit" in msg and "TypeError" in msg for msg in warning_messages)

    def test_move_until_bad_boundary_callback_warnings(self, test_sprite, monkeypatch):
        """Test that MoveUntil warns about bad boundary callback signatures."""
        import warnings

        from actions import set_debug_options

        # Enable debug mode for warnings
        set_debug_options(level=1)

        sprite = test_sprite
        sprite.center_x = 95  # Start closer to boundary
        sprite.center_y = 50

        # Bad callbacks with wrong signatures
        def bad_boundary_enter():  # Missing sprite, axis, side parameters
            pass

        def bad_boundary_exit():  # Missing sprite, axis, side parameters
            pass

        bounds = (0, 0, 100, 100)

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")

            # Test by directly calling _execute_callback_impl with the bad callback
            from actions.base import Action

            Action._execute_callback_impl(bad_boundary_enter, sprite, "x", "right")

        # Should have warnings for bad callbacks
        warning_messages = [str(w.message) for w in caught_warnings if issubclass(w.category, RuntimeWarning)]
        assert len(warning_messages) >= 1  # At least one warning

        # Check warning content
        assert any("bad_boundary" in msg and "TypeError" in msg for msg in warning_messages)

    def test_callback_warning_only_once_per_function(self, test_sprite, monkeypatch):
        """Test that warnings are only issued once per callback function."""
        import warnings

        from actions import set_debug_options

        # Enable debug mode for warnings
        set_debug_options(level=1)

        sprite = test_sprite
        sprite.visible = True

        def bad_callback():  # Missing sprite parameter
            pass

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")

            # Apply the same bad callback multiple times
            action1 = blink_until(
                sprite, seconds_until_change=0.05, condition=infinite, on_blink_enter=bad_callback, tag="test_once_1"
            )

            action2 = blink_until(
                sprite,
                seconds_until_change=0.05,
                condition=infinite,
                on_blink_enter=bad_callback,  # Same function, should not warn again
                tag="test_once_2",
            )

            # Update to trigger callbacks
            for _ in range(20):
                Action.update_all(0.016)

            action1.stop()
            action2.stop()

        # Should have exactly one warning despite multiple uses of the same function
        warning_messages = [str(w.message) for w in caught_warnings if issubclass(w.category, RuntimeWarning)]
        assert len(warning_messages) == 1
        assert "bad_callback" in warning_messages[0]
        assert "TypeError" in warning_messages[0]

    def test_no_warnings_without_debug_mode(self, test_sprite):
        """Test that no warnings are issued when debug level is 0."""
        import warnings

        from actions import set_debug_options

        # Ensure debug is off
        set_debug_options(level=0)

        sprite = test_sprite
        sprite.visible = True

        def bad_callback():  # Missing sprite parameter
            pass

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")

            action = blink_until(
                sprite, seconds_until_change=0.05, condition=infinite, on_blink_enter=bad_callback, tag="test_no_debug"
            )

            # Update to trigger callbacks
            for _ in range(10):
                Action.update_all(0.016)

            action.stop()

        # Should have no warnings when debug mode is off
        warning_messages = [str(w.message) for w in caught_warnings if issubclass(w.category, RuntimeWarning)]
        assert len(warning_messages) == 0


class TestBlinkUntilEfficiency:
    """Test BlinkUntil callback efficiency with SpriteList targets."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sprite_list_callbacks_called_once_not_n_times(self, test_sprite_list):
        """Test that SpriteList callbacks are called once per frame, not once per sprite."""
        sprites = test_sprite_list

        # Add more sprites to make the efficiency difference clear
        for i in range(47):  # test_sprite_list has 3 sprites, add 47 more for 50 total
            sprite = arcade.Sprite()
            sprite.visible = True
            sprites.append(sprite)

        for sprite in sprites:
            sprite.visible = True

        enter_call_count = 0
        exit_call_count = 0

        def count_enter(target):
            nonlocal enter_call_count
            enter_call_count += 1
            # Should receive the SpriteList, not individual sprites
            assert target is sprites
            assert len(target) == 50

        def count_exit(target):
            nonlocal exit_call_count
            exit_call_count += 1
            # Should receive the SpriteList, not individual sprites
            assert target is sprites
            assert len(target) == 50

        action = blink_until(
            sprites,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=count_enter,
            on_blink_exit=count_exit,
            tag="efficiency_test",
        )

        # First blink cycle: all sprites go invisible
        Action.update_all(0.06)

        # Verify all sprites changed
        for sprite in sprites:
            assert not sprite.visible

        # Verify callback was called exactly once, not 50 times
        assert exit_call_count == 1
        assert enter_call_count == 0

        # Second blink cycle: all sprites go visible
        Action.update_all(0.06)

        # Verify all sprites changed
        for sprite in sprites:
            assert sprite.visible

        # Verify callback was called exactly once, not 50 times
        assert enter_call_count == 1
        assert exit_call_count == 1

        action.stop()

    def test_mixed_sprite_visibility_still_triggers_callbacks(self, test_sprite_list):
        """Test that callbacks fire even when sprites have different starting visibility."""
        sprites = test_sprite_list

        for i, sprite in enumerate(sprites):
            # Mix of visible and invisible sprites
            sprite.visible = i % 2 == 0

        callback_calls = []

        def track_calls(target):
            callback_calls.append(("called", target))

        action = blink_until(
            sprites,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=track_calls,
            on_blink_exit=track_calls,
            tag="mixed_test",
        )

        # Update to trigger first blink
        Action.update_all(0.06)

        # Should have at least one callback (some sprites changed)
        assert len(callback_calls) >= 1
        # All calls should receive the SpriteList
        for call_type, target in callback_calls:
            assert target is sprites

        action.stop()


class TestBlinkUntilCloneIndependence(ActionTestBase):
    """Tests for BlinkUntil clone independence of callbacks and state."""


class TestCallbackUntilInterval(ActionTestBase):
    """Tests for CallbackUntil with interval support."""

    def test_callback_until_no_interval_calls_every_frame(self, test_sprite):
        """Without interval, callback should be called every frame."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.1),  # Run for 0.1 seconds
        )
        action.apply(sprite, tag="test_no_interval")

        # Run for 0.1 seconds at 60 FPS = 6 frames
        for _ in range(6):
            Action.update_all(1 / 60)

        assert call_count == 6
        assert action.done

    def test_callback_until_with_interval_calls_on_schedule(self, test_sprite):
        """With interval, callback should be called at specified intervals."""
        sprite = test_sprite
        call_count = 0
        call_times = []

        def callback():
            nonlocal call_count
            call_count += 1
            call_times.append(call_count)

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.5),  # Run for 0.5 seconds
            seconds_between_calls=0.1,  # Call every 0.1 seconds
        )
        action.apply(sprite, tag="test_interval")

        # Run for 0.5 seconds at 60 FPS = 30 frames
        for _ in range(30):
            Action.update_all(1 / 60)

        # Should be called approximately every 0.1 seconds: 0.1, 0.2, 0.3, 0.4, 0.5
        assert call_count == 5
        assert action.done

    def test_callback_until_interval_factor_scaling(self, test_sprite):
        """Factor scaling should affect the interval timing."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.2),
            seconds_between_calls=0.1,
        )
        action.apply(sprite, tag="test_factor")

        # Run at double speed (factor = 2.0) - should call twice as often
        action.set_factor(2.0)

        # Run for 0.2 seconds at 60 FPS = 12 frames
        for _ in range(12):
            Action.update_all(1 / 60)

        # With factor 2.0, 0.1s interval becomes 0.05s, so should call at 0.05, 0.1, 0.15, 0.2
        assert call_count == 4
        assert action.done

    def test_callback_until_zero_factor_stops_calls(self, test_sprite):
        """Factor of 0.0 should stop callback calls."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.2),
            seconds_between_calls=0.05,  # Very frequent calls
        )
        action.apply(sprite, tag="test_zero_factor")

        # Run a few frames normally
        for _ in range(3):
            Action.update_all(1 / 60)
        initial_calls = call_count

        # Set factor to 0 (stops calls)
        action.set_factor(0.0)

        # Run many more frames
        for _ in range(30):
            Action.update_all(1 / 60)

        # Call count should not have increased
        assert call_count == initial_calls

    def test_callback_until_with_target_parameter(self, test_sprite):
        """Callback should receive target parameter when using _safe_call."""
        sprite = test_sprite
        received_targets = []

        def callback_with_target(target):
            received_targets.append(target)

        action = CallbackUntil(
            callback=callback_with_target,
            condition=duration(0.1),
            seconds_between_calls=0.05,
        )
        action.apply(sprite, tag="test_target_param")

        # Run for 0.1 seconds
        for _ in range(6):
            Action.update_all(1 / 60)

        # Should have received the sprite as target parameter
        assert len(received_targets) == 2  # Called at 0.05s and 0.1s
        assert all(target == sprite for target in received_targets)

    def test_callback_until_with_sprite_list_target(self, test_sprite_list):
        """Callback should receive SpriteList when target is SpriteList."""
        sprite_list = test_sprite_list
        received_targets = []

        def callback_with_target(target):
            received_targets.append(target)

        action = CallbackUntil(
            callback=callback_with_target,
            condition=duration(0.1),
            seconds_between_calls=0.05,
        )
        action.apply(sprite_list, tag="test_sprite_list_target")

        # Run for 0.1 seconds
        for _ in range(6):
            Action.update_all(1 / 60)

        # Should have received the SpriteList as target parameter
        assert len(received_targets) == 2
        assert all(target == sprite_list for target in received_targets)

    def test_callback_until_condition_stops_execution(self, test_sprite):
        """Condition should stop callback execution when met."""
        sprite = test_sprite
        call_count = 0
        condition_met = False

        def callback():
            nonlocal call_count
            call_count += 1

        def condition():
            nonlocal condition_met
            # Stop after 2 calls
            return call_count >= 2

        action = CallbackUntil(
            callback=callback,
            condition=condition,
            seconds_between_calls=0.01,  # Very frequent
        )
        action.apply(sprite, tag="test_condition_stop")

        # Run many frames - should stop after 2 calls
        for _ in range(100):  # Way more than needed
            Action.update_all(1 / 60)
            if action.done:
                break

        assert call_count == 2
        assert action.done

    def test_callback_until_reset_functionality(self, test_sprite):
        """Reset should restore original interval timing."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.2),
            seconds_between_calls=0.1,
        )
        action.apply(sprite, tag="test_reset")

        # Run for a bit, then reset
        for _ in range(6):
            Action.update_all(1 / 60)

        initial_calls = call_count
        action.reset()

        # Run again - should start fresh timing
        for _ in range(6):
            Action.update_all(1 / 60)

        # Should have made additional calls after reset
        assert call_count > initial_calls

    def test_callback_until_on_stop_callback(self, test_sprite):
        """on_stop should be called when condition is met."""
        sprite = test_sprite
        on_stop_called = False
        on_stop_data = None

        def callback():
            pass

        def on_stop(data=None):
            nonlocal on_stop_called, on_stop_data
            on_stop_called = True
            on_stop_data = data

        action = CallbackUntil(
            callback=callback,
            condition=duration(0.1),
            seconds_between_calls=0.05,
            on_stop=on_stop,
        )
        action.apply(sprite, tag="test_on_stop")

        # Run until completion
        for _ in range(10):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert on_stop_called
        assert on_stop_data is None  # duration() returns None

    def test_callback_until_validation_errors(self, test_sprite):
        """Should validate input parameters."""
        sprite = test_sprite

        def callback():
            pass

        # Negative interval should raise error
        with pytest.raises(ValueError, match="seconds_between_calls must be non-negative"):
            CallbackUntil(
                callback=callback,
                condition=duration(0.1),
                seconds_between_calls=-0.1,
            )

    def test_callback_until_exception_safety(self, test_sprite):
        """Callback exceptions should not crash the action."""
        sprite = test_sprite
        call_count = 0

        def failing_callback():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Callback failed!")

        action = CallbackUntil(
            callback=failing_callback,
            condition=duration(0.1),
            seconds_between_calls=0.05,
        )
        action.apply(sprite, tag="test_exception")

        # Should not crash despite callback exception
        for _ in range(10):
            Action.update_all(1 / 60)

        # Should have made at least one call before failing
        assert call_count >= 1


class TestCallbackUntilExceptionHandling(ActionTestBase):
    """Test exception handling in CallbackUntil."""

    def test_callback_until_duration_extraction_exception(self, test_sprite):
        """Test exception handling when duration extraction fails."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        # Create a malformed condition that will cause exception during duration extraction
        def bad_condition():
            return False

        # Add attributes that will cause exception in duration extraction
        bad_condition._is_duration_condition = True
        bad_condition._duration_seconds = "not_a_number"  # Invalid type

        action = CallbackUntil(
            callback=callback,
            condition=bad_condition,
            seconds_between_calls=0.05,
        )
        action.apply(sprite, tag="test_exception")

        # Should not crash despite duration extraction exception
        for _ in range(5):
            Action.update_all(1 / 60)

        # Should still work with callback
        assert call_count >= 1

    def test_callback_until_apply_effect_exception_handling(self, test_sprite):
        """Test exception handling in apply_effect duration extraction."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        # Create a condition with malformed closure that will cause exception
        class BadCell:
            @property
            def cell_contents(self):
                raise AttributeError("Simulated cell access error")

        class MockCondition:
            def __call__(self):
                return False

            __closure__ = (BadCell(),)  # This will cause an exception when accessing cell_contents

        bad_closure_condition = MockCondition()

        action = CallbackUntil(
            callback=callback,
            condition=bad_closure_condition,
            seconds_between_calls=0.05,
        )
        action.apply(sprite, tag="test_apply_exception")

        # Should not crash despite exception in apply_effect
        for _ in range(5):
            Action.update_all(1 / 60)

        # Should still work
        assert call_count >= 1

    def test_callback_until_callback_exception_fallback(self, test_sprite):
        """Test fallback to _safe_call when callback has other exceptions."""
        sprite = test_sprite
        exception_count = 0

        def failing_callback():
            nonlocal exception_count
            exception_count += 1
            if exception_count == 1:
                # First call: TypeError (wrong signature)
                raise TypeError("Wrong signature")
            elif exception_count == 2:
                # Second call: RuntimeError (other exception)
                raise RuntimeError("Other error")

        action = CallbackUntil(
            callback=failing_callback,
            condition=duration(0.1),
            seconds_between_calls=0.05,
        )
        action.apply(sprite, tag="test_fallback")

        # Should not crash and use _safe_call fallback
        for _ in range(6):
            Action.update_all(1 / 60)

        # Should have attempted to call at least once
        assert exception_count >= 1

    def test_callback_until_edge_case_completion_callback(self, test_sprite):
        """Test edge case where final callback fires at completion time."""
        sprite = test_sprite
        call_times = []

        def callback():
            call_times.append(len(call_times) + 1)

        # Set up action with very precise timing to trigger edge case
        action = CallbackUntil(
            callback=callback,
            condition=duration(0.1),
            seconds_between_calls=0.1,  # Exactly at completion time
        )
        action.apply(sprite, tag="test_edge_case")

        # Run for exactly the duration
        for _ in range(6):  # 6 * (1/60) = 0.1 seconds
            Action.update_all(1 / 60)

        # Should fire callback at the completion time due to edge case handling
        assert len(call_times) >= 1

    def test_callback_until_no_duration_condition(self, test_sprite):
        """Test CallbackUntil with condition that doesn't have duration."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        # Simple condition without duration
        def simple_condition():
            return call_count >= 3

        action = CallbackUntil(
            callback=callback,
            condition=simple_condition,
            seconds_between_calls=0.02,
        )
        action.apply(sprite, tag="test_no_duration")

        # Run until condition is met
        for _ in range(10):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert call_count == 3
        assert action.done


class TestCallbackUntilStopAndRestart(ActionTestBase):
    """Test CallbackUntil with stop and restart functionality."""

    def test_callback_until_stop_and_restart_with_tag(self, test_sprite):
        """Test CallbackUntil with tag, seconds_between_calls, infinite condition, stop and restart."""
        sprite = test_sprite
        call_count_first = 0
        call_count_second = 0

        def callback_first():
            nonlocal call_count_first
            call_count_first += 1

        def callback_second():
            nonlocal call_count_second
            call_count_second += 1

        # First test run: Set up CallbackUntil with tag and interval
        action1 = CallbackUntil(
            callback=callback_first,
            condition=infinite(),  # Never-ending condition
            seconds_between_calls=0.05,  # Call every 0.05 seconds (50ms)
        )
        action1.apply(sprite, tag="test_callback_action")

        # Verify the action is active
        active_actions = Action.get_actions_for_target(sprite, tag="test_callback_action")
        assert len(active_actions) == 1
        assert active_actions[0] is action1

        # Let it run and fire a couple of times
        # At 0.05 second intervals, we need to run for at least 0.1 seconds to get 2+ calls
        for i in range(10):  # 10 frames at 1/60 = ~0.167 seconds
            Action.update_all(1 / 60)  # 16.67ms per frame

        # Should have fired at least 2-3 times (0.05s and 0.1s marks, possibly 0.15s)
        assert call_count_first >= 2, f"Expected at least 2 calls, got {call_count_first}"
        assert call_count_first <= 4, f"Expected at most 4 calls, got {call_count_first}"  # Allow some tolerance

        # Verify action is still running (infinite condition)
        assert not action1.done

        # Stop the action
        action1.stop()

        # Verify action is stopped and no longer active
        assert action1.done
        active_actions_after_stop = Action.get_actions_for_target(sprite, tag="test_callback_action")
        assert len(active_actions_after_stop) == 0

        # Store the call count from first run
        first_run_calls = call_count_first

        # Wait a bit more to ensure no more calls happen after stop
        for _ in range(5):
            Action.update_all(1 / 60)
        assert call_count_first == first_run_calls, "Callback should not fire after stop"

        # Second test run: Set up the exact same configuration again
        action2 = CallbackUntil(
            callback=callback_second,
            condition=infinite(),  # Same infinite condition
            seconds_between_calls=0.05,  # Same interval
        )
        action2.apply(sprite, tag="test_callback_action")  # Same tag name

        # Verify the new action is active
        active_actions_restart = Action.get_actions_for_target(sprite, tag="test_callback_action")
        assert len(active_actions_restart) == 1
        assert active_actions_restart[0] is action2
        assert active_actions_restart[0] is not action1  # Different instance

        # Let it run and fire a couple of times again
        for i in range(10):  # Same duration as first test
            Action.update_all(1 / 60)

        # Should have fired at least 2-3 times, just like the first run
        assert call_count_second >= 2, f"Expected at least 2 calls on restart, got {call_count_second}"
        assert call_count_second <= 4, f"Expected at most 4 calls on restart, got {call_count_second}"

        # Verify second action is still running
        assert not action2.done

        # Verify first callback counter didn't change
        assert call_count_first == first_run_calls, "First callback should remain unchanged"

        # Clean up: Stop the second action
        action2.stop()
        assert action2.done

        # Final verification: Both callbacks worked independently
        assert call_count_first > 0, "First callback should have been called"
        assert call_count_second > 0, "Second callback should have been called"
        assert call_count_first == first_run_calls, "First callback count should be stable"

    def test_callback_until_in_parallel_stop_and_restart_with_tag(self, test_sprite):
        """Test CallbackUntil within parallel composition with stop and restart functionality."""
        from actions.composite import parallel
        from actions.conditional import DelayUntil, duration

        sprite = test_sprite
        call_count_first = 0
        call_count_second = 0

        def callback_first():
            nonlocal call_count_first
            call_count_first += 1

        def callback_second():
            nonlocal call_count_second
            call_count_second += 1

        # First test run: Set up CallbackUntil within a parallel composition
        callback_action1 = CallbackUntil(
            callback=callback_first,
            condition=infinite(),  # Never-ending condition
            seconds_between_calls=0.05,  # Call every 0.05 seconds (50ms)
        )

        # Create a delay action to run alongside the callback
        delay_action1 = DelayUntil(duration(1.0))  # 1-second delay (longer than our test)

        # Create parallel composition
        parallel_action1 = parallel(callback_action1, delay_action1)
        parallel_action1.apply(sprite, tag="test_parallel_callback")

        # Verify the parallel action is active
        active_actions = Action.get_actions_for_target(sprite, tag="test_parallel_callback")
        assert len(active_actions) == 1
        assert active_actions[0] is parallel_action1

        # Let it run and fire a couple of times
        # At 0.05 second intervals, we need to run for at least 0.1 seconds to get 2+ calls
        for i in range(10):  # 10 frames at 1/60 = ~0.167 seconds
            Action.update_all(1 / 60)  # 16.67ms per frame

        # Should have fired at least 2-3 times (0.05s and 0.1s marks, possibly 0.15s)
        assert call_count_first >= 2, f"Expected at least 2 calls, got {call_count_first}"
        assert call_count_first <= 4, f"Expected at most 4 calls, got {call_count_first}"  # Allow some tolerance

        # Verify parallel action is still running (both actions should be running)
        assert not parallel_action1.done
        assert not callback_action1.done
        assert not delay_action1.done

        # Stop the parallel action (this should stop both child actions)
        parallel_action1.stop()

        # Verify parallel action and its children are stopped
        assert parallel_action1.done
        assert callback_action1.done
        assert delay_action1.done
        active_actions_after_stop = Action.get_actions_for_target(sprite, tag="test_parallel_callback")
        assert len(active_actions_after_stop) == 0

        # Store the call count from first run
        first_run_calls = call_count_first

        # Wait a bit more to ensure no more calls happen after stop
        for _ in range(5):
            Action.update_all(1 / 60)
        assert call_count_first == first_run_calls, "Callback should not fire after parallel stop"

        # Second test run: Set up the exact same parallel configuration again
        callback_action2 = CallbackUntil(
            callback=callback_second,
            condition=infinite(),  # Same infinite condition
            seconds_between_calls=0.05,  # Same interval
        )

        # Create another delay action
        delay_action2 = DelayUntil(duration(1.0))  # Same delay duration

        # Create parallel composition with same tag
        parallel_action2 = parallel(callback_action2, delay_action2)
        parallel_action2.apply(sprite, tag="test_parallel_callback")  # Same tag name

        # Verify the new parallel action is active
        active_actions_restart = Action.get_actions_for_target(sprite, tag="test_parallel_callback")
        assert len(active_actions_restart) == 1
        assert active_actions_restart[0] is parallel_action2
        assert active_actions_restart[0] is not parallel_action1  # Different instance

        # Let it run and fire a couple of times again
        for i in range(10):  # Same duration as first test
            Action.update_all(1 / 60)

        # Should have fired at least 2-3 times, just like the first run
        assert call_count_second >= 2, f"Expected at least 2 calls on restart, got {call_count_second}"
        assert call_count_second <= 4, f"Expected at most 4 calls on restart, got {call_count_second}"

        # Verify second parallel action is still running
        assert not parallel_action2.done
        assert not callback_action2.done
        assert not delay_action2.done

        # Verify first callback counter didn't change
        assert call_count_first == first_run_calls, "First callback should remain unchanged"

        # Clean up: Stop the second parallel action
        parallel_action2.stop()
        assert parallel_action2.done
        assert callback_action2.done
        assert delay_action2.done

        # Final verification: Both callbacks worked independently within parallel compositions
        assert call_count_first > 0, "First callback should have been called"
        assert call_count_second > 0, "Second callback should have been called"
        assert call_count_first == first_run_calls, "First callback count should be stable"

    def test_callback_until_wave_pattern_issue(self, test_sprite):
        """Test CallbackUntil in wave pattern that mimics FlashingForcefieldWave behavior."""
        from actions.composite import parallel
        from actions.conditional import BlinkUntil, MoveUntil

        sprite = test_sprite
        call_count_first = 0
        call_count_second = 0

        def update_color_first():
            nonlocal call_count_first
            call_count_first += 1
            print(f"update_color_first: {call_count_first}")

        def update_color_second():
            nonlocal call_count_second
            call_count_second += 1
            print(f"update_color_second: {call_count_second}")

        # First wave: Simulate FlashingForcefieldWave pattern exactly
        move_action1 = MoveUntil(
            velocity=(50, 0),
            condition=infinite(),
        )
        blink_action1 = BlinkUntil(
            seconds_until_change=0.5,
            condition=infinite(),
        )
        callback_action1 = CallbackUntil(
            seconds_between_calls=0.1,
            callback=update_color_first,
            condition=infinite(),
        )

        # Create parallel composition exactly like in FlashingForcefieldWave
        combined_actions1 = parallel(move_action1, blink_action1, callback_action1)
        combined_actions1.apply(sprite, tag="forcefield")

        print("=== First wave starting ===")

        # Let it run for several callback cycles
        for i in range(20):  # 20 frames at 1/60 = ~0.33 seconds, should get 3+ callbacks
            Action.update_all(1 / 60)

        print(f"First wave callbacks: {call_count_first}")
        assert call_count_first >= 3, f"Expected at least 3 calls in first wave, got {call_count_first}"

        # Store first run count
        first_run_calls = call_count_first

        # Stop the wave - this is what cleanup() does
        combined_actions1.stop()
        print("=== First wave stopped ===")

        # Verify action is stopped
        assert combined_actions1.done
        assert move_action1.done
        assert blink_action1.done
        assert callback_action1.done

        # Wait to ensure no more calls happen
        for _ in range(5):
            Action.update_all(1 / 60)
        assert call_count_first == first_run_calls, "No callbacks should fire after stop"

        # Second wave: Create new instances exactly like FlashingForcefieldWave would
        move_action2 = MoveUntil(
            velocity=(50, 0),
            condition=infinite(),
        )
        blink_action2 = BlinkUntil(
            seconds_until_change=0.5,
            condition=infinite(),
        )
        callback_action2 = CallbackUntil(
            seconds_between_calls=0.1,
            callback=update_color_second,
            condition=infinite(),
        )

        # Create parallel composition exactly like in FlashingForcefieldWave
        combined_actions2 = parallel(move_action2, blink_action2, callback_action2)
        combined_actions2.apply(sprite, tag="forcefield")  # Same tag as before

        print("=== Second wave starting ===")

        # Let it run for several callback cycles - this should work but might not
        for i in range(20):  # Same duration as first test
            Action.update_all(1 / 60)
            if i % 5 == 0:  # Print every 5 frames to debug
                print(f"Frame {i}: Second wave callbacks so far: {call_count_second}")

        print(f"Second wave final callbacks: {call_count_second}")

        # This assertion might fail, revealing the issue
        assert call_count_second >= 3, f"Expected at least 3 calls in second wave, got {call_count_second}"

        # Verify first callback counter didn't change
        assert call_count_first == first_run_calls, "First callback should remain unchanged"

        # Clean up
        combined_actions2.stop()

        print("=== Test completed ===")
        print(f"Final counts - First: {call_count_first}, Second: {call_count_second}")

    def test_callback_until_spritelist_wave_pattern(self, test_sprite):
        """Test CallbackUntil with SpriteList exactly like FlashingForcefieldWave."""
        from actions.composite import parallel
        from actions.conditional import BlinkUntil, MoveUntil

        # Create a SpriteList like FlashingForcefieldWave does
        forcefields1 = arcade.SpriteList()
        forcefields1.append(test_sprite)  # Add a sprite to the list

        call_count_first = 0
        call_count_second = 0

        def update_color_first():
            nonlocal call_count_first
            call_count_first += 1
            print(f"update_color_first: {call_count_first}")

        def update_color_second():
            nonlocal call_count_second
            call_count_second += 1
            print(f"update_color_second: {call_count_second}")

        # Exactly like FlashingForcefieldWave.build()
        combined_actions1 = parallel(
            MoveUntil(
                velocity=(50, 0),
                condition=infinite(),
            ),
            BlinkUntil(
                seconds_until_change=0.5,
                condition=infinite(),
            ),
            CallbackUntil(
                seconds_between_calls=0.1,
                callback=update_color_first,
                condition=infinite(),
            ),
        )
        combined_actions1.apply(forcefields1, tag="forcefield")  # Apply to SpriteList

        print("=== First wave starting (SpriteList) ===")

        # Let it run for several callback cycles
        for i in range(20):  # 20 frames at 1/60 = ~0.33 seconds, should get 3+ callbacks
            Action.update_all(1 / 60)

        print(f"First wave callbacks: {call_count_first}")
        assert call_count_first >= 3, f"Expected at least 3 calls in first wave, got {call_count_first}"

        # Store first run count
        first_run_calls = call_count_first

        # Stop the wave exactly like FlashingForcefieldWave.cleanup()
        combined_actions1.stop()
        print("=== First wave stopped (SpriteList) ===")

        # Wait to ensure no more calls happen
        for _ in range(5):
            Action.update_all(1 / 60)
        assert call_count_first == first_run_calls, "No callbacks should fire after stop"

        # Create NEW SpriteList for second wave (simulating new wave instance)
        forcefields2 = arcade.SpriteList()
        forcefields2.append(test_sprite)  # Same sprite but new list

        # Second wave: Create new parallel composition exactly like new FlashingForcefieldWave
        combined_actions2 = parallel(
            MoveUntil(
                velocity=(50, 0),
                condition=infinite(),
            ),
            BlinkUntil(
                seconds_until_change=0.5,
                condition=infinite(),
            ),
            CallbackUntil(
                seconds_between_calls=0.1,
                callback=update_color_second,
                condition=infinite(),
            ),
        )
        combined_actions2.apply(forcefields2, tag="forcefield")  # Same tag, new SpriteList

        print("=== Second wave starting (SpriteList) ===")

        # Let it run for several callback cycles
        for i in range(20):
            Action.update_all(1 / 60)
            if i % 5 == 0:
                print(f"Frame {i}: Second wave callbacks so far: {call_count_second}")

        print(f"Second wave final callbacks: {call_count_second}")

        # This might fail if there's an issue with SpriteList action management
        assert call_count_second >= 3, f"Expected at least 3 calls in second wave, got {call_count_second}"

        # Verify first callback counter didn't change
        assert call_count_first == first_run_calls, "First callback should remain unchanged"

        # Clean up
        combined_actions2.stop()

        print("=== SpriteList Test completed ===")
        print(f"Final counts - First: {call_count_first}, Second: {call_count_second}")

    def test_callback_until_class_instance_pattern(self, test_sprite):
        """Test CallbackUntil with class instances exactly like FlashingForcefieldWave."""
        from actions.composite import parallel
        from actions.conditional import BlinkUntil, MoveUntil

        class MockWave:
            def __init__(self, wave_id):
                self.wave_id = wave_id
                self.call_count = 0
                self._actions = []
                self._forcefields = arcade.SpriteList()
                self._forcefields.append(test_sprite)

            def update_color(self):
                self.call_count += 1
                print(f"Wave {self.wave_id} update_color: {self.call_count}")

            def build(self):
                combined_actions = parallel(
                    MoveUntil(
                        velocity=(50, 0),
                        condition=infinite(),
                    ),
                    BlinkUntil(
                        seconds_until_change=0.5,
                        condition=infinite(),
                    ),
                    CallbackUntil(
                        seconds_between_calls=0.1,
                        callback=self.update_color,  # Bound method
                        condition=infinite(),
                    ),
                )
                combined_actions.apply(self._forcefields, tag="forcefield")
                self._actions.append(combined_actions)

            def cleanup(self):
                for action in self._actions:
                    action.stop()
                self._actions.clear()

        # First wave instance
        wave1 = MockWave("Wave1")
        wave1.build()

        print("=== First wave starting (Class instance) ===")

        # Let it run for several callback cycles
        for i in range(20):
            Action.update_all(1 / 60)

        print(f"First wave callbacks: {wave1.call_count}")
        assert wave1.call_count >= 3, f"Expected at least 3 calls in first wave, got {wave1.call_count}"

        # Store first run count
        first_run_calls = wave1.call_count

        # Stop the wave
        wave1.cleanup()
        print("=== First wave stopped (Class instance) ===")

        # Wait to ensure no more calls happen
        for _ in range(5):
            Action.update_all(1 / 60)
        assert wave1.call_count == first_run_calls, "No callbacks should fire after stop"

        # Create completely new wave instance (like your game would)
        wave2 = MockWave("Wave2")
        wave2.build()

        print("=== Second wave starting (Class instance) ===")

        # Let it run for several callback cycles
        for i in range(20):
            Action.update_all(1 / 60)
            if i % 5 == 0:
                print(f"Frame {i}: Second wave callbacks so far: {wave2.call_count}")

        print(f"Second wave final callbacks: {wave2.call_count}")

        # This should work unless there's a bound method issue
        assert wave2.call_count >= 3, f"Expected at least 3 calls in second wave, got {wave2.call_count}"

        # Verify first wave counter didn't change
        assert wave1.call_count == first_run_calls, "First wave callback should remain unchanged"

        # Clean up
        wave2.cleanup()

        print("=== Class instance Test completed ===")
        print(f"Final counts - Wave1: {wave1.call_count}, Wave2: {wave2.call_count}")

    def test_boundary_callbacks_dont_fire_after_stop(self, test_sprite):
        """Test that boundary callbacks don't fire after action is stopped.

        This is a regression test for the late callback bug where boundary callbacks
        from stopped actions could interfere with newly started actions.
        """
        sprite = test_sprite
        sprite.center_x = 95  # Start close to right boundary
        sprite.center_y = 50

        boundary_enter_count = 0
        boundary_exit_count = 0

        def on_boundary_enter(sprite, axis, side):
            nonlocal boundary_enter_count
            boundary_enter_count += 1

        def on_boundary_exit(sprite, axis, side):
            nonlocal boundary_exit_count
            boundary_exit_count += 1

        action = MoveUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 100, 100),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )
        action.apply(sprite)

        # Move until boundary is hit (should only take 1-2 frames from x=95 to x=100)
        for _ in range(5):
            Action.update_all(1 / 60)
            sprite.update()  # Apply velocity to position

        initial_enter_count = boundary_enter_count
        initial_exit_count = boundary_exit_count
        assert initial_enter_count >= 1, "Should trigger boundary enter callback"

        # Stop the action
        action.stop()

        # Verify action is stopped and callbacks are deactivated
        assert action.done
        assert not action._is_active
        assert not action._callbacks_active

        # Continue updating - callbacks should NOT fire
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        assert boundary_enter_count == initial_enter_count, "Boundary enter callbacks should not fire after stop"
        assert boundary_exit_count == initial_exit_count, "Boundary exit callbacks should not fire after stop"

    def test_callbacks_active_flag_lifecycle(self, test_sprite):
        """Test that _callbacks_active flag follows the correct lifecycle."""
        sprite = test_sprite

        callback_count = 0

        def callback():
            nonlocal callback_count
            callback_count += 1

        # Create action
        action = CallbackUntil(
            callback=callback,
            condition=infinite,
            seconds_between_calls=0.05,
        )

        # Before apply - should have _callbacks_active = True
        assert action._callbacks_active, "Should have _callbacks_active=True after construction"

        action.apply(sprite)

        # After apply - still active
        assert action._callbacks_active, "Should have _callbacks_active=True after apply"
        assert action._is_active, "Should be active after apply"

        # Let it run and trigger some callbacks
        for _ in range(10):
            Action.update_all(1 / 60)

        assert callback_count > 0, "Callbacks should fire while active"
        initial_count = callback_count

        # Stop the action
        action.stop()

        # After stop - callbacks should be deactivated
        assert not action._callbacks_active, "Should have _callbacks_active=False after stop"
        assert action.done, "Should be done after stop"
        assert not action._is_active, "Should not be active after stop"

        # Continue updating - no more callbacks should fire
        for _ in range(10):
            Action.update_all(1 / 60)

        assert callback_count == initial_count, "No callbacks should fire after stop"

    def test_three_phase_update_prevents_late_callbacks(self, test_sprite):
        """Test that the three-phase update mechanism prevents late callbacks.

        This tests the specific fix for the bug where callbacks from stopped
        actions could fire during the same update_all() call that processes their removal.
        """
        sprite = test_sprite

        callback_fired_after_done = False

        def condition_checker():
            # This will mark the action as done on first call
            return True

        def callback():
            nonlocal callback_fired_after_done
            # This callback should not fire after the action is marked as done
            # Check if the action is done when callback fires
            if action.done:
                callback_fired_after_done = True

        action = CallbackUntil(
            callback=callback,
            condition=condition_checker,
            seconds_between_calls=0.01,  # Fast callbacks
        )
        action.apply(sprite)

        # Single update that will:
        # - Mark action as done (condition returns True)
        # - Should deactivate callbacks in phase 1
        # - Should not call callback in phase 2
        Action.update_all(1 / 60)

        # Verify the action is done
        assert action.done, "Action should be done after condition is met"

        # Verify callback didn't fire after action was marked done
        assert not callback_fired_after_done, (
            "Callback should not fire after action is marked done (three-phase update should prevent this)"
        )

    def test_boundary_callback_cleanup_on_remove_effect(self, test_sprite):
        """Test that boundary callbacks are cleared in remove_effect."""
        sprite = test_sprite
        sprite.center_x = 50
        sprite.center_y = 50

        def on_boundary_enter(sprite, axis, side):
            pass

        def on_boundary_exit(sprite, axis, side):
            pass

        action = MoveUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 100, 100),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )
        action.apply(sprite)

        # Verify callbacks are registered
        assert action.on_boundary_enter is not None
        assert action.on_boundary_exit is not None
        # Boundary state may be lazily initialized on apply; if present, entries should be None/None
        for state in action._boundary_state.values():
            assert state == {"x": None, "y": None}

        # Stop the action (which calls remove_effect)
        action.stop()

        # Verify callbacks and state are cleared
        assert action.on_boundary_enter is None, "on_boundary_enter should be cleared"
        assert action.on_boundary_exit is None, "on_boundary_exit should be cleared"
        assert len(action._boundary_state) == 0, "_boundary_state should be cleared"
