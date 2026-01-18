"""Integration tests for optional PyMunk physics support.

These tests describe the expected behaviour of ArcadeActions when a
``arcade.PymunkPhysicsEngine`` manages a sprite *and* when no physics
engine is present.  They intentionally *fail* until the adapter and
core actions are fully implemented.

A light-weight stub of the physics engine is used so the tests do not
pull the real Arcade + Pymunk dependency tree (keeps CI fast).
"""

from __future__ import annotations

from typing import Any

import arcade  # runtime dependency already used in existing tests
import pytest

from arcadeactions import Action  # global update helper
from arcadeactions import physics_adapter as pa
from arcadeactions.conditional import MoveUntil, RotateUntil, infinite


class _StubPhysicsEngine:
    """Minimal stub mimicking the subset of PymunkPhysicsEngine we need."""

    def __init__(self) -> None:
        self._sprites: dict[int, arcade.Sprite] = {}
        # Track calls for assertions
        self.calls: list[tuple[str, tuple[Any, ...], dict]] = []

    # API -----------------------------------------------------------------
    def add_sprite(self, sprite: arcade.Sprite) -> None:  # signature simplified
        self._sprites[id(sprite)] = sprite

    def has_sprite(self, sprite: arcade.Sprite) -> bool:  # convenience helper
        return id(sprite) in self._sprites

    def set_velocity(self, sprite: arcade.Sprite, velocity: tuple[float, float]) -> None:
        self.calls.append(("set_velocity", (sprite, velocity), {}))
        # No-op behaviour for stub

    def apply_force(self, sprite: arcade.Sprite, force: tuple[float, float]) -> None:
        self.calls.append(("apply_force", (sprite, force), {}))

    def apply_impulse(self, sprite: arcade.Sprite, impulse: tuple[float, float]) -> None:
        self.calls.append(("apply_impulse", (sprite, impulse), {}))

    def set_angular_velocity(self, sprite: arcade.Sprite, omega: float) -> None:
        self.calls.append(("set_angular_velocity", (sprite, omega), {}))


class _StubBody:
    def __init__(self, body_type: str) -> None:
        self.body_type = body_type


class _StubKinematicBody:
    def __init__(self, body_type: str) -> None:
        self.body = _StubBody(body_type)


class _StubEngineWithSprites:
    """Stub engine exposing .sprites mapping for Action.update_all sync."""

    KINEMATIC = "kinematic"
    DYNAMIC = "dynamic"

    def __init__(self) -> None:
        self.sprites: dict[arcade.Sprite, _StubKinematicBody] = {}
        self.calls: list[tuple[arcade.Sprite, tuple[float, float]]] = []

    def set_velocity(self, sprite: arcade.Sprite, velocity: tuple[float, float]) -> None:
        self.calls.append((sprite, velocity))


# ---------------------------------------------------------------------------
# Helper fixtures -----------------------------------------------------------
# ---------------------------------------------------------------------------


@pytest.fixture()
def stub_engine(monkeypatch: pytest.MonkeyPatch) -> _StubPhysicsEngine:  # noqa: PT004
    """Provide a stub physics engine & patch adapter.detect_engine to use it."""

    engine = _StubPhysicsEngine()

    # Patch detect_engine to return our stub when sprite registered
    original_detect = pa.detect_engine

    def _fake_detect(sprite: Any, *, provided: Any | None = None):  # noqa: ANN401
        if engine.has_sprite(sprite):  # type: ignore[attr-defined]
            return engine  # type: ignore[return-value]
        return original_detect(sprite, provided=provided)

    monkeypatch.setattr(pa, "detect_engine", _fake_detect, raising=True)
    return engine


# ---------------------------------------------------------------------------
# Tests ---------------------------------------------------------------------
# ---------------------------------------------------------------------------


def test_moveuntil_routes_to_physics_engine(stub_engine: _StubPhysicsEngine) -> None:
    sprite = arcade.Sprite()
    stub_engine.add_sprite(sprite)

    # Create a simple MoveUntil action
    action = MoveUntil((5, 0), infinite)
    action.apply(sprite)

    # One update tick should route velocity through physics engine
    Action.update_all(1 / 60)

    assert any(call[0] == "set_velocity" for call in stub_engine.calls), (
        "MoveUntil should route velocity through physics engine when sprite is registered."
    )


def test_moveuntil_falls_back_without_engine() -> None:
    sprite = arcade.Sprite()

    action = MoveUntil((7, -3), infinite)
    action.apply(sprite)

    Action.update_all(1 / 60)

    # Expect direct attribute assignment (physics path not used).
    assert (sprite.change_x, sprite.change_y) == (7, -3)


def test_rotateuntil_routes_to_physics_engine(stub_engine: _StubPhysicsEngine) -> None:
    sprite = arcade.Sprite()
    stub_engine.add_sprite(sprite)

    action = RotateUntil(angular_velocity=45, condition=infinite)
    action.apply(sprite)

    Action.update_all(1 / 60)

    assert any(call[0] == "set_angular_velocity" for call in stub_engine.calls), (
        "RotateUntil should route angular velocity through physics engine when sprite is registered."
    )


def test_rotateuntil_falls_back_without_engine() -> None:
    sprite = arcade.Sprite()

    action = RotateUntil(angular_velocity=30, condition=infinite)
    action.apply(sprite)

    Action.update_all(1 / 60)

    # Expect direct attribute assignment (physics path not used).
    assert sprite.change_angle == 30


def test_physics_adapter_get_current_engine() -> None:
    """Test get_current_engine returns the context engine."""
    from arcadeactions.physics_adapter import get_current_engine, set_current_engine

    # Should be None initially
    assert get_current_engine() is None

    # Set an engine
    fake_engine = _StubPhysicsEngine()
    set_current_engine(fake_engine)

    # Should return the engine we set
    assert get_current_engine() is fake_engine

    # Clean up
    set_current_engine(None)


def test_physics_adapter_detect_engine_with_provided() -> None:
    """Test detect_engine prioritizes provided parameter."""
    from arcadeactions.physics_adapter import detect_engine, set_current_engine

    context_engine = _StubPhysicsEngine()
    provided_engine = _StubPhysicsEngine()

    # Set context engine
    set_current_engine(context_engine)

    sprite = arcade.Sprite()

    # Provided engine should take priority
    result = detect_engine(sprite, provided=provided_engine)
    assert result is provided_engine

    # Clean up
    set_current_engine(None)


def test_physics_adapter_get_velocity_fallback() -> None:
    """Test get_velocity falls back to sprite attributes without engine."""
    from arcadeactions.physics_adapter import get_velocity

    sprite = arcade.Sprite()
    sprite.change_x = 42.0
    sprite.change_y = 17.0

    # Should return sprite attributes
    vx, vy = get_velocity(sprite)
    assert vx == 42.0
    assert vy == 17.0


def test_physics_adapter_apply_force_without_engine() -> None:
    """Test apply_force without physics engine (no-op when no engine present)."""
    from arcadeactions.physics_adapter import apply_force

    sprite = arcade.Sprite()

    # Should not raise an error when no physics engine
    apply_force(sprite, (10.0, 20.0))


def test_update_all_syncs_kinematic_sprite_velocities() -> None:
    """Action.update_all syncs change_x/change_y through engine.sprites for kinematic bodies."""
    engine = _StubEngineWithSprites()
    sprite = arcade.Sprite()
    sprite.change_x = 4.0
    sprite.change_y = -2.0
    engine.sprites[sprite] = _StubKinematicBody(engine.KINEMATIC)

    dynamic_sprite = arcade.Sprite()
    dynamic_sprite.change_x = 10.0
    dynamic_sprite.change_y = 5.0
    engine.sprites[dynamic_sprite] = _StubKinematicBody(engine.DYNAMIC)

    Action.update_all(0.5, physics_engine=engine)

    assert engine.calls == [(sprite, (8.0, -4.0))]


def test_update_all_skips_sync_when_delta_time_zero() -> None:
    """Zero delta_time should skip kinematic sync to avoid divide-by-zero."""
    engine = _StubEngineWithSprites()
    sprite = arcade.Sprite()
    sprite.change_x = 3.0
    sprite.change_y = 1.0
    engine.sprites[sprite] = _StubKinematicBody(engine.KINEMATIC)

    Action.update_all(0.0, physics_engine=engine)

    assert engine.calls == []
