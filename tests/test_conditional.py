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


class TestMoveUntil:
    """Test suite for MoveUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_until_basic(self):
        """Test basic MoveUntil functionality."""
        sprite = create_test_sprite()
        start_x = sprite.center_x

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = move_until(sprite, (100, 0), condition, tag="test_basic")

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

    def test_move_until_frame_based_semantics(self):
        """Test that MoveUntil uses pixels per frame at 60 FPS semantics."""
        sprite = create_test_sprite()

        # 5 pixels per frame should move 5 pixels when sprite.update() is called
        action = move_until(sprite, (5, 0), infinite, tag="test_frame_semantics")

        # Update action to apply velocity
        Action.update_all(0.016)
        assert sprite.change_x == 5  # Raw frame-based value

        # Move sprite using its velocity
        start_x = sprite.center_x
        sprite.update()  # Arcade applies change_x to position

        # Should have moved exactly 5 pixels
        distance_moved = sprite.center_x - start_x
        assert distance_moved == 5.0

    def test_move_until_velocity_values(self):
        """Test that MoveUntil sets velocity values directly (pixels per frame at 60 FPS)."""
        sprite = create_test_sprite()

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

            action = move_until(sprite, input_velocity, infinite, tag="test_velocity")
            Action.update_all(0.016)

            assert sprite.change_x == input_velocity[0], f"Failed for input {input_velocity}"
            assert sprite.change_y == input_velocity[1], f"Failed for input {input_velocity}"

    def test_move_until_callback(self):
        """Test MoveUntil with callback."""
        sprite = create_test_sprite()
        callback_called = False
        callback_data = None

        def on_stop(data=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        def condition():
            return {"reason": "collision", "damage": 10}

        action = move_until(sprite, (100, 0), condition, on_stop=on_stop, tag="test_callback")

        Action.update_all(0.016)

        assert callback_called
        assert callback_data == {"reason": "collision", "damage": 10}

    def test_move_until_sprite_list(self):
        """Test MoveUntil with SpriteList."""
        sprite_list = create_test_sprite_list()

        action = move_until(sprite_list, (50, 25), infinite, tag="test_sprite_list")

        Action.update_all(0.016)

        # Both sprites should have the same velocity
        for sprite in sprite_list:
            assert sprite.change_x == 50
            assert sprite.change_y == 25

    def test_move_until_set_current_velocity(self):
        """Test MoveUntil set_current_velocity method."""
        sprite = create_test_sprite()
        action = move_until(sprite, (100, 0), infinite, tag="test_set_velocity")

        # Initial velocity should be set
        Action.update_all(0.016)
        assert sprite.change_x == 100

        # Change velocity
        action.set_current_velocity((50, 25))
        assert sprite.change_x == 50
        assert sprite.change_y == 25

    def test_move_until_limit_boundary_basic(self):
        """Test basic limit boundary behavior - sprite stops exactly at boundary."""
        sprite = create_test_sprite()
        sprite.center_x = 50
        sprite.center_y = 100

        # Set bounds and limit behavior
        bounds = (0, 0, 200, 200)  # left, bottom, right, top
        action = move_until(
            sprite, (100, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_basic"
        )

        # Apply velocity
        Action.update_all(0.016)
        assert sprite.change_x == 100

        # Move sprite - should stop exactly at right boundary (200)
        sprite.update()  # Apply velocity to position
        assert sprite.center_x == 150  # 50 + 100

        # Continue moving - should stop at boundary
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should be stopped exactly at the right boundary
        assert sprite.center_x == 200
        assert sprite.change_x == 0  # Velocity should be zeroed

    def test_move_until_limit_boundary_left(self):
        """Test limit boundary behavior when moving left."""
        sprite = create_test_sprite()
        sprite.center_x = 150
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (-100, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_left"
        )

        Action.update_all(0.016)
        assert sprite.change_x == -100

        # Move sprite - should stop exactly at left boundary (0)
        sprite.update()
        assert sprite.center_x == 50  # 150 - 100

        # Continue moving - should stop at boundary
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should be stopped exactly at the left boundary
        assert sprite.center_x == 0
        assert sprite.change_x == 0

    def test_move_until_limit_boundary_vertical(self):
        """Test limit boundary behavior for vertical movement."""
        sprite = create_test_sprite()
        sprite.center_x = 100
        sprite.center_y = 50

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (0, 100), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_vertical"
        )

        Action.update_all(0.016)
        assert sprite.change_y == 100

        # Move sprite - should stop exactly at top boundary (200)
        sprite.update()
        assert sprite.center_y == 150  # 50 + 100

        # Continue moving - should stop at boundary
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should be stopped exactly at the top boundary
        assert sprite.center_y == 200
        assert sprite.change_y == 0

    def test_move_until_limit_boundary_diagonal(self):
        """Test limit boundary behavior for diagonal movement."""
        sprite = create_test_sprite()
        sprite.center_x = 50
        sprite.center_y = 50

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (100, 100), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_diagonal"
        )

        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 100

        # Move sprite - should stop at whichever boundary is hit first
        sprite.update()
        assert sprite.center_x == 150  # 50 + 100
        assert sprite.center_y == 150  # 50 + 100

        # Continue moving - should stop at boundary
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should be stopped at the boundary (both x and y should be at limits)
        assert sprite.center_x == 200
        assert sprite.center_y == 200
        assert sprite.change_x == 0
        assert sprite.change_y == 0

    def test_move_until_limit_boundary_no_wiggling(self):
        """Test that limit boundary prevents wiggling across boundary."""
        sprite = create_test_sprite()
        sprite.center_x = 199  # Very close to right boundary
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (10, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_no_wiggling"
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

    def test_move_until_limit_boundary_callback(self):
        """Test limit boundary behavior with callback."""
        sprite = create_test_sprite()
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
            (100, 0),
            infinite,
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

    def test_move_until_limit_boundary_sprite_list(self):
        """Test limit boundary behavior with SpriteList."""
        sprite_list = create_test_sprite_list()
        sprite_list[0].center_x = 50
        sprite_list[1].center_x = 150

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite_list, (100, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_sprite_list"
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

    def test_move_until_limit_boundary_already_at_boundary(self):
        """Test limit boundary behavior when sprite starts at boundary."""
        sprite = create_test_sprite()
        sprite.center_x = 200  # Start at right boundary
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (10, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_at_boundary"
        )

        Action.update_all(0.016)
        # Should not set velocity since already at boundary
        assert sprite.change_x == 0

        # Try to move again
        Action.update_all(0.016)
        assert sprite.center_x == 200  # Should stay at boundary
        assert sprite.change_x == 0

    def test_move_until_limit_boundary_multiple_axes(self):
        """Test limit boundary behavior when hitting multiple boundaries."""
        sprite = create_test_sprite()
        sprite.center_x = 199
        sprite.center_y = 199

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (10, 10), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_multiple_axes"
        )

        Action.update_all(0.016)
        sprite.update()

        # Should be stopped at both boundaries
        assert sprite.center_x == 200
        assert sprite.center_y == 200
        assert sprite.change_x == 0
        assert sprite.change_y == 0

    def test_move_until_limit_boundary_negative_bounds(self):
        """Test limit boundary behavior with negative bounds."""
        sprite = create_test_sprite()
        sprite.center_x = -50
        sprite.center_y = 100

        bounds = (-100, 0, 100, 200)  # Negative left bound
        action = move_until(
            sprite, (-10, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_negative_bounds"
        )

        Action.update_all(0.016)
        assert sprite.change_x == -10

        # Move sprite - should stop at left boundary (-100)
        sprite.update()
        assert sprite.center_x == -60

        # Continue moving
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Should be stopped at the left boundary
        assert sprite.center_x == -100
        assert sprite.change_x == 0

    def test_move_until_limit_boundary_precise_stopping(self):
        """Test that limit boundary stops sprite precisely without overshooting."""
        sprite = create_test_sprite()
        sprite.center_x = 195
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (10, 0), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_precise"
        )

        Action.update_all(0.016)
        # For limit behavior, velocity should not be set if it would cross boundary
        assert sprite.change_x == 0

        # Move sprite - should stop exactly at 200, not overshoot
        sprite.update()
        assert sprite.center_x == 200
        assert sprite.change_x == 0

        # Verify no overshooting occurred
        assert sprite.center_x <= 200

    def test_move_until_limit_boundary_velocity_clearing(self):
        """Test that limit boundary properly clears velocity when stopping."""
        sprite = create_test_sprite()
        sprite.center_x = 50
        sprite.center_y = 100

        bounds = (0, 0, 200, 200)
        action = move_until(
            sprite, (100, 50), infinite, bounds=bounds, boundary_behavior="limit", tag="test_limit_velocity_clearing"
        )

        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 50

        # Move until boundary is hit
        for _ in range(10):
            sprite.update()
            Action.update_all(0.016)

        # Both velocities should be cleared when stopped at boundary
        assert sprite.change_x == 0
        assert sprite.change_y == 0


class TestFollowPathUntil:
    """Test suite for FollowPathUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_follow_path_until_basic(self):
        """Test basic FollowPathUntil functionality."""
        sprite = create_test_sprite()
        start_pos = sprite.position

        control_points = [(100, 100), (200, 200), (300, 100)]
        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = follow_path_until(sprite, control_points, 100, condition, tag="test_basic_path")

        Action.update_all(0.016)

        # Sprite should start moving along the path
        assert sprite.position != start_pos

    def test_follow_path_until_completion(self):
        """Test FollowPathUntil completes when reaching end of path."""
        sprite = create_test_sprite()
        control_points = [(100, 100), (200, 100)]  # Simple straight line

        action = follow_path_until(sprite, control_points, 1000, infinite, tag="test_path_completion")  # High velocity

        # Update until path is complete
        for _ in range(100):
            Action.update_all(0.016)
            if action.done:
                break

        assert action.done

    def test_follow_path_until_requires_points(self):
        """Test FollowPathUntil requires at least 2 control points."""
        sprite = create_test_sprite()
        with pytest.raises(ValueError):
            follow_path_until(sprite, [(100, 100)], 100, infinite)

    def test_follow_path_until_no_rotation_by_default(self):
        """Test FollowPathUntil doesn't rotate sprite by default."""
        sprite = create_test_sprite()
        original_angle = sprite.angle

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(sprite, control_points, 100, infinite, tag="test_no_rotation")

        # Update several frames
        for _ in range(10):
            Action.update_all(0.016)

        # Sprite angle should not have changed
        assert sprite.angle == original_angle

    def test_follow_path_until_rotation_horizontal_path(self):
        """Test sprite rotation follows horizontal path correctly."""
        sprite = create_test_sprite()
        sprite.angle = 45  # Start with non-zero angle

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite, control_points, 100, infinite, rotate_with_path=True, tag="test_horizontal_rotation"
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing right (0 degrees)
        # Allow small tolerance for floating point math
        assert abs(sprite.angle) < 1.0

    def test_follow_path_until_rotation_vertical_path(self):
        """Test sprite rotation follows vertical path correctly."""
        sprite = create_test_sprite()

        # Vertical path from bottom to top
        control_points = [(100, 100), (100, 200)]
        action = follow_path_until(
            sprite, control_points, 100, infinite, rotate_with_path=True, tag="test_vertical_rotation"
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing up (90 degrees)
        assert abs(sprite.angle - 90) < 1.0

    def test_follow_path_until_rotation_diagonal_path(self):
        """Test sprite rotation follows diagonal path correctly."""
        sprite = create_test_sprite()

        # Diagonal path from bottom-left to top-right (45 degrees)
        control_points = [(100, 100), (200, 200)]
        action = follow_path_until(
            sprite, control_points, 100, infinite, rotate_with_path=True, tag="test_diagonal_rotation"
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Sprite should be pointing at 45 degrees
        assert abs(sprite.angle - 45) < 1.0

    def test_follow_path_until_rotation_with_offset(self):
        """Test sprite rotation with calibration offset."""
        sprite = create_test_sprite()

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        # Use -90 offset (sprite artwork points up by default)
        action = follow_path_until(
            sprite,
            control_points,
            100,
            infinite,
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

    def test_follow_path_until_rotation_offset_only_when_rotating(self):
        """Test rotation offset is only applied when rotate_with_path is True."""
        sprite = create_test_sprite()
        original_angle = sprite.angle

        # Horizontal path with offset but rotation disabled
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points,
            100,
            infinite,
            rotate_with_path=False,
            rotation_offset=-90,
            tag="test_no_rotation_with_offset",
        )

        # Update several frames
        for _ in range(10):
            Action.update_all(0.016)

        # Sprite angle should not have changed (rotation disabled)
        assert sprite.angle == original_angle

    def test_follow_path_until_rotation_curved_path(self):
        """Test sprite rotation follows curved path correctly."""
        sprite = create_test_sprite()

        # Curved path - quadratic Bezier curve
        control_points = [(100, 100), (150, 200), (200, 100)]
        action = follow_path_until(
            sprite, control_points, 100, infinite, rotate_with_path=True, tag="test_curved_rotation"
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

    def test_follow_path_until_rotation_large_offset(self):
        """Test sprite rotation with large offset values."""
        sprite = create_test_sprite()

        # Horizontal path with large offset
        control_points = [(100, 100), (200, 100)]
        action = follow_path_until(
            sprite,
            control_points,
            100,
            infinite,
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

    def test_follow_path_until_rotation_negative_offset(self):
        """Test sprite rotation with negative offset values."""
        sprite = create_test_sprite()

        # Vertical path with negative offset
        control_points = [(100, 100), (100, 200)]
        action = follow_path_until(
            sprite,
            control_points,
            100,
            infinite,
            rotate_with_path=True,
            rotation_offset=-45,
            tag="test_negative_offset",
        )

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Expected: 90 (up direction) + (-45 offset) = 45 degrees
        assert abs(sprite.angle - 45) < 1.0

    def test_follow_path_until_clone_preserves_rotation_params(self):
        """Test cloning preserves rotation parameters."""
        sprite = create_test_sprite()
        control_points = [(100, 100), (200, 100)]
        original = follow_path_until(
            sprite,
            control_points,
            100,
            infinite,
            rotate_with_path=True,
            rotation_offset=-90,
            tag="test_rotation_params",
        )

        cloned = original.clone()

        assert cloned.rotate_with_path == True
        assert cloned.rotation_offset == -90


class TestRotateUntil:
    """Test suite for RotateUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_rotate_until_basic(self):
        """Test basic RotateUntil functionality."""
        sprite = create_test_sprite()

        target_reached = False

        def condition():
            return target_reached

        action = rotate_until(sprite, 90, condition, tag="test_basic")

        Action.update_all(0.016)

        # RotateUntil uses degrees per frame at 60 FPS semantics
        assert sprite.change_angle == 90

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done

    def test_rotate_until_frame_based_semantics(self):
        """Test that RotateUntil uses degrees per frame at 60 FPS semantics."""
        sprite = create_test_sprite()

        # 3 degrees per frame should rotate 3 degrees when sprite.update() is called
        action = rotate_until(sprite, 3, infinite, tag="test_frame_semantics")

        # Update action to apply angular velocity
        Action.update_all(0.016)
        assert sprite.change_angle == 3  # Raw frame-based value

        # Rotate sprite using its angular velocity
        start_angle = sprite.angle
        sprite.update()  # Arcade applies change_angle to angle

        # Should have rotated exactly 3 degrees
        angle_rotated = sprite.angle - start_angle
        assert angle_rotated == 3.0

    def test_rotate_until_angular_velocity_values(self):
        """Test that RotateUntil sets angular velocity values directly (degrees per frame at 60 FPS)."""
        sprite = create_test_sprite()

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

            action = rotate_until(sprite, input_angular_velocity, infinite, tag="test_velocity")
            Action.update_all(0.016)

            assert sprite.change_angle == input_angular_velocity, f"Failed for input {input_angular_velocity}"


class TestScaleUntil:
    """Test suite for ScaleUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_scale_until_basic(self):
        """Test basic ScaleUntil functionality."""
        sprite = create_test_sprite()
        start_scale = sprite.scale

        target_reached = False

        def condition():
            return target_reached

        action = scale_until(sprite, 0.5, condition, tag="test_basic")

        Action.update_all(0.016)

        # Should be scaling
        assert sprite.scale != start_scale

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestFadeUntil:
    """Test suite for FadeUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_fade_until_basic(self):
        """Test basic FadeUntil functionality."""
        sprite = create_test_sprite()
        start_alpha = sprite.alpha

        target_reached = False

        def condition():
            return target_reached

        action = fade_until(sprite, -100, condition, tag="test_basic")

        Action.update_all(0.016)

        # Should be fading
        assert sprite.alpha != start_alpha

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestBlinkUntil:
    """Test suite for BlinkUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_blink_until_basic(self):
        """Test basic BlinkUntil functionality."""
        sprite = create_test_sprite()

        target_reached = False

        def condition():
            return target_reached

        action = blink_until(sprite, 0.05, condition, tag="test_basic")

        Action.update_all(0.016)

        # Update several times to trigger blinking
        for _ in range(10):
            Action.update_all(0.016)

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestDelayUntil:
    """Test suite for DelayUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_delay_until_basic(self):
        """Test basic DelayUntil functionality."""
        sprite = create_test_sprite()

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = delay_until(sprite, condition, tag="test_basic")

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


class TestTweenUntil:
    """Test suite for TweenUntil action - Direct property animation from start to end value."""

    def teardown_method(self):
        Action.stop_all()

    def test_tween_until_basic_property_animation(self):
        """Test TweenUntil for precise A-to-B property animation."""
        sprite = create_test_sprite()
        sprite.center_x = 0

        # Direct property animation from 0 to 100 over 1 second
        action = tween_until(sprite, 0, 100, "center_x", duration(1.0), tag="test_basic")

        # At halfway point, should be partway through
        Action.update_all(0.5)
        assert 0 < sprite.center_x < 100

        # At completion, should be exactly at end value and done
        Action.update_all(0.5)
        assert sprite.center_x == 100
        assert action.done

    def test_tween_until_custom_easing(self):
        sprite = create_test_sprite()
        sprite.center_x = 0

        def ease_quad(t):
            return t * t

        action = tween_until(
            sprite, 0, 100, "center_x", duration(1.0), ease_function=ease_quad, tag="test_custom_easing"
        )
        Action.update_all(0.5)
        # Should be less than linear at t=0.5
        assert sprite.center_x < 50
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_tween_until_ui_and_effect_animations(self):
        """Test TweenUntil for typical UI and visual effect use cases."""
        sprite = create_test_sprite()

        # Button rotation feedback animation
        sprite.angle = 0
        rotation_feedback = tween_until(sprite, 0, 90, "angle", duration(1.0), tag="test_ui_animation")
        Action.update_all(1.0)
        assert sprite.angle == 90

        # Fade-in effect animation
        sprite.alpha = 0
        fade_in = tween_until(sprite, 0, 255, "alpha", duration(1.0), tag="test_fade_in")
        Action.update_all(1.0)
        assert sprite.alpha == 255

    def test_tween_until_sprite_list(self):
        sprites = create_test_sprite_list()
        for s in sprites:
            s.center_x = 0
        action = tween_until(sprites, 0, 100, "center_x", duration(1.0), tag="test_sprite_list")
        Action.update_all(1.0)
        for s in sprites:
            assert s.center_x == 100

    def test_tween_until_set_factor(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        action = tween_until(sprite, 0, 100, "center_x", duration(1.0), tag="test_set_factor")
        action.set_factor(0.0)  # Pause
        Action.update_all(0.5)
        assert sprite.center_x == 0
        action.set_factor(1.0)  # Resume
        Action.update_all(1.0)
        assert sprite.center_x == 100
        action = tween_until(sprite, 0, 100, "center_x", duration(1.0), tag="test_set_factor_again")
        action.set_factor(2.0)  # Double speed
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_tween_until_completion_and_callback(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        called = {}

        def on_complete(data=None):
            called["done"] = True

        action = tween_until(sprite, 0, 100, "center_x", duration(1.0), on_stop=on_complete, tag="test_on_complete")

        # At halfway point, should be partway through
        Action.update_all(0.5)
        assert not called

        # At completion, should be exactly at end value and callback called
        Action.update_all(0.5)
        assert sprite.center_x == 100
        assert called["done"]

    def test_tween_until_invalid_property(self):
        """Test TweenUntil behavior with invalid property names."""
        sprite = create_test_sprite()

        # Arcade sprites are permissive and allow setting arbitrary attributes
        # so this test demonstrates that TweenUntil can work with any property name
        action = tween_until(sprite, 0, 100, "custom_property", duration(1.0), tag="test_invalid_property")
        Action.update_all(1.0)

        # The sprite should now have the custom property set to the end value
        assert sprite.custom_property == 100
        assert action.done

    def test_tween_until_negative_duration(self):
        sprite = create_test_sprite()
        with pytest.raises(ValueError):
            action = tween_until(sprite, 0, 100, "center_x", duration(-1.0), tag="test_negative_duration")

    def test_tween_until_vs_ease_comparison(self):
        """Test demonstrating when to use TweenUntil vs Ease."""
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite1.center_x = 0
        sprite2.center_x = 0

        # TweenUntil: Perfect for UI panel slide-in (precise A-to-B movement)
        ui_slide = tween_until(sprite1, 0, 200, "center_x", duration(1.0), tag="test_ui_animation")

        # Ease: Perfect for missile launch (smooth acceleration to cruise speed)
        from actions.easing import Ease

        missile_move = move_until(sprite2, (200, 0), infinite, tag="test_missile_move")
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

    def test_tween_until_start_equals_end(self):
        sprite = create_test_sprite()
        sprite.center_x = 42
        action = tween_until(sprite, 42, 42, "center_x", duration(1.0), tag="test_start_equals_end")
        Action.update_all(1.0)
        assert sprite.center_x == 42
        assert action.done

    def test_tween_until_clone(self):
        sprite = create_test_sprite()
        action = tween_until(sprite, 0, 100, "center_x", duration(1.0), tag="test_clone")
        clone = action.clone()
        assert isinstance(clone, type(action))
        assert clone.start_value == 0
        assert clone.end_value == 100
        assert clone.property_name == "center_x"

    def test_tween_until_zero_duration(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        action = tween_until(sprite, 0, 100, "center_x", duration(0.0), tag="test_zero_duration")
        assert sprite.center_x == 100
        assert action.done
