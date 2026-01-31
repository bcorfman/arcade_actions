"""Window utility helpers for DevVisualizer."""

from __future__ import annotations

from typing import Any


def has_window_context(window: Any) -> bool:
    """Return True when window has a valid OpenGL context."""
    try:
        return window._context is not None
    except AttributeError:
        return False


def get_primary_monitor_rect() -> tuple[int, int, int, int] | None:
    """Get the primary monitor rect (x, y, width, height) using the same approach as move_to_primary_monitor."""
    from ctypes import CDLL, POINTER, Structure, byref, c_int, c_uint32
    from ctypes.util import find_library

    class _SDL_Rect(Structure):
        _fields_ = [("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int)]

    def _load_sdl2() -> CDLL | None:
        candidates: list[str] = []
        found = find_library("SDL2")
        if found:
            candidates.append(found)

        import sys

        if sys.platform.startswith("win"):
            candidates += ["SDL2.dll"]
        elif sys.platform == "darwin":
            candidates += ["libSDL2.dylib", "SDL2"]
        else:
            candidates += ["libSDL2-2.0.so.0", "libSDL2.so", "SDL2"]

        for name in candidates:
            try:
                return CDLL(name)
            except OSError:
                continue
        return None

    sdl = _load_sdl2()
    if sdl is not None:
        SDL_INIT_VIDEO = 0x00000020
        sdl.SDL_Init.argtypes = [c_uint32]
        sdl.SDL_Init.restype = c_int  # type: ignore[var-annotated]
        sdl.SDL_Quit.argtypes = []
        sdl.SDL_GetNumVideoDisplays.argtypes = []
        sdl.SDL_GetNumVideoDisplays.restype = c_int  # type: ignore[var-annotated]
        sdl.SDL_GetDisplayBounds.argtypes = [c_int, POINTER(_SDL_Rect)]
        sdl.SDL_GetDisplayBounds.restype = c_int  # type: ignore[var-annotated]

        if sdl.SDL_Init(SDL_INIT_VIDEO) == 0:
            try:
                num_displays = sdl.SDL_GetNumVideoDisplays()
                if num_displays > 0:
                    rect = _SDL_Rect()
                    if sdl.SDL_GetDisplayBounds(0, byref(rect)) == 0:
                        return (rect.x, rect.y, rect.w, rect.h)
            finally:
                sdl.SDL_Quit()

    try:
        from screeninfo import get_monitors

        monitors = get_monitors()
        if monitors:
            primary = monitors[0]
            return (primary.x, primary.y, primary.width, primary.height)
    except Exception:
        pass

    return None
