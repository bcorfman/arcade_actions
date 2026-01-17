"""
Timeline strip for ACE visualizer.

Builds timeline entries from debug store events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore


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
            # Frame-skipping: only update every N frames to reduce CPU load during heavy action creation
            current_frame = self.debug_store.current_frame
            # Always update on first call or if enough frames have passed
            if self._last_update_frame >= 0 and current_frame - self._last_update_frame < self._update_interval:
                return  # Skip this frame
            self._last_update_frame = current_frame

            # Build snapshot map for contextual data
            snapshots = self.debug_store.get_all_snapshots()
            snapshot_by_action = {
                snapshot.action_id: snapshot for snapshot in snapshots if snapshot.action_id is not None
            }

            # Get set of active action IDs from snapshots (source of truth for what's currently active)
            active_action_ids = {snapshot.action_id for snapshot in snapshots if snapshot.is_active}

            # Process events in chronological order (deque stores in order)
            # Limit to most recent events to avoid processing thousands during heavy load
            # We only need recent events to fill in start_frame/end_frame for active actions
            max_events_to_process = 500  # Process at most 500 events per update
            all_events = list(self.debug_store.events)
            events = all_events[-max_events_to_process:] if len(all_events) > max_events_to_process else all_events

            # FIRST: Update cache from active snapshots
            # This ensures we have entries for actions even if their "created" events were evicted
            for snapshot in snapshots:
                # Defensive checks: skip invalid snapshots
                if snapshot is None or not snapshot.is_active:
                    continue  # Skip inactive or invalid snapshots

                action_id = snapshot.action_id
                # Defensive check: skip snapshots with invalid action_id
                if action_id is None:
                    continue

                entry = self._entry_cache.get(action_id)
                if entry:
                    # Update existing entry
                    entry.is_active = True
                    entry.end_frame = None
                    entry.end_time = None
                    # Don't touch start_frame if it's already set - preserve history!
                else:
                    # Create new entry
                    entry = TimelineEntry(
                        action_id=action_id,
                        action_type=snapshot.action_type or "Unknown",
                        target_id=snapshot.target_id if snapshot.target_id is not None else 0,
                        target_type=snapshot.target_type or "Unknown",
                        tag=snapshot.tag,
                        start_frame=None,  # Will be filled from events if available, or current_frame as fallback
                        start_time=None,
                        end_frame=None,
                        end_time=None,
                        is_active=True,
                    )
                    self._entry_cache[action_id] = entry

            # SECOND: Process events to fill in historical data and handle removed actions
            # First, collect all stopped/removed action IDs (for inferring active state when no snapshot exists)
            stopped_action_ids: set[int] = {
                event.action_id
                for event in events
                if event.event_type in {"stopped", "removed"} and event.action_id is not None
            }

            for event in events:
                # Defensive check: skip events with invalid action_id
                if event.action_id is None:
                    continue

                entry = self._entry_cache.get(event.action_id)

                # If entry doesn't exist, create it (this handles cases where snapshot was removed
                # but we still have events in the ring buffer)
                if entry is None:
                    snapshot = snapshot_by_action.get(event.action_id)
                    # If no snapshot, infer active state from events (will be updated as we process events)
                    # Default to active if we haven't seen a stop/remove event yet
                    is_active = event.action_id in active_action_ids or event.action_id not in stopped_action_ids
                    entry = TimelineEntry(
                        action_id=event.action_id,
                        action_type=event.action_type or "Unknown",
                        target_id=snapshot.target_id
                        if snapshot
                        else (event.target_id if event.target_id is not None else 0),
                        target_type=snapshot.target_type if snapshot else (event.target_type or "Unknown"),
                        tag=snapshot.tag if snapshot else event.tag,
                        start_frame=None,
                        start_time=None,
                        end_frame=None,
                        end_time=None,
                        is_active=is_active,
                    )
                    self._entry_cache[event.action_id] = entry

                # Update start/end based on event type
                if event.event_type in {"created", "started"}:
                    if entry.start_frame is None:
                        entry.start_frame = event.frame
                        entry.start_time = event.timestamp
                    # If action is currently active (has snapshot), ensure entry is marked as active
                    if event.action_id in active_action_ids or event.action_id not in stopped_action_ids:
                        entry.is_active = True
                        entry.end_frame = None
                        entry.end_time = None
                elif event.event_type in {"stopped", "removed"}:
                    # Only mark as inactive/remove if action is not currently active
                    # This handles cases where action was stopped but then restarted,
                    # or where we see a "removed" event but the action is still active
                    if event.action_id not in active_action_ids:
                        entry.is_active = False
                        if entry.end_frame is None:
                            entry.end_frame = event.frame
                            entry.end_time = event.timestamp

            # Convert cache to list
            entries = list(self._entry_cache.values())

            # Set fallback start_frame for entries that don't have one (so renderer can display them)
            # This handles cases where "created" events were evicted from the ring buffer
            # Crucially, we only do this ONCE per entry if it's None, and then it's persisted in cache
            current_time = self.debug_store.current_time
            for entry in entries:
                if entry.start_frame is None:
                    entry.start_frame = current_frame
                    entry.start_time = current_time

            if self.filter_tag:
                entries = [entry for entry in entries if entry.tag == self.filter_tag]
            if self.filter_target_id is not None:
                entries = [entry for entry in entries if entry.target_id == self.filter_target_id]

            # Show ONLY active entries to match the overlay display
            active_entries = [e for e in entries if e.is_active]

            # Sort by start frame (earliest first), then by action_id for consistent ordering
            active_entries.sort(key=lambda e: (e.start_frame or 0, e.action_id))

            self.entries = active_entries[: self.max_entries]

            # Prune cache aggressively - keep only active actions
            # Since we only display active actions, remove all inactive entries from cache
            keys_to_remove = []
            for aid, entry in self._entry_cache.items():
                if not entry.is_active:
                    keys_to_remove.append(aid)

            for aid in keys_to_remove:
                del self._entry_cache[aid]

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

    def clear(self) -> None:
        """Clear all entries."""
        self.entries = []
        self._entry_cache = {}
