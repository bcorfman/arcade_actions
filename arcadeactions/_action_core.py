from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from ._action_callbacks import ActionCallbacksMixin
from ._action_conflicts import check_action_conflicts
from ._action_debug import _debug_log_action, describe_target
from ._action_instrumentation import ActionInstrumentationMixin
from ._action_manager import ActionManagerMixin
from ._action_targets import SpriteTarget, TargetAdapter, adapt_target, _get_sprite_list_name

_T = TypeVar("_T", bound="Action")


class Action(ActionManagerMixin, ActionInstrumentationMixin, ActionCallbacksMixin, ABC, Generic[_T]):
    """Base class for all actions."""

    _conflicts_with: tuple[str, ...] = ()
    _requires_sprite_target: bool = True

    num_active_actions = 0
    debug_level: int = 0
    debug_include_classes: set[str] | None = None
    debug_all: bool = False
    _active_actions: list["Action"] = []
    _pending_actions: list["Action"] = []
    _is_updating: bool = False
    _previous_actions: set["Action"] | None = None
    _warned_bad_callbacks: set[Callable] = set()
    _last_counts: dict[str, int] | None = None
    _enable_visualizer: bool = False
    _frame_counter: int = 0
    _debug_store = None
    _is_stepping: bool = False

    def __init__(
        self,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        tag: str | None = None,
    ):
        self.target: SpriteTarget | None = None
        self._target_adapter: TargetAdapter | None = None
        self.condition = condition
        self.on_stop = on_stop
        self.tag = tag
        self.done = False
        self._is_active = False
        self._callbacks_active = True
        self._paused = False
        self._factor = 1.0
        self._condition_met = False
        self._elapsed = 0.0
        self._duration: float | None = None
        self.bounds: tuple[float, float, float, float] | None = None
        self.condition_data: Any = None
        self._instrumented = False
        self.wrapped_action: "Action" | None = None

    def __add__(self, other: "Action") -> "Action":
        from arcadeactions.composite import sequence

        return sequence(self, other)

    def __radd__(self, other: "Action") -> "Action":
        return other.__add__(self)

    def __or__(self, other: "Action") -> "Action":
        from arcadeactions.composite import parallel

        return parallel(self, other)

    def __ror__(self, other: "Action") -> "Action":
        return other.__or__(self)

    def apply(self, target: SpriteTarget | None, tag: str | None = None, replace: bool = False) -> "Action":
        if target is None:
            self.target = None
            self._target_adapter = None
            if tag is not None:
                self.tag = tag
            return self

        if self._requires_sprite_target:
            self._target_adapter = adapt_target(target)
        self.target = target
        if tag is not None:
            self.tag = tag
        self._instrumented = True

        if replace and tag is not None:
            Action.stop_actions_for_target(target, tag=tag)

        if self._requires_sprite_target:
            check_action_conflicts(self, target)

        if self._instrumentation_active():
            self._record_event("created")

        if Action._is_updating:
            Action._pending_actions.append(self)
        else:
            Action._active_actions.append(self)
            self.start()
        return self

    def start(self) -> None:
        _debug_log_action(self, 2, f"start() target={self.target} tag={self.tag}")
        self._is_active = True

        if Action._active_actions:
            other_actions = [a for a in Action._active_actions if a is not self]
            if other_actions and all(a._paused for a in other_actions):
                self._paused = True
                self._on_start_paused()
                _debug_log_action(self, 2, "starting in paused state (matching global pause)")

                if self._instrumentation_active():
                    self._record_event("started")
                    self._update_snapshot()
                return

        if self._instrumentation_active():
            self._record_event("started")
            self._update_snapshot()

        self.apply_effect()
        _debug_log_action(self, 2, f"start() completed _is_active={self._is_active}")

    def apply_effect(self) -> None:
        pass

    def update(self, delta_time: float) -> None:
        if not self._is_active or self.done or self._paused:
            return

        self.update_effect(delta_time)

        if self.condition and not self._condition_met:
            condition_result = self.condition()

            if self._instrumentation_active():
                self._record_condition_evaluation(condition_result)

            if condition_result:
                self._condition_met = True
                self.condition_data = condition_result
                self.remove_effect()
                self.done = True

                if self._instrumentation_active():
                    self._record_event("stopped", condition_data=condition_result)

                if self.on_stop:
                    if condition_result is not True:
                        self._safe_call(self.on_stop, condition_result)
                    else:
                        self._safe_call(self.on_stop)

    def update_effect(self, delta_time: float) -> None:
        pass

    def remove_effect(self) -> None:
        pass

    def stop(self) -> None:
        _debug_log_action(self, 2, f"stop() called done={self.done} _is_active={self._is_active}")

        self._callbacks_active = False
        self.done = True
        self._is_active = False

        if self._instrumentation_active():
            self._record_event("removed")

        if self in Action._active_actions:
            Action._active_actions.remove(self)
            _debug_log_action(self, 2, "removed from _active_actions")
        self.remove_effect()
        _debug_log_action(self, 2, f"stop() completed done={self.done} _is_active={self._is_active}")

    @classmethod
    def _describe_target(cls, target: SpriteTarget | None) -> str:
        return describe_target(target)

    @classmethod
    def _get_sprite_list_name(cls, sprite_list) -> str:
        return _get_sprite_list_name(sprite_list)

    @abstractmethod
    def clone(self) -> "Action":
        raise NotImplementedError

    def for_each_sprite(self, func: Callable[[Any], None]) -> None:
        if self.target is None:
            return
        if self._target_adapter is None:
            self._target_adapter = adapt_target(self.target)
        for sprite in self._target_adapter.iter_sprites():
            func(sprite)

    def set_factor(self, factor: float) -> None:
        self._factor = factor

    @property
    def condition_met(self) -> bool:
        return self._condition_met

    @condition_met.setter
    def condition_met(self, value: bool) -> None:
        self._condition_met = value

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        pass

    def sub_actions(self) -> list["Action"]:
        return []

    def _on_start_paused(self) -> None:
        pass
