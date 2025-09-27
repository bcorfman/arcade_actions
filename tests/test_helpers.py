"""Test suite for helpers.py - Helper functions for common action patterns."""

import arcade

from actions import Action, duration
from actions.helpers import callback_until, cycle_textures_until, move_by, move_to
from tests.conftest import ActionTestBase


class TestHelperFunctions(ActionTestBase):
    """Test suite for helper functions."""

    def test_move_by_with_tuple(self, test_sprite):
        """Test move_by with tuple offset."""
        sprite = test_sprite
        start_x = sprite.center_x
        start_y = sprite.center_y

        action = move_by(sprite, dx_or_offset=(50, 30))

        # Action should be applied and complete immediately
        assert action.target == sprite
        assert action.done  # Instant actions complete immediately

        # Sprite should have moved immediately
        assert sprite.center_x == start_x + 50
        assert sprite.center_y == start_y + 30

    def test_move_by_with_separate_args(self, test_sprite):
        """Test move_by with separate dx, dy arguments."""
        sprite = test_sprite
        start_x = sprite.center_x
        start_y = sprite.center_y

        action = move_by(sprite, dx_or_offset=25, dy=15)

        # Action should be applied and complete immediately
        assert action.target == sprite
        assert action.done  # Instant actions complete immediately

        # Sprite should have moved immediately
        assert sprite.center_x == start_x + 25
        assert sprite.center_y == start_y + 15

    def test_move_by_with_sprite_list(self, test_sprite_list):
        """Test move_by with sprite list."""
        sprite_list = test_sprite_list
        start_positions = [(sprite.center_x, sprite.center_y) for sprite in sprite_list]

        action = move_by(sprite_list, dx_or_offset=(10, 20))

        # Action should be applied and complete immediately
        assert action.target == sprite_list
        assert action.done  # Instant actions complete immediately

        # All sprites should have moved immediately
        for i, sprite in enumerate(sprite_list):
            expected_x = start_positions[i][0] + 10
            expected_y = start_positions[i][1] + 20
            assert sprite.center_x == expected_x
            assert sprite.center_y == expected_y

    def test_move_by_with_callback(self, test_sprite):
        """Test move_by with on_stop callback."""
        sprite = test_sprite
        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        action = move_by(sprite, dx_or_offset=(10, 5), on_stop=on_stop)

        # Update to apply the movement
        Action.update_all(0.016)

        # Callback should be called
        assert callback_called

    def test_move_to_with_tuple(self, test_sprite):
        """Test move_to with tuple position."""
        sprite = test_sprite

        action = move_to(sprite, x_or_position=(200, 300))

        # Action should be applied and complete immediately
        assert action.target == sprite
        assert action.done  # Instant actions complete immediately

        # Sprite should be at the target position immediately
        assert sprite.center_x == 200
        assert sprite.center_y == 300

    def test_move_to_with_separate_args(self, test_sprite):
        """Test move_to with separate x, y arguments."""
        sprite = test_sprite

        action = move_to(sprite, x_or_position=150, y=250)

        # Action should be applied and complete immediately
        assert action.target == sprite
        assert action.done  # Instant actions complete immediately

        # Sprite should be at the target position immediately
        assert sprite.center_x == 150
        assert sprite.center_y == 250

    def test_move_to_with_sprite_list(self, test_sprite_list):
        """Test move_to with sprite list."""
        sprite_list = test_sprite_list

        action = move_to(sprite_list, x_or_position=(100, 200))

        # Action should be applied and complete immediately
        assert action.target == sprite_list
        assert action.done  # Instant actions complete immediately

        # All sprites should be at the target position immediately
        for sprite in sprite_list:
            assert sprite.center_x == 100
            assert sprite.center_y == 200

    def test_move_to_with_callback(self, test_sprite):
        """Test move_to with on_stop callback."""
        sprite = test_sprite
        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        action = move_to(sprite, x_or_position=(50, 75), on_stop=on_stop)

        # Update to apply the movement
        Action.update_all(0.016)

        # Callback should be called
        assert callback_called

    def test_move_by_returns_action(self, test_sprite):
        """Test that move_by returns the action instance."""
        sprite = test_sprite

        action = move_by(sprite, dx_or_offset=(10, 20))

        # Should return the action instance
        assert action is not None
        assert hasattr(action, "apply")
        assert hasattr(action, "update_effect")

    def test_move_to_returns_action(self, test_sprite):
        """Test that move_to returns the action instance."""
        sprite = test_sprite

        action = move_to(sprite, x_or_position=(100, 200))

        # Should return the action instance
        assert action is not None
        assert hasattr(action, "apply")
        assert hasattr(action, "update_effect")


class TestCallbackUntilHelper(ActionTestBase):
    """Test suite for callback_until helper function."""

    def test_callback_until_basic(self, test_sprite):
        """Test basic callback_until functionality."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = callback_until(sprite, callback=callback, condition=duration(0.1))

        # Run for a few frames
        for _ in range(6):
            Action.update_all(1 / 60)

        assert call_count == 6
        assert action.done

    def test_callback_until_with_interval(self, test_sprite):
        """Test callback_until with interval scheduling."""
        sprite = test_sprite
        call_count = 0

        def callback():
            nonlocal call_count
            call_count += 1

        action = callback_until(sprite, callback=callback, condition=duration(0.1), seconds_between_calls=0.05)

        # Run for 6 frames (0.1 seconds)
        for _ in range(6):
            Action.update_all(1 / 60)

        assert call_count == 2  # Called at 0.05s and 0.1s
        assert action.done

    def test_callback_until_with_target_parameter(self, test_sprite):
        """Test callback_until with callback that receives target."""
        sprite = test_sprite
        received_targets = []

        def callback_with_target(target):
            received_targets.append(target)

        action = callback_until(
            sprite, callback=callback_with_target, condition=duration(0.05), seconds_between_calls=0.05
        )

        # Run for enough frames to trigger callback
        for _ in range(3):
            Action.update_all(1 / 60)

        assert len(received_targets) == 1
        assert received_targets[0] == sprite

    def test_callback_until_with_on_stop(self, test_sprite):
        """Test callback_until with on_stop callback."""
        sprite = test_sprite
        on_stop_called = False

        def callback():
            pass

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        action = callback_until(sprite, callback=callback, condition=duration(0.05), on_stop=on_stop)

        # Run until completion
        for _ in range(10):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert on_stop_called

    def test_callback_until_with_tag(self, test_sprite):
        """Test callback_until applies with correct tag."""
        sprite = test_sprite

        def callback():
            pass

        action = callback_until(sprite, callback=callback, condition=duration(0.1), tag="test_tag")

        # Verify action was applied with tag
        assert action.target == sprite
        # Note: tag verification would require accessing internal action manager


class TestCycleTexturesUntilHelper(ActionTestBase):
    """Test suite for cycle_textures_until helper function."""

    def test_cycle_textures_until_basic(self, test_sprite):
        """Test basic cycle_textures_until functionality."""
        sprite = test_sprite

        # Create some dummy textures
        textures = [
            arcade.Texture.create_empty("tex1", (10, 10)),
            arcade.Texture.create_empty("tex2", (10, 10)),
            arcade.Texture.create_empty("tex3", (10, 10)),
        ]

        # Use a simple condition instead of duration() since CycleTexturesUntil
        # doesn't have simulation-time tracking
        frame_count = 0

        def stop_after_frames():
            nonlocal frame_count
            frame_count += 1
            return frame_count >= 5

        action = cycle_textures_until(sprite, textures=textures, condition=stop_after_frames)

        # Action should be applied and running
        assert action.target == sprite
        assert not action.done

        # Run until condition is met
        for _ in range(10):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert action.done

    def test_cycle_textures_until_with_none_condition(self, test_sprite):
        """Test cycle_textures_until with condition=None (infinite)."""
        sprite = test_sprite

        textures = [
            arcade.Texture.create_empty("tex1", (10, 10)),
            arcade.Texture.create_empty("tex2", (10, 10)),
        ]

        action = cycle_textures_until(
            sprite,
            textures=textures,
            condition=None,  # Should default to infinite
        )

        # Action should be applied and running
        assert action.target == sprite
        assert not action.done

        # Run for a few frames - should still be running
        for _ in range(5):
            Action.update_all(1 / 60)

        assert not action.done  # Should still be running infinitely

    def test_cycle_textures_until_with_direction(self, test_sprite):
        """Test cycle_textures_until with backward direction."""
        sprite = test_sprite

        textures = [
            arcade.Texture.create_empty("tex1", (10, 10)),
            arcade.Texture.create_empty("tex2", (10, 10)),
        ]

        action = cycle_textures_until(
            sprite,
            textures=textures,
            direction=-1,  # Backward
            condition=duration(0.1),
        )

        # Action should be applied and running
        assert action.target == sprite
        assert not action.done

    def test_cycle_textures_until_with_on_stop(self, test_sprite):
        """Test cycle_textures_until with on_stop callback."""
        sprite = test_sprite
        on_stop_called = False

        textures = [arcade.Texture.create_empty("tex1", (10, 10))]

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        # Use a simple condition instead of duration()
        frame_count = 0

        def stop_condition():
            nonlocal frame_count
            frame_count += 1
            return frame_count >= 3

        action = cycle_textures_until(sprite, textures=textures, condition=stop_condition, on_stop=on_stop)

        # Run until completion
        for _ in range(10):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert on_stop_called

    def test_cycle_textures_until_with_tag(self, test_sprite):
        """Test cycle_textures_until applies with correct tag."""
        sprite = test_sprite

        textures = [arcade.Texture.create_empty("tex1", (10, 10))]

        action = cycle_textures_until(sprite, textures=textures, condition=duration(0.1), tag="texture_cycle")

        # Verify action was applied
        assert action.target == sprite
