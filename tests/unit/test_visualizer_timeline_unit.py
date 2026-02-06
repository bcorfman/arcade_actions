"""Unit tests for TimelineStrip."""

from __future__ import annotations

import pytest

from arcadeactions.visualizer.timeline import TimelineStrip


class StubSnapshot:
    def __init__(
        self,
        *,
        action_id: int | None,
        action_type: str | None = None,
        target_id: int | None = None,
        target_type: str | None = None,
        tag: str | None = None,
        is_active: bool = True,
    ) -> None:
        self.action_id = action_id
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = target_type
        self.tag = tag
        self.is_active = is_active


class StubEvent:
    def __init__(
        self,
        *,
        event_type: str,
        action_id: int | None,
        action_type: str | None,
        target_id: int | None,
        target_type: str | None,
        tag: str | None,
        frame: int,
        timestamp: float,
    ) -> None:
        self.event_type = event_type
        self.action_id = action_id
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = target_type
        self.tag = tag
        self.frame = frame
        self.timestamp = timestamp


class StubStore:
    def __init__(self) -> None:
        self.current_frame = 0
        self.current_time = 0.0
        self.events: list[StubEvent] = []
        self._snapshots: list[StubSnapshot] = []

    def get_all_snapshots(self) -> list[StubSnapshot]:
        return list(self._snapshots)


def test_update_skips_when_frame_interval() -> None:
    store = StubStore()
    timeline = TimelineStrip(store)

    timeline.update()
    store.current_frame = 0
    timeline.update()

    assert timeline.entries == []


def test_update_builds_from_snapshot() -> None:
    store = StubStore()
    store._snapshots = [
        StubSnapshot(
            action_id=1,
            action_type="Move",
            target_id=3,
            target_type="Sprite",
            tag="t",
            is_active=True,
        )
    ]
    timeline = TimelineStrip(store)

    timeline.update()

    assert len(timeline.entries) == 1
    assert timeline.entries[0].action_id == 1


def test_update_processes_stop_event() -> None:
    store = StubStore()
    store._snapshots = []
    store.events = [
        StubEvent(
            event_type="created",
            action_id=2,
            action_type="Move",
            target_id=4,
            target_type="Sprite",
            tag=None,
            frame=1,
            timestamp=0.1,
        ),
        StubEvent(
            event_type="removed",
            action_id=2,
            action_type="Move",
            target_id=4,
            target_type="Sprite",
            tag=None,
            frame=2,
            timestamp=0.2,
        ),
    ]
    timeline = TimelineStrip(store)

    timeline.update()

    assert timeline.entries == []


def test_filter_tag_and_target() -> None:
    store = StubStore()
    store._snapshots = [
        StubSnapshot(action_id=1, action_type="Move", target_id=9, target_type="Sprite", tag="a"),
        StubSnapshot(action_id=2, action_type="Move", target_id=10, target_type="Sprite", tag="b"),
    ]
    timeline = TimelineStrip(store, filter_tag="a", filter_target_id=9)

    timeline.update()

    assert len(timeline.entries) == 1
    assert timeline.entries[0].action_id == 1


def test_fallback_start_frames() -> None:
    store = StubStore()
    store.current_frame = 5
    store.current_time = 0.5
    store._snapshots = [StubSnapshot(action_id=3, action_type="Move", target_id=1, target_type="Sprite", tag=None)]
    timeline = TimelineStrip(store)

    timeline.update()

    assert timeline.entries[0].start_frame == 5
    assert timeline.entries[0].start_time == 0.5
