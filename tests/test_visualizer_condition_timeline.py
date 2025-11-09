"""
Tests for condition debugger panel and action timeline strip.

Ensures data collection and filtering logic works for condition evaluations
and timeline entries derived from debug instrumentation.
"""

from __future__ import annotations

import pytest
from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip


class TestConditionDebugger:
    """Tests for the condition debugger panel."""

    def setup_method(self):
        self.store = DebugDataStore()

    def _create_snapshot(self, action_id: int, tag: str | None = None) -> None:
        """Helper to register a snapshot for contextual data."""
        self.store.update_snapshot(
            action_id=action_id,
            action_type="MoveUntil",
            target_id=42,
            target_type="Sprite",
            tag=tag,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.25,
        )

    def test_collects_entries_from_evaluations(self):
        """Debugger should collect evaluation entries with snapshot context."""
        self._create_snapshot(1, tag="movement")
        self.store.update_frame(10, 0.20)
        self.store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            condition_str="sprite.x > 100",
            center_x=150,
        )

        debugger = ConditionDebugger(debug_store=self.store)
        debugger.update()

        assert len(debugger.entries) == 1
        entry = debugger.entries[0]
        assert entry.action_id == 1
        assert entry.action_type == "MoveUntil"
        assert entry.result is True
        assert entry.tag == "movement"
        assert entry.variables["center_x"] == 150
        assert entry.condition_str == "sprite.x > 100"

    def test_filters_by_tag(self):
        """Debugger should filter entries by tag when provided."""
        self._create_snapshot(1, tag="movement")
        self._create_snapshot(2, tag="visual")

        self.store.record_condition_evaluation(1, "MoveUntil", False)
        self.store.record_condition_evaluation(2, "FadeUntil", True)

        debugger = ConditionDebugger(debug_store=self.store, filter_tag="movement")
        debugger.update()

        assert len(debugger.entries) == 1
        assert debugger.entries[0].action_id == 1

    def test_limits_history_to_max_entries(self):
        """Debugger should limit stored entries to configured maximum."""
        debugger = ConditionDebugger(debug_store=self.store, max_entries=3)

        for action_id in range(5):
            self._create_snapshot(action_id)
            self.store.record_condition_evaluation(action_id, "MoveUntil", False)

        debugger.update()
        assert len(debugger.entries) == 3  # limited to max_entries


class TestTimelineStrip:
    """Tests for the action timeline strip."""

    def setup_method(self):
        self.store = DebugDataStore()

    def test_builds_entries_from_events(self):
        """Timeline should build entries from recorded events."""
        # Action created and started at frame 1, stopped at frame 5
        self.store.update_frame(1, 0.1)
        self.store.record_event(
            "created",
            action_id=1,
            action_type="MoveUntil",
            target_id=99,
            target_type="Sprite",
            tag="movement",
        )
        self.store.record_event(
            "started",
            action_id=1,
            action_type="MoveUntil",
            target_id=99,
            target_type="Sprite",
            tag="movement",
        )

        self.store.update_frame(5, 0.5)
        self.store.record_event(
            "stopped",
            action_id=1,
            action_type="MoveUntil",
            target_id=99,
            target_type="Sprite",
            tag="movement",
        )

        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.action_id == 1
        assert entry.start_frame == 1
        assert entry.end_frame == 5
        assert entry.is_active is False

    def test_entry_marks_active_when_no_stop_event(self):
        """Timeline should mark entries as active when not yet stopped."""
        self.store.update_frame(2, 0.2)
        self.store.record_event(
            "created",
            action_id=2,
            action_type="RotateUntil",
            target_id=50,
            target_type="Sprite",
            tag=None,
        )
        self.store.record_event(
            "started",
            action_id=2,
            action_type="RotateUntil",
            target_id=50,
            target_type="Sprite",
            tag=None,
        )

        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.end_frame is None
        assert entry.is_active is True

    def test_filters_by_target(self):
        """Timeline should filter entries by target id."""
        self.store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        self.store.record_event("created", 2, "MoveUntil", 200, "Sprite")

        timeline = TimelineStrip(debug_store=self.store, filter_target_id=100)
        timeline.update()

        assert len(timeline.entries) == 1
        assert timeline.entries[0].target_id == 100
