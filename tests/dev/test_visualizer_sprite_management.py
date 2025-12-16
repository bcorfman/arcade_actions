"""Test suite for DevVisualizer sprite import/export and state management.

Tests focus on functionality that works in headless CI environments without
requiring OpenGL context or graphics rendering.
"""

import arcade
import pytest

from actions.dev.visualizer import DevVisualizer
from actions import move_until, infinite
from tests.conftest import ActionTestBase


class TestDevVisualizerImportExport(ActionTestBase):
    """Test suite for sprite import/export functionality."""

    def test_import_sprites_clears_selection_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears selection manager."""
        dev_viz = DevVisualizer()

        # Add sprites and select one
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Select the sprite
        dev_viz.selection_manager.handle_mouse_press(100, 100, False)
        assert len(dev_viz.selection_manager.get_selected()) == 1

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Selection should be cleared
        assert len(dev_viz.selection_manager.get_selected()) == 0
        # Scene should only have new sprite
        assert len(dev_viz.scene_sprites) == 1
        assert dev_viz.scene_sprites[0].center_x == 200

    def test_import_sprites_clears_gizmos_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears gizmo cache."""
        dev_viz = DevVisualizer()

        # Add sprite with bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Create a bounded MoveUntil action
        move_until(sprite1, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Get gizmo (this will cache it)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is not None
        assert sprite1 in dev_viz._gizmos

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Gizmo cache should be cleared
        assert len(dev_viz._gizmos) == 0
        assert len(dev_viz._gizmo_miss_refresh_at) == 0
        # Old sprite should not be in scene
        assert sprite1 not in dev_viz.scene_sprites

    def test_import_sprites_clears_gizmo_miss_cache_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears gizmo miss refresh cache."""
        dev_viz = DevVisualizer()

        # Add sprite without bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Get gizmo (will create negative cache entry)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is None
        assert sprite1 in dev_viz._gizmos
        assert sprite1 in dev_viz._gizmo_miss_refresh_at

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Both caches should be cleared
        assert len(dev_viz._gizmos) == 0
        assert len(dev_viz._gizmo_miss_refresh_at) == 0

    def test_import_sprites_preserves_selection_when_clear_false(self, window):
        """Test that import_sprites with clear=False preserves selection."""
        dev_viz = DevVisualizer()

        # Add sprite and select it
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Select the sprite
        dev_viz.selection_manager.handle_mouse_press(100, 100, False)
        assert len(dev_viz.selection_manager.get_selected()) == 1
        selected_sprite = dev_viz.selection_manager.get_selected()[0]

        # Import new sprites with clear=False
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=False)

        # Selection should still contain original sprite
        assert len(dev_viz.selection_manager.get_selected()) == 1
        assert dev_viz.selection_manager.get_selected()[0] is selected_sprite
        # Scene should have both sprites
        assert len(dev_viz.scene_sprites) == 2

    def test_import_sprites_preserves_gizmos_when_clear_false(self, window):
        """Test that import_sprites with clear=False preserves gizmo cache."""
        dev_viz = DevVisualizer()

        # Add sprite with bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Create a bounded MoveUntil action
        move_until(sprite1, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Get gizmo (this will cache it)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is not None
        assert sprite1 in dev_viz._gizmos

        # Import new sprites with clear=False
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=False)

        # Gizmo cache should still contain original sprite
        assert sprite1 in dev_viz._gizmos
        # Scene should have both sprites
        assert len(dev_viz.scene_sprites) == 2

    def test_import_sprites_clears_scene_before_import(self, window):
        """Test that import_sprites clears scene_sprites when clear=True."""
        dev_viz = DevVisualizer()

        # Add some sprites
        for i in range(3):
            sprite = arcade.Sprite()
            sprite.center_x = i * 100
            dev_viz.scene_sprites.append(sprite)

        assert len(dev_viz.scene_sprites) == 3

        # Import with clear=True
        game_sprites = arcade.SpriteList()
        sprite = arcade.Sprite()
        sprite.center_x = 500
        game_sprites.append(sprite)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Should only have imported sprite
        assert len(dev_viz.scene_sprites) == 1
        assert dev_viz.scene_sprites[0].center_x == 500

    def test_export_sprites_syncs_position(self, window):
        """Test that export_sprites syncs position back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 100
        original.center_y = 200
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.center_x = 300
        imported.center_y = 400

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.center_x == 300
        assert original.center_y == 400

    def test_export_sprites_syncs_angle(self, window):
        """Test that export_sprites syncs angle back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.angle = 0
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.angle = 45

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.angle == 45

    def test_export_sprites_syncs_scale(self, window):
        """Test that export_sprites syncs scale back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.scale = 1.0
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.scale = 2.0

        # Export
        dev_viz.export_sprites()

        # Original should be updated (Arcade 3.x uses tuple scale)
        assert original.scale == (2.0, 2.0) or original.scale == 2.0

    def test_export_sprites_syncs_alpha(self, window):
        """Test that export_sprites syncs alpha back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.alpha = 255
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.alpha = 128

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.alpha == 128

    def test_export_sprites_syncs_color(self, window):
        """Test that export_sprites syncs color back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.color = arcade.color.WHITE
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.color = arcade.color.RED

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.color == arcade.color.RED

    def test_export_sprites_only_syncs_sprites_with_original(self, window):
        """Test that export_sprites only syncs sprites with _original_sprite reference."""
        dev_viz = DevVisualizer()

        # Add sprite without _original_sprite (created directly in scene)
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        dev_viz.scene_sprites.append(sprite1)

        # Add sprite with _original_sprite (imported)
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 200
        game_sprites.append(original)
        dev_viz.import_sprites(game_sprites, clear=False)

        # Modify both
        sprite1.center_x = 300
        dev_viz.scene_sprites[1].center_x = 400

        # Export
        dev_viz.export_sprites()

        # Only imported sprite should sync
        assert original.center_x == 400
        # Direct sprite should be unchanged (no original to sync to)
        assert sprite1.center_x == 300


class TestDevVisualizerGizmoCaching(ActionTestBase):
    """Test suite for gizmo caching behavior."""

    def test_get_gizmo_caches_bounded_action(self, window):
        """Test that _get_gizmo caches gizmo for sprite with bounded action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # Create bounded action
        move_until(sprite, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # First call creates gizmo
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is not None
        assert sprite in dev_viz._gizmos

        # Second call returns cached gizmo
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is gizmo1

    def test_get_gizmo_negative_caches_sprite_without_bounded_action(self, window):
        """Test that _get_gizmo negative-caches sprite without bounded action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # No bounded action - should negative cache
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is None
        assert sprite in dev_viz._gizmos
        assert dev_viz._gizmos[sprite] is None
        assert sprite in dev_viz._gizmo_miss_refresh_at

        # Second call should return None without re-checking (within refresh window)
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is None

    def test_get_gizmo_refreshes_after_miss_cache_expires(self, window):
        """Test that _get_gizmo refreshes negative cache after expiration."""
        import time

        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # First call - negative cache
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is None
        assert sprite in dev_viz._gizmo_miss_refresh_at

        # Manually expire the cache by setting refresh time in the past
        dev_viz._gizmo_miss_refresh_at[sprite] = time.monotonic() - 1.0

        # Now add bounded action
        move_until(sprite, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Should refresh and find the action
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is not None
        assert sprite not in dev_viz._gizmo_miss_refresh_at


class TestDevVisualizerApplyMetadataActions(ActionTestBase):
    """Test suite for apply_metadata_actions functionality."""

    def test_apply_metadata_actions_creates_moveuntil(self, window):
        """Test that apply_metadata_actions creates MoveUntil from metadata."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Add metadata
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (5, 0),
                "condition": "infinite",
            }
        ]

        # Apply metadata
        dev_viz.apply_metadata_actions(sprite)

        # Action should be applied
        from actions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        # MoveUntil uses target_velocity attribute
        assert actions[0].target_velocity == (5, 0)

    def test_apply_metadata_actions_no_metadata(self, window):
        """Test that apply_metadata_actions does nothing if no metadata."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # No metadata - should not crash
        dev_viz.apply_metadata_actions(sprite)

        from actions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0

    def test_apply_metadata_actions_skips_unknown_action_type(self, window):
        """Test that apply_metadata_actions skips unknown action types."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Add unknown action type
        sprite._action_configs = [
            {
                "action_type": "UnknownAction",
                "velocity": (5, 0),
            }
        ]

        # Should not crash
        dev_viz.apply_metadata_actions(sprite)

        from actions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0


