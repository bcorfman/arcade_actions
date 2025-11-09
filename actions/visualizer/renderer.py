"""
Rendering components for ACE visualizer.

Handles drawing overlay UI using arcade.Text and arcade.ShapeElementList.
"""

from __future__ import annotations

import arcade
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.visualizer.overlay import InspectorOverlay, TargetGroup, ActionCard


class OverlayRenderer:
    """
    Renders inspector overlay to screen using Arcade primitives.

    Uses arcade.Text objects for text rendering and ShapeElementList for
    progress bars and backgrounds. Follows dependency injection by receiving
    the overlay as a parameter.
    """

    def __init__(
        self,
        overlay: InspectorOverlay,
        font_size: int = 10,
        line_height: int = 14,
    ):
        """
        Initialize the overlay renderer.

        Args:
            overlay: Injected InspectorOverlay dependency
            font_size: Font size for text rendering
            line_height: Line height for text spacing
        """
        self.overlay = overlay
        self.font_size = font_size
        self.line_height = line_height

        # Text objects for rendering (created once, reused)
        self.text_objects: list[arcade.Text] = []

        # Store rectangle parameters for backgrounds and progress bars
        self._background_rects: list[tuple[float, float, float, float, arcade.Color]] = []
        self._progress_rects: list[tuple[float, float, float, float, arcade.Color]] = []

    def update(self) -> None:
        """
        Update rendering elements from overlay data.

        Recreates text objects and shapes based on current overlay state.
        """
        if not self.overlay.visible:
            self.text_objects = []
            self._background_rects = []
            self._progress_rects = []
            return

        # Clear existing renderables
        self.text_objects = []
        self._background_rects = []
        self._progress_rects = []

        # Calculate positions
        current_y = self.overlay.y

        # Render title
        title_text = f"ACE Inspector - {self.overlay.get_total_action_count()} action(s)"
        title = arcade.Text(
            title_text,
            self.overlay.x + 5,
            current_y,
            arcade.color.WHITE,
            self.font_size + 2,
            bold=True,
        )
        self.text_objects.append(title)
        current_y -= self.line_height * 2

        # Render each group
        for group in self.overlay.groups:
            current_y = self._render_group(group, current_y)
            current_y -= self.line_height  # Gap between groups

    def _render_group(self, group: TargetGroup, start_y: int) -> int:
        """
        Render a target group.

        Args:
            group: Target group to render
            start_y: Starting Y position

        Returns:
            New Y position after rendering
        """
        current_y = start_y

        # Render group header
        header = arcade.Text(
            group.get_header_text(),
            self.overlay.x + 5,
            current_y,
            arcade.color.YELLOW,
            self.font_size,
            bold=True,
        )
        self.text_objects.append(header)
        current_y -= self.line_height

        # Render cards
        for card in group.cards:
            current_y = self._render_card(card, current_y)

        return current_y

    def _render_card(self, card: ActionCard, start_y: int) -> int:
        """
        Render an action card.

        Args:
            card: Action card to render
            start_y: Starting Y position

        Returns:
            New Y position after rendering
        """
        current_y = start_y

        # Render card text
        display_text = card.get_display_text()
        for line in display_text.split("\n"):
            text_obj = arcade.Text(
                line,
                self.overlay.x + 15,
                current_y,
                arcade.color.LIGHT_GRAY,
                self.font_size,
            )
            self.text_objects.append(text_obj)
            current_y -= self.line_height

        # Render progress bar if available
        if card.snapshot.progress is not None:
            bar_width = card.get_progress_bar_width()
            bar_height = 4
            bar_x = self.overlay.x + 15
            bar_y = current_y - 2

            left = bar_x
            bottom = bar_y - bar_height / 2
            self._background_rects.append((left, bottom, card.width, bar_height, arcade.color.DARK_GRAY))

            if bar_width > 0:
                left = bar_x
                bottom = bar_y - bar_height / 2
                self._progress_rects.append((left, bottom, bar_width, bar_height, arcade.color.GREEN))

            current_y -= 10  # Space after progress bar

        return current_y

    def draw(self) -> None:
        """Draw all overlay elements to the screen."""
        if not self.overlay.visible:
            return

        # Draw shapes first (backgrounds, progress bars)
        for rect in self._background_rects:
            arcade.draw_lbwh_rectangle_filled(*rect)
        for rect in self._progress_rects:
            arcade.draw_lbwh_rectangle_filled(*rect)

        # Draw text on top
        for text_obj in self.text_objects:
            text_obj.draw()
