"""Unit tests for DevVisualizer event handler helpers."""

from __future__ import annotations

import types

import arcade

from arcadeactions.dev import event_handlers
from arcadeactions.dev import window_hooks as _window_hooks


class StubSprites:
    def __init__(self) -> None:
        self.draw_called = False

    def draw(self) -> None:
        self.draw_called = True


class StubTracker:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def track_known_position(self, _window, x: int, y: int) -> None:
        self.calls.append((x, y))


class StubHost:
    def __init__(self) -> None:
        self.visible = False
        self.window = None
        self.palette_window = None
        self.overrides_panel = None
        self.scene_sprites = StubSprites()
        self._is_detaching = False
        self._position_tracker = StubTracker()
        self._original_on_draw = None
        self._original_on_key_press = None
        self._original_on_mouse_press = None
        self._original_on_mouse_drag = None
        self._original_on_mouse_release = None
        self._original_on_close = None
        self._original_show_view = None
        self._original_set_location = None
        self.toggle_called = False
        self.toggle_palette_called = False

    def toggle(self) -> None:
        self.toggle_called = True

    def toggle_palette(self) -> None:
        self.toggle_palette_called = True

    def handle_key_press(self, _key: int, _modifiers: int) -> bool:
        return False

    def handle_mouse_press(self, _x: int, _y: int, _button: int, _modifiers: int) -> bool:
        return False

    def handle_mouse_drag(self, _x: int, _y: int, _dx: int, _dy: int, _buttons: int, _modifiers: int) -> bool:
        return False

    def handle_mouse_release(self, _x: int, _y: int, _button: int, _modifiers: int) -> bool:
        return False

    def draw(self) -> None:
        return None

    def hide(self) -> None:
        return None

    def _wrap_view_on_draw(self, view: arcade.View) -> None:
        event_handlers.wrap_view_handlers(self, view)


def test_wrap_window_handlers_draws_scene(monkeypatch):
    """Wrapped on_draw should call original draw and scene draw when context valid."""
    host = StubHost()
    window = types.SimpleNamespace()
    draw_calls: list[str] = []

    class StubScreen:
        def use(self) -> None:
            return None

    class StubCamera:
        def __init__(self) -> None:
            self.viewport = arcade.types.LBWH(0, 0, 1280, 720)

        def use(self) -> None:
            return None

    class StubCtx:
        def __init__(self) -> None:
            self.screen = StubScreen()
            self.scissor = None
            self.current_camera = None

    def original_draw():
        draw_calls.append("original")

    window.ctx = StubCtx()
    window.default_camera = StubCamera()
    window.current_camera = window.default_camera
    window.width = 1280
    window.height = 720
    window.on_draw = original_draw
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: None
    window.on_mouse_drag = lambda *_args: None
    window.on_mouse_release = lambda *_args: None
    window.on_close = lambda: None
    window.switch_to = lambda: None

    stub_commands = types.SimpleNamespace(get_window=lambda: window, set_window=lambda _w: None)
    monkeypatch.setattr(_window_hooks, "window_commands_module", stub_commands)

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: True)
    window.on_draw()

    assert draw_calls == ["original"]
    assert host.scene_sprites.draw_called is True


def test_wrap_window_handlers_handles_f12_toggle():
    """F12 should toggle the host."""
    host = StubHost()
    window = types.SimpleNamespace()
    window.on_draw = lambda: None
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: None
    window.on_mouse_drag = lambda *_args: None
    window.on_mouse_release = lambda *_args: None
    window.on_close = lambda: None
    window.switch_to = lambda: None

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: False)
    window.on_key_press(arcade.key.F12, 0)

    assert host.toggle_called is True


def test_wrap_window_handlers_wraps_show_view_and_set_location(monkeypatch):
    """show_view and set_location should be wrapped."""
    host = StubHost()
    window = types.SimpleNamespace()
    window.on_draw = lambda: None
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: None
    window.on_mouse_drag = lambda *_args: None
    window.on_mouse_release = lambda *_args: None
    window.on_close = lambda: None
    window.switch_to = lambda: None

    called = {"show": False}

    def original_show_view(_view):
        called["show"] = True

    window.show_view = original_show_view

    def original_set_location(x, y, *_args, **_kwargs):
        return None

    window.set_location = original_set_location

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: False)

    view = arcade.View()
    window.show_view(view)

    assert called["show"] is True
    window.set_location(10, 20)
    assert host._position_tracker.calls == [(10, 20)]


def test_wrap_view_handlers_text_input_routes_to_overrides_panel():
    """Wrapped on_text should route input to overrides panel when editing."""
    host = StubHost()
    host.overrides_panel = types.SimpleNamespace(
        is_open=lambda: True,
        editing=True,
        handle_input_char=lambda _ch: None,
    )
    captured: list[str] = []
    host.overrides_panel.handle_input_char = lambda ch: captured.append(ch)

    view = arcade.View()
    view.on_draw = lambda: None
    view.on_text = lambda _text: None

    event_handlers.wrap_view_handlers(host, view)
    view.on_text("ab")

    assert captured == ["a", "b"]


def test_wrap_window_handlers_escape_closes_window_when_visible():
    """ESC should close the window when palette window is missing."""
    host = StubHost()
    host.visible = True
    window = types.SimpleNamespace()
    window.on_draw = lambda: None
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: None
    window.on_mouse_drag = lambda *_args: None
    window.on_mouse_release = lambda *_args: None
    window.on_close = lambda: None
    window.switch_to = lambda: None
    window.closed = False
    window.close_called = False

    def close_window():
        window.close_called = True

    window.close = close_window

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: False)
    window.on_key_press(arcade.key.ESCAPE, 0)

    assert window.close_called is True


def test_wrap_window_handlers_mouse_calls_original_when_not_handled():
    """Mouse handlers should fall through to original handlers when not handled."""
    host = StubHost()
    window = types.SimpleNamespace()
    called = {"press": False, "drag": False, "release": False}
    window.on_draw = lambda: None
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: called.__setitem__("press", True)
    window.on_mouse_drag = lambda *_args: called.__setitem__("drag", True)
    window.on_mouse_release = lambda *_args: called.__setitem__("release", True)
    window.on_close = lambda: None
    window.switch_to = lambda: None

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: False)
    window.on_mouse_press(1, 2, 3, 4)
    window.on_mouse_drag(1, 2, 3, 4, 5, 6)
    window.on_mouse_release(1, 2, 3, 4)

    assert called == {"press": True, "drag": True, "release": True}


def test_wrap_window_handlers_on_close_hides_and_closes_palette():
    """on_close should hide and close the palette window."""
    host = StubHost()
    host.visible = True
    host.hide_called = False

    def hide():
        host.hide_called = True

    host.hide = hide

    palette = types.SimpleNamespace(closed=False)
    palette.close_called = False

    def close_palette():
        palette.close_called = True

    palette.close = close_palette
    host.palette_window = palette

    window = types.SimpleNamespace()
    window.on_draw = lambda: None
    window.on_key_press = lambda *_args: None
    window.on_mouse_press = lambda *_args: None
    window.on_mouse_drag = lambda *_args: None
    window.on_mouse_release = lambda *_args: None
    window.on_close = lambda: None
    window.switch_to = lambda: None

    event_handlers.wrap_window_handlers(host, window, has_window_context=lambda _w: False)
    window.on_close()

    assert host.hide_called is True
    assert palette.close_called is True
    assert host.palette_window is None


def test_wrap_view_handlers_escape_closes_palette_when_visible():
    """ESC should close palette window when visible in view handlers."""
    host = StubHost()
    host.visible = True
    palette = types.SimpleNamespace(closed=False)
    palette.close_called = False

    def close_palette():
        palette.close_called = True

    palette.close = close_palette
    host.palette_window = palette
    host.window = types.SimpleNamespace(closed=False, close=lambda: None)

    view = arcade.View()
    view.on_draw = lambda: None

    event_handlers.wrap_view_handlers(host, view)
    view.on_key_press(arcade.key.ESCAPE, 0)

    assert palette.close_called is True
    assert host.palette_window is None


def test_wrap_view_handlers_mouse_handled_blocks_original():
    """Mouse handlers should short-circuit when DevVisualizer handles them."""
    host = StubHost()
    host.visible = True
    host.handle_mouse_press = lambda *_args: True
    called = {"press": False}

    view = arcade.View()
    view.on_draw = lambda: None
    view.on_mouse_press = lambda *_args: called.__setitem__("press", True)

    event_handlers.wrap_view_handlers(host, view)
    view.on_mouse_press(1, 2, 3, 4)

    assert called["press"] is False
