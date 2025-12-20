"""DevVisualizer manager for coordinating visual editing tools.

Provides unified entry point for DevVisualizer with environment variable
support and keyboard toggle (F12).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
import types
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

import arcade

if TYPE_CHECKING:
    from actions.dev.palette import PaletteSidebar
    from actions.dev.selection import SelectionManager
    from actions.dev.boundary_overlay import BoundaryGizmo
    from actions.dev.prototype_registry import DevContext

from actions.dev.boundary_overlay import BoundaryGizmo
from actions.dev.palette import PaletteSidebar
from actions.dev.palette_window import PaletteWindow
from actions.dev.prototype_registry import DevContext, get_registry
from actions.dev.selection import SelectionManager

from actions import Action
from actions.display import move_to_primary_monitor

_MISSING_GIZMO_REFRESH_SECONDS = 0.25


def _get_primary_monitor_rect() -> tuple[int, int, int, int] | None:
    """Get the primary monitor rect (x, y, width, height) using the same approach as move_to_primary_monitor.

    Returns:
        Tuple of (x, y, width, height) for primary monitor, or None if unavailable.
    """
    # Try SDL2 first (same as move_to_primary_monitor)
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
        else:  # Linux / *nix
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

    # Fall back to screeninfo (same as move_to_primary_monitor)
    try:
        from screeninfo import get_monitors

        monitors = get_monitors()
        if monitors:
            primary = monitors[0]
            return (primary.x, primary.y, primary.width, primary.height)
    except Exception:
        pass

    return None


try:
    import arcade.window_commands as window_commands_module
except ImportError:  # pragma: no cover - only happens in limited environments
    window_commands_module = None


_window_attach_hook_installed = False
_original_set_window: Callable[..., Any] | None = None

_update_all_attach_hook_installed = False
_previous_update_all_func: Callable[..., Any] | None = None


def _install_window_attach_hook() -> None:
    """Install hook on arcade.window_commands.set_window to attach DevVisualizer when window becomes available."""

    global _window_attach_hook_installed, _original_set_window

    if _window_attach_hook_installed:
        return

    if window_commands_module is None:
        return

    _original_set_window = window_commands_module.set_window

    def patched_set_window(window):
        if _original_set_window is not None:
            _original_set_window(window)

        dev_viz = get_dev_visualizer()
        if dev_viz is not None and not dev_viz._attached and window is not None:
            dev_viz.attach_to_window(window)

    window_commands_module.set_window = patched_set_window  # type: ignore[assignment]
    _window_attach_hook_installed = True


def _install_update_all_attach_hook() -> None:
    """Wrap Action.update_all so we can attach DevVisualizer once a window exists.

    This mirrors the debug visualizer strategy: keep retrying attach each frame
    without requiring the window constructor to call set_window.
    """

    global _update_all_attach_hook_installed, _previous_update_all_func

    if _update_all_attach_hook_installed:
        return

    current_update_all = Action.update_all.__func__  # type: ignore[attr-defined]
    _previous_update_all_func = current_update_all

    def wrapped_update_all(cls: type[Action], delta_time: float, physics_engine: Any = None) -> None:
        current_update_all(cls, delta_time, physics_engine=physics_engine)

        dev_viz = get_dev_visualizer()
        if dev_viz is None or dev_viz._attached:
            return

        try:
            window = arcade.get_window()
        except RuntimeError:
            window = None

        if window is not None:
            dev_viz.attach_to_window(window)

    Action.update_all = classmethod(wrapped_update_all)  # type: ignore[method-assign]
    _update_all_attach_hook_installed = True


class DevVisualizer:
    """
    Manager for DevVisualizer visual editing tools.

    Coordinates palette, selection, boundary gizmos, and scene management.
    Provides unified entry point with environment variable support and F12 toggle.
    """

    def __init__(
        self,
        scene_sprites: arcade.SpriteList | None = None,
        window: arcade.Window | None = None,
    ):
        """
        Initialize DevVisualizer.

        Args:
            scene_sprites: SpriteList for editable scene (created if None)
            window: Arcade window (auto-detected if None)
        """
        # Flag to ensure we only schedule one palette-show poll
        self._palette_show_pending: bool = False
        # Decoration deltas measured once (border width, title+border height)
        self._window_decoration_dx: int | None = None
        self._window_decoration_dy: int | None = None
        # Palette window decoration deltas (measured when palette is positioned)
        self._palette_decoration_dx: int | None = None
        self._palette_decoration_dy: int | None = None
        # Extra padding to account for window shadows not captured by decoration measurement
        # This is in addition to the measured borders (main left + palette right)
        self._EXTRA_FRAME_PAD: int = 8

        if scene_sprites is None:
            scene_sprites = arcade.SpriteList()

        self.scene_sprites = scene_sprites
        self.ctx = DevContext(scene_sprites=scene_sprites)

        # Initialize components
        # Palette is now in a separate window
        self.palette_window: PaletteWindow | None = None

        self.selection_manager = SelectionManager(scene_sprites)

        # State
        self.visible = False
        self.window = window
        self._dragging_gizmo_handle: tuple[BoundaryGizmo, object] | None = None
        self._dragging_sprites: list[tuple[arcade.Sprite, float, float]] | None = None  # (sprite, offset_x, offset_y)
        self._gizmos: WeakKeyDictionary[arcade.Sprite, BoundaryGizmo | None] = WeakKeyDictionary()
        self._gizmo_miss_refresh_at: WeakKeyDictionary[arcade.Sprite, float] = WeakKeyDictionary()
        self._tracked_window_positions: dict[int, tuple[int, int]] = {}  # window_id -> (x, y)

        # Create indicator text (shown when DevVisualizer is active)
        self._indicator_text = arcade.Text(
            "Palette [F11] | DEV EDIT MODE [F12]",
            10,
            10,
            arcade.color.YELLOW,
            16,
            bold=True,
        )

        # Track if we've attached to window
        self._attached = False
        self._is_detaching: bool = False  # Flag to prevent on_palette_close from closing main window during detachment
        self._original_on_draw: Callable[..., None] | None = None
        self._original_on_key_press: Callable[..., None] | None = None
        self._original_on_mouse_press: Callable[..., None] | None = None
        self._original_on_mouse_drag: Callable[..., None] | None = None
        self._original_on_mouse_release: Callable[..., None] | None = None
        self._original_on_close: Callable[..., None] | None = None
        self._original_view_on_draw: Callable[..., None] | None = None
        self._original_show_view: Callable[..., None] | None = None
        self._original_set_location: Callable[..., None] | None = None

    def _track_window_position(self, window: arcade.Window, x: int, y: int) -> None:
        """Track the position we set for a window."""
        self._tracked_window_positions[id(window)] = (x, y)

    def _get_tracked_window_position(self, window: arcade.Window) -> tuple[int, int] | None:
        """Get the tracked position for a window."""
        return self._tracked_window_positions.get(id(window))

    def track_window_position(self, window: arcade.Window) -> bool:
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
                self._track_window_position(window, location[0], location[1])
                return True
        except Exception as e:
            print(f"[DevVisualizer] Failed to track window position: {e}")
        return False

    def update_main_window_position(self) -> bool:
        """Update the tracked position of the main window.

        Call this after repositioning the main window to ensure palette positioning
        uses the correct relative location. For example:

        >>> dev_viz = get_dev_visualizer()
        >>> center_window(window)  # or move_to_primary_monitor(window)
        >>> dev_viz.update_main_window_position()
        """
        # Get the current window (in case it was recreated)
        window = self.window
        if window is None:
            try:
                window = arcade.get_window()
            except RuntimeError:
                pass

        if window:
            tracked = self.track_window_position(window)
            # Measure decoration deltas once
            if tracked and self._window_decoration_dx is None:
                try:
                    deco_x, deco_y = window.get_location()
                    if (deco_x, deco_y) != (0, 0):
                        # Try stored location first (from center_window/move_to_primary_monitor)
                        stored = getattr(window, "_arcadeactions_last_set_location", None)
                        if stored:
                            calc_dx = deco_x - stored[0]
                            calc_dy = deco_y - stored[1]
                            if calc_dx or calc_dy:
                                self._window_decoration_dx = calc_dx
                                self._window_decoration_dy = calc_dy
                            else:
                                print("[DevVisualizer] Decoration deltas zero on first check – will retry next frame")
                        # Fallback: use window._x/_y (pyglet client area) vs get_location() (decorated)
                        else:
                            # Try arcade window first
                            client_x = getattr(window, "_x", None)
                            client_y = getattr(window, "_y", None)
                            # If not found, try underlying pyglet window
                            if client_x is None and hasattr(window, "_window"):
                                pyglet_win = getattr(window, "_window", None)
                                if pyglet_win is not None:
                                    client_x = getattr(pyglet_win, "_x", None)
                                    client_y = getattr(pyglet_win, "_y", None)
                            if client_x is not None and client_y is not None:
                                calc_dx = deco_x - client_x
                                calc_dy = deco_y - client_y
                                if calc_dx or calc_dy:
                                    self._window_decoration_dx = calc_dx
                                    self._window_decoration_dy = calc_dy
                                else:
                                    print(
                                        "[DevVisualizer] Decoration deltas zero on first check – will retry next frame"
                                    )
                            else:
                                print(f"[DevVisualizer] Could not find client area coordinates, leaving deltas as None")
                                # Don't set to 0 - leave as None so we can try again later
                except Exception as e:
                    import traceback

                    traceback.print_exc()
            # Update self.window in case it changed
            if self.window != window:
                self.window = window
            # Reposition palette immediately whenever we capture a non-(0,0) position
            if tracked and self.palette_window is not None and not self._palette_show_pending:
                self._position_palette_window(force=True)
            return tracked
        return False

    def attach_to_window(self, window: arcade.Window | None = None) -> bool:
        """
        Attach DevVisualizer to window, wrapping event handlers.

        Args:
            window: Window to attach to (uses arcade.get_window() if None)

        Note: If already attached, detaches first before re-attaching.
        """
        # Detach if already attached
        if self._attached:
            self.detach_from_window()

        if window is None:
            try:
                window = arcade.get_window()
            except RuntimeError:
                return False

        if window is None:
            return False

        self.window = window

        # Try to track the main window position for relative positioning
        self.track_window_position(window)

        # Wrap event handlers
        self._original_on_draw = window.on_draw
        self._original_on_key_press = getattr(window, "on_key_press", None)
        self._original_on_mouse_press = getattr(window, "on_mouse_press", None)
        self._original_on_mouse_drag = getattr(window, "on_mouse_drag", None)
        self._original_on_mouse_release = getattr(window, "on_mouse_release", None)
        self._original_on_close = getattr(window, "on_close", None)

        # Wrap on_draw
        def wrapped_on_draw():
            # Ensure we're using the correct OpenGL context (main window)
            # This is important when multiple windows are open (e.g., palette window)
            # The palette window has its own OpenGL context, and if it's active,
            # we need to switch back to the main window's context before drawing
            restore_window = None
            try:
                # Check if window has an active OpenGL context
                if not hasattr(window, "_context") or window._context is None:
                    return

                if window_commands_module is not None:
                    try:
                        current_window = window_commands_module.get_window()
                    except RuntimeError:
                        current_window = None

                    if current_window is not window:
                        restore_window = current_window
                        window_commands_module.set_window(window)
                        try:
                            window.switch_to()
                        except Exception:
                            # If context switch fails, skip drawing to avoid GL errors
                            return

                # Verify context is still valid after switch
                if not hasattr(window, "_context") or window._context is None:
                    return

                # Call original on_draw first (game's draw code, including clear())
                if self._original_on_draw:
                    self._original_on_draw()

                # Always draw scene sprites after game draw (even when DevVisualizer is hidden)
                # This makes the editor work transparently - no code needed!
                # Scene sprites appear on top of game content, which is correct for editing
                self.scene_sprites.draw()

                # Draw DevVisualizer overlays only when visible
                if self.visible:
                    # Double-check context is valid before drawing DevVisualizer overlays
                    # This prevents GL errors when palette window has focus
                    try:
                        # Ensure context is still valid before drawing
                        if hasattr(window, "_context") and window._context is not None:
                            # Verify we're still on the correct window
                            if window_commands_module is not None:
                                try:
                                    active_window = window_commands_module.get_window()
                                    if active_window is not window:
                                        # Context switched away, skip drawing
                                        return
                                except RuntimeError:
                                    pass
                            self.draw()
                    except Exception as draw_error:
                        # If drawing fails due to context issues, log and continue
                        # This prevents crashes when switching between windows
                        import sys

                        print(f"[DevVisualizer] Draw error (skipping): {draw_error!r}", file=sys.stderr)
            except Exception as e:
                # Catch any GL errors and log them instead of crashing
                # This can happen when context switching fails
                import sys

                print(f"[DevVisualizer] Error in draw (context issue?): {e!r}", file=sys.stderr)
                return
            finally:
                # Restore previous window context if we switched it
                if restore_window is not None and window_commands_module is not None:
                    try:
                        window_commands_module.set_window(restore_window)
                    except Exception:
                        pass

        window.on_draw = wrapped_on_draw

        # Wrap on_key_press
        def wrapped_on_key_press(key: int, modifiers: int):
            # Handle F12 toggle (main overlay)
            if key == arcade.key.F12:
                self.toggle()
                return

            # Handle F11 toggle (palette window)
            if key == arcade.key.F11:
                self.toggle_palette()
                return

            # Handle ESC to close window (only in edit mode)
            # This matches the README: "ESC: Close application (in generated level files)"
            # Only intercept ESC when DevVisualizer is visible (edit mode)
            if key == arcade.key.ESCAPE:
                if self.visible:
                    # Close palette window, which will trigger on_palette_close callback
                    # that closes the main window (no need for explicit window.close())
                    if self.palette_window:
                        try:
                            if not self.palette_window.closed:
                                self.palette_window.close()
                        except Exception:
                            pass
                        self.palette_window = None
                    else:
                        # If palette window doesn't exist, close main window directly
                        if window is not None:
                            try:
                                if not window.closed:
                                    window.close()
                            except Exception:
                                pass
                    return
                # If not in edit mode, let original handler run first (preserves game functionality)
                # This allows games to use ESC for pause menus, canceling actions, etc.
                if self._original_on_key_press:
                    self._original_on_key_press(key, modifiers)
                    return

            # Let DevVisualizer handle keys if visible
            if self.visible and self.handle_key_press(key, modifiers):
                return

            # Otherwise call original handler
            if self._original_on_key_press:
                self._original_on_key_press(key, modifiers)

        window.on_key_press = wrapped_on_key_press

        # Wrap mouse handlers
        def wrapped_on_mouse_press(x: int, y: int, button: int, modifiers: int):
            if self.visible and self.handle_mouse_press(x, y, button, modifiers):
                return
            if self._original_on_mouse_press:
                self._original_on_mouse_press(x, y, button, modifiers)

        def wrapped_on_mouse_drag(x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
            if self.visible and self.handle_mouse_drag(x, y, dx, dy, buttons, modifiers):
                return
            if self._original_on_mouse_drag:
                self._original_on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        def wrapped_on_mouse_release(x: int, y: int, button: int, modifiers: int):
            if self.visible and self.handle_mouse_release(x, y, button, modifiers):
                return
            if self._original_on_mouse_release:
                self._original_on_mouse_release(x, y, button, modifiers)

        window.on_mouse_press = wrapped_on_mouse_press
        window.on_mouse_drag = wrapped_on_mouse_drag
        window.on_mouse_release = wrapped_on_mouse_release

        # Wrap on_close to ensure palette window shuts down with host window
        def wrapped_on_close():
            if self.visible:
                self.hide()
            if self.palette_window:
                try:
                    # Ensure palette window is closed when main window closes
                    if not self.palette_window.closed:
                        self.palette_window.close()
                except Exception:
                    # If close() fails, try to hide it at least
                    try:
                        self.palette_window.set_visible(False)
                    except Exception:
                        pass
                self.palette_window = None
            if self._original_on_close:
                self._original_on_close()

        window.on_close = wrapped_on_close

        # Wrap show_view to intercept when views are set and wrap their on_draw
        self._original_show_view = getattr(window, "show_view", None)
        self._original_set_location = getattr(window, "set_location", None)

        if self._original_set_location is not None:
            original_set_location = self._original_set_location

            def wrapped_set_location(this: arcade.Window, x: int, y: int, *args: Any, **kwargs: Any) -> None:
                original_set_location(x, y, *args, **kwargs)
                try:
                    self._track_window_position(window, int(x), int(y))
                except Exception as hook_error:
                    print(f"[DevVisualizer] set_location hook failed: {hook_error}")

            window.set_location = types.MethodType(wrapped_set_location, window)

        def wrapped_show_view(view: arcade.View) -> None:
            # Call original show_view first
            if self._original_show_view:
                self._original_show_view(view)

            # Wrap the view's on_draw method
            self._wrap_view_on_draw(view)

        if self._original_show_view:
            window.show_view = wrapped_show_view  # type: ignore[assignment]

        # If a view is already active, wrap its on_draw
        current_view = getattr(window, "current_view", None)
        if current_view is not None:
            self._wrap_view_on_draw(current_view)

        self._attached = True
        return True

    def _wrap_view_on_draw(self, view: arcade.View) -> None:
        """Wrap a View's on_draw and event handlers to integrate DevVisualizer."""
        # Store the original on_draw if not already stored
        if not hasattr(view, "_dev_viz_original_on_draw"):
            view._dev_viz_original_on_draw = view.on_draw
            view._dev_viz_original_on_key_press = getattr(view, "on_key_press", None)
            view._dev_viz_original_on_mouse_press = getattr(view, "on_mouse_press", None)
            view._dev_viz_original_on_mouse_drag = getattr(view, "on_mouse_drag", None)
            view._dev_viz_original_on_mouse_release = getattr(view, "on_mouse_release", None)

        # Create wrapped on_draw
        original_on_draw = view._dev_viz_original_on_draw

        def wrapped_view_on_draw():
            # Call original view on_draw first (game's draw code, including clear())
            if original_on_draw:
                original_on_draw()

            # Always draw scene sprites after game draw (even when DevVisualizer is hidden)
            # This makes the editor work transparently - no code needed!
            # Scene sprites appear on top of game content, which is correct for editing
            self.scene_sprites.draw()

            # Draw DevVisualizer overlays only when visible
            if self.visible:
                self.draw()

        view.on_draw = wrapped_view_on_draw  # type: ignore[assignment]

        # Wrap view's on_key_press to handle F12 toggle
        original_on_key_press = view._dev_viz_original_on_key_press

        def wrapped_view_on_key_press(key: int, modifiers: int):
            # Handle F12 toggle (main overlay)
            if key == arcade.key.F12:
                self.toggle()
                return

            # Handle F11 toggle (palette window)
            if key == arcade.key.F11:
                self.toggle_palette()
                return

            # Handle ESC to close window (only in edit mode)
            # This matches the README: "ESC: Close application (in generated level files)"
            # Only intercept ESC when DevVisualizer is visible (edit mode)
            if key == arcade.key.ESCAPE:
                if self.visible:
                    # Close palette window, which will trigger on_palette_close callback
                    # that closes the main window (no need for explicit window.close())
                    if self.palette_window:
                        try:
                            if not self.palette_window.closed:
                                self.palette_window.close()
                        except Exception:
                            pass
                        self.palette_window = None
                    else:
                        # If palette window doesn't exist, close main window directly
                        if self.window is not None:
                            try:
                                if not self.window.closed:
                                    self.window.close()
                            except Exception:
                                pass
                    return
                # If not in edit mode, let original handler run first (preserves game functionality)
                # This allows games to use ESC for pause menus, canceling actions, etc.
                if original_on_key_press:
                    original_on_key_press(key, modifiers)
                    return

            # Let DevVisualizer handle keys if visible
            if self.visible and self.handle_key_press(key, modifiers):
                return

            # Otherwise call original handler
            if original_on_key_press:
                original_on_key_press(key, modifiers)

        view.on_key_press = wrapped_view_on_key_press  # type: ignore[assignment]

        # Wrap view's mouse handlers
        original_on_mouse_press = view._dev_viz_original_on_mouse_press
        original_on_mouse_drag = view._dev_viz_original_on_mouse_drag
        original_on_mouse_release = view._dev_viz_original_on_mouse_release

        def wrapped_view_on_mouse_press(x: int, y: int, button: int, modifiers: int):
            if self.visible and self.handle_mouse_press(x, y, button, modifiers):
                return
            if original_on_mouse_press:
                original_on_mouse_press(x, y, button, modifiers)

        def wrapped_view_on_mouse_drag(x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
            if self.visible and self.handle_mouse_drag(x, y, dx, dy, buttons, modifiers):
                return
            if original_on_mouse_drag:
                original_on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        def wrapped_view_on_mouse_release(x: int, y: int, button: int, modifiers: int):
            if self.visible and self.handle_mouse_release(x, y, button, modifiers):
                return
            if original_on_mouse_release:
                original_on_mouse_release(x, y, button, modifiers)

        view.on_mouse_press = wrapped_view_on_mouse_press  # type: ignore[assignment]
        view.on_mouse_drag = wrapped_view_on_mouse_drag  # type: ignore[assignment]
        view.on_mouse_release = wrapped_view_on_mouse_release  # type: ignore[assignment]

    def detach_from_window(self) -> None:
        """Detach DevVisualizer from window, restoring original handlers."""
        if not self._attached or self.window is None:
            return

        was_visible = self.visible

        self.window.on_draw = self._original_on_draw
        self.window.on_key_press = self._original_on_key_press
        self.window.on_mouse_press = self._original_on_mouse_press
        self.window.on_mouse_drag = self._original_on_mouse_drag
        self.window.on_mouse_release = self._original_on_mouse_release
        self.window.on_close = self._original_on_close
        if self._original_set_location is not None:
            self.window.set_location = self._original_set_location  # type: ignore[assignment]
        if self._original_on_close:
            self.window.on_close = self._original_on_close

        # Restore show_view
        if self._original_show_view:
            self.window.show_view = self._original_show_view  # type: ignore[assignment]

        # Restore current view's handlers if they exist
        current_view = getattr(self.window, "current_view", None)
        if current_view is not None and hasattr(current_view, "_dev_viz_original_on_draw"):
            current_view.on_draw = current_view._dev_viz_original_on_draw  # type: ignore[assignment]
            if hasattr(current_view, "_dev_viz_original_on_key_press"):
                current_view.on_key_press = current_view._dev_viz_original_on_key_press  # type: ignore[assignment]
            if hasattr(current_view, "_dev_viz_original_on_mouse_press"):
                current_view.on_mouse_press = current_view._dev_viz_original_on_mouse_press  # type: ignore[assignment]
            if hasattr(current_view, "_dev_viz_original_on_mouse_drag"):
                current_view.on_mouse_drag = current_view._dev_viz_original_on_mouse_drag  # type: ignore[assignment]
            if hasattr(current_view, "_dev_viz_original_on_mouse_release"):
                current_view.on_mouse_release = current_view._dev_viz_original_on_mouse_release  # type: ignore[assignment]
            # Clean up stored originals
            for attr in [
                "_dev_viz_original_on_draw",
                "_dev_viz_original_on_key_press",
                "_dev_viz_original_on_mouse_press",
                "_dev_viz_original_on_mouse_drag",
                "_dev_viz_original_on_mouse_release",
            ]:
                if hasattr(current_view, attr):
                    delattr(current_view, attr)

        self._attached = False
        if was_visible:
            # Mirror hide() semantics so paused actions resume on detach.
            # Also reset drag states to prevent stale state when reattaching.
            self._dragging_gizmo_handle = None
            self._dragging_sprites = None
            self.selection_manager._is_dragging_marquee = False
            self.selection_manager._marquee_start = None
            self.selection_manager._marquee_end = None
            Action.resume_all()

        self.visible = False

        # Close palette window if it exists
        # Set flag to prevent on_palette_close callback from closing main window
        if self.palette_window:
            self._is_detaching = True
            try:
                self.palette_window.close()
            finally:
                self._is_detaching = False
            self.palette_window = None

        self._original_on_close = None
        self._original_set_location = None

    def toggle(self) -> None:
        """Toggle DevVisualizer visibility and pause/resume actions."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def _poll_show_palette(self, _dt: float = 0.0) -> None:
        """Wait until main window has a real location, then position & show palette."""
        # Check if DevVisualizer is still visible before proceeding
        # This prevents the palette from being shown if hide() was called after show()
        if not self.visible:
            self._palette_show_pending = False
            return
        if self.window is None:
            try:
                self.window = arcade.get_window()
            except RuntimeError:
                pass
        if self.window is None:
            arcade.schedule_once(self._poll_show_palette, 0.05)
            return
        loc_ok = False
        try:
            x, y = self.window.get_location()
            loc_ok = (x, y) != (0, 0) and x > -32000 and y > -32000
        except Exception:
            pass
        if not loc_ok:
            arcade.schedule_once(self._poll_show_palette, 0.05)
            return

        # Fallback: measure decoration deltas if not already measured
        # (e.g., if window was created visible=True and helpers weren't used)
        if self._window_decoration_dx is None:
            try:
                deco_x, deco_y = self.window.get_location()
                # Try stored location first (from center_window/move_to_primary_monitor)
                stored = getattr(self.window, "_arcadeactions_last_set_location", None)
                if stored:
                    calc_dx = deco_x - stored[0]
                    calc_dy = deco_y - stored[1]
                    if calc_dx or calc_dy:
                        self._window_decoration_dx = calc_dx
                        self._window_decoration_dy = calc_dy
                    else:
                        print(
                            "[DevVisualizer] _poll_show_palette: Decoration deltas zero on first check – will retry next frame"
                        )
                # Fallback: use window._x/_y (pyglet client area) vs get_location() (decorated)
                else:
                    # Try arcade window first
                    client_x = getattr(self.window, "_x", None)
                    client_y = getattr(self.window, "_y", None)
                    # If not found, try underlying pyglet window
                    if client_x is None and hasattr(self.window, "_window"):
                        pyglet_win = getattr(self.window, "_window", None)
                        if pyglet_win is not None:
                            client_x = getattr(pyglet_win, "_x", None)
                            client_y = getattr(pyglet_win, "_y", None)
                    if client_x is not None and client_y is not None:
                        calc_dx = deco_x - client_x
                        calc_dy = deco_y - client_y
                        if calc_dx or calc_dy:
                            self._window_decoration_dx = calc_dx
                            self._window_decoration_dy = calc_dy
                        else:
                            print(
                                "[DevVisualizer] _poll_show_palette: Decoration deltas zero on first check – will retry next frame"
                            )
                    else:
                        print(
                            f"[DevVisualizer] _poll_show_palette: Could not find client area coordinates, leaving deltas as None"
                        )
                        # Don't set to 0 - leave as None so we can try again later
            except Exception as e:
                print(f"[DevVisualizer] _poll_show_palette: Exception measuring decorations: {e}")
                import traceback

                traceback.print_exc()

        # Double-check visibility before showing palette (may have changed during polling)
        if not self.visible:
            self._palette_show_pending = False
            return

        # We have a trustworthy location – create / position palette now
        if self.palette_window is None:
            self._create_palette_window()
        self.update_main_window_position()
        self._position_palette_window(force=True)
        self.palette_window.show_window()
        self._palette_show_pending = False

    def show(self) -> None:
        """Show DevVisualizer and pause all actions (enter edit mode)."""
        self.visible = True
        if not self._palette_show_pending:
            self._palette_show_pending = True
            arcade.schedule_once(self._poll_show_palette, 0.0)
        Action.pause_all()

    def hide(self) -> None:
        """Hide DevVisualizer and resume all actions (exit edit mode)."""
        self.visible = False
        # Cancel any pending palette show operation
        self._palette_show_pending = False
        # Hide palette window
        if self.palette_window:
            self.palette_window.hide_window()
        # Reset all drag states to prevent stale drag when hidden during drag operation
        # This ensures that if F12 is pressed during a drag, all drag states are cleaned up
        # since the mouse release event will be skipped when visible=False
        self._dragging_gizmo_handle = None
        self._dragging_sprites = None
        # Reset selection marquee drag state
        self.selection_manager._is_dragging_marquee = False
        self.selection_manager._marquee_start = None
        self.selection_manager._marquee_end = None
        Action.resume_all()

    def _create_palette_window(self) -> None:
        """Create the palette window."""

        def on_palette_close():
            # Close main window when palette window is closed (unless we're detaching)
            # During detachment, we don't want to close the main window since it's
            # being reattached or the visualizer is being replaced
            if not self._is_detaching and self.window:
                try:
                    if not self.window.closed:
                        self.window.close()
                except Exception:
                    pass
            self.palette_window = None

        # Pass main window reference so palette can forward keystrokes to it
        # This ensures keystrokes work regardless of which window has focus,
        # matching the behavior of the ACE debugger's timeline window.
        # The forward_key_handler parameter is kept for API compatibility but not used
        # (all keys are forwarded via dispatch_event to the main window's wrapped handler)
        def forward_key_handler(key: int, modifiers: int) -> bool:
            if not self.visible:
                return False
            return self.handle_key_press(key, modifiers)

        self.palette_window = PaletteWindow(
            registry=get_registry(),
            ctx=self.ctx,
            on_close_callback=on_palette_close,
            forward_key_handler=forward_key_handler,
            main_window=self.window,
        )

    def _get_window_location(self, window: Any) -> tuple[int, int] | None:
        """Safely get window location, using tracked positions when available.

        Args:
            window: Window object (real Arcade window or HeadlessWindow)

        Returns:
            Tuple of (x, y) coordinates, or None if location cannot be determined.
        """
        if window is None:
            return None

        # Prefer the OS-reported position when it looks valid
        if hasattr(window, "get_location"):
            try:
                location = window.get_location()
                # Wayland returns (0,0) until mapped. Some WMs return huge negative off-screen coords while hidden.
                if location and location != (0, 0) and location[0] > -32000 and location[1] > -32000:
                    return (int(location[0]), int(location[1]))
            except Exception:
                pass

        # Next try tracked position (set after explicit set_location())
        tracked_pos = self._get_tracked_window_position(window)
        if tracked_pos and tracked_pos != (0, 0):
            return tracked_pos

        # Then try last explicit location stored on window
        stored = getattr(window, "_arcadeactions_last_set_location", None)
        if stored and stored != (0, 0):
            return stored

        # Fall back to location attribute for HeadlessWindow and similar mocks
        if hasattr(window, "location"):
            loc = window.location
            if isinstance(loc, tuple) and len(loc) == 2:
                return (int(loc[0]), int(loc[1]))

        return None

    def _position_palette_window(self, *, force: bool = False) -> bool:
        """Position palette window relative to main window using the same offset calculation as move_to_primary_monitor.

        Returns:
            True if positioning succeeded, False otherwise.
        """
        if self.palette_window is None:
            print(f"[DevVisualizer] No palette window, returning False")
            return False

        # Only position when window is NOT visible (like toggle_event_window does)
        if self.palette_window.visible and not force:
            print(f"[DevVisualizer] Palette window is visible, not repositioning")
            return False

        # Always get the current window (in case it was recreated)
        anchor_window = self.window
        try:
            current_window = arcade.get_window()
            if current_window is not None and self.window != current_window:
                # Adopt the new window only if it already has a valid compositor location
                test_loc = self._get_tracked_window_position(current_window)
                if test_loc is None and hasattr(current_window, "get_location"):
                    try:
                        test_loc = current_window.get_location()
                    except Exception:
                        test_loc = None
                if test_loc and test_loc != (0, 0) and test_loc[0] > -32000 and test_loc[1] > -32000:
                    self.window = current_window
                    anchor_window = current_window
                else:
                    pass
        except RuntimeError:
            pass

        if anchor_window is None:
            print(f"[DevVisualizer] Anchor window is None")
            return False

        # Get primary monitor rect using the same approach as move_to_primary_monitor
        primary_rect = _get_primary_monitor_rect()
        if primary_rect is None:
            return False
        primary_x, primary_y, primary_w, primary_h = primary_rect

        # Try to get main window location from tracked/stored data first
        main_location = self._get_window_location(anchor_window)
        if main_location is None:
            # As a last resort, use a conservative default position
            # Position main window at 25% from left/top of monitor (avoids corners and centers)
            main_x = primary_x + primary_w // 4
            main_y = primary_y + primary_h // 4
            main_location = (main_x, main_y)

        main_x, main_y = main_location

        # Calculate the offset of the main window from the primary monitor origin
        main_offset_x = main_x - primary_x
        main_offset_y = main_y - primary_y

        deco_dx = self._window_decoration_dx or 0
        deco_dy = self._window_decoration_dy or 0
        palette_width = self.palette_window.width
        palette_right_border = deco_dx if deco_dx > 0 else 0
        total_x_offset = deco_dx + palette_right_border + self._EXTRA_FRAME_PAD

        # Position palette window using the same offset system:
        # Right edge of palette aligns with left edge of main window (accounting for borders + shadow)
        # Top edge of palette aligns with top edge of main window (accounting for title bar)
        # Account for: main window left border + palette window right border + shadow padding
        # (Both windows have similar decoration sizes from the same WM)
        palette_right_border = deco_dx if deco_dx > 0 else 0  # Assume palette right border ≈ main left border
        palette_x = int(
            primary_x + main_offset_x - palette_width - deco_dx - palette_right_border - self._EXTRA_FRAME_PAD
        )
        palette_y = int(main_y - deco_dy)

        # Position window BEFORE making it visible (like toggle_event_window does)
        try:
            self.palette_window.set_location(palette_x, palette_y)
            # Palette positioned while hidden; compositor will honor these coords once mapped.
            # Track the final palette position
            self._track_window_position(self.palette_window, palette_x, palette_y)
            return True
        except Exception as e:
            print(f"[DevVisualizer] Failed to position palette window: {e}")
            return False

    def toggle_palette(self) -> None:
        """Toggle palette window visibility."""
        if self.palette_window is None:
            self._create_palette_window()
        if self.palette_window:
            # Get current visibility state
            was_visible = self.palette_window.visible
            # Position window BEFORE making it visible (like toggle_event_window does)
            if not was_visible:
                tracked = self.update_main_window_position()
                if tracked:
                    self._position_palette_window()
                else:
                    print("[DevVisualizer] Deferring palette positioning until window location is known (toggle)")
            # Toggle visibility
            self.palette_window.toggle_window()
            if not was_visible and self.palette_window.visible:
                self.palette_window.request_main_window_focus()

    def handle_key_press(self, key: int, modifiers: int) -> bool:
        """
        Handle keyboard input for DevVisualizer.

        Args:
            key: Key code
            modifiers: Modifier keys

        Returns:
            True if key was handled, False otherwise
        """
        # F12 is handled in wrapped handler (toggle main overlay)
        # F11: Toggle palette window
        if key == arcade.key.F11:
            self.toggle_palette()
            return True

        # E key: Export scene to YAML
        if key == arcade.key.E:
            from actions.dev.templates import export_template
            import os

            # Try common filenames based on context
            filename = "scene.yaml"
            if os.path.exists("examples"):
                filename = "examples/boss_level.yaml"
            elif os.path.exists("scenes"):
                filename = "scenes/new_scene.yaml"

            export_template(self.scene_sprites, filename, prompt_user=False)
            print(f"✓ Exported {len(self.scene_sprites)} sprites to {filename}")
            return True

        # I key: Import scene from YAML
        if key == arcade.key.I:
            from actions.dev.templates import load_scene_template

            import os

            # Try common filenames
            for filename in ["scene.yaml", "examples/boss_level.yaml", "scenes/new_scene.yaml"]:
                if os.path.exists(filename):
                    load_scene_template(filename, self.ctx)
                    print(f"✓ Imported scene from {filename} ({len(self.scene_sprites)} sprites)")
                    return True
            print("⚠ No scene file found. Try: scene.yaml, examples/boss_level.yaml, or scenes/new_scene.yaml")
            return True

        # Delete key: Remove selected sprites
        if key in (arcade.key.DELETE, arcade.key.BACKSPACE):
            selected = self.selection_manager.get_selected()
            if selected:
                # Remove sprites from scene
                for sprite in selected:
                    if sprite in self.scene_sprites:
                        self.scene_sprites.remove(sprite)
                    # Clean up gizmo references
                    if sprite in self._gizmos:
                        del self._gizmos[sprite]
                    if sprite in self._gizmo_miss_refresh_at:
                        del self._gizmo_miss_refresh_at[sprite]
                # Clear selection after deletion
                self.selection_manager.clear_selection()
                print(f"✓ Deleted {len(selected)} sprite(s)")
                return True

        return False

    def handle_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool:
        """
        Handle mouse press for DevVisualizer.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            button: Mouse button
            modifiers: Modifier keys

        Returns:
            True if event was handled, False otherwise
        """
        shift = modifiers & arcade.key.MOD_SHIFT

        # Handle right-click to deselect all
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.selection_manager.clear_selection()
            return True

        # Only handle left mouse button for dragging and selection
        if button != arcade.MOUSE_BUTTON_LEFT:
            return False

        # Palette is now in separate window, no need to check here

        # Check boundary gizmo handles (highest priority)
        selected = self.selection_manager.get_selected()
        for sprite in selected:
            gizmo = self._get_gizmo(sprite)
            if gizmo and gizmo.has_bounded_action():
                handle = gizmo.get_handle_at_point(x, y)
                if handle:
                    self._dragging_gizmo_handle = (gizmo, handle)
                    return True

        # Check if clicking on a selected sprite to start drag
        clicked_sprites = arcade.get_sprites_at_point((x, y), self.scene_sprites)
        if clicked_sprites:
            clicked_sprite = clicked_sprites[0]
            if clicked_sprite in selected:
                # Start dragging selected sprites
                # Calculate offset from click point to each sprite's center
                self._dragging_sprites = []
                for sprite in selected:
                    offset_x = sprite.center_x - x
                    offset_y = sprite.center_y - y
                    self._dragging_sprites.append((sprite, offset_x, offset_y))
                return True

        # Then handle selection (for unselected sprites or empty space)
        if self.selection_manager.handle_mouse_press(x, y, shift):
            return True
        return False

    def handle_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> bool:
        """
        Handle mouse drag for DevVisualizer.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            dx: X delta
            dy: Y delta
            buttons: Mouse buttons
            modifiers: Modifier keys

        Returns:
            True if event was handled, False otherwise
        """
        handled = False

        # Palette is now in separate window, no need to handle drag here

        # Handle gizmo drag (highest priority)
        if self._dragging_gizmo_handle:
            gizmo, handle = self._dragging_gizmo_handle
            gizmo.handle_drag(handle, dx, dy)
            handled = True

        # Handle sprite dragging
        elif self._dragging_sprites:
            # Update positions of all dragged sprites
            for sprite, offset_x, offset_y in self._dragging_sprites:
                sprite.center_x = x + offset_x
                sprite.center_y = y + offset_y
            handled = True

        # Handle selection marquee (lowest priority)
        elif self.selection_manager._is_dragging_marquee:
            self.selection_manager.handle_mouse_drag(x, y)
            handled = True

        return handled

    def handle_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool:
        """
        Handle mouse release for DevVisualizer.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            button: Mouse button
            modifiers: Modifier keys

        Returns:
            True if event was handled, False otherwise
        """
        handled = False

        # Palette is now in separate window, no need to handle release here

        # Handle gizmo release
        if self._dragging_gizmo_handle:
            self._dragging_gizmo_handle = None
            handled = True

        # Handle sprite drag release
        if self._dragging_sprites:
            self._dragging_sprites = None
            handled = True

        # Handle selection release (returns None, check if actively dragging marquee)
        if self.selection_manager._is_dragging_marquee:
            self.selection_manager.handle_mouse_release(x, y)
            handled = True

        return handled

    def _get_gizmo(self, sprite: arcade.Sprite) -> BoundaryGizmo | None:
        """Get or create gizmo for sprite."""
        if sprite in self._gizmos:
            cached_gizmo = self._gizmos[sprite]
            if cached_gizmo is not None:
                return cached_gizmo

            now = time.monotonic()
            refresh_at = self._gizmo_miss_refresh_at.get(sprite, 0.0)
            if now < refresh_at:
                return None

            # Cache expired; force a re-check below
            del self._gizmos[sprite]
            self._gizmo_miss_refresh_at.pop(sprite, None)

        gizmo = BoundaryGizmo(sprite)
        if gizmo.has_bounded_action():
            self._gizmos[sprite] = gizmo
            self._gizmo_miss_refresh_at.pop(sprite, None)
            return gizmo

        # Negative cache to avoid re-checking every frame, but allow periodic refresh
        expires_at = time.monotonic() + _MISSING_GIZMO_REFRESH_SECONDS
        self._gizmos[sprite] = None
        self._gizmo_miss_refresh_at[sprite] = expires_at
        return None

    def draw(self) -> None:
        """Draw DevVisualizer overlays (selection, gizmos).

        Note: scene_sprites are drawn automatically in wrapped_on_draw(),
        so this method only draws the editor UI overlays.
        Palette is now in a separate window (toggle with F11).
        """
        if not self.visible:
            return

        # Verify we have a valid window and context before drawing
        if self.window is None:
            return

        # Check if OpenGL context is valid
        if not hasattr(self.window, "_context") or self.window._context is None:
            return

        try:
            # Draw indicator (always visible when active)
            window_height = 600  # Default, will use window.height if available
            if self.window:
                window_height = self.window.height

            self._indicator_text.y = window_height - 30
            self._indicator_text.draw()

            # Palette is now in separate window (no drawing needed here)

            # Draw selection (with error handling for context issues)
            try:
                self.selection_manager.draw()
            except Exception as e:
                # If selection drawing fails (e.g., context issue), skip it
                # Suppress GLException during context switches (window focus changes)
                # as it's harmless and doesn't affect functionality
                error_str = str(e)
                is_context_switch_error = "GLException" in type(e).__name__ and (
                    "Invalid operation" in error_str or "current state" in error_str
                )

                if not is_context_switch_error:
                    # Only log non-context-switch errors
                    import sys

                    print(f"[DevVisualizer] Selection draw error (skipping): {e!r}", file=sys.stderr)
                return  # Skip remaining draws if selection fails

            # Draw boundary gizmos for selected sprites
            selected = self.selection_manager.get_selected()
            for sprite in selected:
                try:
                    gizmo = self._get_gizmo(sprite)
                    if gizmo:
                        gizmo.draw()
                except Exception:
                    # Skip gizmo if drawing fails
                    pass
        except Exception as e:
            # Catch any GL errors during drawing
            import sys

            print(f"[DevVisualizer] Draw error: {e!r}", file=sys.stderr)
            # Don't re-raise - just skip drawing this frame

    def import_sprites(self, *sprite_lists: arcade.SpriteList, clear: bool = True) -> None:
        """Import sprites from game sprite lists into the scene for editing.

        Creates copies of sprites that can be edited in the DevVisualizer.
        Original sprites are stored as references for syncing back changes.

        Args:
            *sprite_lists: One or more SpriteList objects to import from
            clear: If True, clear existing scene sprites before importing (default: True)
        """
        if clear:
            self.scene_sprites.clear()
            self.selection_manager.clear_selection()
            self._gizmos.clear()
            self._gizmo_miss_refresh_at.clear()

        for sprite_list in sprite_lists:
            for original_sprite in sprite_list:
                # Create a copy of the sprite
                imported_sprite = arcade.Sprite()

                # Copy visual properties
                imported_sprite.texture = original_sprite.texture
                imported_sprite.center_x = original_sprite.center_x
                imported_sprite.center_y = original_sprite.center_y
                imported_sprite.angle = original_sprite.angle
                # Scale can be a tuple or float - handle both
                if isinstance(original_sprite.scale, tuple):
                    imported_sprite.scale = original_sprite.scale
                else:
                    imported_sprite.scale = (original_sprite.scale, original_sprite.scale)
                imported_sprite.alpha = original_sprite.alpha
                imported_sprite.color = original_sprite.color

                # Store reference to original for syncing back
                imported_sprite._original_sprite = original_sprite

                # Add to scene
                self.scene_sprites.append(imported_sprite)

    def export_sprites(self) -> None:
        """Export sprite changes back to original game sprites.

        Syncs position, angle, scale, and other properties from edited sprites
        back to their original sprites (if they have _original_sprite reference).
        """
        for sprite in self.scene_sprites:
            if hasattr(sprite, "_original_sprite"):
                original = sprite._original_sprite

                # Sync properties back to original
                original.center_x = sprite.center_x
                original.center_y = sprite.center_y
                original.angle = sprite.angle
                # Scale - copy as is (handles both tuple and float)
                original.scale = sprite.scale
                original.alpha = sprite.alpha
                original.color = sprite.color

    def apply_metadata_actions(self, sprite: arcade.Sprite) -> None:
        """Convert action metadata on sprite to actual running actions.

        Takes action configs stored as metadata (_action_configs) and applies
        them as actual Action instances. This converts from edit mode to runtime mode.

        Args:
            sprite: Sprite with _action_configs metadata to apply
        """
        if not hasattr(sprite, "_action_configs"):
            return

        from actions import move_until, infinite

        for config in sprite._action_configs:
            action_type = config.get("action_type")

            if action_type == "MoveUntil":
                velocity = config.get("velocity", (0, 0))
                condition_name = config.get("condition", "infinite")

                # For now, only support infinite condition
                # Can be extended to support other conditions
                if condition_name == "infinite":
                    move_until(sprite, velocity=velocity, condition=infinite)


# Global DevVisualizer instance
_global_dev_visualizer: DevVisualizer | None = None


def enable_dev_visualizer(
    scene_sprites: arcade.SpriteList | None = None,
    window: arcade.Window | None = None,
    auto_attach: bool = True,
) -> DevVisualizer:
    """
    Enable DevVisualizer with optional auto-attach to window.

    Args:
        scene_sprites: SpriteList for editable scene (created if None)
        window: Arcade window (auto-detected if None)
        auto_attach: Automatically attach to window (default: True)

    Returns:
        DevVisualizer instance
    """
    global _global_dev_visualizer

    # Detach existing DevVisualizer to prevent wrapper chain and zombie instances
    if _global_dev_visualizer is not None:
        _global_dev_visualizer.detach_from_window()

    _global_dev_visualizer = DevVisualizer(scene_sprites=scene_sprites, window=window)

    if auto_attach:
        attached = _global_dev_visualizer.attach_to_window(window)
        if not attached:
            _install_window_attach_hook()
            _install_update_all_attach_hook()

    return _global_dev_visualizer


def get_dev_visualizer() -> DevVisualizer | None:
    """
    Get the global DevVisualizer instance.

    Returns:
        DevVisualizer instance if enabled, None otherwise
    """
    return _global_dev_visualizer


def auto_enable_dev_visualizer_from_env() -> DevVisualizer | None:
    """
    Auto-enable DevVisualizer if environment variable is set.

    Checks for environment variables (in order of preference):
    - ARCADEACTIONS_DEVVIZ=1 (explicit DevVisualizer)
    - ARCADEACTIONS_DEV=1 (general dev mode - includes DevVisualizer)
    - ARCADEACTIONS_DEV_MODE=1 (alternative name)

    Returns:
        DevVisualizer instance if enabled, None otherwise

    Note: If window doesn't exist yet, DevVisualizer is created but not attached.
    It will attach automatically when window becomes available (if auto_attach=True).
    When enabled via environment variable, DevVisualizer is automatically shown.

    This function is idempotent - if DevVisualizer is already enabled, returns the
    existing instance instead of creating a new one.
    """
    global _global_dev_visualizer

    # If already enabled, return existing instance (idempotent)
    if _global_dev_visualizer is not None:
        return _global_dev_visualizer

    # Check multiple environment variable options
    env_vars = [
        "ARCADEACTIONS_DEVVIZ",  # Explicit DevVisualizer
        "ARCADEACTIONS_DEV",  # General dev mode
        "ARCADEACTIONS_DEV_MODE",  # Alternative name
    ]

    for env_var in env_vars:
        if os.environ.get(env_var) == "1":
            # Try to get window, but don't fail if it doesn't exist yet
            try:
                window = arcade.get_window()
            except RuntimeError:
                window = None

            # Always request auto_attach so we install the window hook when the
            # window doesn't exist yet (common during import-time env auto-enable).
            dev_viz = enable_dev_visualizer(window=window, auto_attach=True)
            # Auto-show when enabled via environment variable (user explicitly wants editor mode)
            dev_viz.show()
            return dev_viz

    return None
