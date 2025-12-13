"""Test suite for DevVisualizer palette spawn functionality.

Tests drag-and-drop prototype spawning from palette into scene.
"""

import arcade

from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry, register_prototype, get_registry
from actions.dev.palette import PaletteSidebar
from tests.conftest import ActionTestBase


class TestPaletteSpawn(ActionTestBase):
    """Test suite for palette-based sprite spawning."""

    def test_prototype_registry_register_and_create(self):
        """Test prototype registration and instantiation."""
        registry = SpritePrototypeRegistry()
        ctx = DevContext()

        @registry.register("test_sprite")
        def make_test_sprite(context):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
            sprite._prototype_id = "test_sprite"
            return sprite

        assert registry.has("test_sprite")
        assert "test_sprite" in registry.all()

        sprite = registry.create("test_sprite", ctx)
        assert sprite is not None
        assert hasattr(sprite, "_prototype_id")
        assert sprite._prototype_id == "test_sprite"

    def test_prototype_registry_global_decorator(self):
        """Test global decorator-based registration."""
        from actions.dev.prototype_registry import get_registry

        registry = get_registry()

        @register_prototype("global_test_sprite")
        def make_global_sprite(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
            sprite._prototype_id = "global_test_sprite"
            return sprite

        assert registry.has("global_test_sprite")
        sprite = registry.create("global_test_sprite", DevContext())
        assert sprite._prototype_id == "global_test_sprite"

    def test_palette_spawn_at_position(self, window):
        """Test spawning sprite from palette at cursor position."""
        scene_sprites = arcade.SpriteList()
        ctx = DevContext(scene_sprites=scene_sprites)

        @register_prototype("spawnable_sprite")
        def make_spawnable(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.GREEN)
            sprite._prototype_id = "spawnable_sprite"
            return sprite

        palette = PaletteSidebar(registry=get_registry(), ctx=ctx)

        # Simulate drag-and-drop: mouse down on palette, mouse up at world position
        spawn_x, spawn_y = 200, 300
        palette.handle_spawn("spawnable_sprite", spawn_x, spawn_y)

        # Sprite should be in scene at correct position
        assert len(scene_sprites) == 1
        spawned = scene_sprites[0]
        assert spawned.center_x == spawn_x
        assert spawned.center_y == spawn_y
        assert spawned._prototype_id == "spawnable_sprite"

    def test_palette_spawn_multiple(self, window):
        """Test spawning multiple sprites from palette."""
        scene_sprites = arcade.SpriteList()
        ctx = DevContext(scene_sprites=scene_sprites)

        @register_prototype("multi_sprite")
        def make_multi(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.YELLOW)
            sprite._prototype_id = "multi_sprite"
            return sprite

        palette = PaletteSidebar(registry=get_registry(), ctx=ctx)

        # Spawn at different positions
        positions = [(100, 100), (200, 200), (300, 300)]
        for x, y in positions:
            palette.handle_spawn("multi_sprite", x, y)

        assert len(scene_sprites) == 3
        for i, (x, y) in enumerate(positions):
            assert scene_sprites[i].center_x == x
            assert scene_sprites[i].center_y == y
