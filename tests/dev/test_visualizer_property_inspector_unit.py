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


def test_toggle_property_inspector_hides_when_already_visible(mocker):
    """Second toggle should hide inspector and re-activate main window."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    inspector_window = mocker.MagicMock()
    inspector_window.visible = True
    dev_viz.property_inspector_window = inspector_window
    activate = mocker.patch.object(dev_viz, "_activate_main_window")

    dev_viz.toggle_property_inspector()

    inspector_window.hide_window.assert_called_once()
    activate.assert_called_once()


def test_create_property_inspector_window_builds_components(mocker):
    """Creation should instantiate inspector model and window wrapper."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_window = mocker.MagicMock()
    ctor_model = mocker.patch("arcadeactions.dev.visualizer.SpritePropertyInspector", return_value=mocker.MagicMock())
    ctor_window = mocker.patch("arcadeactions.dev.visualizer.PropertyInspectorWindow", return_value=mock_window)
    position = mocker.patch.object(dev_viz, "_position_property_inspector_window")

    dev_viz._create_property_inspector_window()

    ctor_model.assert_called_once()
    ctor_window.assert_called_once()
    position.assert_called_once()
    assert dev_viz.property_inspector_window is mock_window


def test_position_property_inspector_window_sets_location(mocker):
    """Positioning should place inspector to the left of the main window."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    inspector_window = mocker.MagicMock()
    inspector_window.width = 360
    dev_viz.property_inspector_window = inspector_window
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)

    dev_viz._position_property_inspector_window()

    inspector_window.set_location.assert_called_once_with(-268, 200)


def test_position_property_inspector_window_returns_on_errors(mocker):
    """Positioning should no-op if location checks fail or set_location raises."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    inspector_window = mocker.MagicMock()
    inspector_window.width = 360
    dev_viz.property_inspector_window = inspector_window

    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=False)
    dev_viz._position_property_inspector_window()
    inspector_window.set_location.assert_not_called()

    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
    inspector_window.set_location.side_effect = RuntimeError("boom")
    dev_viz._position_property_inspector_window()


def test_reset_scene_syncs_existing_property_inspector_selection(mocker, test_sprite):
    """reset_scene should refresh inspector selection when inspector window exists."""
    window = _make_window_stub(mocker)
    original_list = arcade.SpriteList([test_sprite])
    dev_viz = DevVisualizer(scene_sprites=original_list, window=window)
    inspector_window = mocker.MagicMock()
    dev_viz.property_inspector_window = inspector_window
    new_list = arcade.SpriteList([test_sprite])

    dev_viz.reset_scene(new_list)

    inspector_window.set_selection.assert_called_once_with([])


def test_detach_closes_property_inspector_window(mocker):
    """detach_from_window should close property inspector window and clear reference."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    dev_viz._attached = True
    dev_viz._original_on_draw = window.on_draw
    dev_viz._original_on_key_press = window.on_key_press
    dev_viz._original_on_mouse_press = window.on_mouse_press
    dev_viz._original_on_mouse_drag = window.on_mouse_drag
    dev_viz._original_on_mouse_release = window.on_mouse_release
    dev_viz._original_on_close = window.on_close
    inspector_window = mocker.MagicMock()
    dev_viz.property_inspector_window = inspector_window

    dev_viz.detach_from_window()

    inspector_window.close.assert_called_once()
    assert dev_viz.property_inspector_window is None


def test_selection_sync_called_from_mouse_press_and_release(mocker):
    """Selection sync should run after selection manager handles click/marquee release."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    sync = mocker.patch.object(dev_viz, "_sync_property_inspector_selection")
    mocker.patch("arcadeactions.dev.visualizer.arcade.get_sprites_at_point", return_value=[])
    dev_viz.selection_manager.handle_mouse_press = mocker.MagicMock(return_value=True)

    assert dev_viz.handle_mouse_press(10, 10, arcade.MOUSE_BUTTON_LEFT, 0) is True
    sync.assert_called_once()

    dev_viz.selection_manager._is_dragging_marquee = True
    dev_viz.selection_manager.handle_mouse_release = mocker.MagicMock()
    dev_viz.handle_mouse_release(10, 10, arcade.MOUSE_BUTTON_LEFT, 0)
    assert sync.call_count == 2


def test_draw_syncs_property_inspector_selection_before_render(mocker):
    """draw should sync inspector selection before delegating overlay draw."""
    window = _make_window_stub(mocker)
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    dev_viz.visible = True
    sync = mocker.patch.object(dev_viz, "_sync_property_inspector_selection")
    draw_overlay = mocker.patch("arcadeactions.dev.visualizer.visualizer_draw.draw_visualizer")

    dev_viz.draw()

    sync.assert_called_once()
    draw_overlay.assert_called_once_with(dev_viz)
