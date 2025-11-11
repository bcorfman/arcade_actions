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


def test_center_window_prefers_sdl(monkeypatch):
    window = DummyWindow()
    called = {}

    def fake_sdl(win: DummyWindow) -> bool:
        called["sdl"] = win
        return True

    def fake_screeninfo(win: DummyWindow) -> bool:
        raise AssertionError("screeninfo fallback should not run when SDL succeeds")

    monkeypatch.setattr(display, "_center_with_sdl", fake_sdl)
    monkeypatch.setattr(display, "_center_with_screeninfo", fake_screeninfo)

    assert display.center_window(window)
    assert called["sdl"] == window


def test_center_window_falls_back(monkeypatch):
    window = DummyWindow()
    called = []

    monkeypatch.setattr(display, "_center_with_sdl", lambda *args, **kwargs: False)

    def fake_screeninfo(win: DummyWindow) -> bool:
        called.append(win)
        # Simulate centering (set location to center of a 1920x1080 display)
        win.set_location(860, 480)  # (1920-200)/2, (1080-120)/2
        return True

    monkeypatch.setattr(display, "_center_with_screeninfo", fake_screeninfo)

    assert display.center_window(window)
    assert len(called) == 1
    assert called[0] == window
    assert window.location == (860, 480)

