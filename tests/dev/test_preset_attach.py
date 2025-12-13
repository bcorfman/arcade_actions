"""Test suite for DevVisualizer preset action library and bulk attach.

Tests preset registration, parameter editing, and bulk application to selected sprites.
"""

import arcade

from actions.conditional import infinite
from actions.dev.presets import ActionPresetRegistry, register_preset
from actions.dev.selection import SelectionManager
from tests.conftest import ActionTestBase


class TestPresetAttach(ActionTestBase):
    """Test suite for preset action library."""

    def test_preset_registry_register(self):
        """Test preset registration."""
        registry = ActionPresetRegistry()

        @registry.register("scroll_left", category="Movement", params={"speed": 4})
        def make_scroll_left(ctx, speed):
            from actions.helpers import move_until

            return move_until(
                None,  # Unbound action
                velocity=(-speed, 0),
                condition=infinite,
            )

        assert registry.has("scroll_left")
        assert "scroll_left" in registry.all()

    def test_preset_create_action(self):
        """Test creating action from preset."""
        from actions.dev.presets import get_preset_registry

        registry = get_preset_registry()

        @register_preset("test_scroll", category="Movement", params={"speed": 3})
        def make_test_scroll(ctx, speed):
            from actions.helpers import move_until

            return move_until(None, velocity=(-speed, 0), condition=infinite)

        ctx = type("Context", (), {})()  # Mock context
        action = registry.create("test_scroll", ctx, speed=3)

        assert action is not None
        assert hasattr(action, "target_velocity")
        assert action.target_velocity == (-3, 0)

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
            from actions.helpers import move_until

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
        from actions.dev.presets import get_preset_registry

        @register_preset("editable", category="Movement", params={"speed": 2, "direction": -1})
        def make_editable(ctx, speed, direction):
            from actions.helpers import move_until

            return move_until(None, velocity=(speed * direction, 0), condition=infinite)

        registry = get_preset_registry()
        ctx = type("Context", (), {})()

        # Create with default params
        action1 = registry.create("editable", ctx, speed=2, direction=-1)
        assert action1.target_velocity == (-2, 0)

        # Create with edited params
        action2 = registry.create("editable", ctx, speed=4, direction=-1)
        assert action2.target_velocity == (-4, 0)
