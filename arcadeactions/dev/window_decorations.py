"""Helpers for window decoration offsets."""

from __future__ import annotations

import arcade


def measure_window_decoration_deltas(window: arcade.Window) -> tuple[int | None, int | None]:
    """Measure window decoration deltas (frame/border offsets) if possible."""
    try:
        deco_x, deco_y = window.get_location()
    except Exception:
        return None, None

    if (deco_x, deco_y) == (0, 0):
        return None, None

    stored = getattr(window, "_arcadeactions_last_set_location", None)
    if stored:
        calc_dx = deco_x - stored[0]
        calc_dy = deco_y - stored[1]
        if calc_dx or calc_dy:
            return calc_dx, calc_dy
        return None, None

    client_x = getattr(window, "_x", None)
    client_y = getattr(window, "_y", None)
    if client_x is None and hasattr(window, "_window"):
        pyglet_win = getattr(window, "_window", None)
        if pyglet_win is not None:
            client_x = getattr(pyglet_win, "_x", None)
            client_y = getattr(pyglet_win, "_y", None)

    if client_x is not None and client_y is not None:
        calc_dx = deco_x - client_x
        calc_dy = deco_y - client_y
        if calc_dx or calc_dy:
            return calc_dx, calc_dy
        return None, None

    return None, None
