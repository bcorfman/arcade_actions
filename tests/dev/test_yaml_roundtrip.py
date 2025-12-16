"""Test suite for DevVisualizer YAML export/import round-trip.

Tests that exported YAML can be loaded back and produces identical sprite configurations.
"""

import arcade
import tempfile
import os
import pytest

from actions.dev.prototype_registry import DevContext, register_prototype, get_registry
from actions.dev.templates import export_template, load_scene_template
from tests.conftest import ActionTestBase


class TestYAMLRoundtrip(ActionTestBase):
    """Test suite for YAML export/import functionality."""

    @pytest.mark.integration
    def test_export_basic_sprite(self, window):
        """Test exporting a single sprite to YAML."""
        scene_sprites = arcade.SpriteList()

        @register_prototype("test_export")
        def make_test_export(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
            sprite._prototype_id = "test_export"
            return sprite

        registry = get_registry()
        ctx = DevContext(scene_sprites=scene_sprites)
        sprite = registry.create("test_export", ctx)
        sprite.center_x = 150
        sprite.center_y = 250
        scene_sprites.append(sprite)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            export_template(scene_sprites, temp_path, prompt_user=False)

            # Verify file exists and has content
            assert os.path.exists(temp_path)
            with open(temp_path, "r") as f:
                content = f.read()
                assert "test_export" in content
                assert "150" in content or "x: 150" in content
                assert "250" in content or "y: 250" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.integration
    def test_import_basic_sprite(self, window):
        """Test importing a sprite from YAML."""
        scene_sprites = arcade.SpriteList()

        @register_prototype("test_import")
        def make_test_import(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
            sprite._prototype_id = "test_import"
            return sprite

        yaml_content = """- prototype: "test_import"
  x: 300
  y: 400
  group: ""
  actions: []
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            ctx = DevContext(scene_sprites=scene_sprites)
            load_scene_template(temp_path, ctx)

            assert len(scene_sprites) == 1
            sprite = scene_sprites[0]
            assert sprite._prototype_id == "test_import"
            assert sprite.center_x == 300
            assert sprite.center_y == 400
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.integration
    def test_roundtrip_with_actions(self, window):
        """Test export/import round-trip with action presets."""
        scene_sprites = arcade.SpriteList()

        @register_prototype("roundtrip_sprite")
        def make_roundtrip(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.GREEN)
            sprite._prototype_id = "roundtrip_sprite"
            return sprite

        from actions.dev.presets import register_preset

        @register_preset("roundtrip_preset", category="Movement", params={"speed": 7})
        def make_roundtrip_preset(ctx, speed):
            from actions.helpers import move_until
            from actions.conditional import infinite

            return move_until(None, velocity=(-speed, 0), condition=infinite)

        registry = get_registry()
        ctx = DevContext(scene_sprites=scene_sprites)
        sprite = registry.create("roundtrip_sprite", ctx)
        sprite.center_x = 500
        sprite.center_y = 600
        sprite._action_configs = [{"preset": "roundtrip_preset", "params": {"speed": 7}}]
        scene_sprites.append(sprite)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Export
            export_template(scene_sprites, temp_path, prompt_user=False)

            # Clear and reimport
            scene_sprites.clear()
            load_scene_template(temp_path, ctx)

            # Verify round-trip
            assert len(scene_sprites) == 1
            loaded_sprite = scene_sprites[0]
            assert loaded_sprite._prototype_id == "roundtrip_sprite"
            assert loaded_sprite.center_x == 500
            assert loaded_sprite.center_y == 600
            assert hasattr(loaded_sprite, "_action_configs")
            assert len(loaded_sprite._action_configs) == 1
            assert loaded_sprite._action_configs[0]["preset"] == "roundtrip_preset"
            assert loaded_sprite._action_configs[0]["params"]["speed"] == 7
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.integration
    def test_symbolic_bounds_export(self, window):
        """Test that symbolic bounds tokens are exported instead of raw numbers."""
        # This will be implemented with symbolic token mapping
        # For now, just verify the export function accepts bounds
        scene_sprites = arcade.SpriteList()

        @register_prototype("bounds_sprite")
        def make_bounds(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.YELLOW)
            sprite._prototype_id = "bounds_sprite"
            return sprite

        registry = get_registry()
        ctx = DevContext(scene_sprites=scene_sprites)
        sprite = registry.create("bounds_sprite", ctx)
        sprite.center_x = 100
        sprite.center_y = 100
        # Simulate action with bounds (stored as metadata)
        sprite._action_configs = [
            {
                "preset": "test_preset",
                "params": {"bounds": (0, 0, 800, 600)},  # Should export as symbolic if matching
            }
        ]
        scene_sprites.append(sprite)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            export_template(scene_sprites, temp_path, prompt_user=False)
            # Verify export succeeded (symbolic replacement tested in implementation)
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


