from __future__ import annotations

"""Physics adapter layer for optional PyMunk integration.

This module provides helpers that allow ArcadeActions to optionally route
movement and rotation operations through an ``arcade.PymunkPhysicsEngine``
when one is available, while maintaining backward compatibility with direct
sprite attribute manipulation.
"""

from typing import Any, Protocol


class _PhysicsEngineProtocol(Protocol):
    """Subset of the arcade.PymunkPhysicsEngine API we rely on."""

    def set_velocity(self, sprite: Any, velocity: tuple[float, float]) -> None: ...  # noqa: E501

    def get_velocity(self, sprite: Any) -> tuple[float, float]: ...

    def apply_force(self, sprite: Any, force: tuple[float, float]) -> None: ...

    def apply_impulse(self, sprite: Any, impulse: tuple[float, float]) -> None: ...

    def set_angular_velocity(self, sprite: Any, omega: float) -> None: ...

    # Convenience method for quick membership check; not present on real engine
    def has_sprite(self, sprite: Any) -> bool: ...


_current_engine: _PhysicsEngineProtocol | None = None


def set_current_engine(engine: _PhysicsEngineProtocol | None) -> None:
    """Set the current physics engine context for this update frame.

    The ArcadeActions global update may pass an engine each frame. This avoids
    tight coupling and enables easy test injection.
    """

    global _current_engine
    _current_engine = engine


def get_current_engine() -> _PhysicsEngineProtocol | None:
    """Return the current physics engine context, if any."""

    return _current_engine


def detect_engine(sprite: Any, *, provided: _PhysicsEngineProtocol | None = None) -> _PhysicsEngineProtocol | None:
    """Detect which physics engine manages a sprite.

    Returns the provided engine if given, otherwise returns the current
    frame's engine context set via set_current_engine.
    """

    if provided is not None:
        return provided
    return _current_engine


# ---------------------------------------------------------------------------
# Adapter helper functions
# ---------------------------------------------------------------------------


def set_velocity(
    sprite: Any,
    velocity: tuple[float, float],
    *,
    physics_engine: _PhysicsEngineProtocol | None = None,
) -> None:
    """Set (change_x, change_y) on *sprite* or route via physics engine.

    If a physics engine is available for the sprite, route to engine.set_velocity.
    Otherwise assign to ``sprite.change_x`` and ``sprite.change_y``.
    """
    engine = detect_engine(sprite, provided=physics_engine)
    if engine is not None:
        engine.set_velocity(sprite, velocity)
        return
    vx, vy = velocity
    sprite.change_x = vx
    sprite.change_y = vy


def get_velocity(
    sprite: Any,
    *,
    physics_engine: _PhysicsEngineProtocol | None = None,
) -> tuple[float, float]:
    """Get current velocity of *sprite* from physics engine or sprite attributes.

    If a physics engine is available for the sprite, route to engine.get_velocity.
    Otherwise return ``(sprite.change_x, sprite.change_y)``.
    """
    engine = detect_engine(sprite, provided=physics_engine)
    if engine is not None:
        return engine.get_velocity(sprite)
    return (sprite.change_x, sprite.change_y)


def apply_force(
    sprite: Any,
    force: tuple[float, float],
    *,
    physics_engine: _PhysicsEngineProtocol | None = None,
) -> None:
    """Apply a force to sprite via physics engine.

    If a physics engine is available for the sprite, route to engine.apply_force.
    Otherwise this is a no-op (forces only make sense with physics simulation).
    """

    engine = detect_engine(sprite, provided=physics_engine)
    if engine is not None:
        engine.apply_force(sprite, force)


def apply_impulse(
    sprite: Any,
    impulse: tuple[float, float],
    *,
    physics_engine: _PhysicsEngineProtocol | None = None,
) -> None:
    """Apply an impulse to *sprite* via physics engine.

    If a physics engine is available for the sprite, route to engine.apply_impulse.
    Otherwise this is a no-op (impulses only make sense with physics simulation).
    """

    engine = detect_engine(sprite, provided=physics_engine)
    if engine is not None:
        engine.apply_impulse(sprite, impulse)


def set_angular_velocity(
    sprite: Any,
    omega: float,
    *,
    physics_engine: _PhysicsEngineProtocol | None = None,
) -> None:
    """Set angular velocity on *sprite* or via physics engine.

    If a physics engine is available for the sprite, route to engine.set_angular_velocity.
    Otherwise assign to ``sprite.change_angle``.
    """

    engine = detect_engine(sprite, provided=physics_engine)
    if engine is not None:
        engine.set_angular_velocity(sprite, omega)
        return
    sprite.change_angle = omega
