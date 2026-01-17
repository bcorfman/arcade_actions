from __future__ import annotations

from actions.dev.override_inspector import ArrangeOverrideInspector


class OverridesPanel:
    """Non-graphical panel for listing and editing arrange_grid per-cell overrides.

    This serves as the UI backend: a minimal panel used by DevVisualizer that can be
    wired to rendering code later. All operations delegate to ArrangeOverrideInspector.
    """

    def __init__(self, dev_visualizer) -> None:
        self.dev_visualizer = dev_visualizer
        self.visible: bool = False
        self.sprite = None
        self.inspector: ArrangeOverrideInspector | None = None

        # UI state
        self._selected_index: int | None = None

        # Inline edit state
        self.editing: bool = False
        self._input_buffer: str = ""
        self._editing_field: str = "x"  # 'x' or 'y'

    def start_edit(self, field: str = "x") -> None:
        """Begin inline edit for the selected override. Field must be 'x' or 'y'."""
        if field not in ("x", "y"):
            raise ValueError("field must be 'x' or 'y'")
        # Ensure a selection exists
        if self._selected_index is None:
            overrides = self.list_overrides()
            if not overrides:
                return
            self._selected_index = 0

        sel = self.get_selected()
        if not sel:
            return
        self._editing_field = field
        # Initialize buffer empty so user can type new values
        self._input_buffer = ""
        self.editing = True

    def handle_input_char(self, ch: str) -> None:
        """Handle a single character of input while editing. Supports digits, comma, minus, and backspace ("\b")."""
        if not self.editing:
            return
        if ch == "\b":
            self._input_buffer = self._input_buffer[:-1]
            return
        # Only allow digits, comma, minus
        if ch.isdigit() or ch in (",", "-"):
            self._input_buffer += ch

    def commit_edit(self) -> None:
        """Parse the input buffer and apply the override (both x,y expected)."""
        if not self.editing:
            return
        try:
            parts = [p.strip() for p in self._input_buffer.split(",", 1)]
            if len(parts) == 1:
                # If only one value provided, treat as x and keep existing y
                x = int(parts[0])
                sel = self.get_selected()
                y = sel.get("y") or 0
            else:
                x = int(parts[0]) if parts[0] != "" else 0
                y = int(parts[1]) if parts[1] != "" else 0
            sel = self.get_selected()
            if sel:
                row = sel.get("row")
                col = sel.get("col")
                self.set_override(row, col, x, y)
        except Exception:
            # Ignore parse errors and cancel
            pass
        finally:
            self.editing = False
            self._input_buffer = ""

    def cancel_edit(self) -> None:
        self.editing = False
        self._input_buffer = ""

    def select_next(self) -> None:
        overrides = self.list_overrides()
        if not overrides:
            self._selected_index = None
            return
        if self._selected_index is None:
            self._selected_index = 0
        else:
            self._selected_index = min(len(overrides) - 1, self._selected_index + 1)

    def select_prev(self) -> None:
        overrides = self.list_overrides()
        if not overrides:
            self._selected_index = None
            return
        if self._selected_index is None:
            self._selected_index = 0
        else:
            self._selected_index = max(0, self._selected_index - 1)

    def get_selected(self) -> dict | None:
        overrides = self.list_overrides()
        if not overrides or self._selected_index is None:
            return None
        if self._selected_index < 0 or self._selected_index >= len(overrides):
            return None
        return overrides[self._selected_index]

    def increment_selected(self, dx: int, dy: int) -> None:
        sel = self.get_selected()
        if not sel:
            return
        row = sel.get("row")
        col = sel.get("col")
        x = sel.get("x") or 0
        y = sel.get("y") or 0
        self.set_override(row, col, x + dx, y + dy)

    def draw(self) -> None:
        """Draw a simple textual representation of the overrides panel."""
        if not self.visible or not self.inspector:
            return
        win = self.dev_visualizer.window
        if not win:
            return
        w = getattr(win, "width", 800)
        h = getattr(win, "height", 600)

        # Draw a translucent background at top-right
        panel_w = 260
        panel_h = 120
        x = w - panel_w / 2 - 8
        y = h - panel_h / 2 - 40
        import arcade

        arcade.draw_rect_filled(arcade.rect.XYWH(x, y, panel_w, panel_h), arcade.color_from_hex_string("#22282a"))
        title = "Overrides"
        arcade.draw_text(title, x - panel_w / 2 + 8, y + panel_h / 2 - 20, arcade.color.WHITE, 14)

        overrides = self.list_overrides()
        for i, o in enumerate(overrides[:6]):
            # Render x/y and highlight editing field if applicable
            x_val = o.get("x")
            y_val = o.get("y")
            if self.editing and self._selected_index == i:
                x_s = f"[{x_val}]" if self._editing_field == "x" else f"x{x_val}"
                y_s = f"[{y_val}]" if self._editing_field == "y" else f"y{y_val}"
            else:
                x_s = f"x{x_val}"
                y_s = f"y{y_val}"
            text = f"{i}: r{o.get('row')} c{o.get('col')} {x_s} {y_s}"
            color = arcade.color.YELLOW if self._selected_index == i else arcade.color.WHITE
            arcade.draw_text(text, x - panel_w / 2 + 8, y + panel_h / 2 - 40 - i * 16, color, 12)

        # Draw input buffer if editing
        if self.editing:
            buf_text = self._input_buffer or ""
            arcade.draw_text(
                f"Edit: {buf_text}", x - panel_w / 2 + 8, y - panel_h / 2 + 20, arcade.color.LIGHT_GRAY, 12
            )

    def handle_key(self, key: str) -> None:
        """Handle simple key commands from DevVisualizer.

        Currently supports Ctrl+Z for undoing the last inspector change.
        """
        if key == "CTRL+Z":
            if self.inspector and hasattr(self.inspector, "undo"):
                if self.inspector.undo():
                    # If undo changed the underlying data, keep selection sane
                    overrides = self.list_overrides()
                    if not overrides:
                        self._selected_index = None
                    else:
                        self._selected_index = min(self._selected_index or 0, len(overrides) - 1)

    def open(self, sprite: object) -> bool:
        """Open the panel for the given sprite's arrange call. Returns True if opened."""
        inspector = self.dev_visualizer.get_override_inspector_for_sprite(sprite)
        if not inspector:
            return False
        self.sprite = sprite
        self.inspector = inspector
        self.visible = True
        return True

    def close(self) -> None:
        self.visible = False
        self.sprite = None
        self.inspector = None

    def toggle(self, sprite: object | None = None) -> bool:
        """Toggle panel visibility. If sprite is provided, open for that sprite."""
        if self.visible:
            self.close()
            return False
        if sprite is None and self.sprite is not None:
            sprite = self.sprite
        if sprite is None:
            return False
        return self.open(sprite)

    def is_open(self) -> bool:
        return self.visible

    # Delegate methods
    def list_overrides(self) -> list[dict]:
        if not self.inspector:
            return []
        return self.inspector.list_overrides()

    def set_override(self, row: int, col: int, x: int, y: int):
        if not self.inspector:
            raise RuntimeError("OverridesPanel is not open")
        return self.inspector.set_override(row, col, x, y)

    def remove_override(self, row: int, col: int):
        if not self.inspector:
            raise RuntimeError("OverridesPanel is not open")
        return self.inspector.remove_override(row, col)
