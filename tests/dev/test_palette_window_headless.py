"""Tests for PaletteWindow headless mode."""

from __future__ import annotations

from unittest.mock import MagicMock

import arcade
import pytest

from actions.dev.palette_window import PaletteWindow
from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry
from tests.conftest import ActionTestBase


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


class TestHeadlessMode:
    """Test headless mode functionality."""

    def test_init_headless_mode_sets_attributes(self, registry, mocker):
        """Test _init_headless_mode sets headless attributes."""
        ctx = DevContext()
        # Create window that will trigger headless mode
        # We'll manually call _init_headless_mode to test it
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Manually set headless mode attributes
        window._init_headless_mode(250, 400, "Test Window")

        assert window._is_headless is True
        assert window._headless_width == 250
        assert window._headless_height == 400
        assert window._headless_scale == 1.0
        assert window._is_visible is False
        assert window.has_exit is False
        assert window.location == (0, 0)

    def test_headless_size_methods(self, registry):
        """Test size methods in headless mode."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = True
        window._headless_width = 300
        window._headless_height = 500

        width, height = window.get_size()

        assert width == 300
        assert height == 500

        window.set_size(400, 600)

        assert window._headless_width == 400
        assert window._headless_height == 600

    def test_headless_location_methods(self, registry):
        """Test location methods in headless mode."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = True
        window.location = (100, 200)

        location = window.get_location()

        assert location == (100, 200)

        window.set_location(150, 250)

        assert window.location == (150, 250)

    def test_headless_visibility_methods(self, registry):
        """Test visibility methods in headless mode."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = True

        assert not window.visible

        window.set_visible(True)

        assert window.visible

        window.set_visible(False)

        assert not window.visible

    def test_headless_clear(self, registry):
        """Test clear method in headless mode."""
        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )
        window._is_headless = True

        # Should not crash
        window.clear()
