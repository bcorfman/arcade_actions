"""Tests for validation and edge cases in formation.py."""

import arcade
import pytest

from actions.base import Action
from actions.formation import arrange_circle, arrange_line


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestArrangeLineValidation:
    """Test validation in arrange_line function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_arrange_line_both_sprites_and_count(self):
        """Test that specifying both sprites and count raises ValueError - line 66."""
        sprites = [create_test_sprite() for _ in range(5)]

        with pytest.raises(ValueError, match="Cannot specify both 'sprites' and 'count'"):
            arrange_line(sprites=sprites, count=5)


class TestArrangeCircleValidation:
    """Test validation in arrange_circle function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_arrange_circle_both_sprites_and_count(self):
        """Test that specifying both sprites and count raises ValueError - line 219."""
        sprites = [create_test_sprite() for _ in range(6)]

        with pytest.raises(ValueError, match="Cannot specify both 'sprites' and 'count'"):
            arrange_circle(sprites=sprites, count=6, center_x=400, center_y=300, radius=100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
