#!/usr/bin/env python3
"""
Test that _Repeat + ParametricMotionUntil does not produce position jumps when
wall-clock time (used by duration()) diverges from simulation delta_time.
"""

import sys

import arcade

from actions import Action, repeat
from actions.pattern import create_wave_pattern


def _run_frames(frames: int) -> None:
    for _ in range(frames):
        Action.update_all(1 / 60)


def test_repeat_with_wallclock_drift_no_jump():
    # Save and monkeypatch time.time used by duration()
    import time as real_time_module

    original_time_fn = real_time_module.time

    # Controlled simulated wall clock
    sim_time = {"t": original_time_fn()}

    def fake_time():
        return sim_time["t"]

    # Monkeypatch the time module globally
    sys.modules["time"].time = fake_time

    try:
        # Setup sprite and repeating full-wave action
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
        rep = repeat(full_wave)
        rep.apply(sprite, tag="repeat_wallclock")

        last_pos = (sprite.center_x, sprite.center_y)
        # Run ~10 seconds, injecting wall-clock drift every 2 seconds
        for frame in range(10 * 60):
            # Advance simulated wall clock normally
            sim_time["t"] += 1 / 60
            # Every 120 frames (~2 s), inject 150 ms extra wall time to simulate hitches
            if frame and frame % 120 == 0:
                sim_time["t"] += 0.15

            Action.update_all(1 / 60)

            current = (sprite.center_x, sprite.center_y)
            # Detect sudden large position jumps within one frame
            dx = current[0] - last_pos[0]
            dy = current[1] - last_pos[1]
            step_dist = (dx * dx + dy * dy) ** 0.5
            # Allow generous per-frame distance for wave motion; disallow implausible jumps
            assert step_dist < 30.0, f"Unexpected jump {step_dist:.2f} at frame {frame}"
            last_pos = current

    finally:
        # Restore real time.time
        sys.modules["time"].time = original_time_fn
