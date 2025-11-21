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
            snapshot_dict = asdict(snapshot)
            snapshot_dict["target_name"] = target_names.get(snapshot.target_id)
            snapshot_entries.append(snapshot_dict)

        event_entries: list[dict[str, object]] = []
        for event in self.debug_store.get_recent_events():
            event_dict = asdict(event)
            event_dict["target_name"] = target_names.get(event.target_id)
            event_entries.append(event_dict)

        data = {
            "stats": self.debug_store.get_statistics(),
            "target_names": target_names,
            "snapshots": snapshot_entries,
            "events": event_entries,
            "evaluations": [asdict(evaluation) for evaluation in self.debug_store.get_recent_evaluations()],
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
