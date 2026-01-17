import textwrap

import arcade

from actions.dev import sync
from actions.dev.visualizer import DevVisualizer


def test_export_calls_sync_for_tagged_sprites(monkeypatch, tmp_path):
    # Create a file with an assignment
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        forcefield.left = 100
    """)
    )

    # Create original sprite and tag
    original = arcade.Sprite()
    original.center_x = 100
    original.center_y = 200

    # Create edited sprite (scene sprite) that references original
    edited = arcade.Sprite()
    edited.center_x = 220
    edited.center_y = 200
    edited._original_sprite = original
    edited._position_id = "forcefield"
    # Simulate parser-provided marker pointing to file and attr
    edited._source_markers = [{"file": str(p), "lineno": 1, "attr": "left", "status": "yellow"}]

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    calls = []

    original_update = sync.update_position_assignment

    def fake_update(file_path, target_name, attr_name, new_value_src):
        calls.append((str(file_path), target_name, attr_name, new_value_src))
        # perform real update to file for integration
        return original_update(file_path, target_name, attr_name, new_value_src)

    monkeypatch.setattr(sync, "update_position_assignment", fake_update)

    viz.export_sprites()

    assert calls, "sync.update_position_assignment should be called"
    file_path, target, attr, val = calls[0]
    assert file_path == str(p)
    assert target == "forcefield"
    assert attr == "left"
    # Ensure new value was used based on edited sprite left mapping
    expected = str(int(round(getattr(edited, "left", edited.center_x))))
    assert expected in val

    # Check file was updated
    contents = p.read_text()
    assert expected in contents
    # Backup exists
    bak = p.with_suffix(p.suffix + ".bak")
    assert bak.exists()
