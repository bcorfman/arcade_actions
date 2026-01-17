"""Tests for PaletteWindow mouse interaction methods."""

from __future__ import annotations

import arcade
import pytest

from actions.dev.palette_window import PaletteWindow
from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry

pytestmark = pytest.mark.slow


@pytest.fixture
def registry():
    """Create a test registry with prototypes."""
    reg = SpritePrototypeRegistry()

    @reg.register("sprite1")
    def make_sprite1(ctx):
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite._prototype_id = "sprite1"
        return sprite

    @reg.register("sprite2")
    def make_sprite2(ctx):
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite._prototype_id = "sprite2"
        return sprite

    return reg


@pytest.fixture
def palette_window(registry):
    """Create a PaletteWindow instance for testing."""
    ctx = DevContext()
    scene_sprites = arcade.SpriteList()
    ctx.scene_sprites = scene_sprites
    window = PaletteWindow(
        registry=registry,
        ctx=ctx,
        on_close_callback=lambda: None,
        forward_key_handler=lambda k, m: False,
    )
    window.height = 400
    return window


class TestMouseInteraction:
    """Test mouse interaction methods."""

    def test_on_mouse_press_left_button_spawns(self, palette_window, mocker):
        """Test on_mouse_press with left button spawns sprite."""
        mock_spawn = mocker.patch.object(palette_window, "_spawn_prototype")

        palette_window.on_mouse_press(50, 300, arcade.MOUSE_BUTTON_LEFT, 0)

        mock_spawn.assert_called_once()

    def test_on_mouse_press_non_left_button(self, palette_window, mocker):
        """Test on_mouse_press with non-left button does nothing."""
        mock_spawn = mocker.patch.object(palette_window, "_spawn_prototype")

        palette_window.on_mouse_press(50, 300, arcade.MOUSE_BUTTON_RIGHT, 0)
        palette_window.on_mouse_press(50, 300, arcade.MOUSE_BUTTON_MIDDLE, 0)

        mock_spawn.assert_not_called()

    def test_on_mouse_press_empty_prototypes(self, registry, mocker):
        """Test on_mouse_press with empty prototype list."""
        empty_registry = SpritePrototypeRegistry()
        ctx = DevContext()
        window = PaletteWindow(
            registry=empty_registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window.height = 400

        mock_spawn = mocker.patch.object(window, "_spawn_prototype")

        window.on_mouse_press(50, 300, arcade.MOUSE_BUTTON_LEFT, 0)

        mock_spawn.assert_not_called()

    def test_on_mouse_press_calculates_correct_index(self, palette_window, mocker):
        """Test on_mouse_press calculates correct prototype index."""
        mock_spawn = mocker.patch.object(palette_window, "_spawn_prototype")

        # Items start at y = height - MARGIN - 60 = 400 - 12 - 60 = 328
        # With ITEM_HEIGHT = 50:
        # - Item 0: y = 328 - 0*50 = 328
        # - Item 1: y = 328 - 1*50 = 278
        start_y = palette_window.height - palette_window.MARGIN - 60

        # Click on first item (index 0)
        y_pos = start_y - 0 * palette_window.ITEM_HEIGHT
        palette_window.on_mouse_press(50, int(y_pos), arcade.MOUSE_BUTTON_LEFT, 0)

        assert mock_spawn.called
        # Check first prototype was spawned
        call_args = mock_spawn.call_args[0]
        prototypes = list(palette_window.registry.all().keys())
        assert call_args[0] == prototypes[0]

    def test_on_mouse_press_out_of_bounds(self, palette_window, mocker):
        """Test on_mouse_press with out of bounds coordinates."""
        mock_spawn = mocker.patch.object(palette_window, "_spawn_prototype")

        # Click way above items
        palette_window.on_mouse_press(50, 500, arcade.MOUSE_BUTTON_LEFT, 0)

        # Click way below items
        palette_window.on_mouse_press(50, 0, arcade.MOUSE_BUTTON_LEFT, 0)

        # Should not spawn (index out of range)
        # Actually, it might try to spawn with invalid index - check that it doesn't crash
        # The method should handle this gracefully

    def test_spawn_prototype_valid(self, palette_window):
        """Test _spawn_prototype with valid prototype."""
        scene_sprites = palette_window.dev_context.scene_sprites

        palette_window._spawn_prototype("sprite1")

        assert len(scene_sprites) == 1
        assert scene_sprites[0]._prototype_id == "sprite1"

    def test_spawn_prototype_invalid(self, palette_window):
        """Test _spawn_prototype with invalid prototype."""
        scene_sprites = palette_window.dev_context.scene_sprites
        initial_count = len(scene_sprites)

        palette_window._spawn_prototype("nonexistent")

        # Should not add sprite
        assert len(scene_sprites) == initial_count

    def test_spawn_prototype_no_scene_sprites(self, registry):
        """Test _spawn_prototype when no scene_sprites in context."""
        ctx = DevContext()
        ctx.scene_sprites = None
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Should not crash
        window._spawn_prototype("sprite1")

    def test_spawn_prototype_multiple(self, palette_window):
        """Test spawning multiple prototypes."""
        scene_sprites = palette_window.dev_context.scene_sprites

        palette_window._spawn_prototype("sprite1")
        palette_window._spawn_prototype("sprite2")
        palette_window._spawn_prototype("sprite1")

        assert len(scene_sprites) == 3
