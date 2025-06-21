from __future__ import annotations

"""Typed capability protocols for the ArcadeActions framework.

These lightweight ``typing.Protocol`` classes express *capabilities* that an
object may support (movement, composition, grouping, …).  They enable static
analysis and self-documentation while **avoiding** the need for runtime
``isinstance`` / ``hasattr`` inspection – aligning with the project rule of
ZERO TOLERANCE for such checks.

The protocols are intentionally minimal: they only include the methods that
other framework components already *call* on their collaborators.  Feel free
to extend **sparingly** when new capabilities are required.

No concrete classes are required to *inherit* from these protocols – static
type checkers rely on *structural* sub-typing, so any class with matching
attributes will satisfy the protocol automatically.
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

__all__ = [
    "MovementLike",
    "CompositeLike",
    "GroupLike",
]


@runtime_checkable
class MovementLike(Protocol):
    """An *action* that exposes movement-related helpers."""

    def reverse_movement(self, axis: str) -> None: ...

    def extract_movement_direction(self, collector: Callable[[float, float], None]) -> None: ...


@runtime_checkable
class CompositeLike(Protocol):
    """An *action* that wraps or coordinates other actions."""

    # The minimal public surface actually *used* by the engine.
    duration: float
    done: bool

    def start(self) -> None: ...

    def update(self, delta_time: float) -> None: ...

    def stop(self) -> None: ...


@runtime_checkable
class GroupLike(Protocol):
    """A container that can run actions on a group of sprites (SpriteGroup)."""

    def do(self, action: CompositeLike | MovementLike | Action) -> CompositeLike | MovementLike | Action: ...

    def clear_actions(self) -> None: ...

    def __iter__(self): ...

    def __len__(self) -> int: ...
