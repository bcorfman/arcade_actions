"""Tests for PaletteWindow lifecycle methods."""

from __future__ import annotations

from unittest.mock import MagicMock

import arcade
import pytest

from arcadeactions.dev.palette_window import PaletteWindow
from arcadeactions.dev.prototype_registry import DevContext, SpritePrototypeRegistry

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


class TestWindowLifecycle:
    """Test window lifecycle methods."""

    def test_on_close_callback_invocation(self, registry):
        """Test on_close callback is invoked."""
        callback_called = []

        def on_close():
            callback_called.append(True)

        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=on_close,
            forward_key_handler=lambda k, m: False,
        )

        window.on_close()

        assert len(callback_called) == 1

    def test_on_close_no_callback(self, registry):
        """Test on_close handles None callback."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=None,
            forward_key_handler=lambda k, m: False,
        )

        # Should not crash
        window.on_close()

    def test_set_visible_error_handling(self, palette_window, mocker):
        """Test set_visible handles errors gracefully."""
        mock_main_window = MagicMock()
        palette_window._main_window = mock_main_window

        # Mock super().set_visible to raise exception
        mock_super_set_visible = mocker.patch.object(
            PaletteWindow.__bases__[0], "set_visible", side_effect=Exception("Error")
        )

        # Should not crash, should update _is_visible
        palette_window.set_visible(True)

        assert palette_window._is_visible is True

    def test_set_visible_headless_mode(self, palette_window):
        """Test set_visible in headless mode."""
        palette_window._is_headless = True

        palette_window.set_visible(True)
        assert palette_window._is_visible is True

        palette_window.set_visible(False)
        assert palette_window._is_visible is False
