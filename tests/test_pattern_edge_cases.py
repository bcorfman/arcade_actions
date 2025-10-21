"""Tests for edge cases and error handling in pattern.py."""

import arcade
import pytest

from actions.base import Action
from actions.pattern import (
    create_figure_eight_pattern,
    create_orbit_pattern,
    create_wave_pattern,
)


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestWavePatternValidation:
    """Test validation in create_wave_pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_wave_pattern_invalid_start_progress_negative(self):
        """Test that start_progress < 0 raises ValueError."""
        with pytest.raises(ValueError, match="start_progress and end_progress must be within"):
            create_wave_pattern(20, 80, 4, start_progress=-0.1)

    def test_wave_pattern_invalid_start_progress_too_large(self):
        """Test that start_progress > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="start_progress and end_progress must be within"):
            create_wave_pattern(20, 80, 4, start_progress=1.1)

    def test_wave_pattern_invalid_end_progress_negative(self):
        """Test that end_progress < 0 raises ValueError."""
        with pytest.raises(ValueError, match="start_progress and end_progress must be within"):
            create_wave_pattern(20, 80, 4, end_progress=-0.1)

    def test_wave_pattern_invalid_end_progress_too_large(self):
        """Test that end_progress > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="start_progress and end_progress must be within"):
            create_wave_pattern(20, 80, 4, end_progress=1.1)

    def test_wave_pattern_end_less_than_start(self):
        """Test that end_progress < start_progress raises ValueError."""
        with pytest.raises(ValueError, match="end_progress must be >= start_progress"):
            create_wave_pattern(20, 80, 4, start_progress=0.8, end_progress=0.2)

    def test_wave_pattern_valid_partial_range(self):
        """Test that valid partial progress range works."""
        sprite = create_test_sprite()
        # Should not raise - valid partial range
        action = create_wave_pattern(20, 80, 4, start_progress=0.25, end_progress=0.75)
        action.apply(sprite, tag="wave")
        # Just verify it was created successfully
        assert action is not None


class TestFigureEightPatternExecution:
    """Test figure-eight pattern execution to cover offset function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_figure_eight_pattern_executes(self):
        """Test figure-eight pattern executes and covers offset_fn lines 278-282."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x
        initial_y = sprite.center_y

        # Create and apply figure-eight pattern
        action = create_figure_eight_pattern((100, 100), 100, 50, 180)
        action.apply(sprite, tag="figure_eight")

        # Run for several frames to ensure offset_fn is called
        for _ in range(30):
            Action.update_all(1 / 60)

        # Sprite should have moved from initial position
        # (the figure-eight pattern will move it)
        assert sprite.center_x != initial_x or sprite.center_y != initial_y


class TestOrbitPatternValidation:
    """Test validation in create_orbit_pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_orbit_pattern_invalid_radius_zero(self):
        """Test that radius <= 0 raises ValueError - line 315."""
        with pytest.raises(ValueError, match="radius must be > 0"):
            create_orbit_pattern((400, 300), 0, 100)

    def test_orbit_pattern_invalid_radius_negative(self):
        """Test that negative radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be > 0"):
            create_orbit_pattern((400, 300), -50, 100)


class TestWavePatternZeroSpan:
    """Test wave pattern with zero span - covers line 187."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_wave_pattern_zero_span(self):
        """Test wave pattern with start_progress == end_progress returns no-op - line 187."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x
        initial_y = sprite.center_y

        # Create wave pattern with zero span (same start and end)
        action = create_wave_pattern(20, 80, 4, start_progress=0.5, end_progress=0.5)
        action.apply(sprite, tag="wave")

        # Run for several frames
        for _ in range(30):
            Action.update_all(1 / 60)

        # Sprite should not have moved (no-op action)
        assert sprite.center_x == initial_x
        assert sprite.center_y == initial_y


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
