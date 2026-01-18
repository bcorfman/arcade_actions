from __future__ import annotations

from collections.abc import Callable
from typing import Any

from arcadeactions._movement_bounds import _MoveUntilBoundsMixin
from arcadeactions._movement_runtime import _MoveUntilRuntimeMixin
from arcadeactions._shared_logging import _debug_log
from arcadeactions.base import Action as _Action
from arcadeactions.frame_conditions import _clone_condition

from . import physics_adapter as _pa


class MoveUntil(_MoveUntilRuntimeMixin, _MoveUntilBoundsMixin, _Action):
    """Move sprites using Arcade's velocity system until a condition is satisfied.

    The action maintains both the original target velocity and a current velocity
    that can be modified by easing wrappers for smooth acceleration effects.

    Args:
        velocity: (dx, dy) velocity vector to apply to sprites
        condition: Function that returns truthy value when movement should stop, or None/False to continue
        on_stop: Optional callback called when condition is satisfied. Receives condition data if provided.
        bounds: Optional (left, bottom, right, top) boundary box using edge-based coordinates.
            When a sprite's edge (left/right/bottom/top) reaches the corresponding bound,
            the boundary behavior is triggered. For example, bounds=(0, 0, 800, 600) means
            sprite.left hits 0, sprite.right hits 800, sprite.bottom hits 0, sprite.top hits 600.
        boundary_behavior: "bounce", "wrap", "limit", or None (default: None for no boundary checking)
        velocity_provider: Optional function returning (dx, dy) to dynamically provide velocity each frame
        on_boundary_enter: Optional callback(sprite, axis, side) called when sprite enters a boundary
        on_boundary_exit: Optional callback(sprite, axis, side) called when sprite exits a boundary
    """

    _conflicts_with = ("position", "velocity")

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
        try:
            velocity_x, velocity_y = velocity
        except Exception:
            raise ValueError("velocity must be a tuple or list of length 2") from None

        super().__init__(condition, on_stop)
        self.target_velocity = (velocity_x, velocity_y)  # Immutable target velocity
        self.current_velocity = (velocity_x, velocity_y)  # Current velocity (can be scaled by factor)
        # Boundary checking
        self.bounds = bounds  # (left, bottom, right, top)
        self.boundary_behavior = boundary_behavior

        # Velocity provider and boundary event callbacks
        self.velocity_provider = velocity_provider
        self.on_boundary_enter = on_boundary_enter
        self.on_boundary_exit = on_boundary_exit

        # Track boundary state for enter/exit detection
        self._boundary_state = {}  # {sprite_id: {"x": side_or_None, "y": side_or_None}}
        self._frame_callback_tracker: set[tuple[int, str, str]] = set()
        self._paused_velocity: tuple[float, float] | None = None

        # Track if we just completed a step and need to preserve velocities for one frame
        self._step_velocity_pending = False

        # Duration tracking for simulation time compatibility
        self._elapsed = 0.0
        self._duration = None

        _debug_log(
            f"__init__: id={id(self)}, velocity={velocity}, bounds={bounds}, boundary_behavior={boundary_behavior}, "
            f"velocity_provider={bool(self.velocity_provider)}",
            action="MoveUntil",
        )

    def set_factor(self, factor: float) -> None:
        """Scale the velocity by the given factor.

        Args:
            factor: Scaling factor for velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_velocity = (self.target_velocity[0] * factor, self.target_velocity[1] * factor)
        # Immediately apply the new velocity if action is active
        if not self.done and self.target is not None:
            self.apply_effect()
        _debug_log(
            f"set_factor: id={id(self)}, factor={factor}, target_velocity={self.target_velocity}, "
            f"current_velocity={self.current_velocity}",
            action="MoveUntil",
        )

    def set_bounds(self, bounds: tuple[float, float, float, float]) -> None:
        """Update the boundary bounds for this action.

        Args:
            bounds: New bounds tuple (left, bottom, right, top)
        """
        try:
            left, bottom, right, top = bounds
        except Exception as exc:
            raise ValueError("bounds must be a tuple or list of length 4") from exc
        self.bounds = (left, bottom, right, top)
        _debug_log(
            f"set_bounds: id={id(self)}, bounds={bounds}",
            action="MoveUntil",
        )

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement on the specified axis.

        Args:
            axis: 'x' or 'y' to reverse movement on that axis
        """
        if axis == "x":
            self.current_velocity = (-self.current_velocity[0], self.current_velocity[1])
        elif axis == "y":
            self.current_velocity = (self.current_velocity[0], -self.current_velocity[1])
        else:
            raise ValueError("axis must be 'x' or 'y'")

        # Apply the new velocity to all sprites
        self.apply_effect()
        self._update_motion_snapshot(velocity=self.current_velocity)

    def reset(self) -> None:
        """Reset velocity to original target velocity."""
        self.current_velocity = self.target_velocity
        self.apply_effect()
        _debug_log(
            f"reset: id={id(self)}, target_velocity={self.target_velocity}",
            action="MoveUntil",
        )

    def clone(self) -> MoveUntil:
        """Create a copy of this MoveUntil action."""
        _debug_log(f"clone: id={id(self)}", action="MoveUntil")
        return MoveUntil(
            self.target_velocity,  # Use target_velocity for cloning
            _clone_condition(self.condition),
            self.on_stop,
            self.bounds,
            self.boundary_behavior,
            self.velocity_provider,
            self.on_boundary_enter,
            self.on_boundary_exit,
        )

    def pause(self) -> None:
        if self._paused:
            return
        # Save current velocity before pausing
        # During stepping, this happens after update_effect() has run and boundary checks
        # have modified current_velocity, so we save the correct velocity for next resume
        self._paused_velocity = self.current_velocity
        super().pause()
        if not self.done:
            # During stepping, keep velocities set so sprite.update() can use them
            # During normal pause, clear velocities immediately
            if not _Action._is_stepping:
                self.set_current_velocity((0.0, 0.0))
            else:
                # We're stepping - mark that velocities need to be preserved for one frame
                # so sprite.update() can move sprites after step_all() completes
                self._step_velocity_pending = True

    def update(self, delta_time: float) -> None:
        """
        Update the action.

        Override to clear velocities when paused (but not during stepping).
        This ensures that after step_all() completes, velocities are cleared
        so sprites don't continue moving when actions are paused.
        """
        if not self._is_active or self.done:
            return

        # If paused, clear velocities that might have been left from stepping
        # This happens when step_all() completes: velocities are set for sprite.update(),
        # but after sprite.update() runs, we need to clear them so sprite doesn't continue moving
        if self._paused:
            if not _Action._is_stepping:
                # Check if we just completed a step and velocities need to be preserved
                # for one frame so sprite.update() can move sprites
                if self._step_velocity_pending:
                    # Preserve velocities for this frame, clear the flag
                    self._step_velocity_pending = False
                    return
                # Not currently stepping - clear any velocities left from previous step
                self.set_current_velocity((0.0, 0.0))
            return

        # Call parent update which handles update_effect() and condition checking
        super().update(delta_time)

    def resume(self) -> None:
        if not self._paused:
            return
        paused_velocity = self._paused_velocity
        self._paused_velocity = None
        self._step_velocity_pending = False  # Clear step flag when resuming
        super().resume()
        if not self.done and paused_velocity is not None:
            self.set_current_velocity(paused_velocity)

    def _on_start_paused(self) -> None:
        self._paused_velocity = self.current_velocity


class RotateUntil(_Action):
    """Rotate sprites using Arcade's rotation system until a condition is satisfied.

    Args:
        angular_velocity: Rotation velocity in degrees per frame (Arcade uses degrees)
        condition: Function that returns truthy value when rotation should stop
        on_stop: Optional callback called when condition is satisfied
    """

    _conflicts_with = ("rotation",)

    def __init__(
        self,
        angular_velocity: float,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        super().__init__(condition, on_stop)
        self.target_angular_velocity = angular_velocity  # Immutable target velocity
        self.current_angular_velocity = angular_velocity  # Current velocity (can be scaled)

    def set_factor(self, factor: float) -> None:
        """Scale the angular velocity by the given factor."""
        self.current_angular_velocity = self.target_angular_velocity * factor
        if not self.done and self.target is not None:
            self.apply_effect()

    def apply_effect(self) -> None:
        """Apply angular velocity to all sprites."""

        def set_angular_velocity(sprite):
            _pa.set_angular_velocity(sprite, self.current_angular_velocity)

        self.for_each_sprite(set_angular_velocity)

    def remove_effect(self) -> None:
        """Clear angular velocity from all sprites."""

        def clear_rotation(sprite):
            sprite.change_angle = 0

        self.for_each_sprite(clear_rotation)

    def clone(self) -> RotateUntil:
        return RotateUntil(self.target_angular_velocity, _clone_condition(self.condition), self.on_stop)

    def reset(self) -> None:
        self.current_angular_velocity = self.target_angular_velocity

    def set_duration(self, duration: float) -> None:
        raise NotImplementedError
