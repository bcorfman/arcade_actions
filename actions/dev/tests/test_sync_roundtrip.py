import textwrap
from pathlib import Path

from actions.dev import sync
from actions.dev import code_parser


def test_update_simple_assignment(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        forcefield.left = 100  # original comment
        forcefield.top = 200
    """)
    )

    res = sync.update_position_assignment(p, "forcefield", "left", "220")
    assert res.changed
    assert res.backup is not None

    # Parse file and confirm left value updated
    assigns, _ = code_parser.parse_file(str(p))
    left = [a for a in assigns if a.attr == "left"]
    assert left
    assert "220" in left[0].value_src

    # Ensure comment preserved (libcst preserves formatting)
    new_src = p.read_text()
    assert "# original comment" in new_src


def test_update_noop_returns_changed_false(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        forcefield.top = 200
    """)
    )

    res = sync.update_position_assignment(p, "forcefield", "left", "220")
    assert not res.changed
    assert res.backup is None
