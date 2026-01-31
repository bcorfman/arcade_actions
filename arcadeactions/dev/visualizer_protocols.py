"""Protocol definitions for DevVisualizer metadata and window handling."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import arcade


@runtime_checkable
class SpriteWithActionConfigs(Protocol):
    """Protocol for sprites with action configuration metadata."""

    _action_configs: list[dict[str, Any]]


@runtime_checkable
class SpriteWithSourceMarkers(Protocol):
    """Protocol for sprites with source code markers."""

    _source_markers: list[dict[str, Any]]


@runtime_checkable
class SpriteWithOriginal(Protocol):
    """Protocol for sprites that reference an original sprite for sync."""

    _original_sprite: arcade.Sprite


@runtime_checkable
class SpriteWithPositionId(Protocol):
    """Protocol for sprites with position ID for source code sync."""

    _position_id: str | None


@runtime_checkable
class WindowWithContext(Protocol):
    """Protocol for windows with OpenGL context."""

    _context: Any | None
    height: int

    def get_location(self) -> tuple[int, int] | None: ...
