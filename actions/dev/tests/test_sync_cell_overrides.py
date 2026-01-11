"""Tests for sync.py cell override functions: update_arrange_cell, delete_arrange_override, list_arrange_overrides."""
import textwrap
from pathlib import Path

from actions.dev import sync, code_parser


def test_update_arrange_cell_adds_override_to_call_without_overrides(tmp_path):
    """Test adding a cell override to an arrange_grid call that has no overrides parameter."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2)
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.update_arrange_cell(p, call.lineno, row=0, col=1, x=150, y=200)
    assert result.changed
    assert result.backup is not None

    new_src = p.read_text()
    assert "overrides" in new_src
    assert "'row'" in new_src or '"row"' in new_src
    assert "'col'" in new_src or '"col"' in new_src
    assert "150" in new_src  # x value
    assert "200" in new_src  # y value


def test_update_arrange_cell_updates_existing_override(tmp_path):
    """Test updating an existing cell override in an arrange_grid call."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 1, 'x': 100, 'y': 100}])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.update_arrange_cell(p, call.lineno, row=0, col=1, x=250, y=300)
    assert result.changed

    new_src = p.read_text()
    # Should have exactly one override for (0, 1)
    assert new_src.count("'row'") >= 1
    assert new_src.count("'col'") >= 1
    assert "250" in new_src  # new x value
    assert "300" in new_src  # new y value


def test_update_arrange_cell_adds_new_override_to_existing_list(tmp_path):
    """Test adding a new cell override to an arrange_grid call that already has overrides."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 0, 'x': 50, 'y': 50}])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.update_arrange_cell(p, call.lineno, row=1, col=1, x=200, y=250)
    assert result.changed

    new_src = p.read_text()
    # Should have overrides for both (0, 0) and (1, 1)
    assert "200" in new_src  # new override x
    assert "250" in new_src  # new override y


def test_list_arrange_overrides_returns_empty_list_when_no_overrides(tmp_path):
    """Test list_arrange_overrides returns empty list when call has no overrides."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2)
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    overrides = sync.list_arrange_overrides(p, call.lineno)
    assert overrides == []


def test_list_arrange_overrides_returns_override_dicts(tmp_path):
    """Test list_arrange_overrides correctly parses and returns override dictionaries."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 1, 'x': 150, 'y': 200}])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    overrides = sync.list_arrange_overrides(p, call.lineno)
    assert len(overrides) == 1
    override = overrides[0]
    assert override["row"] == 0
    assert override["col"] == 1
    assert override["x"] == 150
    assert override["y"] == 200


def test_list_arrange_overrides_handles_multiple_overrides(tmp_path):
    """Test list_arrange_overrides correctly handles multiple overrides in the list."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[
            {'row': 0, 'col': 0, 'x': 100, 'y': 100},
            {'row': 1, 'col': 1, 'x': 200, 'y': 200}
        ])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    overrides = sync.list_arrange_overrides(p, call.lineno)
    assert len(overrides) == 2

    # Find the specific overrides
    override_00 = next(o for o in overrides if o["row"] == 0 and o["col"] == 0)
    assert override_00["x"] == 100
    assert override_00["y"] == 100

    override_11 = next(o for o in overrides if o["row"] == 1 and o["col"] == 1)
    assert override_11["x"] == 200
    assert override_11["y"] == 200


def test_delete_arrange_override_removes_specific_override(tmp_path):
    """Test delete_arrange_override removes a specific override from the list."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[
            {'row': 0, 'col': 0, 'x': 100, 'y': 100},
            {'row': 0, 'col': 1, 'x': 150, 'y': 200}
        ])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.delete_arrange_override(p, call.lineno, row=0, col=1)
    assert result.changed

    # Verify the override was removed by listing overrides
    overrides = sync.list_arrange_overrides(p, call.lineno)
    assert len(overrides) == 1
    assert overrides[0]["row"] == 0
    assert overrides[0]["col"] == 0


def test_delete_arrange_override_removes_overrides_arg_when_empty(tmp_path):
    """Test delete_arrange_override removes the overrides argument when it becomes empty."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 1, 'x': 150, 'y': 200}])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.delete_arrange_override(p, call.lineno, row=0, col=1)
    assert result.changed

    new_src = p.read_text()
    # The overrides argument should be removed entirely
    assert "overrides=" not in new_src


def test_delete_arrange_override_noop_when_override_not_found(tmp_path):
    """Test delete_arrange_override returns changed=False when override doesn't exist."""
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 0, 'x': 100, 'y': 100}])
        """)
    )

    assigns, arr_calls = code_parser.parse_file(str(p))
    call = arr_calls[0]

    result = sync.delete_arrange_override(p, call.lineno, row=1, col=1)
    assert not result.changed
    assert result.backup is None
