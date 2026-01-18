from __future__ import annotations

from collections.abc import Callable
from typing import Any

from arcadeactions.frame_timing import after_frames, frames_to_seconds


# Helper function for cloning conditions
def _clone_condition(condition):
    """Create a fresh copy of a condition, preserving frame metadata when available."""
    if hasattr(condition, "_is_frame_condition") and condition._is_frame_condition:
        # Create a fresh frame-based condition
        frame_count = getattr(condition, "_frame_count", 0)
        return after_frames(frame_count)
    else:
        # For non-duration/non-frame conditions, return as-is
        return condition


# Common condition functions


def infinite() -> Callable[[], bool]:
    """Create a condition function that never returns True.

    Use this for actions that should continue indefinitely until explicitly stopped.

    Usage:
        # Move forever (or until action is stopped externally)
        move_until(sprite, (100, 0), infinite)

        # Rotate continuously
        rotate_until(sprite, 45, infinite)
    """

    return False


def _extract_duration_seconds(cond: Callable[[], Any]) -> float | None:
    """Extract a simulation-time duration (in seconds) from frame metadata if available."""
    frame_count = getattr(cond, "_frame_count", None)
    if isinstance(frame_count, (int, float)) and frame_count >= 0:
        return frames_to_seconds(frame_count)

    frame_window = getattr(cond, "_frame_window", None)
    if isinstance(frame_window, tuple) and len(frame_window) == 2:
        start, end = frame_window
        if all(isinstance(value, (int, float)) for value in frame_window) and end >= start:
            return frames_to_seconds(end - start)

    return None
