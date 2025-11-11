"""
Rendering components for ACE visualizer.

Handles drawing overlay UI using arcade.Text and arcade.ShapeElementList.
"""

from __future__ import annotations

import arcade
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from actions.visualizer.overlay import InspectorOverlay, TargetGroup, ActionCard
    from actions.visualizer.timeline import TimelineStrip


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


class TimelineRenderer:
    """
    Renders timeline entries as horizontal bars in a dedicated window.
    
    Displays action lifetime timelines with start/end frames and visual bars.
    """

    def __init__(
        self,
        timeline: "TimelineStrip",
        width: int,
        height: int,
        margin: int,
        target_names_provider: Callable[[], dict[int, str]] | None = None,
    ):
        """
        Initialize the timeline renderer.

        Args:
            timeline: Injected TimelineStrip dependency
            width: Width of the timeline area
            height: Height of the timeline area
            margin: Margin around the timeline
            target_names_provider: Optional callable returning target names by ID
        """
        self.timeline = timeline
        self.width = width
        self.height = height
        self.margin = margin
        self.target_names_provider = target_names_provider

        # Rendering elements (created/updated in update())
        self._bars: list[tuple[float, float, float, float, arcade.Color]] = []
        self._labels: list[arcade.Text] = []

    def update(self) -> None:
        """
        Update rendering elements from timeline data.
        
        Recreates timeline bars and labels based on current timeline entries.
        """
        # Clear existing renderables
        self._bars = []
        self._labels = []

        if not self.timeline.entries:
            return

        # Calculate bar height and spacing
        entry_height = max(12, (self.height - 2 * self.margin) // max(len(self.timeline.entries), 1))
        entry_spacing = entry_height + 2

        # Get target names if provider available
        target_names: dict[int, str] = {}
        if self.target_names_provider:
            try:
                target_names = self.target_names_provider() or {}
            except Exception:
                target_names = {}

        # Calculate time range for scaling
        all_frames = []
        for entry in self.timeline.entries:
            if entry.start_frame is not None:
                all_frames.append(entry.start_frame)
            if entry.end_frame is not None:
                all_frames.append(entry.end_frame)

        if not all_frames:
            return

        min_frame = min(all_frames)
        max_frame = max(all_frames)
        frame_range = max(1, max_frame - min_frame)

        # Render each entry
        current_y = self.height - self.margin - entry_height
        for entry in self.timeline.entries:
            if current_y < self.margin:
                break

            # Calculate bar position and width
            if entry.start_frame is not None:
                bar_x = self.margin + ((entry.start_frame - min_frame) / frame_range) * (self.width - 2 * self.margin)
                bar_width = entry_height  # Default width for active entries

                if entry.end_frame is not None:
                    # Calculate width based on duration
                    bar_width = max(
                        entry_height,
                        ((entry.end_frame - entry.start_frame) / frame_range) * (self.width - 2 * self.margin),
                    )
                else:
                    # Active entry - extend to current position
                    bar_width = max(entry_height, (self.width - 2 * self.margin) - (bar_x - self.margin))

                # Choose color based on target type
                if entry.target_type == "SpriteList":
                    color = arcade.color.CYAN
                elif entry.target_type == "Sprite":
                    color = arcade.color.ORANGE
                else:
                    color = arcade.color.WHITE

                # Add bar
                self._bars.append((bar_x, current_y, bar_width, entry_height, color))

                # Add label if space allows
                if entry_spacing > 14:  # Only add labels if there's enough space
                    label_text = entry.action_type
                    if entry.target_id is not None and entry.target_id in target_names:
                        label_text = f"{target_names[entry.target_id]}: {label_text}"
                    elif entry.target_id is not None:
                        label_text = f"{entry.target_type}#{entry.target_id}: {label_text}"

                    label = arcade.Text(
                        label_text,
                        bar_x + 2,
                        current_y + entry_height / 2 - 6,
                        arcade.color.WHITE,
                        9,
                    )
                    self._labels.append(label)

            current_y -= entry_spacing

    def draw(self) -> None:
        """Draw all timeline elements to the screen."""
        # Draw bars
        for bar in self._bars:
            x, y, width, height, color = bar
            arcade.draw_lbwh_rectangle_filled(x, y, width, height, color)

        # Draw labels
        for label in self._labels:
            label.draw()
