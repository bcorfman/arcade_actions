"""Tests for actions.dev.__init__.py - enable_dev_mode and auto_enable_from_env functions."""

import os

from actions.dev import auto_enable_from_env, enable_dev_mode
from actions.dev.reload import ReloadManager


class TestEnableDevMode:
    """Test suite for enable_dev_mode function."""

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any managers created
        pass

    def test_enable_dev_mode_defaults(self, tmp_path):
        """Test enable_dev_mode with default parameters."""
        manager = enable_dev_mode()
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_watch_paths(self, tmp_path):
        """Test enable_dev_mode with custom watch paths."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        manager = enable_dev_mode(watch_paths=[watch_dir])
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_file_path(self, tmp_path):
        """Test enable_dev_mode with file path (not directory)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        manager = enable_dev_mode(watch_paths=[test_file])
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_nonexistent_path(self, tmp_path):
        """Test enable_dev_mode with nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        manager = enable_dev_mode(watch_paths=[nonexistent])
        assert isinstance(manager, ReloadManager)
        # Should still start (watcher handles nonexistent paths)
        manager.stop()

    def test_enable_dev_mode_with_root_path(self, tmp_path):
        """Test enable_dev_mode with explicit root_path."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        manager = enable_dev_mode(watch_paths=[watch_dir], root_path=tmp_path)
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_infers_root_from_watch_paths(self, tmp_path):
        """Test enable_dev_mode infers root_path from watch_paths."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        manager = enable_dev_mode(watch_paths=[watch_dir])
        assert isinstance(manager, ReloadManager)
        # root_path should be inferred from watch_paths
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_auto_reload_false(self, tmp_path):
        """Test enable_dev_mode with auto_reload=False."""
        manager = enable_dev_mode(watch_paths=[tmp_path], auto_reload=False)
        assert isinstance(manager, ReloadManager)
        # When auto_reload=False, manager doesn't start watching automatically
        assert not manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_preserve_state_false(self, tmp_path):
        """Test enable_dev_mode with preserve_state=False."""
        manager = enable_dev_mode(watch_paths=[tmp_path], preserve_state=False)
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_custom_callbacks(self, tmp_path):
        """Test enable_dev_mode with custom state_provider, sprite_provider, and on_reload."""
        state_captured = []
        sprites_captured = []
        reload_called = []

        def state_provider():
            state_captured.append("called")
            return {"test": "state"}

        def sprite_provider():
            sprites_captured.append("called")
            return []

        def on_reload(files, state):
            reload_called.append((files, state))

        manager = enable_dev_mode(
            watch_paths=[tmp_path], state_provider=state_provider, sprite_provider=sprite_provider, on_reload=on_reload
        )
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_reload_key(self, tmp_path):
        """Test enable_dev_mode with custom reload_key."""
        manager = enable_dev_mode(watch_paths=[tmp_path], reload_key="F5")
        assert isinstance(manager, ReloadManager)
        assert hasattr(manager, "reload_key")
        assert manager.reload_key == "F5"
        manager.stop()

    def test_enable_dev_mode_with_reload_key_none(self, tmp_path):
        """Test enable_dev_mode with reload_key=None."""
        manager = enable_dev_mode(watch_paths=[tmp_path], reload_key=None)
        assert isinstance(manager, ReloadManager)
        assert manager.reload_key is None
        manager.stop()

    def test_enable_dev_mode_with_patterns(self, tmp_path):
        """Test enable_dev_mode with custom file patterns."""
        manager = enable_dev_mode(watch_paths=[tmp_path], patterns=["*.py", "*.pyx"])
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_debounce_seconds(self, tmp_path):
        """Test enable_dev_mode with custom debounce_seconds."""
        manager = enable_dev_mode(watch_paths=[tmp_path], debounce_seconds=0.5)
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_enable_dev_mode_with_empty_watch_paths(self):
        """Test enable_dev_mode with empty watch_paths list."""
        manager = enable_dev_mode(watch_paths=[])
        assert isinstance(manager, ReloadManager)
        # When watch_paths is empty, root_path should default to cwd
        assert manager.is_watching()
        manager.stop()


class TestAutoEnableFromEnv:
    """Test suite for auto_enable_from_env function."""

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up environment variable
        if "ARCADEACTIONS_DEV" in os.environ:
            del os.environ["ARCADEACTIONS_DEV"]

    def test_auto_enable_from_env_when_set(self, tmp_path, monkeypatch):
        """Test auto_enable_from_env when ARCADEACTIONS_DEV=1."""
        monkeypatch.setenv("ARCADEACTIONS_DEV", "1")

        manager = auto_enable_from_env()
        assert isinstance(manager, ReloadManager)
        assert manager.is_watching()
        manager.stop()

    def test_auto_enable_from_env_when_not_set(self, monkeypatch):
        """Test auto_enable_from_env when ARCADEACTIONS_DEV is not set."""
        monkeypatch.delenv("ARCADEACTIONS_DEV", raising=False)

        manager = auto_enable_from_env()
        assert manager is None

    def test_auto_enable_from_env_when_set_to_other_value(self, monkeypatch):
        """Test auto_enable_from_env when ARCADEACTIONS_DEV is set to something other than '1'."""
        monkeypatch.setenv("ARCADEACTIONS_DEV", "0")

        manager = auto_enable_from_env()
        assert manager is None
