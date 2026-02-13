"""Focused unit tests for arcadeactions.dev.visualizer_keys helpers."""

from __future__ import annotations

import arcade

from arcadeactions.dev import visualizer_keys


class _StubSelectionManager:
    def __init__(self, selected: list[object] | None = None) -> None:
        self._selected = selected or []

    def get_selected(self) -> list[object]:
        return list(self._selected)


class _StubDevViz:
    def __init__(self, *, selected: list[object] | None = None, toggle_result: bool = False) -> None:
        self.selection_manager = _StubSelectionManager(selected=selected)
        self.scene_sprites = []
        self.overrides_panel = object()
        self._toggle_result = toggle_result
        self.toggle_calls: list[object | None] = []

    def toggle_overrides_panel_for_sprite(self, sprite: object | None = None) -> bool:
        self.toggle_calls.append(sprite)
        return self._toggle_result


def test_handle_key_press_o_reports_when_selected_sprite_is_not_override_compatible(capsys):
    """Pressing O with selected sprite should print warning if panel toggle fails."""
    sprite = object()
    dev_viz = _StubDevViz(selected=[sprite], toggle_result=False)

    handled = visualizer_keys.handle_key_press(dev_viz, arcade.key.O, 0)

    assert handled is True
    assert dev_viz.toggle_calls == [sprite]
    assert "Overrides panel unavailable" in capsys.readouterr().out
