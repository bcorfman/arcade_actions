import textwrap

import arcade

from actions.dev import position_tag
from actions.dev.visualizer import DevVisualizer


def test_overrides_panel_open_set_remove(tmp_path):
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

    # Attach markers by simulating reload
    viz.on_reload([p], saved_state={})

    # Open panel
    opened = viz.open_overrides_panel_for_sprite(s)
    assert opened is True
    assert viz.overrides_panel.is_open() is True

    # Set an override via panel
    res = viz.overrides_panel.set_override(0, 1, 160, 105)
    assert res.changed is True
    contents = p.read_text()
    assert "overrides" in contents

    # List via panel
    entries = viz.overrides_panel.list_overrides()
    assert len(entries) == 1
    e = entries[0]
    assert e.get("row") == 0 and e.get("col") == 1

    # Remove via panel
    rem = viz.overrides_panel.remove_override(0, 1)
    assert rem.changed is True
    contents = p.read_text()
    assert "overrides" not in contents

    # Close panel
    viz.overrides_panel.close()
    assert viz.overrides_panel.is_open() is False
