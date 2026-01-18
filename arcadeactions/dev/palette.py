"""Palette sidebar widget for DevVisualizer.

Provides drag-and-drop interface for spawning sprite prototypes into the scene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import arcade

if TYPE_CHECKING:
    from arcadeactions.dev.prototype_registry import DevContext, SpritePrototypeRegistry


class PaletteSidebar:
    """
    Sidebar widget displaying sprite prototypes for drag-and-drop spawning.

    Shows thumbnails and names of registered prototypes. Handles drag operations
    to spawn sprites at world coordinates.
    """

    def __init__(
        self,
        registry: SpritePrototypeRegistry,
        ctx: DevContext,
        x: int = 10,
        y: int = 10,
        width: int = 200,
        visible: bool = True,
    ):
        """
        Initialize palette sidebar.

        Args:
            registry: SpritePrototypeRegistry with registered prototypes
            ctx: DevContext with scene_sprites reference
            x: X position of sidebar
            y: Y position of sidebar
            width: Width of sidebar panel
            visible: Initial visibility state
        """
        self.registry = registry
        self.ctx = ctx
        self.x = x
        self.y = y
        self.width = width
        self.visible = visible
        self._dragging_prototype: str | None = None
        self._drag_ghost: arcade.Sprite | None = None
        # Cache text objects to avoid creating them every frame
        self._text_cache: list[arcade.Text] = []
        self._cached_prototype_ids: tuple[str, ...] = ()
        self._item_height = 50

    def handle_spawn(self, prototype_id: str, world_x: float, world_y: float) -> None:
        """
        Spawn a sprite from prototype at world coordinates.

        Args:
            prototype_id: ID of prototype to spawn
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        if not self.registry.has(prototype_id):
            return

        sprite = self.registry.create(prototype_id, self.ctx)
        sprite.center_x = world_x
        sprite.center_y = world_y

        if self.ctx.scene_sprites is not None:
            self.ctx.scene_sprites.append(sprite)

    def handle_mouse_press(self, x: int, y: int) -> bool:
        """
        Handle mouse press on palette.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate

        Returns:
            True if press was on palette, False otherwise
        """
        if not self.visible:
            return False

        # Check if click is within sidebar bounds
        if not (self.x <= x <= self.x + self.width):
            return False

        # Find which prototype was clicked (simplified - just check Y position)
        prototypes = list(self.registry.all().keys())
        if not prototypes:
            return False
        # Items are drawn top-to-bottom (item 0 at highest y)
        # Item i is drawn at: self.y + (len(prototypes) - i) * self._item_height
        # So relative_y = (y - self.y) // self._item_height maps to the item index as:
        # clicked_index = len(prototypes) - relative_y
        relative_y = int((y - self.y) // self._item_height)
        clicked_index = len(prototypes) - relative_y

        if 0 <= clicked_index < len(prototypes):
            self._dragging_prototype = prototypes[clicked_index]
            # Create drag ghost sprite
            if self._dragging_prototype:
                ghost = self.registry.create(self._dragging_prototype, self.ctx)
                ghost.alpha = 128  # Semi-transparent
                self._drag_ghost = ghost
            return True

        return False

    def handle_mouse_drag(self, x: float, y: float) -> None:
        """
        Handle mouse drag - update ghost sprite position.

        Args:
            x: Mouse X coordinate (world space)
            y: Mouse Y coordinate (world space)
        """
        if self._drag_ghost is not None:
            self._drag_ghost.center_x = x
            self._drag_ghost.center_y = y

    def handle_mouse_release(self, world_x: float, world_y: float) -> bool:
        """
        Handle mouse release - spawn sprite if released in world space.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            True if sprite was spawned, False otherwise
        """
        if self._dragging_prototype is None:
            return False

        # Spawn sprite at release position
        self.handle_spawn(self._dragging_prototype, world_x, world_y)

        # Clean up drag state
        self._dragging_prototype = None
        self._drag_ghost = None

        return True

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
        for i, prototype_id in enumerate(prototypes):
            y_pos = self.y + (len(prototypes) - i) * self._item_height
            text = arcade.Text(
                prototype_id,
                self.x + 10,
                y_pos,
                arcade.color.WHITE,
                14,
            )
            self._text_cache.append(text)

        self._cached_prototype_ids = current_ids

    def draw(self) -> None:
        """Draw the palette sidebar and drag ghost."""
        if not self.visible:
            return

        # Rebuild text cache if prototype list changed
        self._rebuild_text_cache()

        # Draw cached text objects (created once, reused each frame)
        for text in self._text_cache:
            text.draw()

        # Draw drag ghost if active
        if self._drag_ghost is not None:
            self._drag_ghost.draw()
