"""Unit tests for visualizer instrumentation data store."""

from __future__ import annotations

from arcadeactions.visualizer.instrumentation import DebugDataStore


def test_record_event_created_indexes_and_stats() -> None:
    store = DebugDataStore(max_events=10)
    store.update_frame(3, 1.5)

    store.record_event(
        event_type="created",
        action_id=10,
        action_type="Move",
        target_id=7,
        target_type="Sprite",
        tag="player",
    )

    assert store.total_actions_created == 1
    assert store.actions_by_target[7] == [10]
    assert store.actions_by_tag["player"] == [10]


def test_record_event_removed_cleans_indices_and_snapshot() -> None:
    store = DebugDataStore(max_events=10)
    store.update_snapshot(
        action_id=5,
        action_type="Move",
        target_id=9,
        target_type="Sprite",
        is_active=True,
    )
    store.record_event(
        event_type="created",
        action_id=5,
        action_type="Move",
        target_id=9,
        target_type="Sprite",
        tag="enemy",
    )

    store.record_event(
        event_type="removed",
        action_id=5,
        action_type="Move",
        target_id=9,
        target_type="Sprite",
        tag="enemy",
    )

    assert 5 not in store.active_snapshots
    assert store.actions_by_target[9] == []
    assert store.actions_by_tag["enemy"] == []


def test_record_condition_updates_snapshot() -> None:
    store = DebugDataStore(max_events=10)
    store.update_snapshot(
        action_id=2,
        action_type="Rotate",
        target_id=1,
        target_type="Sprite",
        is_active=True,
    )

    store.record_condition_evaluation(
        action_id=2,
        action_type="Rotate",
        result=True,
        condition_str="angle >= 90",
    )

    snapshot = store.active_snapshots[2]
    assert snapshot.last_condition_result is True
    assert snapshot.condition_str == "angle >= 90"
    assert store.total_conditions_evaluated == 1


def test_update_snapshot_merges_metadata() -> None:
    store = DebugDataStore(max_events=10)
    store.update_snapshot(
        action_id=1,
        action_type="Move",
        target_id=4,
        target_type="Sprite",
        metadata={"a": 1},
        is_active=True,
    )

    store.update_snapshot(action_id=1, metadata={"b": 2})

    snapshot = store.active_snapshots[1]
    assert snapshot.metadata == {"a": 1, "b": 2}


def test_get_actions_for_target_and_tag() -> None:
    store = DebugDataStore(max_events=10)
    store.record_event(
        event_type="created",
        action_id=1,
        action_type="Move",
        target_id=10,
        target_type="Sprite",
        tag="a",
    )
    store.update_snapshot(
        action_id=1,
        action_type="Move",
        target_id=10,
        target_type="Sprite",
        is_active=True,
    )

    store.record_event(
        event_type="created",
        action_id=2,
        action_type="Rotate",
        target_id=10,
        target_type="Sprite",
        tag="b",
    )
    store.update_snapshot(
        action_id=2,
        action_type="Rotate",
        target_id=10,
        target_type="Sprite",
        is_active=True,
    )

    assert [snap.action_id for snap in store.get_actions_for_target(10)] == [1, 2]
    assert [snap.action_id for snap in store.get_actions_by_tag("a")] == [1]


def test_clear_resets_state() -> None:
    store = DebugDataStore(max_events=10)
    store.update_frame(5, 2.0)
    store.record_event(
        event_type="created",
        action_id=1,
        action_type="Move",
        target_id=2,
        target_type="Sprite",
    )
    store.record_condition_evaluation(
        action_id=1,
        action_type="Move",
        result=False,
    )
    store.update_snapshot(
        action_id=1,
        action_type="Move",
        target_id=2,
        target_type="Sprite",
        is_active=True,
    )

    store.clear()

    assert store.current_frame == 0
    assert store.current_time == 0.0
    assert list(store.events) == []
    assert list(store.evaluations) == []
    assert store.active_snapshots == {}
    assert store.actions_by_target == {}
    assert store.actions_by_tag == {}
    assert store.total_actions_created == 0
    assert store.total_conditions_evaluated == 0
