"""Unit tests for palette helper functions."""

from __future__ import annotations

import types

import arcade

from arcadeactions.dev import palette_helpers


class StubHost:
    def __init__(self, tracked_location=None) -> None:
        self._tracked_location = tracked_location

    def _get_tracked_window_position(self, _window):
        return self._tracked_location


def test_get_window_location_prefers_window_location():
    """Return the OS-reported location when it is valid."""
    host = StubHost(tracked_location=(10, 20))
    window = types.SimpleNamespace()
    window.get_location = lambda: (100, 200)

    assert palette_helpers.get_window_location(host, window) == (100, 200)


def test_get_window_location_falls_back_to_tracked():
    """Return tracked location when OS location is invalid."""
    host = StubHost(tracked_location=(50, 60))
    window = types.SimpleNamespace()
    window.get_location = lambda: (0, 0)

    assert palette_helpers.get_window_location(host, window) == (50, 60)


class StubPaletteWindow:
    def __init__(self) -> None:
        self.visible = False
        self.show_called = False
        self.width = 250
        self.height = 400

    def show_window(self) -> None:
        self.visible = True
        self.show_called = True


class StubPollHost:
    def __init__(self) -> None:
        self.visible = True
        self.window = None
        self.palette_window = None
        self._palette_show_pending = True
        self._palette_desired_visible = True
        self._window_decoration_dx = 1
        self._window_decoration_dy = 1
        self._EXTRA_FRAME_PAD = 0
        self._is_detaching = False
        self.ctx = object()
        self._position_tracker = object()
        self.created = 0
        self.updated = 0
        self.positioned = 0
        self.restored = 0
        self.activated = 0

    def update_main_window_position(self) -> bool:
        self.updated += 1
        return True

    def _get_tracked_window_position(self, _window):
        return None

    def handle_key_press(self, _key: int, _modifiers: int) -> bool:
        return False

    def _create_palette_window(self) -> None:
        self.created += 1
        self.palette_window = StubPaletteWindow()

    def _position_palette_window(self, *, force: bool = False) -> bool:
        self.positioned += 1
        return True

    def _restore_palette_location_after_show(self) -> None:
        self.restored += 1

    def _activate_main_window(self) -> None:
        self.activated += 1


def test_poll_show_palette_cancels_when_not_desired(monkeypatch):
    """poll_show_palette cancels stale pending callbacks when palette is not desired."""
    host = StubPollHost()
    host._palette_desired_visible = False
    host._palette_show_pending = True

    monkeypatch.setattr(arcade, "schedule_once", lambda *_args, **_kwargs: None)

    palette_helpers.poll_show_palette(
        host,
        get_primary_monitor_rect=lambda: (0, 0, 1920, 1080),
        palette_window_cls=lambda **_kwargs: None,
        registry_provider=lambda: None,
    )

    assert host._palette_show_pending is False


def test_poll_show_palette_schedules_retry_without_window(monkeypatch):
    """poll_show_palette schedules a retry when main window is missing."""
    host = StubPollHost()
    host.window = None

    calls: list[float] = []

    def schedule_once(_fn, delay: float):
        calls.append(float(delay))

    monkeypatch.setattr(arcade, "schedule_once", schedule_once)

    palette_helpers.poll_show_palette(
        host,
        get_primary_monitor_rect=lambda: (0, 0, 1920, 1080),
        palette_window_cls=lambda **_kwargs: None,
        registry_provider=lambda: None,
    )

    assert calls == [0.05]


def test_poll_show_palette_shows_positions_and_restores(monkeypatch):
    """poll_show_palette creates/positions/shows and runs post-show hooks."""
    host = StubPollHost()
    host.window = types.SimpleNamespace(get_location=lambda: (100, 200))

    scheduled: list[float] = []

    def schedule_once(_fn, delay: float):
        scheduled.append(float(delay))

    monkeypatch.setattr(arcade, "schedule_once", schedule_once)

    palette_helpers.poll_show_palette(
        host,
        get_primary_monitor_rect=lambda: (0, 0, 1920, 1080),
        palette_window_cls=lambda **_kwargs: None,
        registry_provider=lambda: None,
    )

    assert host.created == 1
    assert host.updated == 1
    assert host.positioned == 1
    assert host.palette_window is not None
    assert host.palette_window.show_called is True
    assert host.restored == 1
    assert host.activated == 1
    assert host._palette_show_pending is False
