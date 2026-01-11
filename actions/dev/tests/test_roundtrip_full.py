import textwrap
from pathlib import Path

import arcade
from actions.dev.visualizer import DevVisualizer
from actions.dev import sync, code_parser, position_tag


def test_export_roundtrip_preserves_comment_and_backup(tmp_path):
    p = tmp_path / "scene.py"
    orig = textwrap.dedent("""
        # Scene header
        forcefield.left = 100  # original comment
        forcefield.top = 200

        other = 1
    """)
    p.write_text(orig)

    # Tag runtime sprite
    original = arcade.Sprite()
    position_tag.tag_sprite(original, "forcefield")

    edited = arcade.Sprite()
    edited.center_x = 220
    edited.center_y = 200
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "forcefield")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    # Initial reload to populate markers
    viz.on_reload([p], saved_state={})

    # Export should update file and create backup
    viz.export_sprites()

    contents = p.read_text()
    # Updated value present (based on left or center mapping)
    expected_left = str(int(round(getattr(edited, "left", edited.center_x))))
    expected_top = str(int(round(getattr(edited, "top", edited.center_y))))
    assert expected_left in contents
    assert expected_top in contents
    # Comment preserved
    assert "# original comment" in contents

    # Stricter checks: ensure spacing and non-numeric parts of the assignment line are preserved
    import re

    def _normalize_digits(s: str) -> str:
        return re.sub(r"\d+", "<NUM>", s)

    orig_line = next(line for line in orig.splitlines() if "forcefield.left" in line)
    new_line = next(line for line in contents.splitlines() if "forcefield.left" in line)
    # Non-numeric structure preserved
    assert _normalize_digits(orig_line) == _normalize_digits(new_line)
    # Comment spacing preserved (two spaces before inline comment)
    assert new_line.rstrip().endswith("  # original comment")

    # Backup exists and is an exact copy of the original source
    bak = p.with_suffix(p.suffix + ".bak")
    assert bak.exists()
    bak_contents = bak.read_text()
    assert bak_contents == orig
    assert "# original comment" in bak_contents


def test_export_roundtrip_arrange_preserves_format_and_adds_override(tmp_path):
    p = tmp_path / "scene.py"
    src = textwrap.dedent("""
        # Grid with comment
        sprites = [a, b, c, d]
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=100, spacing_x=50, spacing_y=50)  # arrange
    """)
    p.write_text(src)

    original = arcade.Sprite()
    position_tag.tag_sprite(original, "sprites")

    edited = arcade.Sprite()
    # Place near second column, first row (col=1, row=0)
    edited.center_x = 150
    edited.center_y = 100
    edited._original_sprite = original
    position_tag.tag_sprite(edited, "sprites")

    viz = DevVisualizer(scene_sprites=arcade.SpriteList())
    viz.scene_sprites.append(edited)

    # Initial reload to populate arrange markers
    viz.on_reload([p], saved_state={})

    # Export should update arrange call and add per-cell override
    viz.export_sprites()

    contents = p.read_text()
    assert "arrange_grid" in contents
    # Check for overrides keyword and a dict entry with 'row' and 'col'
    assert "overrides" in contents
    assert "'row'" in contents and "'col'" in contents
    # Inline comment preserved
    assert "# arrange" in contents

    # Stricter arrange checks: ensure trailing inline comment preserved on the same line
    arrange_old = next(line for line in src.splitlines() if "arrange_grid" in line)
    arrange_new = next(line for line in contents.splitlines() if "arrange_grid" in line or "overrides" in line)
    assert arrange_new.strip().endswith("# arrange")
    # Ensure key kwargs still present
    assert "rows=2" in contents and "cols=2" in contents

    # Backup exists and is an exact copy of original
    bak = p.with_suffix(p.suffix + ".bak")
    assert bak.exists()
    bak_contents = bak.read_text()
    assert bak_contents == src
    assert "# arrange" in bak_contents
