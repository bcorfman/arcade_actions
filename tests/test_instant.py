"""Test suite for instant.py - Instant actions for immediate sprite repositioning."""

import pytest

from actions import Action
from actions.instant import MoveBy, MoveTo
from tests.conftest import ActionTestBase


class TestMoveTo(ActionTestBase):
    """Test suite for MoveTo action."""

    def test_move_to_with_tuple(self, test_sprite):
        """Test MoveTo with tuple position."""
        sprite = test_sprite
        sprite.center_x = 100
        sprite.center_y = 200

        action = MoveTo((300, 400))
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 300
        assert sprite.center_y == 400

    def test_move_to_with_separate_args(self, test_sprite):
        """Test MoveTo with separate x, y arguments."""
        sprite = test_sprite
        sprite.center_x = 50
        sprite.center_y = 75

        action = MoveTo(150, 250)
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 150
        assert sprite.center_y == 250

    def test_move_to_with_sprite_list(self, test_sprite_list):
        """Test MoveTo with sprite list."""
        sprite_list = test_sprite_list
        for sprite in sprite_list:
            sprite.center_x = 10
            sprite.center_y = 20

        action = MoveTo((100, 200))
        action.apply(sprite_list)

        # Should complete immediately
        assert action.done
        for sprite in sprite_list:
            assert sprite.center_x == 100
            assert sprite.center_y == 200

    def test_move_to_with_callback(self, test_sprite):
        """Test MoveTo with on_stop callback."""
        sprite = test_sprite
        callback_called = False
        callback_data = None

        def on_stop(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        action = MoveTo((50, 75), on_stop=on_stop)
        action.apply(sprite)

        # Callback should be called
        assert callback_called
        assert callback_data is None  # No data passed for instant actions

    def test_move_to_with_callback_no_data(self, test_sprite):
        """Test MoveTo with callback that doesn't accept data."""
        sprite = test_sprite
        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        action = MoveTo((25, 30), on_stop=on_stop)
        action.apply(sprite)

        # Callback should be called
        assert callback_called

    def test_move_to_invalid_tuple(self, test_sprite):
        """Test MoveTo with invalid tuple."""
        with pytest.raises(ValueError, match="Position must be a tuple/list of \\(x, y\\) coordinates"):
            MoveTo((100,))  # Wrong length

        with pytest.raises(ValueError, match="Position must be a tuple/list of \\(x, y\\) coordinates"):
            MoveTo("invalid")  # Not a tuple/list

    def test_move_to_removes_from_active_actions(self, test_sprite):
        """Test that MoveTo removes itself from active actions."""
        initial_count = len(Action._active_actions)

        action = MoveTo((50, 75))
        action.apply(test_sprite)

        # Should be removed from active actions immediately
        assert len(Action._active_actions) == initial_count


class TestMoveBy(ActionTestBase):
    """Test suite for MoveBy action."""

    def test_move_by_with_tuple(self, test_sprite):
        """Test MoveBy with tuple offset."""
        sprite = test_sprite
        sprite.center_x = 100
        sprite.center_y = 200

        action = MoveBy((50, 75))
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 150  # 100 + 50
        assert sprite.center_y == 275  # 200 + 75

    def test_move_by_with_separate_args(self, test_sprite):
        """Test MoveBy with separate dx, dy arguments."""
        sprite = test_sprite
        sprite.center_x = 200
        sprite.center_y = 300

        action = MoveBy(25, 40)
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 225  # 200 + 25
        assert sprite.center_y == 340  # 300 + 40

    def test_move_by_with_sprite_list(self, test_sprite_list):
        """Test MoveBy with sprite list."""
        sprite_list = test_sprite_list
        for i, sprite in enumerate(sprite_list):
            sprite.center_x = 10 + i * 10
            sprite.center_y = 20 + i * 10

        action = MoveBy((5, 15))
        action.apply(sprite_list)

        # Should complete immediately
        assert action.done
        for i, sprite in enumerate(sprite_list):
            expected_x = 10 + i * 10 + 5
            expected_y = 20 + i * 10 + 15
            assert sprite.center_x == expected_x
            assert sprite.center_y == expected_y

    def test_move_by_with_callback(self, test_sprite):
        """Test MoveBy with on_stop callback."""
        sprite = test_sprite
        callback_called = False
        callback_data = None

        def on_stop(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        action = MoveBy((10, 20), on_stop=on_stop)
        action.apply(sprite)

        # Callback should be called
        assert callback_called
        assert callback_data is None  # No data passed for instant actions

    def test_move_by_with_callback_no_data(self, test_sprite):
        """Test MoveBy with callback that doesn't accept data."""
        sprite = test_sprite
        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        action = MoveBy((5, 10), on_stop=on_stop)
        action.apply(sprite)

        # Callback should be called
        assert callback_called

    def test_move_by_invalid_tuple(self, test_sprite):
        """Test MoveBy with invalid tuple."""
        with pytest.raises(ValueError, match="Offset must be a tuple/list of \\(dx, dy\\) coordinates"):
            MoveBy((100,))  # Wrong length

        with pytest.raises(ValueError, match="Offset must be a tuple/list of \\(dx, dy\\) coordinates"):
            MoveBy("invalid")  # Not a tuple/list

    def test_move_by_removes_from_active_actions(self, test_sprite):
        """Test that MoveBy removes itself from active actions."""
        initial_count = len(Action._active_actions)

        action = MoveBy((25, 30))
        action.apply(test_sprite)

        # Should be removed from active actions immediately
        assert len(Action._active_actions) == initial_count

    def test_move_by_negative_offset(self, test_sprite):
        """Test MoveBy with negative offset."""
        sprite = test_sprite
        sprite.center_x = 100
        sprite.center_y = 200

        action = MoveBy((-25, -50))
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 75  # 100 - 25
        assert sprite.center_y == 150  # 200 - 50

    def test_move_by_zero_offset(self, test_sprite):
        """Test MoveBy with zero offset."""
        sprite = test_sprite
        sprite.center_x = 100
        sprite.center_y = 200

        action = MoveBy((0, 0))
        action.apply(sprite)

        # Should complete immediately
        assert action.done
        assert sprite.center_x == 100  # Unchanged
        assert sprite.center_y == 200  # Unchanged
