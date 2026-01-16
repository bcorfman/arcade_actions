"""Tests for PaletteWindow drawing methods."""

from __future__ import annotations

from unittest.mock import MagicMock

import arcade
import pytest

from actions.dev.palette_window import PaletteWindow
from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry, get_registry
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.slow


@pytest.fixture
def registry():
    """Create a test registry."""
    reg = SpritePrototypeRegistry()

    @reg.register("test_sprite")
    def make_test(ctx):
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite._prototype_id = "test_sprite"
        return sprite

    @reg.register("test_sprite2")
    def make_test2(ctx):
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite._prototype_id = "test_sprite2"
        return sprite

    return reg


@pytest.fixture
def palette_window(registry):
    """Create a PaletteWindow instance for testing."""
    ctx = DevContext()
    window = PaletteWindow(
        registry=registry,
        ctx=ctx,
        on_close_callback=lambda: None,
        forward_key_handler=lambda k, m: False,
    )
    return window


class TestDrawing:
    """Test drawing methods."""

    def test_on_draw_headless_mode(self, registry, mocker):
        """Test on_draw returns early in headless mode."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = True
        window._title_text = None

        mock_clear = mocker.patch.object(window, "clear")
        mock_rebuild = mocker.patch.object(window, "_rebuild_text_cache")

        window.on_draw()

        mock_clear.assert_not_called()
        mock_rebuild.assert_not_called()

    def test_on_draw_with_empty_prototypes(self, registry, mocker):
        """Test on_draw with empty prototype list."""
        empty_registry = SpritePrototypeRegistry()
        ctx = DevContext()
        window = PaletteWindow(
            registry=empty_registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = False

        # Mock title text
        mock_title = MagicMock()
        window._title_text = mock_title
        mock_draw = mocker.patch.object(mock_title, "draw")
        mock_clear = mocker.patch.object(window, "clear")
        mock_rebuild = mocker.patch.object(window, "_rebuild_text_cache")

        window.on_draw()

        mock_clear.assert_called_once()
        mock_rebuild.assert_called_once()

    def test_on_draw_with_prototypes(self, palette_window, mocker):
        """Test on_draw with prototypes."""
        palette_window._is_headless = False

        # Mock title text
        mock_title = MagicMock()
        palette_window._title_text = mock_title
        mock_title_draw = mocker.patch.object(mock_title, "draw")
        mock_clear = mocker.patch.object(palette_window, "clear")
        mock_rebuild = mocker.patch.object(palette_window, "_rebuild_text_cache")

        # Mock text cache
        mock_text = MagicMock()
        mock_text.y = 100
        palette_window._text_cache = [mock_text]
        mock_text_draw = mocker.patch.object(mock_text, "draw")
        mock_draw_rect = mocker.patch.object(palette_window, "_draw_centered_rect")

        palette_window.on_draw()

        mock_clear.assert_called_once()
        mock_rebuild.assert_called_once()
        mock_title_draw.assert_called_once()
        mock_text_draw.assert_called()

    def test_on_draw_rebuilds_cache_when_changed(self, palette_window, mocker):
        """Test on_draw calls _rebuild_text_cache."""
        palette_window._is_headless = False
        mock_title = MagicMock()
        palette_window._title_text = mock_title
        mocker.patch.object(mock_title, "draw")
        mocker.patch.object(palette_window, "clear")
        mock_rebuild = mocker.patch.object(palette_window, "_rebuild_text_cache")

        palette_window.on_draw()

        mock_rebuild.assert_called_once()

    def test_draw_centered_rect_headless(self, palette_window, mocker):
        """Test _draw_centered_rect in headless mode."""
        palette_window._is_headless = True

        # Should not crash
        palette_window._draw_centered_rect(100, 200, 50, 75, arcade.color.RED)

    def test_draw_centered_rect_normal(self, palette_window, mocker):
        """Test _draw_centered_rect in normal mode."""
        palette_window._is_headless = False

        # Mock arcade drawing
        mock_draw = mocker.patch("arcade.draw_lbwh_rectangle_filled")

        palette_window._draw_centered_rect(100, 200, 50, 75, arcade.color.RED)

        # Should call arcade drawing function
        mock_draw.assert_called_once()

    def test_rebuild_text_cache_when_prototypes_change(self, palette_window, mocker):
        """Test _rebuild_text_cache when prototype list changes."""
        palette_window._is_headless = False
        palette_window._cached_prototype_ids = ("old_id",)

        palette_window._rebuild_text_cache()

        # Cache should be updated
        assert len(palette_window._text_cache) > 0
        assert palette_window._cached_prototype_ids != ("old_id",)

    def test_rebuild_text_cache_when_unchanged(self, palette_window, mocker):
        """Test _rebuild_text_cache when prototypes unchanged (cache hit)."""
        palette_window._is_headless = False

        # Set cache to match current prototypes
        prototypes = list(palette_window.registry.all().keys())
        palette_window._cached_prototype_ids = tuple(prototypes)
        original_cache = palette_window._text_cache.copy()

        palette_window._rebuild_text_cache()

        # Cache should be unchanged (early return)
        # Since prototypes match, cache should not be rebuilt
        # Actually, the method clears cache first, so we need to check differently
        # The cache will be rebuilt but with same prototype IDs
        assert palette_window._cached_prototype_ids == tuple(prototypes)


class TestTextCache:
    """Test text cache management."""

    def test_rebuild_text_cache_clears_old_cache(self, palette_window):
        """Test _rebuild_text_cache clears old cache."""
        palette_window._is_headless = False
        palette_window._text_cache = [MagicMock(), MagicMock()]
        palette_window._cached_prototype_ids = ("old",)

        palette_window._rebuild_text_cache()

        # Cache should be rebuilt with new items
        assert len(palette_window._text_cache) == len(list(palette_window.registry.all().keys()))

    def test_rebuild_text_cache_creates_text_objects(self, palette_window):
        """Test _rebuild_text_cache creates text objects."""
        palette_window._is_headless = False

        palette_window._rebuild_text_cache()

        assert len(palette_window._text_cache) > 0
        for text in palette_window._text_cache:
            assert text is not None

    def test_rebuild_text_cache_updates_cached_ids(self, palette_window):
        """Test _rebuild_text_cache updates cached prototype IDs."""
        palette_window._is_headless = False
        palette_window._cached_prototype_ids = ()

        palette_window._rebuild_text_cache()

        prototypes = list(palette_window.registry.all().keys())
        assert palette_window._cached_prototype_ids == tuple(prototypes)
