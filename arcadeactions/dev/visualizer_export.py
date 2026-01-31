"""Helpers for exporting DevVisualizer sprite edits back to runtime."""

from __future__ import annotations

from typing import Any


def export_sprites(scene_sprites: list[Any]) -> None:
    """Export sprite changes back to original sprites and source markers."""
    for sprite in scene_sprites:
        if hasattr(sprite, "_original_sprite"):
            original = sprite._original_sprite  # type: ignore[attr-defined]
            _sync_original_properties(sprite, original)
            _sync_source_markers(sprite)


def _sync_original_properties(sprite: Any, original: Any) -> None:
    original.center_x = sprite.center_x
    original.center_y = sprite.center_y
    original.angle = sprite.angle
    original.scale = sprite.scale
    original.alpha = sprite.alpha
    original.color = sprite.color


def _sync_source_markers(sprite: Any) -> None:
    try:
        pid = getattr(sprite, "_position_id", None)
        markers = getattr(sprite, "_source_markers", None)
        if not pid or not markers:
            return

        from arcadeactions.dev import sync

        last_marker = None
        for marker in markers:
            last_marker = marker
            file = marker.get("file")
            attr = marker.get("attr")
            if not (file and attr):
                continue

            new_value_src = _get_marker_value(sprite, attr)
            if new_value_src is None:
                continue
            try:
                sync.update_position_assignment(file, pid, attr, new_value_src)
            except Exception:
                pass

        if last_marker is None:
            return

        if last_marker.get("type") == "arrange":
            _sync_arrange_marker(sprite, last_marker)
    except Exception:
        pass


def _get_marker_value(sprite: Any, attr: str) -> str | None:
    if attr == "left":
        val = getattr(sprite, "left", None)
        if val is None:
            val = sprite.center_x
        return str(int(round(val)))
    if attr == "top":
        val = getattr(sprite, "top", None)
        if val is None:
            val = sprite.center_y
        return str(int(round(val)))
    if attr == "center_x":
        return str(int(round(sprite.center_x)))
    return None


def _sync_arrange_marker(sprite: Any, marker: dict) -> None:
    file = marker.get("file")
    lineno = marker.get("lineno")
    kwargs = marker.get("kwargs", {}) or {}
    new_start_x = int(round(getattr(sprite, "left", sprite.center_x)))
    new_start_y = int(round(getattr(sprite, "top", sprite.center_y)))

    from arcadeactions.dev import sync

    try:
        sync.update_arrange_call(file, lineno, "start_x", str(new_start_x))
    except Exception:
        pass
    try:
        sync.update_arrange_call(file, lineno, "start_y", str(new_start_y))
    except Exception:
        pass

    try:
        rows = int(float(kwargs.get("rows", "0"))) if kwargs.get("rows") else None
        cols = int(float(kwargs.get("cols", "0"))) if kwargs.get("cols") else None
        spacing_x = (
            float(kwargs.get("spacing_x", kwargs.get("spacing", "0")).strip("()"))
            if kwargs.get("spacing_x") or kwargs.get("spacing")
            else None
        )
        spacing_y = (
            float(kwargs.get("spacing_y", kwargs.get("spacing", "0")).strip("()"))
            if kwargs.get("spacing_y") or kwargs.get("spacing")
            else None
        )
        start_x = float(kwargs.get("start_x")) if kwargs.get("start_x") else None
        start_y = float(kwargs.get("start_y")) if kwargs.get("start_y") else None

        if rows and cols and spacing_x and spacing_y and start_x is not None and start_y is not None:
            col = int(round((sprite.center_x - start_x) / spacing_x))
            row = int(round((sprite.center_y - start_y) / spacing_y))
            col = max(0, min(cols - 1, col))
            row = max(0, min(rows - 1, row))

            cell_x = int(round(sprite.center_x))
            cell_y = int(round(sprite.center_y))

            try:
                sync.update_arrange_cell(file, lineno, row, col, cell_x, cell_y)
            except Exception:
                pass
    except Exception:
        pass
