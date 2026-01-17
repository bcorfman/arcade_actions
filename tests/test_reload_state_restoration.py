"""Tests for automatic state restoration after hot-reload.

These tests verify that ReloadManager automatically restores sprite
positions, angles, and scales after a reload, following the project's
design principles of no runtime type checking.
"""

import arcade

from actions import Action
from actions.dev.reload import ReloadManager


class TestStateRestoration:
    """Test automatic state restoration after reload."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_restore_sprite_positions_after_reload(self, tmp_path):
        """Should automatically restore sprite positions after reload."""
        # Create sprites with specific positions
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200
        sprite1.angle = 45
        sprite1.scale = 2.0

        sprite2 = arcade.SpriteSolidColor(32, 32, arcade.color.RED)
        sprite2.center_x = 300
        sprite2.center_y = 400
        sprite2.angle = 90
        sprite2.scale = 1.5

        sprites = [sprite1, sprite2]

        def sprite_provider():
            return sprites

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,  # Enable automatic restoration
            sprite_provider=sprite_provider,
        )

        # Simulate sprites moving (positions change)
        sprite1.center_x = 150
        sprite1.center_y = 250
        sprite1.angle = 90
        sprite2.center_x = 350
        sprite2.center_y = 450

        # Perform reload - should restore positions
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Sprites should be restored to original positions
        assert sprite1.center_x == 100
        assert sprite1.center_y == 200
        assert sprite1.angle == 45
        # Arcade stores scale as tuple (scale_x, scale_y)
        assert sprite1.scale == (2.0, 2.0)
        assert sprite2.center_x == 300
        assert sprite2.center_y == 400
        assert sprite2.angle == 90
        assert sprite2.scale == (1.5, 1.5)

    def test_no_restore_when_auto_restore_disabled(self, tmp_path):
        """Should not restore sprite positions when auto_restore=False."""
        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.center_x = 100
        sprite.center_y = 200

        def sprite_provider():
            return [sprite]

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=False,  # Disable automatic restoration
            sprite_provider=sprite_provider,
        )

        # Change sprite position
        sprite.center_x = 150
        sprite.center_y = 250

        # Perform reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Sprite should NOT be restored (positions stay modified)
        assert sprite.center_x == 150
        assert sprite.center_y == 250

    def test_restore_handles_missing_sprite_gracefully(self, tmp_path):
        """Should handle sprites that no longer exist after reload."""
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200

        sprites = [sprite1]

        def sprite_provider():
            # Return list that might change between calls
            return sprites

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Capture initial state
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Modify sprite
        sprite1.center_x = 150

        # Remove sprite from list (simulating it being deleted)
        sprites.clear()

        # Perform reload - should not crash
        manager._perform_reload([test_file])

        # Should complete without error (sprite not in list = can't restore)
        assert True

    def test_restore_preserves_scale_tuple(self, tmp_path):
        """Should restore non-uniform scale correctly."""
        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.center_x = 100
        sprite.center_y = 200
        sprite.scale = (2.0, 3.0)

        def sprite_provider():
            return [sprite]

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Change sprite scale
        sprite.scale = (1.0, 1.0)

        # Perform reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Scale should be restored
        assert sprite.scale == (2.0, 3.0)

    def test_restore_with_sprite_list(self, tmp_path):
        """Should handle arcade.SpriteList in sprite_provider."""
        sprite_list = arcade.SpriteList()
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200
        sprite_list.append(sprite1)

        sprite2 = arcade.SpriteSolidColor(32, 32, arcade.color.RED)
        sprite2.center_x = 300
        sprite2.center_y = 400
        sprite_list.append(sprite2)

        def sprite_provider():
            return list(sprite_list)  # Convert SpriteList to list

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Modify sprites
        sprite1.center_x = 150
        sprite2.center_x = 350

        # Perform reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Sprites should be restored
        assert sprite1.center_x == 100
        assert sprite2.center_x == 300

    def test_restore_only_affects_preserved_sprites(self, tmp_path):
        """Should only restore sprites that were in the original preservation list."""
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200

        sprite2 = arcade.SpriteSolidColor(32, 32, arcade.color.RED)
        sprite2.center_x = 300
        sprite2.center_y = 400

        # Only preserve sprite1
        def sprite_provider():
            return [sprite1]

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Modify both sprites
        sprite1.center_x = 150
        sprite2.center_x = 350

        # Perform reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Only sprite1 should be restored
        assert sprite1.center_x == 100
        # sprite2 should remain modified (wasn't preserved)
        assert sprite2.center_x == 350

    def test_restore_with_callback_override(self, tmp_path):
        """Should allow on_reload callback to override restoration."""
        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.center_x = 100
        sprite.center_y = 200

        callback_state = []

        def sprite_provider():
            return [sprite]

        def on_reload(files, state):
            # Callback can access preserved state
            callback_state.append(state)
            # And can override restoration by modifying sprite
            sprite.center_x = 999

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
            on_reload=on_reload,
        )

        # Modify sprite
        sprite.center_x = 150

        # Perform reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Callback should have run and overridden the restoration
        assert len(callback_state) > 0
        # Sprite position should be what callback set (999, not 100)
        assert sprite.center_x == 999


class TestErrorHandling:
    """Test error handling follows project rules (no error silencing)."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sprite_provider_returns_empty_list(self, tmp_path):
        """Should handle sprite_provider returning empty list as valid case."""

        def sprite_provider():
            return []

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Perform reload - should not crash
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Should complete successfully
        assert True

    def test_sprite_provider_returns_none(self, tmp_path):
        """Should handle sprite_provider returning None as empty list."""

        def sprite_provider():
            return None

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Perform reload - should handle None gracefully
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Should complete successfully
        assert True

    def test_state_provider_returns_none(self, tmp_path):
        """Should handle state_provider returning None as empty dict."""

        def state_provider():
            return None

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            state_provider=state_provider,
        )

        # Perform reload - should handle None gracefully
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Should complete successfully
        assert True
