import math
from collections.abc import Callable
from typing import Any

from actions.base import Action as _Action


class MoveUntil(_Action):
    """Move sprites using Arcade's velocity system until a condition is satisfied.

    The action maintains both the original target velocity and a current velocity
    that can be modified by easing wrappers for smooth acceleration effects.

    Args:
        velocity: (dx, dy) velocity vector to apply to sprites
        condition: Function that returns truthy value when movement should stop, or None/False to continue
        on_stop: Optional callback called when condition is satisfied. Receives condition data if provided.
        bounds: Optional (left, bottom, right, top) boundary box for bouncing/wrapping
        boundary_behavior: "bounce", "wrap", or None (default: None for no boundary checking)
        on_boundary: Optional callback(sprite, axis) called when sprite hits boundary
    """

    def __init__(
        self,
        velocity: tuple[float, float],
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        boundary_behavior: str | None = None,
        on_boundary: Callable[[Any, str], None] | None = None,
    ):
        if not isinstance(velocity, (tuple, list)) or len(velocity) != 2:
            raise ValueError("velocity must be a tuple or list of length 2")

        super().__init__(condition, on_stop)
        self.target_velocity = velocity  # Immutable target velocity
        self.current_velocity = velocity  # Current velocity (can be scaled by factor)

        # Boundary checking
        self.bounds = bounds  # (left, bottom, right, top)
        self.boundary_behavior = boundary_behavior
        self.on_boundary = on_boundary

        # Duration tracking for simulation time compatibility
        self._elapsed = 0.0
        self._duration = None

    def set_factor(self, factor: float) -> None:
        """Scale the velocity by the given factor.

        Args:
            factor: Scaling factor for velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_velocity = (self.target_velocity[0] * factor, self.target_velocity[1] * factor)
        # Immediately apply the new velocity if action is active
        if not self.done and self.target is not None:
            self.apply_effect()

    def apply_effect(self) -> None:
        """Apply velocity to all sprites."""

        # Try to extract duration from the condition function if it's from duration() helper
        self._duration = None
        try:
            # Check if condition is from duration() helper by looking for closure
            if (
                hasattr(self.condition, "__closure__")
                and self.condition.__closure__
                and len(self.condition.__closure__) >= 1
            ):
                # Get the seconds value from the closure
                seconds = self.condition.__closure__[0].cell_contents
                if isinstance(seconds, (int, float)) and seconds > 0:
                    self._duration = seconds
        except (AttributeError, IndexError, TypeError):
            pass

        self._elapsed = 0.0

        dx, dy = self.current_velocity

        def set_velocity(sprite):
            # For limit boundary behavior, check if velocity would cross boundary
            if self.boundary_behavior == "limit" and self.bounds:
                left, bottom, right, top = self.bounds

                # Check if applying velocity would cross horizontal boundary
                if dx > 0 and sprite.center_x + dx > right:
                    # Would cross right boundary - don't apply velocity
                    sprite.change_x = 0
                    sprite.center_x = right  # Set to boundary
                elif dx < 0 and sprite.center_x + dx < left:
                    # Would cross left boundary - don't apply velocity
                    sprite.change_x = 0
                    sprite.center_x = left  # Set to boundary
                else:
                    # Safe to apply velocity
                    sprite.change_x = dx

                # Check if applying velocity would cross vertical boundary
                if dy > 0 and sprite.center_y + dy > top:
                    # Would cross top boundary - don't apply velocity
                    sprite.change_y = 0
                    sprite.center_y = top  # Set to boundary
                elif dy < 0 and sprite.center_y + dy < bottom:
                    # Would cross bottom boundary - don't apply velocity
                    sprite.change_y = 0
                    sprite.center_y = bottom  # Set to boundary
                else:
                    # Safe to apply velocity
                    sprite.change_y = dy
            else:
                # Normal behavior for other boundary types or no boundaries
                sprite.change_x = dx
                sprite.change_y = dy

        self.for_each_sprite(set_velocity)

    def update_effect(self, delta_time: float) -> None:
        """Update movement and handle boundary checking if enabled."""
        # Handle duration-based conditions using simulation time
        if self._duration is not None:
            self._elapsed += delta_time

            # Check if duration has elapsed
            if self._elapsed >= self._duration:
                # End immediately and clear velocities to avoid carryover into next actions
                self._condition_met = True
                self.remove_effect()
                self.done = True
                if self.on_stop:
                    self.on_stop()
                return

        # Check boundaries if configured
        if self.bounds and self.boundary_behavior:
            self.for_each_sprite(self._check_boundaries)

    def _check_boundaries(self, sprite) -> None:
        """Check and handle boundary interactions for a single sprite."""
        if not self.bounds:
            return

        left, bottom, right, top = self.bounds

        # Check each axis independently
        self._process_axis_boundary(sprite, sprite.center_x, left, right, sprite.change_x, "x")
        self._process_axis_boundary(sprite, sprite.center_y, bottom, top, sprite.change_y, "y")

    def _process_axis_boundary(self, sprite, position, low_bound, high_bound, velocity, axis):
        """Process boundary interaction for a single axis."""
        if position <= low_bound or position >= high_bound:
            # Apply boundary behavior
            self._apply_boundary_behavior(sprite, position, low_bound, high_bound, velocity, axis)

            # Call boundary callback if configured
            if self.on_boundary:
                self.on_boundary(sprite, axis)

    def _apply_boundary_behavior(self, sprite, position, low_bound, high_bound, velocity, axis):
        """Apply the specific boundary behavior for an axis."""
        behavior_handlers = {
            "bounce": self._bounce_behavior,
            "wrap": self._wrap_behavior,
            "limit": self._limit_behavior,
        }

        handler = behavior_handlers.get(self.boundary_behavior)
        if handler:
            handler(sprite, position, low_bound, high_bound, velocity, axis)

    def _bounce_behavior(self, sprite, position, low_bound, high_bound, velocity, axis):
        """Handle bounce boundary behavior."""
        if axis == "x":
            sprite.change_x = -sprite.change_x
            self.current_velocity = (-self.current_velocity[0], self.current_velocity[1])
            self.target_velocity = (-self.target_velocity[0], self.target_velocity[1])
            # Keep sprite in bounds
            if sprite.center_x <= low_bound:
                sprite.center_x = low_bound
            elif sprite.center_x >= high_bound:
                sprite.center_x = high_bound
        else:  # axis == "y"
            sprite.change_y = -sprite.change_y
            self.current_velocity = (self.current_velocity[0], -self.current_velocity[1])
            self.target_velocity = (self.target_velocity[0], -self.target_velocity[1])
            # Keep sprite in bounds
            if sprite.center_y <= low_bound:
                sprite.center_y = low_bound
            elif sprite.center_y >= high_bound:
                sprite.center_y = high_bound

    def _wrap_behavior(self, sprite, position, low_bound, high_bound, velocity, axis):
        """Handle wrap boundary behavior."""
        if axis == "x":
            if sprite.center_x <= low_bound:
                sprite.center_x = high_bound
            elif sprite.center_x >= high_bound:
                sprite.center_x = low_bound
        else:  # axis == "y"
            if sprite.center_y <= low_bound:
                sprite.center_y = high_bound
            elif sprite.center_y >= high_bound:
                sprite.center_y = low_bound

    def _limit_behavior(self, sprite, position, low_bound, high_bound, velocity, axis):
        """Handle limit boundary behavior."""
        if axis == "x":
            if position < low_bound:
                sprite.center_x = low_bound
                sprite.change_x = 0
                self.current_velocity = (0, self.current_velocity[1])
                self.target_velocity = (0, self.target_velocity[1])
            elif position > high_bound:
                sprite.center_x = high_bound
                sprite.change_x = 0
                self.current_velocity = (0, self.current_velocity[1])
                self.target_velocity = (0, self.target_velocity[1])
        else:  # axis == "y"
            if position < low_bound:
                sprite.center_y = low_bound
                sprite.change_y = 0
                self.current_velocity = (self.current_velocity[0], 0)
                self.target_velocity = (self.target_velocity[0], 0)
            elif position > high_bound:
                sprite.center_y = high_bound
                sprite.change_y = 0
                self.current_velocity = (self.current_velocity[0], 0)
                self.target_velocity = (self.target_velocity[0], 0)

    def remove_effect(self) -> None:
        """Clear velocities when the action finishes to avoid carryover between actions."""

        def clear_velocity(sprite):
            sprite.change_x = 0
            sprite.change_y = 0

        self.for_each_sprite(clear_velocity)

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Allow external code to modify current velocity (for easing wrapper compatibility).

        This enables easing wrappers to gradually modify the velocity over time,
        such as for startup acceleration from zero to target velocity.

        Args:
            velocity: (dx, dy) velocity tuple to apply
        """
        self.current_velocity = velocity
        if not self.done:
            self.apply_effect()  # Immediately apply velocity to sprites

    def remove_effect(self) -> None:
        """Stop movement by clearing velocity on all sprites."""

        def clear_velocity(sprite):
            sprite.change_x = 0
            sprite.change_y = 0

        self.for_each_sprite(clear_velocity)

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

    def reset(self) -> None:
        """Reset velocity to original target velocity."""
        self.current_velocity = self.target_velocity
        self.apply_effect()

    def clone(self) -> "MoveUntil":
        """Create a copy of this MoveUntil action."""
        return MoveUntil(
            self.target_velocity,  # Use target_velocity for cloning
            _clone_condition(self.condition),
            self.on_stop,
            self.bounds,
            self.boundary_behavior,
            self.on_boundary,
        )


class FollowPathUntil(_Action):
    """Follow a Bezier curve path at constant velocity until a condition is satisfied.

    Unlike duration-based Bezier actions, this maintains constant speed along the curve
    and can be interrupted by any condition (collision, position, time, etc.).

    The action supports automatic sprite rotation to face the movement direction, with
    calibration offset for sprites that aren't naturally drawn pointing to the right.

    Args:
        control_points: List of (x, y) points defining the Bezier curve (minimum 2 points)
        velocity: Speed in pixels per second along the curve
        condition: Function that returns truthy value when path following should stop
        on_stop: Optional callback called when condition is satisfied
        rotate_with_path: When True, automatically rotates sprite to face movement direction.
            When False (default), sprite maintains its original orientation.
        rotation_offset: Rotation offset in degrees to calibrate sprite's natural orientation.
            Use this when sprite artwork doesn't point to the right by default:
            - 0.0 (default): Sprite artwork points right
            - -90.0: Sprite artwork points up
            - 180.0: Sprite artwork points left
            - 90.0: Sprite artwork points down

    Examples:
        # Basic path following without rotation
        action = FollowPathUntil([(100, 100), (200, 200)], velocity=150, condition=duration(3.0))

        # Path following with automatic rotation (sprite artwork points right)
        action = FollowPathUntil(
            [(100, 100), (200, 200)], velocity=150, condition=duration(3.0),
            rotate_with_path=True
        )

        # Path following with rotation for sprite artwork that points up by default
        action = FollowPathUntil(
            [(100, 100), (200, 200)], velocity=150, condition=duration(3.0),
            rotate_with_path=True, rotation_offset=-90.0
        )

        # Complex curved path with rotation
        bezier_points = [(100, 100), (150, 200), (250, 150), (300, 100)]
        action = FollowPathUntil(
            bezier_points, velocity=200, condition=lambda: sprite.center_x > 400,
            rotate_with_path=True
        )
    """

    def __init__(
        self,
        control_points: list[tuple[float, float]],
        velocity: float,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        rotate_with_path: bool = False,
        rotation_offset: float = 0.0,
    ):
        super().__init__(condition, on_stop)
        if len(control_points) < 2:
            raise ValueError("Must specify at least 2 control points")

        self.control_points = control_points
        self.target_velocity = velocity  # Immutable target velocity
        self.current_velocity = velocity  # Current velocity (can be scaled)
        self.rotate_with_path = rotate_with_path  # Enable automatic sprite rotation
        self.rotation_offset = rotation_offset  # Degrees to offset for sprite artwork orientation

        # Track last applied movement angle to smooth out rotations when
        # the incremental movement vector becomes (nearly) zero – e.g. when
        # a path repeats and the sprite is momentarily stationary.
        self._prev_movement_angle: float | None = None

        # Path traversal state
        self._curve_progress = 0.0  # Progress along curve: 0.0 (start) to 1.0 (end)
        self._curve_length = 0.0  # Total length of the curve in pixels
        self._last_position = None  # Previous position for calculating movement delta

    def set_factor(self, factor: float) -> None:
        """Scale the path velocity by the given factor.

        Args:
            factor: Scaling factor for path velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_velocity = self.target_velocity * factor
        # No immediate apply needed - velocity is used in update_effect

    def _bezier_point(self, t: float) -> tuple[float, float]:
        """Calculate point on Bezier curve at parameter t (0-1)."""
        n = len(self.control_points) - 1
        x = y = 0
        for i, point in enumerate(self.control_points):
            # Binomial coefficient * (1-t)^(n-i) * t^i
            coef = math.comb(n, i) * (1 - t) ** (n - i) * t**i
            x += point[0] * coef
            y += point[1] * coef
        return (x, y)

    def _calculate_curve_length(self, samples: int = 100) -> float:
        """Approximate curve length by sampling points."""
        length = 0.0
        prev_point = self._bezier_point(0.0)

        for i in range(1, samples + 1):
            t = i / samples
            current_point = self._bezier_point(t)
            dx = current_point[0] - prev_point[0]
            dy = current_point[1] - prev_point[1]
            length += math.sqrt(dx * dx + dy * dy)
            prev_point = current_point

        return length

    def apply_effect(self) -> None:
        """Initialize path following and rotation state."""
        # Calculate curve length for constant velocity movement
        self._curve_length = self._calculate_curve_length()
        self._curve_progress = 0.0

        # Set initial position on the curve
        start_point = self._bezier_point(0.0)
        self._last_position = start_point

        # Snap target(s) to the exact start point to guarantee continuity across repeats
        def snap_to_start(sprite):
            sprite.center_x = start_point[0]
            sprite.center_y = start_point[1]

        self.for_each_sprite(snap_to_start)

    def update_effect(self, delta_time: float) -> None:
        """Update path following with constant velocity and optional rotation."""
        if self._curve_length <= 0:
            return

        # Calculate how far to move along curve based on velocity
        distance_per_frame = self.current_velocity * delta_time
        progress_delta = distance_per_frame / self._curve_length
        self._curve_progress = min(1.0, self._curve_progress + progress_delta)

        # Calculate new position on curve
        current_point = self._bezier_point(self._curve_progress)

        # Apply relative movement to sprite(s)
        if self._last_position:
            dx = current_point[0] - self._last_position[0]
            dy = current_point[1] - self._last_position[1]

            # Calculate sprite rotation angle to face movement direction
            movement_angle: float | None = None
            if self.rotate_with_path:
                # Determine if the incremental vector is significant.  Very small
                # vectors occur when a closed path repeats and the sprite is
                # effectively stationary for one frame; using such a vector for
                # direction calculation causes a visible rotation jump.
                if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                    direction_angle = math.degrees(math.atan2(dy, dx))
                    movement_angle = direction_angle + self.rotation_offset
                    self._prev_movement_angle = movement_angle
                else:
                    # Re-use the previous angle to maintain continuity
                    movement_angle = self._prev_movement_angle

            def apply_movement(sprite):
                # Move sprite along the path
                sprite.center_x += dx
                sprite.center_y += dy
                # Rotate sprite to face movement direction if enabled
                if movement_angle is not None:
                    sprite.angle = movement_angle

            self.for_each_sprite(apply_movement)

        self._last_position = current_point

        # Check if we've reached the end of the path
        if self._curve_progress >= 1.0:
            # Path completed - trigger condition
            self._condition_met = True
            self.done = True
            if self.on_stop:
                self.on_stop(None)

    def remove_effect(self) -> None:
        """Ensure exact end-point alignment when finishing the path.

        This prevents visible offsets when a hitch causes completion in the same
        frame and a new iteration starts immediately under _Repeat.
        """
        try:
            end_point = self._bezier_point(1.0)
        except Exception:
            return

        def snap_to_end(sprite):
            sprite.center_x = end_point[0]
            sprite.center_y = end_point[1]

        self.for_each_sprite(snap_to_end)

    def clone(self) -> "FollowPathUntil":
        """Create a copy of this FollowPathUntil action with all parameters preserved."""
        return FollowPathUntil(
            self.control_points.copy(),
            self.target_velocity,
            _clone_condition(self.condition),
            self.on_stop,
            self.rotate_with_path,
            self.rotation_offset,
        )


class RotateUntil(_Action):
    """Rotate a sprite or sprite list until a condition is satisfied.

    Args:
        angular_velocity: The angular velocity in degrees per frame
        condition: Function that returns truthy value when rotation should stop
        on_stop: Optional callback called when condition is satisfied
    """

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
        """Scale the angular velocity by the given factor.

        Args:
            factor: Scaling factor for angular velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_angular_velocity = self.target_angular_velocity * factor
        # Immediately apply the new angular velocity if action is active
        if not self.done and self.target is not None:
            self.apply_effect()

    def apply_effect(self) -> None:
        """Apply angular velocity to all sprites."""

        def set_angular_velocity(sprite):
            sprite.change_angle = self.current_angular_velocity

        self.for_each_sprite(set_angular_velocity)

    def remove_effect(self) -> None:
        """Stop rotation by clearing angular velocity on all sprites."""

        def clear_angular_velocity(sprite):
            sprite.change_angle = 0

        self.for_each_sprite(clear_angular_velocity)

    def clone(self) -> "RotateUntil":
        """Create a copy of this RotateUntil action."""
        return RotateUntil(self.target_angular_velocity, _clone_condition(self.condition), self.on_stop)


class ScaleUntil(_Action):
    """Scale a sprite or sprite list until a condition is satisfied.

    Args:
        scale_velocity: The scale velocity per frame
        condition: Function that returns truthy value when scaling should stop
        on_stop: Optional callback called when condition is satisfied
    """

    def __init__(
        self,
        scale_velocity: float,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        super().__init__(condition, on_stop)
        # Normalize scale_velocity to always be a tuple
        if isinstance(scale_velocity, int | float):
            self.target_scale_velocity = (scale_velocity, scale_velocity)
        else:
            self.target_scale_velocity = scale_velocity
        self.current_scale_velocity = self.target_scale_velocity  # Current rate (can be scaled)
        self._original_scales = {}

    def set_factor(self, factor: float) -> None:
        """Scale the scale velocity by the given factor.

        Args:
            factor: Scaling factor for scale velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_scale_velocity = (self.target_scale_velocity[0] * factor, self.target_scale_velocity[1] * factor)
        # No immediate apply needed - scaling happens in update_effect

    def apply_effect(self) -> None:
        """Start scaling - store original scales for velocity calculation."""

        def store_original_scale(sprite):
            self._original_scales[id(sprite)] = (sprite.scale, sprite.scale)

        self.for_each_sprite(store_original_scale)

    def update_effect(self, delta_time: float) -> None:
        """Apply scaling based on velocity."""
        sx, sy = self.current_scale_velocity
        scale_delta_x = sx * delta_time
        scale_delta_y = sy * delta_time

        def apply_scale(sprite):
            # Get current scale (which is a tuple in arcade)
            current_scale = sprite.scale
            if isinstance(current_scale, tuple):
                current_scale_x, current_scale_y = current_scale
            else:
                # Handle case where scale might be a single value
                current_scale_x = current_scale_y = current_scale

            # Apply scale velocity (avoiding negative scales)
            new_scale_x = max(0.01, current_scale_x + scale_delta_x)
            new_scale_y = max(0.01, current_scale_y + scale_delta_y)
            sprite.scale = (new_scale_x, new_scale_y)

        self.for_each_sprite(apply_scale)

    def clone(self) -> "ScaleUntil":
        """Create a copy of this action."""
        return ScaleUntil(self.target_scale_velocity, _clone_condition(self.condition), self.on_stop)


class FadeUntil(_Action):
    """Fade sprites until a condition is satisfied.

    Args:
        fade_velocity: The fade velocity per frame (change in alpha)
        condition: Function that returns truthy value when fading should stop
        on_stop: Optional callback called when condition is satisfied
    """

    def __init__(
        self,
        fade_velocity: float,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        super().__init__(condition, on_stop)
        self.target_fade_velocity = fade_velocity  # Immutable target velocity
        self.current_fade_velocity = fade_velocity  # Current velocity (can be scaled)

    def set_factor(self, factor: float) -> None:
        """Scale the fade velocity by the given factor.

        Args:
            factor: Scaling factor for fade velocity (0.0 = stopped, 1.0 = full speed)
        """
        self.current_fade_velocity = self.target_fade_velocity * factor
        # No immediate apply needed - fading happens in update_effect

    def update_effect(self, delta_time: float) -> None:
        """Apply fading based on velocity."""
        alpha_delta = self.current_fade_velocity * delta_time

        def apply_fade(sprite):
            new_alpha = sprite.alpha + alpha_delta
            sprite.alpha = max(0, min(255, new_alpha))  # Clamp to valid range

        self.for_each_sprite(apply_fade)

    def clone(self) -> "FadeUntil":
        """Create a copy of this action."""
        return FadeUntil(self.target_fade_velocity, _clone_condition(self.condition), self.on_stop)


class BlinkUntil(_Action):
    """Blink sprites (toggle visibility) until a condition is satisfied.

    Args:
        seconds_until_change: Seconds to wait before toggling visibility
        condition: Function that returns truthy value when blinking should stop
        on_stop: Optional callback called when condition is satisfied
    """

    def __init__(
        self,
        seconds_until_change: float,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        if seconds_until_change <= 0:
            raise ValueError("seconds_until_change must be positive")

        super().__init__(condition, on_stop)
        self.target_seconds_until_change = seconds_until_change  # Immutable target rate
        self.current_seconds_until_change = seconds_until_change  # Current rate (can be scaled)
        self._blink_elapsed = 0.0
        self._original_visibility = {}

    def set_factor(self, factor: float) -> None:
        """Scale the blink rate by the given factor.

        Factor affects the time between blinks - higher factor = faster blinking.
        A factor of 0.0 stops blinking (sprites stay in current visibility state).

        Args:
            factor: Scaling factor for blink rate (0.0 = stopped, 1.0 = normal speed, 2.0 = double speed)
        """
        if factor <= 0:
            # Stop blinking - set to a very large value
            self.current_seconds_until_change = float("inf")
        else:
            # Faster factor = shorter time between changes
            self.current_seconds_until_change = self.target_seconds_until_change / factor

    def apply_effect(self) -> None:
        """Store original visibility for all sprites."""

        def store_visibility(sprite):
            self._original_visibility[id(sprite)] = sprite.visible

        self.for_each_sprite(store_visibility)

    def remove_effect(self) -> None:
        """Restore original visibility for all sprites."""

        def restore_visibility(sprite):
            original_visible = self._original_visibility.get(id(sprite), True)
            sprite.visible = original_visible

        self.for_each_sprite(restore_visibility)

    def update_effect(self, delta_time: float) -> None:
        """Apply blinking effect based on the configured interval."""
        self._blink_elapsed += delta_time
        # Determine how many intervals have passed to know whether we should show or hide.
        cycles = int(self._blink_elapsed / self.current_seconds_until_change)

        def apply_blink(sprite):
            # Even cycles: visible, odd cycles: invisible
            sprite.visible = cycles % 2 == 0

        self.for_each_sprite(apply_blink)

    def reset(self) -> None:
        """Reset blinking rate to original target rate."""
        self.current_seconds_until_change = self.target_seconds_until_change

    def clone(self) -> "BlinkUntil":
        """Create a copy of this action."""
        return BlinkUntil(self.target_seconds_until_change, _clone_condition(self.condition), self.on_stop)


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
        # Try to extract duration from the condition function if it's from duration() helper
        self._duration = None
        try:
            # Check if condition is from duration() helper by looking for closure
            if (
                hasattr(self.condition, "__closure__")
                and self.condition.__closure__
                and len(self.condition.__closure__) >= 1
            ):
                # Get the seconds value from the closure
                seconds = self.condition.__closure__[0].cell_contents
                if isinstance(seconds, (int, float)) and seconds > 0:
                    self._duration = seconds
        except (AttributeError, IndexError, TypeError):
            pass

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


class TweenUntil(_Action):
    """Directly animate a sprite property from start to end value with precise control.

    TweenUntil is perfect for A-to-B property animations like UI elements sliding into position,
    health bars updating, button feedback, or fade effects. Unlike Ease (which modulates continuous
    actions), TweenUntil directly sets property values and completes when the end value is reached.

    Use TweenUntil when you need:
    - Precise property animation (position, scale, alpha, etc.)
    - UI element animations (panels, buttons, menus)
    - Value transitions (health bars, progress indicators)
    - Simple A-to-B movements that should stop at the target

    Use Ease instead when you need:
    - Smooth acceleration/deceleration of continuous movement
    - Complex path following with smooth transitions
    - Actions that should continue after the easing completes

    Args:
        start_value: Starting value for the property being tweened
        end_value: Ending value for the property being tweened
        property_name: Name of the sprite property to tween ('center_x', 'center_y', 'angle', 'scale', 'alpha')
        condition: Function that returns truthy value when tweening should stop
        on_stop: Optional callback called when condition is satisfied
        ease_function: Easing function to use for tweening (default: linear)

    Examples:
        # UI panel slide-in animation
        slide_in = TweenUntil(-200, 100, "center_x", duration(0.8), ease_function=easing.ease_out)
        slide_in.apply(ui_panel, tag="show_panel")

        # Health bar update
        health_change = TweenUntil(old_health, new_health, "width", duration(0.5))
        health_change.apply(health_bar, tag="health_update")

        # Button press feedback
        button_press = TweenUntil(1.0, 1.2, "scale", duration(0.1))
        button_press.apply(button, tag="press_feedback")

        # Fade effect
        fade_out = TweenUntil(255, 0, "alpha", duration(1.0))
        fade_out.apply(sprite, tag="disappear")
    """

    def __init__(
        self,
        start_value: float,
        end_value: float,
        property_name: str,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        ease_function: Callable[[float], float] | None = None,
    ):
        super().__init__(condition=condition, on_stop=on_stop)
        self.start_value = start_value
        self.end_value = end_value
        self.property_name = property_name
        self.ease_function = ease_function or (lambda t: t)
        self._duration = None
        self._tween_elapsed = 0.0
        self._completed_naturally = False  # Track if action completed vs was stopped

    def update(self, delta_time: float) -> None:
        """
        Override update to ensure tween logic runs before condition check.
        This prevents race conditions where condition is met before _completed_naturally is set.
        """
        if not self._is_active or self.done or self._paused:
            return

        # Update the tween effect first - this may set _completed_naturally and self.done
        self.update_effect(delta_time)

        # If tween completed naturally during update_effect, we're done
        if self.done:
            return

        # Now check external condition
        if self.condition and not self._condition_met:
            condition_result = self.condition()
            if condition_result:
                self._condition_met = True
                self.condition_data = condition_result

                self.remove_effect()
                self.done = True
                if self.on_stop:
                    if condition_result is not True:
                        self.on_stop(condition_result)
                    else:
                        self.on_stop()

    def set_factor(self, factor: float) -> None:
        """Scale the tween speed by the given factor.

        Args:
            factor: Scaling factor for tween speed (0.0 = stopped, 1.0 = normal speed)
        """
        self._factor = factor

    def apply_effect(self):
        # Extract duration (explicit or closure) FIRST
        duration_val = 1.0
        try:
            # EAFP: Try to get duration from the closure of the `duration` helper.
            # This is more Pythonic and robust than checking function name with hasattr.
            if self.condition.__name__ == "condition":
                duration_val = self.condition.__closure__[0].cell_contents
        except (AttributeError, IndexError, TypeError):
            # This is expected if condition is not from `duration()` or has no closure.
            pass

        # An explicitly set duration should override the one from the condition.
        if self._duration is not None:
            duration_val = self._duration

        self._duration = duration_val
        if self._duration < 0:
            raise ValueError("Duration must be non-negative")

        # Define a helper to set the initial value, using EAFP for property validation.
        def set_initial_value(sprite):
            """Set the initial value of the property on a single sprite."""
            try:
                setattr(sprite, self.property_name, self.start_value)
            except AttributeError:
                raise AttributeError(f"Target sprite does not have property '{self.property_name}'")

        if self._duration == 0:
            # If duration is zero, immediately set to the end value.
            self.for_each_sprite(lambda sprite: setattr(sprite, self.property_name, self.end_value))
            self.done = True
            if self.on_stop:
                self.on_stop(None)
            return

        # For positive duration, set the initial value on all sprites.
        self.for_each_sprite(set_initial_value)
        self._tween_elapsed = 0.0

    def update_effect(self, delta_time: float):
        if self.done:
            return

        # Update elapsed time with factor applied
        self._tween_elapsed += delta_time * self._factor

        # Calculate progress (0 to 1)
        t = min(self._tween_elapsed / self._duration, 1.0)
        eased_t = self.ease_function(t)

        # Calculate current value
        value = self.start_value + (self.end_value - self.start_value) * eased_t

        # Apply the value to all target sprites
        self.for_each_sprite(lambda sprite: setattr(sprite, self.property_name, value))

        # Check for completion
        if t >= 1.0:
            # Ensure we set the exact end value

            self.for_each_sprite(lambda sprite: setattr(sprite, self.property_name, self.end_value))
            self._completed_naturally = True  # Mark as naturally completed
            self.done = True

            if self.on_stop:
                self.on_stop(None)

    def remove_effect(self) -> None:
        """Clean up the tween effect.

        If the action completed naturally or reached its full duration, leave the property at its final value.
        If the action was stopped prematurely, reset to start value.
        """
        # Check if tween reached its natural end, even if condition was met first
        reached_natural_end = self._duration is not None and self._tween_elapsed >= self._duration

        if not self._completed_naturally and not reached_natural_end:
            # Action was stopped before completion - reset to start value
            self.for_each_sprite(lambda sprite: setattr(sprite, self.property_name, self.start_value))
        # If action completed naturally or reached full duration, leave property at end value

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self._tween_elapsed = 0.0
        self._duration = None
        self._completed_naturally = False

    def clone(self) -> "TweenUntil":
        return TweenUntil(
            self.start_value,
            self.end_value,
            self.property_name,
            _clone_condition(self.condition),
            self.on_stop,
            self.ease_function,
        )

    def set_duration(self, duration: float) -> None:
        raise NotImplementedError


class CallbackUntil(_Action):
    """Execute a callback function until a condition is satisfied.

    The callback is called every frame while the action is active.

    Args:
        callback: Function to call every frame
        condition: Function that returns truthy value when callbacks should stop
        on_stop: Optional callback called when condition is satisfied
    """

    def __init__(
        self,
        callback: Callable[[], None],
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    ):
        super().__init__(condition=condition, on_stop=on_stop)
        self.callback = callback

    def update_effect(self, delta_time: float) -> None:
        """Call the callback function."""
        if self.callback:
            self.callback()

    def clone(self) -> "CallbackUntil":
        """Create a copy of this action."""
        return CallbackUntil(
            self.callback,
            _clone_condition(self.condition),
            self.on_stop,
        )


# Helper function for cloning conditions
def _clone_condition(condition):
    """Create a fresh copy of a condition, especially for duration conditions."""
    if hasattr(condition, "_is_duration_condition") and condition._is_duration_condition:
        # Create a fresh duration condition
        return duration(condition._duration_seconds)
    else:
        # For non-duration conditions, return as-is
        return condition


# Common condition functions
def duration(seconds: float):
    """Create a condition function that returns True after a specified duration.

    Usage:
        # Move for 2 seconds
        MoveUntil((100, 0), duration(2.0))

        # Blink (toggle visibility every 0.25 seconds) for 3 seconds
        BlinkUntil(0.25, duration(3.0))

        # Delay for 1 second
        DelayUntil(duration(1.0))

        # Follow path for 5 seconds
        FollowPathUntil(points, 150, duration(5.0))
    """
    start_time = None

    def condition():
        nonlocal start_time
        import time

        if start_time is None:
            start_time = time.time()
        return time.time() - start_time >= seconds

    # Mark this as a duration condition for cloning purposes
    condition._is_duration_condition = True
    condition._duration_seconds = seconds

    def reset_duration():
        nonlocal start_time
        start_time = None

    condition._reset_duration = reset_duration

    return condition


def infinite() -> Callable[[], bool]:
    """Create a condition function that never returns True.

    Use this for actions that should continue indefinitely until explicitly stopped.

    Usage:
        # Move forever (or until action is stopped externally)
        move_until(sprite, (100, 0), infinite())

        # Rotate continuously
        rotate_until(sprite, 45, infinite())
    """

    return False


# =========================
# Relative parametric motion
# =========================
from collections.abc import Callable as _Callable
from typing import Any as _Any


class ParametricMotionUntil(_Action):
    """Move sprites along a relative parametric curve.

    The *offset_fn* receives progress *t* (0→1) and returns (dx, dy) offsets that
    are **added** to each sprite's origin captured at *apply* time.  Completion is
    governed by the same *condition* mechanism used elsewhere (typically the
    ``duration()`` helper).
    """

    def __init__(
        self,
        offset_fn: _Callable[[float], tuple[float, float]],
        condition: _Callable[[], _Any],
        on_stop: _Callable[[_Any], None] | _Callable[[], None] | None = None,
        *,
        explicit_duration: float | None = None,
        rotate_with_path: bool = False,
        rotation_offset: float = 0.0,
        # --- debug ---
        debug: bool = False,
        debug_threshold: float | None = None,
    ):
        super().__init__(condition=condition, on_stop=on_stop)
        self._offset_fn = offset_fn
        self._origins: dict[int, tuple[float, float]] = {}
        self._elapsed = 0.0
        self._duration = explicit_duration  # May be filled in apply_effect
        self.rotate_with_path = rotate_with_path
        self.rotation_offset = rotation_offset
        self._prev_offset = None  # Track previous offset for rotation calculation

        # Debug helpers
        self._debug = debug
        self._debug_threshold = debug_threshold if debug_threshold is not None else 120.0  # px / frame

    # --------------------- Action hooks --------------------
    def apply_effect(self) -> None:  # noqa: D401 – imperative style
        """Memorise origins and determine duration."""

        def capture_origin(sprite):
            self._origins[id(sprite)] = (sprite.center_x, sprite.center_y)

        self.for_each_sprite(capture_origin)

        if self._duration is None:
            # Try to extract duration from the condition function if it's from duration() helper
            try:
                # Check if condition is from duration() helper by looking for closure
                if (
                    hasattr(self.condition, "__closure__")
                    and self.condition.__closure__
                    and len(self.condition.__closure__) >= 1
                ):
                    # Get the seconds value from the closure
                    seconds = self.condition.__closure__[0].cell_contents
                    if isinstance(seconds, (int, float)) and seconds > 0:
                        self._duration = seconds
            except (AttributeError, IndexError, TypeError):
                pass

            # Fallback to the helper function if the above didn't work
            if self._duration is None or self._duration == 0:
                self._duration = _extract_duration_seconds(self.condition) or 0.0

        # Do not pre-position sprites; offsets are relative to captured origins
        self._prev_offset = self._offset_fn(0.0)

    def update_effect(self, delta_time: float) -> None:  # noqa: D401
        self._elapsed += delta_time * self._factor
        progress = min(1.0, self._elapsed / self._duration) if self._duration > 0 else 1.0

        # Clamp progress to 1.0 for offset calculation to ensure exact endpoint positioning
        clamped_progress = min(1.0, progress)
        current_offset = self._offset_fn(clamped_progress)
        dx, dy = current_offset

        # Calculate rotation if enabled
        sprite_angle = None
        if self.rotate_with_path and self._prev_offset is not None:
            # Calculate movement vector from previous to current offset
            movement_dx = dx - self._prev_offset[0]
            movement_dy = dy - self._prev_offset[1]

            # Debug: detect large single-frame jumps in relative space
            if self._debug:
                import math
                import time as _t

                jump_mag = math.hypot(movement_dx, movement_dy)
                if jump_mag > self._debug_threshold:
                    stamp = f"{_t.time():.3f}"
                    print(
                        f"[ParametricMotionUntil:jump] t={stamp} Δ={jump_mag:.2f}px (thr={self._debug_threshold})"
                        f" prev_offset={self._prev_offset} new_offset={(dx, dy)}"
                    )
            # Only calculate angle if there's significant movement
            if abs(movement_dx) > 1e-6 or abs(movement_dy) > 1e-6:
                angle = math.degrees(math.atan2(movement_dy, movement_dx))
                sprite_angle = angle + self.rotation_offset

        # Apply movement and rotation
        def apply_transform(sprite):
            _apply_offset(sprite, dx, dy, self._origins)
            if sprite_angle is not None:
                sprite.angle = sprite_angle

        self.for_each_sprite(apply_transform)

        # Store current offset for next frame's rotation calculation
        self._prev_offset = current_offset

        if progress >= 1.0:
            # Skip final position snap to prevent jumps when sprite count changes
            # This happens when enemies are destroyed during wave patterns
            # self.remove_effect()  # commented out to prevent position jumps

            self._condition_met = True
            self.done = True

            if self.on_stop:
                self.on_stop(None)

    def remove_effect(self) -> None:
        """
        Skip position snapping to prevent jumps in repeated wave patterns.

        Originally this would snap sprites to exact endpoints for seamless
        repetition, but when sprite counts change (enemies destroyed) or
        multiple actions overlap, this causes visible position jumps.
        """
        # Disabled to prevent jumps - let patterns complete naturally
        pass

    def clone(self) -> "ParametricMotionUntil":  # type: ignore[name-defined]
        return ParametricMotionUntil(
            self._offset_fn,
            _clone_condition(self.condition),
            self.on_stop,
            explicit_duration=self._duration,
            rotate_with_path=self.rotate_with_path,
            rotation_offset=self.rotation_offset,
            debug=self._debug,
            debug_threshold=self._debug_threshold,
        )

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self._elapsed = 0.0
        self._origins.clear()
        self._prev_offset = None
        self._condition_met = False
        self.done = False

    def set_factor(self, factor: float) -> None:
        """Scale the motion speed by the given factor.

        Args:
            factor: Scaling factor for motion speed (0.0 = stopped, 1.0 = normal speed)
        """
        self._factor = factor


# ------------------ helpers ------------------


def _apply_offset(sprite, dx: float, dy: float, origins: dict[int, tuple[float, float]]):
    ox, oy = origins[id(sprite)]
    sprite.center_x = ox + dx
    sprite.center_y = oy + dy


def _extract_duration_seconds(cond: _Callable[[], _Any]) -> float | None:
    try:
        if cond.__name__ == "condition":
            return cond.__closure__[0].cell_contents  # type: ignore[index]
    except Exception:
        pass
    return None
