"""Unit tests for palette helper functions."""

from __future__ import annotations

import types

from arcadeactions.dev import palette_helpers


class StubHost:
    def __init__(self, tracked_location=None) -> None:
        self._tracked_location = tracked_location

    def _get_tracked_window_position(self, _window):
        return self._tracked_location


def test_get_window_location_prefers_window_location():
    """Return the OS-reported location when it is valid."""
    host = StubHost(tracked_location=(10, 20))
    window = types.SimpleNamespace()
    window.get_location = lambda: (100, 200)

    assert palette_helpers.get_window_location(host, window) == (100, 200)


def test_get_window_location_falls_back_to_tracked():
    """Return tracked location when OS location is invalid."""
    host = StubHost(tracked_location=(50, 60))
    window = types.SimpleNamespace()
    window.get_location = lambda: (0, 0)

    assert palette_helpers.get_window_location(host, window) == (50, 60)
