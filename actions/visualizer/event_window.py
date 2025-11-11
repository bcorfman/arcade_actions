"""
Timeline viewer window for the ACE visualizer.

Displays action lifetime timelines in a dedicated window.
"""

from __future__ import annotations

import arcade
from typing import Callable

from arcade import window_commands

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.timeline import TimelineStrip
from actions.visualizer.renderer import TimelineRenderer


class EventInspectorWindow(arcade.Window):
    """Secondary window that displays action timeline bars."""

    MARGIN = 12

    def __init__(
        self,
        debug_store: DebugDataStore,
        *,
        title: str = "ACE Action Timeline",
        width: int = 520,
        height: int = 360,
        on_close_callback: Callable[[], None] | None = None,
        target_names_provider: Callable[[], dict[int, str]] | None = None,
        timeline_cls: type[TimelineStrip] = TimelineStrip,
        timeline_renderer_cls: type[TimelineRenderer] = TimelineRenderer,
    ) -> None:
        super().__init__(width=width, height=height, title=title, resizable=True, visible=False)
        self.background_color = (20, 24, 38)

        self._on_close_callback = on_close_callback

        self._timeline = timeline_cls(debug_store)
        # Timeline fills entire window minus margins
        self._timeline_renderer = timeline_renderer_cls(
            self._timeline,
            width=width - 2 * self.MARGIN,
            height=height - 2 * self.MARGIN,
            margin=self.MARGIN,
            target_names_provider=target_names_provider,
        )

        self._font_size = 11
        self._suppress_next_close_key = True

        self._timeline_label = arcade.Text(
            "Action Timeline",
            self.MARGIN,
            0,
            arcade.color.WHITE,
            self._font_size + 2,
            bold=True,
        )
        self._legend_prefix = arcade.Text(
            "Legend: ",
            self.MARGIN,
            0,
            arcade.color.WHITE,
            self._font_size,
        )
        self._legend_sprite_list = arcade.Text(
            "SpriteList",
            self.MARGIN,
            0,
            arcade.color.CYAN,
            self._font_size,
        )
        self._legend_separator = arcade.Text(
            " | ",
            self.MARGIN,
            0,
            arcade.color.WHITE,
            self._font_size,
        )
        self._legend_sprite = arcade.Text(
            "Sprite",
            self.MARGIN,
            0,
            arcade.color.ORANGE,
            self._font_size,
        )

    # ------------------------------------------------------------------ Events
    def on_draw(self) -> None:
        if not self._has_active_context():
            return

        restore_window = None
        try:
            try:
                current_window = window_commands.get_window()
            except RuntimeError:
                current_window = None

            if current_window is not self:
                restore_window = current_window
                window_commands.set_window(self)

            try:
                self.switch_to()
            except Exception:
                return

            self.clear()

            self._timeline.update()
            # Update timeline renderer with current window dimensions
            # Account for title (font_size + 2) and legend (font_size + 4) at top, plus spacing
            title_height = self._font_size + 2  # Title font size
            legend_height = self._font_size + 4  # Legend font size + spacing
            title_and_legend_height = title_height + legend_height + self.MARGIN
            self._timeline_renderer.width = self.width - 2 * self.MARGIN
            self._timeline_renderer.height = self.height - 2 * self.MARGIN - title_and_legend_height
            self._timeline_renderer.update()

            self._draw_background()
            self._draw_timeline()
        finally:
            if restore_window is not None:
                window_commands.set_window(restore_window)
            else:
                window_commands.set_window(None)

    def on_update(self, delta_time: float) -> None:  # noqa: ARG002
        # No per-frame state accumulation; draw pulls current data.
        return

    def on_close(self) -> None:
        if self._on_close_callback is not None:
            try:
                self._on_close_callback()
            except Exception as exc:
                print(f"[ACE] Error in event window close callback: {exc!r}")
        super().on_close()

    # ---------------------------------------------------------------- Controls
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:  # noqa: ARG002
        # No interactive controls; clicks are ignored.
        return

    def on_key_press(self, symbol: int, modifiers: int) -> None:  # noqa: ARG002
        if symbol == arcade.key.F4:
            if self._suppress_next_close_key:
                self._suppress_next_close_key = False
                return
            self.close()

    # ---------------------------------------------------------------- Helpers
    def _draw_timeline(self) -> None:
        # Draw title at top
        title_y = self.height - self.MARGIN - 4
        self._timeline_label.position = (self.MARGIN, title_y)
        self._timeline_label.draw()

        # Draw legend below title with colored text
        legend_y = title_y - (self._font_size + 2) - 4
        x_pos = self.MARGIN

        # "Legend: "
        self._legend_prefix.position = (x_pos, legend_y)
        self._legend_prefix.draw()
        x_pos += self._legend_prefix.content_width

        # "SpriteList" in cyan
        self._legend_sprite_list.position = (x_pos, legend_y)
        self._legend_sprite_list.draw()
        x_pos += self._legend_sprite_list.content_width

        # " | "
        self._legend_separator.position = (x_pos, legend_y)
        self._legend_separator.draw()
        x_pos += self._legend_separator.content_width

        # "Sprite" in orange
        self._legend_sprite.position = (x_pos, legend_y)
        self._legend_sprite.draw()

        # Timeline renderer draws itself (height already adjusted in on_draw)
        self._timeline_renderer.draw()

    def _draw_background(self) -> None:
        if not self._has_active_context():
            return
        # Single background for entire timeline area
        arcade.draw_lbwh_rectangle_filled(
            self.MARGIN,
            self.MARGIN,
            self.width - 2 * self.MARGIN,
            self.height - 2 * self.MARGIN,
            (25, 30, 47, 200),
        )

    def _has_active_context(self) -> bool:
        return getattr(self, "_context", None) is not None
