"""Tests for formation slot coordinate helper."""

import arcade
import pytest

from arcadeactions.formation import arrange_grid, arrange_line, arrange_triangle, get_slot_coordinates
from tests.conftest import ActionTestBase


class TestSlotHelper(ActionTestBase):
    """Test suite for get_slot_coordinates helper."""

    def test_get_slot_coordinates_line(self):
        """Test getting slot coordinates for line formation."""
        # Test line formation with 5 sprites
        slot_0 = get_slot_coordinates(arrange_line, 0, start_x=100, start_y=200, spacing=50, count=5)
        assert slot_0 == (100, 200)

        slot_2 = get_slot_coordinates(arrange_line, 2, start_x=100, start_y=200, spacing=50, count=5)
        assert slot_2 == (200, 200)

        slot_4 = get_slot_coordinates(arrange_line, 4, start_x=100, start_y=200, spacing=50, count=5)
        assert slot_4 == (300, 200)

    def test_get_slot_coordinates_grid(self):
        """Test getting slot coordinates for grid formation."""
        # Test 2x3 grid (rows=2, cols=3)
        # Index 0: row 0, col 0
        slot_0 = get_slot_coordinates(
            arrange_grid, 0, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40
        )
        assert slot_0 == (100, 300)

        # Index 2: row 0, col 2
        slot_2 = get_slot_coordinates(
            arrange_grid, 2, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40
        )
        assert slot_2 == (200, 300)

        # Index 3: row 1, col 0
        slot_3 = get_slot_coordinates(
            arrange_grid, 3, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40
        )
        assert slot_3 == (100, 340)

        # Index 5: row 1, col 2
        slot_5 = get_slot_coordinates(
            arrange_grid, 5, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40
        )
        assert slot_5 == (200, 340)

    def test_get_slot_coordinates_out_of_bounds(self):
        """Test that out-of-bounds indices raise appropriate errors."""
        with pytest.raises(IndexError):
            get_slot_coordinates(arrange_line, 10, start_x=100, start_y=200, spacing=50, count=5)

    def test_get_slot_coordinates_matches_actual_placement(self):
        """Test that slot coordinates match actual sprite placement."""
        sprites = arcade.SpriteList()
        for _ in range(6):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        # Place in grid
        arrange_grid(sprites, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40)

        # Verify slot coordinates match actual positions
        for i, sprite in enumerate(sprites):
            expected_slot = get_slot_coordinates(
                arrange_grid, i, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40
            )
            assert sprite.center_x == expected_slot[0]
            assert sprite.center_y == expected_slot[1]

    def test_get_slot_coordinates_triangle_matches_actual_placement(self):
        """Test that slot coordinates match actual sprite placement for triangle."""
        sprites = arcade.SpriteList()
        for _ in range(6):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        # Place in triangle (perfect triangular number: 1+2+3 = 6)
        arrange_triangle(sprites, apex_x=400, apex_y=500, row_spacing=50, lateral_spacing=60)

        # Verify slot coordinates match actual positions
        for i, sprite in enumerate(sprites):
            expected_slot = get_slot_coordinates(
                arrange_triangle, i, count=6, apex_x=400, apex_y=500, row_spacing=50, lateral_spacing=60
            )
            assert sprite.center_x == expected_slot[0]
            assert sprite.center_y == expected_slot[1]

    def test_get_slot_coordinates_triangle_incomplete_row(self):
        """Test triangle with incomplete last row (non-triangular count)."""
        # count=4: row 0 (1 sprite), row 1 (2 sprites), row 2 (1 sprite - incomplete)
        sprites = arcade.SpriteList()
        for _ in range(4):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        apex_x = 400
        apex_y = 500
        lateral_spacing = 60

        # Place in triangle
        arrange_triangle(sprites, apex_x=apex_x, apex_y=apex_y, row_spacing=50, lateral_spacing=lateral_spacing)

        # Verify slot coordinates match actual positions
        for i, sprite in enumerate(sprites):
            expected_slot = get_slot_coordinates(
                arrange_triangle,
                i,
                count=4,
                apex_x=apex_x,
                apex_y=apex_y,
                row_spacing=50,
                lateral_spacing=lateral_spacing,
            )
            assert sprite.center_x == expected_slot[0], f"Index {i}: expected {expected_slot[0]}, got {sprite.center_x}"
            assert sprite.center_y == expected_slot[1], f"Index {i}: expected {expected_slot[1]}, got {sprite.center_y}"

        # Specifically test index 3 (incomplete last row with 1 sprite)
        # Should be centered at apex_x, not offset by lateral_spacing
        assert sprites[3].center_x == apex_x, (
            f"Last sprite should be centered at apex_x ({apex_x}), got {sprites[3].center_x}"
        )
