"""Unit tests for timeline strip."""

from __future__ import annotations

import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.timeline import TimelineEntry, TimelineStrip


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


class TestTimelineStrip:
    def test_init(self, debug_store):
        timeline = TimelineStrip(debug_store)
        assert timeline.debug_store is debug_store
        assert timeline.max_entries == 100
        assert timeline.filter_tag is None
        assert timeline.filter_target_id is None
        assert timeline.entries == []
        assert timeline._entry_cache == {}

    def test_init_with_filters(self, debug_store):
        timeline = TimelineStrip(debug_store, filter_tag="movement", filter_target_id=100)
        assert timeline.filter_tag == "movement"
        assert timeline.filter_target_id == 100

    def test_init_with_max_entries(self, debug_store):
        timeline = TimelineStrip(debug_store, max_entries=50)
        assert timeline.max_entries == 50

    def test_update_no_snapshots(self, debug_store):
        timeline = TimelineStrip(debug_store)
        timeline.update()
        assert timeline.entries == []

    def test_update_with_active_snapshot(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.action_id == 1
        assert entry.action_type == "MoveUntil"
        assert entry.target_id == 100
        assert entry.is_active is True

    def test_update_filters_by_tag(self, debug_store):
        timeline = TimelineStrip(debug_store, filter_tag="movement")
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        debug_store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag="rotation",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        timeline.update()
        assert len(timeline.entries) == 1
        assert timeline.entries[0].action_id == 1

    def test_update_filters_by_target_id(self, debug_store):
        timeline = TimelineStrip(debug_store, filter_target_id=100)
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 1
        assert timeline.entries[0].target_id == 100

    def test_update_with_events(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        assert entry.start_frame == 1

    def test_update_with_stopped_action(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        debug_store.update_snapshot(
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
        debug_store.update_frame(10, 0.16)
        debug_store.record_event("stopped", 1, "MoveUntil", 100, "Sprite")
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=False,  # Now inactive
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        timeline.update()
        # Stopped actions should not appear in active entries
        assert len(timeline.entries) == 0

    def test_update_respects_max_entries(self, debug_store):
        timeline = TimelineStrip(debug_store, max_entries=2)
        for i in range(5):
            debug_store.update_snapshot(
                action_id=i,
                action_type="MoveUntil",
                target_id=100 + i,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
            )
        timeline.update()
        assert len(timeline.entries) <= 2

    def test_update_frame_skipping(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.update_snapshot(
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
        timeline.update()
        first_update_frame = timeline._last_update_frame

        # Update frame but not enough to trigger update
        debug_store.update_frame(2, 0.032)
        timeline.update()
        # Should skip update if not enough frames passed
        assert timeline._last_update_frame == first_update_frame

    def test_update_sorts_by_start_frame(self, debug_store):
        timeline = TimelineStrip(debug_store)
        # Create actions in reverse order
        debug_store.update_frame(10, 0.16)
        debug_store.record_event("created", 2, "MoveUntil", 200, "Sprite")
        debug_store.update_snapshot(
            action_id=2,
            action_type="MoveUntil",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        debug_store.update_frame(5, 0.08)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 2
        # Should be sorted by start_frame
        assert timeline.entries[0].start_frame <= timeline.entries[1].start_frame

    def test_update_handles_missing_start_frame(self, debug_store):
        timeline = TimelineStrip(debug_store)
        # Create snapshot without event
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 1
        entry = timeline.entries[0]
        # Should have fallback start_frame
        assert entry.start_frame is not None

    def test_update_handles_exception(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        # Make get_all_snapshots raise an exception
        original_get = debug_store.get_all_snapshots
        call_count = []

        def failing_get():
            call_count.append(True)
            if len(call_count) == 1:
                raise RuntimeError("boom")
            return original_get()

        monkeypatch.setattr(debug_store, "get_all_snapshots", failing_get)
        timeline.update()
        # Should handle exception gracefully
        assert isinstance(timeline.entries, list)

    def test_clear(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline.entries) == 1
        timeline.clear()
        assert timeline.entries == []
        assert timeline._entry_cache == {}

    def test_update_prunes_inactive_entries(self, debug_store):
        timeline = TimelineStrip(debug_store)
        debug_store.update_snapshot(
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
        timeline.update()
        assert len(timeline._entry_cache) == 1

        # Mark action as stopped and remove snapshot
        debug_store.update_frame(10, 0.16)
        debug_store.record_event("stopped", 1, "MoveUntil", 100, "Sprite")
        debug_store.record_event("removed", 1, "MoveUntil", 100, "Sprite")
        debug_store.active_snapshots.pop(1, None)
        timeline.update()
        # Cache should be pruned since entry is inactive and not in active snapshots
        # Timeline only shows active entries, so inactive ones are pruned
        assert len(timeline.entries) == 0  # No active entries shown


class TestTimelineEntry:
    def test_entry_creation(self):
        entry = TimelineEntry(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            start_frame=10,
            start_time=0.16,
            end_frame=None,
            end_time=None,
            is_active=True,
        )
        assert entry.action_id == 1
        assert entry.action_type == "MoveUntil"
        assert entry.target_id == 100
        assert entry.target_type == "Sprite"
        assert entry.tag == "test"
        assert entry.start_frame == 10
        assert entry.start_time == 0.16
        assert entry.end_frame is None
        assert entry.end_time is None
        assert entry.is_active is True
