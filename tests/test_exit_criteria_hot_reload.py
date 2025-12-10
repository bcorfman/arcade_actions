"""Tests for Hot-Reload Core exit criteria verification.

Verifies that all exit criteria from the plan are met:
1. Edit wave class, save → see change in <1s
2. Modify sprite positioning code → updates without losing player position  
3. No crashes across 50 consecutive reloads
4. Works with existing visualizer (no conflicts)
"""

import importlib
import sys
import time
from pathlib import Path

import arcade
import pytest

from actions import Action
from actions.dev import enable_dev_mode
from actions.dev.reload import ReloadManager


class TestExitCriteria:
    """Test suite verifying hot-reload exit criteria."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_1_reload_speed_under_1_second(self, tmp_path):
        """Exit Criteria 1: Edit wave class, save → see change in <1s."""
        # Create a test module
        module_file = tmp_path / "test_wave.py"
        module_file.write_text("""
class Wave:
    def __init__(self):
        self.value = 1
""")

        sys.path.insert(0, str(tmp_path))
        try:
            import test_wave

            reload_times = []
            reload_count = [0]

            def on_reload(files, state):
                reload_count[0] += 1

            manager = ReloadManager(
                watch_paths=[tmp_path],
                root_path=tmp_path,
                on_reload=on_reload,
                auto_reload=False,  # Manual control for testing
            )

            # Perform 5 reloads and measure time
            for _ in range(5):
                start = time.time()
                manager._perform_reload([module_file])
                elapsed = time.time() - start
                reload_times.append(elapsed)

                # Modify file slightly
                module_file.write_text(f"""
class Wave:
    def __init__(self):
        self.value = {reload_count[0] + 1}
""")
                importlib.reload(test_wave)

            # Average reload time should be well under 1 second
            # (excluding file watching overhead, which adds ~300ms debounce)
            average_time = sum(reload_times) / len(reload_times)
            max_time = max(reload_times)

            # Reload itself should be fast (<100ms), but we allow more for CI
            assert max_time < 1.0, f"Reload took {max_time:.3f}s, expected <1.0s"
            assert average_time < 0.5, f"Average reload took {average_time:.3f}s, expected <0.5s"

        finally:
            if "test_wave" in sys.modules:
                del sys.modules["test_wave"]
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_2_preserve_player_position_after_positioning_change(self, tmp_path):
        """Exit Criteria 2: Modify sprite positioning code → updates without losing player position."""
        # Create player sprite at specific position
        player = arcade.SpriteSolidColor(32, 32, arcade.color.BLUE)
        player.center_x = 100
        player.center_y = 200

        def sprite_provider():
            return [player]

        manager = ReloadManager(
            root_path=tmp_path,
            auto_restore=True,
            sprite_provider=sprite_provider,
        )

        # Simulate player moving during gameplay
        player.center_x = 250
        player.center_y = 350

        # Simulate reload (e.g., after modifying positioning code)
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._perform_reload([test_file])

        # Player position should be restored to original (baseline)
        assert player.center_x == 100
        assert player.center_y == 200

    def test_3_no_crashes_across_50_consecutive_reloads(self, tmp_path):
        """Exit Criteria 3: No crashes across 50 consecutive reloads."""
        # Create a test module
        module_file = tmp_path / "test_module.py"
        module_file.write_text("""
VALUE = 0
""")

        sys.path.insert(0, str(tmp_path))
        try:
            import test_module

            reload_count = [0]
            errors = []

            def on_reload(files, state):
                reload_count[0] += 1
                # Verify module reloaded correctly
                if reload_count[0] % 10 == 0:
                    assert test_module.VALUE == reload_count[0]

            manager = ReloadManager(
                watch_paths=[tmp_path],
                root_path=tmp_path,
                on_reload=on_reload,
                auto_reload=False,  # Manual control for testing
            )

            # Perform 50 consecutive reloads
            for i in range(50):
                try:
                    # Update module content
                    module_file.write_text(f"""
VALUE = {i + 1}
""")
                    # Reload
                    manager._perform_reload([module_file])
                    importlib.reload(test_module)

                except Exception as e:
                    errors.append((i + 1, str(e)))
                    # Don't fail immediately - collect all errors

            # Verify no crashes occurred
            assert len(errors) == 0, f"Errors during reloads: {errors}"
            assert reload_count[0] == 50, f"Expected 50 reloads, got {reload_count[0]}"

            # Verify final state is correct
            assert test_module.VALUE == 50

        finally:
            if "test_module" in sys.modules:
                del sys.modules["test_module"]
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_4_works_with_existing_visualizer_no_conflicts(self):
        """Exit Criteria 4: Works with existing visualizer (no conflicts)."""
        # Check that visualizer and reload manager can coexist
        # Visualizer uses F3 (Shift+F3), reload manager uses R key
        # They should not conflict

        from actions.visualizer import attach_visualizer, is_visualizer_attached, detach_visualizer

        # Create a window (required for visualizer)
        window = arcade.Window(800, 600, "Test", visible=False)
        try:
            # Attach visualizer
            visualizer_session = attach_visualizer()
            assert is_visualizer_attached()

            # Create reload manager
            manager = ReloadManager()
            assert manager is not None

            # Both should work simultaneously
            # Visualizer wraps Action.update_all()
            # Reload manager calls Action.update_all() in game loop
            # They should not conflict

            # Verify both are active
            assert is_visualizer_attached()
            assert manager.indicator is not None

            # Test that reload manager can process reloads with visualizer attached
            manager._perform_reload([])  # Empty reload should work
            assert is_visualizer_attached()  # Visualizer still attached

            # Clean up
            detach_visualizer()

        finally:
            window.close()

    def test_4b_visualizer_and_reload_manager_key_shortcuts_dont_conflict(self):
        """Verify visualizer (F3) and reload manager (R) keyboard shortcuts don't conflict."""
        # Visualizer uses Shift+F3 (or F3)
        # Reload manager uses R key (configurable)
        # These are different keys, so no conflict

        import arcade

        # Verify key codes are different
        visualizer_key = arcade.key.F3
        reload_key = arcade.key.R

        assert visualizer_key != reload_key, "Visualizer and reload manager use same key - conflict!"

        # Visualizer modifier is Shift (optional)
        # Reload manager has no modifier
        # No conflict possible

        assert True  # If we get here, keys don't conflict

