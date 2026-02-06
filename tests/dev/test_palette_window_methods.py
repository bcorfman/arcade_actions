"""Tests for PaletteWindow methods to improve coverage."""

from __future__ import annotations

import os

import pytest

from arcadeactions.dev.palette_window import PaletteWindow
from arcadeactions.dev.prototype_registry import DevContext, get_registry
from tests.conftest import ActionTestBase

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.fixture(autouse=True)
def prevent_palette_window_showing_in_ci(monkeypatch):
    """Prevent PaletteWindow from popping up when running locally with CI=true."""
    if os.environ.get("CI") == "true":
        monkeypatch.setattr(PaletteWindow.__bases__[0], "set_visible", lambda *_args, **_kwargs: None)
    yield


class TestPaletteWindowMethods(ActionTestBase):
    """Test PaletteWindow methods that don't require full window context."""

    def test_palette_window_get_size(self, window):
        """Test get_size method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        width, height = palette.get_size()

        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0

    def test_palette_window_set_size(self, window):
        """Test set_size method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        palette.set_size(400, 300)

        width, height = palette.get_size()
        assert width == 400
        assert height == 300

    def test_palette_window_clear(self, window):
        """Test clear method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Should not crash
        palette.clear()

    def test_palette_window_get_location(self, window, mocker):
        """Test get_location method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Mock window.get_location if available
        if hasattr(palette, "get_location"):
            location = palette.get_location()
            assert location is None or (isinstance(location, tuple) and len(location) == 2)

    def test_palette_window_set_location(self, window, mocker):
        """Test set_location method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Should not crash
        palette.set_location(100, 200)

    def test_palette_window_visible_property(self, window):
        """Test visible property."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Initially not visible
        assert not palette.visible

    def test_palette_window_set_visible(self, window):
        """Test set_visible method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        palette.set_visible(True)
        assert palette.visible

        palette.set_visible(False)
        assert not palette.visible

    def test_palette_window_get_dragging_prototype(self, window):
        """Test get_dragging_prototype method."""
        palette = PaletteWindow(
            registry=get_registry(),
            ctx=DevContext(),
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
        )

        # Initially no dragging prototype
        result = palette.get_dragging_prototype()
        assert result is None
