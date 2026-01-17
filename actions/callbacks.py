from __future__ import annotations

from collections.abc import Callable
from typing import Any

from actions.base import Action as _Action

from actions._shared_logging import _debug_log
from actions.frame_conditions import _clone_condition


class DelayUntil(_Action):
    """Wait/delay until a condition is satisfied.

    This action does nothing but wait for the condition to be met.
    Useful in sequences to create conditional pauses.

    Args:
        condition: Function that returns truthy value when delay should end
        on_stop: Optional callback called when condition is satisfied
    """

    def __init__(
        self,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        super().__init__(condition, on_stop)
        self._elapsed = 0.0
        self._duration = None

    def apply_effect(self) -> None:
        """Initialize delay timing."""
        # Legacy wall-clock helpers are no longer supported; rely on frame-based conditions directly
        self._duration = None
        self._elapsed = 0.0

    def update_effect(self, delta_time: float) -> None:
        """Update delay timing using simulation time."""
        if self._duration is not None:
            # Use simulation time for duration-based delays
            self._elapsed += delta_time

            # Check if duration has elapsed
            if self._elapsed >= self._duration:
                # Mark as complete by setting the condition as met
                self._condition_met = True
                self.done = True
                if self.on_stop:
                    self.on_stop()

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self._elapsed = 0.0
        self._duration = None

    def clone(self) -> "DelayUntil":
        """Create a copy of this action."""
        return DelayUntil(_clone_condition(self.condition), self.on_stop)


class CallbackUntil(_Action):
    """Execute a callback function until a condition is satisfied.

    The callback is called every frame by default, or at a fixed interval
    if ``seconds_between_calls`` is provided. Interval timing respects
    ``set_factor`` scaling (higher factor → shorter interval).

    Args:
        callback: Function to call (accepts optional target parameter)
        condition: Function that returns truthy value when callbacks should stop
        on_stop: Optional callback called when condition is satisfied
        seconds_between_calls: Optional seconds between calls; None → every frame
    """

    def __init__(
        self,
        callback: Callable[..., None],
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        *,
        seconds_between_calls: float | None = None,
    ):
        super().__init__(condition=condition, on_stop=on_stop)
        if seconds_between_calls is not None and seconds_between_calls < 0:
            raise ValueError("seconds_between_calls must be non-negative")
        self.callback = callback
        self.target_seconds_between_calls = seconds_between_calls
        self.current_seconds_between_calls = seconds_between_calls
        self._elapsed_since_call = 0.0
        self._duration: float | None = None
        self._elapsed = 0.0
        self._next_fire_time: float | None = None

        _debug_log(f"__init__: id={id(self)}, callback={callback}, seconds_between_calls={seconds_between_calls}")

    def set_factor(self, factor: float) -> None:
        """Scale the callback interval by the given factor.

        Factor affects the time between calls - higher factor = faster callbacks.
        A factor of 0.0 stops callbacks (when using interval mode).
        """
        if self.target_seconds_between_calls is None:
            # Per-frame mode; factor has no effect on rate here
            self._factor = factor
            return

        if factor <= 0:
            self.current_seconds_between_calls = float("inf")
        else:
            self.current_seconds_between_calls = self.target_seconds_between_calls / factor

        # Update next fire time if we're already scheduled
        if self._next_fire_time is not None:
            if self.current_seconds_between_calls == float("inf"):
                # Paused - don't update next fire time
                pass
            else:
                # Reschedule based on new interval
                self._next_fire_time = self._elapsed + self.current_seconds_between_calls

    def update_effect(self, delta_time: float) -> None:
        """Call the callback function respecting optional interval scheduling."""
        _debug_log(
            f"update_effect: id={id(self)}, delta_time={delta_time:.4f}, elapsed={self._elapsed:.4f}, done={self.done}"
        )

        if not self.callback:
            _debug_log(f"update_effect: id={id(self)}, no callback - returning")
            return

        # Always advance simulation time first for duration conditions
        self._elapsed += delta_time

        # Per-frame mode
        if self.current_seconds_between_calls is None:
            _debug_log(f"update_effect: id={id(self)}, per-frame mode - calling callback")
            # Call callback once per frame, trying both signatures
            self._call_callback_with_fallback()
            return

        # Interval mode (use absolute scheduling to ensure exact counts)
        # Bootstrap schedule on first update
        if self._next_fire_time is None:
            self._next_fire_time = self.current_seconds_between_calls or 0.0
            _debug_log(f"update_effect: id={id(self)}, interval mode - bootstrap next_fire_time={self._next_fire_time}")

        # Fire when elapsed meets or exceeds schedule (but not if paused)
        should_fire = (
            self.current_seconds_between_calls != float("inf") and self._elapsed >= self._next_fire_time - 1e-9
        )
        _debug_log(
            f"update_effect: id={id(self)}, interval mode - elapsed={self._elapsed:.4f}, next_fire={self._next_fire_time:.4f}, should_fire={should_fire}"
        )

        if should_fire:
            _debug_log(f"update_effect: id={id(self)}, interval mode - calling callback")
            # Call callback once, trying both signatures
            self._call_callback_with_fallback()

            # Schedule next fire time
            self._next_fire_time += self.current_seconds_between_calls or 0.0

        # Special case: if we have a duration condition and we're very close to completion,
        # check if there's a pending callback that should fire at completion time
        if (
            self.current_seconds_between_calls != float("inf")
            and self._duration is not None
            and self._elapsed >= (self._duration - 1e-9)
            and self._next_fire_time is not None
            and self._next_fire_time <= self._duration + 1e-9
        ):
            # Fire final callback if it's scheduled at or before the completion time
            if self._elapsed < self._next_fire_time <= self._duration + 1e-9:
                self._call_callback_with_fallback()

    def apply_effect(self) -> None:
        """Initialize duration tracking based on frame metadata, if available."""
        _debug_log(f"apply_effect: id={id(self)}, target={self.target}")
        self._elapsed = 0.0
        self._elapsed_since_call = 0.0
        self.current_seconds_between_calls = self.target_seconds_between_calls
        self._next_fire_time = None
        self._duration = None

    def _call_callback_with_fallback(self) -> None:
        """Call the callback, trying both with and without target parameter."""
        _debug_log(f"_call_callback_with_fallback: id={id(self)}, callback={self.callback}, target={self.target}")
        try:
            # Try with target parameter first
            _debug_log(f"_call_callback_with_fallback: id={id(self)}, trying callback(target)")
            self.callback(self.target)
            _debug_log(f"_call_callback_with_fallback: id={id(self)}, callback(target) succeeded")
        except TypeError:
            try:
                # Fall back to no parameters
                _debug_log(f"_call_callback_with_fallback: id={id(self)}, trying callback()")
                self.callback()
                _debug_log(f"_call_callback_with_fallback: id={id(self)}, callback() succeeded")
            except Exception as e:
                # Use safe call for any other exceptions (includes TypeError)
                _debug_log(f"_call_callback_with_fallback: id={id(self)}, callback() failed: {e}, using safe_call")
                self._safe_call(self.callback)

    def reset(self) -> None:
        """Reset interval timing to initial state."""
        _debug_log(f"reset: id={id(self)}")
        self._elapsed_since_call = 0.0
        self.current_seconds_between_calls = self.target_seconds_between_calls
        self._elapsed = 0.0
        self._next_fire_time = None

    def clone(self) -> "CallbackUntil":
        """Create a copy of this action."""
        return CallbackUntil(
            self.callback,
            _clone_condition(self.condition),
            self.on_stop,
            seconds_between_calls=self.target_seconds_between_calls,
        )
