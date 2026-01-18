import textwrap

from arcadeactions.dev import code_parser, sync


def test_update_arrange_call_kwarg(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=1, cols=3, start_x=100, start_y=200)
    """)
    )

    # Parse to find lineno
    assigns, arr = code_parser.parse_file(str(p))
    assert arr
    call = arr[0]
    assert call.kwargs.get("start_x") == "100"

    res = sync.update_arrange_call(p, call.lineno, "start_x", "300")
    assert res.changed
    assert res.backup is not None

    new_src = p.read_text()
    assert "start_x=300" in new_src or "start_x = 300" in new_src


def test_update_arrange_call_add_kwarg(tmp_path):
    p = tmp_path / "scene.py"
    p.write_text(
        textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=1, cols=3)
    """)
    )

    assigns, arr = code_parser.parse_file(str(p))
    call = arr[0]

    res = sync.update_arrange_call(p, call.lineno, "start_y", "400")
    assert res.changed
    assert res.backup is not None

    new_src = p.read_text()
    assert "start_y=400" in new_src or "start_y = 400" in new_src
