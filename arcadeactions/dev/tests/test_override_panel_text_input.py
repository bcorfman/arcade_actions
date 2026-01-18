import textwrap

import arcade

from arcadeactions.dev import position_tag
from arcadeactions.dev.visualizer import DevVisualizer


def test_text_input_hits_buffer_and_backspace(tmp_path):
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

    viz.on_reload([p], saved_state={})

    ins = viz.get_override_inspector_for_sprite(s)
    assert ins is not None

    res = ins.set_override(0, 1, 160, 105)
    assert res.changed is True

    # Open panel
    viz.handle_key_press(arcade.key.F8, 0)
    assert viz.overrides_panel.is_open()

    # Start editing x via X key
    viz.handle_key_press(arcade.key.X, 0)
    assert viz.overrides_panel.editing is True

    # Type '12' then BACKSPACE then '3' -> buffer should be '13'
    viz._wrapped_view_on_text = None
    # simulate text input event via DevVisualizer wrapper (calls panel.handle_input_char)
    viz.overrides_panel.handle_input_char("1")
    viz.overrides_panel.handle_input_char("2")
    viz.handle_key_press(arcade.key.BACKSPACE, 0)
    viz.overrides_panel.handle_input_char("3")

    # Commit
    viz.handle_key_press(arcade.key.ENTER, 0)

    entries = viz.overrides_panel.list_overrides()
    assert entries and entries[0]["x"] == 13

    # Now try using on_text wrapper by directly calling the view.on_text
    class DummyView:
        pass

    dv = DummyView()
    dv.on_text = lambda t: None
    dv.on_draw = lambda: None
    viz._wrap_view_on_draw(dv)

    # open again and start edit
    viz.overrides_panel.start_edit("x")
    # call wrapped view on_text
    dv.on_text("9")
    dv.on_text("0")
    viz.handle_key_press(arcade.key.ENTER, 0)
    entries = viz.overrides_panel.list_overrides()
    assert entries and entries[0]["x"] == 90
