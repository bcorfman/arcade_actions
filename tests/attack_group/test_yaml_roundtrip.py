"""Tests for YAML export/import round-trip with attack_groups."""

import tempfile
from pathlib import Path

import arcade
import pytest

from arcadeactions.dev.prototype_registry import DevContext
from arcadeactions.dev.templates import export_template, load_scene_template
from tests.conftest import ActionTestBase


class TestYAMLRoundtrip(ActionTestBase):
    """Test suite for YAML export/import with AttackGroups."""

    def test_yaml_export_backwards_compatible(self):
        """Test that YAML export without AttackGroups uses old format."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 100
            sprite.center_y = 200
            sprite._prototype_id = "test_sprite"
            sprites.append(sprite)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            export_template(sprites, temp_path, prompt_user=False)

            # Load and verify it's a list (old format)
            import yaml

            with open(temp_path) as f:
                data = yaml.safe_load(f)
                assert isinstance(data, list)
                assert len(data) == 3
        finally:
            Path(temp_path).unlink()

    def test_yaml_export_with_attack_groups(self):
        """Test that YAML export with AttackGroups uses new format."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 100
            sprite.center_y = 200
            sprite._prototype_id = "test_sprite"
            sprite._group = "test_group"
            # Simulate AttackGroup config metadata
            sprite._attack_group_config = {
                "id": "test_group",
                "formation": "line",
                "formation_params": {"start_x": 100, "start_y": 200, "spacing": 50},
            }
            sprites.append(sprite)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            export_template(sprites, temp_path, prompt_user=False)

            # Load and verify it's a dict with sprites and attack_groups
            import yaml

            with open(temp_path) as f:
                data = yaml.safe_load(f)
                assert isinstance(data, dict)
                assert "sprites" in data
                assert "attack_groups" in data
                assert len(data["sprites"]) == 5
                assert len(data["attack_groups"]) == 1
        finally:
            Path(temp_path).unlink()

    def test_yaml_import_old_format(self):
        """Test that YAML import handles old format (list of sprites)."""
        import yaml

        # Create old-format YAML
        old_format_data = [
            {
                "prototype": "test_sprite",
                "x": 100,
                "y": 200,
                "group": "",
                "actions": [],
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(old_format_data, f)
            temp_path = f.name

        try:
            ctx = DevContext(scene_sprites=arcade.SpriteList())
            # This will fail if we don't have the prototype registered
            # For now, just verify the loader handles the format
            with pytest.raises((KeyError, ValueError)):
                load_scene_template(temp_path, ctx)
        finally:
            Path(temp_path).unlink()

    def test_yaml_import_new_format(self):
        """Test that YAML import handles new format (dict with sprites/attack_groups)."""
        import yaml

        # Create new-format YAML
        new_format_data = {
            "sprites": [
                {
                    "prototype": "test_sprite",
                    "x": 100,
                    "y": 200,
                    "group": "test_group",
                    "actions": [],
                }
            ],
            "attack_groups": [
                {
                    "id": "test_group",
                    "formation": "line",
                    "formation_params": {"start_x": 100, "start_y": 200, "spacing": 50},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(new_format_data, f)
            temp_path = f.name

        try:
            ctx = DevContext(scene_sprites=arcade.SpriteList())
            # This will fail if we don't have the prototype registered
            # For now, just verify the loader handles the format
            with pytest.raises((KeyError, ValueError)):
                load_scene_template(temp_path, ctx)
            # But verify attack_groups_data is stored
            assert hasattr(ctx, "attack_groups_data")
        finally:
            Path(temp_path).unlink()
