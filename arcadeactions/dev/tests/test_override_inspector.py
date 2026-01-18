import textwrap

import arcade

from arcadeactions.dev import position_tag
from arcadeactions.dev.override_inspector import ArrangeOverrideInspector
from arcadeactions.dev.visualizer import DevVisualizer


def test_list_add_edit_remove_overrides(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    arrange_line = next(i for i, l in enumerate(p.read_text().splitlines(), start=1) if "arrange_grid" in l)
    inspector = ArrangeOverrideInspector(p, arrange_line)

    # Initially no overrides
    assert inspector.list_overrides() == []

    # Add an override
    res = inspector.set_override(0, 1, 160, 105)
    assert res.changed is True
    contents = p.read_text()
    assert "overrides" in contents

    # Edit the same override (should not duplicate)
    res2 = inspector.set_override(0, 1, 170, 110)
    assert res2.changed is True
    contents = p.read_text()
    count = contents.count("{'row'")
    assert count == 1

    # List overrides
    entries = inspector.list_overrides()
    assert len(entries) == 1
    e = entries[0]
    assert e.get("row") == 0 and e.get("col") == 1 and e.get("x") == 170 and e.get("y") == 110

    # Remove override
    rem = inspector.remove_override(0, 1)
    assert rem.changed is True
    contents = p.read_text()
    assert "overrides" not in contents


def test_devvisualizer_open_inspector_and_modify(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)
    """)
    )

    s = arcade.Sprite()
    position_tag.tag_sprite(s, "sprites")
    s.center_x = 160
    s.center_y = 105

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(s)

    # attach markers by simulating reload
    viz.on_reload([p], saved_state={})

    inspector = viz.get_override_inspector_for_sprite(s)
    assert inspector is not None

    res = inspector.set_override(0, 1, 160, 105)
    assert res.changed is True
    contents = p.read_text()
    assert "overrides" in contents

    # Clean up by deleting
    rem = inspector.remove_override(0, 1)
    assert rem.changed is True
    contents = p.read_text()
    assert "overrides" not in contents
