"""
Easing wrapper for ArcadeActions.

This module provides easing functionality that wraps conditional actions
and modulates their intensity over time using easing curves.
"""

from __future__ import annotations

from collections.abc import Callable

from arcade import easing

from actions.base import Action


class Easing(Action):
    """
    Wraps a conditional action and modulates its rate using an easing function.

    This allows the wrapped action to appear to accelerate, decelerate, or both — depending
    on the easing curve used. The easing function transforms normalized time (t in [0,1])
    into a factor that scales the wrapped action's intensity via set_factor().

    The wrapped action must implement set_factor(float) to respond to intensity changes.
    All conditional actions in ArcadeActions support this interface.

    Parameters:
        action: The conditional action to be wrapped and time-warped
        seconds: Duration of the easing effect in seconds
        ease_function: Easing function taking t ∈ [0, 1] and returning eased factor
        on_complete: Optional callback when easing completes

    Example:
        >>> from actions.conditional import MoveUntil, duration
        >>> from actions.easing import Easing
        >>> from arcade import easing
        >>> # Create base movement action
        >>> move = MoveUntil((100, 0), lambda: False)  # Move indefinitely
        >>> # Wrap with easing for smooth acceleration/deceleration
        >>> eased_move = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)
        >>> eased_move.apply(sprite, tag="eased_movement")
        >>> # The sprite will smoothly accelerate to full speed, then decelerate to stop
    """

    def __init__(
        self,
        action: Action,
        seconds: float,
        ease_function: Callable[[float], float] = easing.ease_in_out,
        on_complete: Callable[[], None] | None = None,
    ):
        if seconds <= 0:
            raise ValueError("seconds must be positive")

        # No external condition - easing manages its own completion
        super().__init__(condition_func=None, on_condition_met=None)

        self.wrapped_action = action
        self.easing_duration = seconds
        self.ease_function = ease_function
        self.on_complete = on_complete

        # Easing state
        self._elapsed = 0.0
        self._easing_complete = False

    def apply(self, target, tag: str = "default") -> Action:
        """Apply both this easing wrapper and the wrapped action to the target."""
        # Apply the wrapped action first
        self.wrapped_action.apply(target, tag=f"{tag}_wrapped")

        # Then apply this easing wrapper
        return super().apply(target, tag)

    def apply_effect(self) -> None:
        """Initialize easing - start with factor 0."""
        self.wrapped_action.set_factor(0.0)

    def update_effect(self, delta_time: float) -> None:
        """Update easing factor and apply to wrapped action."""
        if self._easing_complete:
            return

        self._elapsed += delta_time

        # Calculate easing progress (0 to 1)
        t = min(self._elapsed / self.easing_duration, 1.0)

        # Apply easing function to get factor
        factor = self.ease_function(t)

        # Update wrapped action's intensity
        self.wrapped_action.set_factor(factor)

        # Check if easing is complete
        if t >= 1.0:
            self._easing_complete = True
            self.done = True

            if self.on_complete:
                self.on_complete()

    def remove_effect(self) -> None:
        """Clean up easing - leave wrapped action at final factor."""
        # The wrapped action continues running at its final factor
        # This allows the underlying action to continue until its own condition is met
        pass

    def stop(self) -> None:
        """Stop both this easing wrapper and the wrapped action."""
        # Stop the wrapped action
        self.wrapped_action.stop()

        # Stop this wrapper
        super().stop()

    def set_factor(self, factor: float) -> None:
        """Forward factor changes to the wrapped action.

        This allows easing actions to be nested or chained.
        """
        self.wrapped_action.set_factor(factor)

    def clone(self) -> Easing:
        """Create a copy of this Easing action."""
        return Easing(
            self.wrapped_action.clone(),
            self.easing_duration,
            self.ease_function,
            self.on_complete,
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Easing(duration={self.easing_duration}, "
            f"ease_function={self.ease_function.__name__}, "
            f"wrapped={repr(self.wrapped_action)})"
        )
