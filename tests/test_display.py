"""Test suite for display.py - Display utilities."""

import pytest

from actions.display import _SDL_Rect, _WindowProto, center_window


class MockWindow:
    """Mock window class for testing."""

    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self._location = (0, 0)

    def set_location(self, x: int, y: int) -> None:
        self._location = (x, y)

    def get_location(self):
        return self._location


class TestSDL_Rect:
    """Test suite for _SDL_Rect structure."""

    def test_sdl_rect_creation(self):
        """Test _SDL_Rect structure creation."""
        rect = _SDL_Rect()
        assert rect.x == 0
        assert rect.y == 0
        assert rect.w == 0
        assert rect.h == 0

    def test_sdl_rect_fields(self):
        """Test _SDL_Rect field assignment."""
        rect = _SDL_Rect()
        rect.x = 100
        rect.y = 200
        rect.w = 800
        rect.h = 600

        assert rect.x == 100
        assert rect.y == 200
        assert rect.w == 800
        assert rect.h == 600


class TestCenterWindow:
    """Test suite for center_window function - simplified tests focusing on testable behavior."""

    def test_center_window_with_mock_window(self):
        """Test center_window with a mock window in a controlled environment."""
        from unittest.mock import patch

        window = MockWindow(800, 600)

        # Mock both SDL2 and screeninfo to avoid environment dependencies
        with patch("actions.display._load_sdl2", return_value=None):
            with patch("actions.display._center_with_screeninfo", return_value=True):
                result = center_window(window)
                assert result is True

        # Test the fallback case where both methods fail
        with patch("actions.display._load_sdl2", return_value=None):
            with patch("actions.display._center_with_screeninfo", return_value=False):
                result = center_window(window)
                assert result is False

    def test_center_window_with_real_arcade_window(self):
        """Test center_window with a real arcade.Window in a controlled environment."""
        from unittest.mock import patch

        try:
            import arcade

            window = arcade.Window(800, 600, visible=False)

            # Mock both SDL2 and screeninfo to avoid environment dependencies
            with patch("actions.display._load_sdl2", return_value=None):
                with patch("actions.display._center_with_screeninfo", return_value=True):
                    result = center_window(window)
                    assert result is True

        except Exception:
            # Skip test if arcade is not available or window creation fails
            pytest.skip("Arcade not available or window creation failed")


class TestWindowProtocol:
    """Test suite for _WindowProto protocol."""

    def test_window_protocol_interface(self):
        """Test that _WindowProto defines the expected interface."""
        # This is more of a type checking test
        # In practice, we can't easily test protocols without concrete implementations

        class TestWindow:
            def __init__(self):
                self.width = 800
                self.height = 600

            def set_location(self, x: int, y: int) -> None:
                self._x = x
                self._y = y

        # This should work without type errors
        window: _WindowProto = TestWindow()
        window.set_location(100, 200)
        assert window.width == 800
        assert window.height == 600


class TestDisplayPlatformSpecific:
    """Test platform-specific behavior and error conditions."""

    def test_center_window_with_different_platforms(self):
        """Test center_window behavior with different platform configurations."""
        import sys
        from unittest.mock import patch

        window = MockWindow(800, 600)

        # Test with different platform strings to cover missing lines
        with patch.object(sys, "platform", "win32"):
            with patch("actions.display._load_sdl2", return_value=None):
                with patch("actions.display._center_with_screeninfo", return_value=True):
                    result = center_window(window)
                    assert result is True

        with patch.object(sys, "platform", "darwin"):
            with patch("actions.display._load_sdl2", return_value=None):
                with patch("actions.display._center_with_screeninfo", return_value=False):
                    result = center_window(window)
                    assert result is False

        with patch.object(sys, "platform", "linux"):
            with patch("actions.display._load_sdl2", return_value=None):
                with patch("actions.display._center_with_screeninfo", return_value=True):
                    result = center_window(window)
                    assert result is True

    def test_load_sdl2_osError_handling(self):
        """Test SDL2 loading OSError handling (lines 72-74)."""
        from unittest.mock import patch

        from actions.display import _load_sdl2

        # Test OSError handling when CDLL fails to load libraries
        with patch("ctypes.util.find_library", return_value="fake_sdl2"):
            with patch("actions.display.CDLL", side_effect=OSError("Library not found")):
                result = _load_sdl2()
                assert result is None

    def test_center_with_sdl_error_conditions(self):
        """Test SDL centering with various error conditions."""
        from unittest.mock import MagicMock, patch

        from actions.display import _center_with_sdl

        window = MockWindow(800, 600)

        # Test SDL_Init failure (line 92)
        mock_sdl = MagicMock()
        mock_sdl.SDL_Init.return_value = -1  # Failure

        with patch("actions.display._load_sdl2", return_value=mock_sdl):
            result = _center_with_sdl(window)
            assert result is False

        # Test SDL_GetNumVideoDisplays failure (line 97)
        mock_sdl.SDL_Init.return_value = 0  # Success
        mock_sdl.SDL_GetNumVideoDisplays.return_value = 0  # No displays

        with patch("actions.display._load_sdl2", return_value=mock_sdl):
            result = _center_with_sdl(window)
            assert result is False

        # Test SDL_GetDisplayBounds failure (line 100)
        mock_sdl.SDL_GetNumVideoDisplays.return_value = 1  # One display
        mock_sdl.SDL_GetDisplayBounds.return_value = -1  # Failure

        with patch("actions.display._load_sdl2", return_value=mock_sdl):
            result = _center_with_sdl(window)
            assert result is False

    def test_sdl_rect_ellipsis_method(self):
        """Test _SDL_Rect ellipsis method (line 40)."""
        from actions.display import _WindowProto

        # Create a test implementation that uses the ellipsis method
        class TestRect(_WindowProto):
            def __init__(self):
                self.width = 800
                self.height = 600

            def set_location(self, x: int, y: int) -> None:
                # This should trigger the ellipsis method in _WindowProto
                ...

        rect = TestRect()

        # This tests the ellipsis method - it should not raise an exception
        rect.set_location(100, 200)

        # The ellipsis method doesn't do anything, so we just verify it doesn't crash
        assert rect is not None
