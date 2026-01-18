"""
Timeline viewer window for the ACE visualizer.

Displays action lifetime timelines in a dedicated window.
"""

from __future__ import annotations

from collections.abc import Callable

import arcade
from arcade import window_commands

from arcadeactions.visualizer.instrumentation import DebugDataStore
from arcadeactions.visualizer.renderer import TimelineRenderer
from arcadeactions.visualizer.timeline import TimelineStrip


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
        highlighted_target_provider: Callable[[], int | None] | None = None,
        timeline_cls: type[TimelineStrip] = TimelineStrip,
        timeline_renderer_cls: type[TimelineRenderer] = TimelineRenderer,
        forward_key_handler: Callable[[int, int], bool] | None = None,
        main_window: arcade.Window | None = None,
    ) -> None:
        super().__init__(width=width, height=height, title=title, resizable=True, visible=False)
        self.background_color = (20, 24, 38)

        self._base_width = width
        self._base_height = height
        self._min_font_size = 10.0
        self._max_font_size = 12.0
        self._font_size = self._min_font_size
        self._should_draw = False
        self._forward_key_handler = forward_key_handler
        self._main_window = main_window

        try:
            self.set_minimum_size(width, height)  # type: ignore[attr-defined]
        except Exception:
            pass

        self._on_close_callback = on_close_callback

        self._timeline = timeline_cls(debug_store)
        # Timeline fills entire window minus margins
        self._timeline_renderer = timeline_renderer_cls(
            self._timeline,
            width=width - 2 * self.MARGIN,
            height=height - 2 * self.MARGIN,
            margin=self.MARGIN,
            target_names_provider=target_names_provider,
            highlighted_target_provider=highlighted_target_provider,
        )

        self._timeline_label: arcade.Text | None = None
        self._legend_prefix: arcade.Text | None = None
        self._legend_sprite_list: arcade.Text | None = None
        self._legend_separator: arcade.Text | None = None
        self._legend_sprite: arcade.Text | None = None

        self._update_font_size_for_window(width, height)

    # ------------------------------------------------------------------ Events
    def on_draw(self) -> None:
        if not self._should_draw:
            return
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

    def _schedule_focus_restore(self, delay: float) -> None:
        if self._main_window is None:
            return

        def _activate_main_window(_dt: float) -> None:
            if self._main_window is None:
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
        """Schedule multiple attempts to restore focus to the main window."""
        if self._main_window is None:
            return
        for delay in (0.0, 0.01, 0.05):
            self._schedule_focus_restore(delay)

    def on_key_press(self, symbol: int, modifiers: int) -> None:  # noqa: ARG002
        # Only handle F4 to close the window
        # All other keys should be forwarded to the main game window
        if symbol == arcade.key.F4:
            if self._forward_key_handler is not None:
                handled = False
                try:
                    handled = bool(self._forward_key_handler(symbol, modifiers))
                except Exception:
                    handled = False
                if handled:
                    return
            self.close()
        else:
            self._forward_to_main_window("on_key_press", symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:  # noqa: ARG002
        """Forward key releases so movement stop/start stays in sync."""
        self._forward_to_main_window("on_key_release", symbol, modifiers)

    def _forward_to_main_window(self, handler_name: str, symbol: int, modifiers: int) -> None:
        # First try the debug handler (for function keys)
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

    def set_visible(self, visible: bool) -> None:
        try:
            super().set_visible(visible)
        except Exception:
            pass
        self._should_draw = bool(visible)
        if visible:
            self.request_main_window_focus()
            self._update_font_size_for_window(self._base_width, self._base_height)

    def on_resize(self, width: int, height: int) -> None:
        if width < self._base_width or height < self._base_height:
            super().on_resize(self._base_width, self._base_height)
            self.set_size(self._base_width, self._base_height)
            self._update_font_size_for_window(self._base_width, self._base_height)
            return

        super().on_resize(width, height)
        self._update_font_size_for_window(width, height)

    # ---------------------------------------------------------------- Helpers
    def _draw_timeline(self) -> None:
        # Draw title at top
        title_y = self.height - self.MARGIN - 4
        if self._timeline_label is not None:
            self._timeline_label.position = (self.MARGIN, title_y)
            self._timeline_label.draw()

        # Draw legend below title with colored text
        legend_y = title_y - (self._font_size + 2) - 4
        x_pos = self.MARGIN

        # "Legend: "
        if self._legend_prefix is not None:
            self._legend_prefix.position = (x_pos, legend_y)
            self._legend_prefix.draw()
            x_pos += self._legend_prefix.content_width

        # "SpriteList" in cyan
        if self._legend_sprite_list is not None:
            self._legend_sprite_list.position = (x_pos, legend_y)
            self._legend_sprite_list.draw()
            x_pos += self._legend_sprite_list.content_width

        # " | "
        if self._legend_separator is not None:
            self._legend_separator.position = (x_pos, legend_y)
            self._legend_separator.draw()
            x_pos += self._legend_separator.content_width

        # "Sprite" in orange
        if self._legend_sprite is not None:
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

    def _build_text_elements(self) -> None:
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

    def _update_font_size_for_window(self, width: int, height: int) -> None:
        scale = min(width / self._base_width, height / self._base_height)
        max_scale = self._max_font_size / self._min_font_size
        clamped_scale = max(1.0, min(scale, max_scale))
        new_font_size = max(self._min_font_size, min(self._min_font_size * clamped_scale, self._max_font_size))

        font_changed = abs(new_font_size - self._font_size) > 0.01
        requires_init = self._timeline_label is None

        if font_changed or requires_init:
            self._font_size = new_font_size
            self._build_text_elements()
            self._timeline_renderer.set_font_size(self._font_size)
