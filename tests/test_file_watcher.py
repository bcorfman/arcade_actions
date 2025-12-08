"""Tests for the file watcher service that monitors Python files for hot-reload.

Fast unit tests only - integration tests are in tests/integration/test_file_watcher_integration.py
"""

from collections.abc import Callable
from pathlib import Path

from actions.dev.watch import FileWatcher


class TestFileWatcher:
    """Test suite for FileWatcher service - fast unit tests only."""

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

    def test_restart_after_stop_creates_fresh_observer(self, tmp_path):
        """Should allow restarting watcher after stopping it."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)

        watcher.start()
        watcher.stop()

        watcher.start()
        assert watcher.is_running()
        watcher.stop()

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
