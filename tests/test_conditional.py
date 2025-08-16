"""Test suite for condition_actions.py - Conditional actions."""

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
from tests.conftest import ActionTestBase


class TestMoveUntil(ActionTestBase):
    """Test suite for MoveUntil action."""

    def test_move_until_basic(self, test_sprite):
        """Test basic MoveUntil functionality."""
        sprite = test_sprite
        start_x = sprite.center_x

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = move_until(sprite, velocity=(100, 0), condition=condition, tag="test_basic")

        # Update for one frame - sprite should have velocity applied
        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 0

        # Let it move for a bit
        for _ in range(10):
            sprite.update()  # Apply velocity to position
            Action.update_all(0.016)

        assert sprite.center_x > start_x

        # Trigger condition
        condition_met = True
        Action.update_all(0.016)

        # Velocity should be zeroed
        assert sprite.change_x == 0
        assert sprite.change_y == 0
        assert action.done

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

    def test_move_until_velocity_values(self, test_sprite):
        """Test that MoveUntil sets velocity values directly (pixels per frame at 60 FPS)."""
        sprite = test_sprite

        # Test various velocity values
        test_cases = [
            (1, 0),  # Should result in change_x = 1.0
            (2, 0),  # Should result in change_x = 2.0
            (0, 3),  # Should result in change_y = 3.0
            (5, 4),  # Should result in change_x = 5.0, change_y = 4.0
        ]

        for input_velocity in test_cases:
            Action.stop_all()
            sprite.change_x = 0
            sprite.change_y = 0

            action = move_until(sprite, velocity=input_velocity, condition=infinite, tag="test_velocity")
            Action.update_all(0.016)

            assert sprite.change_x == input_velocity[0], f"Failed for input {input_velocity}"
            assert sprite.change_y == input_velocity[1], f"Failed for input {input_velocity}"

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

        def on_boundary(sprite, axis):
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
            on_boundary=on_boundary,
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

    def test_follow_path_until_clone_preserves_rotation_params(self, test_sprite):
        """Test cloning preserves rotation parameters."""
        sprite = test_sprite
        control_points = [(100, 100), (200, 100)]
        original = follow_path_until(
            sprite,
            control_points=control_points,
            velocity=100,
            condition=infinite,
            rotate_with_path=True,
            rotation_offset=-90,
            tag="test_rotation_params",
        )

        cloned = original.clone()

        assert cloned.rotate_with_path == True
        assert cloned.rotation_offset == -90


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

    def test_tween_until_clone(self, test_sprite):
        sprite = test_sprite
        action = tween_until(
            sprite, start_value=0, end_value=100, property_name="center_x", condition=duration(1.0), tag="test_clone"
        )
        clone = action.clone()
        assert isinstance(clone, type(action))
        assert clone.start_value == 0
        assert clone.end_value == 100
        assert clone.property_name == "center_x"

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
