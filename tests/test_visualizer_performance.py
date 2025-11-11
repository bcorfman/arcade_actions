"""
Stress tests ensuring ACE visualizer components handle large datasets.
"""

from __future__ import annotations

import arcade
from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.renderer import OverlayRenderer
from actions.visualizer.guides import GuideManager
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip


def _populate_store(store: DebugDataStore, count: int = 250) -> None:
    for idx in range(count):
        target_id = idx // 5
        store.update_snapshot(
            action_id=idx,
            action_type="MoveUntil" if idx % 2 == 0 else "RotateUntil",
            target_id=target_id,
            target_type="Sprite",
            tag="movement" if idx % 3 == 0 else None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=idx * 0.01,
            progress=(idx % 100) / 100,
            velocity=(idx % 5, (idx + 2) % 5),
            bounds=(0, 0, 800, 600) if idx % 10 == 0 else None,
            metadata={"path_points": [(0, 0), (100, 50), (200, 0)]} if idx % 7 == 0 else None,
        )
        store.record_condition_evaluation(
            action_id=idx,
            action_type="MoveUntil",
            result=(idx % 2 == 0),
            condition_str=f"cond_{idx}",
            sample=idx,
        )
        store.record_event(
            "created",
            action_id=idx,
            action_type="MoveUntil",
            target_id=target_id,
            target_type="Sprite",
            tag=None,
        )
        if idx % 4 == 0:
            store.record_event(
                "started",
                action_id=idx,
                action_type="MoveUntil",
                target_id=target_id,
                target_type="Sprite",
                tag=None,
            )


def test_overlay_renderer_handles_large_snapshot_sets():
    store = DebugDataStore()
    _populate_store(store)

    overlay = InspectorOverlay(debug_store=store)
    overlay.update()

    renderer = OverlayRenderer(overlay)
    renderer.update()

    assert overlay.get_total_action_count() == 250
    assert len(renderer.text_objects) > 0


def test_guides_and_panels_scale_with_dataset():
    store = DebugDataStore()
    _populate_store(store)

    guides = GuideManager()
    condition_debugger = ConditionDebugger(debug_store=store, max_entries=200)
    timeline = TimelineStrip(debug_store=store, max_entries=200)

    overlay = InspectorOverlay(debug_store=store)
    overlay.update()

    sprite_positions = {snapshot.target_id: (snapshot.target_id * 10, 50) for snapshot in store.get_all_snapshots()}

    guides.toggle_all()
    guides.update(store.get_all_snapshots(), sprite_positions)
    condition_debugger.update()
    timeline.update()

    assert len(guides.velocity_guide.arrows) > 0
    assert len(guides.bounds_guide.rectangles) > 0
    assert len(condition_debugger.entries) == condition_debugger.max_entries
    assert len(timeline.entries) <= timeline.max_entries
