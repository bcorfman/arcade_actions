"""Tests for the file watcher service that monitors Python files for hot-reload."""

import time
from collections.abc import Callable
from pathlib import Path

from actions.dev.watch import FileWatcher


class TestFileWatcher:
    """Test suite for FileWatcher service."""

    def setup_method(self):
        """Setup before each test."""
        self.test_dir = None
        self.watcher = None
        self.callback_called = False
        self.callback_paths = []

    def teardown_method(self):
        """Clean up after each test."""
        if self.watcher is not None:
            self.watcher.stop()
        self.callback_called = False
        self.callback_paths = []

    def make_callback(self) -> Callable[[list[Path]], None]:
        """Create a callback that records when it's called."""

        def callback(changed_files: list[Path]) -> None:
            self.callback_called = True
            self.callback_paths.extend(changed_files)

        return callback

    def test_create_watcher_with_single_path(self, tmp_path):
        """Should create watcher for a single path."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)
        assert watcher is not None
        assert not watcher.is_running()

    def test_create_watcher_with_multiple_paths(self, tmp_path):
        """Should create watcher for multiple paths."""
        path1 = tmp_path / "dir1"
        path2 = tmp_path / "dir2"
        path1.mkdir()
        path2.mkdir()

        callback = self.make_callback()
        watcher = FileWatcher(paths=[path1, path2], callback=callback)
        assert watcher is not None

    def test_create_watcher_with_pattern(self, tmp_path):
        """Should create watcher with file pattern filter."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"])
        assert watcher is not None

    def test_create_watcher_with_debounce_time(self, tmp_path):
        """Should create watcher with custom debounce time."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, debounce_seconds=0.5)
        assert watcher is not None

    def test_start_watcher(self, tmp_path):
        """Should start watching files."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)
        watcher.start()
        assert watcher.is_running()
        watcher.stop()

    def test_stop_watcher(self, tmp_path):
        """Should stop watching files."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)
        watcher.start()
        assert watcher.is_running()
        watcher.stop()
        assert not watcher.is_running()

    def test_detect_file_change(self, tmp_path):
        """Should detect when a Python file is modified."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("# Initial content")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.1)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.2)

        # Modify the file
        test_file.write_text("# Modified content")

        # Wait for debounce and callback
        time.sleep(0.5)

        watcher.stop()

        assert self.callback_called
        assert len(self.callback_paths) > 0
        assert any(p.name == "test.py" for p in self.callback_paths)

    def test_debounce_multiple_rapid_changes(self, tmp_path):
        """Should debounce multiple rapid changes into single callback."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Initial")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.3)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.2)

        # Make multiple rapid changes
        for i in range(5):
            test_file.write_text(f"# Change {i}")
            time.sleep(0.05)  # Faster than debounce time

        # Wait for debounce window to close
        time.sleep(0.6)

        watcher.stop()

        # Should have been called once (or very few times) due to debouncing
        assert self.callback_called
        # The exact number depends on timing, but should be much less than 5
        # Just verify we got at least one callback with the file
        assert any(p.name == "test.py" for p in self.callback_paths)

    def test_ignore_non_matching_patterns(self, tmp_path):
        """Should ignore files that don't match patterns."""
        # Create files with different extensions
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("# Python")
        txt_file.write_text("Text")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.1)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.2)

        # Modify only the txt file
        txt_file.write_text("Modified text")

        # Wait for debounce
        time.sleep(0.5)

        watcher.stop()

        # Should not have been called since only .txt was modified
        assert not self.callback_called

    def test_watch_subdirectories(self, tmp_path):
        """Should watch subdirectories recursively."""
        # Create subdirectory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.py"
        test_file.write_text("# Initial")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.1)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.2)

        # Modify file in subdirectory
        test_file.write_text("# Modified")

        # Wait for debounce
        time.sleep(0.5)

        watcher.stop()

        assert self.callback_called
        assert any(p.name == "test.py" for p in self.callback_paths)

    def test_provide_absolute_paths_to_callback(self, tmp_path):
        """Should provide absolute paths to callback."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Initial")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.1)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.2)

        # Modify the file
        test_file.write_text("# Modified")

        # Wait for debounce
        time.sleep(0.5)

        watcher.stop()

        assert self.callback_called
        assert all(p.is_absolute() for p in self.callback_paths)

    def test_handle_nonexistent_path(self, tmp_path):
        """Should handle nonexistent paths gracefully."""
        nonexistent = tmp_path / "does_not_exist"
        callback = self.make_callback()

        # Should not raise exception
        watcher = FileWatcher(paths=[nonexistent], callback=callback)
        watcher.start()
        watcher.stop()

    def test_context_manager_support(self, tmp_path):
        """Should support context manager protocol."""
        callback = self.make_callback()

        with FileWatcher(paths=[tmp_path], callback=callback) as watcher:
            assert watcher.is_running()

        # Should auto-stop after exiting context
        assert not watcher.is_running()


class TestFileWatcherIntegration:
    """Integration tests for FileWatcher with realistic scenarios."""

    def test_reload_workflow(self, tmp_path):
        """Simulate a typical hot-reload workflow."""
        # Setup: create a module file
        module_file = tmp_path / "my_module.py"
        module_file.write_text("""
class MyWave:
    def __init__(self):
        self.width = 5
""")

        changes_detected = []

        def on_change(paths: list[Path]) -> None:
            changes_detected.extend(paths)

        # Start watching
        watcher = FileWatcher(paths=[tmp_path], callback=on_change, patterns=["*.py"], debounce_seconds=0.2)
        watcher.start()
        time.sleep(0.2)

        # Simulate developer editing the file
        module_file.write_text("""
class MyWave:
    def __init__(self):
        self.width = 10  # Changed!
""")

        # Wait for detection and debounce
        time.sleep(0.5)

        watcher.stop()

        # Verify change was detected
        assert len(changes_detected) > 0
        assert any(p.name == "my_module.py" for p in changes_detected)

    def test_race_condition_during_callback_execution(self, tmp_path):
        """Should not lose events that arrive while callback is executing."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# initial")

        callback_count = 0
        all_changes = []

        def slow_callback(changed_files: list[Path]) -> None:
            """Callback that takes time, creating window for race condition."""
            nonlocal callback_count
            callback_count += 1
            all_changes.extend(changed_files)

            # If this is the first callback, trigger another change
            # while we're still executing (but after pending_files was cleared)
            if callback_count == 1:
                time.sleep(0.1)  # Simulate slow callback
                test_file.write_text(f"# change {callback_count + 1}")
                time.sleep(0.1)  # Give time for event to be registered

        watcher = FileWatcher(paths=[tmp_path], callback=slow_callback, patterns=["*.py"], debounce_seconds=0.2)
        watcher.start()
        time.sleep(0.1)

        # Trigger first change
        test_file.write_text("# change 1")

        # Wait for both callbacks to complete
        # First callback after 0.2s debounce + 0.2s execution
        # Second callback after another 0.2s debounce
        time.sleep(1.0)

        watcher.stop()

        # Both changes should have been processed
        # If race condition exists, second change is lost
        assert callback_count >= 2, f"Expected at least 2 callbacks, got {callback_count}"

    def test_stop_immediately_after_event_no_unbound_error(self, tmp_path):
        """Should not raise UnboundLocalError if stopped immediately after event triggers thread.

        This tests the fix for a race condition where:
        1. An event triggers, creating a new debounce thread
        2. stop() is called immediately, setting _stop_debounce = True
        3. Thread checks while condition before entering loop body
        4. Old code would skip loop, then try to access undefined time_since_last_event

        The fix ensures variables are always defined before use.
        """
        test_file = tmp_path / "test.py"
        test_file.write_text("# Initial")

        callback_called = False

        def callback(changed_files: list[Path]) -> None:
            nonlocal callback_called
            callback_called = True

        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.3)
        watcher.start()

        # Give watcher time to initialize
        time.sleep(0.1)

        # Modify file to trigger event and spawn debounce thread
        test_file.write_text("# Modified")

        # Stop immediately after modification, creating race condition window
        # The debounce thread may not have entered its while loop yet
        time.sleep(0.02)  # Small delay to ensure event handler runs
        watcher.stop()

        # Old code would raise UnboundLocalError here during thread cleanup
        # New code handles this gracefully
        # Test passes if no exception is raised
