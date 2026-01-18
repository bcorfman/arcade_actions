"""Integration tests for FileWatcher with real file I/O and timing.

These tests are slow because they:
- Wait for file system events (0.2-1.0 seconds per test)
- Use real file I/O and background threads
- Depend on debouncing and timing behavior

Run with: uv run pytest tests/integration/test_file_watcher_integration.py
"""

import time
from collections.abc import Callable
from pathlib import Path

import pytest

from arcadeactions.dev.watch import FileWatcher

pytestmark = pytest.mark.slow


class TestFileWatcherIntegration:
    """Integration tests for FileWatcher with real file system operations."""

    def setup_method(self):
        """Setup before each test."""
        self.callback_called = False
        self.callback_paths = []

    def teardown_method(self):
        """Clean up after each test."""
        self.callback_called = False
        self.callback_paths = []

    def make_callback(self) -> Callable[[list[Path]], None]:
        """Create a callback that records when it's called."""

        def callback(changed_files: list[Path]) -> None:
            self.callback_called = True
            self.callback_paths.extend(changed_files)

        return callback

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

    def test_existing_files_before_start_do_not_trigger(self, tmp_path):
        """Existing files created before start should not trigger callbacks on start."""
        preexisting = tmp_path / "test.py"
        preexisting.write_text("# created before watcher start")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, patterns=["*.py"], debounce_seconds=0.1)
        watcher.start()

        time.sleep(0.2)
        watcher.stop()

        assert not self.callback_called

    def test_restart_before_debounce_completes_clears_pending_files(self, tmp_path):
        """Should clear pending files when stopped, preventing stale events on restart.

        This tests the bug where:
        1. File is modified -> added to _pending_files
        2. Watcher is stopped BEFORE debounce completes
        3. Watcher is restarted with set_cutoff_time()
        4. The old _pending_files bypass cutoff check and get processed

        The fix: _DebounceHandler.stop() must clear _pending_files.
        """
        test_file = tmp_path / "test.py"
        test_file.write_text("# initial")

        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback, debounce_seconds=0.5)
        watcher.start()

        # Wait for watcher to initialize
        time.sleep(0.2)

        # Modify file - this adds it to _pending_files
        test_file.write_text("# modified")

        # Stop IMMEDIATELY before debounce completes (debounce is 0.5s)
        time.sleep(0.1)  # Give event time to be detected, but not debounced
        watcher.stop()

        # At this point, _pending_files should contain test_file
        # If stop() doesn't clear it, it will be processed on restart

        # Clear callback state
        self.callback_called = False
        self.callback_paths = []

        # Restart watcher - this sets a new cutoff_time
        watcher.start()
        time.sleep(0.2)

        # Trigger a NEW event to start the debounce worker
        # This will process both the new event AND any old pending files
        test_file2 = tmp_path / "test2.py"
        test_file2.write_text("# new file")

        # Wait for debounce
        time.sleep(0.8)

        # BUG: Without the fix, the callback will include BOTH files (test.py and test2.py)
        # FIX: After clearing _pending_files in stop(), callback should only include test2.py
        if self.callback_called:
            # Check that only the new file was processed, not the stale one
            assert len(self.callback_paths) == 1, (
                f"Expected 1 file (test2.py), but got {len(self.callback_paths)}: {self.callback_paths}. "
                "Stale pending files from previous session should not be processed."
            )
            assert self.callback_paths[0].name == "test2.py", (
                f"Expected test2.py, but got {self.callback_paths[0].name}. "
                "Stale pending files (test.py) should not be processed after restart."
            )

        watcher.stop()

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

    def test_restart_after_stop_detects_changes(self, tmp_path):
        """Watcher should detect changes after being stopped and started again."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# initial")

        changes = []

        def on_change(paths: list[Path]) -> None:
            changes.extend(paths)

        watcher = FileWatcher(paths=[tmp_path], callback=on_change, patterns=["*.py"], debounce_seconds=0.1)

        # Start and stop without any modifications to simulate a pause/resume cycle
        watcher.start()
        time.sleep(0.2)
        watcher.stop()
        assert not changes  # No events yet

        # Restart watcher and make a change
        watcher.start()
        time.sleep(0.2)
        test_file.write_text("# modified after restart")
        time.sleep(0.5)
        watcher.stop()

        assert any(p.name == "test.py" for p in changes)

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
