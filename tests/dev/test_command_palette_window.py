"""Tests for command palette secondary window routing and execution."""

from __future__ import annotations

import arcade
import pytest

import arcadeactions.dev.command_palette as command_palette_module
from arcadeactions.dev.command_palette import CommandPaletteWindow
from arcadeactions.dev.command_registry import CommandExecutionContext, CommandRegistry

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def force_headless_command_palette_window(mocker):
    """Force CommandPaletteWindow construction through headless fallback path."""
    mocker.patch.object(
        command_palette_module.arcade.Window,
        "__init__",
        side_effect=command_palette_module.GLException("headless test mode"),
    )
    mocker.patch.object(command_palette_module.arcade.Window, "on_close", return_value=None)


@pytest.fixture(autouse=True)
def mock_arcade_text(mocker):
    """Patch arcade.Text to keep tests deterministic in headless CI."""

    def make_text(*args, **kwargs):
        text = mocker.MagicMock()
        text.text = args[0] if args else kwargs.get("text", "")
        text.draw = mocker.MagicMock()
        text.y = kwargs.get("y", 0)
        return text

    mocker.patch("arcadeactions.dev.command_palette.arcade.Text", side_effect=make_text)


@pytest.fixture
def context(window):
    """Create a palette context for tests."""
    return CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])


def test_f8_closes_palette(window, context, mocker):
    """F8 toggles palette closed."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mock_hide = mocker.patch.object(palette, "hide_window")

    palette.on_key_press(arcade.key.F8, 0)

    mock_hide.assert_called_once()


def test_escape_closes_palette(window, context, mocker):
    """ESC closes palette."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mock_hide = mocker.patch.object(palette, "hide_window")

    palette.on_key_press(arcade.key.ESCAPE, 0)

    mock_hide.assert_called_once()


def test_enter_executes_highlighted_command(window, context):
    """Enter executes currently highlighted enabled command."""
    called: list[str] = []
    registry = CommandRegistry()
    registry.register_command(
        key=arcade.key.E,
        name="Export Scene",
        category="Export/Import",
        handler=lambda _ctx: called.append("export") or True,
    )
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)

    palette.on_key_press(arcade.key.ENTER, 0)

    assert called == ["export"]


def test_arrow_keys_cycle_enabled_commands(window, context):
    """Up/down update selected index across enabled command list."""
    registry = CommandRegistry()
    registry.register_command(key=arcade.key.E, name="Export", category="Export/Import", handler=lambda _ctx: True)
    registry.register_command(key=arcade.key.I, name="Import", category="Export/Import", handler=lambda _ctx: True)
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)

    assert palette.selected_index == 0
    palette.on_key_press(arcade.key.DOWN, 0)
    assert palette.selected_index == 1
    palette.on_key_press(arcade.key.UP, 0)
    assert palette.selected_index == 0


def test_quick_key_executes_enabled_command(window, context):
    """Quick key executes matching enabled command immediately."""
    called: list[str] = []
    registry = CommandRegistry()
    registry.register_command(
        key=arcade.key.E,
        name="Export Scene",
        category="Export/Import",
        handler=lambda _ctx: called.append("export") or True,
    )
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)

    palette.on_key_press(arcade.key.E, 0)

    assert called == ["export"]


def test_unhandled_key_forwards_to_main_window(window, context, mocker):
    """Unhandled keys are forwarded to main window dispatch_event."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mock_dispatch = mocker.patch.object(window, "dispatch_event")

    palette.on_key_press(arcade.key.W, 0)

    mock_dispatch.assert_called_once_with("on_key_press", arcade.key.W, 0)


def test_set_context_clamps_selected_index(window, context):
    """set_context should clamp selection index to enabled command list length."""
    registry = CommandRegistry()
    registry.register_command(key=arcade.key.E, name="Export", category="Export/Import", handler=lambda _ctx: True)
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    palette.selected_index = 5

    palette.set_context(context)

    assert palette.selected_index == 0


def test_move_selection_handles_empty_enabled_list(window, context):
    """Move selection should reset index when no enabled commands."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    palette.selected_index = 3

    palette._move_selection(1)

    assert palette.selected_index == 0


def test_execute_selected_swallows_handler_errors(window, context):
    """Executing selected command should not raise when command handler fails."""
    registry = CommandRegistry()
    registry.register_command(
        key=arcade.key.E,
        name="Export",
        category="Export/Import",
        handler=lambda _ctx: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)

    palette._execute_selected()


def test_on_key_release_forwards(window, context, mocker):
    """Key release events should forward to main window."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mock_dispatch = mocker.patch.object(window, "dispatch_event")

    palette.on_key_release(arcade.key.E, 0)

    mock_dispatch.assert_called_once_with("on_key_release", arcade.key.E, 0)


def test_forward_falls_back_to_direct_on_key_press(window, context, mocker):
    """Dispatch failures should fall back to direct main-window handler calls."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mocker.patch.object(window, "dispatch_event", side_effect=RuntimeError("dispatch failed"))
    mock_key_press = mocker.patch.object(window, "on_key_press")

    palette._forward_to_main_window("on_key_press", arcade.key.W, 0)

    mock_key_press.assert_called_once_with(arcade.key.W, 0)


def test_forward_falls_back_to_direct_on_key_release(window, context, mocker):
    """Dispatch failures should fall back for key release handlers."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mocker.patch.object(window, "dispatch_event", side_effect=RuntimeError("dispatch failed"))
    mock_key_release = mocker.patch.object(window, "on_key_release")

    palette._forward_to_main_window("on_key_release", arcade.key.W, 0)

    mock_key_release.assert_called_once_with(arcade.key.W, 0)


def test_on_draw_renders_enabled_and_disabled_commands(window, context, mocker):
    """on_draw should render command rows with both enabled and disabled states."""
    registry = CommandRegistry()
    registry.register_command(key=arcade.key.E, name="Export", category="Export/Import", handler=lambda _ctx: True)
    registry.register_command(
        key=arcade.key.G,
        name="Grid",
        category="Visualization",
        handler=lambda _ctx: True,
        enabled_check=lambda _ctx: False,
    )
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    palette._is_headless = False
    palette._title_text = mocker.MagicMock()
    mock_clear = mocker.patch.object(palette, "clear")

    palette.on_draw()

    mock_clear.assert_called_once()
    assert palette._title_text.draw.called


def test_on_close_calls_callback(window, context):
    """on_close should notify callback."""
    called = {"closed": False}

    def on_close():
        called["closed"] = True

    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window, on_close_callback=on_close)
    palette._is_headless = True

    palette.on_close()
    assert called["closed"] is True


def test_key_label_falls_back_when_symbol_string_missing():
    """_key_label should fallback to numeric string when symbol helper is unavailable."""
    label = CommandPaletteWindow._key_label(42)
    assert label


def test_on_draw_returns_early_in_headless_mode(window, context, mocker):
    """Headless mode should bypass draw operations."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    palette._is_headless = True
    mock_clear = mocker.patch.object(palette, "clear")

    palette.on_draw()

    mock_clear.assert_not_called()


def test_forward_returns_when_no_main_window(window, context):
    """Forwarding should no-op when main window is absent."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=None)
    palette._forward_to_main_window("on_key_press", arcade.key.A, 0)


def test_forward_swallows_fallback_exceptions(window, context, mocker):
    """Forwarding should swallow errors if both dispatch and direct fallback fail."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    mocker.patch.object(window, "dispatch_event", side_effect=RuntimeError("dispatch failed"))
    mocker.patch.object(window, "on_key_press", side_effect=RuntimeError("fallback failed"))

    palette._forward_to_main_window("on_key_press", arcade.key.A, 0)
