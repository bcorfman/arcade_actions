"""Secondary-window sprite property inspector with live editing."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

import arcade

from arcadeactions.dev.property_history import PropertyHistory
from arcadeactions.dev.property_registry import PropertyDefinition, SpritePropertyRegistry
from arcadeactions.dev.property_widgets import parse_property_text

try:
    from pyglet.gl.lib import GLException, MissingFunctionException
except ImportError:  # pragma: no cover
    GLException = Exception
    MissingFunctionException = Exception


class Clipboard(Protocol):
    """Clipboard adapter for copy/paste workflows."""

    def copy(self, text: str) -> None: ...

    def paste(self) -> str: ...


class InMemoryClipboard:
    """Default clipboard used in tests/headless mode."""

    def __init__(self) -> None:
        self._value = ""

    def copy(self, text: str) -> None:
        self._value = text

    def paste(self) -> str:
        return self._value


class SpritePropertyInspector:
    """Core property inspector model independent from window rendering."""

    def __init__(
        self,
        *,
        property_registry: SpritePropertyRegistry,
        history: PropertyHistory,
        clipboard: Clipboard,
        window: arcade.Window | None,
    ) -> None:
        self._registry = property_registry
        self._history = history
        self._clipboard = clipboard
        self._window = window
        self._selection: list[arcade.Sprite] = []
        self._last_non_empty_selection: list[arcade.Sprite] = []
        self._properties: list[PropertyDefinition] = []
        self._active_index = 0

    def set_selection(self, selection: Sequence[arcade.Sprite]) -> None:
        self._selection = list(selection)
        if self._selection:
            self._last_non_empty_selection = list(self._selection)
        self._properties = self._registry.properties_for_selection(self._selection)
        if self._active_index >= len(self._properties):
            self._active_index = max(0, len(self._properties) - 1)

    def selection(self) -> list[arcade.Sprite]:
        return list(self._selection)

    def visible_properties(self) -> list[PropertyDefinition]:
        return list(self._properties)

    def current_property(self) -> PropertyDefinition | None:
        if not self._properties:
            return None
        return self._properties[self._active_index]

    def move_active_property(self, delta: int) -> None:
        if not self._properties:
            self._active_index = 0
            return
        self._active_index = (self._active_index + delta) % len(self._properties)

    def _expression_names(self, property_name: str) -> dict[str, float]:
        width = 0.0
        height = 0.0
        if self._window is not None:
            width = float(self._window.width)
            height = float(self._window.height)

        axis_center = width / 2.0
        if property_name in ("center_y", "top", "bottom"):
            axis_center = height / 2.0

        return {
            "SCREEN_WIDTH": width,
            "SCREEN_HEIGHT": height,
            "SCREEN_CENTER": axis_center,
            "SCREEN_CENTER_X": width / 2.0,
            "SCREEN_CENTER_Y": height / 2.0,
        }

    def apply_property_text(self, property_name: str, text: str) -> bool:
        if not self._selection:
            return False

        parsed = parse_property_text(property_name, text, self._expression_names(property_name))
        for sprite in self._selection:
            old_value = self._registry.get_value(sprite, property_name)
            self._registry.set_value(sprite, property_name, parsed)
            new_value = self._registry.get_value(sprite, property_name)
            if old_value != new_value:
                self._history.record_change(sprite, property_name, old_value, new_value)
        return True

    def undo(self) -> bool:
        targets = self._selection if self._selection else self._last_non_empty_selection
        changed = False
        for sprite in targets:
            if self._history.undo(sprite) is not None:
                changed = True
        return changed

    def redo(self) -> bool:
        targets = self._selection if self._selection else self._last_non_empty_selection
        changed = False
        for sprite in targets:
            if self._history.redo(sprite) is not None:
                changed = True
        return changed

    def copy_selection_as_python(self, property_names: Sequence[str] | None = None) -> str:
        if not self._selection:
            snippet = ""
            self._clipboard.copy(snippet)
            return snippet

        names = list(property_names) if property_names is not None else [prop.name for prop in self._properties]
        lines: list[str] = []
        sprite = self._selection[0]
        for property_name in names:
            value = self._registry.get_value(sprite, property_name)
            lines.append(f"sprite.{property_name} = {self._format_python_value(value)}")

        snippet = "\n".join(lines)
        self._clipboard.copy(snippet)
        return snippet

    def copy_current_property(self) -> str:
        current = self.current_property()
        if current is None or not self._selection:
            self._clipboard.copy("")
            return ""
        value = self._registry.get_value(self._selection[0], current.name)
        snippet = f"sprite.{current.name} = {self._format_python_value(value)}"
        self._clipboard.copy(snippet)
        return snippet

    def paste_assignment(self, text: str) -> bool:
        parts = text.split("=", 1)
        if len(parts) != 2:
            return False
        lhs = parts[0].strip()
        rhs = parts[1].strip()
        if not lhs.startswith("sprite."):
            return False
        property_name = lhs.removeprefix("sprite.")
        return self.apply_property_text(property_name, rhs)

    def paste_from_clipboard(self) -> bool:
        return self.paste_assignment(self._clipboard.paste())

    @staticmethod
    def _format_python_value(value: object) -> str:
        if type(value) is str:
            return repr(value)
        return str(value)


class PropertyInspectorWindow(arcade.Window):
    """Secondary window wrapper for SpritePropertyInspector interactions."""

    MARGIN = 12
    LINE_HEIGHT = 20

    def __init__(
        self,
        *,
        inspector: SpritePropertyInspector,
        main_window: arcade.Window | None = None,
        on_close_callback: Callable[[], None] | None = None,
        width: int = 360,
        height: int = 420,
        title: str = "Sprite Property Inspector",
    ) -> None:
        self._is_headless = False
        self._is_visible = False
        try:
            super().__init__(width=width, height=height, title=title, resizable=True, visible=False)
        except (GLException, MissingFunctionException):
            self._init_headless_mode(width, height, title)
        else:
            self._is_headless = False

        self._inspector = inspector
        self._main_window = main_window
        self._on_close_callback = on_close_callback
        self.background_color = (26, 26, 34)
        self._title_text = None
        if not self._is_headless:
            self._title_text = arcade.Text(
                "Sprite Properties",
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
        self.location = (0, 0)
        self.has_exit = False
        self.handlers = {}
        self._title = title
        self._view = None
        self._is_headless = True

    @property
    def visible(self) -> bool:
        return self._is_visible

    def set_visible(self, visible: bool) -> None:
        self._is_visible = bool(visible)
        if self._is_headless:
            return
        try:
            super().set_visible(visible)
        except Exception:
            return

    def show_window(self) -> None:
        self.set_visible(True)

    def hide_window(self) -> None:
        self.set_visible(False)

    def set_selection(self, selection: Sequence[arcade.Sprite]) -> None:
        self._inspector.set_selection(selection)

    def apply_property_text(self, property_name: str, text: str) -> bool:
        return self._inspector.apply_property_text(property_name, text)

    def undo(self) -> bool:
        return self._inspector.undo()

    def redo(self) -> bool:
        return self._inspector.redo()

    def copy_selection_as_python(self, property_names: Sequence[str] | None = None) -> str:
        return self._inspector.copy_selection_as_python(property_names)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in (arcade.key.ESCAPE,):
            self.hide_window()
            return

        if symbol == arcade.key.DOWN:
            self._inspector.move_active_property(1)
            return

        if symbol == arcade.key.UP:
            self._inspector.move_active_property(-1)
            return

        if symbol == arcade.key.TAB:
            direction = -1 if modifiers & arcade.key.MOD_SHIFT else 1
            self._inspector.move_active_property(direction)
            return

        if symbol == arcade.key.SPACE:
            current = self._inspector.current_property()
            if current is None:
                return
            if current.editor_type != "bool":
                return
            selection = self._inspector.selection()
            if not selection:
                return
            current_value = bool(selection[0].__dict__.get(current.name, object.__getattribute__(selection[0], current.name)))
            self._inspector.apply_property_text(current.name, "false" if current_value else "true")
            return

        if modifiers & arcade.key.MOD_CTRL:
            if symbol == arcade.key.C:
                self._inspector.copy_current_property()
                return
            if symbol == arcade.key.V:
                self._inspector.paste_from_clipboard()
                return
            if symbol == arcade.key.Z:
                self._inspector.undo()
                return
            if symbol == arcade.key.Y:
                self._inspector.redo()
                return

        self._forward_to_main_window(symbol, modifiers)

    def _forward_to_main_window(self, symbol: int, modifiers: int) -> None:
        if self._main_window is None:
            return
        try:
            self._main_window.dispatch_event("on_key_press", symbol, modifiers)
        except Exception:
            try:
                self._main_window.on_key_press(symbol, modifiers)
            except Exception:
                return

    def on_draw(self) -> None:
        if self._is_headless:
            return

        self.clear()
        width = self.width
        height = self.height
        if self._title_text is not None:
            self._title_text.y = height - self.MARGIN - 20
            self._title_text.draw()

        y = height - self.MARGIN - 52
        properties = self._inspector.visible_properties()
        current = self._inspector.current_property()
        for prop in properties:
            prefix = "> " if current is not None and current.name == prop.name else "  "
            text = arcade.Text(f"{prefix}{prop.category}: {prop.name}", self.MARGIN, y, arcade.color.WHITE, 11)
            text.draw()
            y -= self.LINE_HEIGHT
            if y < self.MARGIN:
                break

    def on_close(self) -> None:
        if self._on_close_callback is not None:
            self._on_close_callback()
        super().on_close()
