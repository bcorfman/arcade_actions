"""Test suite for DevVisualizer preset action library and bulk attach.

Tests preset registration, parameter editing, and bulk application to selected sprites.
"""

import arcade
import pytest

from arcadeactions.conditional import infinite
from arcadeactions.dev.presets import ActionPresetRegistry, register_preset
from arcadeactions.dev.selection import SelectionManager
from arcadeactions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase


class TestPresetAttach(ActionTestBase):
    """Test suite for preset action library."""

    def test_preset_registry_register(self):
        """Test preset registration."""
        registry = ActionPresetRegistry()

        @registry.register("scroll_left", category="Movement", params={"speed": 4})
        def make_scroll_left(ctx, speed):
            from arcadeactions.helpers import move_until

            return move_until(
                None,  # Unbound action
                velocity=(-speed, 0),
                condition=infinite,
            )

        assert registry.has("scroll_left")
        assert "scroll_left" in registry.all()

    def test_preset_create_action(self):
        """Test creating action from preset."""
        from arcadeactions.dev.presets import get_preset_registry

        registry = get_preset_registry()

        @register_preset("test_scroll", category="Movement", params={"speed": 3})
        def make_test_scroll(ctx, speed):
            from arcadeactions.helpers import move_until

            return move_until(None, velocity=(-speed, 0), condition=infinite)

        ctx = type("Context", (), {})()  # Mock context
        action = registry.create("test_scroll", ctx, speed=3)

        assert action is not None
        assert hasattr(action, "target_velocity")
        assert action.target_velocity == (-3, 0)

    @pytest.mark.integration
    def test_bulk_attach_preset_to_selected(self, window):
        """Test applying preset to multiple selected sprites."""
        scene_sprites = arcade.SpriteList()
        sprites = []
        for i in range(3):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
            sprite.center_x = 100 + i * 50
            sprite.center_y = 100
            scene_sprites.append(sprite)
            sprites.append(sprite)

        selection_manager = SelectionManager(scene_sprites)
        # Select all sprites
        for sprite in sprites:
            selection_manager._selected.add(sprite)

        @register_preset("bulk_test", category="Movement", params={"speed": 5})
        def make_bulk_test(ctx, speed):
            from arcadeactions.helpers import move_until

            return move_until(None, velocity=(-speed, 0), condition=infinite)

        # Bulk attach preset
        selected = selection_manager.get_selected()
        assert len(selected) == 3

        # Attach preset to each selected sprite (as metadata, not running)
        for sprite in selected:
            # Store as metadata (not applying - edit mode)
            if not hasattr(sprite, "_action_configs"):
                sprite._action_configs = []
            sprite._action_configs.append({"preset": "bulk_test", "params": {"speed": 5}})

        # Verify metadata stored
        for sprite in selected:
            assert hasattr(sprite, "_action_configs")
            assert len(sprite._action_configs) == 1
            assert sprite._action_configs[0]["preset"] == "bulk_test"
            assert sprite._action_configs[0]["params"]["speed"] == 5

    def test_preset_param_editing(self):
        """Test editing preset parameters."""
        from arcadeactions.dev.presets import get_preset_registry

        @register_preset("editable", category="Movement", params={"speed": 2, "direction": -1})
        def make_editable(ctx, speed, direction):
            from arcadeactions.helpers import move_until

            return move_until(None, velocity=(speed * direction, 0), condition=infinite)

        registry = get_preset_registry()
        ctx = type("Context", (), {})()

        # Create with default params
        action1 = registry.create("editable", ctx, speed=2, direction=-1)
        assert action1.target_velocity == (-2, 0)

        # Create with edited params
        action2 = registry.create("editable", ctx, speed=4, direction=-1)
        assert action2.target_velocity == (-4, 0)

    def test_dev_viz_attach_preset_to_selected(self):
        """DevVisualizer should provide API to attach presets to selected sprites as metadata."""
        scene_sprites = arcade.SpriteList()
        sprites = []
        for i in range(2):
            sprite = arcade.SpriteSolidColor(width=16, height=16, color=arcade.color.BLUE)
            sprite.center_x = 10 + i * 20
            sprite.center_y = 10
            scene_sprites.append(sprite)
            sprites.append(sprite)

        selection_manager = SelectionManager(scene_sprites)
        for s in sprites:
            selection_manager._selected.add(s)

        dev_viz = DevVisualizer()
        dev_viz.selection_manager = selection_manager

        dev_viz.attach_preset_to_selected("bulk_test", params={"speed": 5}, tag="movement")

        for s in sprites:
            assert hasattr(s, "_action_configs")
            assert len(s._action_configs) == 1
            cfg = s._action_configs[0]
            assert cfg["preset"] == "bulk_test"
            assert cfg["params"]["speed"] == 5
            assert cfg["tag"] == "movement"

    def test_update_action_config_api(self):
        """DevVisualizer API should allow updating action config params for sprites."""
        sprite = arcade.SpriteSolidColor(width=16, height=16, color=arcade.color.BLUE)
        sprite.center_x = 50
        sprite.center_y = 50
        sprite._action_configs = [{"action_type": "MoveUntil", "velocity": (2, 0), "bounds": (0, 0, 100, 100)}]

        dev_viz = DevVisualizer()

        # Update the first config velocity
        dev_viz.update_action_config(sprite, 0, velocity=(10, 0))
        assert sprite._action_configs[0]["velocity"] == (10, 0)

        # Update selected sprites' config
        scene = arcade.SpriteList()
        scene.append(sprite)
        selection_manager = SelectionManager(scene)
        selection_manager._selected.add(sprite)
        dev_viz.selection_manager = selection_manager

        dev_viz.update_selected_action_config(0, boundary_behavior="limit")
        assert sprite._action_configs[0]["boundary_behavior"] == "limit"
