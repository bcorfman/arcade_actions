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
