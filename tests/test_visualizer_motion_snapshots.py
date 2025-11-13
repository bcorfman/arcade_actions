"""
Integration tests ensuring visualizer snapshots capture motion data for guides.
"""

from __future__ import annotations

from pathlib import Path

import arcade
import pytest

from actions import Action, follow_path_until, infinite, move_until
from actions.visualizer.attach import _collect_sprite_positions, attach_visualizer, detach_visualizer
from actions.visualizer.guides import VelocityGuide


class PassiveOverlay:
    """Minimal overlay stub for visualizer integration tests."""

    def __init__(self, debug_store):
        self.debug_store = debug_store
        self.visible = True

    def update(self) -> None:
        return


class PassiveRenderer:
    """Renderer stub that avoids real OpenGL work."""

    def __init__(self, overlay: PassiveOverlay):
        self.overlay = overlay

    def update(self) -> None:
        return

    def draw(self) -> None:
        return


class PassiveGuides:
    """Guide manager stub that just records last snapshot batch."""

    def __init__(self):
        self.last_snapshots = []
        self.last_positions: dict[int, tuple[float, float]] | None = None

    def toggle_all(self) -> None:  # pragma: no cover - unused
        return

    def update(self, snapshots, sprite_positions=None) -> None:
        self.last_snapshots = list(snapshots)
        self.last_positions = sprite_positions


class PassiveConditionDebugger:
    """Condition debugger stub."""

    def __init__(self, debug_store):
        self.debug_store = debug_store
        self.cleared = False

    def update(self) -> None:
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True


class PassiveTimeline:
    """Timeline stub."""

    def __init__(self, debug_store):
        self.debug_store = debug_store

    def update(self) -> None:
        return


class PassiveControlManager:
    """Control manager stub that wires the other components together."""

    def __init__(
        self,
        overlay: PassiveOverlay,
        guides: PassiveGuides,
        condition_debugger: PassiveConditionDebugger,
        timeline: PassiveTimeline,
        snapshot_directory: Path,
        action_controller: type[Action],
        toggle_event_window=None,
        target_names_provider=None,
        step_delta: float = 1 / 60,
    ) -> None:
        self.overlay = overlay
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.timeline = timeline
        self.snapshot_directory = snapshot_directory
        self.action_controller = action_controller
        self.toggle_event_window = toggle_event_window
        self.target_names_provider = target_names_provider
        self.step_delta = step_delta

    def handle_key_press(self, key: int, modifiers: int = 0) -> bool:  # pragma: no cover - unused
        return False

    def update(self, sprite_positions=None) -> None:
        self.overlay.update()
        self.timeline.update()
        if self.condition_debugger is not None:
            self.condition_debugger.update()
        self.guides.update(self.overlay.debug_store.get_all_snapshots(), sprite_positions or {})

    def get_target_names(self) -> dict[int, str]:
        if self.target_names_provider is None:
            return {}
        try:
            names = self.target_names_provider() or {}
        except Exception:
            return {}
        normalized: dict[int, str] = {}
        for key, value in names.items():
            try:
                normalized[int(key)] = str(value)
            except (TypeError, ValueError):
                continue
        return normalized


@pytest.fixture
def visualizer_session(tmp_path: Path):
    """Attach the visualizer with passive stubs for integration testing."""

    session = attach_visualizer(
        snapshot_directory=tmp_path,
        overlay_cls=PassiveOverlay,
        renderer_cls=PassiveRenderer,
        guide_manager_cls=PassiveGuides,
        condition_debugger_cls=PassiveConditionDebugger,
        timeline_cls=PassiveTimeline,
        controls_cls=PassiveControlManager,
    )
    try:
        yield session
    finally:
        detach_visualizer()


def _find_snapshot_by_action_type(store, action_type: str):
    for snapshot in store.get_all_snapshots():
        if snapshot.action_type == action_type:
            return snapshot
    raise AssertionError(f"No snapshot recorded for action type {action_type!r}")


def test_move_until_snapshots_include_velocity_and_bounds(visualizer_session):
    """MoveUntil snapshots should contain velocity, bounds, and boundary metadata for guides."""

    sprite = arcade.SpriteSolidColor(width=10, height=10, color=arcade.color.WHITE)
    sprite.center_x = 145  # Close to right boundary so we trigger bounce metadata immediately
    sprite.center_y = 75

    bounds = (100, 50, 150, 100)
    move_until(
        sprite,
        velocity=(5, 0),
        condition=infinite,
        bounds=bounds,
        boundary_behavior="bounce",
    )

    # allow the action to start and hit the boundary
    Action.update_all(1 / 60)
    sprite.update()  # apply the assigned velocity to position
    Action.update_all(1 / 60)

    snapshot = _find_snapshot_by_action_type(visualizer_session.debug_store, "MoveUntil")
    assert snapshot.velocity == (-5, 0)  # bounced to the left
    assert snapshot.bounds == bounds
    assert snapshot.metadata is not None
    boundary_state = snapshot.metadata.get("boundary_state", {})
    assert boundary_state, "Expected boundary metadata when collision occurred"
    assert list(boundary_state.values()), "At least one axis should be marked as touching a boundary"
    sprite_ids = snapshot.metadata.get("sprite_ids")
    assert sprite_ids and isinstance(sprite_ids, list)
    assert id(sprite) in sprite_ids


def test_follow_path_until_snapshot_preserves_path_metadata(visualizer_session):
    """FollowPathUntil snapshots should retain path points for path guides."""

    sprite = arcade.SpriteSolidColor(width=10, height=10, color=arcade.color.WHITE)
    sprite.center_x = 50
    sprite.center_y = 50

    path_points = [(50, 50), (75, 110), (120, 80)]
    follow_path_until(
        sprite,
        control_points=path_points,
        velocity=120,
        condition=infinite,
    )

    Action.update_all(1 / 60)
    Action.update_all(1 / 60)

    snapshot = _find_snapshot_by_action_type(visualizer_session.debug_store, "FollowPathUntil")
    metadata = snapshot.metadata or {}
    assert metadata.get("path_points") == path_points


def test_move_until_sprite_list_records_sprite_ids_for_guides(visualizer_session):
    """MoveUntil applied to SpriteList should record every sprite ID for velocity guides."""

    sprite_list = arcade.SpriteList()
    for offset in (0, 20, 40):
        sprite = arcade.SpriteSolidColor(width=8, height=8, color=arcade.color.YELLOW)
        sprite.center_x = 120 + offset
        sprite.center_y = 180
        sprite_list.append(sprite)

    bounds = (100, 150, 300, 220)
    move_until(
        sprite_list,
        velocity=(3, 0),
        condition=infinite,
        bounds=bounds,
        boundary_behavior="bounce",
    )

    # Run enough frames to capture snapshots and boundary state
    for _ in range(3):
        Action.update_all(1 / 60)
        sprite_list.update()

    snapshot = _find_snapshot_by_action_type(visualizer_session.debug_store, "MoveUntil")
    metadata = snapshot.metadata or {}
    sprite_ids = metadata.get("sprite_ids")
    assert sprite_ids and len(sprite_ids) == len(sprite_list)
    positions = _collect_sprite_positions()
    for sprite in sprite_list:
        assert id(sprite) in sprite_ids
        assert id(sprite) in positions

    # Velocity guide should produce one arrow per sprite when metadata is present
    velocity_guide = VelocityGuide()
    velocity_guide.enabled = True
    velocity_guide.update([snapshot], positions)
    assert len(velocity_guide.arrows) == len(sprite_list)
