"""Test suite for condition-based actions (MoveUntil, RotateUntil, etc.)."""

import arcade
from arcade.texture import Texture

from actions.move_until import (
    Action,
    DelayUntil,
    FadeUntil,
    MoveUntil,
    MoveWhile,
    RotateUntil,
    ScaleUntil,
    Sequence,
    Spawn,
    duration_condition,
)


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with a 1x1 transparent texture for testing."""
    texture = Texture.create_empty("test", (1, 1))
    sprite = arcade.Sprite()
    sprite.texture = texture
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestActionGlobalManagement:
    """Test the global action management system."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_global_action_registration(self):
        """Test that actions are registered globally."""
        sprite = create_test_sprite()
        action = MoveUntil((100, 0), lambda: False)
        action.apply(sprite)

        assert len(Action._active_actions) == 1
        assert action in Action._active_actions

    def test_global_action_cleanup(self):
        """Test that completed actions are cleaned up."""
        sprite = create_test_sprite()
        action = MoveUntil((100, 0), lambda: True)  # Condition immediately true
        action.apply(sprite)

        Action.update_all(0.016)  # One frame
        assert len(Action._active_actions) == 0

    def test_stop_all_actions(self):
        """Test stopping all actions at once."""
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()

        action1 = MoveUntil((100, 0), lambda: False)
        action2 = RotateUntil(90, lambda: False)

        action1.apply(sprite1)
        action2.apply(sprite2)

        assert len(Action._active_actions) == 2

        Action.stop_all()
        assert len(Action._active_actions) == 0


class TestMoveUntil:
    """Test MoveUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_until_basic(self):
        """Test basic MoveUntil functionality."""
        sprite = create_test_sprite()
        start_x = sprite.center_x

        # Move for a fixed duration
        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = MoveUntil((100, 0), condition)
        action.apply(sprite)

        # Update for one frame - sprite should move
        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 0

        # Let it move for a bit
        sprite.update()  # Apply velocity to position
        assert sprite.center_x > start_x

        # Trigger condition
        condition_met = True
        Action.update_all(0.016)

        # Velocity should be zeroed
        assert sprite.change_x == 0
        assert sprite.change_y == 0

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
        sprite_list = arcade.SpriteList()
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        action = MoveUntil((50, 25), lambda: False)
        action.apply(sprite_list)

        Action.update_all(0.016)

        # Both sprites should have the same velocity
        assert sprite1.change_x == 50
        assert sprite1.change_y == 25
        assert sprite2.change_x == 50
        assert sprite2.change_y == 25


class TestMoveWhile:
    """Test MoveWhile action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_while_basic(self):
        """Test MoveWhile stops when condition becomes False."""
        sprite = create_test_sprite()

        condition_active = True

        def condition():
            return condition_active

        action = MoveWhile((100, 0), condition)
        action.apply(sprite)

        # Should move while condition is True
        Action.update_all(0.016)
        assert sprite.change_x == 100

        # Stop condition
        condition_active = False
        Action.update_all(0.016)
        assert sprite.change_x == 0


class TestRotateUntil:
    """Test RotateUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_rotate_until_basic(self):
        """Test basic RotateUntil functionality."""
        sprite = create_test_sprite()
        start_angle = sprite.angle

        target_reached = False

        def condition():
            return target_reached

        action = RotateUntil(90, condition)  # 90 degrees per second
        action.apply(sprite)

        Action.update_all(1.0)  # Update for 1 second
        sprite.update()  # Apply rotation

        # Should have rotated 90 degrees
        assert abs(sprite.angle - (start_angle + 90)) < 1.0

        target_reached = True
        Action.update_all(0.016)

        # Should stop rotating
        assert sprite.change_angle == 0


class TestScaleUntil:
    """Test ScaleUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_scale_until_basic(self):
        """Test basic ScaleUntil functionality."""
        sprite = create_test_sprite()
        sprite.scale = 1.0

        condition_met = False

        def condition():
            return condition_met

        action = ScaleUntil((0.5, 0.5), condition)  # Scale by 0.5 per second
        action.apply(sprite)

        Action.update_all(1.0)  # Update for 1 second

        # Should have scaled
        assert sprite.scale != 1.0  # Scale should have changed

        condition_met = True
        Action.update_all(0.016)

        # Should stop scaling (this requires checking internal state)
        assert action.done


class TestFadeUntil:
    """Test FadeUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_fade_until_basic(self):
        """Test basic FadeUntil functionality."""
        sprite = create_test_sprite()
        sprite.alpha = 255

        condition_met = False

        def condition():
            return condition_met

        action = FadeUntil(-100, condition)  # Fade out at 100 alpha per second
        action.apply(sprite)

        Action.update_all(1.0)  # Update for 1 second

        # Should have faded
        assert sprite.alpha < 255

        condition_met = True
        Action.update_all(0.016)

        # Should stop fading
        assert action.done


class TestDelayUntil:
    """Test DelayUntil action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_delay_until_basic(self):
        """Test basic DelayUntil functionality."""
        condition_met = False
        callback_called = False

        def condition():
            return condition_met

        def on_complete():
            nonlocal callback_called
            callback_called = True

        action = DelayUntil(condition, on_complete)
        action.apply(None)  # DelayUntil doesn't need a target

        Action.update_all(0.016)
        assert not callback_called

        condition_met = True
        Action.update_all(0.016)
        assert callback_called


class TestSequence:
    """Test Sequence composite action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_basic(self):
        """Test basic Sequence functionality."""
        sprite = create_test_sprite()

        # Create a sequence: move right, then move up
        move_right = MoveUntil((100, 0), duration_condition(0.1))  # 0.1 seconds
        move_up = MoveUntil((0, 100), duration_condition(0.1))  # 0.1 seconds

        sequence = Sequence([move_right, move_up])
        sequence.apply(sprite)

        # First action should start
        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 0

        # Complete first action
        Action.update_all(0.1)
        Action.update_all(0.016)  # Process completion

        # Second action should start
        assert sprite.change_x == 0
        assert sprite.change_y == 100


class TestSpawn:
    """Test Spawn composite action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_spawn_basic(self):
        """Test basic Spawn functionality."""
        sprite = create_test_sprite()

        # Create spawn: move right and rotate simultaneously
        move_action = MoveUntil((100, 0), duration_condition(0.2))
        rotate_action = RotateUntil(90, duration_condition(0.1))

        spawn = Spawn([move_action, rotate_action])
        spawn.apply(sprite)

        # Both actions should start
        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_angle == 90
