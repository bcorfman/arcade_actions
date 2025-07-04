"""Test suite for condition_actions.py - Conditional actions."""

import arcade
import pytest

from actions import (
    Action,
    BlinkUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    InterpolateUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    duration,
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
        Action.clear_all()

    def test_move_until_basic(self):
        """Test basic MoveUntil functionality."""
        sprite = create_test_sprite()
        start_x = sprite.center_x

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = MoveUntil((100, 0), condition)
        action.apply(sprite)

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

        action = MoveUntil((100, 0), condition, on_stop)
        action.apply(sprite)

        Action.update_all(0.016)

        assert callback_called
        assert callback_data == {"reason": "collision", "damage": 10}

    def test_move_until_sprite_list(self):
        """Test MoveUntil with SpriteList."""
        sprite_list = create_test_sprite_list()

        action = MoveUntil((50, 25), lambda: False)
        action.apply(sprite_list)

        Action.update_all(0.016)

        # Both sprites should have the same velocity
        for sprite in sprite_list:
            assert sprite.change_x == 50
            assert sprite.change_y == 25

    def test_move_until_set_current_velocity(self):
        """Test MoveUntil set_current_velocity method."""
        sprite = create_test_sprite()
        action = MoveUntil((100, 0), lambda: False)
        action.apply(sprite)

        # Initial velocity should be set
        Action.update_all(0.016)
        assert sprite.change_x == 100

        # Change velocity
        action.set_current_velocity((50, 25))
        assert sprite.change_x == 50
        assert sprite.change_y == 25


class TestFollowPathUntil:
    """Test suite for FollowPathUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_follow_path_until_basic(self):
        """Test basic FollowPathUntil functionality."""
        sprite = create_test_sprite()
        start_pos = sprite.position

        control_points = [(100, 100), (200, 200), (300, 100)]
        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = FollowPathUntil(control_points, 100, condition)
        action.apply(sprite, tag="test_basic_path")

        Action.update_all(0.016)

        # Sprite should start moving along the path
        assert sprite.position != start_pos

    def test_follow_path_until_completion(self):
        """Test FollowPathUntil completes when reaching end of path."""
        sprite = create_test_sprite()
        control_points = [(100, 100), (200, 100)]  # Simple straight line

        action = FollowPathUntil(control_points, 1000, lambda: False)  # High velocity
        action.apply(sprite, tag="test_path_completion")

        # Update until path is complete
        for _ in range(100):
            Action.update_all(0.016)
            if action.done:
                break

        assert action.done

    def test_follow_path_until_requires_points(self):
        """Test FollowPathUntil requires at least 2 control points."""
        with pytest.raises(ValueError):
            FollowPathUntil([(100, 100)], 100, lambda: False)

    def test_follow_path_until_no_rotation_by_default(self):
        """Test FollowPathUntil doesn't rotate sprite by default."""
        sprite = create_test_sprite()
        original_angle = sprite.angle

        # Horizontal path from left to right
        control_points = [(100, 100), (200, 100)]
        action = FollowPathUntil(control_points, 100, lambda: False)
        action.apply(sprite, tag="test_no_rotation")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True)
        action.apply(sprite, tag="test_horizontal_rotation")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True)
        action.apply(sprite, tag="test_vertical_rotation")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True)
        action.apply(sprite, tag="test_diagonal_rotation")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True, rotation_offset=-90)
        action.apply(sprite, tag="test_rotation_offset")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=False, rotation_offset=-90)
        action.apply(sprite, tag="test_no_rotation_with_offset")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True)
        action.apply(sprite, tag="test_curved_rotation")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True, rotation_offset=450)
        action.apply(sprite, tag="test_large_offset")

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
        action = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True, rotation_offset=-45)
        action.apply(sprite, tag="test_negative_offset")

        # Update a few frames to get movement
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Expected: 90 (up direction) + (-45 offset) = 45 degrees
        assert abs(sprite.angle - 45) < 1.0

    def test_follow_path_until_clone_preserves_rotation_params(self):
        """Test cloning preserves rotation parameters."""
        control_points = [(100, 100), (200, 100)]
        original = FollowPathUntil(control_points, 100, lambda: False, rotate_with_path=True, rotation_offset=-90)

        cloned = original.clone()

        assert cloned.rotate_with_path == True
        assert cloned.rotation_offset == -90


class TestRotateUntil:
    """Test suite for RotateUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_rotate_until_basic(self):
        """Test basic RotateUntil functionality."""
        sprite = create_test_sprite()

        target_reached = False

        def condition():
            return target_reached

        action = RotateUntil(90, condition)  # 90 degrees per second
        action.apply(sprite)

        Action.update_all(0.016)

        # Should be rotating
        assert sprite.change_angle == 90

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done


class TestScaleUntil:
    """Test suite for ScaleUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_scale_until_basic(self):
        """Test basic ScaleUntil functionality."""
        sprite = create_test_sprite()
        start_scale = sprite.scale

        target_reached = False

        def condition():
            return target_reached

        action = ScaleUntil(0.5, condition)  # Scale velocity
        action.apply(sprite)

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
        Action.clear_all()

    def test_fade_until_basic(self):
        """Test basic FadeUntil functionality."""
        sprite = create_test_sprite()
        start_alpha = sprite.alpha

        target_reached = False

        def condition():
            return target_reached

        action = FadeUntil(-100, condition)  # Fade out velocity
        action.apply(sprite)

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
        Action.clear_all()

    def test_blink_until_basic(self):
        """Test basic BlinkUntil functionality."""
        sprite = create_test_sprite()

        target_reached = False

        def condition():
            return target_reached

        action = BlinkUntil(0.05, condition)  # toggle every 0.05 seconds (equivalent to 10 blinks per second)
        action.apply(sprite)

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
        Action.clear_all()

    def test_delay_until_basic(self):
        """Test basic DelayUntil functionality."""
        sprite = create_test_sprite()

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = DelayUntil(condition)
        action.apply(sprite)

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


class TestInterpolateUntil:
    """Test suite for InterpolateUntil action."""

    def teardown_method(self):
        Action.clear_all()

    def test_interpolate_until_basic(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        action = InterpolateUntil(0, 100, "center_x", duration(1.0))
        action.apply(sprite)
        Action.update_all(0.5)
        assert 0 < sprite.center_x < 100
        Action.update_all(0.5)
        assert sprite.center_x == 100
        assert action.done

    def test_interpolate_until_custom_easing(self):
        sprite = create_test_sprite()
        sprite.center_x = 0

        def ease_quad(t):
            return t * t

        action = InterpolateUntil(0, 100, "center_x", duration(1.0), ease_function=ease_quad)
        action.apply(sprite)
        Action.update_all(0.5)
        # Should be less than linear at t=0.5
        assert sprite.center_x < 50
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_interpolate_until_other_properties(self):
        sprite = create_test_sprite()
        sprite.angle = 0
        action = InterpolateUntil(0, 90, "angle", duration(1.0))
        action.apply(sprite)
        Action.update_all(1.0)
        assert sprite.angle == 90
        sprite.alpha = 0
        action2 = InterpolateUntil(0, 255, "alpha", duration(1.0))
        action2.apply(sprite)
        Action.update_all(1.0)
        assert sprite.alpha == 255

    def test_interpolate_until_sprite_list(self):
        sprites = create_test_sprite_list()
        for s in sprites:
            s.center_x = 0
        action = InterpolateUntil(0, 100, "center_x", duration(1.0))
        action.apply(sprites)
        Action.update_all(1.0)
        for s in sprites:
            assert s.center_x == 100

    def test_interpolate_until_set_factor(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        action = InterpolateUntil(0, 100, "center_x", duration(1.0))
        action.apply(sprite)
        action.set_factor(0.0)  # Pause
        Action.update_all(0.5)
        assert sprite.center_x == 0
        action.set_factor(1.0)  # Resume
        Action.update_all(1.0)
        assert sprite.center_x == 100
        action = InterpolateUntil(0, 100, "center_x", duration(1.0))
        action.apply(sprite)
        action.set_factor(2.0)  # Double speed
        Action.update_all(0.5)
        assert sprite.center_x == 100

    def test_interpolate_until_completion_and_callback(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        called = {}

        def on_complete(data=None):
            called["done"] = True

        action = InterpolateUntil(0, 100, "center_x", duration(1.0), on_condition_met=on_complete)
        action.apply(sprite)
        Action.update_all(1.0)
        assert action.done
        assert called.get("done")

    def test_interpolate_until_invalid_property(self):
        sprite = create_test_sprite()
        with pytest.raises(AttributeError):
            action = InterpolateUntil(0, 100, "not_a_property", duration(1.0))
            action.apply(sprite)
            Action.update_all(1.0)

    def test_interpolate_until_negative_duration(self):
        sprite = create_test_sprite()
        action = InterpolateUntil(0, 100, "center_x", duration(-1.0))
        with pytest.raises(ValueError):
            action.apply(sprite)

    def test_interpolate_until_start_equals_end(self):
        sprite = create_test_sprite()
        sprite.center_x = 42
        action = InterpolateUntil(42, 42, "center_x", duration(1.0))
        action.apply(sprite)
        Action.update_all(1.0)
        assert sprite.center_x == 42
        assert action.done

    def test_interpolate_until_clone(self):
        sprite = create_test_sprite()
        action = InterpolateUntil(0, 100, "center_x", duration(1.0))
        clone = action.clone()
        assert isinstance(clone, InterpolateUntil)
        assert clone.start_value == 0
        assert clone.end_value == 100
        assert clone.property_name == "center_x"

    def test_interpolate_until_zero_duration(self):
        sprite = create_test_sprite()
        sprite.center_x = 0
        action = InterpolateUntil(0, 100, "center_x", duration(0.0))
        action.apply(sprite)
        assert sprite.center_x == 100
        assert action.done
