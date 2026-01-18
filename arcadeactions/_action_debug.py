from __future__ import annotations

from typing import Any

from ._action_targets import adapt_target


def _debug_log_action(action: Any, level: int, message: str) -> None:
    """Centralized debug logger with level and per-Action filtering."""
    from ._action_core import Action

    action_name = type(action).__name__

    if Action.debug_level < level:
        return

    if not Action.debug_all:
        include = Action.debug_include_classes
        if not include or action_name not in include:
            return

    print(f"[AA L{level} {action_name}] {message}")


def describe_target(target: Any) -> str:
    """Return a debug string for a target using adapters."""
    if target is None:
        return "None"
    adapter = adapt_target(target)
    return adapter.describe_target()
