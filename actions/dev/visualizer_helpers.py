"""Helper functions for DevVisualizer.

Pure functions extracted from visualizer.py for better testability.
These functions have no GUI dependencies and can be fully unit tested.
"""

from __future__ import annotations

from typing import Any, Callable


def resolve_condition(cond: Any) -> Callable[[], bool]:
    """Resolve a condition specification to a callable.

    Supports:
      - callables (returned unchanged)
      - string identifiers: "infinite", "after_frames:N", "after_seconds:N", "within_frames:S:E"
      - None (returns infinite condition)

    Args:
        cond: Condition specification (callable, string, or None)

    Returns:
        Callable that returns a boolean
    """
    from actions.frame_timing import after_frames, seconds_to_frames, within_frames, infinite

    if cond is None:
        return infinite()
    if callable(cond):
        return cond
    if isinstance(cond, str):
        cond = cond.strip()
        if cond == "infinite":
            return infinite()
        if cond.startswith("after_frames:"):
            try:
                n = int(cond.split(":", 1)[1])
                return after_frames(n)
            except Exception:
                return infinite
        if cond.startswith("after_seconds:") or cond.startswith("seconds:"):
            try:
                parts = cond.split(":", 1)
                secs = float(parts[1])
                frames = seconds_to_frames(secs)
                return after_frames(frames)
            except Exception:
                return infinite
        if cond.startswith("within_frames:"):
            try:
                _, rest = cond.split(":", 1)
                start_s, end_s = rest.split(":")
                start = int(start_s)
                end = int(end_s)
                return within_frames(start, end)
            except Exception:
                return infinite
    # Fallback: return infinite
    return infinite


def resolve_callback(value: Any, resolver: Callable[[str], Any] | None = None) -> Any:
    """Resolve callback value to a callable using optional resolver.

    Accepts a callable, or a string which will be passed to resolver.
    If resolver is None and value is a string, returns None (skip).

    Args:
        value: Callback value (callable, string, or None)
        resolver: Optional function to resolve string values to callables

    Returns:
        Callable if resolved, None otherwise
    """
    if value is None:
        return None
    if callable(value):
        return value
    if isinstance(value, str) and resolver is not None:
        try:
            return resolver(value)
        except Exception:
            return None
    return None
