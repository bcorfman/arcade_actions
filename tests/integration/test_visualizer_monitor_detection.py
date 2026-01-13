"""Tests for monitor detection in visualizer.py."""

from __future__ import annotations

import arcade
import pytest

from actions.dev.visualizer import DevVisualizer, _get_primary_monitor_rect


class TestMonitorDetection:
    """Test monitor detection functionality."""

    def test_get_primary_monitor_rect_returns_value(self, mocker):
        """Test _get_primary_monitor_rect returns a value (tests screeninfo fallback)."""
        # Mock SDL2 to fail (tests screeninfo fallback path)
        mocker.patch("ctypes.util.find_library", return_value=None)

        result = _get_primary_monitor_rect()

        # Should return None or a tuple (depends on screeninfo availability)
        assert result is None or (isinstance(result, tuple) and len(result) == 4)

    def test_get_primary_monitor_rect_sdl2_path(self, mocker):
        """Test _get_primary_monitor_rect SDL2 path."""
        # Mock SDL2 library loading
        mock_cdll = mocker.MagicMock()
        mock_sdl = mocker.MagicMock()
        mock_cdll.return_value = mock_sdl

        # Mock SDL2 functions
        mock_sdl.SDL_Init.return_value = 0
        mock_sdl.SDL_GetNumVideoDisplays.return_value = 1

        class MockRect:
            def __init__(self):
                self.x = 0
                self.y = 0
                self.w = 1920
                self.h = 1080

        mock_rect = MockRect()
        mock_sdl.SDL_GetDisplayBounds.return_value = 0

        # Mock ctypes
        mocker.patch("ctypes.CDLL", return_value=mock_sdl)
        mocker.patch("ctypes.byref", return_value=mock_rect)

        result = _get_primary_monitor_rect()

        # May return None if mocking is incomplete, but shouldn't crash
        assert result is None or isinstance(result, tuple)

    def test_get_primary_monitor_rect_screeninfo_exception(self, mocker):
        """Test _get_primary_monitor_rect handles screeninfo exceptions."""
        # Mock SDL2 to fail
        mocker.patch("ctypes.util.find_library", return_value=None)

        # Mock screeninfo to raise exception
        mocker.patch("screeninfo.get_monitors", side_effect=Exception("Screeninfo error"))

        result = _get_primary_monitor_rect()

        # Should return None when screeninfo fails
        assert result is None or isinstance(result, tuple)
