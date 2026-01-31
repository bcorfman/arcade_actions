"""
Instrumentation layer for ACE visualization.

Provides hooks for capturing action lifecycle events, condition evaluations,
and frame-by-frame state for debugging and visualization.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade

    SpriteTarget = arcade.Sprite | arcade.SpriteList


class ActionEvent:
    """Records a lifecycle event for an action."""

    __slots__ = (
        "frame",
        "timestamp",
        "event_type",
        "action_id",
        "action_type",
        "target_id",
        "target_type",
        "tag",
        "details",
    )

    def __init__(
        self,
        *,
        frame: int,
        timestamp: float,
        event_type: str,
        action_id: int,
        action_type: str,
        target_id: int,
        target_type: str,
        tag: str | None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.frame = frame
        self.timestamp = timestamp
        self.event_type = event_type
        self.action_id = action_id
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = target_type
        self.tag = tag
        self.details = details or {}


class ConditionEvaluation:
    """Records a condition evaluation result."""

    __slots__ = (
        "frame",
        "timestamp",
        "action_id",
        "action_type",
        "result",
        "condition_str",
        "variables",
    )

    def __init__(
        self,
        *,
        frame: int,
        timestamp: float,
        action_id: int,
        action_type: str,
        result: Any,
        condition_str: str | None,
        variables: dict[str, Any] | None = None,
    ) -> None:
        self.frame = frame
        self.timestamp = timestamp
        self.action_id = action_id
        self.action_type = action_type
        self.result = result
        self.condition_str = condition_str
        self.variables = variables or {}


class ActionSnapshot:
    """Current state snapshot of an action."""

    __slots__ = (
        "action_id",
        "action_type",
        "target_id",
        "target_type",
        "tag",
        "is_active",
        "is_paused",
        "factor",
        "elapsed",
        "progress",
        "velocity",
        "bounds",
        "boundary_state",
        "last_condition_result",
        "condition_str",
        "metadata",
    )

    def __init__(
        self,
        *,
        action_id: int,
        action_type: str,
        target_id: int,
        target_type: str,
        tag: str | None,
        is_active: bool,
        is_paused: bool,
        factor: float,
        elapsed: float,
        progress: float | None,
        velocity: tuple[float, float] | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        boundary_state: dict[str, Any] | None = None,
        last_condition_result: Any = None,
        condition_str: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.action_id = action_id
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = target_type
        self.tag = tag
        self.is_active = is_active
        self.is_paused = is_paused
        self.factor = factor
        self.elapsed = elapsed
        self.progress = progress
        self.velocity = velocity
        self.bounds = bounds
        self.boundary_state = boundary_state
        self.last_condition_result = last_condition_result
        self.condition_str = condition_str
        self.metadata = metadata or {}


_SNAPSHOT_FIELDS = {
    "action_type",
    "target_id",
    "target_type",
    "tag",
    "is_active",
    "is_paused",
    "factor",
    "elapsed",
    "progress",
    "velocity",
    "bounds",
    "boundary_state",
    "last_condition_result",
    "condition_str",
}


class DebugDataStore:
    """
    Centralized storage for debug instrumentation data.

    Uses ring buffers to limit memory usage while providing recent history
    for visualization and time-travel debugging.
    """

    def __init__(self, max_events: int = 1000, max_evaluations: int = 500):
        """
        Initialize the debug data store.

        Args:
            max_events: Maximum number of action events to retain
            max_evaluations: Maximum number of condition evaluations to retain
        """
        self.max_events = max_events
        self.max_evaluations = max_evaluations

        # Ring buffers for historical data
        self.events: deque[ActionEvent] = deque(maxlen=max_events)
        self.evaluations: deque[ConditionEvaluation] = deque(maxlen=max_evaluations)

        # Current frame state
        self.current_frame = 0
        self.current_time = 0.0
        self.active_snapshots: dict[int, ActionSnapshot] = {}  # action_id -> snapshot

        # Index for quick lookups
        self.actions_by_target: dict[int, list[int]] = {}  # target_id -> list of action_ids
        self.actions_by_tag: dict[str, list[int]] = {}  # tag -> list of action_ids

        # Statistics
        self.total_actions_created = 0
        self.total_conditions_evaluated = 0

    def update_frame(self, frame: int, timestamp: float) -> None:
        """Update current frame and timestamp."""
        self.current_frame = frame
        self.current_time = timestamp

    def record_event(
        self,
        event_type: str,
        action_id: int,
        action_type: str,
        target_id: int,
        target_type: str,
        tag: str | None = None,
        **details,
    ) -> None:
        """Record an action lifecycle event."""
        self.events.append(
            ActionEvent(
                frame=self.current_frame,
                timestamp=self.current_time,
                event_type=event_type,
                action_id=action_id,
                action_type=action_type,
                target_id=target_id,
                target_type=target_type,
                tag=tag,
                details=details,
            )
        )

        if event_type == "created":
            self._record_created_event(action_id, target_id, tag)
        elif event_type == "removed":
            self._record_removed_event(action_id, target_id, tag)

    def record_condition_evaluation(
        self,
        action_id: int,
        action_type: str,
        result: Any,
        condition_str: str | None = None,
        **variables,
    ) -> None:
        """Record a condition evaluation."""
        evaluation = ConditionEvaluation(
            frame=self.current_frame,
            timestamp=self.current_time,
            action_id=action_id,
            action_type=action_type,
            result=result,
            condition_str=condition_str,
            variables=variables,
        )
        self.evaluations.append(evaluation)
        self.total_conditions_evaluated += 1

        # Update snapshot with latest condition result
        if action_id in self.active_snapshots:
            snapshot = self.active_snapshots[action_id]
            snapshot.last_condition_result = result
            snapshot.condition_str = condition_str

    def update_snapshot(self, action_id: int, **kwargs) -> None:
        """Update or create a snapshot for an action."""
        if action_id in self.active_snapshots:
            snapshot = self.active_snapshots[action_id]
            self._apply_snapshot_updates(snapshot, kwargs)
        else:
            self.active_snapshots[action_id] = self._build_snapshot(action_id, kwargs)

    def get_events_for_action(self, action_id: int, limit: int = 50) -> list[ActionEvent]:
        """Get recent events for a specific action."""
        return [e for e in reversed(self.events) if e.action_id == action_id][:limit]

    def get_evaluations_for_action(self, action_id: int, limit: int = 50) -> list[ConditionEvaluation]:
        """Get recent condition evaluations for a specific action."""
        return [e for e in reversed(self.evaluations) if e.action_id == action_id][:limit]

    def get_actions_for_target(self, target_id: int) -> list[ActionSnapshot]:
        """Get all active action snapshots for a target."""
        action_ids = self.actions_by_target.get(target_id, [])
        return [self.active_snapshots[aid] for aid in action_ids if aid in self.active_snapshots]

    def get_actions_by_tag(self, tag: str) -> list[ActionSnapshot]:
        """Get all active action snapshots with a specific tag."""
        action_ids = self.actions_by_tag.get(tag, [])
        return [self.active_snapshots[aid] for aid in action_ids if aid in self.active_snapshots]

    def get_all_snapshots(self) -> list[ActionSnapshot]:
        """Get all active action snapshots."""
        return list(self.active_snapshots.values())

    def get_recent_events(self, limit: int = 100) -> list[ActionEvent]:
        """Get most recent action events."""
        return list(reversed(self.events))[:limit]

    def get_recent_evaluations(self, limit: int = 100) -> list[ConditionEvaluation]:
        """Get most recent condition evaluations."""
        return list(reversed(self.evaluations))[:limit]

    def clear(self) -> None:
        """Clear all stored data."""
        self.events.clear()
        self.evaluations.clear()
        self.active_snapshots.clear()
        self.actions_by_target.clear()
        self.actions_by_tag.clear()
        self.current_frame = 0
        self.current_time = 0.0
        self.total_actions_created = 0
        self.total_conditions_evaluated = 0

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics."""
        return {
            "current_frame": self.current_frame,
            "current_time": self.current_time,
            "active_actions": len(self.active_snapshots),
            "total_created": self.total_actions_created,
            "total_evaluations": self.total_conditions_evaluated,
            "events_buffered": len(self.events),
            "evaluations_buffered": len(self.evaluations),
        }

    def _record_created_event(self, action_id: int, target_id: int, tag: str | None) -> None:
        self.total_actions_created += 1
        self.actions_by_target.setdefault(target_id, []).append(action_id)
        if tag:
            self.actions_by_tag.setdefault(tag, []).append(action_id)

    def _record_removed_event(self, action_id: int, target_id: int, tag: str | None) -> None:
        self._remove_action_id(self.actions_by_target.get(target_id), action_id)
        if tag:
            self._remove_action_id(self.actions_by_tag.get(tag), action_id)
        self.active_snapshots.pop(action_id, None)

    def _remove_action_id(self, action_ids: list[int] | None, action_id: int) -> None:
        if not action_ids:
            return
        try:
            action_ids.remove(action_id)
        except ValueError:
            return

    def _apply_snapshot_updates(self, snapshot: ActionSnapshot, updates: dict[str, Any]) -> None:
        metadata = updates.get("metadata")
        if isinstance(metadata, dict):
            snapshot.metadata.update(metadata)
        for key in _SNAPSHOT_FIELDS:
            if key in updates:
                setattr(snapshot, key, updates[key])

    def _build_snapshot(self, action_id: int, updates: dict[str, Any]) -> ActionSnapshot:
        return ActionSnapshot(
            action_id=action_id,
            action_type=updates.get("action_type", "Unknown"),
            target_id=updates.get("target_id", 0),
            target_type=updates.get("target_type", "Unknown"),
            tag=updates.get("tag"),
            is_active=updates.get("is_active", False),
            is_paused=updates.get("is_paused", False),
            factor=updates.get("factor", 1.0),
            elapsed=updates.get("elapsed", 0.0),
            progress=updates.get("progress"),
            velocity=updates.get("velocity"),
            bounds=updates.get("bounds"),
            boundary_state=updates.get("boundary_state"),
            metadata=updates.get("metadata", {}),
        )
