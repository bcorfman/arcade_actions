"""
Runtime configuration for ArcadeActions.

This module provides a minimal configuration surface so applications can
enable or disable debug behavior (like action creation logging) for the
entire library in one place. It uses simple setters/getters to keep
dependencies explicit and testable.
"""

from __future__ import annotations

import os
from typing import Final

from .base import Action

__all__ = [
    "set_debug_actions",
    "get_debug_actions",
    "apply_environment_configuration",
]


_ENV_DEBUG_FLAG: Final[str] = "ARCADEACTIONS_DEBUG"


def set_debug_actions(enabled: bool) -> None:
    """Enable or disable action debug logging globally.

    This updates `Action.debug_actions` which controls extra diagnostics in
    `Action.update_all`.

    Dependency guidance:
    - Call from your app's startup or tests to get consistent output.
    - Prefer this over touching `Action.debug_actions` directly.
    """

    Action.debug_actions = bool(enabled)


def get_debug_actions() -> bool:
    """Return whether action debug logging is enabled."""

    return bool(Action.debug_actions)


def apply_environment_configuration() -> None:
    """Apply configuration from environment variables.

    Currently supports:
    - ARCADEACTIONS_DEBUG: "1", "true", "yes" (case-insensitive) enable debug logs.
    """

    value = os.getenv(_ENV_DEBUG_FLAG)
    if value is None:
        return

    normalized = value.strip().lower()
    enabled = normalized in {"1", "true", "yes", "on"}
    set_debug_actions(enabled)
