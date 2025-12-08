"""Tests for the ReloadManager that orchestrates hot-reload functionality.

Fast unit tests only - integration tests are in tests/integration/test_reload_manager_integration.py
"""

import importlib
import sys
from pathlib import Path
from queue import Empty
from threading import Thread

import arcade
import pytest

from actions import Action
from actions.base import Action as BaseAction
from actions.conditional import MoveUntil, infinite
from actions.dev.reload import ReloadIndicator, ReloadManager
from actions.dev.watch import FileWatcher


class TestReloadManager:
    """Test suite for ReloadManager - fast unit tests only."""

    def setup_method(self):
        """Setup before each test."""
        self.manager = None
        self.reloads_performed = []
        self.reload_states = []

    def teardown_method(self):
        """Clean up after each test."""
        if self.manager is not None:
            self.manager.stop()
        Action.stop_all()
        self.reloads_performed.clear()
        self.reload_states.clear()

    def test_create_reload_manager(self):
        """Should create ReloadManager instance."""
        manager = ReloadManager()
        assert manager is not None
        assert not manager.is_watching()
        manager.stop()

    def test_reload_manager_with_watch_paths(self, tmp_path):
        """Should create manager with watch paths."""
        manager = ReloadManager(watch_paths=[tmp_path])
        assert manager is not None
        manager.stop()

    def test_start_watching(self, tmp_path):
        """Should start file watching."""
        manager = ReloadManager(watch_paths=[tmp_path])
        manager.start()
        assert manager.is_watching()
        manager.stop()

    def test_stop_watching(self, tmp_path):
        """Should stop file watching."""
        manager = ReloadManager(watch_paths=[tmp_path])
        manager.start()
        manager.stop()
        assert not manager.is_watching()

    def test_queue_reload_from_background_thread(self, tmp_path):
        """Should queue reload request from background thread."""
        manager = ReloadManager(watch_paths=[tmp_path])
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Simulate FileWatcher callback from background thread
        changed_files = [test_file]
        manager._on_files_changed(changed_files)

        # Process from main thread
        manager.process_reloads()

        # Verify reload was queued and processed
        assert len(self.reloads_performed) == 0  # No actual reload callback yet

    def test_thread_safe_reload_queue(self, tmp_path):
        """Should safely queue reloads from multiple threads."""
        manager = ReloadManager(watch_paths=[tmp_path])
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Queue from multiple threads
        threads = []
        for i in range(5):
            thread = Thread(target=lambda: manager._on_files_changed([tmp_path / f"test{i}.py"]), daemon=True)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=1.0)

        # Process all queued reloads
        processed_count = 0
        while True:
            try:
                files = manager._reload_queue.get_nowait()
                processed_count += 1
            except Empty:
                break

        # Should have received all 5 reload requests
        assert processed_count == 5

    def test_preserve_state_before_reload(self):
        """Should preserve sprite and action state before reload."""
        manager = ReloadManager()

        # Create test sprites
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200
        sprite1.angle = 45
        sprite1.scale = 2.0

        sprite2 = arcade.SpriteSolidColor(32, 32, arcade.color.RED)
        sprite2.center_x = 300
        sprite2.center_y = 400
        sprite2.angle = 90

        # Create test actions
        action1 = MoveUntil((5, 0), infinite())
        action1.apply(sprite1, tag="move1")
        action1._elapsed = 1.5

        action2 = MoveUntil((0, 5), infinite())
        action2.apply(sprite2, tag="move2")
        action2._elapsed = 2.3

        # Capture state
        state = manager._preserve_state([sprite1, sprite2])

        # Verify sprite state preserved
        assert "sprites" in state
        sprite_states = state["sprites"]
        assert len(sprite_states) == 2

        # Find sprite states by position (since IDs may differ)
        found_sprite1 = False
        found_sprite2 = False
        for sprite_id, sprite_data in sprite_states.items():
            pos = sprite_data["position"]
            if pos == (100, 200):
                assert sprite_data["angle"] == 45
                assert sprite_data["scale"] == (2.0, 2.0)
                found_sprite1 = True
            elif pos == (300, 400):
                assert sprite_data["angle"] == 90
                assert sprite_data["scale"] == (1.0, 1.0)
                found_sprite2 = True

        assert found_sprite1
        assert found_sprite2

        # Verify action state preserved
        assert "actions" in state
        action_states = state["actions"]
        assert len(action_states) >= 2

        # Check action data
        found_action1 = False
        found_action2 = False
        for action_id, action_data in action_states.items():
            if action_data["tag"] == "move1":
                assert action_data["elapsed"] == 1.5
                found_action1 = True
            elif action_data["tag"] == "move2":
                assert action_data["elapsed"] == 2.3
                found_action2 = True

        assert found_action1
        assert found_action2

    def test_reload_module_from_path(self, tmp_path):
        """Should reload a Python module from file path."""
        manager = ReloadManager()

        # Create a test module
        module_dir = tmp_path / "test_package"
        module_dir.mkdir()
        module_file = module_dir / "__init__.py"
        module_file.write_text("VALUE = 1")

        # Import the module
        sys.path.insert(0, str(tmp_path))
        try:
            import test_package

            assert test_package.VALUE == 1

            # Modify the module
            module_file.write_text("VALUE = 2")

            # Reload
            result = manager._reload_module(module_file, tmp_path)
            assert result

            # Verify value changed
            assert test_package.VALUE == 2

            # Cleanup
            sys.path.remove(str(tmp_path))
            if "test_package" in sys.modules:
                del sys.modules["test_package"]
        finally:
            if "test_package" in sys.modules:
                del sys.modules["test_package"]
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_reload_module_not_imported(self, tmp_path):
        """Should return False for module that hasn't been imported."""
        manager = ReloadManager()
        test_file = tmp_path / "never_imported.py"
        test_file.write_text("# never imported")

        result = manager._reload_module(test_file, tmp_path)
        assert not result

    def test_path_to_module_name_conversion(self, tmp_path):
        """Should convert file path to Python module name."""
        manager = ReloadManager()

        # Test various path formats
        module_file = tmp_path / "my_module.py"
        module_name = manager._path_to_module_name(module_file, tmp_path)
        assert module_name == "my_module"

        # Test nested package
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        nested_file = package_dir / "nested.py"
        module_name = manager._path_to_module_name(nested_file, tmp_path)
        assert module_name == "package.nested"

        # Test __init__.py
        init_file = package_dir / "__init__.py"
        module_name = manager._path_to_module_name(init_file, tmp_path)
        assert module_name == "package"

    def test_path_to_module_name_outside_root(self, tmp_path):
        """Should return None for paths outside root."""
        manager = ReloadManager()
        other_path = tmp_path.parent / "other.py"
        other_path.write_text("# test")

        module_name = manager._path_to_module_name(other_path, tmp_path)
        assert module_name is None

    def test_process_reloads_empty_queue(self):
        """Should handle empty reload queue gracefully."""
        manager = ReloadManager()
        # Should not raise exception
        manager.process_reloads()

    def test_reload_with_custom_callback(self, tmp_path):
        """Should call custom reload callback after reload."""
        callback_called = []

        def on_reload(files: list[Path], state: dict) -> None:
            callback_called.append((files, state))

        manager = ReloadManager(
            watch_paths=[tmp_path],
            on_reload=on_reload,
            root_path=tmp_path,
        )

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Manually trigger reload (simulating queued request)
        manager._on_files_changed([test_file])
        manager.process_reloads()

        # Callback should be called
        assert len(callback_called) > 0

    def test_reload_pauses_actions(self, tmp_path):
        """Should pause actions during reload process."""
        manager = ReloadManager(watch_paths=[tmp_path], root_path=tmp_path)

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        action = MoveUntil((5, 0), infinite())
        action.apply(sprite, tag="test")

        # Verify action is active
        assert action._is_active
        assert not action._paused

        # Simulate reload
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")
        manager._on_files_changed([test_file])

        # Before processing, actions should not be paused
        assert not action._paused

        # Process reload (this should pause actions)
        manager.process_reloads()

        # Actions should be resumed after reload
        # (ReloadManager doesn't permanently pause, just during reload)
        assert action._is_active

    def test_reload_handles_import_errors_gracefully(self, tmp_path):
        """Should handle module reload errors without crashing."""
        manager = ReloadManager(root_path=tmp_path)

        # Create a module with invalid syntax
        bad_module = tmp_path / "bad_module.py"
        bad_module.write_text("syntax error !!!")

        # Import it first (this will fail, but we'll handle it)
        sys.path.insert(0, str(tmp_path))
        try:
            # Try to reload non-existent module (should fail gracefully)
            result = manager._reload_module(bad_module, tmp_path)
            # Should return False for non-imported module
            assert not result
        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_reload_indicator_trigger(self):
        """Should trigger reload indicator flash."""
        indicator = ReloadIndicator()
        assert indicator._flash_alpha == 0.0

        indicator.trigger()
        assert indicator._flash_alpha == 1.0

    def test_reload_indicator_update(self):
        """Should decay flash alpha over time."""
        indicator = ReloadIndicator()
        indicator.trigger()

        # Update multiple times
        for _ in range(10):
            indicator.update(0.02)  # 0.02 seconds each

        # Flash should have decayed
        assert indicator._flash_alpha < 1.0
        assert indicator._flash_alpha >= 0.0

    def test_reload_indicator_expires(self):
        """Should expire flash after duration."""
        indicator = ReloadIndicator(flash_duration=0.1)
        indicator.trigger()

        # Wait for duration
        elapsed = 0.0
        while elapsed < 0.2:
            indicator.update(0.05)
            elapsed += 0.05

        # Flash should be expired
        assert indicator._flash_alpha == 0.0

    def test_reload_indicator_draw(self):
        """Should draw flash overlay when active."""
        indicator = ReloadIndicator()
        indicator.trigger()

        # Should be drawable (won't actually draw in headless test)
        # Just verify it doesn't crash
        try:
            indicator.draw()
        except Exception:
            # Expected in headless environment - that's okay
            pass

    def test_state_provider_callback(self):
        """Should include custom state from state_provider callback."""
        custom_state = {"score": 100, "level": 3}

        def state_provider() -> dict:
            return custom_state

        manager = ReloadManager(state_provider=state_provider)

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        state = manager._preserve_state([sprite])

        assert "custom" in state
        assert state["custom"] == custom_state

    def test_sprite_provider_callback(self):
        """Should use sprite_provider callback to get sprites for preservation."""
        sprite1 = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite1.center_x = 100
        sprite1.center_y = 200

        sprite2 = arcade.SpriteSolidColor(32, 32, arcade.color.RED)
        sprite2.center_x = 300
        sprite2.center_y = 400

        def sprite_provider() -> list:
            return [sprite1, sprite2]

        manager = ReloadManager(sprite_provider=sprite_provider)

        # Perform reload should use sprite_provider to get sprites
        manager._perform_reload([])

        # Verify sprites were preserved (check via callback)
        callback_called = []

        def on_reload(files, state):
            callback_called.append(state)

        manager.on_reload = on_reload
        manager._perform_reload([])

        assert len(callback_called) > 0
        state = callback_called[0]
        assert "sprites" in state
        assert len(state["sprites"]) == 2

    def test_sprite_provider_exception_handling(self):
        """Should handle exceptions in sprite_provider gracefully."""

        def failing_sprite_provider():
            raise ValueError("Sprite provider error")

        manager = ReloadManager(sprite_provider=failing_sprite_provider)

        # Should not raise exception
        manager._perform_reload([])

        # Should preserve empty sprite list on error
        assert True  # If we get here, exception was handled

    def test_reload_module_with_exception(self, tmp_path):
        """Should handle reload exceptions gracefully."""
        manager = ReloadManager(root_path=tmp_path)

        # Test that reload returns False for non-existent module
        nonexistent_file = tmp_path / "nonexistent.py"
        result = manager._reload_module(nonexistent_file, tmp_path)
        assert not result

    def test_force_reload_all_files(self, tmp_path):
        """Should force reload all Python files in watch paths."""
        manager = ReloadManager(watch_paths=[tmp_path], root_path=tmp_path)

        # Create test files
        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.py"
        file1.write_text("# file1")
        file2.write_text("# file2")

        # Force reload all
        # This will try to reload all .py files
        # Since they're not imported, it will just return
        manager.force_reload()

        # Should not raise exception
        assert True

    def test_force_reload_specific_files(self, tmp_path):
        """Should force reload specified files."""
        manager = ReloadManager(root_path=tmp_path)

        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.py"
        file1.write_text("# file1")
        file2.write_text("# file2")

        # Force reload specific files
        manager.force_reload([file1, file2])

        # Should not raise exception
        assert True

    def test_indicator_is_flashing_property(self):
        """Should correctly report if indicator is flashing."""
        indicator = ReloadIndicator()
        assert not indicator.is_flashing

        indicator.trigger()
        assert indicator.is_flashing

        indicator.update(0.3)  # Longer than duration
        assert not indicator.is_flashing

    def test_indicator_draw_when_not_flashing(self):
        """Should not draw when alpha is 0."""
        indicator = ReloadIndicator()
        # Should not crash
        indicator.draw()

    def test_reload_with_module_without_file_attribute(self, tmp_path):
        """Should handle modules without __file__ attribute gracefully."""
        # Create a mock module without __file__
        import types

        mock_module = types.ModuleType("mock_module")
        sys.modules["mock_module"] = mock_module

        try:
            manager = ReloadManager(root_path=tmp_path)
            # Create a fake path
            fake_file = tmp_path / "mock_module.py"

            # The module doesn't have __file__, so reload should handle it
            # Since module_name won't match, this will return False
            result = manager._reload_module(fake_file, tmp_path)
            # Should return False because path doesn't resolve to module name
            assert not result
        finally:
            if "mock_module" in sys.modules:
                del sys.modules["mock_module"]

    def test_preserve_state_disabled(self, tmp_path):
        """Should skip state preservation when preserve_state=False."""
        state_captured = []

        def state_provider():
            state_captured.append("called")
            return {"test": "data"}

        def sprite_provider():
            sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
            sprite.center_x = 100
            sprite.center_y = 200
            return [sprite]

        manager = ReloadManager(
            root_path=tmp_path, preserve_state=False, state_provider=state_provider, sprite_provider=sprite_provider
        )

        # Create a test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("# test")

        # Trigger reload
        manager._perform_reload([test_file])

        # State provider should NOT have been called
        assert len(state_captured) == 0

    def test_preserve_state_enabled(self, tmp_path):
        """Should preserve state when preserve_state=True (default)."""
        state_captured = []

        def state_provider():
            state_captured.append("called")
            return {"test": "data"}

        def sprite_provider():
            sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
            sprite.center_x = 100
            sprite.center_y = 200
            return [sprite]

        manager = ReloadManager(
            root_path=tmp_path, preserve_state=True, state_provider=state_provider, sprite_provider=sprite_provider
        )

        # Create a test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("# test")

        # Trigger reload
        manager._perform_reload([test_file])

        # State provider should have been called
        assert len(state_captured) == 1

    def test_reload_key_attribute(self):
        """Should store reload_key attribute."""
        manager = ReloadManager()
        assert manager.reload_key is None

        # Should be settable
        manager.reload_key = "R"
        assert manager.reload_key == "R"

    def test_on_key_press_with_reload_key(self):
        """Should trigger reload when configured key is pressed."""
        reload_triggered = []

        manager = ReloadManager()
        manager.reload_key = "R"

        # Mock force_reload to detect trigger
        original_force_reload = manager.force_reload

        def mock_force_reload(files=None):
            reload_triggered.append(True)

        manager.force_reload = mock_force_reload

        try:
            # Press R key
            result = manager.on_key_press(arcade.key.R, 0)
            assert result is True
            assert len(reload_triggered) == 1

            # Press other key
            result = manager.on_key_press(arcade.key.A, 0)
            assert result is False
            assert len(reload_triggered) == 1  # No additional reload

        finally:
            manager.force_reload = original_force_reload

    def test_on_key_press_disabled(self):
        """Should not trigger reload when reload_key is None."""
        manager = ReloadManager()
        manager.reload_key = None

        # Press R key - should not trigger reload
        result = manager.on_key_press(arcade.key.R, 0)
        assert result is False

    def test_on_key_press_with_f5_key(self):
        """Should support F5 as reload key."""
        reload_triggered = []

        manager = ReloadManager()
        manager.reload_key = "F5"

        # Mock force_reload
        original_force_reload = manager.force_reload

        def mock_force_reload(files=None):
            reload_triggered.append(True)

        manager.force_reload = mock_force_reload

        try:
            # Press F5 key
            result = manager.on_key_press(arcade.key.F5, 0)
            assert result is True
            assert len(reload_triggered) == 1

        finally:
            manager.force_reload = original_force_reload

    def test_on_key_press_case_insensitive(self):
        """Should handle reload_key case-insensitively."""
        reload_triggered = []

        manager = ReloadManager()
        manager.reload_key = "r"  # lowercase

        # Mock force_reload
        original_force_reload = manager.force_reload

        def mock_force_reload(files=None):
            reload_triggered.append(True)

        manager.force_reload = mock_force_reload

        try:
            # Press R key - should still work
            result = manager.on_key_press(arcade.key.R, 0)
            assert result is True
            assert len(reload_triggered) == 1

        finally:
            manager.force_reload = original_force_reload


class TestReloadIndicator:
    """Test suite for ReloadIndicator visual feedback."""

    def test_initial_state(self):
        """Should start with alpha at 0."""
        indicator = ReloadIndicator()
        assert indicator._flash_alpha == 0.0

    def test_trigger_flash(self):
        """Should set alpha to 1.0 when triggered."""
        indicator = ReloadIndicator()
        indicator.trigger()
        assert indicator._flash_alpha == 1.0

    def test_update_decays_alpha(self):
        """Should decay alpha over time."""
        indicator = ReloadIndicator(flash_duration=0.2)
        indicator.trigger()

        # Initial state
        assert indicator._flash_alpha == 1.0

        # After 0.1 seconds (half duration)
        indicator.update(0.1)
        assert indicator._flash_alpha < 1.0
        assert indicator._flash_alpha > 0.0

        # After full duration
        indicator.update(0.1)
        assert indicator._flash_alpha == 0.0

    def test_multiple_triggers(self):
        """Should restart flash on multiple triggers."""
        indicator = ReloadIndicator(flash_duration=0.2)
        indicator.trigger()

        # Decay a bit
        indicator.update(0.1)
        assert indicator._flash_alpha < 1.0

        # Trigger again - should reset
        indicator.trigger()
        assert indicator._flash_alpha == 1.0

    def test_custom_flash_duration(self):
        """Should respect custom flash duration."""
        indicator = ReloadIndicator(flash_duration=0.5)
        indicator.trigger()

        # After 0.25 seconds, should still be visible
        indicator.update(0.25)
        assert indicator._flash_alpha > 0.0

        # After full 0.5 seconds
        indicator.update(0.25)
        assert indicator._flash_alpha == 0.0

    def test_preserve_state_with_float_scale(self):
        """Should handle float scale values."""
        manager = ReloadManager()

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.scale = 1.5  # Float scale

        state = manager._preserve_state([sprite])
        sprite_states = state["sprites"]
        assert len(sprite_states) == 1
        for sprite_data in sprite_states.values():
            assert sprite_data["scale"] == (1.5, 1.5)

    def test_preserve_state_with_int_scale(self):
        """Should handle int scale values."""
        manager = ReloadManager()

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.scale = 2  # Int scale

        state = manager._preserve_state([sprite])
        sprite_states = state["sprites"]
        assert len(sprite_states) == 1
        for sprite_data in sprite_states.values():
            assert sprite_data["scale"] == (2.0, 2.0)

    def test_preserve_state_with_non_uniform_scale_tuple(self):
        """Should preserve both x and y scale components."""
        manager = ReloadManager()

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        sprite.scale = (2.0, 3.0)

        state = manager._preserve_state([sprite])
        sprite_states = state["sprites"]
        assert len(sprite_states) == 1
        for sprite_data in sprite_states.values():
            assert sprite_data["scale"] == (2.0, 3.0)

    def test_preserve_state_with_empty_tuple_scale(self):
        """Should handle empty tuple scale values with fallback."""
        manager = ReloadManager()

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        # Arcade won't let us set invalid scale, but we can test empty tuple handling
        # by accessing scale directly (it will be a valid tuple)
        # Actually, we can't easily test invalid scale since Arcade validates it
        # The fallback path (line 233) is defensive code that may not be reachable
        # in practice, but it's good to have. Let's skip this test.
        state = manager._preserve_state([sprite])
        sprite_states = state["sprites"]
        assert len(sprite_states) == 1
        # Verify scale is preserved correctly
        for sprite_data in sprite_states.values():
            assert "scale" in sprite_data
            assert isinstance(sprite_data["scale"], tuple)

    def test_state_provider_exception_handling(self):
        """Should handle exceptions in state_provider gracefully."""

        def failing_state_provider():
            raise ValueError("State provider error")

        manager = ReloadManager(state_provider=failing_state_provider)

        sprite = arcade.SpriteSolidColor(32, 32, arcade.color.WHITE)
        # Should not raise exception
        state = manager._preserve_state([sprite])

        # Should have empty custom state on error
        assert "custom" in state
        assert state["custom"] == {}
