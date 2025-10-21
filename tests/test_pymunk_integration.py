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

from actions import Action  # global update helper
from actions import physics_adapter as pa
from actions.conditional import MoveUntil, RotateUntil, infinite


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
    from actions.physics_adapter import get_current_engine, set_current_engine

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
    from actions.physics_adapter import detect_engine, set_current_engine

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
    from actions.physics_adapter import get_velocity

    sprite = arcade.Sprite()
    sprite.change_x = 42.0
    sprite.change_y = 17.0

    # Should return sprite attributes
    vx, vy = get_velocity(sprite)
    assert vx == 42.0
    assert vy == 17.0


def test_physics_adapter_apply_force_without_engine() -> None:
    """Test apply_force without physics engine (no-op when no engine present)."""
    from actions.physics_adapter import apply_force

    sprite = arcade.Sprite()

    # Should not raise an error when no physics engine
    apply_force(sprite, (10.0, 20.0))
