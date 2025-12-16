"""Test suite for DevVisualizer palette spawn functionality.

Tests drag-and-drop prototype spawning from palette into scene.
"""

import arcade
import pytest

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

    @pytest.mark.integration
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

    @pytest.mark.integration
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

    @pytest.mark.integration
    def test_palette_click_detection_top_to_bottom(self, window):
        """Test that clicking on palette items correctly selects prototypes in top-to-bottom order."""
        scene_sprites = arcade.SpriteList()
        ctx = DevContext(scene_sprites=scene_sprites)
        # Use a fresh registry instance to avoid interference from other tests
        registry = SpritePrototypeRegistry()

        # Register multiple prototypes
        @registry.register("top_item")
        def make_top(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
            sprite._prototype_id = "top_item"
            return sprite

        @registry.register("middle_item")
        def make_middle(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.GREEN)
            sprite._prototype_id = "middle_item"
            return sprite

        @registry.register("bottom_item")
        def make_bottom(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
            sprite._prototype_id = "bottom_item"
            return sprite

        palette = PaletteSidebar(registry=registry, ctx=ctx, x=10, y=10)
        prototypes = list(registry.all().keys())

        # Items are drawn top-to-bottom: item 0 (top_item) at highest y, item 2 (bottom_item) at lowest y
        # With item_height=50, self.y=10:
        # - Item 0 (top_item): y = 10 + (3-0)*50 = 160
        # - Item 1 (middle_item): y = 10 + (3-1)*50 = 110
        # - Item 2 (bottom_item): y = 10 + (3-2)*50 = 60

        item_height = 50

        # Click on top item (should select prototype at index 0)
        click_y_top = 10 + (len(prototypes) - 0) * item_height  # 160
        result = palette.handle_mouse_press(50, click_y_top)  # x=50 is within palette width
        assert result is True
        assert palette._dragging_prototype == "top_item"

        # Clean up for next test
        palette._dragging_prototype = None

        # Click on middle item (should select prototype at index 1)
        click_y_middle = 10 + (len(prototypes) - 1) * item_height  # 110
        result = palette.handle_mouse_press(50, click_y_middle)
        assert result is True
        assert palette._dragging_prototype == "middle_item"

        # Clean up for next test
        palette._dragging_prototype = None

        # Click on bottom item (should select prototype at index 2)
        click_y_bottom = 10 + (len(prototypes) - 2) * item_height  # 60
        result = palette.handle_mouse_press(50, click_y_bottom)
        assert result is True
        assert palette._dragging_prototype == "bottom_item"

    @pytest.mark.integration
    def test_palette_click_detection_boundaries(self, window):
        """Test click detection at item boundaries and outside palette."""
        scene_sprites = arcade.SpriteList()
        ctx = DevContext(scene_sprites=scene_sprites)
        # Use a fresh registry instance to avoid interference from other tests
        registry = SpritePrototypeRegistry()

        @registry.register("test_item")
        def make_test(ctx):
            sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
            sprite._prototype_id = "test_item"
            return sprite

        palette = PaletteSidebar(registry=registry, ctx=ctx, x=10, y=10, width=200)

        # Click outside palette X bounds (should return False)
        result = palette.handle_mouse_press(300, 60)  # x=300 is beyond palette width
        assert result is False

        # Click below palette Y bounds (should return False)
        result = palette.handle_mouse_press(50, 5)  # y=5 is below self.y=10
        assert result is False

        # Click on invisible palette (should return False)
        palette.visible = False
        result = palette.handle_mouse_press(50, 60)
        assert result is False
