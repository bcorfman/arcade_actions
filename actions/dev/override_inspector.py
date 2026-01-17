from __future__ import annotations

from pathlib import Path

from actions.dev import sync


class ArrangeOverrideInspector:
    """Programmatic inspector for per-cell overrides on an arrange_grid call.

    Provides non-UI methods to list, edit, remove per-cell overrides, and
    simple undo support. Intended to be integrated into the DevVisualizer UI
    layer where a graphical panel can call into these methods.
    """

    def __init__(self, file_path: str | Path, lineno: int) -> None:
        self.file_path = Path(file_path)
        self.lineno = lineno
        # Simple undo stack: list of dicts describing inverse operations
        self._undo_stack: list[dict] = []

    def list_overrides(self) -> list[dict]:
        """Return a list of overrides (dicts with keys 'row','col','x','y')."""
        return sync.list_arrange_overrides(self.file_path, self.lineno)

    def set_override(self, row: int, col: int, x: int, y: int) -> sync.UpdateResult:
        """Add or update an override for (row,col) with coordinates (x,y).

        Pushes the previous state onto the undo stack so callers can undo this change.
        """
        # Capture previous entry for this cell (if any)
        prev = None
        for e in self.list_overrides():
            if e.get("row") == row and e.get("col") == col:
                prev = {"x": e.get("x"), "y": e.get("y")}
                break

        res = sync.update_arrange_cell(self.file_path, self.lineno, row, col, x, y)
        if res.changed:
            # Record inverse operation
            if prev is None:
                # The inverse is to delete the newly added cell
                self._undo_stack.append({"op": "delete", "row": row, "col": col})
            else:
                # Restore previous coords
                self._undo_stack.append({"op": "set", "row": row, "col": col, "x": prev["x"], "y": prev["y"]})
        return res

    def remove_override(self, row: int, col: int) -> sync.UpdateResult:
        """Remove the override for (row,col) if present.

        Pushes the previous state onto the undo stack so callers can undo this removal.
        """
        # Capture previous entry
        prev = None
        for e in self.list_overrides():
            if e.get("row") == row and e.get("col") == col:
                prev = {"x": e.get("x"), "y": e.get("y")}
                break

        res = sync.delete_arrange_override(self.file_path, self.lineno, row, col)
        if res.changed and prev is not None:
            # Restore by setting previous coords on undo
            self._undo_stack.append({"op": "set", "row": row, "col": col, "x": prev["x"], "y": prev["y"]})
        return res

    def undo(self) -> bool:
        """Undo last change made via this inspector. Returns True if something was undone."""
        if not self._undo_stack:
            return False
        op = self._undo_stack.pop()
        if op["op"] == "delete":
            # delete the override - only delete if present
            res = sync.delete_arrange_override(self.file_path, self.lineno, op["row"], op["col"])
            return res.changed
        if op["op"] == "set":
            res = sync.update_arrange_cell(self.file_path, self.lineno, op["row"], op["col"], op["x"], op["y"])
            return res.changed
        return False

    def can_undo(self) -> bool:
        return bool(self._undo_stack)


__all__ = ["ArrangeOverrideInspector"]
