"""Tests for command palette secondary window routing and execution."""

from __future__ import annotations

from unittest.mock import MagicMock

import arcade
import pytest

from arcadeactions.dev.command_palette import CommandPaletteWindow
from arcadeactions.dev.command_registry import CommandExecutionContext, CommandRegistry

pytestmark = pytest.mark.slow


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


def test_unhandled_key_forwards_to_main_window(window, context):
    """Unhandled keys are forwarded to main window dispatch_event."""
    registry = CommandRegistry()
    palette = CommandPaletteWindow(registry=registry, context=context, main_window=window)
    window.dispatch_event = MagicMock()

    palette.on_key_press(arcade.key.W, 0)

    window.dispatch_event.assert_called_once_with("on_key_press", arcade.key.W, 0)

