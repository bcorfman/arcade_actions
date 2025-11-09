"""Snapshot exporter for ACE visualizer."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

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
            "snapshots": [asdict(snapshot) for snapshot in self.debug_store.get_all_snapshots()],
            "events": [asdict(event) for event in self.debug_store.get_recent_events()],
            "evaluations": [asdict(evaluation) for evaluation in self.debug_store.get_recent_evaluations()],
        }

        filename = f"snapshot_{int(time.time() * 1000)}.json"
        path = self.directory / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, default=str)
        return path
