"""Tests for arcadeactions.dev.selection module."""

import arcade
import pytest

from arcadeactions.dev import selection


@pytest.fixture
def sprite_list():
    """Create a sprite list with test sprites."""
    sprites = arcade.SpriteList()
    for i in range(5):
        sprite = arcade.SpriteSolidColor(50, 50, arcade.color.RED)
        sprite.center_x = 100 + i * 100
        sprite.center_y = 100 + i * 100
        sprite._prototype_id = f"sprite_{i}"
        sprites.append(sprite)
    return sprites


class TestDrawCenteredRectangleOutline:
    """Test _draw_centered_rectangle_outline function."""

    def test_draw_centered_rectangle_outline(self, mocker):
        """Test that _draw_centered_rectangle_outline calls arcade.draw_lbwh_rectangle_outline."""
        mock_draw = mocker.patch("arcade.draw_lbwh_rectangle_outline")

        selection._draw_centered_rectangle_outline(100, 200, 50, 60, arcade.color.RED, 2)

        mock_draw.assert_called_once()
        call_args = mock_draw.call_args[0]
        assert call_args[0] == 75.0  # left = center_x - width/2
        assert call_args[1] == 170.0  # bottom = center_y - height/2
        assert call_args[2] == 50  # width
        assert call_args[3] == 60  # height
        assert call_args[4] == arcade.color.RED
        assert call_args[5] == 2  # border_width


class TestDrawCenteredRectangleFilled:
    """Test _draw_centered_rectangle_filled function."""

    def test_draw_centered_rectangle_filled(self, mocker):
        """Test that _draw_centered_rectangle_filled calls arcade.draw_lbwh_rectangle_filled."""
        mock_draw = mocker.patch("arcade.draw_lbwh_rectangle_filled")

        selection._draw_centered_rectangle_filled(100, 200, 50, 60, arcade.color.BLUE)

        mock_draw.assert_called_once()
        call_args = mock_draw.call_args[0]
        assert call_args[0] == 75.0  # left
        assert call_args[1] == 170.0  # bottom
        assert call_args[2] == 50  # width
        assert call_args[3] == 60  # height
        assert call_args[4] == arcade.color.BLUE


class TestSelectionManager:
    """Test SelectionManager class."""

    def test_init(self, sprite_list):
        """Test SelectionManager initialization."""
        manager = selection.SelectionManager(sprite_list)

        assert manager.scene_sprites == sprite_list
        assert len(manager.get_selected()) == 0

    def test_handle_mouse_press_selects_sprite(self, sprite_list, mocker):
        """Test handle_mouse_press selects sprite on click."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[sprite_list[0]])

        result = manager.handle_mouse_press(100, 100, shift=False)

        assert result is True
        selected = manager.get_selected()
        assert len(selected) == 1
        assert selected[0] == sprite_list[0]

    def test_handle_mouse_press_shift_click_adds_to_selection(self, sprite_list, mocker):
        """Test handle_mouse_press with shift adds to selection."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", side_effect=[[sprite_list[0]], [sprite_list[1]]])

        # First click selects sprite 0
        manager.handle_mouse_press(100, 100, shift=False)
        # Shift-click selects sprite 1
        manager.handle_mouse_press(200, 200, shift=True)

        selected = manager.get_selected()
        assert len(selected) == 2
        assert sprite_list[0] in selected
        assert sprite_list[1] in selected

    def test_handle_mouse_press_click_already_selected_sprite(self, sprite_list, mocker):
        """Test handle_mouse_press on already selected sprite keeps selection."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[sprite_list[0]])

        # Click once
        manager.handle_mouse_press(100, 100, shift=False)
        # Click same sprite again
        manager.handle_mouse_press(100, 100, shift=False)

        selected = manager.get_selected()
        assert len(selected) == 1
        assert selected[0] == sprite_list[0]

    def test_handle_mouse_press_empty_space_starts_marquee(self, sprite_list, mocker):
        """Test handle_mouse_press on empty space starts marquee."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])

        result = manager.handle_mouse_press(50, 50, shift=False)

        assert result is True
        assert manager._is_dragging_marquee is True
        assert manager._marquee_start == (50, 50)
        assert len(manager.get_selected()) == 0  # Selection cleared

    def test_handle_mouse_press_empty_space_with_shift(self, sprite_list, mocker):
        """Test handle_mouse_press on empty space with shift doesn't start marquee."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])

        result = manager.handle_mouse_press(50, 50, shift=True)

        assert result is False
        assert manager._is_dragging_marquee is False

    def test_handle_mouse_drag_updates_marquee(self, sprite_list, mocker):
        """Test handle_mouse_drag updates marquee end position."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])
        manager.handle_mouse_press(50, 50, shift=False)

        manager.handle_mouse_drag(150, 150)

        assert manager._marquee_end == (150, 150)

    def test_handle_mouse_drag_no_marquee(self, sprite_list):
        """Test handle_mouse_drag when not dragging marquee."""
        manager = selection.SelectionManager(sprite_list)

        manager.handle_mouse_drag(150, 150)

        assert manager._marquee_end is None

    def test_handle_mouse_release_finalizes_marquee(self, sprite_list, mocker):
        """Test handle_mouse_release finalizes marquee selection."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])
        manager.handle_mouse_press(50, 50, shift=False)
        manager.handle_mouse_drag(250, 250)

        # Release at position that should select sprites 0, 1, 2
        manager.handle_mouse_release(250, 250)

        assert manager._is_dragging_marquee is False
        assert manager._marquee_start is None
        assert manager._marquee_end is None
        selected = manager.get_selected()
        assert len(selected) > 0

    def test_handle_mouse_release_marquee_selects_sprites_in_rectangle(self, sprite_list, mocker):
        """Test handle_mouse_release selects sprites within marquee rectangle."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])
        # Start marquee at (0, 0)
        manager.handle_mouse_press(0, 0, shift=False)
        # Drag to (250, 250) - should include sprites 0, 1, 2
        manager.handle_mouse_release(250, 250)

        selected = manager.get_selected()
        # Check that sprites with centers in [0, 250] x [0, 250] are selected
        selected_centers = {(s.center_x, s.center_y) for s in selected}
        assert (100, 100) in selected_centers  # sprite 0
        assert (200, 200) in selected_centers  # sprite 1

    def test_handle_mouse_release_no_marquee(self, sprite_list):
        """Test handle_mouse_release when not dragging marquee."""
        manager = selection.SelectionManager(sprite_list)

        manager.handle_mouse_release(100, 100)

        assert manager._is_dragging_marquee is False

    def test_get_selected(self, sprite_list, mocker):
        """Test get_selected returns list of selected sprites."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[sprite_list[0], sprite_list[1]])

        manager.handle_mouse_press(100, 100, shift=False)
        manager.handle_mouse_press(200, 200, shift=True)

        selected = manager.get_selected()
        assert isinstance(selected, list)
        assert len(selected) == 2

    def test_clear_selection(self, sprite_list, mocker):
        """Test clear_selection removes all selections."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[sprite_list[0]])
        manager.handle_mouse_press(100, 100, shift=False)

        assert len(manager.get_selected()) == 1

        manager.clear_selection()

        assert len(manager.get_selected()) == 0

    def test_draw_selected_outlines(self, sprite_list, mocker):
        """Test draw draws outlines for selected sprites."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[sprite_list[0]])
        manager.handle_mouse_press(100, 100, shift=False)

        mock_draw_outline = mocker.patch("arcadeactions.dev.selection._draw_centered_rectangle_outline")

        manager.draw()

        mock_draw_outline.assert_called_once()
        call_args = mock_draw_outline.call_args[0]
        assert call_args[0] == sprite_list[0].center_x
        assert call_args[1] == sprite_list[0].center_y
        assert call_args[4] == arcade.color.YELLOW

    def test_draw_marquee_rectangle(self, sprite_list, mocker):
        """Test draw draws marquee rectangle when dragging."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", return_value=[])
        manager.handle_mouse_press(50, 50, shift=False)
        manager.handle_mouse_drag(150, 150)

        mock_draw_outline = mocker.patch("arcadeactions.dev.selection._draw_centered_rectangle_outline")
        mock_draw_filled = mocker.patch("arcadeactions.dev.selection._draw_centered_rectangle_filled")

        manager.draw()

        # Should draw both outline and filled rectangle
        assert mock_draw_outline.call_count >= 1
        assert mock_draw_filled.call_count >= 1

    def test_draw_no_marquee_when_not_dragging(self, sprite_list, mocker):
        """Test draw doesn't draw marquee when not dragging."""
        manager = selection.SelectionManager(sprite_list)

        mock_draw_outline = mocker.patch("arcadeactions.dev.selection._draw_centered_rectangle_outline")
        mock_draw_filled = mocker.patch("arcadeactions.dev.selection._draw_centered_rectangle_filled")

        manager.draw()

        # Should not draw marquee (only selected sprites if any)
        # Check that marquee-specific calls weren't made
        marquee_calls = [
            call for call in mock_draw_outline.call_args_list if len(call[0]) > 0 and call[0][4] == arcade.color.CYAN
        ]
        assert len(marquee_calls) == 0

    def test_handle_mouse_press_replaces_selection(self, sprite_list, mocker):
        """Test handle_mouse_press replaces selection on new click."""
        manager = selection.SelectionManager(sprite_list)

        mocker.patch("arcade.get_sprites_at_point", side_effect=[[sprite_list[0]], [sprite_list[1]]])

        # First click
        manager.handle_mouse_press(100, 100, shift=False)
        # Second click without shift
        manager.handle_mouse_press(200, 200, shift=False)

        selected = manager.get_selected()
        assert len(selected) == 1
        assert selected[0] == sprite_list[1]  # Only second sprite selected
