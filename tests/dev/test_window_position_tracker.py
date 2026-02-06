"""Tests for window position tracker.

Tests the WindowPositionTracker class extracted from visualizer.py.
"""

from __future__ import annotations

from arcadeactions.dev.window_position_tracker import WindowPositionTracker
from tests.conftest import HeadlessWindow


class TestWindowPositionTracker:
    """Test suite for WindowPositionTracker class."""

    def test_init(self):
        """Test tracker initialization."""
        tracker = WindowPositionTracker()
        assert tracker._tracked_positions == {}

    def test_track_window_position_with_location(self):
        """Test tracking window position using get_location()."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window.set_location(100, 200)

        # Mock get_location method
        def get_location():
            return (100, 200)

        window.get_location = get_location

        result = tracker.track_window_position(window)
        assert result is True
        assert tracker.get_tracked_position(window) == (100, 200)

    def test_track_window_position_with_stored_location(self):
        """Test tracking window position using _arcadeactions_last_set_location."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window._arcadeactions_last_set_location = (150, 250)

        result = tracker.track_window_position(window)
        assert result is True
        assert tracker.get_tracked_position(window) == (150, 250)

    def test_track_window_position_ignores_zero(self):
        """Test that (0, 0) placeholder is ignored."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()

        # Mock get_location to return (0, 0)
        def get_location():
            return (0, 0)

        window.get_location = get_location

        result = tracker.track_window_position(window)
        assert result is False
        assert tracker.get_tracked_position(window) is None

    def test_track_window_position_ignores_zero_stored(self):
        """Test that stored (0, 0) is ignored."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window._arcadeactions_last_set_location = (0, 0)

        result = tracker.track_window_position(window)
        assert result is False
        assert tracker.get_tracked_position(window) is None

    def test_get_tracked_position_not_tracked(self):
        """Test getting position for untracked window returns None."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()

        assert tracker.get_tracked_position(window) is None

    def test_get_tracked_position_after_tracking(self):
        """Test getting position after tracking."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window.set_location(300, 400)

        def get_location():
            return (300, 400)

        window.get_location = get_location

        tracker.track_window_position(window)
        assert tracker.get_tracked_position(window) == (300, 400)

    def test_track_window_position_handles_exception(self):
        """Test that exceptions during tracking are handled gracefully."""
        tracker = WindowPositionTracker()

        class FailingWindow:
            def get_location(self):
                raise RuntimeError("Window error")

        window = FailingWindow()

        result = tracker.track_window_position(window)
        assert result is False
        assert tracker.get_tracked_position(window) is None

    def test_track_window_position_handles_unexpected_attribute_error(self):
        """Return False when the window object raises during attribute access.

        This exercises the outer exception handler, which can trigger when
        reading a stored location raises unexpectedly.
        """
        tracker = WindowPositionTracker()

        class ExplodingStoredLocation:
            def get_location(self):
                return None

            def __getattribute__(self, name: str):
                if name == "_arcadeactions_last_set_location":
                    raise RuntimeError("boom")
                return object.__getattribute__(self, name)

        window = ExplodingStoredLocation()
        assert tracker.track_window_position(window) is False
        assert tracker.get_tracked_position(window) is None

    def test_track_multiple_windows(self):
        """Test tracking multiple windows independently."""
        tracker = WindowPositionTracker()

        window1 = HeadlessWindow()
        window1.set_location(100, 200)

        def get_location1():
            return (100, 200)

        window1.get_location = get_location1

        window2 = HeadlessWindow()
        window2.set_location(300, 400)

        def get_location2():
            return (300, 400)

        window2.get_location = get_location2

        tracker.track_window_position(window1)
        tracker.track_window_position(window2)

        assert tracker.get_tracked_position(window1) == (100, 200)
        assert tracker.get_tracked_position(window2) == (300, 400)

    def test_track_position_no_get_location(self):
        """Test tracking window without get_location method."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window._arcadeactions_last_set_location = (500, 600)

        result = tracker.track_window_position(window)
        assert result is True
        assert tracker.get_tracked_position(window) == (500, 600)

    def test_track_position_get_location_returns_none(self):
        """Test tracking when get_location returns None."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window._arcadeactions_last_set_location = (700, 800)

        def get_location():
            return None

        window.get_location = get_location

        result = tracker.track_window_position(window)
        assert result is True
        assert tracker.get_tracked_position(window) == (700, 800)

    def test_track_position_prefers_get_location_over_stored(self):
        """Test that get_location is preferred over stored location."""
        tracker = WindowPositionTracker()
        window = HeadlessWindow()
        window._arcadeactions_last_set_location = (100, 100)

        def get_location():
            return (200, 200)

        window.get_location = get_location

        result = tracker.track_window_position(window)
        assert result is True
        # Should use get_location result, not stored location
        assert tracker.get_tracked_position(window) == (200, 200)
