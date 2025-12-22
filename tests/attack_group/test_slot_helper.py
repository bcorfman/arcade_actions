"""Tests for formation slot coordinate helper."""

import pytest
import arcade
from actions.formation import arrange_line, arrange_grid, get_slot_coordinates
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
