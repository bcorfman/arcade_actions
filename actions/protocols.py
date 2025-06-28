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

import arcade

__all__ = [
    "MovementLike",
    "CompositeLike",
    "GroupLike",
    "CollisionDetector",
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


@runtime_checkable
class CollisionDetector(Protocol):
    """Protocol for collision detection strategies."""

    def check_collision(
        self, sprite: ActionSprite, target_group: arcade.SpriteList | list[arcade.Sprite]
    ) -> list[arcade.Sprite]:
        """Check for collisions between a sprite and a group of sprites.

        Args:
            sprite: The sprite to check for collisions
            target_group: The group of sprites to check against

        Returns:
            List of sprites that collided with the given sprite
        """
        ...


class ArcadeCollisionDetector:
    """Default collision detector using Arcade's built-in collision detection."""

    def check_collision(
        self, sprite: arcade.Sprite, target_group: arcade.SpriteList | list[arcade.Sprite]
    ) -> list[arcade.Sprite]:
        """Check for collisions using arcade.check_for_collision_with_list."""
        # Ensure we have an Arcade SpriteList for collision API
        if isinstance(target_group, list):
            temp_list = arcade.SpriteList()
            for s in target_group:
                temp_list.append(s)
            collision_group = temp_list
        else:
            collision_group = target_group

        return arcade.check_for_collision_with_list(sprite, collision_group)


class MockCollisionDetector:
    """Mock collision detector for testing without OpenGL context."""

    def __init__(self):
        self.collision_results: dict[tuple[arcade.Sprite, tuple], list[arcade.Sprite]] = {}

    def set_collision_result(
        self, sprite: arcade.Sprite, target_sprites: tuple[arcade.Sprite, ...], result: list[arcade.Sprite]
    ):
        """Pre-configure collision results for testing."""
        self.collision_results[(sprite, target_sprites)] = result

    def check_collision(
        self, sprite: arcade.Sprite, target_group: arcade.SpriteList | list[arcade.Sprite]
    ) -> list[arcade.Sprite]:
        """Return pre-configured collision results."""
        target_tuple = tuple(target_group)
        return self.collision_results.get((sprite, target_tuple), [])


class BoundingBoxCollisionDetector:
    """Simple bounding box collision detector that works without OpenGL."""

    def check_collision(
        self, sprite: arcade.Sprite, target_group: arcade.SpriteList | list[arcade.Sprite]
    ) -> list[arcade.Sprite]:
        """Check collisions using simple bounding box overlap."""
        collisions = []

        sprite_left = sprite.center_x - sprite.width / 2
        sprite_right = sprite.center_x + sprite.width / 2
        sprite_bottom = sprite.center_y - sprite.height / 2
        sprite_top = sprite.center_y + sprite.height / 2

        for target in target_group:
            target_left = target.center_x - target.width / 2
            target_right = target.center_x + target.width / 2
            target_bottom = target.center_y - target.height / 2
            target_top = target.center_y + target.height / 2

            # Check for overlap
            if (
                sprite_left < target_right
                and sprite_right > target_left
                and sprite_bottom < target_top
                and sprite_top > target_bottom
            ):
                collisions.append(target)

        return collisions
