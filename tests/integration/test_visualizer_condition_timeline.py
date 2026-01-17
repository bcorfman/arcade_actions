"""
Tests for condition debugger panel and action timeline strip.

Ensures data collection and filtering logic works for condition evaluations
and timeline entries derived from debug instrumentation.
"""

from __future__ import annotations

from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.instrumentation import DebugDataStore
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

        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        # Active action should appear in timeline
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.action_id == 1
        assert entry.start_frame == 1
        assert entry.is_active is True

        # When stopped, action should be removed from timeline
        self.store.update_frame(5, 0.5)
        self.store.record_event(
            "stopped",
            action_id=1,
            action_type="MoveUntil",
            target_id=99,
            target_type="Sprite",
            tag="movement",
        )

        timeline.update()
        # Stopped actions are immediately removed from timeline to match overlay behavior
        # The timeline only shows active actions to stay in sync with the overlay
        assert len(timeline.entries) == 0

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

    def test_shows_active_snapshots_without_events(self):
        """Timeline should show active snapshots even if their events were evicted from ring buffer."""
        # Create a snapshot without any events (simulating events being evicted)
        self.store.update_snapshot(
            action_id=42,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=1.5,
            progress=0.25,
        )

        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        # Should show the active snapshot even though there are no events
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.action_id == 42
        assert entry.is_active is True
        assert entry.action_type == "MoveUntil"
        assert entry.tag == "movement"

    def test_shows_active_actions_despite_removed_events(self):
        """Timeline should show active actions even if a 'removed' event exists in history."""
        # Simulate an action that was stopped but then restarted (or event was stale)
        self.store.update_frame(10, 1.0)
        self.store.record_event("created", 100, "MoveUntil", 200, "Sprite", tag="test")
        self.store.record_event("started", 100, "MoveUntil", 200, "Sprite", tag="test")

        # Action was "removed" at some point
        self.store.update_frame(20, 2.0)
        self.store.record_event("removed", 100, "MoveUntil", 200, "Sprite", tag="test")

        # But now it's active again (snapshot exists)
        self.store.update_frame(30, 3.0)
        self.store.update_snapshot(
            action_id=100,
            action_type="MoveUntil",
            target_id=200,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.25,
        )

        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        # Should show the active action despite the "removed" event
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.action_id == 100
        assert entry.is_active is True
        assert entry.start_frame == 10  # Should have start frame from event
        assert entry.end_frame is None  # Should not have end frame since it's active

    def test_persists_start_frame_after_event_eviction(self):
        """Timeline should remember start_frame even after 'created' event is evicted."""
        # 1. Create action with event
        self.store.update_frame(100, 1.0)
        self.store.record_event("created", 999, "MoveUntil", 10, "Sprite")

        # 2. Update timeline - should see start_frame=100
        timeline = TimelineStrip(debug_store=self.store)
        timeline.update()

        assert len(timeline.entries) == 1
        assert timeline.entries[0].start_frame == 100

        # 3. Clear events (simulate eviction)
        self.store.events.clear()

        # 4. Create snapshot to keep action active
        self.store.update_frame(200, 2.0)
        self.store.update_snapshot(
            action_id=999,
            action_type="MoveUntil",
            target_id=10,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=1.0,
            progress=0.5,
        )

        # 5. Update timeline again
        timeline.update()

        # 6. Should still have start_frame=100 (cached), not current frame 200
        assert len(timeline.entries) == 1
        assert timeline.entries[0].start_frame == 100
