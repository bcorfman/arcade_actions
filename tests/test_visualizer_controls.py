"""
Tests for debug control manager handling keyboard shortcuts.
"""

from __future__ import annotations

import arcade
import pytest
from pathlib import Path

from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.guides import GuideManager
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip
from actions.visualizer.controls import DebugControlManager


class StubActionController:
    """Simple stub implementing pause/resume/step for tests."""

    def __init__(self):
        self.paused = False
        self.steps: list[float] = []

    def pause_all(self) -> None:
        self.paused = True

    def resume_all(self) -> None:
        self.paused = False

    def step_all(self, delta_time: float) -> None:
        self.steps.append(delta_time)


@pytest.fixture
def control_context(tmp_path: Path):
    store = DebugDataStore()
    overlay = InspectorOverlay(debug_store=store)
    guides = GuideManager()
    condition_debugger = ConditionDebugger(debug_store=store)
    timeline = TimelineStrip(debug_store=store)
    action_controller = StubActionController()
    manager = DebugControlManager(
        overlay=overlay,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        snapshot_directory=tmp_path,
        action_controller=action_controller,
        step_delta=0.016,
    )
    return store, overlay, guides, condition_debugger, timeline, action_controller, manager, tmp_path


def press(manager: DebugControlManager, key: int) -> None:
    manager.handle_key_press(key, modifiers=0)


def test_f3_toggles_overlay_visibility(control_context):
    _, overlay, _, _, _, _, manager, _ = control_context
    assert overlay.visible is True
    press(manager, arcade.key.F3)
    assert overlay.visible is False
    press(manager, arcade.key.F3)
    assert overlay.visible is True


def test_f5_toggles_guides(control_context):
    _, _, guides, _, _, _, manager, _ = control_context
    initial_state = guides.velocity_guide.enabled
    press(manager, arcade.key.F5)
    assert guides.velocity_guide.enabled is not initial_state
    assert guides.bounds_guide.enabled is not initial_state
    assert guides.path_guide.enabled is not initial_state


def test_f6_f7_pause_and_step(control_context):
    _, _, _, _, _, action_controller, manager, _ = control_context

    press(manager, arcade.key.F6)
    assert action_controller.paused is True

    # When paused, F7 should step once
    press(manager, arcade.key.F7)
    assert action_controller.steps == [0.016]

    # While still paused, another step accumulates
    press(manager, arcade.key.F7)
    assert action_controller.steps == [0.016, 0.016]

    # Resume (unpaused) - steps should not change
    press(manager, arcade.key.F6)
    assert action_controller.paused is False
    press(manager, arcade.key.F7)
    assert action_controller.steps == [0.016, 0.016]


def test_f8_cycles_highlight(control_context):
    store, overlay, _, _, _, _, manager, _ = control_context

    store.update_snapshot(
        action_id=1,
        action_type="MoveUntil",
        target_id=100,
        target_type="Sprite",
        tag=None,
        is_active=True,
        is_paused=False,
        factor=1.0,
        elapsed=0.0,
        progress=None,
    )
    store.update_snapshot(
        action_id=2,
        action_type="RotateUntil",
        target_id=200,
        target_type="Sprite",
        tag=None,
        is_active=True,
        is_paused=False,
        factor=1.0,
        elapsed=0.0,
        progress=None,
    )

    overlay.update()

    press(manager, arcade.key.F8)
    assert overlay.highlighted_target_id == 100
    press(manager, arcade.key.F8)
    assert overlay.highlighted_target_id == 200


def test_f9_exports_snapshot(control_context):
    store, overlay, _, _, _, _, manager, snapshot_dir = control_context

    store.update_frame(5, 0.2)
    store.record_event(
        "created",
        action_id=1,
        action_type="MoveUntil",
        target_id=123,
        target_type="Sprite",
        tag=None,
    )

    overlay.update()
    press(manager, arcade.key.F9)

    files = list(snapshot_dir.glob("snapshot_*.json"))
    assert len(files) == 1
    contents = files[0].read_text()
    assert "MoveUntil" in contents
    assert "created" in contents


def test_f4_toggles_condition_panel(control_context):
    _, _, _, condition_debugger, _, _, manager, _ = control_context
    assert manager.condition_panel_visible is True
    press(manager, arcade.key.F4)
    assert manager.condition_panel_visible is False
    press(manager, arcade.key.F4)
    assert manager.condition_panel_visible is True

def test_unhandled_key_returns_false(control_context):
    *_, manager, _ = control_context
    handled = manager.handle_key_press(arcade.key.A)
    assert handled is False

def test_update_when_condition_panel_hidden(control_context):
    store, overlay, guides, condition_debugger, timeline, _, manager, _ = control_context
    # populate store so guides see snapshots
    store.update_snapshot(
        action_id=1,
        action_type="MoveUntil",
        target_id=50,
        target_type="Sprite",
        tag=None,
        is_active=True,
        is_paused=False,
        factor=1.0,
        elapsed=0.0,
        progress=None,
        velocity=(1, 0),
    )
    manager.handle_key_press(arcade.key.F4)  # hide condition panel
    manager.update(sprite_positions={50: (10, 10)})
    assert manager.condition_panel_visible is False
    assert condition_debugger.entries == []
    assert len(guides.velocity_guide.arrows) == 1

def test_f7_no_step_when_not_paused(control_context):
    *_, action_controller, manager, _ = control_context
    handled = manager.handle_key_press(arcade.key.F7)
    assert handled is True
    assert action_controller.steps == []

