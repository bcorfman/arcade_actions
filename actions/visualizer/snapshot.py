"""Snapshot exporter for ACE visualizer."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot, ActionEvent, ConditionEvaluation


class SnapshotExporter:
    """Exports current debug store state to JSON snapshots."""

    def __init__(
        self,
        debug_store: "DebugDataStore",
        directory: Path,
        *,
        target_names_provider: Callable[[], dict[int, str]] | None = None,
    ) -> None:
        self.debug_store = debug_store
        self.directory = Path(directory)
        self._target_names_provider = target_names_provider

    def export(self) -> Path:
        """Write a snapshot JSON file and return its path."""
        self.directory.mkdir(parents=True, exist_ok=True)

        target_names = self._collect_target_names()

        snapshot_entries: list[dict[str, object]] = []
        for snapshot in self.debug_store.get_all_snapshots():
            try:
                snapshot_dict = asdict(snapshot)
            except (NotImplementedError, TypeError) as e:
                # Handle sprites that don't support deep copying
                # Convert manually, skipping problematic fields
                snapshot_dict = {
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
                    "velocity": snapshot.velocity,
                    "bounds": snapshot.bounds,
                    "boundary_state": None if snapshot.boundary_state is None else dict(snapshot.boundary_state),
                    "last_condition_result": str(snapshot.last_condition_result)
                    if snapshot.last_condition_result is not None
                    else None,
                    "condition_str": snapshot.condition_str,
                    "metadata": f"<unable to serialize: {type(e).__name__}>",
                }
            snapshot_dict["target_name"] = target_names.get(snapshot.target_id)
            snapshot_entries.append(snapshot_dict)

        event_entries: list[dict[str, object]] = []
        for event in self.debug_store.get_recent_events():
            try:
                event_dict = asdict(event)
            except (NotImplementedError, TypeError):
                # Handle events with non-serializable details
                event_dict = {
                    "frame": event.frame,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "action_id": event.action_id,
                    "action_type": event.action_type,
                    "target_id": event.target_id,
                    "target_type": event.target_type,
                    "tag": event.tag,
                    "details": "<unable to serialize>",
                }
            event_dict["target_name"] = target_names.get(event.target_id)
            event_entries.append(event_dict)

        evaluation_entries: list[dict[str, object]] = []
        for evaluation in self.debug_store.get_recent_evaluations():
            try:
                evaluation_dict = asdict(evaluation)
            except (NotImplementedError, TypeError):
                # Handle evaluations with non-serializable variables
                evaluation_dict = {
                    "frame": evaluation.frame,
                    "timestamp": evaluation.timestamp,
                    "action_id": evaluation.action_id,
                    "action_type": evaluation.action_type,
                    "result": str(evaluation.result),
                    "condition_str": evaluation.condition_str,
                    "variables": "<unable to serialize>",
                }
            evaluation_entries.append(evaluation_dict)

        data = {
            "stats": self.debug_store.get_statistics(),
            "target_names": target_names,
            "snapshots": snapshot_entries,
            "events": event_entries,
            "evaluations": evaluation_entries,
        }

        filename = f"snapshot_{int(time.time() * 1000)}.json"
        path = self.directory / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, default=str)
        return path

    def _collect_target_names(self) -> dict[int, str]:
        """Safely collect target names from the provided callable."""
        if self._target_names_provider is None:
            return {}
        try:
            names = self._target_names_provider() or {}
        except Exception:
            return {}

        # Ensure keys are integers so they line up with stored target_ids.
        normalized: dict[int, str] = {}
        for key, value in names.items():
            try:
                normalized[int(key)] = str(value)
            except (TypeError, ValueError):
                continue
        return normalized
