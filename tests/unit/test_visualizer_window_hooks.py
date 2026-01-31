"""Unit tests for visualizer window hook helpers."""

from __future__ import annotations

from pathlib import Path

import arcade
import pytest

from arcadeactions.visualizer import _session
from arcadeactions.visualizer._session import VisualizerSession
from arcadeactions.visualizer._window_hooks import _install_window_handler, _remove_window_handler


class StubRenderer:
    def __init__(self) -> None:
        self.draw_calls = 0

    def draw(self) -> None:
        self.draw_calls += 1


class StubGuideRenderer:
    def __init__(self) -> None:
        self.draw_calls = 0

    def draw(self) -> None:
        self.draw_calls += 1


class StubControlManager:
    def __init__(self, handled: bool) -> None:
        self.handled = handled
        self.key_calls: list[tuple[int, int]] = []

    def handle_key_press(self, symbol: int, modifiers: int) -> bool:
        self.key_calls.append((symbol, modifiers))
        return self.handled


class StubEventWindow:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class StubWindow:
    def __init__(self) -> None:
        self.draw_calls = 0
        self.key_calls: list[tuple[int, int]] = []
        self.close_calls = 0
        self.switch_calls = 0

        self.on_draw = self._on_draw
        self.on_key_press = self._on_key_press
        self.on_close = self._on_close

    def _on_draw(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
        self.draw_calls += 1

    def _on_key_press(self, symbol: int, modifiers: int) -> None:
        self.key_calls.append((symbol, modifiers))

    def _on_close(self) -> None:
        self.close_calls += 1

    def switch_to(self) -> None:
        self.switch_calls += 1


@pytest.fixture(autouse=True)
def reset_visualizer_session() -> None:
    _session._VISUALIZER_SESSION = None
    yield
    _session._VISUALIZER_SESSION = None


def _make_session(*, control_manager: StubControlManager, event_window: StubEventWindow | None) -> VisualizerSession:
    renderer = StubRenderer()
    guide_renderer = StubGuideRenderer()
    return VisualizerSession(
        debug_store=object(),
        overlay=object(),
        renderer=renderer,
        guides=object(),
        condition_debugger=object(),
        timeline=object(),
        control_manager=control_manager,
        guide_renderer=guide_renderer,
        event_window=event_window,
        snapshot_directory=Path("."),
        sprite_positions_provider=None,
        target_names_provider=None,
        wrapped_update_all=lambda *_args, **_kwargs: None,
        previous_update_all=lambda *_args, **_kwargs: None,
        previous_debug_store=None,
        previous_enable_flag=False,
    )


def test_install_wraps_on_draw_and_renders(monkeypatch) -> None:
    """Hooked draw should call original and render overlays when attached."""
    window = StubWindow()
    set_calls: list[arcade.Window | None] = []

    monkeypatch.setattr(arcade, "get_window", lambda: window)
    monkeypatch.setattr(
        "arcadeactions.visualizer._window_hooks.window_commands.get_window", lambda: None
    )
    monkeypatch.setattr(
        "arcadeactions.visualizer._window_hooks.window_commands.set_window",
        lambda win: set_calls.append(win),
    )

    session = _make_session(control_manager=StubControlManager(False), event_window=None)
    _session._VISUALIZER_SESSION = session
    monkeypatch.setattr("arcadeactions.visualizer._window_hooks._VISUALIZER_SESSION", session)

    _install_window_handler(session)

    assert window.on_draw is not window._on_draw
    window.on_draw()

    assert window.draw_calls == 1
    assert session.renderer.draw_calls == 1
    assert session.guide_renderer.draw_calls == 1
    assert window.switch_calls == 1
    assert set_calls == [window, None]


def test_install_wraps_on_key_press_handled(monkeypatch) -> None:
    """When debug handler handles key press, original handler is skipped."""
    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    control_manager = StubControlManager(True)
    session = _make_session(control_manager=control_manager, event_window=None)
    _session._VISUALIZER_SESSION = session
    monkeypatch.setattr("arcadeactions.visualizer._window_hooks._VISUALIZER_SESSION", session)

    _install_window_handler(session)
    result = window.on_key_press(arcade.key.F4, 0)

    assert result is True
    assert control_manager.key_calls == [(arcade.key.F4, 0)]
    assert window.key_calls == []


def test_install_wraps_on_key_press_passthrough(monkeypatch) -> None:
    """When debug handler does not handle, original handler runs."""
    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    control_manager = StubControlManager(False)
    session = _make_session(control_manager=control_manager, event_window=None)
    _session._VISUALIZER_SESSION = session
    monkeypatch.setattr("arcadeactions.visualizer._window_hooks._VISUALIZER_SESSION", session)

    _install_window_handler(session)
    result = window.on_key_press(arcade.key.F4, 0)

    assert result is False
    assert control_manager.key_calls == [(arcade.key.F4, 0)]
    assert window.key_calls == [(arcade.key.F4, 0)]


def test_install_wraps_on_close(monkeypatch) -> None:
    """Closing main window should close the event window first."""
    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    event_window = StubEventWindow()
    session = _make_session(control_manager=StubControlManager(False), event_window=event_window)
    _session._VISUALIZER_SESSION = session
    monkeypatch.setattr("arcadeactions.visualizer._window_hooks._VISUALIZER_SESSION", session)

    _install_window_handler(session)
    window.on_close()

    assert event_window.close_calls == 1
    assert window.close_calls == 1
    assert session.event_window is None


def test_remove_window_handler_restores_originals(monkeypatch) -> None:
    """Remove should restore original handlers and clear session state."""
    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    session = _make_session(control_manager=StubControlManager(False), event_window=None)
    _session._VISUALIZER_SESSION = session
    monkeypatch.setattr("arcadeactions.visualizer._window_hooks._VISUALIZER_SESSION", session)

    original_on_draw = window.on_draw
    original_on_key_press = window.on_key_press
    original_on_close = window.on_close

    _install_window_handler(session)
    _remove_window_handler(session)

    assert window.on_draw is original_on_draw
    assert window.on_key_press is original_on_key_press
    assert window.on_close is original_on_close
    assert session.window is None
    assert session.original_window_on_draw is None
    assert session.original_window_on_key_press is None
    assert session.original_window_on_close is None
