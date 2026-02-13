"""Unit tests for PropertyInspectorWindow keyboard and lifecycle behaviors."""

from __future__ import annotations

import arcade
import pytest

import arcadeactions.dev.property_inspector as inspector_module
from arcadeactions.dev.property_inspector import PropertyInspectorWindow


class _InspectorStub:
    def __init__(self) -> None:
        self._selection: list[arcade.Sprite] = []
        self._moves: list[int] = []
        self._applied: list[tuple[str, str]] = []
        self._copied_current = False
        self._pasted = False
        self._undo_count = 0
        self._redo_count = 0

    def set_selection(self, selection):
        self._selection = list(selection)

    def selection(self):
        return list(self._selection)

    def move_active_property(self, delta: int):
        self._moves.append(delta)

    def current_property(self):
        class _Prop:
            name = "is_collidable"
            editor_type = "bool"

        return _Prop()

    def apply_property_text(self, property_name: str, text: str):
        self._applied.append((property_name, text))
        return True

    def copy_current_property(self):
        self._copied_current = True
        return "sprite.center_x = 100"

    def paste_from_clipboard(self):
        self._pasted = True
        return True

    def undo(self):
        self._undo_count += 1
        return True

    def redo(self):
        self._redo_count += 1
        return True

    def copy_selection_as_python(self, _property_names=None):
        return "sprite.center_x = 123"

    def visible_properties(self):
        class _Prop:
            def __init__(self, category: str, name: str):
                self.category = category
                self.name = name

        return [_Prop("Position", "center_x"), _Prop("Transform", "angle")]


@pytest.fixture(autouse=True)
def _patch_window_and_text(mocker):
    mocker.patch.object(inspector_module.arcade.Window, "__init__", return_value=None)
    mocker.patch.object(inspector_module.arcade.Window, "set_visible", return_value=None)
    mocker.patch.object(inspector_module.arcade.Window, "on_close", return_value=None)

    def make_text(*args, **kwargs):
        text = mocker.MagicMock()
        text.y = kwargs.get("y", 0)
        text.draw = mocker.MagicMock()
        return text

    mocker.patch("arcadeactions.dev.property_inspector.arcade.Text", side_effect=make_text)


def _create_window(*, main_window=None, on_close_callback=None) -> tuple[PropertyInspectorWindow, _InspectorStub]:
    inspector = _InspectorStub()
    window = PropertyInspectorWindow(
        inspector=inspector,
        main_window=main_window,
        on_close_callback=on_close_callback,
    )
    window._is_headless = True
    window._headless_width = 360
    window._headless_height = 420
    window._is_visible = False
    window._width = 360
    window._height = 420
    window.clear = lambda: None
    return window, inspector


def test_show_and_hide_window_track_visibility():
    """Window visibility helpers should update tracked state."""
    window, _ = _create_window()

    window.show_window()
    assert window.visible is True

    window.hide_window()
    assert window.visible is False


def test_init_headless_mode_sets_expected_state():
    """Headless initialization helper should set deterministic fallback state."""
    window, _ = _create_window()

    window._init_headless_mode(320, 240, "Headless Inspector")

    assert window._is_headless is True
    assert window._headless_width == 320
    assert window._headless_height == 240
    assert window._title == "Headless Inspector"


def test_set_selection_delegates_to_inspector(test_sprite):
    """Selection updates should be delegated to the inspector model."""
    window, inspector = _create_window()

    window.set_selection([test_sprite])

    assert inspector.selection() == [test_sprite]


def test_wrapper_methods_delegate_to_inspector(test_sprite):
    """Window convenience methods should call underlying inspector methods."""
    window, inspector = _create_window()
    inspector.set_selection([test_sprite])

    assert window.apply_property_text("center_x", "123") is True
    assert window.undo() is True
    assert window.redo() is True
    snippet = window.copy_selection_as_python(["center_x"])
    assert "sprite.center_x" in snippet


def test_key_navigation_handles_up_down_and_tab():
    """Arrow/tab keys should cycle active property index."""
    window, inspector = _create_window()

    window.on_key_press(arcade.key.DOWN, 0)
    window.on_key_press(arcade.key.UP, 0)
    window.on_key_press(arcade.key.TAB, 0)
    window.on_key_press(arcade.key.TAB, arcade.key.MOD_SHIFT)

    assert inspector._moves == [1, -1, 1, -1]


def test_space_toggles_boolean_property(test_sprite):
    """Space should toggle active boolean property."""
    window, inspector = _create_window()
    test_sprite.is_collidable = True
    inspector.set_selection([test_sprite])

    window.on_key_press(arcade.key.SPACE, 0)

    assert inspector._applied == [("is_collidable", "false")]


def test_space_does_nothing_without_property_or_selection(mocker):
    """Space should no-op when current property is missing/non-bool or selection is empty."""
    window, inspector = _create_window()
    inspector.current_property = lambda: None
    window.on_key_press(arcade.key.SPACE, 0)
    assert inspector._applied == []

    class _NonBoolProp:
        name = "center_x"
        editor_type = "number"

    inspector.current_property = lambda: _NonBoolProp()
    window.on_key_press(arcade.key.SPACE, 0)
    assert inspector._applied == []

    class _BoolProp:
        name = "is_collidable"
        editor_type = "bool"

    inspector.current_property = lambda: _BoolProp()
    inspector.set_selection([])
    window.on_key_press(arcade.key.SPACE, 0)
    assert inspector._applied == []


def test_ctrl_shortcuts_delegate_to_inspector(mocker):
    """Ctrl+C/V/Z/Y should invoke copy/paste/undo/redo hooks."""
    window, inspector = _create_window()
    forward = mocker.patch.object(window, "_forward_to_main_window")

    window.on_key_press(arcade.key.C, arcade.key.MOD_CTRL)
    window.on_key_press(arcade.key.V, arcade.key.MOD_CTRL)
    window.on_key_press(arcade.key.Z, arcade.key.MOD_CTRL)
    window.on_key_press(arcade.key.Y, arcade.key.MOD_CTRL)

    assert inspector._copied_current is True
    assert inspector._pasted is True
    assert inspector._undo_count == 1
    assert inspector._redo_count == 1
    forward.assert_not_called()


def test_escape_hides_window():
    """Escape should hide the inspector window."""
    window, _ = _create_window()
    window.show_window()

    window.on_key_press(arcade.key.ESCAPE, 0)

    assert window.visible is False


def test_unhandled_key_forwards_to_main_window(mocker):
    """Unhandled keys should be forwarded to the main window."""
    main_window = mocker.MagicMock()
    window, _ = _create_window(main_window=main_window)

    window.on_key_press(arcade.key.A, 0)

    main_window.dispatch_event.assert_called_once_with("on_key_press", arcade.key.A, 0)


def test_forward_falls_back_to_main_window_handler(mocker):
    """Forwarding should fallback when dispatch_event fails."""
    main_window = mocker.MagicMock()
    main_window.dispatch_event.side_effect = RuntimeError("boom")
    window, _ = _create_window(main_window=main_window)

    window._forward_to_main_window(arcade.key.B, 0)

    main_window.on_key_press.assert_called_once_with(arcade.key.B, 0)


def test_forward_swallows_dispatch_and_fallback_failures(mocker):
    """Forward helper should swallow errors if both dispatch and fallback fail."""
    main_window = mocker.MagicMock()
    main_window.dispatch_event.side_effect = RuntimeError("dispatch boom")
    main_window.on_key_press.side_effect = RuntimeError("fallback boom")
    window, _ = _create_window(main_window=main_window)

    window._forward_to_main_window(arcade.key.C, 0)


def test_on_draw_returns_early_in_headless(mocker):
    """Headless mode should skip draw operations."""
    window, _ = _create_window()
    clear = mocker.patch.object(window, "clear")

    window.on_draw()

    clear.assert_not_called()


def test_on_draw_renders_text_rows(mocker):
    """Non-headless draw should render title and property rows."""
    window, inspector = _create_window()
    window._is_headless = False
    window._title_text = mocker.MagicMock()
    clear = mocker.patch.object(window, "clear")

    window.on_draw()

    clear.assert_called_once()
    assert window._title_text.draw.called
    assert len(inspector.visible_properties()) == 2


def test_on_draw_stops_when_rows_reach_bottom_margin(mocker):
    """Draw should stop rendering rows once bottom margin is reached."""
    window, inspector = _create_window()
    window._is_headless = False
    window._title_text = mocker.MagicMock()
    window._height = 90

    class _Prop:
        def __init__(self, i: int):
            self.category = "Category"
            self.name = f"prop_{i}"

    inspector.visible_properties = lambda: [_Prop(i) for i in range(20)]
    inspector.current_property = lambda: None
    clear = mocker.patch.object(window, "clear")

    window.on_draw()

    clear.assert_called_once()


def test_on_close_invokes_callback():
    """Close should notify callback before delegating to base close."""
    called = {"value": False}

    def on_close():
        called["value"] = True

    window, _ = _create_window(on_close_callback=on_close)

    window.on_close()

    assert called["value"] is True


def test_set_visible_swallows_super_errors(mocker):
    """set_visible should swallow backend visibility errors."""
    window, _ = _create_window()
    window._is_headless = False
    mocker.patch.object(inspector_module.arcade.Window, "set_visible", side_effect=RuntimeError("boom"))

    window.set_visible(True)
    assert window.visible is True
