import textwrap

import arcade

from arcadeactions.dev import position_tag, sync
from arcadeactions.dev.visualizer import DevVisualizer


def test_export_updates_arrange_start(monkeypatch, tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c]
        arrange_grid(sprites, rows=1, cols=3, start_x=100, start_y=200, spacing_x=50, spacing_y=50)
    """)
    )

    # Create sprite and tag with token "sprites" so parser's tokens match
    original = arcade.Sprite()
    position_tag.tag_sprite(original, "sprites")

    edited = arcade.Sprite()
    edited.center_x = 300
    edited.center_y = 400
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "sprites")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    # Run reload so markers are created
    viz.on_reload([p], saved_state={})

    # Ensure we have arrange marker
    markers = getattr(edited, "_source_markers", [])
    assert any(m.get("type") == "arrange" for m in markers)

    calls = []

    original_update = sync.update_arrange_call

    def fake_update_arrange(file_path, lineno, arg_name, new_value_src):
        calls.append((str(file_path), lineno, arg_name, new_value_src))
        return original_update(file_path, lineno, arg_name, new_value_src)

    monkeypatch.setattr(sync, "update_arrange_call", fake_update_arrange)

    viz.export_sprites()

    # Expect at least start_x and start_y updates called
    assert any(c[2] == "start_x" for c in calls)
    assert any(c[2] == "start_y" for c in calls)

    # Verify file updated to the sprite's left/top mapping (rounded integers)
    expected_x = str(int(round(getattr(edited, "left", edited.center_x))))
    expected_y = str(int(round(getattr(edited, "top", edited.center_y))))
    contents = p.read_text()
    assert f"start_x={expected_x}" in contents or f"start_x = {expected_x}" in contents
    assert f"start_y={expected_y}" in contents or f"start_y = {expected_y}" in contents
