"""
Tests for SpriteList support in helper functions.

This test module ensures that all helper functions that should support SpriteList
targets actually do so, preventing regressions where they might be incorrectly
typed to only accept individual Sprites.
"""

import arcade

from actions import (
    Action,
    blink_until,
    delay_until,
    ease,
    fade_until,
    move_until,
    rotate_until,
    scale_until,
    tween_until,
)
from actions.conditional import MoveUntil, duration


class TestHelperFunctionSpriteListSupport:
    """Test that all helper functions support SpriteList targets."""

    def setup_method(self):
        """Set up test fixtures."""
        Action.clear_all()

        # Create test sprites and sprite list
        self.sprite1 = arcade.Sprite()
        self.sprite1.center_x = 100
        self.sprite1.center_y = 100

        self.sprite2 = arcade.Sprite()
        self.sprite2.center_x = 200
        self.sprite2.center_y = 200

        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite1)
        self.sprite_list.append(self.sprite2)

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_move_until_supports_sprite_list(self):
        """Test that move_until helper supports SpriteList targets."""
        action = move_until(self.sprite_list, (5, 0), duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

        # Verify it applies to all sprites in the list
        Action.update_all(1 / 60.0)
        assert self.sprite1.change_x == 5
        assert self.sprite2.change_x == 5

    def test_rotate_until_supports_sprite_list(self):
        """Test that rotate_until helper supports SpriteList targets."""
        action = rotate_until(self.sprite_list, 90, duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

        # Verify it applies to all sprites in the list
        Action.update_all(1 / 60.0)
        assert self.sprite1.change_angle == 90
        assert self.sprite2.change_angle == 90

    def test_tween_until_supports_sprite_list(self):
        """Test that tween_until helper supports SpriteList targets."""
        # This was the main regression - tween_until was typed for Sprite only
        action = tween_until(
            self.sprite_list, start_value=0, end_value=10, property_name="change_y", condition_func=duration(0.1)
        )

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

        # Verify it applies to all sprites in the list
        Action.update_all(1 / 60.0)
        assert self.sprite1.change_y != 0  # Should be tweening
        assert self.sprite2.change_y != 0  # Should be tweening
        assert self.sprite1.change_y == self.sprite2.change_y  # Should be same value

    def test_blink_until_supports_sprite_list(self):
        """Test that blink_until helper supports SpriteList targets."""
        action = blink_until(self.sprite_list, 0.1, duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

    def test_delay_until_supports_sprite_list(self):
        """Test that delay_until helper supports SpriteList targets."""
        action = delay_until(self.sprite_list, duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

    def test_fade_until_supports_sprite_list(self):
        """Test that fade_until helper supports SpriteList targets."""
        action = fade_until(self.sprite_list, -50, duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

    def test_scale_until_supports_sprite_list(self):
        """Test that scale_until helper supports SpriteList targets."""
        action = scale_until(self.sprite_list, 2.0, duration(1.0))

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 1

    def test_ease_supports_sprite_list(self):
        """Test that ease helper supports SpriteList targets."""
        base_action = MoveUntil((5, 0), lambda: False)
        action = ease(self.sprite_list, base_action, 1.0)

        assert action.target == self.sprite_list
        assert len(Action._active_actions) == 2  # Ease wrapper + wrapped action

    def test_all_helpers_accept_both_sprite_and_sprite_list(self):
        """Comprehensive test that all helpers accept both Sprite and SpriteList."""

        # Test with individual sprite
        move_until(self.sprite1, (1, 0), duration(0.1))
        rotate_until(self.sprite1, 45, duration(0.1))
        tween_until(self.sprite1, 0, 5, "center_x", duration(0.1))
        blink_until(self.sprite1, 0.1, duration(0.1))
        delay_until(self.sprite1, duration(0.1))
        fade_until(self.sprite1, -10, duration(0.1))
        scale_until(self.sprite1, 1.5, duration(0.1))

        sprite_actions = len(Action._active_actions)

        # Test with sprite list
        move_until(self.sprite_list, (1, 0), duration(0.1))
        rotate_until(self.sprite_list, 45, duration(0.1))
        tween_until(self.sprite_list, 0, 5, "center_x", duration(0.1))
        blink_until(self.sprite_list, 0.1, duration(0.1))
        delay_until(self.sprite_list, duration(0.1))
        fade_until(self.sprite_list, -10, duration(0.1))
        scale_until(self.sprite_list, 1.5, duration(0.1))

        # Should have double the actions now
        assert len(Action._active_actions) == sprite_actions * 2
