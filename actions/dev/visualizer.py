"""DevVisualizer manager for coordinating visual editing tools.

Provides unified entry point for DevVisualizer with environment variable
support and keyboard toggle (F12).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
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
from actions.dev.prototype_registry import DevContext, get_registry
from actions.dev.selection import SelectionManager

from actions import Action

_MISSING_GIZMO_REFRESH_SECONDS = 0.25

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
        palette_x: int = 10,
        palette_y: int = 10,
        palette_width: int = 200,
    ):
        """
        Initialize DevVisualizer.

        Args:
            scene_sprites: SpriteList for editable scene (created if None)
            window: Arcade window (auto-detected if None)
            palette_x: X position of palette sidebar
            palette_y: Y position of palette sidebar
            palette_width: Width of palette sidebar
        """
        if scene_sprites is None:
            scene_sprites = arcade.SpriteList()

        self.scene_sprites = scene_sprites
        self.ctx = DevContext(scene_sprites=scene_sprites)

        # Initialize components
        self.palette = PaletteSidebar(
            registry=get_registry(),
            ctx=self.ctx,
            x=palette_x,
            y=palette_y,
            width=palette_width,
        )

        self.selection_manager = SelectionManager(scene_sprites)

        # State
        self.visible = False
        self.window = window
        self._dragging_gizmo_handle: tuple[BoundaryGizmo, object] | None = None
        self._gizmos: WeakKeyDictionary[arcade.Sprite, BoundaryGizmo | None] = WeakKeyDictionary()
        self._gizmo_miss_refresh_at: WeakKeyDictionary[arcade.Sprite, float] = WeakKeyDictionary()

        # Create indicator text (shown when DevVisualizer is active)
        self._indicator_text = arcade.Text(
            "DEV EDIT MODE [F12]",
            10,
            10,
            arcade.color.YELLOW,
            16,
            bold=True,
        )

        # Track if we've attached to window
        self._attached = False
        self._original_on_draw: Callable[..., None] | None = None
        self._original_on_key_press: Callable[..., None] | None = None
        self._original_on_mouse_press: Callable[..., None] | None = None
        self._original_on_mouse_drag: Callable[..., None] | None = None
        self._original_on_mouse_release: Callable[..., None] | None = None

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

        # Wrap event handlers
        self._original_on_draw = window.on_draw
        self._original_on_key_press = getattr(window, "on_key_press", None)
        self._original_on_mouse_press = getattr(window, "on_mouse_press", None)
        self._original_on_mouse_drag = getattr(window, "on_mouse_drag", None)
        self._original_on_mouse_release = getattr(window, "on_mouse_release", None)

        # Wrap on_draw
        def wrapped_on_draw():
            # Call original on_draw first (game's draw code, including clear())
            if self._original_on_draw:
                self._original_on_draw()

            # Always draw scene sprites after game draw (even when DevVisualizer is hidden)
            # This makes the editor work transparently - no code needed!
            # Scene sprites appear on top of game content, which is correct for editing
            self.scene_sprites.draw()

            # Draw DevVisualizer overlays only when visible
            if self.visible:
                self.draw()

        window.on_draw = wrapped_on_draw

        # Wrap on_key_press
        def wrapped_on_key_press(key: int, modifiers: int):
            # Handle F12 toggle
            if key == arcade.key.F12:
                self.toggle()
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

        self._attached = True
        return True

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

        self._attached = False
        if was_visible:
            # Mirror hide() semantics so paused actions resume on detach.
            # Also reset drag states to prevent stale state when reattaching.
            self._dragging_gizmo_handle = None
            self.palette._drag_ghost = None
            self.palette._dragging_prototype = None
            self.selection_manager._is_dragging_marquee = False
            self.selection_manager._marquee_start = None
            self.selection_manager._marquee_end = None
            Action.resume_all()

        self.visible = False

    def toggle(self) -> None:
        """Toggle DevVisualizer visibility and pause/resume actions."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self) -> None:
        """Show DevVisualizer and pause all actions (enter edit mode)."""
        self.visible = True
        Action.pause_all()

    def hide(self) -> None:
        """Hide DevVisualizer and resume all actions (exit edit mode)."""
        self.visible = False
        # Reset all drag states to prevent stale drag when hidden during drag operation
        # This ensures that if F12 is pressed during a drag, all drag states are cleaned up
        # since the mouse release event will be skipped when visible=False
        self._dragging_gizmo_handle = None
        # Reset palette drag state
        self.palette._drag_ghost = None
        self.palette._dragging_prototype = None
        # Reset selection marquee drag state
        self.selection_manager._is_dragging_marquee = False
        self.selection_manager._marquee_start = None
        self.selection_manager._marquee_end = None
        Action.resume_all()

    def handle_key_press(self, key: int, modifiers: int) -> bool:
        """
        Handle keyboard input for DevVisualizer.

        Args:
            key: Key code
            modifiers: Modifier keys

        Returns:
            True if key was handled, False otherwise
        """
        # F12 is handled in wrapped handler
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

        # Check palette first
        if self.palette.handle_mouse_press(x, y):
            return True

        # Check boundary gizmo handles
        selected = self.selection_manager.get_selected()
        for sprite in selected:
            gizmo = self._get_gizmo(sprite)
            if gizmo and gizmo.has_bounded_action():
                handle = gizmo.get_handle_at_point(x, y)
                if handle:
                    self._dragging_gizmo_handle = (gizmo, handle)
                    return True

        # Then handle selection
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

        # Handle palette drag (returns None, check if actively dragging)
        if self.palette._drag_ghost is not None:
            self.palette.handle_mouse_drag(x, y)
            handled = True

        # Handle gizmo drag
        if self._dragging_gizmo_handle:
            gizmo, handle = self._dragging_gizmo_handle
            gizmo.handle_drag(handle, dx, dy)
            handled = True

        # Handle selection marquee (returns None, check if actively dragging)
        if self.selection_manager._is_dragging_marquee:
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

        # Convert screen coordinates to world coordinates if needed
        world_x, world_y = x, y

        # Handle palette release (returns bool)
        if self.palette.handle_mouse_release(world_x, world_y):
            handled = True

        # Handle gizmo release
        if self._dragging_gizmo_handle:
            self._dragging_gizmo_handle = None
            handled = True

        # Handle selection release (returns None, check if actively dragging marquee)
        if self.selection_manager._is_dragging_marquee:
            self.selection_manager.handle_mouse_release(world_x, world_y)
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
        """Draw DevVisualizer overlays (palette, selection, gizmos).

        Note: scene_sprites are drawn automatically in wrapped_on_draw(),
        so this method only draws the editor UI overlays.
        """
        if not self.visible:
            return

        # Draw indicator (always visible when active)
        # Position it at bottom-left to avoid conflicting with palette (top-left)
        window_height = 600  # Default, will use window.height if available
        if self.window:
            window_height = self.window.height

        self._indicator_text.y = window_height - 30
        self._indicator_text.draw()

        # Draw palette
        self.palette.draw()

        # Draw selection
        self.selection_manager.draw()

        # Draw boundary gizmos for selected sprites
        selected = self.selection_manager.get_selected()
        for sprite in selected:
            gizmo = self._get_gizmo(sprite)
            if gizmo:
                gizmo.draw()

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
            return enable_dev_visualizer(window=window, auto_attach=True)

    return None
