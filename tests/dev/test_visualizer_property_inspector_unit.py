"""Unit tests for DevVisualizer property inspector integration."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import DevVisualizer


@pytest.fixture(autouse=True)
def _mock_arcade_text(mocker):
    def create_text(*args, **kwargs):
        text = mocker.MagicMock()
        text.y = kwargs.get("y", 0)
        text.text = args[0] if args else ""
        text.draw = mocker.MagicMock()
        return text

    mocker.patch("arcadeactions.dev.visualizer.arcade.Text", side_effect=create_text)


def _make_window_stub(mocker):
    window = mocker.MagicMock()
    window.closed = False
    window.current_view = None
    window.on_draw = mocker.MagicMock()
    window.on_key_press = mocker.MagicMock()
    window.on_mouse_press = mocker.MagicMock()
    window.on_mouse_drag = mocker.MagicMock()
    window.on_mouse_release = mocker.MagicMock()
    window.on_close = mocker.MagicMock()
    window.get_location = mocker.MagicMock(return_value=(100, 200))
    window.activate = mocker.MagicMock()
    window.show_view = mocker.MagicMock()
    window.set_location = mocker.MagicMock()
    window.width = 800
    window.height = 600
    return window


def test_alt_i_toggles_property_inspector_from_key_handler(mocker):
    """Alt+I should route through DevVisualizer key handling and toggle inspector."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    toggle_mock = mocker.patch.object(dev_viz, "toggle_property_inspector")

    handled = dev_viz.handle_key_press(arcade.key.I, arcade.key.MOD_ALT)

    assert handled is True
    toggle_mock.assert_called_once_with()


def test_toggle_property_inspector_creates_window_and_syncs_selection(mocker, test_sprite):
    """First toggle should create window and provide current selection context."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList([test_sprite]), window=window)
    dev_viz.selection_manager._selected.add(test_sprite)

    inspector_window = mocker.MagicMock()
    inspector_window.visible = False
    create_mock = mocker.patch.object(dev_viz, "_create_property_inspector_window")

    def _create():
        dev_viz.property_inspector_window = inspector_window

    create_mock.side_effect = _create

    dev_viz.toggle_property_inspector()

    inspector_window.set_selection.assert_called_once_with([test_sprite])
    inspector_window.show_window.assert_called_once()


def test_hide_does_not_clear_property_history(mocker, test_sprite):
    """Undo history should survive F12 show/hide toggles."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList([test_sprite]), window=window)
    history = dev_viz.property_history

    old_x = float(test_sprite.center_x)
    test_sprite.center_x = old_x + 10
    history.record_change(test_sprite, "center_x", old_x, old_x + 10)

    dev_viz.show()
    dev_viz.hide()

    assert history.undo(test_sprite) is not None
    assert test_sprite.center_x == old_x
