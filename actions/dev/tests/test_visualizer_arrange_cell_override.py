import textwrap

import arcade

from actions.dev import position_tag, sync
from actions.dev.visualizer import DevVisualizer


def test_export_adds_cell_override(monkeypatch, tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    original = arcade.Sprite()
    position_tag.tag_sprite(original, "sprites")

    edited = arcade.Sprite()
    edited.center_x = 175  # this should map to col=2? within bounds (calc)
    edited.center_y = 125
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "sprites")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    viz.on_reload([p], saved_state={})

    # Replace update_arrange_cell with a spy that performs the actual update
    calls = []
    original_updater = sync.update_arrange_cell

    def fake_update_cell(file_path, lineno, row, col, x, y):
        calls.append((str(file_path), lineno, row, col, x, y))
        return original_updater(file_path, lineno, row, col, x, y)

    monkeypatch.setattr(sync, "update_arrange_cell", fake_update_cell)

    viz.export_sprites()

    assert calls, "update_arrange_cell should be called"
    # Verify file contains 'overrides' with a row/col entry
    content = p.read_text()
    assert "overrides" in content
    assert "'row'" in content and "'col'" in content
