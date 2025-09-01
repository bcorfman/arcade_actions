from __future__ import annotations

"""Display utilities for ArcadeActions.

Currently provides ``center_window`` which positions an ``arcade.Window`` on the
primary monitor *before* it becomes visible.  The helper prefers SDL2 (via
``ctypes``) because that works reliably across X11/Wayland/Windows/macOS.  If
SDL2 is not available, it falls back to the pure-Python ``screeninfo`` package.

Usage
-----
>>> window = arcade.Window(800, 600, visible=False)
>>> from actions.display import center_window
>>> center_window(window)  # returns True on success
>>> window.set_visible(True)

The function returns ``True`` when a centering strategy succeeded; otherwise it
returns ``False`` and leaves the window untouched.
"""

from ctypes import CDLL, POINTER, Structure, byref, c_int, c_uint32
from ctypes.util import find_library

# Only import arcade for type checking to avoid hard dependency order issues.
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover
    import arcade

__all__ = ["center_window"]


class _WindowProto(Protocol):
    """Minimal protocol extracted from :class:`arcade.Window`."""

    width: int
    height: int

    def set_location(self, x: int, y: int) -> None:  # noqa: D401 – arcade naming
        ...


# ---------------------------------------------------------------------------
# SDL2 helper
# ---------------------------------------------------------------------------


class _SDL_Rect(Structure):
    _fields_ = [("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int)]


def _load_sdl2() -> CDLL | None:
    """Attempt to load the SDL2 shared library, returning a ``ctypes.CDLL``."""

    candidates: list[str] = []
    found = find_library("SDL2")
    if found:
        candidates.append(found)

    import sys

    if sys.platform.startswith("win"):
        candidates += ["SDL2.dll"]
    elif sys.platform == "darwin":
        candidates += ["libSDL2.dylib", "SDL2"]
    else:  # Linux / *nix
        candidates += ["libSDL2-2.0.so.0", "libSDL2.so", "SDL2"]

    for name in candidates:
        try:
            return CDLL(name)
        except OSError:
            continue
    return None


def _center_with_sdl(window: _WindowProto) -> bool:
    sdl = _load_sdl2()
    if sdl is None:
        return False

    SDL_INIT_VIDEO = 0x00000020
    sdl.SDL_Init.argtypes = [c_uint32]
    sdl.SDL_Init.restype = c_int  # type: ignore[var-annotated]
    sdl.SDL_Quit.argtypes = []
    sdl.SDL_GetNumVideoDisplays.argtypes = []
    sdl.SDL_GetNumVideoDisplays.restype = c_int  # type: ignore[var-annotated]
    sdl.SDL_GetDisplayBounds.argtypes = [c_int, POINTER(_SDL_Rect)]
    sdl.SDL_GetDisplayBounds.restype = c_int  # type: ignore[var-annotated]

    if sdl.SDL_Init(SDL_INIT_VIDEO) != 0:
        return False

    try:
        num_displays = sdl.SDL_GetNumVideoDisplays()
        if num_displays <= 0:
            return False
        rect = _SDL_Rect()
        if sdl.SDL_GetDisplayBounds(0, byref(rect)) != 0:
            return False
        center_x = rect.x + (rect.w - window.width) // 2
        center_y = rect.y + (rect.h - window.height) // 2
        window.set_location(center_x, center_y)
        return True
    finally:
        sdl.SDL_Quit()


# ---------------------------------------------------------------------------
# screeninfo helper
# ---------------------------------------------------------------------------


def _center_with_screeninfo(window: _WindowProto) -> bool:  # pragma: no cover
    try:
        from screeninfo import get_monitors
    except Exception:
        return False

    monitors = get_monitors()
    if not monitors:
        return False
    primary = monitors[0]
    center_x = primary.x + (primary.width - window.width) // 2
    center_y = primary.y + (primary.height - window.height) // 2
    window.set_location(center_x, center_y)
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def center_window(window: arcade.Window, /) -> bool:  # type: ignore[name-defined]
    """Center *window* on the primary monitor.

    The function tries SDL2 first (most reliable) and then screeninfo.  It
    returns ``True`` if any strategy succeeded, otherwise ``False``.
    """

    return _center_with_sdl(window) or _center_with_screeninfo(window)
