"""Unit tests for EventInspectorWindow helper behaviors."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.visualizer.event_window import EventInspectorWindow


class StubTimeline:
    def __init__(self, _store: object) -> None:
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


class StubTimelineRenderer:
    def __init__(self, timeline: StubTimeline, **_kwargs: object) -> None:
        self.timeline = timeline
        self.width = 0
        self.height = 0
        self.update_calls = 0
        self.draw_calls = 0
        self.font_sizes: list[float] = []

    def set_font_size(self, size: float) -> None:
        self.font_sizes.append(size)

    def update(self) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        self.draw_calls += 1


class StubWindow:
    def __init__(self) -> None:
        self.dispatch_calls: list[tuple[str, int, int]] = []
        self.handler_calls: list[tuple[int, int]] = []

    def dispatch_event(self, handler: str, symbol: int, modifiers: int) -> None:
        self.dispatch_calls.append((handler, symbol, modifiers))

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.handler_calls.append((symbol, modifiers))


@pytest.fixture
def window() -> EventInspectorWindow:
    window = EventInspectorWindow(
        debug_store=object(),
        timeline_cls=StubTimeline,
        timeline_renderer_cls=StubTimelineRenderer,
    )
    window._should_draw = True
    return window


def test_on_draw_updates_renderer_geometry(monkeypatch, window: EventInspectorWindow) -> None:
    renderer = window._timeline_renderer
    assert isinstance(renderer, StubTimelineRenderer)

    monkeypatch.setattr(window, "_has_active_context", lambda: True)
    monkeypatch.setattr("arcadeactions.visualizer.event_window.window_commands.get_window", lambda: window)
    monkeypatch.setattr("arcadeactions.visualizer.event_window.window_commands.set_window", lambda _win: None)
    monkeypatch.setattr(window, "switch_to", lambda: None)
    monkeypatch.setattr(window, "clear", lambda: None)
    monkeypatch.setattr(window, "_draw_background", lambda: None)
    monkeypatch.setattr(window, "_draw_timeline", lambda: None)

    window.width = 500
    window.height = 400
    window.on_draw()

    assert renderer.update_calls == 1
    assert renderer.width == window.width - 2 * window.MARGIN
    assert renderer.height < window.height


def test_forward_to_main_window_dispatches(monkeypatch, window: EventInspectorWindow) -> None:
    stub_main = StubWindow()
    window._main_window = stub_main

    window._forward_to_main_window("on_key_press", arcade.key.F5, 0)

    assert stub_main.dispatch_calls == [("on_key_press", arcade.key.F5, 0)]
    assert stub_main.handler_calls == []


def test_forward_to_main_window_fallback(monkeypatch, window: EventInspectorWindow) -> None:
    stub_main = StubWindow()
    window._main_window = stub_main

    def fail_dispatch(_handler: str, _symbol: int, _modifiers: int) -> None:
        raise RuntimeError("no dispatch")

    stub_main.dispatch_event = fail_dispatch  # type: ignore[assignment]

    window._forward_to_main_window("on_key_press", arcade.key.F5, 0)

    assert stub_main.handler_calls == [(arcade.key.F5, 0)]


def test_request_main_window_focus_schedules(monkeypatch, window: EventInspectorWindow) -> None:
    calls: list[float] = []

    def record_schedule(func, delay: float) -> None:
        calls.append(delay)

    monkeypatch.setattr(arcade, "schedule_once", record_schedule)
    window._main_window = StubWindow()

    window.request_main_window_focus()

    assert calls == [0.0, 0.01, 0.05]


def test_on_key_press_forward_handler_handles(monkeypatch, window: EventInspectorWindow) -> None:
    handled: list[tuple[int, int]] = []

    def forward(symbol: int, modifiers: int) -> bool:
        handled.append((symbol, modifiers))
        return True

    window._forward_key_handler = forward
    window.close = lambda: None  # type: ignore[assignment]

    window.on_key_press(arcade.key.F4, 0)

    assert handled == [(arcade.key.F4, 0)]


def test_on_key_press_f4_closes(monkeypatch, window: EventInspectorWindow) -> None:
    closed = []

    def close() -> None:
        closed.append(True)

    window.close = close  # type: ignore[assignment]

    window.on_key_press(arcade.key.F4, 0)

    assert closed == [True]
