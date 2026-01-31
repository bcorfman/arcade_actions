"""
Timeline strip for ACE visualizer.

Builds timeline entries from debug store events.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from arcadeactions.visualizer.instrumentation import DebugDataStore


class TimelineEntry:
    """Represents a single action on the timeline."""

    __slots__ = (
        "action_id",
        "action_type",
        "target_id",
        "target_type",
        "tag",
        "start_frame",
        "start_time",
        "end_frame",
        "end_time",
        "is_active",
    )

    def __init__(
        self,
        *,
        action_id: int,
        action_type: str,
        target_id: int | None,
        target_type: str | None,
        tag: str | None,
        start_frame: int | None,
        start_time: float | None,
        end_frame: int | None,
        end_time: float | None,
        is_active: bool,
    ) -> None:
        self.action_id = action_id
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = target_type
        self.tag = tag
        self.start_frame = start_frame
        self.start_time = start_time
        self.end_frame = end_frame
        self.end_time = end_time
        self.is_active = is_active


class TimelineStrip:
    """
    Builds timeline entries from action events recorded in the debug store.
    """

    def __init__(
        self,
        debug_store: DebugDataStore,
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
        # Cache of entries by action_id to persist state across updates
        # This prevents "flickering" when events are evicted from the ring buffer
        self._entry_cache: dict[int, TimelineEntry] = {}
        # Frame-skipping for performance: only update every N frames during heavy load
        self._last_update_frame = -1
        self._update_interval = 2  # Update every 2 frames (30 FPS update rate)

    def update(self) -> None:
        """Refresh entries from debug store events and active snapshots."""
        try:
            current_frame = self.debug_store.current_frame
            if self._should_skip_update(current_frame):
                return

            snapshots, snapshot_by_action, active_action_ids = self._build_snapshot_index()
            events = self._get_recent_events()

            self._update_cache_from_snapshots(snapshots)
            self._update_cache_from_events(events, snapshot_by_action, active_action_ids)

            entries = list(self._entry_cache.values())
            self._apply_fallback_start_frames(entries, current_frame, self.debug_store.current_time)

            entries = self._apply_filters(entries)
            entries = [entry for entry in entries if entry.is_active]
            entries.sort(key=lambda entry: (entry.start_frame or 0, entry.action_id))
            self.entries = entries[: self.max_entries]

            self._prune_inactive_entries()

        except Exception as e:
            # Defensive: catch any exceptions during update to prevent crashes
            # Log the error but don't crash the game
            import sys

            print(f"[ACE Timeline] Error during update: {e!r}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            # Keep existing entries on error to avoid blank timeline
            if not self.entries:
                self.entries = []

    def _should_skip_update(self, current_frame: int) -> bool:
        if self._last_update_frame >= 0 and current_frame - self._last_update_frame < self._update_interval:
            return True
        self._last_update_frame = current_frame
        return False

    def _build_snapshot_index(self) -> tuple[list[Any], dict[int, Any], set[int]]:
        snapshots = self.debug_store.get_all_snapshots()
        snapshot_by_action = self._index_snapshots_by_id(snapshots)
        active_action_ids = self._collect_active_action_ids(snapshots)
        return snapshots, snapshot_by_action, active_action_ids

    def _get_recent_events(self) -> list[Any]:
        max_events_to_process = 500
        all_events = list(self.debug_store.events)
        if len(all_events) > max_events_to_process:
            return all_events[-max_events_to_process:]
        return all_events

    def _index_snapshots_by_id(self, snapshots: list[Any]) -> dict[int, Any]:
        return {snapshot.action_id: snapshot for snapshot in snapshots if snapshot.action_id is not None}

    def _collect_active_action_ids(self, snapshots: list[Any]) -> set[int]:
        return {snapshot.action_id for snapshot in snapshots if snapshot.is_active}

    def _update_cache_from_snapshots(self, snapshots: list[Any]) -> None:
        for snapshot in snapshots:
            if snapshot is None or not snapshot.is_active:
                continue
            action_id = snapshot.action_id
            if action_id is None:
                continue

            entry = self._entry_cache.get(action_id)
            if entry:
                entry.is_active = True
                entry.end_frame = None
                entry.end_time = None
                continue

            self._entry_cache[action_id] = TimelineEntry(
                action_id=action_id,
                action_type=snapshot.action_type or "Unknown",
                target_id=snapshot.target_id if snapshot.target_id is not None else 0,
                target_type=snapshot.target_type or "Unknown",
                tag=snapshot.tag,
                start_frame=None,
                start_time=None,
                end_frame=None,
                end_time=None,
                is_active=True,
            )

    def _update_cache_from_events(
        self,
        events: list[Any],
        snapshot_by_action: dict[int, Any],
        active_action_ids: set[int],
    ) -> None:
        stopped_action_ids = self._collect_stopped_action_ids(events)
        for event in events:
            action_id = event.action_id
            if action_id is None:
                continue

            entry = self._entry_cache.get(action_id)
            if entry is None:
                entry = self._build_entry_from_event(event, snapshot_by_action, active_action_ids, stopped_action_ids)
                self._entry_cache[action_id] = entry

            self._apply_event_to_entry(entry, event, active_action_ids, stopped_action_ids)

    def _collect_stopped_action_ids(self, events: list[Any]) -> set[int]:
        return {
            event.action_id
            for event in events
            if event.event_type in {"stopped", "removed"} and event.action_id is not None
        }

    def _build_entry_from_event(
        self,
        event: Any,
        snapshot_by_action: dict[int, Any],
        active_action_ids: set[int],
        stopped_action_ids: set[int],
    ) -> TimelineEntry:
        snapshot = snapshot_by_action.get(event.action_id)
        is_active = event.action_id in active_action_ids or event.action_id not in stopped_action_ids
        return TimelineEntry(
            action_id=event.action_id,
            action_type=event.action_type or "Unknown",
            target_id=snapshot.target_id if snapshot else (event.target_id if event.target_id is not None else 0),
            target_type=snapshot.target_type if snapshot else (event.target_type or "Unknown"),
            tag=snapshot.tag if snapshot else event.tag,
            start_frame=None,
            start_time=None,
            end_frame=None,
            end_time=None,
            is_active=is_active,
        )

    def _apply_event_to_entry(
        self,
        entry: TimelineEntry,
        event: Any,
        active_action_ids: set[int],
        stopped_action_ids: set[int],
    ) -> None:
        if event.event_type in {"created", "started"}:
            if entry.start_frame is None:
                entry.start_frame = event.frame
                entry.start_time = event.timestamp
            if event.action_id in active_action_ids or event.action_id not in stopped_action_ids:
                entry.is_active = True
                entry.end_frame = None
                entry.end_time = None
            return

        if event.event_type in {"stopped", "removed"} and event.action_id not in active_action_ids:
            entry.is_active = False
            if entry.end_frame is None:
                entry.end_frame = event.frame
                entry.end_time = event.timestamp

    def _apply_fallback_start_frames(
        self, entries: list[TimelineEntry], current_frame: int, current_time: float
    ) -> None:
        for entry in entries:
            if entry.start_frame is None:
                entry.start_frame = current_frame
                entry.start_time = current_time

    def _apply_filters(self, entries: list[TimelineEntry]) -> list[TimelineEntry]:
        if self.filter_tag:
            entries = [entry for entry in entries if entry.tag == self.filter_tag]
        if self.filter_target_id is not None:
            entries = [entry for entry in entries if entry.target_id == self.filter_target_id]
        return entries

    def _prune_inactive_entries(self) -> None:
        inactive_ids = [aid for aid, entry in self._entry_cache.items() if not entry.is_active]
        for aid in inactive_ids:
            del self._entry_cache[aid]

    def clear(self) -> None:
        """Clear all entries."""
        self.entries = []
        self._entry_cache = {}
