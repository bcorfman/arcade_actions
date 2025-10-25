"""
Axis-specific movement actions for safe composition of orthogonal motion.

This module provides MoveXUntil and MoveYUntil classes that only affect
their respective axes, enabling safe composition via parallel() for
orthogonal movement patterns.
"""

from collections.abc import Callable
from typing import Any

from actions.conditional import MoveUntil, _debug_log


class MoveXUntil(MoveUntil):
    """Axis-specific MoveUntil for safe composition via parallel(); affects only X axis.

    This class extends MoveUntil but only modifies sprite.change_x and never
    writes to sprite.change_y. Boundary behavior is applied only on the X axis,
    leaving Y-axis movement untouched.

    Args:
        velocity: (dx, dy) velocity vector to apply to sprites (dy is ignored)
        condition: Function that returns truthy value when movement should stop
        on_stop: Optional callback called when condition is satisfied
        bounds: Optional (left, bottom, right, top) boundary box for bouncing/wrapping/limiting
        boundary_behavior: "bounce", "wrap", "limit", or None (default: None)
        velocity_provider: Optional function returning (dx, dy) to dynamically provide velocity
        on_boundary_enter: Optional callback(sprite, axis, side) called when sprite enters a boundary
        on_boundary_exit: Optional callback(sprite, axis, side) called when sprite exits a boundary
    """

    def __init__(
        self,
        velocity: tuple[float, float],
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        boundary_behavior: str | None = None,
        velocity_provider: Callable[[], tuple[float, float]] | None = None,
        on_boundary_enter: Callable[[Any, str, str], None] | None = None,
        on_boundary_exit: Callable[[Any, str, str], None] | None = None,
    ):
        super().__init__(
            velocity,
            condition,
            on_stop,
            bounds,
            boundary_behavior,
            velocity_provider,
            on_boundary_enter,
            on_boundary_exit,
        )

        _debug_log(
            f"MoveXUntil.__init__: id={id(self)}, velocity={velocity}, bounds={bounds}, "
            f"boundary_behavior={boundary_behavior}",
            action="MoveXUntil",
        )

    def apply_effect(self) -> None:
        """Apply X-axis only movement to sprites."""

        # Extract duration from condition if present (for duration-based conditions)
        self._duration = None
        if hasattr(self.condition, "_duration_seconds"):
            seconds = self.condition._duration_seconds
            if isinstance(seconds, (int, float)) and seconds > 0:
                self._duration = seconds

        self._elapsed = 0.0

        def apply_to_sprite(sprite):
            # Get current velocity (from provider or current)
            if self.velocity_provider:
                current_velocity = self.velocity_provider()
            else:
                current_velocity = self.current_velocity

            # Only set change_x, preserve change_y
            sprite.change_x = current_velocity[0]
            # change_y is intentionally not modified

            _debug_log(
                f"MoveXUntil.apply_effect: sprite={id(sprite)}, change_x={sprite.change_x}, "
                f"change_y={sprite.change_y} (preserved)",
                action="MoveXUntil",
            )

        self.for_each_sprite(apply_to_sprite)

    def update_effect(self, delta_time: float) -> None:
        """Update X-axis movement and handle X-axis boundary behavior only."""
        _debug_log(
            f"MoveXUntil.update_effect: id={id(self)}, delta_time={delta_time:.4f}, done={self.done}",
            action="MoveXUntil",
        )

        # Handle duration-based conditions using simulation time
        if self._duration is not None:
            self._elapsed += delta_time
            if self._elapsed >= self._duration:
                _debug_log(
                    f"MoveXUntil.update_effect: duration elapsed ({self._duration:.4f}s) - stopping",
                    action="MoveXUntil",
                )
                self._condition_met = True
                self.remove_effect()
                self.done = True
                if self.on_stop:
                    self.on_stop()
                return

        # Re-apply velocity from provider if available (X-axis only)
        if self.velocity_provider:
            try:
                dx, dy = self.velocity_provider()
                _debug_log(
                    f"MoveXUntil.update_effect: velocity_provider returned dx={dx}",
                    action="MoveXUntil",
                )

                def set_velocity(sprite):
                    sprite.change_x = dx  # Only set X, preserve Y

                self.for_each_sprite(set_velocity)
            except Exception as error:
                _debug_log(
                    f"MoveXUntil.update_effect: velocity_provider exception={error!r} - keeping current velocity",
                    action="MoveXUntil",
                )
                pass  # Keep current velocity on provider error

        # Handle X-axis boundaries only
        if self.bounds and self.boundary_behavior:
            self._handle_x_boundaries()

    def _handle_x_boundaries(self) -> None:
        """Handle boundary behavior only for X axis."""

        def handle_sprite_boundaries(sprite):
            left, bottom, right, top = self.bounds

            # Only check X boundaries
            if sprite.center_x <= left:
                if self.boundary_behavior == "bounce":
                    sprite.change_x = abs(sprite.change_x)
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "left")
                elif self.boundary_behavior == "wrap":
                    sprite.center_x = right
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "left")
                elif self.boundary_behavior == "limit":
                    sprite.center_x = left
                    sprite.change_x = 0
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "left")

            elif sprite.center_x >= right:
                if self.boundary_behavior == "bounce":
                    sprite.change_x = -abs(sprite.change_x)
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "right")
                elif self.boundary_behavior == "wrap":
                    sprite.center_x = left
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "right")
                elif self.boundary_behavior == "limit":
                    sprite.center_x = right
                    sprite.change_x = 0
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "x", "right")

        self.for_each_sprite(handle_sprite_boundaries)

    def clone(self) -> "MoveXUntil":
        """Create a copy of this MoveXUntil action."""
        _debug_log(f"MoveXUntil.clone: id={id(self)}", action="MoveXUntil")
        return MoveXUntil(
            self.target_velocity,
            self.condition,  # Use condition directly, not _clone_condition
            self.on_stop,
            self.bounds,
            self.boundary_behavior,
            self.velocity_provider,
            self.on_boundary_enter,
            self.on_boundary_exit,
        )


class MoveYUntil(MoveUntil):
    """Axis-specific MoveUntil for safe composition via parallel(); affects only Y axis.

    This class extends MoveUntil but only modifies sprite.change_y and never
    writes to sprite.change_x. Boundary behavior is applied only on the Y axis,
    leaving X-axis movement untouched.

    Args:
        velocity: (dx, dy) velocity vector to apply to sprites (dx is ignored)
        condition: Function that returns truthy value when movement should stop
        on_stop: Optional callback called when condition is satisfied
        bounds: Optional (left, bottom, right, top) boundary box for bouncing/wrapping/limiting
        boundary_behavior: "bounce", "wrap", "limit", or None (default: None)
        velocity_provider: Optional function returning (dx, dy) to dynamically provide velocity
        on_boundary_enter: Optional callback(sprite, axis, side) called when sprite enters a boundary
        on_boundary_exit: Optional callback(sprite, axis, side) called when sprite exits a boundary
    """

    def __init__(
        self,
        velocity: tuple[float, float],
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        boundary_behavior: str | None = None,
        velocity_provider: Callable[[], tuple[float, float]] | None = None,
        on_boundary_enter: Callable[[Any, str, str], None] | None = None,
        on_boundary_exit: Callable[[Any, str, str], None] | None = None,
    ):
        super().__init__(
            velocity,
            condition,
            on_stop,
            bounds,
            boundary_behavior,
            velocity_provider,
            on_boundary_enter,
            on_boundary_exit,
        )

        _debug_log(
            f"MoveYUntil.__init__: id={id(self)}, velocity={velocity}, bounds={bounds}, "
            f"boundary_behavior={boundary_behavior}",
            action="MoveYUntil",
        )

    def apply_effect(self) -> None:
        """Apply Y-axis only movement to sprites."""

        # Extract duration from condition if present (for duration-based conditions)
        self._duration = None
        if hasattr(self.condition, "_duration_seconds"):
            seconds = self.condition._duration_seconds
            if isinstance(seconds, (int, float)) and seconds > 0:
                self._duration = seconds

        self._elapsed = 0.0

        def apply_to_sprite(sprite):
            # Get current velocity (from provider or current)
            if self.velocity_provider:
                current_velocity = self.velocity_provider()
            else:
                current_velocity = self.current_velocity

            # Only set change_y, preserve change_x
            sprite.change_y = current_velocity[1]
            # change_x is intentionally not modified

            _debug_log(
                f"MoveYUntil.apply_effect: sprite={id(sprite)}, change_x={sprite.change_x} (preserved), "
                f"change_y={sprite.change_y}",
                action="MoveYUntil",
            )

        self.for_each_sprite(apply_to_sprite)

    def update_effect(self, delta_time: float) -> None:
        """Update Y-axis movement and handle Y-axis boundary behavior only."""
        _debug_log(
            f"MoveYUntil.update_effect: id={id(self)}, delta_time={delta_time:.4f}, done={self.done}",
            action="MoveYUntil",
        )

        # Handle duration-based conditions using simulation time
        if self._duration is not None:
            self._elapsed += delta_time
            if self._elapsed >= self._duration:
                _debug_log(
                    f"MoveYUntil.update_effect: duration elapsed ({self._duration:.4f}s) - stopping",
                    action="MoveYUntil",
                )
                self._condition_met = True
                self.remove_effect()
                self.done = True
                if self.on_stop:
                    self.on_stop()
                return

        # Re-apply velocity from provider if available (Y-axis only)
        if self.velocity_provider:
            try:
                dx, dy = self.velocity_provider()
                _debug_log(
                    f"MoveYUntil.update_effect: velocity_provider returned dy={dy}",
                    action="MoveYUntil",
                )

                def set_velocity(sprite):
                    sprite.change_y = dy  # Only set Y, preserve X

                self.for_each_sprite(set_velocity)
            except Exception as error:
                _debug_log(
                    f"MoveYUntil.update_effect: velocity_provider exception={error!r} - keeping current velocity",
                    action="MoveYUntil",
                )
                pass  # Keep current velocity on provider error

        # Handle Y-axis boundaries only
        if self.bounds and self.boundary_behavior:
            self._handle_y_boundaries()

    def _handle_y_boundaries(self) -> None:
        """Handle boundary behavior only for Y axis."""

        def handle_sprite_boundaries(sprite):
            left, bottom, right, top = self.bounds

            # Only check Y boundaries
            if sprite.center_y <= bottom:
                if self.boundary_behavior == "bounce":
                    sprite.change_y = abs(sprite.change_y)
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "bottom")
                elif self.boundary_behavior == "wrap":
                    sprite.center_y = top
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "bottom")
                elif self.boundary_behavior == "limit":
                    sprite.center_y = bottom
                    sprite.change_y = 0
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "bottom")

            elif sprite.center_y >= top:
                if self.boundary_behavior == "bounce":
                    sprite.change_y = -abs(sprite.change_y)
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "top")
                elif self.boundary_behavior == "wrap":
                    sprite.center_y = bottom
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "top")
                elif self.boundary_behavior == "limit":
                    sprite.center_y = top
                    sprite.change_y = 0
                    if self.on_boundary_enter:
                        self.on_boundary_enter(sprite, "y", "top")

        self.for_each_sprite(handle_sprite_boundaries)

    def clone(self) -> "MoveYUntil":
        """Create a copy of this MoveYUntil action."""
        _debug_log(f"MoveYUntil.clone: id={id(self)}", action="MoveYUntil")
        return MoveYUntil(
            self.target_velocity,
            self.condition,  # Use condition directly, not _clone_condition
            self.on_stop,
            self.bounds,
            self.boundary_behavior,
            self.velocity_provider,
            self.on_boundary_enter,
            self.on_boundary_exit,
        )
