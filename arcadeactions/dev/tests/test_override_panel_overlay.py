import textwrap

import arcade

from arcadeactions.dev import position_tag
from arcadeactions.dev.visualizer import DevVisualizer


def test_overrides_panel_overlay_keystrokes(tmp_path):
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

    # Attach markers
    viz.on_reload([p], saved_state={})

    # Ensure inspector can add override
    ins = viz.get_override_inspector_for_sprite(s)
    assert ins is not None
    res = ins.set_override(0, 1, 160, 105)
    assert res.changed is True

    # Open overrides panel directly
    handled = viz.open_overrides_panel_for_sprite(s)
    assert handled is True
    assert viz.overrides_panel.is_open() is True

    # Move selection to first (index 0) and start inline edit via ENTER
    viz.handle_key_press(arcade.key.DOWN, 0)  # select first
    # Start editing
    viz.handle_key_press(arcade.key.ENTER, 0)
    # Simulate typing '1','7','5',',','1','1','5'
    for ch in list("175,115"):
        viz.overrides_panel.handle_input_char(ch)
    # Commit via ENTER
    viz.handle_key_press(arcade.key.ENTER, 0)

    entries = viz.overrides_panel.list_overrides()
    assert entries and entries[0]["x"] == 175 and entries[0]["y"] == 115

    # Start edit and cancel via ESCAPE
    viz.handle_key_press(arcade.key.ENTER, 0)
    viz.overrides_panel.handle_input_char("9")
    viz.handle_key_press(arcade.key.ESCAPE, 0)
    entries = viz.overrides_panel.list_overrides()
    assert entries and entries[0]["x"] == 175 and entries[0]["y"] == 115

    # Delete via DELETE key
    viz.handle_key_press(arcade.key.DELETE, 0)
    entries = viz.overrides_panel.list_overrides()
    assert entries == []

    # Draw call should not crash
    viz.draw()
