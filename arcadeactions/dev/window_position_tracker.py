"""Window position tracking for DevVisualizer.

Extracted from visualizer.py for better testability.
"""

from __future__ import annotations

from typing import Any

import arcade


class WindowPositionTracker:
    """Tracks window positions for relative positioning.

    Stores tracked positions of windows to enable relative positioning
    of other windows (e.g., palette window relative to main window).
    """

    def __init__(self):
        """Initialize the tracker."""
        self._tracked_positions: dict[int, tuple[int, int]] = {}  # window_id -> (x, y)

    def track_window_position(self, window: arcade.Window | Any) -> bool:
        """Track the current position of a window.

        This should be called after positioning a window to enable relative positioning
        of other windows. For example, call this after move_to_primary_monitor().

        Args:
            window: The window to track the position of

        Returns:
            True if a valid position was recorded, False otherwise.
        """
        try:
            # Prefer the OS-reported position when available so we account for window manager adjustments
            location = None
            if hasattr(window, "get_location"):
                try:
                    loc = window.get_location()
                    if loc and loc != (0, 0):
                        location = loc
                except Exception:
                    location = None
            if location is None:
                location = getattr(window, "_arcadeactions_last_set_location", None)
            # Ignore (0, 0) which is a common Wayland placeholder
            if location and location != (0, 0):
                self._track_position(window, location[0], location[1])
                return True
        except Exception:
            return False
        return False

    def _track_position(self, window: arcade.Window | Any, x: int, y: int) -> None:
        """Track the position we set for a window."""
        self._tracked_positions[id(window)] = (x, y)

    def track_known_position(self, window: arcade.Window | Any, x: int, y: int) -> None:
        """Track a known position for a window.

        Use this when you know the exact position (e.g., after calling set_location).

        Args:
            window: The window to track the position for
            x: X coordinate
            y: Y coordinate
        """
        self._track_position(window, x, y)

    def get_tracked_position(self, window: arcade.Window | Any) -> tuple[int, int] | None:
        """Get the tracked position for a window.

        Args:
            window: The window to get the tracked position for

        Returns:
            Tuple of (x, y) if position is tracked, None otherwise
        """
        return self._tracked_positions.get(id(window))
