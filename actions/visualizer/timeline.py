"""
Timeline strip for ACE visualizer.

Builds timeline entries from debug store events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot, ActionEvent


@dataclass(slots=True)
class TimelineEntry:
    """Represents a single action on the timeline."""

    action_id: int
    action_type: str
    target_id: int | None
    target_type: str | None
    tag: str | None
    start_frame: int | None
    start_time: float | None
    end_frame: int | None
    end_time: float | None
    is_active: bool


class TimelineStrip:
    """
    Builds timeline entries from action events recorded in the debug store.
    """

    def __init__(
        self,
        debug_store: "DebugDataStore",
        *,
        max_entries: int = 100,
        filter_tag: str | None = None,
        filter_target_id: int | None = None,
    ) -> None:
        """
        Initialize the timeline strip.

        Args:
            debug_store: Injected debug data store
            max_entries: Maximum number of timeline entries
            filter_tag: Optional tag filter
            filter_target_id: Optional target filter
        """
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.filter_tag = filter_tag
        self.filter_target_id = filter_target_id
        self.entries: list[TimelineEntry] = []

    def update(self) -> None:
        """Refresh entries from debug store events."""
        # Build snapshot map for contextual data
        snapshots = self.debug_store.get_all_snapshots()
        snapshot_by_action = {snapshot.action_id: snapshot for snapshot in snapshots}

        # Process events in chronological order (deque stores in order)
        events = list(self.debug_store.events)

        entries_by_action: dict[int, TimelineEntry] = {}

        for event in events:
            entry = entries_by_action.get(event.action_id)
            if entry is None:
                snapshot = snapshot_by_action.get(event.action_id)
                entry = TimelineEntry(
                    action_id=event.action_id,
                    action_type=event.action_type,
                    target_id=snapshot.target_id if snapshot else event.target_id,
                    target_type=snapshot.target_type if snapshot else event.target_type,
                    tag=snapshot.tag if snapshot else event.tag,
                    start_frame=None,
                    start_time=None,
                    end_frame=None,
                    end_time=None,
                    is_active=True,
                )
                entries_by_action[event.action_id] = entry

            # Update start/end based on event type
            if event.event_type in {"created", "started"}:
                if entry.start_frame is None:
                    entry.start_frame = event.frame
                    entry.start_time = event.timestamp
            elif event.event_type in {"stopped", "removed"}:
                entry.end_frame = event.frame
                entry.end_time = event.timestamp
                entry.is_active = False
                entries_by_action.pop(event.action_id, None)
                continue

        # Convert to list respecting filters
        entries = list(entries_by_action.values())

        if self.filter_tag:
            entries = [entry for entry in entries if entry.tag == self.filter_tag]
        if self.filter_target_id is not None:
            entries = [entry for entry in entries if entry.target_id == self.filter_target_id]

        # Sort by start frame (earliest first)
        entries.sort(key=lambda e: (e.start_frame or 0, e.action_id))

        self.entries = entries[: self.max_entries]

    def clear(self) -> None:
        """Clear all entries."""
        self.entries = []
