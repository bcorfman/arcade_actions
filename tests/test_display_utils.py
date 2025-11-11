from __future__ import annotations

import pytest

from actions import display


class DummyWindow:
    def __init__(self):
        self.width = 200
        self.height = 120
        self.location: tuple[int, int] | None = None

    def set_location(self, x: int, y: int) -> None:
        self.location = (x, y)


def test_move_to_primary_monitor_prefers_sdl(monkeypatch):
    window = DummyWindow()
    called = {}

    def fake_sdl(win: DummyWindow, ox: int, oy: int) -> bool:
        called["sdl"] = (win, ox, oy)
        return True

    def fake_screeninfo(win: DummyWindow, ox: int, oy: int) -> bool:
        raise AssertionError("screeninfo fallback should not run when SDL succeeds")

    monkeypatch.setattr(display, "_move_to_primary_with_sdl", fake_sdl)
    monkeypatch.setattr(display, "_move_to_primary_with_screeninfo", fake_screeninfo)

    assert display.move_to_primary_monitor(window, offset_x=10, offset_y=20)
    assert called["sdl"] == (window, 10, 20)


def test_move_to_primary_monitor_falls_back(monkeypatch):
    window = DummyWindow()
    calls: list[tuple[int, int]] = []

    monkeypatch.setattr(display, "_move_to_primary_with_sdl", lambda *args, **kwargs: False)

    def fake_screeninfo(win: DummyWindow, ox: int, oy: int) -> bool:
        calls.append((ox, oy))
        win.set_location(ox, oy)
        return True

    monkeypatch.setattr(display, "_move_to_primary_with_screeninfo", fake_screeninfo)

    assert display.move_to_primary_monitor(window, offset_x=30, offset_y=40)
    assert calls == [(30, 40)]
    assert window.location == (30, 40)
