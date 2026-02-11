"""Secondary window for dev command palette (F8)."""

from __future__ import annotations

from collections.abc import Callable

import arcade

from arcadeactions.dev.command_registry import CommandExecutionContext, CommandRegistry

try:
    from pyglet.gl.lib import GLException, MissingFunctionException
except ImportError:  # pragma: no cover
    GLException = Exception
    MissingFunctionException = Exception


class CommandPaletteWindow(arcade.Window):
    """Small secondary window for visual command list and keyboard routing."""

    MARGIN = 12
    LINE_HEIGHT = 22

    @staticmethod
    def _key_label(symbol: int) -> str:
        """Return a stable display label for a key symbol."""
        try:
            symbol_string = getattr(arcade.key, "symbol_string", None)
            if callable(symbol_string):
                return str(symbol_string(symbol))
        except Exception:
            pass
        return str(int(symbol))

    def __init__(
        self,
        *,
        registry: CommandRegistry,
        context: CommandExecutionContext,
        main_window: arcade.Window | None = None,
        on_close_callback: Callable[[], None] | None = None,
        width: int = 400,
        height: int = 240,
        title: str = "Dev Command Palette",
    ) -> None:
        try:
            super().__init__(width=width, height=height, title=title, resizable=True, visible=False)
        except (GLException, MissingFunctionException):
            self._init_headless_mode(width, height, title)
        else:
            self._is_headless = False

        self._registry = registry
        self._context = context
        self._main_window = main_window
        self._on_close_callback = on_close_callback
        self._is_visible = False
        self.selected_index = 0
        self.background_color = (24, 24, 34)
        self._title_text = None
        if not self._is_headless:
            self._title_text = arcade.Text(
                "Dev Commands",
                self.MARGIN,
                height - self.MARGIN - 20,
                arcade.color.WHITE,
                14,
                bold=True,
            )

    def _init_headless_mode(self, width: int, height: int, title: str) -> None:
        self._headless_width = int(width)
        self._headless_height = int(height)
        self._headless_scale = 1.0
        self._is_visible = False
        self.location: tuple[int, int] = (0, 0)
        self.has_exit = False
        self.handlers: dict[str, object] = {}
        self._title = title
        self._view = None
        self._is_headless = True

    def get_size(self) -> tuple[int, int]:
        """Return window size, handling unstable/headless backends safely."""
        if getattr(self, "_is_headless", False):
            return self._safe_window_size()
        try:
            return super().get_size()
        except Exception:
            return self._safe_window_size()

    def _safe_window_size(self) -> tuple[int, int]:
        width = getattr(self, "_headless_width", None)
        height = getattr(self, "_headless_height", None)
        if width is None:
            width = getattr(self, "_width", 400)
        if height is None:
            height = getattr(self, "_height", 240)
        return int(width), int(height)

    @property
    def visible(self) -> bool:
        """Return tracked visibility state."""
        return self._is_visible

    def set_visible(self, visible: bool) -> None:
        """Set visibility in both normal and headless mode."""
        self._is_visible = bool(visible)
        if self._is_headless:
            return
        try:
            super().set_visible(visible)
        except Exception:
            return

    def show_window(self) -> None:
        """Show palette window."""
        self.set_visible(True)

    def hide_window(self) -> None:
        """Hide palette window."""
        self.set_visible(False)

    def toggle_window(self) -> None:
        """Toggle palette window visibility."""
        self.set_visible(not self._is_visible)

    def set_context(self, context: CommandExecutionContext) -> None:
        """Update command execution context for live selection/window state."""
        self._context = context
        enabled = self._registry.get_enabled_commands(self._context)
        if not enabled:
            self.selected_index = 0
        elif self.selected_index >= len(enabled):
            self.selected_index = len(enabled) - 1

    def on_draw(self) -> None:
        """Draw command list."""
        if self._is_headless:
            return

        self.clear()
        try:
            width, height = self.get_size()
        except Exception:
            width, height = self._safe_window_size()
        if self._title_text is not None:
            self._title_text.y = height - self.MARGIN - 20
            self._title_text.draw()

        entries = self._registry.get_commands_with_enabled_state(self._context)
        start_y = height - self.MARGIN - 52
        active_index = 0
        for command, enabled in entries:
            color = arcade.color.WHITE if enabled else arcade.color.GRAY
            prefix = f"[{self._key_label(command.key)}] "
            text_value = f"{prefix}{command.name} ({command.category})"
            if enabled and active_index == self.selected_index:
                text_value = f"> {text_value}"
            else:
                text_value = f"  {text_value}"

            text = arcade.Text(text_value, self.MARGIN, start_y, color, 12)
            text.draw()
            start_y -= self.LINE_HEIGHT
            if enabled:
                active_index += 1

    def on_close(self) -> None:
        """Notify parent on close."""
        if self._on_close_callback is not None:
            self._on_close_callback()
        super().on_close()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle palette interactions and forward unhandled keys."""
        if symbol in (arcade.key.ESCAPE, arcade.key.F8):
            self.hide_window()
            return
        if symbol == arcade.key.DOWN:
            self._move_selection(1)
            return
        if symbol == arcade.key.UP:
            self._move_selection(-1)
            return
        if symbol == arcade.key.ENTER:
            self._execute_selected()
            return

        if self._registry.execute_key(symbol, self._context):
            return

        self._forward_to_main_window("on_key_press", symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Forward key release events to main window."""
        self._forward_to_main_window("on_key_release", symbol, modifiers)

    def _move_selection(self, direction: int) -> None:
        enabled = self._registry.get_enabled_commands(self._context)
        if not enabled:
            self.selected_index = 0
            return
        self.selected_index = (self.selected_index + direction) % len(enabled)

    def _execute_selected(self) -> None:
        enabled = self._registry.get_enabled_commands(self._context)
        if not enabled:
            return
        command = enabled[self.selected_index]
        try:
            command.handler(self._context)
        except Exception:
            return

    def _forward_to_main_window(self, handler_name: str, symbol: int, modifiers: int) -> None:
        if self._main_window is None:
            return

        try:
            self._main_window.dispatch_event(handler_name, symbol, modifiers)
        except Exception:
            try:
                if handler_name == "on_key_press":
                    self._main_window.on_key_press(symbol, modifiers)
                elif handler_name == "on_key_release":
                    self._main_window.on_key_release(symbol, modifiers)
            except Exception:
                return
