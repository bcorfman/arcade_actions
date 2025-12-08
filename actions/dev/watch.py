"""
File watcher service for hot-reload functionality.

Monitors Python files and triggers callbacks when changes are detected,
with debouncing to avoid excessive reloads during rapid edits.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from threading import Lock, Thread

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _DebounceHandler(FileSystemEventHandler):
    """
    Event handler that debounces file system events.

    Collects file change events and triggers a callback only after
    a quiet period (no events for debounce_seconds).
    """

    def __init__(
        self,
        callback: Callable[[list[Path]], None],
        debounce_seconds: float,
        patterns: list[str] | None = None,
    ):
        """
        Initialize the debounce handler.

        Args:
            callback: Function to call with list of changed file paths
            debounce_seconds: Minimum quiet time before triggering callback
            patterns: List of file patterns to watch (e.g., ["*.py"])
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.patterns = patterns or ["*.py"]

        self._pending_files: set[Path] = set()
        self._lock = Lock()
        self._last_event_time = 0.0
        self._debounce_thread: Thread | None = None
        self._stop_debounce = False

    def _matches_pattern(self, path: Path) -> bool:
        """Check if path matches any of the watch patterns."""
        return any(path.match(pattern) for pattern in self.patterns)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(event.src_path).resolve()

        # Check if file matches patterns
        if not self._matches_pattern(path):
            return

        # Add to pending files
        with self._lock:
            self._pending_files.add(path)
            self._last_event_time = time.time()

            # Start debounce thread if not already running
            if self._debounce_thread is None or not self._debounce_thread.is_alive():
                self._stop_debounce = False
                self._debounce_thread = Thread(target=self._debounce_worker, daemon=True)
                self._debounce_thread.start()

    def _debounce_worker(self) -> None:
        """
        Worker thread that waits for quiet period before triggering callback.

        Runs in background, checking if enough time has passed since the last
        event before calling the callback with accumulated file paths.
        """
        while not self._stop_debounce:
            time.sleep(0.05)  # Check frequently

            # Initialize variables for this iteration
            should_trigger = False
            files = []

            with self._lock:
                if not self._pending_files:
                    # No pending changes, exit thread
                    break

                time_since_last_event = time.time() - self._last_event_time

                if time_since_last_event >= self.debounce_seconds:
                    # Quiet period passed, trigger callback
                    files = list(self._pending_files)
                    self._pending_files.clear()
                    should_trigger = True

            # Call callback outside of lock
            if should_trigger:
                try:
                    self.callback(files)
                except Exception as e:
                    # Don't crash the watcher thread on callback errors
                    print(f"Error in file watcher callback: {e}")

                # Check if new events arrived while callback was executing
                with self._lock:
                    if not self._pending_files:
                        # No new events, safe to exit
                        break
                    # New events arrived - continue loop to process them

    def stop(self) -> None:
        """Stop the debounce worker thread."""
        self._stop_debounce = True
        if self._debounce_thread is not None and self._debounce_thread.is_alive():
            self._debounce_thread.join(timeout=1.0)


class FileWatcher:
    """
    Watches file system paths for changes and triggers callbacks.

    Uses watchdog library to monitor files, with debouncing to prevent
    excessive callback invocations during rapid file modifications.

    Example:
        def on_reload(changed_files):
            print(f"Reloading: {changed_files}")

        watcher = FileWatcher(
            paths=["src/game/"],
            callback=on_reload,
            patterns=["*.py"],
            debounce_seconds=0.3
        )
        watcher.start()

        # ... do work ...

        watcher.stop()

    Or use as context manager:
        with FileWatcher(paths=["src/"], callback=on_reload) as watcher:
            # ... do work ...
            pass
    """

    def __init__(
        self,
        paths: list[Path | str],
        callback: Callable[[list[Path]], None],
        patterns: list[str] | None = None,
        debounce_seconds: float = 0.3,
    ):
        """
        Initialize file watcher.

        Args:
            paths: List of directories or files to watch
            callback: Function to call with list of changed file paths
            patterns: File patterns to watch (default: ["*.py"])
            debounce_seconds: Minimum quiet time before triggering callback (default: 0.3)
        """
        self.paths = [Path(p) for p in paths]
        self.callback = callback
        self.patterns = patterns or ["*.py"]
        self.debounce_seconds = debounce_seconds

        self._observer = Observer()
        self._handler = _DebounceHandler(callback=callback, debounce_seconds=debounce_seconds, patterns=self.patterns)
        self._is_running = False

    def start(self) -> None:
        """Start watching files."""
        if self._is_running:
            return

        # Schedule observers for each path
        for path in self.paths:
            if not path.exists():
                # Skip nonexistent paths (might be created later)
                continue

            # Watch recursively if it's a directory
            self._observer.schedule(self._handler, str(path), recursive=path.is_dir())

        self._observer.start()
        self._is_running = True

    def stop(self) -> None:
        """Stop watching files."""
        if not self._is_running:
            return

        self._handler.stop()
        self._observer.stop()
        self._observer.join(timeout=2.0)
        self._is_running = False

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._is_running

    def __enter__(self) -> FileWatcher:
        """Enter context manager (starts watching)."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager (stops watching)."""
        self.stop()
