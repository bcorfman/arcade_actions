"""Snapshot exporter for ACE visualizer."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot, ActionEvent, ConditionEvaluation


class SnapshotExporter:
    """Exports current debug store state to JSON snapshots."""

    def __init__(self, debug_store: "DebugDataStore", directory: Path) -> None:
        self.debug_store = debug_store
        self.directory = Path(directory)

    def export(self) -> Path:
        """Write a snapshot JSON file and return its path."""
        self.directory.mkdir(parents=True, exist_ok=True)

        data = {
            "stats": self.debug_store.get_statistics(),
            "snapshots": [self._serialize_snapshot(snapshot) for snapshot in self.debug_store.get_all_snapshots()],
            "events": [self._serialize_event(event) for event in self.debug_store.get_recent_events()],
            "evaluations": [
                self._serialize_evaluation(evaluation) for evaluation in self.debug_store.get_recent_evaluations()
            ],
        }

        filename = f"snapshot_{int(time.time() * 1000)}.json"
        path = self.directory / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, default=str)
        return path

    @staticmethod
    def _serialize_snapshot(snapshot: "ActionSnapshot") -> dict[str, Any]:
        return {
            "action_id": snapshot.action_id,
            "action_type": snapshot.action_type,
            "target_id": snapshot.target_id,
            "target_type": snapshot.target_type,
            "tag": snapshot.tag,
            "is_active": snapshot.is_active,
            "is_paused": snapshot.is_paused,
            "factor": snapshot.factor,
            "elapsed": snapshot.elapsed,
            "progress": snapshot.progress,
            "velocity": SnapshotExporter._safe_value(snapshot.velocity),
            "bounds": SnapshotExporter._safe_value(snapshot.bounds),
            "boundary_state": SnapshotExporter._safe_value(snapshot.boundary_state),
            "last_condition_result": SnapshotExporter._safe_value(snapshot.last_condition_result),
            "condition_str": snapshot.condition_str,
            "metadata": SnapshotExporter._safe_mapping(snapshot.metadata),
        }

    @staticmethod
    def _serialize_event(event: "ActionEvent") -> dict[str, Any]:
        return {
            "frame": event.frame,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "action_id": event.action_id,
            "action_type": event.action_type,
            "target_id": event.target_id,
            "target_type": event.target_type,
            "tag": event.tag,
            "details": SnapshotExporter._safe_mapping(event.details),
        }

    @staticmethod
    def _serialize_evaluation(evaluation: "ConditionEvaluation") -> dict[str, Any]:
        return {
            "frame": evaluation.frame,
            "timestamp": evaluation.timestamp,
            "action_id": evaluation.action_id,
            "action_type": evaluation.action_type,
            "result": SnapshotExporter._safe_value(evaluation.result),
            "condition_str": evaluation.condition_str,
            "variables": SnapshotExporter._safe_mapping(evaluation.variables),
        }

    @staticmethod
    def _safe_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [SnapshotExporter._safe_value(item) for item in value]
        if isinstance(value, dict):
            return SnapshotExporter._safe_mapping(value)
        try:
            return snapshot_repr(value)  # type: ignore[name-defined]
        except NameError:
            pass
        return repr(value)

    @staticmethod
    def _safe_mapping(mapping: dict | None) -> dict[str, Any] | None:
        if mapping is None:
            return None
        safe: dict[str, Any] = {}
        for key, value in mapping.items():
            safe[str(key)] = SnapshotExporter._safe_value(value)
        return safe


def snapshot_repr(obj: Any) -> str:
    """Return a concise string for non-serializable objects."""
    cls = type(obj)
    name = getattr(obj, "name", None)
    if isinstance(name, str):
        return f"<{cls.__module__}.{cls.__name__} name={name!r}>"
    return f"<{cls.__module__}.{cls.__name__}>"
