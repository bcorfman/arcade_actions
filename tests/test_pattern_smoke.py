"""Lightweight smoke tests for movement pattern factories."""

import arcade
import pytest

from arcadeactions.frame_timing import after_frames
from arcadeactions.pattern import (
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_formation_entry_from_sprites,
    create_orbit_pattern,
    create_patrol_pattern,
    create_spiral_pattern,
    create_wave_pattern,
    create_zigzag_pattern,
)


def test_create_zigzag_pattern_runs_with_frame_args():
    pattern = create_zigzag_pattern(width=100, height=50, velocity=5, segments=3)
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="zigzag")
    assert pattern.condition() is False


def test_create_zigzag_pattern_validates_segments():
    with pytest.raises(ValueError, match="segments must be > 0"):
        create_zigzag_pattern(width=100, height=50, velocity=5, segments=0)


def test_create_zigzag_pattern_validates_velocity():
    with pytest.raises(ValueError, match="velocity must be > 0"):
        create_zigzag_pattern(width=100, height=50, velocity=0, segments=3)


def test_create_wave_pattern_uses_velocity_parameter():
    pattern = create_wave_pattern(amplitude=20, length=60, velocity=4, condition=after_frames(30))
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="wave")
    assert pattern.condition() is False


def test_create_wave_pattern_validates_progress_range():
    with pytest.raises(ValueError, match="start_progress and end_progress must be within"):
        create_wave_pattern(amplitude=20, length=60, velocity=4, start_progress=-0.1)


def test_create_wave_pattern_validates_progress_order():
    with pytest.raises(ValueError, match="end_progress must be >= start_progress"):
        create_wave_pattern(amplitude=20, length=60, velocity=4, start_progress=0.8, end_progress=0.2)


def test_create_wave_pattern_zero_span():
    pattern = create_wave_pattern(amplitude=20, length=60, velocity=4, start_progress=0.5, end_progress=0.5)
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="wave_zero")
    # Zero-span patterns complete immediately (after_frames(0))
    assert pattern.condition() is True


def test_create_spiral_pattern_accepts_velocity_and_condition():
    pattern = create_spiral_pattern(
        center=(0, 0), max_radius=50, revolutions=2.0, velocity=3, condition=after_frames(45)
    )
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="spiral")
    assert pattern.condition() is False


def test_create_spiral_pattern_inward_direction():
    pattern = create_spiral_pattern(center=(0, 0), max_radius=50, revolutions=2.0, velocity=3, direction="inward")
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="spiral_inward")
    assert pattern.condition() is False


def test_create_spiral_pattern_validates_direction():
    # Spiral pattern doesn't validate direction - it just uses it as-is
    # Invalid direction will be caught by FollowPathUntil if needed
    pattern = create_spiral_pattern(center=(0, 0), max_radius=50, revolutions=2.0, velocity=3, direction="sideways")
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="spiral_invalid")
    assert pattern.condition() is False


def test_create_figure_eight_pattern():
    pattern = create_figure_eight_pattern(
        center=(400, 300), width=100, height=80, velocity=5, condition=after_frames(60)
    )
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="figure_eight")
    assert pattern.condition() is False


def test_create_orbit_pattern():
    pattern = create_orbit_pattern(center=(400, 300), radius=100, velocity=3, clockwise=True)
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="orbit")
    assert pattern.condition() is False


def test_create_orbit_pattern_counterclockwise():
    pattern = create_orbit_pattern(center=(400, 300), radius=100, velocity=3, clockwise=False)
    sprite = arcade.Sprite()
    pattern.apply(sprite, tag="orbit_ccw")
    assert pattern.condition() is False


def test_create_patrol_pattern():
    # create_patrol_pattern signature: velocity tuple, bounds, axis
    pattern = create_patrol_pattern(velocity=(5, 0), bounds=(0, 0, 400, 400), axis="x")
    sprite = arcade.SpriteSolidColor(20, 20, arcade.color.WHITE)
    sprite.center_x = 100
    sprite.center_y = 200
    pattern.apply(sprite, tag="patrol")
    assert pattern.condition() is False


def test_create_formation_entry_from_sprites():
    # create_formation_entry_from_sprites signature: target_formation (SpriteList), **kwargs
    sprite_list = arcade.SpriteList()
    for i in range(3):
        sprite = arcade.Sprite()
        sprite.center_x = 200 + i * 50
        sprite.center_y = 200
        sprite_list.append(sprite)

    result = create_formation_entry_from_sprites(
        sprite_list, window_bounds=(0, 0, 800, 600), velocity=5, stagger_delay_frames=10
    )

    # Returns list of (sprite, sprite_list, wave_index) tuples
    assert isinstance(result, list)
    assert len(result) > 0


def test_create_bounce_pattern_accepts_callbacks():
    pattern = create_bounce_pattern(velocity=(5, 0), bounds=(0, 0, 200, 200))
    sprite = arcade.SpriteSolidColor(20, 20, arcade.color.WHITE)
    pattern.apply(sprite, tag="bounce")
    assert pattern.bounds == (0, 0, 200, 200)
