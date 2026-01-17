"""Edge case tests for code_parser.py to improve coverage."""

import textwrap

from actions.dev import code_parser


def test_parse_handles_complex_expressions():
    """Test parsing handles complex expressions in assignment values."""
    src = textwrap.dedent("""
        sprite.left = (100 + 50) * 2
        sprite.top = func_call() + 20
        sprite.center_x = obj.method().attr
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    assert len(assignments) == 3

    # Check that complex expressions are captured
    left = next(a for a in assignments if a.attr == "left")
    assert "100" in left.value_src or "50" in left.value_src or "*" in left.value_src

    top = next(a for a in assignments if a.attr == "top")
    assert "func_call" in top.value_src or "20" in top.value_src


def test_parse_handles_attribute_chains():
    """Test parsing handles attribute access chains in target expressions."""
    src = textwrap.dedent("""
        obj.sprite.left = 100
        group.sprites[0].top = 200
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    # Should find assignments with attribute chains
    assert len(assignments) >= 1

    left = next(a for a in assignments if a.attr == "left")
    assert left.target_expr  # Should have target expression


def test_parse_ignores_non_coordinate_attributes():
    """Test parsing ignores attributes that aren't left, top, or center_x."""
    src = textwrap.dedent("""
        sprite.width = 100
        sprite.height = 200
        sprite.angle = 45
        sprite.left = 50
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    # Should only find left, not width, height, or angle
    assert len(assignments) == 1
    assert assignments[0].attr == "left"


def test_parse_arrange_grid_as_method_call():
    """Test parsing detects arrange_grid when called as a method."""
    src = textwrap.dedent("""
        from mylib import LayoutHelper
        
        helper = LayoutHelper()
        helper.arrange_grid(sprites, rows=2, cols=2)
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    # Should detect arrange_grid even when called as a method
    assert len(arr_calls) == 1
    assert "arrange_grid" in arr_calls[0].call_src


def test_parse_arrange_grid_with_positional_args():
    """Test parsing handles arrange_grid calls with positional arguments."""
    src = textwrap.dedent("""
        from mylib import arrange_grid
        
        arrange_grid(sprites, 2, 3, 100, 200)
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    assert len(arr_calls) == 1
    # Should parse successfully even with positional args
    assert arr_calls[0].lineno > 0


def test_parse_handles_nested_calls():
    """Test parsing handles arrange_grid calls nested in other expressions."""
    src = textwrap.dedent("""
        from mylib import arrange_grid
        
        result = arrange_grid(sprites, rows=2, cols=2)
        other_func(arrange_grid(sprites, rows=1, cols=3))
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    # Should find both arrange_grid calls
    assert len(arr_calls) == 2
    assert all("arrange_grid" in call.call_src for call in arr_calls)


def test_parse_handles_multiline_arrange_call():
    """Test parsing handles multi-line arrange_grid calls."""
    src = textwrap.dedent("""
        from mylib import arrange_grid
        
        arrange_grid(
            sprites,
            rows=2,
            cols=2,
            start_x=100,
            start_y=200
        )
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    assert len(arr_calls) == 1
    call = arr_calls[0]
    assert call.kwargs.get("rows") == "2"
    assert call.kwargs.get("cols") == "2"
    assert call.kwargs.get("start_x") == "100"


def test_parse_handles_comments_in_code():
    """Test parsing handles code with comments."""
    src = textwrap.dedent("""
        # Setup sprites
        sprite.left = 100  # Starting position
        sprite.top = 200
        
        # Arrange in grid
        arrange_grid(sprites, rows=2, cols=2)  # Layout
    """)

    assignments, arr_calls = code_parser.parse_source(src, filename="test.py")
    # Should ignore comments and parse correctly
    assert len(assignments) == 2
    assert len(arr_calls) == 1
