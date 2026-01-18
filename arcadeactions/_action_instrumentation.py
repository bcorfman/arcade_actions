from __future__ import annotations

from typing import Any


class ActionInstrumentationMixin:
    """Instrumentation hooks for Action."""

    def _instrumentation_active(self) -> bool:
        return self._instrumented and type(self)._enable_visualizer and type(self)._debug_store is not None

    @classmethod
    def set_debug_store(cls, debug_store) -> None:
        """Inject a DebugDataStore dependency for visualization instrumentation."""
        cls._debug_store = debug_store

    def _record_event(self, event_type: str, **details) -> None:
        if not self._instrumentation_active():
            return

        target_id = id(self.target) if self.target else 0
        target_type = type(self.target).__name__ if self.target else "None"

        store = type(self)._debug_store
        if not store:
            return

        store.record_event(
            event_type=event_type,
            action_id=id(self),
            action_type=type(self).__name__,
            target_id=target_id,
            target_type=target_type,
            tag=self.tag,
            **details,
        )

    def _record_condition_evaluation(self, result: Any) -> None:
        if not self._instrumentation_active():
            return

        condition_str = "<unknown>"
        try:
            condition_str = self.condition.__name__
        except AttributeError:
            condition_doc = None
            try:
                condition_doc = self.condition.__doc__
            except AttributeError:
                condition_doc = None
            if condition_doc:
                condition_str = condition_doc.strip()

        store = type(self)._debug_store
        if not store:
            return

        store.record_condition_evaluation(
            action_id=id(self), action_type=type(self).__name__, result=result, condition_str=condition_str
        )

    def _update_snapshot(self, **kwargs) -> None:
        if not self._instrumentation_active():
            return

        if self.done or not self._is_active:
            return

        target_id = id(self.target) if self.target else 0
        target_type = type(self.target).__name__ if self.target else "None"

        snapshot_data = {
            "action_id": id(self),
            "action_type": type(self).__name__,
            "target_id": target_id,
            "target_type": target_type,
            "tag": self.tag,
            "is_active": self._is_active,
            "is_paused": self._paused,
            "factor": self._factor,
            "elapsed": self._elapsed,
            "progress": None,
        }
        snapshot_data.update(kwargs)

        store = type(self)._debug_store
        if not store:
            return

        store.update_snapshot(**snapshot_data)

    @classmethod
    def _record_debug_frame(cls, frame_number: int, timestamp: float) -> None:
        store = cls._debug_store
        if not store:
            return

        store.update_frame(frame_number, timestamp)
