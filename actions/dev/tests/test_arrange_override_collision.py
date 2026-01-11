import textwrap
from pathlib import Path
import re

import arcade
from actions.dev.visualizer import DevVisualizer
from actions.dev import position_tag


def _count_override_entries(src: str, row: int, col: int) -> int:
    pattern = re.compile(r"\{[^}]*'row'\s*[:=]\s*%d[^}]*'col'\s*[:=]\s*%d[^}]*\}" % (row, col))
    return len(pattern.findall(src))


def _find_override_coords(src: str, row: int, col: int):
    # Find the first dict for given row/col and extract x and y ints
    pattern = re.compile(r"\{([^}]*)\}")
    for m in pattern.findall(src):
        if f"'row'" in m and f"'col'" in m and f"{row}" in m and f"{col}" in m:
            # find x and y
            x_m = re.search(r"'x'\s*[:=]\s*(\d+)", m)
            y_m = re.search(r"'y'\s*[:=]\s*(\d+)", m)
            x = int(x_m.group(1)) if x_m else None
            y = int(y_m.group(1)) if y_m else None
            return x, y
    return None, None


def test_collision_last_export_wins(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    # Two runtime sprites tag and scene edits map to same cell (col=1,row=0)
    s1 = arcade.Sprite()
    position_tag.tag_sprite(s1, "sprites")
    s1.center_x = 150
    s1.center_y = 100

    s2 = arcade.Sprite()
    position_tag.tag_sprite(s2, "sprites")
    # Slightly different coords but same computed cell
    s2.center_x = 160
    s2.center_y = 105

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    # Append in order s1 then s2 - s2 should win
    viz.scene_sprites.append(s1)
    viz.scene_sprites.append(s2)

    viz.on_reload([p], saved_state={})

    # Ensure arrange markers were attached
    assert hasattr(s1, "_source_markers") and any(m.get("type") == "arrange" for m in s1._source_markers)
    assert hasattr(s2, "_source_markers") and any(m.get("type") == "arrange" for m in s2._source_markers)

    # Inspect attached kwargs and ensure numeric parsing will succeed
    m1 = next(m for m in s1._source_markers if m.get("type") == "arrange")
    kwargs = m1.get("kwargs")
    assert kwargs.get("rows") == "2" or kwargs.get("rows") == "2"
    assert kwargs.get("cols") == "2"
    assert "spacing_x" in kwargs or "spacing" in kwargs
    assert kwargs.get("start_x") == "100"
    assert kwargs.get("start_y") == "100"

    # Replicate parsing logic from visualizer to ensure we can compute row/col
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

    # Ensure the marker lineno matches the file arrange_grid line
    arrange_line = next(i for i, l in enumerate(p.read_text().splitlines(), start=1) if "arrange_grid" in l)
    assert m1.get("lineno") == arrange_line

    assert rows and cols and spacing_x and spacing_y and start_x is not None and start_y is not None

    # Sanity check: call update_arrange_cell directly to verify it works
    from actions.dev import sync

    direct = sync.update_arrange_cell(p, m1.get("lineno"), 0, 1, 160, 105)
    assert direct.changed is True
    contents_direct = p.read_text()
    assert _count_override_entries(contents_direct, 0, 1) == 1

    # Now try export path
    # Ensure sprites are considered 'imported' by setting _original_sprite so export will sync
    s1._original_sprite = s1
    s2._original_sprite = s2
    viz.export_sprites()

    contents = p.read_text()
    assert _count_override_entries(contents, 0, 1) == 1
    x, y = _find_override_coords(contents, 0, 1)
    assert x == 160 and y == 105


def test_collision_first_export_wins_when_order_reversed(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    s1 = arcade.Sprite()
    position_tag.tag_sprite(s1, "sprites")
    s1.center_x = 150
    s1.center_y = 100

    s2 = arcade.Sprite()
    position_tag.tag_sprite(s2, "sprites")
    s2.center_x = 160
    s2.center_y = 105

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    # Append in order s2 then s1 - s1 should win
    viz.scene_sprites.append(s2)
    viz.scene_sprites.append(s1)

    viz.on_reload([p], saved_state={})

    # Ensure arrange markers were attached
    assert hasattr(s1, "_source_markers") and any(m.get("type") == "arrange" for m in s1._source_markers)
    assert hasattr(s2, "_source_markers") and any(m.get("type") == "arrange" for m in s2._source_markers)

    # Ensure sprites are considered 'imported' by setting _original_sprite so export will sync
    s1._original_sprite = s1
    s2._original_sprite = s2

    viz.export_sprites()

    contents = p.read_text()
    assert _count_override_entries(contents, 0, 1) == 1
    x, y = _find_override_coords(contents, 0, 1)
    assert x == 150 and y == 100
