"""Tests for the file watcher service that monitors Python files for hot-reload.

Fast unit tests only - integration tests are in tests/integration/test_file_watcher_integration.py
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from actions.dev.watch import FileWatcher

pytestmark = pytest.mark.slow


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

    def test_debounce_handler_is_after_cutoff_none(self, tmp_path):
        """Test _DebounceHandler._is_after_cutoff when cutoff_time is None."""
        from actions.dev.watch import _DebounceHandler

        handler = _DebounceHandler(callback=lambda files: None, debounce_seconds=0.1)
        handler._cutoff_time = None

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Should return True when cutoff_time is None
        assert handler._is_after_cutoff(test_file) is True

    def test_debounce_handler_is_after_cutoff_file_not_found(self, tmp_path):
        """Test _DebounceHandler._is_after_cutoff when file doesn't exist."""
        from actions.dev.watch import _DebounceHandler
        import time

        handler = _DebounceHandler(callback=lambda files: None, debounce_seconds=0.1)
        handler._cutoff_time = time.time()

        nonexistent = tmp_path / "nonexistent.py"

        # Should return False when file doesn't exist
        assert handler._is_after_cutoff(nonexistent) is False

    def test_debounce_handler_matches_pattern(self, tmp_path):
        """Test _DebounceHandler._matches_pattern."""
        from actions.dev.watch import _DebounceHandler

        handler = _DebounceHandler(callback=lambda files: None, debounce_seconds=0.1, patterns=["*.py", "*.txt"])

        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        other_file = tmp_path / "test.js"

        assert handler._matches_pattern(py_file) is True
        assert handler._matches_pattern(txt_file) is True
        assert handler._matches_pattern(other_file) is False

    def test_debounce_handler_on_modified_ignores_directories(self, tmp_path):
        """Test _DebounceHandler.on_modified ignores directory events."""
        from actions.dev.watch import _DebounceHandler
        from watchdog.events import FileSystemEvent

        callback_called = []

        def callback(files):
            callback_called.append(files)

        handler = _DebounceHandler(callback=callback, debounce_seconds=0.1)

        # Create a mock directory event
        class MockDirEvent:
            is_directory = True
            src_path = str(tmp_path)

        handler.on_modified(MockDirEvent())

        # Should not trigger callback for directories
        assert len(callback_called) == 0

    def test_debounce_handler_on_modified_filters_by_pattern(self, tmp_path):
        """Test _DebounceHandler.on_modified filters files by pattern."""
        from actions.dev.watch import _DebounceHandler
        from watchdog.events import FileSystemEvent
        import time

        callback_called = []

        def callback(files):
            callback_called.append(files)

        handler = _DebounceHandler(callback=callback, debounce_seconds=0.1, patterns=["*.py"])
        handler._cutoff_time = time.time() - 1  # Allow all files

        # Create a mock event for a .js file (should be ignored)
        class MockJsEvent:
            is_directory = False
            src_path = str(tmp_path / "test.js")

        handler.on_modified(MockJsEvent())

        # Should not trigger callback for non-matching pattern
        assert len(callback_called) == 0

    def test_debounce_handler_on_modified_filters_by_cutoff(self, tmp_path):
        """Test _DebounceHandler.on_modified filters files by cutoff time."""
        from actions.dev.watch import _DebounceHandler
        from watchdog.events import FileSystemEvent
        import time

        callback_called = []

        def callback(files):
            callback_called.append(files)

        handler = _DebounceHandler(callback=callback, debounce_seconds=0.1, patterns=["*.py"])
        # Set cutoff time in the future (should reject old files)
        handler._cutoff_time = time.time() + 100

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Create a mock event
        class MockEvent:
            is_directory = False
            src_path = str(test_file)

        handler.on_modified(MockEvent())

        # Should not trigger callback for files older than cutoff
        assert len(callback_called) == 0

    def test_debounce_handler_stop_clears_pending_files(self, tmp_path):
        """Test _DebounceHandler.stop() clears pending files."""
        from actions.dev.watch import _DebounceHandler
        import time

        callback_called = []

        def callback(files):
            callback_called.append(files)

        handler = _DebounceHandler(callback=callback, debounce_seconds=0.1)
        handler._cutoff_time = time.time() - 1

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Add a pending file
        handler._pending_files.add(test_file)

        # Stop should clear pending files
        handler.stop()

        assert len(handler._pending_files) == 0

    def test_file_watcher_start_handles_nonexistent_path(self, tmp_path):
        """Test FileWatcher.start() handles nonexistent paths gracefully."""
        nonexistent = tmp_path / "does_not_exist"
        callback = self.make_callback()

        watcher = FileWatcher(paths=[nonexistent], callback=callback)
        # Should not raise exception
        watcher.start()
        assert watcher.is_running()
        watcher.stop()

    def test_file_watcher_start_handles_file_path(self, tmp_path):
        """Test FileWatcher.start() handles file paths (not just directories)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        callback = self.make_callback()

        watcher = FileWatcher(paths=[test_file], callback=callback)
        watcher.start()
        assert watcher.is_running()
        watcher.stop()

    def test_file_watcher_stop_when_not_running(self, tmp_path):
        """Test FileWatcher.stop() when not running."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)

        # Should not raise exception when stopping a non-running watcher
        watcher.stop()
        assert not watcher.is_running()

    def test_file_watcher_start_when_already_running(self, tmp_path):
        """Test FileWatcher.start() when already running."""
        callback = self.make_callback()
        watcher = FileWatcher(paths=[tmp_path], callback=callback)

        watcher.start()
        assert watcher.is_running()

        # Starting again should be a no-op
        watcher.start()
        assert watcher.is_running()

        watcher.stop()

    def test_debounce_handler_on_modified_triggers_callback(self, tmp_path):
        """Test _DebounceHandler.on_modified triggers callback after debounce."""
        from actions.dev.watch import _DebounceHandler
        import time
        import threading

        callback_called = []
        callback_lock = threading.Lock()

        def callback(files):
            with callback_lock:
                callback_called.append(files)

        handler = _DebounceHandler(
            callback=callback,
            debounce_seconds=0.1,  # Short debounce for testing
        )
        handler._cutoff_time = time.time() - 1  # Allow all files

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Create a mock event
        class MockEvent:
            is_directory = False
            src_path = str(test_file)

        handler.on_modified(MockEvent())

        # Wait for debounce to complete
        time.sleep(0.15)

        # Stop the handler to ensure thread completes
        handler.stop()

        # Give thread a moment to finish
        if handler._debounce_thread is not None:
            handler._debounce_thread.join(timeout=0.5)

        # Callback should have been called
        with callback_lock:
            assert len(callback_called) > 0
            assert test_file in callback_called[0]

    def test_debounce_handler_stop_joins_thread(self, tmp_path):
        """Test _DebounceHandler.stop() joins the debounce thread."""
        from actions.dev.watch import _DebounceHandler
        import time

        def callback(files):
            pass

        # Use a longer debounce time to ensure thread stays alive longer
        # This helps avoid race conditions on faster systems
        handler = _DebounceHandler(callback=callback, debounce_seconds=0.5)
        handler._cutoff_time = time.time() - 1

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Create a mock event to start the debounce thread
        class MockEvent:
            is_directory = False
            src_path = str(test_file)

        handler.on_modified(MockEvent())

        # Wait for thread to start and ensure it's running
        # Use a loop to wait for thread to actually start (handles timing variations)
        max_wait = 0.2
        waited = 0.0
        while handler._debounce_thread is None and waited < max_wait:
            time.sleep(0.01)
            waited += 0.01

        # Verify thread was created
        assert handler._debounce_thread is not None

        # On some platforms/timing (especially Mac with Python 3.11/3.12),
        # the thread might complete very quickly. Check if it's alive.
        # If it's not alive, that's okay - it means it completed naturally.
        # The important thing is that stop() works correctly in both cases.
        thread_was_alive = handler._debounce_thread.is_alive()

        # Stop should join the thread (if it's still running) or be a no-op (if it completed)
        handler.stop()

        # After stop, thread should definitely not be alive
        # NOTE: We only check thread.is_alive(), NOT handler._stop_debounce, because
        # _stop_debounce is set to True by stop() before returning, making any assertion
        # like "assert not thread.is_alive() or handler._stop_debounce" a tautology that
        # would always pass regardless of whether the thread was actually joined.
        if thread_was_alive:
            # If thread was alive, it should now be stopped
            # Give it a moment to join (stop() calls join with timeout=1.0)
            handler._debounce_thread.join(timeout=0.1)
            # Verify thread was actually joined - this assertion would fail if join() didn't work
            assert not handler._debounce_thread.is_alive()
        # If thread wasn't alive, that's also fine - it means it completed naturally
        # and stop() correctly handled the case where the thread already finished

    def test_debounce_handler_stop_when_thread_already_completed(self, tmp_path):
        """Test _DebounceHandler.stop() when thread completes naturally before stop() is called.

        This tests the timing issue where the debounce thread might complete very quickly
        (especially on Mac with Python 3.11/3.12) before we call stop(). The stop() method
        should handle this gracefully.
        """
        from actions.dev.watch import _DebounceHandler
        import time

        callback_called = []

        def callback(files):
            callback_called.append(files)

        # Use a very short debounce time so the thread completes quickly
        handler = _DebounceHandler(callback=callback, debounce_seconds=0.05)
        handler._cutoff_time = time.time() - 1

        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Create a mock event to start the debounce thread
        class MockEvent:
            is_directory = False
            src_path = str(test_file)

        handler.on_modified(MockEvent())

        # Wait for thread to start
        max_wait = 0.1
        waited = 0.0
        while handler._debounce_thread is None and waited < max_wait:
            time.sleep(0.01)
            waited += 0.01

        assert handler._debounce_thread is not None

        # Wait for the debounce time to pass and thread to complete naturally
        time.sleep(0.1)  # Wait longer than debounce_seconds (0.05)

        # Thread should have completed by now (callback should have been called)
        # Give it a moment to finish
        if handler._debounce_thread.is_alive():
            handler._debounce_thread.join(timeout=0.1)

        # Verify callback was called
        assert len(callback_called) > 0

        # Thread should be completed (not alive)
        assert not handler._debounce_thread.is_alive()

        # stop() should handle this gracefully (thread already finished)
        # This should not raise an exception
        handler.stop()

        # Verify stop() cleared pending files
        assert len(handler._pending_files) == 0
