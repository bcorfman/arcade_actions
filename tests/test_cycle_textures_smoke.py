"""Slimmed-down coverage for CycleTexturesUntil after frame-based overhaul."""

import arcade

from arcadeactions import cycle_textures_until
from arcadeactions.conditional import CycleTexturesUntil
from arcadeactions.frame_timing import after_frames


def _make_textures(count: int):
    return [arcade.Texture.create_empty(f"tex_{i}", (4, 4)) for i in range(count)]


def test_cycle_textures_basic_advances_after_configured_frames():
    textures = _make_textures(2)
    action = CycleTexturesUntil(textures=textures, frames_per_texture=2)
    sprite = arcade.Sprite()
    action.apply(sprite)

    # First two frames keep the initial texture
    action.update_effect(0.0)
    assert sprite.texture == textures[0]
    action.update_effect(0.0)
    assert sprite.texture == textures[0]

    # Third update triggers swap
    action.update_effect(0.0)
    assert sprite.texture == textures[1]


def test_cycle_textures_direction_reversal():
    textures = _make_textures(3)
    action = CycleTexturesUntil(textures=textures, frames_per_texture=1, direction=-1)
    sprite = arcade.Sprite()
    action.apply(sprite)

    action.update_effect(0.0)
    action.update_effect(0.0)  # Switch to previous (wrap)
    assert sprite.texture == textures[-1]


def test_helper_function_uses_frame_arguments(monkeypatch):
    texture = arcade.Texture.create_empty("tex", (4, 4))
    captured = {}

    def mock_apply(self, target, tag=None):
        captured["target"] = target
        captured["frames_per_texture"] = self._frames_per_texture
        captured["condition"] = self.condition

    monkeypatch.setattr(CycleTexturesUntil, "apply", mock_apply, raising=False)

    sprite = arcade.Sprite()
    cycle_textures_until(
        sprite,
        textures=[texture],
        frames_per_texture=5,
        condition=after_frames(10),
        tag="smoke",
    )

    assert captured["target"] is sprite
    assert captured["frames_per_texture"] == 5
    assert captured["condition"]() is False  # after_frames returns callable
