"""Window hook helpers for attaching the DevVisualizer."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import arcade

from arcadeactions import Action

try:
    import arcade.window_commands as window_commands_module
except ImportError:  # pragma: no cover - only happens in limited environments
    window_commands_module = None

_window_attach_hook_installed = False
_original_set_window: Callable[..., Any] | None = None

_update_all_attach_hook_installed = False
_previous_update_all_func: Callable[..., Any] | None = None


def install_window_attach_hook(get_dev_visualizer: Callable[[], Any]) -> None:
    """Install hook on arcade.window_commands.set_window to attach DevVisualizer when window becomes available."""
    global _window_attach_hook_installed, _original_set_window

    if _window_attach_hook_installed:
        return

    if window_commands_module is None:
        return

    _original_set_window = window_commands_module.set_window

    def patched_set_window(window):
        if _original_set_window is not None:
            _original_set_window(window)

        dev_viz = get_dev_visualizer()
        if dev_viz is not None and not dev_viz._attached and window is not None:
            dev_viz.attach_to_window(window)

    window_commands_module.set_window = patched_set_window  # type: ignore[assignment]
    _window_attach_hook_installed = True


def install_update_all_attach_hook(get_dev_visualizer: Callable[[], Any]) -> None:
    """Wrap Action.update_all so we can attach DevVisualizer once a window exists."""
    global _update_all_attach_hook_installed, _previous_update_all_func

    if _update_all_attach_hook_installed:
        return

    current_update_all = Action.update_all.__func__  # type: ignore[attr-defined]
    _previous_update_all_func = current_update_all

    def wrapped_update_all(cls: type[Action], delta_time: float, physics_engine: Any = None) -> None:
        current_update_all(cls, delta_time, physics_engine=physics_engine)

        dev_viz = get_dev_visualizer()
        if dev_viz is None or dev_viz._attached:
            return

        try:
            window = arcade.get_window()
        except RuntimeError:
            window = None

        if window is not None:
            dev_viz.attach_to_window(window)

    Action.update_all = classmethod(wrapped_update_all)  # type: ignore[method-assign]
    _update_all_attach_hook_installed = True
