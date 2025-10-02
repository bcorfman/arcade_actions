"""
Runtime configuration for ArcadeActions.

This module provides a minimal configuration surface so applications can
enable or disable debug behavior (like action creation logging) for the
entire library in one place. It uses simple setters/getters to keep
dependencies explicit and testable.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Final

from .base import Action

__all__ = [
    "set_debug_actions",
    "get_debug_actions",
    "apply_environment_configuration",
    "set_debug_options",
    "get_debug_options",
    "observe_actions",
    "clear_observed_actions",
]


_ENV_DEBUG_FLAG: Final[str] = "ARCADEACTIONS_DEBUG"


def _normalize_names(items: Iterable[object] | None) -> set[str] | None:
    """Convert class types or strings to normalized class name set."""
    if items is None:
        return None
    names: set[str] = set()
    for it in items:
        if isinstance(it, str):
            names.add(it)
        else:
            try:
                names.add(it.__name__)  # type: ignore[attr-defined]
            except Exception:
                pass
    return names if names else None


def set_debug_actions(enabled: bool) -> None:
    """Legacy function: maps boolean to debug levels.

    True -> level 1, False -> level 0
    Prefer using set_debug_options() for more control.
    """
    Action.debug_level = 1 if enabled else 0


def get_debug_actions() -> bool:
    """Legacy function: returns True if debug level >= 1."""
    return bool(Action.debug_level >= 1)


def set_debug_options(*, level: int = 0, include: Iterable[object] | None = None, include_all: bool = False) -> None:
    """Configure debug logging level and per-Action filters.

    Args:
        level: Debug level (0=off, 1=summary, 2=lifecycle, 3+=verbose)
        include: Action classes or names to observe (None = none)
        include_all: If True, observe all actions regardless of include filter
    """
    Action.debug_level = int(level)
    Action.debug_all = bool(include_all)
    Action.debug_include_classes = _normalize_names(include)
    # Reset summaries so level/filters apply immediately
    Action._last_counts = None
    Action._previous_actions = None


def get_debug_options() -> dict:
    """Return current debug configuration as a dict."""
    return {
        "level": Action.debug_level,
        "include_all": Action.debug_all,
        "include": sorted(Action.debug_include_classes) if Action.debug_include_classes else None,
    }


def observe_actions(*classes_or_names: object) -> None:
    """Add to the include filter for observed Action classes.

    Args:
        *classes_or_names: Action classes or string names to observe
    """
    names = _normalize_names(classes_or_names)
    if names:
        if Action.debug_include_classes is None:
            Action.debug_include_classes = set()
        Action.debug_include_classes.update(names)


def clear_observed_actions() -> None:
    """Clear any include filters."""
    Action.debug_include_classes = None


def apply_environment_configuration() -> None:
    """Apply configuration from environment variables.

    Supports:
    - ARCADEACTIONS_DEBUG: "0","1","2","3" (or "true"/"yes"/"on" -> 1)
    - ARCADEACTIONS_DEBUG_ALL: enable include_all
    - ARCADEACTIONS_DEBUG_INCLUDE: comma-separated class names
    """
    value = os.getenv(_ENV_DEBUG_FLAG)
    if value is None:
        return

    normalized = value.strip().lower()

    # Handle empty or whitespace-only strings
    if not normalized:
        set_debug_actions(False)
        return

    level: int
    if normalized.isdigit():
        level = int(normalized)
    elif normalized in {"true", "yes", "on"}:
        level = 1
    elif normalized in {"false", "no", "off"}:
        level = 0
    else:
        # Unknown values default to level 1
        level = 1

    include_all = os.getenv("ARCADEACTIONS_DEBUG_ALL", "").strip().lower() in {"1", "true", "yes", "on"}

    include_env = os.getenv("ARCADEACTIONS_DEBUG_INCLUDE")
    include = None
    if include_env:
        include = [name.strip() for name in include_env.split(",") if name.strip()]

    set_debug_options(level=level, include=include, include_all=include_all)
