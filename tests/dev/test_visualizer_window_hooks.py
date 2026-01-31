"""Test suite for DevVisualizer window attach hooks."""

from __future__ import annotations

import types

import arcade
import pytest

from arcadeactions import Action
from arcadeactions.dev import visualizer as viz_module
from arcadeactions.dev import window_hooks


@pytest.fixture(autouse=True)
def reset_hook_state():
    """Reset hook module state between tests."""
    original_window_commands = window_hooks.window_commands_module
    original_set_window = window_hooks._original_set_window
    original_window_hook = window_hooks._window_attach_hook_installed
    original_update_hook = window_hooks._update_all_attach_hook_installed
    original_prev_update = window_hooks._previous_update_all_func
    original_update_all = Action.update_all
    try:
        window_hooks._window_attach_hook_installed = False
        window_hooks._original_set_window = None
        window_hooks._update_all_attach_hook_installed = False
        window_hooks._previous_update_all_func = None
        yield
    finally:
        window_hooks.window_commands_module = original_window_commands
        window_hooks._original_set_window = original_set_window
        window_hooks._window_attach_hook_installed = original_window_hook
        window_hooks._update_all_attach_hook_installed = original_update_hook
        window_hooks._previous_update_all_func = original_prev_update
        Action.update_all = original_update_all


class TestWindowAttachHooks:
    """Coverage for hook helpers that attach DevVisualizer to windows."""

    def test_install_window_attach_hook_attaches_on_set_window(self, monkeypatch):
        """Patch set_window and attach when a window becomes available."""
        called = {"original": False, "attach": False}

        def original_set_window(window):
            called["original"] = True

        stub_commands = types.SimpleNamespace(set_window=original_set_window)
        monkeypatch.setattr(window_hooks, "window_commands_module", stub_commands)

        class StubDevViz:
            _attached = False

            def attach_to_window(self, window):
                called["attach"] = True

        monkeypatch.setattr(viz_module, "get_dev_visualizer", lambda: StubDevViz())

        viz_module._install_window_attach_hook()
        stub_commands.set_window(types.SimpleNamespace())

        assert called["original"] is True
        assert called["attach"] is True

    def test_install_update_all_attach_hook_attaches_when_window_exists(self, monkeypatch):
        """Attach DevVisualizer when Action.update_all runs and a window exists."""
        called = {"update": False, "attach": False}

        def stub_update_all(cls, delta_time, physics_engine=None):
            called["update"] = True

        monkeypatch.setattr(Action, "update_all", classmethod(stub_update_all))

        class StubDevViz:
            _attached = False

            def attach_to_window(self, window):
                called["attach"] = True

        monkeypatch.setattr(viz_module, "get_dev_visualizer", lambda: StubDevViz())
        monkeypatch.setattr(arcade, "get_window", lambda: types.SimpleNamespace())

        viz_module._install_update_all_attach_hook()
        Action.update_all(0.016)

        assert called["update"] is True
        assert called["attach"] is True
