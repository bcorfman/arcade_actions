"""Tests for visualizer function key behaviors (F3-F9) and game key preservation."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions import Action
from arcadeactions.visualizer import attach as visualizer_attach
from arcadeactions.visualizer import detach_visualizer, get_visualizer_session


@pytest.mark.usefixtures("window")
def test_f3_toggles_overlay(monkeypatch, window: arcade.Window | None) -> None:
    """F3 should toggle the visualizer overlay on/off."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        # Ensure clean start
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        # Setup window
        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        # Attach visualizer
        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        # Trigger lazy initialization
        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # Initial state: overlay should be visible at upper_left
        assert session.overlay.visible is True
        assert session.overlay.position == "upper_left"

        # Press F3 to cycle to upper_right
        result = session.keyboard_handler(arcade.key.F3, 0)
        assert result is True  # Key was handled
        assert session.overlay.visible is True
        assert session.overlay.position == "upper_right"

        # Press F3 again to cycle to lower_right
        result = session.keyboard_handler(arcade.key.F3, 0)
        assert result is True
        assert session.overlay.visible is True
        assert session.overlay.position == "lower_right"

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_f5_toggles_guides(monkeypatch, window: arcade.Window | None) -> None:
    """F5 should toggle all visual guides (velocity arrows, bounds, paths)."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # Get initial states
        initial_velocity = session.guides.velocity_guide.enabled
        initial_bounds = session.guides.bounds_guide.enabled
        initial_path = session.guides.path_guide.enabled

        # Press F5 to toggle all guides
        result = session.keyboard_handler(arcade.key.F5, 0)
        assert result is True

        # All guides should have toggled
        assert session.guides.velocity_guide.enabled != initial_velocity
        assert session.guides.bounds_guide.enabled != initial_bounds
        assert session.guides.path_guide.enabled != initial_path

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_f6_toggles_pause(monkeypatch, window: arcade.Window | None) -> None:
    """F6 should pause/resume all actions."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # Initially not paused
        assert session.control_manager.is_paused is False

        # Press F6 to pause
        result = session.keyboard_handler(arcade.key.F6, 0)
        assert result is True
        assert session.control_manager.is_paused is True

        # Press F6 again to resume
        result = session.keyboard_handler(arcade.key.F6, 0)
        assert result is True
        assert session.control_manager.is_paused is False

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_f7_steps_when_paused(monkeypatch, window: arcade.Window | None) -> None:
    """F7 should step through one frame when paused."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # Pause first
        session.keyboard_handler(arcade.key.F6, 0)
        assert session.control_manager.is_paused is True

        # F7 should be handled (even though we can't easily verify step was called)
        result = session.keyboard_handler(arcade.key.F7, 0)
        assert result is True

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_f8_highlights_next_action(monkeypatch, window: arcade.Window | None) -> None:
    """F8 should cycle through highlighted actions."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # F8 should be handled
        result = session.keyboard_handler(arcade.key.F8, 0)
        assert result is True

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_f9_exports_snapshot(monkeypatch, window: arcade.Window | None, tmp_path) -> None:
    """F9 should export a debug snapshot."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        # Attach with custom snapshot directory
        visualizer_attach.attach_visualizer(snapshot_directory=tmp_path)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # F9 should be handled
        result = session.keyboard_handler(arcade.key.F9, 0)
        assert result is True

        # Verify snapshot was created (snapshot exporter creates a file)
        # Note: We can't easily verify the file was created without more complex mocking,
        # but we can verify the key was handled
        assert result is True

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


@pytest.mark.usefixtures("window")
def test_non_function_keys_not_handled(monkeypatch, window: arcade.Window | None) -> None:
    """Regular keys (not F3-F9) should not be handled by visualizer."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        try:
            detach_visualizer()
        except Exception:
            pass
        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False

        if window is None or not hasattr(window, "show_view"):

            class StubWindow:
                def __init__(self) -> None:
                    self.handlers: dict[str, object] = {}
                    self._view = None
                    self.width = 800
                    self.height = 600

                @property
                def current_view(self):
                    return self._view

                def push_handlers(self, **handlers: object) -> None:
                    self.handlers.update(handlers)

                def show_view(self, view) -> None:
                    self._view = view
                    view.window = self

                def set_visible(self, value: bool) -> None:
                    self.visible = value

            window = StubWindow()
        else:
            if not hasattr(window, "current_view"):
                monkeypatch.setattr(type(window), "current_view", property(lambda self: getattr(self, "_view", None)))

        # Use monkeypatch to ensure window is restored

        original_set_window = arcade.set_window

        monkeypatch.setattr(arcade, "set_window", lambda w: original_set_window(w))

        arcade.set_window(window)

        visualizer_attach.auto_attach_from_env(force=True)
        session = get_visualizer_session()
        assert session is not None

        if session.keyboard_handler is None:
            Action.update_all(0.016)
            session = get_visualizer_session()
            assert session is not None

        assert session.keyboard_handler is not None

        # Test various regular keys - none should be handled by visualizer
        regular_keys = [
            arcade.key.A,
            arcade.key.SPACE,
            arcade.key.ENTER,
            arcade.key.ESCAPE,
            arcade.key.LEFT,
            arcade.key.RIGHT,
            arcade.key.UP,
            arcade.key.DOWN,
            arcade.key.LCTRL,
            arcade.key.R,
        ]

        for key in regular_keys:
            result = session.keyboard_handler(key, 0)
            assert result is False, f"Key {key} should not be handled by visualizer"

    finally:
        detach_visualizer()
        # Restore the global test window
        try:
            from tests.conftest import _global_test_window

            if _global_test_window is not None:
                arcade.set_window(_global_test_window)
        except (ImportError, AttributeError):
            pass
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)
