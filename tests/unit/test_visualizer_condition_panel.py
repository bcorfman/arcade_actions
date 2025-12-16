"""Unit tests for condition panel debugger."""

from __future__ import annotations

import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.condition_panel import ConditionDebugger, ConditionEntry


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


class TestConditionDebugger:
    def test_init(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        assert debugger.debug_store is debug_store
        assert debugger.max_entries == 50
        assert debugger.filter_tag is None
        assert debugger.entries == []

    def test_init_with_filter(self, debug_store):
        debugger = ConditionDebugger(debug_store, filter_tag="movement")
        assert debugger.filter_tag == "movement"

    def test_init_with_max_entries(self, debug_store):
        debugger = ConditionDebugger(debug_store, max_entries=100)
        assert debugger.max_entries == 100

    def test_update_no_evaluations(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        debugger.update()
        assert debugger.entries == []

    def test_update_with_evaluation_no_snapshot(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            condition_str="lambda: True",
        )
        debugger.update()
        # Entry should be skipped because no snapshot exists
        assert len(debugger.entries) == 0

    def test_update_with_evaluation_and_snapshot(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            condition_str="lambda: True",
        )
        debugger.update()
        assert len(debugger.entries) == 1
        entry = debugger.entries[0]
        assert entry.action_id == 1
        assert entry.action_type == "MoveUntil"
        assert entry.result is True
        assert entry.tag == "test"
        assert entry.target_id == 100

    def test_update_filters_by_tag(self, debug_store):
        debugger = ConditionDebugger(debug_store, filter_tag="movement")
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
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
        )
        debug_store.record_condition_evaluation(
            action_id=2,
            action_type="RotateUntil",
            result=False,
        )
        debugger.update()
        assert len(debugger.entries) == 1
        assert debugger.entries[0].action_id == 1

    def test_update_respects_max_entries(self, debug_store):
        debugger = ConditionDebugger(debug_store, max_entries=2)
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
            debug_store.record_condition_evaluation(
                action_id=i,
                action_type="MoveUntil",
                result=True,
            )
        debugger.update()
        assert len(debugger.entries) == 2

    def test_update_with_variables(self, debug_store):
        debugger = ConditionDebugger(debug_store)
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
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            x=10,
            y=20,
        )
        debugger.update()
        assert len(debugger.entries) == 1
        entry = debugger.entries[0]
        assert entry.variables == {"x": 10, "y": 20}

    def test_update_removed_action_skipped(self, debug_store):
        debugger = ConditionDebugger(debug_store)
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
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
        )
        # Remove the action
        debug_store.record_event("removed", 1, "MoveUntil", 100, "Sprite")
        debugger.update()
        # Entry should be skipped because snapshot was removed
        assert len(debugger.entries) == 0

    def test_clear(self, debug_store):
        debugger = ConditionDebugger(debug_store)
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
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
        )
        debugger.update()
        assert len(debugger.entries) == 1
        debugger.clear()
        assert debugger.entries == []

    def test_update_multiple_evaluations_same_action(self, debug_store):
        debugger = ConditionDebugger(debug_store)
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
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=False,
        )
        debug_store.update_frame(2, 0.032)
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
        )
        debugger.update()
        # Should get most recent evaluations (newest first)
        assert len(debugger.entries) >= 1


class TestConditionEntry:
    def test_entry_creation(self):
        entry = ConditionEntry(
            action_id=1,
            action_type="MoveUntil",
            frame=10,
            timestamp=0.16,
            result=True,
            condition_str="lambda: True",
            variables={"x": 10},
            tag="test",
            target_id=100,
            target_type="Sprite",
        )
        assert entry.action_id == 1
        assert entry.action_type == "MoveUntil"
        assert entry.frame == 10
        assert entry.timestamp == 0.16
        assert entry.result is True
        assert entry.condition_str == "lambda: True"
        assert entry.variables == {"x": 10}
        assert entry.tag == "test"
        assert entry.target_id == 100
        assert entry.target_type == "Sprite"

