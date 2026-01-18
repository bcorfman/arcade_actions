from __future__ import annotations

from ctypes import Structure, c_int
from unittest.mock import MagicMock

from arcadeactions import display


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


def test_load_sdl2_success(monkeypatch):
    """Test _load_sdl2 when SDL2 is found via find_library."""
    mock_cdll = MagicMock()

    def mock_find_library(name):
        if name == "SDL2":
            return "/usr/lib/libSDL2.so"
        return None

    def mock_cdll_constructor(name):
        if "SDL2" in name:
            return mock_cdll
        raise OSError("Library not found")

    monkeypatch.setattr(display, "find_library", mock_find_library)
    monkeypatch.setattr(display, "CDLL", mock_cdll_constructor)

    result = display._load_sdl2()
    assert result is not None


def test_load_sdl2_failure_all_candidates_fail(monkeypatch):
    """Test _load_sdl2 when all candidates fail to load."""

    def mock_find_library(name):
        return None

    def mock_cdll_constructor(name):
        raise OSError("Library not found")

    monkeypatch.setattr(display, "find_library", mock_find_library)
    monkeypatch.setattr(display, "CDLL", mock_cdll_constructor)

    result = display._load_sdl2()
    assert result is None


def test_sdl_primary_rect_success(monkeypatch):
    """Test _sdl_primary_rect when SDL2 is available and returns display info."""
    mock_sdl = MagicMock()
    mock_sdl.SDL_Init.return_value = 0  # Success
    mock_sdl.SDL_GetNumVideoDisplays.return_value = 1

    def mock_load_sdl2():
        return mock_sdl

    def mock_byref(obj):
        return obj

    def mock_get_display_bounds(display_index, rect_ptr):
        # Populate the rect that was passed in
        rect_ptr.x = 0
        rect_ptr.y = 0
        rect_ptr.w = 1920
        rect_ptr.h = 1080
        return 0  # Success

    mock_sdl.SDL_GetDisplayBounds.side_effect = mock_get_display_bounds

    monkeypatch.setattr(display, "_load_sdl2", mock_load_sdl2)
    monkeypatch.setattr(display, "byref", mock_byref)

    result = display._sdl_primary_rect()
    assert result is not None
    assert result.x == 0
    assert result.y == 0
    assert result.w == 1920
    assert result.h == 1080
    assert mock_sdl.SDL_Init.called
    assert mock_sdl.SDL_Quit.called


def test_sdl_primary_rect_no_sdl(monkeypatch):
    """Test _sdl_primary_rect when SDL2 is not available."""

    def mock_load_sdl2():
        return None

    monkeypatch.setattr(display, "_load_sdl2", mock_load_sdl2)

    result = display._sdl_primary_rect()
    assert result is None


def test_sdl_primary_rect_init_fails(monkeypatch):
    """Test _sdl_primary_rect when SDL_Init fails."""
    mock_sdl = MagicMock()
    mock_sdl.SDL_Init.return_value = -1  # Failure

    def mock_load_sdl2():
        return mock_sdl

    monkeypatch.setattr(display, "_load_sdl2", mock_load_sdl2)

    result = display._sdl_primary_rect()
    assert result is None
    assert mock_sdl.SDL_Init.called


def test_sdl_primary_rect_no_displays(monkeypatch):
    """Test _sdl_primary_rect when no displays are available."""
    mock_sdl = MagicMock()
    mock_sdl.SDL_Init.return_value = 0
    mock_sdl.SDL_GetNumVideoDisplays.return_value = 0  # No displays

    def mock_load_sdl2():
        return mock_sdl

    monkeypatch.setattr(display, "_load_sdl2", mock_load_sdl2)

    result = display._sdl_primary_rect()
    assert result is None
    assert mock_sdl.SDL_Quit.called


def test_sdl_primary_rect_get_bounds_fails(monkeypatch):
    """Test _sdl_primary_rect when SDL_GetDisplayBounds fails."""
    mock_sdl = MagicMock()
    mock_sdl.SDL_Init.return_value = 0
    mock_sdl.SDL_GetNumVideoDisplays.return_value = 1
    mock_sdl.SDL_GetDisplayBounds.return_value = -1  # Failure

    def mock_load_sdl2():
        return mock_sdl

    def mock_byref(obj):
        return obj

    monkeypatch.setattr(display, "_load_sdl2", mock_load_sdl2)
    monkeypatch.setattr(display, "byref", mock_byref)

    result = display._sdl_primary_rect()
    assert result is None
    assert mock_sdl.SDL_Quit.called


def test_center_with_sdl_success(monkeypatch):
    """Test _center_with_sdl when SDL rect is available."""
    window = DummyWindow()

    class MockRect(Structure):
        _fields_ = [("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int)]

    mock_rect = MockRect()
    mock_rect.x = 0
    mock_rect.y = 0
    mock_rect.w = 1920
    mock_rect.h = 1080

    def mock_sdl_primary_rect():
        return mock_rect

    monkeypatch.setattr(display, "_sdl_primary_rect", mock_sdl_primary_rect)

    result = display._center_with_sdl(window)
    assert result is True
    # Window should be centered: (1920-200)/2 = 860, (1080-120)/2 = 480
    assert window.location == (860, 480)


def test_center_with_sdl_no_rect(monkeypatch):
    """Test _center_with_sdl when SDL rect is not available."""
    window = DummyWindow()

    def mock_sdl_primary_rect():
        return None

    monkeypatch.setattr(display, "_sdl_primary_rect", mock_sdl_primary_rect)

    result = display._center_with_sdl(window)
    assert result is False
    assert window.location is None


def test_move_to_primary_with_sdl_success(monkeypatch):
    """Test _move_to_primary_with_sdl when SDL rect is available."""
    window = DummyWindow()

    class MockRect(Structure):
        _fields_ = [("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int)]

    mock_rect = MockRect()
    mock_rect.x = 0
    mock_rect.y = 0
    mock_rect.w = 1920
    mock_rect.h = 1080

    def mock_sdl_primary_rect():
        return mock_rect

    monkeypatch.setattr(display, "_sdl_primary_rect", mock_sdl_primary_rect)

    result = display._move_to_primary_with_sdl(window, offset_x=40, offset_y=40)
    assert result is True
    # Window should be at (0+40, 0+40) = (40, 40)
    assert window.location == (40, 40)


def test_move_to_primary_with_sdl_no_rect(monkeypatch):
    """Test _move_to_primary_with_sdl when SDL rect is not available."""
    window = DummyWindow()

    def mock_sdl_primary_rect():
        return None

    monkeypatch.setattr(display, "_sdl_primary_rect", mock_sdl_primary_rect)

    result = display._move_to_primary_with_sdl(window, offset_x=40, offset_y=40)
    assert result is False
    assert window.location is None


def test_move_to_primary_with_sdl_clamps_to_bounds(monkeypatch):
    """Test _move_to_primary_with_sdl clamps position to monitor bounds."""
    window = DummyWindow()

    class MockRect(Structure):
        _fields_ = [("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int)]

    mock_rect = MockRect()
    mock_rect.x = 0
    mock_rect.y = 0
    mock_rect.w = 1920
    mock_rect.h = 1080

    def mock_sdl_primary_rect():
        return mock_rect

    monkeypatch.setattr(display, "_sdl_primary_rect", mock_sdl_primary_rect)

    # Try to move way off screen - should clamp to max position
    result = display._move_to_primary_with_sdl(window, offset_x=10000, offset_y=10000)
    assert result is True
    # Should be clamped to: max_x = 1920-200 = 1720, max_y = 1080-120 = 960
    assert window.location == (1720, 960)


def test_move_to_primary_monitor_prefers_sdl(monkeypatch):
    """Test move_to_primary_monitor prefers SDL over screeninfo."""
    window = DummyWindow()
    called = {}

    def fake_sdl(win: DummyWindow, offset_x: int, offset_y: int) -> bool:
        called["sdl"] = (win, offset_x, offset_y)
        return True

    def fake_screeninfo(win: DummyWindow, offset_x: int, offset_y: int) -> bool:
        raise AssertionError("screeninfo fallback should not run when SDL succeeds")

    monkeypatch.setattr(display, "_move_to_primary_with_sdl", fake_sdl)
    monkeypatch.setattr(display, "_move_to_primary_with_screeninfo", fake_screeninfo)

    assert display.move_to_primary_monitor(window, offset_x=40, offset_y=40)
    assert called["sdl"] == (window, 40, 40)


def test_move_to_primary_monitor_falls_back(monkeypatch):
    """Test move_to_primary_monitor falls back to screeninfo when SDL fails."""
    window = DummyWindow()
    called = []

    monkeypatch.setattr(display, "_move_to_primary_with_sdl", lambda *args, **kwargs: False)

    def fake_screeninfo(win: DummyWindow, offset_x: int, offset_y: int) -> bool:
        called.append((win, offset_x, offset_y))
        win.set_location(40, 40)
        return True

    monkeypatch.setattr(display, "_move_to_primary_with_screeninfo", fake_screeninfo)

    assert display.move_to_primary_monitor(window, offset_x=40, offset_y=40)
    assert len(called) == 1
    assert called[0] == (window, 40, 40)
    assert window.location == (40, 40)
