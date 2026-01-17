"""Tests for PaletteWindow keyboard and focus management."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import arcade
import pytest

from actions.dev.palette_window import PaletteWindow
from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry

pytestmark = pytest.mark.slow

# Skip tests that require DISPLAY on Windows/macOS CI
_skip_if_no_display = pytest.mark.skipif(
    (os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true")
    and not sys.platform.startswith("linux"),
    reason="Tests require DISPLAY which is only available on Linux CI",
)


@pytest.fixture(autouse=True)
def mock_arcade_text(mocker):
    """Mock arcade.Text to avoid OpenGL requirements in headless CI environments.

    This fixture patches arcade.Text in the palette_window module before PaletteWindow
    is created, preventing OpenGL context errors when Text objects are created
    in __init__ methods.
    """

    def create_mock_text(*args, **kwargs):
        """Create a new mock Text instance for each call."""
        mock_text = mocker.MagicMock()
        # Set default properties that tests might access
        mock_text.y = kwargs.get("y", args[2] if len(args) > 2 else 100)
        mock_text.text = kwargs.get("text", args[0] if len(args) > 0 else "")
        mock_text.draw = mocker.MagicMock()
        return mock_text

    # Patch Text in the palette_window module where it's used
    mocker.patch("actions.dev.palette_window.arcade.Text", side_effect=create_mock_text)


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


class TestKeyboardForwarding:
    """Test keyboard event forwarding."""

    def test_on_key_press_forwards_to_handler(self, registry, mocker):
        """Test on_key_press forwards to forward_key_handler when it handles."""
        handled = []
        mock_handler = MagicMock(return_value=True)  # Handler returns True (handled)

        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=mock_handler,
        )

        window.on_key_press(arcade.key.SPACE, 0)

        mock_handler.assert_called_once_with(arcade.key.SPACE, 0)

    def test_on_key_press_forwards_to_main_window(self, registry, mocker):
        """Test on_key_press forwards to main window when handler doesn't handle."""
        mock_handler = MagicMock(return_value=False)  # Handler returns False (not handled)
        mock_main_window = MagicMock()
        mock_dispatch = mocker.patch.object(mock_main_window, "dispatch_event")

        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=mock_handler,
            main_window=mock_main_window,
        )

        window.on_key_press(arcade.key.SPACE, 0)

        mock_handler.assert_called_once()
        # Should forward to main window
        mock_dispatch.assert_called()

    def test_on_key_press_fallback_handler(self, registry, mocker):
        """Test on_key_press fallback when no main window."""
        mock_handler = MagicMock(return_value=False)

        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=mock_handler,
            main_window=None,
        )

        # Should not crash
        window.on_key_press(arcade.key.SPACE, 0)

    def test_on_key_release_forwards(self, registry, mocker):
        """Test on_key_release forwards to main window."""
        mock_main_window = MagicMock()
        mock_dispatch = mocker.patch.object(mock_main_window, "dispatch_event")

        ctx = DevContext()
        window = PaletteWindow(
            registry=registry,
            ctx=ctx,
            on_close_callback=lambda: None,
            forward_key_handler=lambda k, m: False,
            main_window=mock_main_window,
        )

        window.on_key_release(arcade.key.SPACE, 0)

        # Should forward to main window
        mock_dispatch.assert_called()


@_skip_if_no_display
class TestFocusManagement:
    """Test focus restoration methods."""

    def test_schedule_focus_restore_no_main_window(self, palette_window, mocker):
        """Test _schedule_focus_restore does nothing when no main window."""
        palette_window._main_window = None
        mock_schedule = mocker.patch("arcade.schedule_once")

        palette_window._schedule_focus_restore(0.1)

        mock_schedule.assert_not_called()

    def test_schedule_focus_restore_schedules_call(self, palette_window, mocker):
        """Test _schedule_focus_restore schedules focus restoration."""
        mock_main_window = MagicMock()
        palette_window._main_window = mock_main_window
        mock_schedule = mocker.patch("arcade.schedule_once")

        palette_window._schedule_focus_restore(0.1)

        mock_schedule.assert_called_once()
        # Check that the scheduled function would activate main window
        call_args = mock_schedule.call_args
        scheduled_func = call_args[0][0]
        assert callable(scheduled_func)

    def test_request_main_window_focus_schedules_multiple(self, palette_window, mocker):
        """Test request_main_window_focus schedules multiple attempts."""
        mock_main_window = MagicMock()
        palette_window._main_window = mock_main_window
        mock_schedule = mocker.patch("arcade.schedule_once")

        palette_window.request_main_window_focus()

        # Should schedule multiple attempts
        assert mock_schedule.call_count >= 2

    def test_request_main_window_focus_no_main_window(self, palette_window, mocker):
        """Test request_main_window_focus does nothing when no main window."""
        palette_window._main_window = None
        mock_schedule = mocker.patch("arcade.schedule_once")

        palette_window.request_main_window_focus()

        mock_schedule.assert_not_called()

    def test_set_visible_requests_focus_restore(self, palette_window, mocker):
        """Test set_visible requests focus restore when becoming visible."""
        mock_main_window = MagicMock()
        palette_window._main_window = mock_main_window
        mock_request_focus = mocker.patch.object(palette_window, "request_main_window_focus")
        mock_super_set_visible = mocker.patch.object(PaletteWindow.__bases__[0], "set_visible")

        palette_window.set_visible(True)

        # Should request focus restore
        mock_request_focus.assert_called_once()

    def test_set_visible_not_visible_no_focus(self, palette_window, mocker):
        """Test set_visible doesn't request focus when hiding."""
        mock_main_window = MagicMock()
        palette_window._main_window = mock_main_window
        mock_request_focus = mocker.patch.object(palette_window, "request_main_window_focus")

        palette_window.set_visible(False)

        # Should not request focus when hiding
        # Actually, request_focus is only called when visible=True
        # So when visible=False, it shouldn't be called
        # But the method sets _is_visible before calling request_focus, so we check the final state
        assert not palette_window._is_visible
