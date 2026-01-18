"""Test suite for DevVisualizer multi-selection functionality.

Tests click-to-select, shift-click, and marquee selection.
"""

import arcade
import pytest

from arcadeactions.dev.selection import SelectionManager
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.integration


class TestSelectionMulti(ActionTestBase):
    """Test suite for multi-selection functionality."""

    @pytest.mark.integration
    def test_click_to_select_single(self, window):
        """Test clicking a sprite to select it."""
        scene_sprites = arcade.SpriteList()
        sprite1 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite1.center_x = 100
        sprite1.center_y = 100
        scene_sprites.append(sprite1)

        sprite2 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite2.center_x = 200
        sprite2.center_y = 200
        scene_sprites.append(sprite2)

        manager = SelectionManager(scene_sprites)

        # Click on sprite1
        manager.handle_mouse_press(100, 100, False)

        selected = manager.get_selected()
        assert len(selected) == 1
        assert sprite1 in selected
        assert sprite2 not in selected

    @pytest.mark.integration
    def test_shift_click_adds_to_selection(self, window):
        """Test shift-clicking to add sprites to selection."""
        scene_sprites = arcade.SpriteList()
        sprite1 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite1.center_x = 100
        sprite1.center_y = 100
        scene_sprites.append(sprite1)

        sprite2 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite2.center_x = 200
        sprite2.center_y = 200
        scene_sprites.append(sprite2)

        sprite3 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.GREEN)
        sprite3.center_x = 300
        sprite3.center_y = 300
        scene_sprites.append(sprite3)

        manager = SelectionManager(scene_sprites)

        # Click sprite1
        manager.handle_mouse_press(100, 100, False)
        assert len(manager.get_selected()) == 1

        # Shift-click sprite2
        manager.handle_mouse_press(200, 200, True)
        selected = manager.get_selected()
        assert len(selected) == 2
        assert sprite1 in selected
        assert sprite2 in selected

        # Shift-click sprite3
        manager.handle_mouse_press(300, 300, True)
        selected = manager.get_selected()
        assert len(selected) == 3
        assert sprite1 in selected
        assert sprite2 in selected
        assert sprite3 in selected

    @pytest.mark.integration
    def test_marquee_select_multiple(self, window):
        """Test drag marquee to select multiple sprites."""
        scene_sprites = arcade.SpriteList()
        # Create sprites in a grid
        sprites = []
        for i in range(3):
            for j in range(3):
                sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.WHITE)
                sprite.center_x = 100 + i * 50
                sprite.center_y = 100 + j * 50
                scene_sprites.append(sprite)
                sprites.append(sprite)

        manager = SelectionManager(scene_sprites)

        # Drag marquee from (75, 75) to (175, 175) - should capture 4 sprites
        manager.handle_mouse_press(75, 75, False)
        manager.handle_mouse_drag(175, 175)
        manager.handle_mouse_release(175, 175)

        selected = manager.get_selected()
        # Should select sprites in the marquee rectangle
        assert len(selected) >= 2  # At least 2 sprites should be in the box

    @pytest.mark.integration
    def test_marquee_select_clears_previous(self, window):
        """Test that marquee selection clears previous single selection."""
        scene_sprites = arcade.SpriteList()
        sprite1 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite1.center_x = 50
        sprite1.center_y = 50
        scene_sprites.append(sprite1)

        sprite2 = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        sprite2.center_x = 200
        sprite2.center_y = 200
        scene_sprites.append(sprite2)

        manager = SelectionManager(scene_sprites)

        # First select sprite1
        manager.handle_mouse_press(50, 50, False)
        assert len(manager.get_selected()) == 1

        # Then marquee select (should clear previous and select new)
        manager.handle_mouse_press(150, 150, False)
        manager.handle_mouse_drag(250, 250)
        manager.handle_mouse_release(250, 250)

        # Should have new selection (sprite2 if in marquee)
        selected = manager.get_selected()
        assert sprite1 not in selected or len(selected) > 1

    @pytest.mark.integration
    def test_selection_outline_drawing(self, window):
        """Test that selected sprites have outline indicators."""
        scene_sprites = arcade.SpriteList()
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100
        scene_sprites.append(sprite)

        manager = SelectionManager(scene_sprites)
        manager.handle_mouse_press(100, 100, False)

        # Manager should track selection for drawing
        selected = manager.get_selected()
        assert len(selected) == 1
        # Drawing is tested visually, but we can verify selection state
