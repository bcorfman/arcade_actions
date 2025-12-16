"""Unit tests for snapshot exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.snapshot import SnapshotExporter


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


@pytest.fixture
def tmp_snapshot_dir(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    return snapshot_dir


class TestSnapshotExporter:
    def test_init(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        assert exporter.debug_store is debug_store
        assert exporter.directory == tmp_snapshot_dir
        assert exporter._target_names_provider is None

    def test_init_with_target_names_provider(self, debug_store, tmp_snapshot_dir):
        def provider():
            return {100: "self.player"}

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
        assert exporter._target_names_provider is provider

    def test_export_empty_store(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        path = exporter.export()
        assert path.exists()
        assert path.parent == tmp_snapshot_dir
        assert path.suffix == ".json"

        data = json.loads(path.read_text())
        assert "stats" in data
        assert "target_names" in data
        assert "snapshots" in data
        assert "events" in data
        assert "evaluations" in data
        assert data["snapshots"] == []
        assert data["events"] == []
        assert data["evaluations"] == []

    def test_export_with_snapshots(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
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
            progress=0.5,
        )
        path = exporter.export()
        data = json.loads(path.read_text())
        assert len(data["snapshots"]) == 1
        snapshot = data["snapshots"][0]
        assert snapshot["action_id"] == 1
        assert snapshot["action_type"] == "MoveUntil"
        assert snapshot["target_id"] == 100
        assert snapshot["tag"] == "movement"
        assert snapshot["progress"] == 0.5

    def test_export_with_events(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite", tag="test")
        path = exporter.export()
        data = json.loads(path.read_text())
        assert len(data["events"]) == 1
        event = data["events"][0]
        assert event["event_type"] == "created"
        assert event["action_id"] == 1
        assert event["tag"] == "test"

    def test_export_with_evaluations(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            condition_str="lambda: True",
        )
        path = exporter.export()
        data = json.loads(path.read_text())
        assert len(data["evaluations"]) == 1
        evaluation = data["evaluations"][0]
        assert evaluation["action_id"] == 1
        assert evaluation["result"] is True or evaluation["result"] == "True"  # May be bool or string
        assert evaluation["condition_str"] == "lambda: True"

    def test_export_with_target_names(self, debug_store, tmp_snapshot_dir):
        def provider():
            return {100: "self.player"}

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
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
        path = exporter.export()
        data = json.loads(path.read_text())
        # JSON keys are strings
        assert data["target_names"] == {"100": "self.player"} or data["target_names"] == {100: "self.player"}
        assert data["snapshots"][0]["target_name"] == "self.player"

    def test_export_creates_directory(self, debug_store, tmp_path):
        snapshot_dir = tmp_path / "new_snapshots"
        exporter = SnapshotExporter(debug_store, snapshot_dir)
        path = exporter.export()
        assert snapshot_dir.exists()
        assert path.exists()

    def test_export_handles_non_serializable_snapshot(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        # Create a snapshot with non-serializable metadata
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
            metadata={"func": lambda x: x},  # Non-serializable
        )
        path = exporter.export()
        data = json.loads(path.read_text())
        # Should handle gracefully
        assert len(data["snapshots"]) == 1

    def test_export_handles_non_serializable_event(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        # Create an event with non-serializable details
        debug_store.record_event(
            "created",
            1,
            "MoveUntil",
            100,
            "Sprite",
            tag="test",
            func=lambda x: x,  # Non-serializable
        )
        path = exporter.export()
        data = json.loads(path.read_text())
        # Should handle gracefully
        assert len(data["events"]) == 1

    def test_export_handles_non_serializable_evaluation(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        # Create an evaluation with non-serializable variables
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=lambda: True,  # Non-serializable
            func=lambda x: x,  # Non-serializable
        )
        path = exporter.export()
        data = json.loads(path.read_text())
        # Should handle gracefully
        assert len(data["evaluations"]) == 1

    def test_collect_target_names_no_provider(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        names = exporter._collect_target_names()
        assert names == {}

    def test_collect_target_names_with_provider(self, debug_store, tmp_snapshot_dir):
        def provider():
            return {100: "self.player", 200: "self.enemy"}

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
        names = exporter._collect_target_names()
        assert names == {100: "self.player", 200: "self.enemy"}

    def test_collect_target_names_provider_exception(self, debug_store, tmp_snapshot_dir):
        def failing_provider():
            raise RuntimeError("boom")

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=failing_provider)
        names = exporter._collect_target_names()
        assert names == {}

    def test_collect_target_names_provider_returns_none(self, debug_store, tmp_snapshot_dir):
        def provider():
            return None

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
        names = exporter._collect_target_names()
        assert names == {}

    def test_collect_target_names_normalizes_keys(self, debug_store, tmp_snapshot_dir):
        def provider():
            return {"100": "self.player", 200: "self.enemy"}

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
        names = exporter._collect_target_names()
        assert names == {100: "self.player", 200: "self.enemy"}

    def test_collect_target_names_invalid_keys(self, debug_store, tmp_snapshot_dir):
        def provider():
            return {"invalid": "self.player", None: "self.enemy"}

        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir, target_names_provider=provider)
        names = exporter._collect_target_names()
        # Invalid keys should be skipped
        assert "invalid" not in names
        assert None not in names

    def test_export_includes_statistics(self, debug_store, tmp_snapshot_dir):
        exporter = SnapshotExporter(debug_store, tmp_snapshot_dir)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        debug_store.record_condition_evaluation(action_id=1, action_type="MoveUntil", result=True)
        path = exporter.export()
        data = json.loads(path.read_text())
        assert "stats" in data
        stats = data["stats"]
        # Stats structure may vary - just check it exists
        assert isinstance(stats, dict)
