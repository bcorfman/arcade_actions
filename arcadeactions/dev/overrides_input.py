"""Overrides panel input helpers."""

from __future__ import annotations

from typing import Protocol

import arcade


class OverridesPanelInput(Protocol):
    """Protocol for overrides panel input handling."""

    editing: bool
    _editing_field: str

    def is_open(self) -> bool: ...

    def handle_key(self, key: str) -> None: ...

    def commit_edit(self) -> None: ...

    def start_edit(self, field: str | None = None) -> None: ...

    def cancel_edit(self) -> None: ...

    def handle_input_char(self, text: str) -> None: ...

    def select_prev(self) -> None: ...

    def select_next(self) -> None: ...

    def increment_selected(self, dx: int, dy: int) -> None: ...

    def get_selected(self) -> dict | None: ...

    def remove_override(self, row: int | None, col: int | None) -> None: ...


def handle_overrides_panel_key(panel: OverridesPanelInput | None, key: int, modifiers: int) -> bool:
    """Handle overrides panel-specific key input."""
    if panel is None or not panel.is_open():
        return False

    if _handle_undo(panel, key, modifiers):
        return True
    handled = _handle_editing_keys(panel, key)
    if handled is not None:
        return handled
    return _handle_navigation_keys(panel, key)


def _handle_undo(panel: OverridesPanelInput, key: int, modifiers: int) -> bool:
    if key != arcade.key.Z or not (modifiers & arcade.key.MOD_CTRL):
        return False
    try:
        panel.handle_key("CTRL+Z")
    except Exception:
        pass
    return True


def _handle_editing_keys(panel: OverridesPanelInput, key: int) -> bool | None:
    if key == arcade.key.ENTER:
        if panel.editing:
            panel.commit_edit()
        else:
            panel.start_edit()
        return True
    if key == arcade.key.ESCAPE:
        if panel.editing:
            panel.cancel_edit()
            return True
        return False
    if key == arcade.key.X:
        panel.start_edit("x")
        return True
    if key == arcade.key.Y:
        panel.start_edit("y")
        return True
    if key == arcade.key.TAB:
        if panel.editing:
            panel._editing_field = "y" if panel._editing_field == "x" else "x"
            return True
        return None
    if key == arcade.key.BACKSPACE and panel.editing:
        panel.handle_input_char("\b")
        return True
    return None


def _handle_navigation_keys(panel: OverridesPanelInput, key: int) -> bool:
    if key == arcade.key.UP:
        return False
    if key == arcade.key.DOWN:
        panel.select_next()
        return True
    if key == arcade.key.LEFT:
        panel.increment_selected(-1, 0)
        return True
    if key == arcade.key.RIGHT:
        panel.increment_selected(1, 0)
        return True
    if key == arcade.key.PAGEUP:
        panel.increment_selected(0, 1)
        return True
    if key == arcade.key.PAGEDOWN:
        panel.increment_selected(0, -1)
        return True
    if key == arcade.key.DELETE:
        selected = panel.get_selected()
        if selected:
            panel.remove_override(selected.get("row"), selected.get("col"))
        return True
    return False


def handle_overrides_panel_text(panel: OverridesPanelInput | None, text: str) -> bool:
    """Handle text input for overrides panel editing."""
    if panel is None or not panel.is_open() or not panel.editing:
        return False

    try:
        for ch in text:
            panel.handle_input_char(ch)
    except Exception:
        pass
    return True
