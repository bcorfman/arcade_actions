"""Integration tests for DevVisualizer window position tracking."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import DevVisualizer


@pytest.fixture
def dev_visualizer(window):
    """Create a DevVisualizer instance for testing."""
    scene_sprites = arcade.SpriteList()
    dev_viz = DevVisualizer(scene_sprites=scene_sprites, window=window)
    dev_viz.attach_to_window(window)
    return dev_viz


class TestWindowPositionTracking:
    """Test window position tracking methods."""

    def test_track_window_position(self, dev_visualizer, window):
        """Test window position tracking."""
        # Set window location
        window.set_location(100, 200)

        result = dev_visualizer.track_window_position(window)

        assert result is True

    def test_update_main_window_position(self, dev_visualizer, window, mocker):
        """Test main window position updates."""
        # Mock position tracker
        mock_track = mocker.patch.object(dev_visualizer._position_tracker, "track_window_position")
        mock_track.return_value = True

        window.set_location(150, 250)

        result = dev_visualizer.update_main_window_position()

        assert result is True
        mock_track.assert_called_once_with(window)

    def test_get_window_location_fallback_chain(self, dev_visualizer, window, mocker):
        """Test location retrieval fallback chain."""
        # Test get_location() path
        mock_get_location = mocker.patch.object(window, "get_location")
        mock_get_location.return_value = (100, 200)

        location = dev_visualizer._get_window_location(window)

        assert location == (100, 200)

        # Test tracked position fallback
        mock_get_location.return_value = None
        mock_tracked = mocker.patch.object(dev_visualizer, "_get_tracked_window_position")
        mock_tracked.return_value = (150, 250)

        location = dev_visualizer._get_window_location(window)

        assert location == (150, 250)

        # Test stored position fallback
        mock_tracked.return_value = None
        window._arcadeactions_last_set_location = (200, 300)

        location = dev_visualizer._get_window_location(window)

        assert location == (200, 300)

    def test_get_window_location_handles_wayland(self, dev_visualizer, window, mocker):
        """Test handling of Wayland (0,0) coordinates."""
        # Wayland returns (0, 0) until mapped
        mock_get_location = mocker.patch.object(window, "get_location")
        mock_get_location.return_value = (0, 0)

        mock_tracked = mocker.patch.object(dev_visualizer, "_get_tracked_window_position")
        mock_tracked.return_value = (100, 200)

        # Should fall back to tracked position when get_location returns (0,0)
        location = dev_visualizer._get_window_location(window)

        assert location == (100, 200)

    def test_get_window_location_handles_invalid_coords(self, dev_visualizer, window, mocker):
        """Test handling of invalid coordinates."""
        # Test huge negative off-screen coords
        mock_get_location = mocker.patch.object(window, "get_location")
        mock_get_location.return_value = (-50000, -50000)

        mock_tracked = mocker.patch.object(dev_visualizer, "_get_tracked_window_position")
        mock_tracked.return_value = (100, 200)

        # Should fall back to tracked position for invalid coords
        location = dev_visualizer._get_window_location(window)

        assert location == (100, 200)

    def test_window_position_persistence(self, dev_visualizer, window):
        """Test position tracking across window operations."""
        # Track initial position
        window.set_location(100, 200)
        dev_visualizer.track_window_position(window)

        # Move window
        window.set_location(300, 400)
        dev_visualizer.track_window_position(window)

        # Verify tracked position
        tracked = dev_visualizer._get_tracked_window_position(window)
        assert tracked is not None

    def test_get_window_location_returns_none_for_no_window(self, dev_visualizer):
        """Test location retrieval returns None when window is None."""
        location = dev_visualizer._get_window_location(None)

        assert location is None
