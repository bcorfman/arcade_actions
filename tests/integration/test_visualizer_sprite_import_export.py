"""Integration tests for DevVisualizer sprite import/export functionality."""

from __future__ import annotations

import arcade
import pytest

from actions.dev.visualizer import DevVisualizer


@pytest.fixture
def dev_visualizer(window):
    """Create a DevVisualizer instance for testing."""
    scene_sprites = arcade.SpriteList()
    dev_viz = DevVisualizer(scene_sprites=scene_sprites, window=window)
    return dev_viz


class TestSpriteImport:
    """Test sprite import functionality."""

    def test_import_sprites_creates_copies(self, dev_visualizer):
        """Verify imported sprites are copies with _original_sprite references."""
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 100
        original.center_y = 200
        original.angle = 45
        original.scale = 2.0
        original.alpha = 128
        original.color = (255, 0, 0)
        game_sprites.append(original)

        dev_visualizer.import_sprites(game_sprites, clear=True)

        assert len(dev_visualizer.scene_sprites) == 1
        imported = dev_visualizer.scene_sprites[0]
        assert imported is not original
        assert hasattr(imported, "_original_sprite")
        assert imported._original_sprite is original

    def test_import_sprites_clear_flag(self, dev_visualizer):
        """Test clear=True vs clear=False behavior."""
        # Add existing sprite
        existing = arcade.Sprite()
        existing.center_x = 50
        dev_visualizer.scene_sprites.append(existing)

        # Import with clear=True
        game_sprites = arcade.SpriteList()
        new_sprite = arcade.Sprite()
        new_sprite.center_x = 100
        game_sprites.append(new_sprite)

        dev_visualizer.import_sprites(game_sprites, clear=True)
        assert len(dev_visualizer.scene_sprites) == 1
        assert dev_visualizer.scene_sprites[0].center_x == 100

        # Add another sprite
        another = arcade.Sprite()
        another.center_x = 200
        dev_visualizer.scene_sprites.append(another)
        assert len(dev_visualizer.scene_sprites) == 2

        # Import with clear=False
        more_sprites = arcade.SpriteList()
        third = arcade.Sprite()
        third.center_x = 300
        more_sprites.append(third)

        dev_visualizer.import_sprites(more_sprites, clear=False)
        assert len(dev_visualizer.scene_sprites) == 3

    def test_import_sprites_preserves_properties(self, dev_visualizer):
        """Verify position, angle, scale, alpha, color are copied."""
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 150
        original.center_y = 250
        original.angle = 90
        original.scale = (1.5, 2.0)  # Tuple scale
        original.alpha = 200
        original.color = (0, 255, 0)
        game_sprites.append(original)

        dev_visualizer.import_sprites(game_sprites, clear=True)

        imported = dev_visualizer.scene_sprites[0]
        assert imported.center_x == 150
        assert imported.center_y == 250
        assert imported.angle == 90
        assert imported.scale == (1.5, 2.0)
        assert imported.alpha == 200
        # Color is returned as Color object, compare RGB values
        assert imported.color.r == 0
        assert imported.color.g == 255
        assert imported.color.b == 0

    def test_import_sprites_handles_float_scale(self, dev_visualizer):
        """Test import handles float scale values."""
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.scale = 2.5  # Float scale
        game_sprites.append(original)

        dev_visualizer.import_sprites(game_sprites, clear=True)

        imported = dev_visualizer.scene_sprites[0]
        assert imported.scale == (2.5, 2.5)

    def test_import_sprites_multiple_lists(self, dev_visualizer):
        """Test importing from multiple sprite lists."""
        list1 = arcade.SpriteList()
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        list1.append(sprite1)

        list2 = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        list2.append(sprite2)

        dev_visualizer.import_sprites(list1, list2, clear=True)

        assert len(dev_visualizer.scene_sprites) == 2
        assert dev_visualizer.scene_sprites[0].center_x == 100
        assert dev_visualizer.scene_sprites[1].center_x == 200


class TestSpriteExport:
    """Test sprite export functionality."""

    def test_export_sprites_syncs_to_originals(self, dev_visualizer):
        """Verify exported changes sync back to original sprites."""
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 100
        original.center_y = 100
        original.angle = 0
        original.scale = 1.0
        original.alpha = 255
        original.color = (255, 255, 255)
        game_sprites.append(original)

        dev_visualizer.import_sprites(game_sprites, clear=True)
        imported = dev_visualizer.scene_sprites[0]

        # Modify imported sprite
        imported.center_x = 200
        imported.center_y = 300
        imported.angle = 45
        imported.scale = 2.0
        imported.alpha = 128
        imported.color = (255, 0, 0)

        # Export
        dev_visualizer.export_sprites()

        # Verify original was updated
        assert original.center_x == 200
        assert original.center_y == 300
        assert original.angle == 45
        # Scale is converted to tuple when set as float
        assert original.scale == (2.0, 2.0)
        assert original.alpha == 128
        # Color is returned as Color object, compare RGB values
        assert original.color.r == 255
        assert original.color.g == 0
        assert original.color.b == 0

    def test_export_sprites_without_original_reference(self, dev_visualizer):
        """Test export handles sprites without _original_sprite gracefully."""
        # Add sprite directly (no import)
        sprite = arcade.Sprite()
        sprite.center_x = 100
        dev_visualizer.scene_sprites.append(sprite)

        # Export should not crash
        dev_visualizer.export_sprites()

        # Sprite should be unchanged (no original to sync to)
        assert sprite.center_x == 100

    def test_export_sprites_with_source_markers(self, dev_visualizer, tmp_path, mocker):
        """Test export with _position_id and _source_markers."""
        # Mock sync module to track calls
        sync_calls = []

        def mock_update_position_assignment(file, pid, attr, value):
            sync_calls.append(("update_position_assignment", file, pid, attr, value))

        mocker.patch("actions.dev.sync.update_position_assignment", side_effect=mock_update_position_assignment)

        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 100
        original.center_y = 200
        game_sprites.append(original)

        dev_visualizer.import_sprites(game_sprites, clear=True)
        imported = dev_visualizer.scene_sprites[0]

        # Add source markers
        test_file = str(tmp_path / "test.py")
        imported._position_id = "test_sprite"
        imported._source_markers = [{"file": test_file, "lineno": 10, "attr": "center_x", "status": "yellow"}]

        # Modify and export
        imported.center_x = 250
        dev_visualizer.export_sprites()

        # Verify sync was called
        assert len(sync_calls) == 1
        assert sync_calls[0][0] == "update_position_assignment"
        assert sync_calls[0][1] == test_file
        assert sync_calls[0][2] == "test_sprite"
        assert sync_calls[0][3] == "center_x"
        assert sync_calls[0][4] == "250"

    def test_export_sprites_handles_errors_gracefully(self, dev_visualizer, mocker):
        """Verify export continues on sync errors."""
        game_sprites = arcade.SpriteList()
        original1 = arcade.Sprite()
        original1.center_x = 100
        game_sprites.append(original1)

        original2 = arcade.Sprite()
        original2.center_x = 200
        game_sprites.append(original2)

        dev_visualizer.import_sprites(game_sprites, clear=True)

        # Make sync fail for first sprite
        call_count = 0

        def mock_update_position_assignment(file, pid, attr, value):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Sync error")

        mocker.patch("actions.dev.sync.update_position_assignment", side_effect=mock_update_position_assignment)

        imported1 = dev_visualizer.scene_sprites[0]
        imported1._position_id = "sprite1"
        imported1._source_markers = [{"file": "test.py", "lineno": 10, "attr": "center_x"}]

        imported1.center_x = 150

        # Export should not crash
        dev_visualizer.export_sprites()

        # Should have attempted sync (error was caught)
        assert call_count == 1
