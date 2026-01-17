"""
Condition debugger panel for ACE visualizer.

Collects recent condition evaluations and formats them for display.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore


class ConditionEntry:
    """Represents a single condition evaluation entry."""

    __slots__ = (
        "action_id",
        "action_type",
        "frame",
        "timestamp",
        "result",
        "condition_str",
        "variables",
        "tag",
        "target_id",
        "target_type",
    )

    def __init__(
        self,
        *,
        action_id: int,
        action_type: str,
        frame: int,
        timestamp: float,
        result: Any,
        condition_str: str | None,
        variables: dict[str, Any],
        tag: str | None,
        target_id: int | None,
        target_type: str | None,
    ) -> None:
        self.action_id = action_id
        self.action_type = action_type
        self.frame = frame
        self.timestamp = timestamp
        self.result = result
        self.condition_str = condition_str
        self.variables = variables
        self.tag = tag
        self.target_id = target_id
        self.target_type = target_type


class ConditionDebugger:
    """
    Collects condition evaluation history for display in the overlay.

    Uses dependency injection to receive a DebugDataStore instance.
    """

    def __init__(
        self,
        debug_store: DebugDataStore,
        *,
        max_entries: int = 50,
        filter_tag: str | None = None,
    ) -> None:
        """
        Initialize the condition debugger.

        Args:
            debug_store: Injected debug data store
            max_entries: Maximum number of entries to retain
            filter_tag: Optional tag filter
        """
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.filter_tag = filter_tag
        self.entries: list[ConditionEntry] = []

    def update(self) -> None:
        """Refresh entries from the debug store."""
        # Get evaluations (newest first) and build entries list
        raw_evaluations = self.debug_store.get_recent_evaluations(limit=self.max_entries * 2)

        # Map action_id to latest snapshot for contextual info
        # Note: get_all_snapshots() only returns active actions (removed actions have no snapshot)
        snapshots = self.debug_store.get_all_snapshots()
        snapshot_by_action = {snapshot.action_id: snapshot for snapshot in snapshots}

        entries: list[ConditionEntry] = []
        for evaluation in raw_evaluations:
            snapshot = snapshot_by_action.get(evaluation.action_id)

            # Skip entries for removed actions (no snapshot means action was removed)
            if snapshot is None:
                continue

            tag = snapshot.tag
            target_id = snapshot.target_id
            target_type = snapshot.target_type

            # Apply tag filter before recording entry
            if self.filter_tag and tag != self.filter_tag:
                continue

            entry = ConditionEntry(
                action_id=evaluation.action_id,
                action_type=evaluation.action_type,
                frame=evaluation.frame,
                timestamp=evaluation.timestamp,
                result=evaluation.result,
                condition_str=evaluation.condition_str,
                variables=dict(evaluation.variables),
                tag=tag,
                target_id=target_id,
                target_type=target_type,
            )
            entries.append(entry)

            if len(entries) >= self.max_entries:
                break

        self.entries = entries

    def clear(self) -> None:
        """Clear all collected entries."""
        self.entries = []
