import textwrap

import arcade

from arcadeactions.dev.position_tag import tag_sprite
from arcadeactions.dev.reload import ReloadManager
from arcadeactions.dev.visualizer import enable_dev_visualizer


class DummySprite:
    def __init__(self):
        self.center_x = 0
        self.center_y = 0


def test_reload_triggers_devvisualizer_markers(tmp_path, monkeypatch):
    src = textwrap.dedent(
        """
        forcefield.left = 100
        forcefield.top = 200
        """
    )
    p = tmp_path / "forcefield.py"
    p.write_text(src)

    s = DummySprite()
    tag_sprite(s, "forcefield")

    # Ensure a global DevVisualizer exists
    dev_viz = enable_dev_visualizer(scene_sprites=arcade.SpriteList())

    manager = ReloadManager(watch_paths=[tmp_path], root_path=tmp_path)

    # Monkeypatch _reload_module to avoid importing/reloading the module for real
    monkeypatch.setattr(manager, "_reload_module", lambda file_path, root_path: True)

    # Call perform reload directly (simulates file change)
    manager._perform_reload([p])

    # After reload, tagged sprite should have source markers
    assert hasattr(s, "_source_markers")
    markers = s._source_markers
    assert any(str(m["file"]) == str(p) for m in markers)

    # Now simulate file change removing assignments and expect markers marked red
    p.write_text("# removed assignments\n")
    manager._perform_reload([p])

    # Markers should be present but may be flagged red due to missing matches
    assert hasattr(s, "_source_markers")
    # At least one marker should have status 'red' or be updated in some way
    statuses = {m.get("status") for m in s._source_markers}
    assert "red" in statuses or "yellow" in statuses
