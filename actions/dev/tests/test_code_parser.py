import textwrap

import pytest

from actions.dev import code_parser


def test_parse_direct_assignments():
    src = textwrap.dedent(
        """
        sprite.left = 100
        sprite.top = 200
        enemy.center_x = player.x + 10
        other = 5
        """
    )

    assignments, arr_calls = code_parser.parse_source(src, filename="testfile.py")
    assert len(assignments) == 3
    attrs = {(a.target_expr.strip(), a.attr): a for a in assignments}

    assert ("sprite", "left") in attrs or any(a.attr == "left" for a in assignments)
    # Confirm values were captured
    left = next(a for a in assignments if a.attr == "left")
    assert "100" in left.value_src

    top = next(a for a in assignments if a.attr == "top")
    assert "200" in top.value_src

    center = next(a for a in assignments if a.attr == "center_x")
    assert "player.x" in center.value_src

    # No arrange calls here
    assert len(arr_calls) == 0


def test_parse_arrange_grid_detected(tmp_path):
    src = textwrap.dedent(
        """
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=1, cols=3, spacing=(100, 120))
        """
    )

    p = tmp_path / "scene.py"
    p.write_text(src)

    assignments, arr_calls = code_parser.parse_file(str(p))
    assert len(arr_calls) == 1
    call = arr_calls[0]
    assert "arrange_grid" in call.call_src
    # The source includes a leading blank line, so arrange_grid appears on line 5
    assert call.lineno == 5
    # Keyword args should be parsed
    assert call.kwargs.get("rows") == "1"
    assert "spacing" in call.kwargs


if __name__ == "__main__":
    pytest.main([__file__])
