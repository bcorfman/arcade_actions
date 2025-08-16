#!/usr/bin/env python3
"""
Tests for ParametricMotionUntil mid-cycle stop and _Repeat restart continuity.
"""

import arcade

from actions import Action, repeat
from actions.pattern import create_wave_pattern


def _run_frames(frames: int) -> None:
    for _ in range(frames):
        Action.update_all(1 / 60)


def test_parametric_midcycle_stop_snaps_to_end():
    # Setup
    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Full wave returns to origin at end
    full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
    full_wave.apply(sprite, tag="midcycle")

    # Advance part-way (not near end)
    _run_frames(45)  # ~0.75s
    assert not full_wave.done

    # Force early completion via condition override that returns True now
    # Replace condition with immediate true so base Action.update triggers remove_effect
    full_wave.condition = lambda: True
    Action.update_all(0)  # Trigger evaluation

    # After early stop, the position must be at exact end (t=1.0) relative to origin
    final_dx, final_dy = full_wave._offset_fn(1.0)
    assert abs(sprite.center_x - (100 + final_dx)) < 1e-3
    assert abs(sprite.center_y - (100 + final_dy)) < 1e-3


def test_repeat_restart_no_offset_after_midcycle_stop():
    # Setup
    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
    rep = repeat(full_wave)
    rep.apply(sprite, tag="repeat_midcycle")

    # Let it complete a couple cycles normally
    _run_frames(400)
    pos_before = (sprite.center_x, sprite.center_y)

    # Force mid-cycle completion of current inner action
    current = rep.current_action
    assert current is not None
    # Replace its condition with immediate true to simulate premature stop
    current.condition = lambda: True
    Action.update_all(0)
    pos_after_stop = (sprite.center_x, sprite.center_y)

    # Immediately after, _Repeat should start a fresh iteration
    # Run one frame to allow restart
    _run_frames(1)
    pos_after_restart = (sprite.center_x, sprite.center_y)

    # Positions should not jump by a large amount due to offset mismatch
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    # Snap-to-end ensures no extreme discontinuity at stop moment
    assert dist(pos_before, pos_after_stop) < 90  # strictly bounded (wave span is 80)

    # Restart should not produce a huge jump; allow small movement
    assert dist(pos_after_stop, pos_after_restart) < 15
