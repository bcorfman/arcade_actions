"""
Rendering components for ACE visualizer.

Handles drawing overlay UI using arcade.Text and arcade.ShapeElementList.
"""

from __future__ import annotations

import arcade
from typing import TYPE_CHECKING, Callable, Iterable, NamedTuple

from pyglet.gl.lib import GLException

if TYPE_CHECKING:
    from actions.visualizer.overlay import InspectorOverlay, TargetGroup, ActionCard
    from actions.visualizer.condition_panel import ConditionDebugger, ConditionEntry
    from actions.visualizer.timeline import TimelineStrip, TimelineEntry
    from actions.visualizer.guides import GuideManager


class _TextSpec(NamedTuple):
    """Description of a text element that will be rendered."""

    text: str
    x: float
    y: float
    color: arcade.Color
    font_size: int
    bold: bool = False


def _sync_text_objects(
    text_objects: list[arcade.Text],
    specs: list[_TextSpec],
    last_specs: list[_TextSpec],
) -> None:
    """
    Ensure text objects mirror the provided specifications.

    Rebuilds the cached text objects only when the specifications change to avoid
    interacting with arcade.Text properties before an OpenGL context is active.
    """

    if last_specs == specs:
        return

    text_objects.clear()
    if not specs:
        last_specs.clear()
        return

    for spec in specs:
        text_objects.append(
            arcade.Text(
                spec.text,
                spec.x,
                spec.y,
                spec.color,
                spec.font_size,
                bold=spec.bold,
            )
        )

    last_specs[:] = list(specs)


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
        self._text_specs: list[_TextSpec] = []
        self._last_text_specs: list[_TextSpec] = []

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
            self._text_specs = []
            self._last_text_specs = []
            self._background_rects = []
            self._progress_rects = []
            return

        # Clear existing renderables
        self._text_specs = []
        self._background_rects = []
        self._progress_rects = []

        # Calculate positions
        current_y = self.overlay.y

        # Render title
        title_text = f"ACE Inspector - {self.overlay.get_total_action_count()} action(s)"
        self._text_specs.append(
            _TextSpec(
                title_text,
                self.overlay.x + 5,
                current_y,
                arcade.color.WHITE,
                self.font_size + 2,
                True,
            )
        )
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
        self._text_specs.append(
            _TextSpec(
                group.get_header_text(),
                self.overlay.x + 5,
                current_y,
                arcade.color.YELLOW,
                self.font_size,
                True,
            )
        )
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
            self._text_specs.append(
                _TextSpec(
                    line,
                    self.overlay.x + 15,
                    current_y,
                    arcade.color.LIGHT_GRAY,
                    self.font_size,
                )
            )
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

        _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)

        # Draw shapes first (backgrounds, progress bars)
        for rect in self._background_rects:
            arcade.draw_lbwh_rectangle_filled(*rect)
        for rect in self._progress_rects:
            arcade.draw_lbwh_rectangle_filled(*rect)

        # Draw text on top
        try:
            for text_obj in self.text_objects:
                text_obj.draw()
        except GLException:
            self.text_objects = []
            self._last_text_specs = []
            _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)
            for text_obj in self.text_objects:
                text_obj.draw()


class ConditionPanelRenderer:
    """Render the condition debugger panel."""

    def __init__(
        self,
        debugger: "ConditionDebugger",
        *,
        width: int = 320,
        max_rows: int = 14,
        font_size: int = 10,
        line_height: int = 16,
        margin: int = 8,
    ) -> None:
        self.debugger = debugger
        self.width = width
        self.max_rows = max_rows
        self.font_size = font_size
        self.line_height = line_height
        self.margin = margin

        self.text_objects: list[arcade.Text] = []
        self._text_specs: list[_TextSpec] = []
        self._last_text_specs: list[_TextSpec] = []
        self._background_rect: tuple[float, float, float, float, arcade.Color] | None = None
        self._border_rect: tuple[float, float, float, float, arcade.Color] | None = None
        self._visible: bool = False

    def update(self, visible: bool) -> None:
        self._visible = visible
        self._text_specs = []
        self._background_rect = None
        self._border_rect = None

        if not visible:
            self.text_objects = []
            self._last_text_specs = []
            return

        entries = self.debugger.entries
        try:
            window = arcade.get_window()
            top = window.height - self.margin
            left = window.width - self.width - self.margin
        except RuntimeError:
            top = 720 - self.margin
            left = 1280 - self.width - self.margin

        rows = min(len(entries), self.max_rows)
        if rows == 0:
            rows = 1
            display_entries: Iterable["ConditionEntry"] | None = None
        else:
            display_entries = entries[:rows]

        current_y = top - self.margin
        self._text_specs.append(
            _TextSpec(
                "Condition Debugger",
                left + self.margin,
                current_y,
                arcade.color.WHITE,
                self.font_size + 1,
                True,
            )
        )
        current_y -= self.line_height

        if display_entries is None:
            self._text_specs.append(
                _TextSpec(
                    "No condition evaluations yet",
                    left + self.margin,
                    current_y,
                    arcade.color.LIGHT_GRAY,
                    self.font_size,
                )
            )
            current_y -= self.line_height
        else:
            for entry in display_entries:
                tag = entry.tag or "-"
                result = str(entry.result)
                if len(result) > 60:
                    result = result[:57] + "..."
                line = f"{entry.action_type} [{tag}] -> {result}"
                self._text_specs.append(
                    _TextSpec(
                        line,
                        left + self.margin,
                        current_y,
                        arcade.color.LIGHT_GRAY,
                        self.font_size,
                    )
                )
                current_y -= self.line_height

        height = top - current_y + self.margin
        bottom = top - height
        self._background_rect = (
            left,
            bottom,
            self.width,
            height,
            (20, 24, 38, 200),
        )
        self._border_rect = (
            left,
            bottom,
            left + self.width,
            bottom + height,
            (90, 105, 135, 220),
        )

    def draw(self) -> None:
        if not self._visible:
            return

        _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)

        if self._background_rect is not None:
            arcade.draw_lbwh_rectangle_filled(*self._background_rect)
        if self._border_rect is not None:
            left, bottom, right, top, color = self._border_rect
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, color, border_width=1)
        try:
            for text_obj in self.text_objects:
                text_obj.draw()
        except GLException:
            self.text_objects = []
            self._last_text_specs = []
            _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)
            for text_obj in self.text_objects:
                text_obj.draw()


class TimelineRenderer:
    """Render the timeline strip."""

    def __init__(
        self,
        timeline: "TimelineStrip",
        *,
        width: int = 420,
        height: int = 90,
        margin: int = 8,
        row_height: int = 18,
        font_size: int = 9,
        target_names_provider: Callable[[], dict[int, str]] | None = None,
    ) -> None:
        self.timeline = timeline
        self.width = width
        self.height = height
        self.margin = margin
        self.row_height = row_height
        self.font_size = font_size
        self.target_names_provider = target_names_provider

        self._background_rect: tuple[float, float, float, float, arcade.Color] | None = None
        self._bars: list[tuple[float, float, float, float, arcade.Color]] = []
        self.text_objects: list[arcade.Text] = []
        self._text_specs: list[_TextSpec] = []
        self._last_text_specs: list[_TextSpec] = []

    def update(self) -> None:
        self._background_rect = None
        self._bars = []
        self._text_specs = []

        entries = [entry for entry in self.timeline.entries if entry.start_frame is not None]
        if not entries:
            self.text_objects = []
            self._last_text_specs = []
            return

        try:
            window = arcade.get_window()
            base_left = self.margin
            base_bottom = self.margin
            base_width = min(self.width, window.width - 2 * self.margin)
        except RuntimeError:
            base_left = self.margin
            base_bottom = self.margin
            base_width = self.width

        base_height = self.height
        frame_min = min(entry.start_frame or 0 for entry in entries)
        current_frame = self.timeline.debug_store.current_frame
        frame_max = max(max(entry.end_frame or current_frame, entry.start_frame or frame_min) for entry in entries)
        if frame_max == frame_min:
            frame_max += 1
        frame_span = frame_max - frame_min

        max_rows = max(1, int(base_height // self.row_height)) if self.row_height else 1
        rows = min(len(entries), max_rows)
        row_height = base_height / rows if rows else base_height

        self._background_rect = (
            base_left,
            base_bottom,
            base_width,
            base_height,
            (15, 18, 30, 200),
        )

        for index, entry in enumerate(entries[:rows]):
            start = entry.start_frame or frame_min
            end = entry.end_frame if entry.end_frame is not None else current_frame
            if end < start:
                end = start
            left = base_left + ((start - frame_min) / frame_span) * base_width
            right = base_left + ((end - frame_min) / frame_span) * base_width
            if right - left < 2:
                right = left + 2
            top = base_bottom + base_height - index * row_height
            bottom = top - row_height
            # Color-blind friendly distinction: SpriteList uses cyan/teal, Sprite uses orange
            # Different brightness for active vs inactive states
            if entry.target_type == "SpriteList":
                if entry.is_active:
                    color = arcade.color.CYAN  # Bright cyan for active SpriteList
                else:
                    color = arcade.color.TEAL  # Darker teal for inactive SpriteList
            else:  # Sprite or None/unknown
                if entry.is_active:
                    color = arcade.color.ORANGE  # Bright orange for active Sprite
                else:
                    color = arcade.color.DARK_ORANGE  # Darker orange for inactive Sprite
            self._bars.append((left, bottom, right, top, color))

            # Build label with target name if available
            target_name = None
            if entry.target_id is not None and self.target_names_provider is not None:
                try:
                    names = self.target_names_provider()
                    if names:
                        target_name = names.get(entry.target_id)
                except Exception:
                    pass  # Fall back to hex if provider fails

            # Format target identifier
            if target_name:
                target_label = target_name
            elif entry.target_id is not None:
                # Fallback to hex ID (last 4 chars for brevity)
                hex_id = hex(entry.target_id)[-4:]
                target_type_label = entry.target_type or "Unknown"
                target_label = f"{target_type_label}#{hex_id}"
            else:
                target_label = entry.target_type or "Unknown"

            label_text = f"{entry.action_type} [{entry.tag or '-'}] → {target_label}"
            label_y = bottom + max(2.0, (row_height - self.font_size) / 2)
            self._text_specs.append(
                _TextSpec(
                    label_text,
                    left + 4,
                    label_y,
                    arcade.color.BLACK,
                    self.font_size,
                )
            )

    def draw(self) -> None:
        if self._background_rect is None:
            return
        arcade.draw_lbwh_rectangle_filled(*self._background_rect)
        for left, bottom, right, top, color in self._bars:
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
        _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)
        try:
            for label in self.text_objects:
                label.draw()
        except GLException:
            self.text_objects = []
            self._last_text_specs = []
            _sync_text_objects(self.text_objects, self._text_specs, self._last_text_specs)
            for label in self.text_objects:
                label.draw()


class GuideRenderer:
    """Render velocity, bounds, and path guides."""

    def __init__(self, guide_manager: "GuideManager") -> None:
        self.guide_manager = guide_manager

    def update(self) -> None:
        # Guides operate on live data; no cached state necessary.
        return

    def draw(self) -> None:
        velocity = self.guide_manager.velocity_guide
        if velocity.enabled:
            for x1, y1, x2, y2 in velocity.arrows:
                arcade.draw_line(x1, y1, x2, y2, velocity.color, 2)

        bounds = self.guide_manager.bounds_guide
        if bounds.enabled:
            for left, bottom, right, top in bounds.rectangles:
                arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, bounds.color, border_width=2)

        path = self.guide_manager.path_guide
        if path.enabled:
            for points in path.paths:
                if len(points) >= 2:
                    arcade.draw_line_strip(points, path.color, 2)
