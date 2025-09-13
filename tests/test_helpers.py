"""Test suite for helpers.py - Helper functions for common action patterns."""

from actions import Action
from actions.helpers import move_by, move_to
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
