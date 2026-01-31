"""Unit tests for overrides panel input helpers."""

from __future__ import annotations

import arcade

from arcadeactions.dev import overrides_input


class StubPanel:
    def __init__(self) -> None:
        self._open = True
        self.editing = False
        self._editing_field = "x"
        self.calls: list[tuple[str, object]] = []

    def is_open(self) -> bool:
        return self._open

    def handle_key(self, key: str) -> None:
        self.calls.append(("handle_key", key))

    def commit_edit(self) -> None:
        self.calls.append(("commit_edit", None))

    def start_edit(self, field: str | None = None) -> None:
        self.calls.append(("start_edit", field))

    def cancel_edit(self) -> None:
        self.calls.append(("cancel_edit", None))

    def handle_input_char(self, text: str) -> None:
        self.calls.append(("handle_input_char", text))

    def select_prev(self) -> None:
        self.calls.append(("select_prev", None))

    def select_next(self) -> None:
        self.calls.append(("select_next", None))

    def increment_selected(self, dx: int, dy: int) -> None:
        self.calls.append(("increment_selected", (dx, dy)))

    def get_selected(self) -> dict | None:
        return {"row": 1, "col": 2}

    def remove_override(self, row: int | None, col: int | None) -> None:
        self.calls.append(("remove_override", (row, col)))


def test_handle_overrides_panel_key_ctrl_z():
    panel = StubPanel()

    handled = overrides_input.handle_overrides_panel_key(panel, arcade.key.Z, arcade.key.MOD_CTRL)

    assert handled is True
    assert ("handle_key", "CTRL+Z") in panel.calls


def test_handle_overrides_panel_key_enter_starts_edit():
    panel = StubPanel()

    handled = overrides_input.handle_overrides_panel_key(panel, arcade.key.ENTER, 0)

    assert handled is True
    assert ("start_edit", None) in panel.calls


def test_handle_overrides_panel_text_routes_chars():
    panel = StubPanel()
    panel.editing = True

    handled = overrides_input.handle_overrides_panel_text(panel, "12")

    assert handled is True
    assert ("handle_input_char", "1") in panel.calls
    assert ("handle_input_char", "2") in panel.calls


def test_handle_overrides_panel_key_up_returns_false():
    panel = StubPanel()

    handled = overrides_input.handle_overrides_panel_key(panel, arcade.key.UP, 0)

    assert handled is False
    assert ("select_prev", None) not in panel.calls


def test_handle_overrides_panel_key_down_selects_next():
    panel = StubPanel()

    handled = overrides_input.handle_overrides_panel_key(panel, arcade.key.DOWN, 0)

    assert handled is True
    assert ("select_next", None) in panel.calls
