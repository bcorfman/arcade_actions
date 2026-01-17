"""Regression tests for wave pattern timing and ParametricMotionUntil.

These tests perform explicit time/step sampling to ensure that
`create_wave_pattern` backed by `ParametricMotionUntil`:

- Produces smooth per-frame motion (no large jumps)
- Actually animates over multiple frames (not an instant snap)
- Uses frame-based timing correctly with after_frames() conditions
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import arcade

from actions import Action, repeat, sequence
from actions.pattern import create_wave_pattern

REFERENCE_PATH = Path(__file__).with_name("data") / "wave_reference_a85.json"


class TestWavePatternTiming:
    """Frame-based sampling tests for create_wave_pattern."""

    def setup_method(self):
        """Clean up action state before each test."""
        Action.stop_all()

    def teardown_method(self):
        """Clean up action state after each test."""
        Action.stop_all()

    def test_wave_pattern_animates_over_multiple_frames(self):
        """Current create_wave_pattern should move the sprite smoothly over many frames."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 200

        wave = create_wave_pattern(amplitude=30, length=80, velocity=4)
        wave.apply(sprite, tag="wave_motion")

        positions: list[tuple[float, float]] = []
        last_pos = (sprite.center_x, sprite.center_y)
        max_step = 0.0

        # Sample ~3 seconds at 60 FPS
        for _ in range(180):
            Action.update_all(1 / 60)
            current = (sprite.center_x, sprite.center_y)
            positions.append(current)
            dx = current[0] - last_pos[0]
            dy = current[1] - last_pos[1]
            step = math.hypot(dx, dy)
            max_step = max(max_step, step)
            last_pos = current

        # Sprite should have moved appreciably in both axes
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        assert max(xs) - min(xs) > 5.0
        assert max(ys) - min(ys) > 5.0

        # No single step should be an implausibly large jump
        assert max_step < 40.0

    def test_wave_pattern_matches_legacy_reference_sample(self):
        """Ensure current frame-based implementation matches legacy sampled motion."""
        reference = json.loads(REFERENCE_PATH.read_text())
        positions = self._sample_space_clutter_wave(
            amplitude=reference["amplitude"],
            length=reference["length"],
            velocity=reference["velocity"],
            frames=reference["total_frames"],
        )

        assert len(positions) == len(reference["positions"])

        for idx, ((expected_x, expected_y), (actual_x, actual_y)) in enumerate(
            zip(reference["positions"], positions), start=1
        ):
            assert math.isclose(actual_x, expected_x, abs_tol=1e-6), f"x mismatch at frame {idx}"
            assert math.isclose(actual_y, expected_y, abs_tol=1e-6), f"y mismatch at frame {idx}"

    @staticmethod
    def _sample_space_clutter_wave(*, amplitude: float, length: float, velocity: float, frames: int):
        Action.stop_all()
        sprite = arcade.Sprite()
        sprite.center_x = 0
        sprite.center_y = 0

        quarter_wave = create_wave_pattern(
            amplitude=amplitude,
            length=length,
            velocity=velocity,
            start_progress=0.75,
            end_progress=1.0,
        )
        full_wave = create_wave_pattern(amplitude=amplitude, length=length, velocity=velocity)
        pattern = sequence(quarter_wave, repeat(full_wave))
        pattern.apply(sprite, tag="enemy_wave")

        positions: list[tuple[float, float]] = []
        for _ in range(frames):
            Action.update_all(1 / 60)
            positions.append((sprite.center_x, sprite.center_y))

        return positions
