"""Test suite for condition_actions.py - Conditional actions."""

import arcade
import pytest

from actions import (
    Action,
    BlinkUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
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
        action.apply(sprite)

        Action.update_all(0.016)

        # Sprite should start moving along the path
        assert sprite.position != start_pos

    def test_follow_path_until_completion(self):
        """Test FollowPathUntil completes when reaching end of path."""
        sprite = create_test_sprite()
        control_points = [(100, 100), (200, 100)]  # Simple straight line

        action = FollowPathUntil(control_points, 1000, lambda: False)  # High velocity
        action.apply(sprite)

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

        action = BlinkUntil(10.0, condition)  # 10 blinks per second
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
