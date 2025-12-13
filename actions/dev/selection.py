"""Selection manager for DevVisualizer.

Handles click-to-select, shift-click multi-select, and marquee selection.
"""

from __future__ import annotations

import arcade


class SelectionManager:
    """
    Manages sprite selection in DevVisualizer.

    Supports:
    - Single click selection
    - Shift-click to add to selection
    - Click-drag marquee for multi-select
    - Visual outline drawing for selected sprites
    """

    def __init__(self, scene_sprites: arcade.SpriteList):
        """
        Initialize selection manager.

        Args:
            scene_sprites: SpriteList containing sprites that can be selected
        """
        self.scene_sprites = scene_sprites
        self._selected: set[arcade.Sprite] = set()
        self._marquee_start: tuple[float, float] | None = None
        self._marquee_end: tuple[float, float] | None = None
        self._is_dragging_marquee = False

    def handle_mouse_press(self, x: float, y: float, shift: bool) -> bool:
        """
        Handle mouse press for selection.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            shift: True if shift key is pressed

        Returns:
            True if selection changed, False otherwise
        """
        # Check if clicking on a sprite
        clicked_sprites = arcade.get_sprites_at_point((x, y), self.scene_sprites)

        if clicked_sprites:
            sprite = clicked_sprites[0]  # Get first sprite at point

            if shift:
                # Shift-click: toggle selection
                if sprite in self._selected:
                    self._selected.remove(sprite)
                else:
                    self._selected.add(sprite)
            else:
                # Regular click: replace selection
                if sprite not in self._selected:
                    self._selected.clear()
                    self._selected.add(sprite)
                # If already selected, keep selection (don't clear)

            return True
        else:
            # Click on empty space: start marquee if not shift
            if not shift:
                self._marquee_start = (x, y)
                self._marquee_end = (x, y)
                self._is_dragging_marquee = True
                # Clear selection when starting marquee
                self._selected.clear()
                return True

        return False

    def handle_mouse_drag(self, x: float, y: float) -> None:
        """
        Handle mouse drag - update marquee rectangle.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
        """
        if self._is_dragging_marquee:
            self._marquee_end = (x, y)

    def handle_mouse_release(self, x: float, y: float) -> None:
        """
        Handle mouse release - finalize marquee selection.

        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
        """
        if self._is_dragging_marquee and self._marquee_start is not None:
            self._marquee_end = (x, y)

            # Calculate marquee rectangle
            start_x, start_y = self._marquee_start
            end_x, end_y = self._marquee_end

            left = min(start_x, end_x)
            right = max(start_x, end_x)
            bottom = min(start_y, end_y)
            top = max(start_y, end_y)

            # Find sprites within marquee rectangle
            # Use spatial hash if available, otherwise check all sprites
            selected_in_marquee = set()

            for sprite in self.scene_sprites:
                # Check if sprite center is within rectangle
                if left <= sprite.center_x <= right and bottom <= sprite.center_y <= top:
                    selected_in_marquee.add(sprite)

            # Update selection
            self._selected = selected_in_marquee

        self._is_dragging_marquee = False
        self._marquee_start = None
        self._marquee_end = None

    def get_selected(self) -> list[arcade.Sprite]:
        """
        Get list of currently selected sprites.

        Returns:
            List of selected sprites
        """
        return list(self._selected)

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected.clear()

    def draw(self) -> None:
        """Draw selection outlines and marquee rectangle."""
        # Draw glowing outline around selected sprites
        for sprite in self._selected:
            # Draw outline using arcade shapes (simplified for MVP)
            # In full implementation, would use shader or custom drawing
            arcade.draw_rectangle_outline(
                sprite.center_x,
                sprite.center_y,
                sprite.width + 4,
                sprite.height + 4,
                arcade.color.YELLOW,
                2,
            )

        # Draw marquee rectangle if dragging
        if self._is_dragging_marquee and self._marquee_start is not None and self._marquee_end is not None:
            start_x, start_y = self._marquee_start
            end_x, end_y = self._marquee_end

            left = min(start_x, end_x)
            right = max(start_x, end_x)
            bottom = min(start_y, end_y)
            top = max(start_y, end_y)

            width = right - left
            height = top - bottom

            # Draw translucent rectangle
            arcade.draw_rectangle_outline(
                left + width / 2,
                bottom + height / 2,
                width,
                height,
                arcade.color.CYAN,
                2,
            )
            arcade.draw_rectangle_filled(
                left + width / 2,
                bottom + height / 2,
                width,
                height,
                (*arcade.color.CYAN[:3], 64),  # Semi-transparent
            )
