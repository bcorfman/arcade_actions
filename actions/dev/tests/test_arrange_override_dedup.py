import textwrap
from pathlib import Path
import re

import arcade
from actions.dev.visualizer import DevVisualizer
from actions.dev import sync, code_parser, position_tag


def _count_override_entries(src: str, row: int, col: int) -> int:
    # Simple regex to find dicts containing 'row' and 'col' with given values
    pattern = re.compile(r"\{[^}]*'row'\s*[:=]\s*%d[^}]*'col'\s*[:=]\s*%d[^}]*\}" % (row, col))
    return len(pattern.findall(src))


def test_overrides_deduplicated_on_multiple_exports(tmp_path, monkeypatch):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    original = arcade.Sprite()
    position_tag.tag_sprite(original, "sprites")

    edited = arcade.Sprite()
    edited.center_x = 150
    edited.center_y = 100
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "sprites")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    # Populate markers then export twice
    viz.on_reload([p], saved_state={})
    viz.export_sprites()
    viz.export_sprites()

    contents = p.read_text()
    # Expect exactly one override for row=0,col=1
    assert _count_override_entries(contents, 0, 1) == 1


def test_overrides_updated_when_cell_moved(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    original = arcade.Sprite()
    position_tag.tag_sprite(original, "sprites")

    edited = arcade.Sprite()
    edited.center_x = 150
    edited.center_y = 100
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "sprites")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    viz.on_reload([p], saved_state={})
    viz.export_sprites()

    # Move the sprite slightly (new x/y)
    edited.center_x = 160
    edited.center_y = 105
    viz.export_sprites()

    contents = p.read_text()
    # There should still be only one override for this row/col
    assert _count_override_entries(contents, 0, 1) == 1
    # And the override coordinates should reflect the updated x/y
    assert "'x'" in contents and "'y'" in contents
    assert "160" in contents or "105" in contents
