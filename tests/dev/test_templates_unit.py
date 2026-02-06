"""Unit tests for dev templates helpers and edge cases."""

from __future__ import annotations

import tempfile

import arcade
import pytest

from arcadeactions.dev.prototype_registry import DevContext, register_prototype
from arcadeactions.dev.templates import (
    _resolve_bounds,
    _resolve_symbolic,
    _symbolize_value,
    export_template,
    load_scene_template,
)


class TestTemplateHelpers:
    """Test suite for symbolic helpers in templates."""

    def test_resolve_symbolic_token(self):
        """_resolve_symbolic should replace known tokens."""
        assert _resolve_symbolic("SCREEN_LEFT") == 0

    def test_resolve_symbolic_passthrough(self):
        """_resolve_symbolic should passthrough unknown values."""
        assert _resolve_symbolic("NOT_A_TOKEN") == "NOT_A_TOKEN"

    def test_symbolize_value_prefers_axis(self):
        """_symbolize_value should use axis preferences for ambiguous values."""
        assert _symbolize_value(0, axis="x") == "SCREEN_LEFT"
        assert _symbolize_value(0, axis="y") == "SCREEN_BOTTOM"

    def test_symbolize_value_reverse_mapping(self):
        """_symbolize_value should use reverse mapping when no axis is provided."""
        assert _symbolize_value(800) == "SCREEN_WIDTH"

    def test_resolve_bounds_list(self):
        """_resolve_bounds should resolve symbolic bounds list."""
        bounds = _resolve_bounds(["SCREEN_LEFT", "SCREEN_BOTTOM", "SCREEN_RIGHT", "SCREEN_TOP"])
        assert bounds == (0, 0, 800, 600)

    def test_resolve_bounds_none(self):
        """_resolve_bounds should return None for None input."""
        assert _resolve_bounds(None) is None

    def test_resolve_bounds_invalid(self):
        """_resolve_bounds should return None for invalid shapes."""
        assert _resolve_bounds({"left": 0}) is None


class TestTemplateEdgeCases:
    """Test suite for export/load edge cases."""

    def test_export_symbolizes_bounds(self, tmp_path):
        """export_template should symbolize bounds using axis preferences."""
        sprites = arcade.SpriteList()
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite._prototype_id = "symbolic_sprite"
        sprite._action_configs = [
            {
                "preset": "bounds_preset",
                "params": {"bounds": (0, 0, 800, 600)},
            }
        ]
        sprites.append(sprite)

        out_path = tmp_path / "scene.yaml"
        export_template(sprites, out_path, prompt_user=False)

        contents = out_path.read_text()
        assert "SCREEN_LEFT" in contents
        assert "SCREEN_BOTTOM" in contents
        assert "SCREEN_RIGHT" in contents
        assert "SCREEN_TOP" in contents

    def test_load_scene_template_invalid_yaml_type(self, tmp_path):
        """load_scene_template should raise for invalid YAML types."""
        out_path = tmp_path / "invalid.yaml"
        out_path.write_text("123")
        ctx = DevContext(scene_sprites=arcade.SpriteList())

        with pytest.raises(ValueError, match="YAML must contain"):
            load_scene_template(out_path, ctx)

    def test_load_scene_template_reconstructs_attack_groups(self, tmp_path):
        """load_scene_template should rebuild sprites and attach attack groups."""

        @register_prototype("unit_template_sprite")
        def make_template_sprite(ctx):
            sprite = arcade.SpriteSolidColor(width=16, height=16, color=arcade.color.RED)
            sprite._prototype_id = "unit_template_sprite"
            return sprite

        yaml_content = """sprites:
  - x: 10
    y: 20
    group: "missing"
    actions: []
  - prototype: "unit_template_sprite"
    x: 100
    y: 200
    group: "group_a"
    actions:
      - params:
          speed: 5
      - preset: "move_preset"
        params:
          bounds: [SCREEN_LEFT, SCREEN_BOTTOM, SCREEN_RIGHT, SCREEN_TOP]
attack_groups:
  - id: "group_a"
    formation: "line"
    formation_params:
      start_x: 100
      start_y: 200
      spacing: 50
"""
        out_path = tmp_path / "scene.yaml"
        out_path.write_text(yaml_content)
        ctx = DevContext(scene_sprites=None)

        sprites = load_scene_template(out_path, ctx)

        assert ctx.scene_sprites is not None
        assert len(sprites) == 1
        sprite = sprites[0]
        assert sprite.center_x == 100
        assert sprite.center_y == 200
        assert sprite._group == "group_a"
        assert sprite._action_configs[0]["preset"] == "move_preset"
        assert sprite._action_configs[0]["params"]["bounds"] == (0, 0, 800, 600)
        assert hasattr(sprite, "_attack_group")
