"""
Palette window for DevVisualizer.

Displays sprite prototypes in a dedicated window for drag-and-drop spawning.
"""

from __future__ import annotations

import arcade
from arcade import window_commands
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from actions.dev.prototype_registry import DevContext, SpritePrototypeRegistry


# Note: arcade.Window has a read-only 'ctx' property for OpenGL context,
# so we use 'dev_context' to store the DevContext to avoid conflicts


class PaletteWindow(arcade.Window):
    """Separate window that displays sprite prototype palette."""

    MARGIN = 12
    ITEM_HEIGHT = 50

    def __init__(
        self,
        registry: SpritePrototypeRegistry,
        ctx: DevContext,
        *,
        title: str = "Sprite Palette",
        width: int = 250,
        height: int = 400,
        on_close_callback: Callable[[], None] | None = None,
        forward_key_handler: Callable[[int, int], bool] | None = None,
        main_window: arcade.Window | None = None,
    ) -> None:
        # Try to create the window normally, but fall back to headless mode if OpenGL is unavailable
        # This handles CI environments (Windows/macOS) where OpenGL drivers aren't available
        try:
            super().__init__(width=width, height=height, title=title, resizable=True, visible=False)
        except Exception as e:
            # Check if this is an OpenGL-related error (headless CI environment)
            error_msg = str(e).lower()
            if "opengl" in error_msg or "glcreateshader" in error_msg or "missingfunction" in error_msg:
                # Initialize as headless window - set attributes manually without calling super().__init__()
                # This mimics what HeadlessWindow.__init__() would do
                self.width = width
                self.height = height
                # Use _is_visible instead of visible (visible is a property, not a settable attribute)
                self._is_visible = False
                self.has_exit = False
                self.location: tuple[int, int] = (0, 0)
                self._title = title
                self.handlers: dict[str, object] = {}
                self._view = None
                self._update_rate = 60
                # Mark as headless for any methods that need to check
                self._is_headless = True
            else:
                # Re-raise if it's not an OpenGL error
                raise
        else:
            # Normal initialization succeeded
            self._is_headless = False

        self.background_color = (30, 30, 40)

        self._on_close_callback = on_close_callback
        self.registry = registry
        self.dev_context = ctx
        self._forward_key_handler = forward_key_handler
        self._main_window = main_window

        # Track visibility state explicitly to avoid stale property issues
        self._is_visible = False

        # Drag state
        self._dragging_prototype: str | None = None
        self._drag_start_window_x: int = 0
        self._drag_start_window_y: int = 0

        # Cache text objects to avoid creating them every frame
        self._text_cache: list[arcade.Text] = []
        self._cached_prototype_ids: tuple[str, ...] = ()

        # Create title text
        self._title_text = arcade.Text(
            "Drag to spawn:",
            self.MARGIN,
            height - self.MARGIN - 20,
            arcade.color.WHITE,
            14,
            bold=True,
        )

    def clear(self) -> None:
        """Clear the window. No-op in headless mode."""
        if not getattr(self, "_is_headless", False):
            super().clear()

    def _draw_centered_rect(
        self, center_x: float, center_y: float, width: float, height: float, color: arcade.Color
    ) -> None:
        """
        Draw a rectangle using Arcade 3.3's lbwh helper while preserving the
        legacy center-based call sites used throughout the dev tools.
        """
        # No-op in headless mode
        if getattr(self, "_is_headless", False):
            return
        left = center_x - width / 2
        bottom = center_y - height / 2
        arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, color)

    def on_draw(self) -> None:
        """Draw the palette window."""
        # No-op in headless mode (CI environments without OpenGL)
        if getattr(self, "_is_headless", False):
            return

        self.clear()

        # Draw title
        self._title_text.y = self.height - self.MARGIN - 20
        self._title_text.draw()

        # Rebuild text cache if prototype list changed
        self._rebuild_text_cache()

        # Draw prototype items
        for text in self._text_cache:
            # Draw background for each item
            item_y = text.y - 5
            self._draw_centered_rect(
                self.width / 2,
                item_y,
                self.width - 2 * self.MARGIN,
                self.ITEM_HEIGHT - 10,
                (50, 50, 60),
            )
            text.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Handle mouse press - click to spawn sprite in main window."""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Find which prototype was clicked
        prototypes = list(self.registry.all().keys())
        if not prototypes:
            return

        # Calculate which item was clicked
        # Items start at y = height - MARGIN - 60 and go down by ITEM_HEIGHT
        start_y = self.height - self.MARGIN - 60
        relative_y = start_y - y
        clicked_index = int(relative_y / self.ITEM_HEIGHT)

        if 0 <= clicked_index < len(prototypes):
            prototype_id = prototypes[clicked_index]
            # Spawn sprite at center of main window (or last clicked position)
            self._spawn_prototype(prototype_id)

    def _spawn_prototype(self, prototype_id: str) -> None:
        """Spawn a prototype sprite in the scene."""
        if not self.registry.has(prototype_id):
            return

        sprite = self.registry.create(prototype_id, self.dev_context)
        # Default spawn position (center of typical window)
        sprite.center_x = 640
        sprite.center_y = 360

        if self.dev_context.scene_sprites is not None:
            self.dev_context.scene_sprites.append(sprite)
            print(f"✓ Spawned '{prototype_id}' sprite")

    def on_close(self) -> None:
        """Handle window close event."""
        if self._on_close_callback:
            self._on_close_callback()

    def _rebuild_text_cache(self) -> None:
        """Rebuild cached text objects when prototype list changes."""
        prototypes = list(self.registry.all().keys())
        current_ids = tuple(prototypes)

        # Only rebuild if prototype list changed
        if current_ids == self._cached_prototype_ids:
            return

        # Clear old cache
        self._text_cache.clear()

        # Create text objects for each prototype
        start_y = self.height - self.MARGIN - 60
        for i, prototype_id in enumerate(prototypes):
            y_pos = start_y - i * self.ITEM_HEIGHT
            text = arcade.Text(
                prototype_id,
                self.MARGIN + 10,
                y_pos,
                arcade.color.WHITE,
                12,
            )
            self._text_cache.append(text)

        self._cached_prototype_ids = current_ids

    def get_dragging_prototype(self) -> str | None:
        """Get the currently dragging prototype ID."""
        return self._dragging_prototype

    def get_location(self) -> tuple[int, int]:
        """Get window location. Works in both normal and headless mode."""
        # In headless mode, use location attribute directly
        if getattr(self, "_is_headless", False):
            return self.location
        # Real Arcade windows have get_location() method
        try:
            return super().get_location()  # type: ignore[misc]
        except (AttributeError, Exception):
            # Fallback to location attribute if available
            if hasattr(self, "location"):
                return self.location
            return (0, 0)

    def set_location(self, x: int, y: int) -> None:
        """Set window location. Works in both normal and headless mode."""
        # In headless mode, update location attribute directly
        if getattr(self, "_is_headless", False):
            self.location = (x, y)
            return
        # Real Arcade windows have set_location() method
        try:
            super().set_location(x, y)  # type: ignore[misc]
        except (AttributeError, Exception):
            # Fallback to location attribute if available
            if hasattr(self, "location"):
                self.location = (x, y)

    @property
    def visible(self) -> bool:
        """Return tracked visibility state."""
        # Return explicitly tracked state to avoid stale property values
        return self._is_visible

    def set_visible(self, visible: bool) -> None:
        """Set window visibility with error handling."""
        # In headless mode, just update our tracked state
        if getattr(self, "_is_headless", False):
            self._is_visible = bool(visible)
            # Don't try to set self.visible directly - it's a property
            # In headless mode, we only track _is_visible
            return

        try:
            super().set_visible(visible)
            # If successful, the parent's visible property should be updated
            # but we also track it explicitly to avoid stale values
            self._is_visible = bool(visible)
        except Exception:
            # Swallow errors during visibility changes (e.g., during context switches)
            # but still update our tracked state based on what we tried to set
            self._is_visible = bool(visible)

        # When window becomes visible, immediately request focus return to main window
        # This ensures keystrokes are always handled by the main window handler,
        # matching the behavior of the ACE debugger's timeline window
        if visible:
            self.request_main_window_focus()

    def show_window(self) -> None:
        """Show the palette window."""
        self.set_visible(True)
        # Note: Positioning should be handled by DevVisualizer after window is visible

    def hide_window(self) -> None:
        """Hide the palette window."""
        self.set_visible(False)

    def toggle_window(self) -> None:
        """Toggle palette window visibility."""
        # Use explicitly tracked state instead of property to avoid stale values
        self.set_visible(not self._is_visible)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Forward all keystrokes to main window handler."""
        self._forward_to_main_window("on_key_press", symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Forward key releases so movement stop/start stays in sync."""
        self._forward_to_main_window("on_key_release", symbol, modifiers)

    def _schedule_focus_restore(self, delay: float) -> None:
        """Schedule a delayed attempt to restore focus to the main window."""
        if self._main_window is None:
            return

        def _activate_main_window(_dt: float) -> None:
            if self._main_window is None or window_commands is None:
                return
            try:
                window_commands.set_window(self._main_window)
            except Exception:
                pass
            try:
                self._main_window.activate()
            except Exception:
                pass

        arcade.schedule_once(_activate_main_window, delay)

    def request_main_window_focus(self) -> None:
        """Schedule multiple attempts to restore focus to the main window.

        This ensures that when the palette window becomes visible, focus
        is immediately returned to the main window so keystrokes are always
        handled by the main window handler, matching ACE debugger behavior.
        """
        if self._main_window is None:
            return
        # Schedule multiple attempts with increasing delays to handle timing issues
        for delay in (0.0, 0.01, 0.05):
            self._schedule_focus_restore(delay)

    def _forward_to_main_window(self, handler_name: str, symbol: int, modifiers: int) -> None:
        """Forward keyboard events to the main window handler.

        This ensures keystrokes work regardless of which window has focus,
        matching the behavior of the ACE debugger's timeline window.
        """
        if self._forward_key_handler is not None and handler_name == "on_key_press":
            try:
                handled = bool(self._forward_key_handler(symbol, modifiers))
                if handled:
                    return
            except Exception:
                pass

        if self._main_window is None:
            return

        try:
            # Use dispatch_event to ensure the event reaches the current View
            # Direct method access (getattr(window, "on_key_press")) only hits the Window's
            # default implementation, which doesn't delegate to Views unless manually overridden.
            # This will call the wrapped handler set up by DevVisualizer, which processes
            # F11, F12, ESC, and other keys, then forwards to the original handler.
            self._main_window.dispatch_event(handler_name, symbol, modifiers)
        except Exception:
            # Fallback: try calling the method directly if dispatch_event fails
            # (e.g. if main_window isn't a real Window but a mock/stub)
            try:
                handler = getattr(self._main_window, handler_name, None)
                if handler is not None:
                    handler(symbol, modifiers)
            except Exception:
                pass
