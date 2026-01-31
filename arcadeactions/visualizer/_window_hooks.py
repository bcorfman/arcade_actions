"""Window hook helpers for ACE visualizer attach."""

from __future__ import annotations

from typing import Any

import arcade
from arcade import window_commands

from arcadeactions.visualizer._session import VisualizerSession, _VISUALIZER_SESSION, is_visualizer_attached


def _install_window_handler(session: VisualizerSession) -> None:
    """Register window hooks so the overlay renders and function keys work."""

    window = _get_active_window()
    if window is None:
        return

    if session.window is not None and session.window is not window:
        _remove_window_handler(session)

    _wrap_on_draw(session, window)
    _wrap_on_key_press(session, window)
    _wrap_on_close(session, window)

    session.window = window


def _remove_window_handler(session: VisualizerSession) -> None:
    """Remove any previously registered draw handler."""

    if session.window is None:
        _clear_original_handlers(session)
        return

    _restore_handler(
        session.window,
        "on_draw",
        "__visualizer_overlay__",
        session.original_window_on_draw,
    )
    _restore_handler(
        session.window,
        "on_key_press",
        "__visualizer_key__",
        session.original_window_on_key_press,
    )
    _restore_handler(
        session.window,
        "on_close",
        "__visualizer_close__",
        session.original_window_on_close,
    )

    session.window = None
    _clear_original_handlers(session)


def _get_active_window() -> arcade.Window | None:
    try:
        return arcade.get_window()
    except RuntimeError:
        return None


def _wrap_on_draw(session: VisualizerSession, window: arcade.Window) -> None:
    current_on_draw = getattr(window, "on_draw", None)
    if current_on_draw is None:
        return
    if getattr(current_on_draw, "__visualizer_overlay__", False):
        session.original_window_on_draw = getattr(current_on_draw, "__visualizer_original__", None)
        return
    if session.original_window_on_draw is not None:
        return

    def overlay_on_draw(*args: Any, **kwargs: Any) -> Any:
        result: Any = None
        try:
            result = current_on_draw(*args, **kwargs)
        finally:
            if is_visualizer_attached() and _VISUALIZER_SESSION is session:
                _draw_overlay(session)
        return result

    overlay_on_draw.__visualizer_overlay__ = True
    overlay_on_draw.__visualizer_original__ = current_on_draw
    window.on_draw = overlay_on_draw  # type: ignore[assignment]
    session.original_window_on_draw = current_on_draw


def _draw_overlay(session: VisualizerSession) -> None:
    render_window = session.window
    previous_window: arcade.Window | None = None
    if render_window is not None:
        try:
            previous_window = _get_current_window_for_restore(render_window)
        except Exception:
            render_window = None
    try:
        session.renderer.draw()
        session.guide_renderer.draw()
    except Exception:
        pass
    if render_window is not None and previous_window is not render_window:
        window_commands.set_window(previous_window)


def _get_current_window_for_restore(render_window: arcade.Window) -> arcade.Window | None:
    try:
        previous_window = window_commands.get_window()
    except RuntimeError:
        previous_window = None
    if previous_window is not render_window:
        window_commands.set_window(render_window)
        render_window.switch_to()
    return previous_window


def _wrap_on_key_press(session: VisualizerSession, window: arcade.Window) -> None:
    current_on_key_press = getattr(window, "on_key_press", None)
    if current_on_key_press is None:
        return
    if getattr(current_on_key_press, "__visualizer_key__", False):
        session.original_window_on_key_press = getattr(current_on_key_press, "__visualizer_key_original__", None)
        return
    if session.original_window_on_key_press is not None:
        return

    def overlay_on_key_press(symbol: int, modifiers: int) -> bool:
        if _handle_debug_key(session, symbol, modifiers):
            return True

        result = current_on_key_press(symbol, modifiers)
        if result is None:
            return False
        return bool(result)

    overlay_on_key_press.__visualizer_key__ = True
    overlay_on_key_press.__visualizer_key_original__ = current_on_key_press
    window.on_key_press = overlay_on_key_press  # type: ignore[assignment]
    session.original_window_on_key_press = current_on_key_press


def _handle_debug_key(session: VisualizerSession, symbol: int, modifiers: int) -> bool:
    if not is_visualizer_attached() or _VISUALIZER_SESSION is not session:
        return False
    if session.control_manager is None:
        return False
    try:
        return bool(session.control_manager.handle_key_press(symbol, modifiers))
    except Exception:
        return False


def _wrap_on_close(session: VisualizerSession, window: arcade.Window) -> None:
    current_on_close = getattr(window, "on_close", None)
    if current_on_close is None:
        return
    if getattr(current_on_close, "__visualizer_close__", False):
        session.original_window_on_close = getattr(current_on_close, "__visualizer_close_original__", None)
        return
    if session.original_window_on_close is not None:
        return

    def overlay_on_close(*args: Any, **kwargs: Any) -> Any:
        _close_event_window(session)
        if current_on_close is not None:
            return current_on_close(*args, **kwargs)
        return None

    overlay_on_close.__visualizer_close__ = True
    overlay_on_close.__visualizer_close_original__ = current_on_close
    window.on_close = overlay_on_close  # type: ignore[assignment]
    session.original_window_on_close = current_on_close


def _close_event_window(session: VisualizerSession) -> None:
    if session.event_window is None:
        return
    try:
        session.event_window.close()
    except Exception as exc:
        print(f"[ACE] Error closing debugger window: {exc!r}")
    session.event_window = None


def _restore_handler(
    window: arcade.Window,
    handler_name: str,
    marker_attr: str,
    original_handler: Any,
) -> None:
    current_handler = getattr(window, handler_name, None)
    should_restore = getattr(current_handler, marker_attr, False)
    if original_handler is not None and should_restore:
        setattr(window, handler_name, original_handler)


def _clear_original_handlers(session: VisualizerSession) -> None:
    session.original_window_on_draw = None
    session.original_window_on_key_press = None
    session.original_window_on_close = None
