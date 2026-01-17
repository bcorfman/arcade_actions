import textwrap

import arcade

from actions.dev import position_tag
from actions.dev.visualizer import DevVisualizer


def test_export_roundtrip_updates_markers(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        forcefield.left = 100
    """)
    )

    # Original sprite (game) and register with position tag
    original = arcade.Sprite()
    original.center_x = 100
    original.center_y = 200
    position_tag.tag_sprite(original, "forcefield")

    # Edited scene sprite referencing original
    edited = arcade.Sprite()
    edited.center_x = 300
    edited.center_y = 200
    edited._original_sprite = original

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    # Attach same position id to edited sprite so get_sprites_for finds it
    position_tag.tag_sprite(edited, "forcefield")

    # Simulate initial reload so sprite gets markers
    viz.on_reload([p], saved_state={})

    # Export should update file
    viz.export_sprites()

    contents = p.read_text()
    expected = str(int(round(getattr(edited, "left", edited.center_x))))
    assert expected in contents

    # Now simulate reload to update markers (again)
    viz.on_reload([p], saved_state={})

    # The edited sprite should have source markers
    assert hasattr(edited, "_source_markers")
    assert any(str(m["file"]) == str(p) for m in edited._source_markers)
