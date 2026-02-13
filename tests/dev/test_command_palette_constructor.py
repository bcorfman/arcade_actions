"""Constructor-focused tests for CommandPaletteWindow backend edge cases."""

from __future__ import annotations

import arcade

import arcadeactions.dev.command_palette as command_palette_module
from arcadeactions.dev.command_palette import CommandPaletteWindow
from arcadeactions.dev.command_registry import CommandExecutionContext, CommandRegistry


def test_constructor_handles_set_visible_called_during_super_init(mocker):
    """Palette constructor should tolerate backends that call set_visible early."""

    def fake_window_init(self, *args, **kwargs):
        self._width = kwargs.get("width")
        self._height = kwargs.get("height")
        self.set_visible(kwargs.get("visible", True))

    base_window_cls = CommandPaletteWindow.__mro__[1]
    mocker.patch.object(base_window_cls, "__init__", autospec=True, side_effect=fake_window_init)
    mocker.patch("arcadeactions.dev.command_palette.arcade.Text")

    registry = CommandRegistry()
    context = CommandExecutionContext(window=mocker.MagicMock(), scene_sprites=arcade.SpriteList(), selection=[])

    palette = CommandPaletteWindow(registry=registry, context=context, main_window=None)

    assert palette._is_headless is False
    assert palette.visible is False
    assert palette._command_context is context
    assert getattr(palette, "_context", None) is not context


def test_key_label_uses_pyglet_fallback_when_arcade_symbol_string_missing(mocker):
    """_key_label should use pyglet symbol_string if arcade helper is unavailable."""
    e_symbol = arcade.key.E
    mocker.patch.object(command_palette_module.arcade, "key", object())
    pyglet_key = mocker.MagicMock()
    pyglet_key.symbol_string.return_value = "E"
    mocker.patch.object(command_palette_module, "pyglet_key", pyglet_key)

    assert CommandPaletteWindow._key_label(e_symbol) == "E"


def test_key_label_falls_back_to_numeric_when_all_helpers_unavailable(mocker):
    """_key_label should return numeric fallback if no symbol helper is available."""
    mocker.patch.object(command_palette_module.arcade, "key", object())
    mocker.patch.object(command_palette_module, "pyglet_key", None)

    assert CommandPaletteWindow._key_label(42) == "42"
