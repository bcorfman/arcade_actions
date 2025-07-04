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
        condition_func: Function that returns truthy value when movement should stop, or None/False to continue
        on_condition_met: Optional callback called when condition is satisfied. Receives condition data if provided.
        check_interval: How often to check condition (in seconds, default: 0.0 for every frame)
        bounds: Optional (left, bottom, right, top) boundary box for bouncing/wrapping
        boundary_behavior: "bounce", "wrap", or None (default: None for no boundary checking)
        on_boundary: Optional callback(sprite, axis) called when sprite hits boundary
    """

    def __init__(
        self,
        velocity: tuple[float, float],
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
        bounds: tuple[float, float, float, float] | None = None,
        boundary_behavior: str | None = None,
        on_boundary: Callable[[Any, str], None] | None = None,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        self.target_velocity = velocity  # Immutable target velocity
        self.current_velocity = velocity  # Current velocity (can be scaled by factor)

        # Boundary checking
        self.bounds = bounds  # (left, bottom, right, top)
        self.boundary_behavior = boundary_behavior
        self.on_boundary = on_boundary

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
        dx, dy = self.current_velocity

        def set_velocity(sprite):
            sprite.change_x = dx
            sprite.change_y = dy

        self.for_each_sprite(set_velocity)

    def update_effect(self, delta_time: float) -> None:
        """Update movement and handle boundary checking if enabled."""
        # Check boundaries if configured
        if self.bounds and self.boundary_behavior:
            self.for_each_sprite(self._check_boundaries)

    def _check_boundaries(self, sprite) -> None:
        """Check and handle boundary interactions for a single sprite."""
        if not self.bounds:
            return

        left, bottom, right, top = self.bounds

        # Check horizontal boundaries
        if sprite.center_x <= left or sprite.center_x >= right:
            if self.boundary_behavior == "bounce":
                sprite.change_x = -sprite.change_x
                self.current_velocity = (-self.current_velocity[0], self.current_velocity[1])
                # Also update target velocity to maintain factor scaling
                self.target_velocity = (-self.target_velocity[0], self.target_velocity[1])
                # Keep sprite in bounds
                if sprite.center_x <= left:
                    sprite.center_x = left
                elif sprite.center_x >= right:
                    sprite.center_x = right
            elif self.boundary_behavior == "wrap":
                if sprite.center_x <= left:
                    sprite.center_x = right
                elif sprite.center_x >= right:
                    sprite.center_x = left

            if self.on_boundary:
                self.on_boundary(sprite, "x")

        # Check vertical boundaries
        if sprite.center_y <= bottom or sprite.center_y >= top:
            if self.boundary_behavior == "bounce":
                sprite.change_y = -sprite.change_y
                self.current_velocity = (self.current_velocity[0], -self.current_velocity[1])
                # Also update target velocity to maintain factor scaling
                self.target_velocity = (self.target_velocity[0], -self.target_velocity[1])
                # Keep sprite in bounds
                if sprite.center_y <= bottom:
                    sprite.center_y = bottom
                elif sprite.center_y >= top:
                    sprite.center_y = top
            elif self.boundary_behavior == "wrap":
                if sprite.center_y <= bottom:
                    sprite.center_y = top
                elif sprite.center_y >= top:
                    sprite.center_y = bottom

            if self.on_boundary:
                self.on_boundary(sprite, "y")

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

    def clone(self) -> "MoveUntil":
        """Create a copy of this MoveUntil action."""
        return MoveUntil(
            self.target_velocity,  # Use target_velocity for cloning
            self.condition_func,
            self.on_condition_met,
            self.check_interval,
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
        condition_func: Function that returns truthy value when path following should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds, default: 0.0 for every frame)
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
        action = FollowPathUntil([(100, 100), (200, 200)], 150, duration(3.0))

        # Path following with automatic rotation (sprite artwork points right)
        action = FollowPathUntil(
            [(100, 100), (200, 200)], 150, duration(3.0),
            rotate_with_path=True
        )

        # Path following with rotation for sprite artwork that points up by default
        action = FollowPathUntil(
            [(100, 100), (200, 200)], 150, duration(3.0),
            rotate_with_path=True, rotation_offset=-90.0
        )

        # Complex curved path with rotation
        bezier_points = [(100, 100), (150, 200), (250, 150), (300, 100)]
        action = FollowPathUntil(
            bezier_points, 200, lambda: sprite.center_x > 400,
            rotate_with_path=True
        )
    """

    def __init__(
        self,
        control_points: list[tuple[float, float]],
        velocity: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
        rotate_with_path: bool = False,
        rotation_offset: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        if len(control_points) < 2:
            raise ValueError("Must specify at least 2 control points")

        self.control_points = control_points
        self.target_velocity = velocity  # Immutable target velocity
        self.current_velocity = velocity  # Current velocity (can be scaled)
        self.rotate_with_path = rotate_with_path  # Enable automatic sprite rotation
        self.rotation_offset = rotation_offset  # Degrees to offset for sprite artwork orientation

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
            movement_angle = None
            if self.rotate_with_path and (dx != 0 or dy != 0):
                # Calculate movement direction angle using atan2 for proper quadrant handling
                # atan2(dy, dx) returns angle in radians where:
                #   - 0 radians (0°) = moving right (+x direction)
                #   - π/2 radians (90°) = moving up (+y direction)
                #   - π radians (180°) = moving left (-x direction)
                #   - 3π/2 radians (270°) = moving down (-y direction)
                direction_angle = math.degrees(math.atan2(dy, dx))

                # Apply rotation offset to compensate for sprite artwork orientation
                # If sprite artwork points up by default, use offset=-90 to correct
                movement_angle = direction_angle + self.rotation_offset

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
            if self.on_condition_met:
                self.on_condition_met(None)

    def clone(self) -> "FollowPathUntil":
        """Create a copy of this FollowPathUntil action with all parameters preserved."""
        return FollowPathUntil(
            self.control_points.copy(),
            self.target_velocity,
            self.condition_func,
            self.on_condition_met,
            self.check_interval,
            self.rotate_with_path,
            self.rotation_offset,
        )


class RotateUntil(_Action):
    """Rotate sprites until a condition is satisfied.

    Args:
        angular_velocity: Degrees per second to rotate
        condition_func: Function that returns truthy value when rotation should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        angular_velocity: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        self.target_angular_velocity = angular_velocity  # Immutable target rate
        self.current_angular_velocity = angular_velocity  # Current rate (can be scaled)

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
        return RotateUntil(
            self.target_angular_velocity, self.condition_func, self.on_condition_met, self.check_interval
        )


class ScaleUntil(_Action):
    """Scale sprites until a condition is satisfied.

    Args:
        scale_velocity: Scale change per second (float for uniform, tuple for x/y)
        condition_func: Function that returns truthy value when scaling should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        scale_velocity: tuple[float, float] | float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
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
        """Create a copy of this ScaleUntil action."""
        return ScaleUntil(self.target_scale_velocity, self.condition_func, self.on_condition_met, self.check_interval)


class FadeUntil(_Action):
    """Fade sprites until a condition is satisfied.

    Args:
        fade_velocity: Alpha change per second (negative for fade out, positive for fade in)
        condition_func: Function that returns truthy value when fading should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        fade_velocity: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        self.target_fade_velocity = fade_velocity  # Immutable target rate
        self.current_fade_velocity = fade_velocity  # Current rate (can be scaled)

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
        """Create a copy of this FadeUntil action."""
        return FadeUntil(self.target_fade_velocity, self.condition_func, self.on_condition_met, self.check_interval)


class BlinkUntil(_Action):
    """Blink sprites (toggle visibility) until a condition is satisfied.

    Args:
        seconds_until_change: Seconds to wait before toggling visibility. For example, a value
            of ``0.5`` will cause the sprite to become invisible after half a second, then
            visible again after another half-second, resulting in one full *blink* per second.
        condition_func: Function that returns truthy value when blinking should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        seconds_until_change: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        if seconds_until_change <= 0:
            raise ValueError("seconds_until_change must be positive")

        super().__init__(condition_func, on_condition_met, check_interval)
        self.target_seconds_until_change = seconds_until_change  # Immutable target rate
        self.current_seconds_until_change = seconds_until_change  # Current rate (can be scaled)
        self._elapsed = 0.0
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

    def update_effect(self, delta_time: float) -> None:
        """Apply blinking effect based on the configured interval."""
        self._elapsed += delta_time
        # Determine how many intervals have passed to know whether we should show or hide.
        cycles = int(self._elapsed / self.current_seconds_until_change)

        def apply_blink(sprite):
            original_visible = self._original_visibility.get(id(sprite), True)
            sprite.visible = original_visible if cycles % 2 == 0 else not original_visible

        self.for_each_sprite(apply_blink)

    def remove_effect(self) -> None:
        """Restore original visibility for all sprites."""

        def restore_visibility(sprite):
            original_visible = self._original_visibility.get(id(sprite), True)
            sprite.visible = original_visible

        self.for_each_sprite(restore_visibility)

    def clone(self) -> "BlinkUntil":
        """Create a copy of this BlinkUntil action."""
        return BlinkUntil(
            self.target_seconds_until_change, self.condition_func, self.on_condition_met, self.check_interval
        )


class DelayUntil(_Action):
    """Wait/delay until a condition is satisfied.

    This action does nothing but wait for the condition to be met.
    Useful in sequences to create conditional pauses.

    Args:
        condition_func: Function that returns truthy value when delay should end
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)

    def clone(self) -> "DelayUntil":
        """Create a copy of this DelayUntil action."""
        return DelayUntil(self.condition_func, self.on_condition_met, self.check_interval)


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
        condition_func: Function that returns truthy value when tweening should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds, default: 0.0 for every frame)
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
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
        ease_function: Callable[[float], float] | None = None,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        self.start_value = start_value
        self.end_value = end_value
        self.property_name = property_name
        self.ease_function = ease_function or (lambda t: t)
        self._factor = 1.0
        self._duration = None
        self._elapsed = 0.0

    def set_factor(self, factor: float) -> None:
        self._factor = factor

    def apply_effect(self):
        # Extract duration (explicit or closure) FIRST
        duration_val = 1.0
        try:
            # EAFP: Try to get duration from the closure of the `duration` helper.
            # This is more Pythonic and robust than checking function name with hasattr.
            if self.condition_func.__name__ == "condition":
                duration_val = self.condition_func.__closure__[0].cell_contents
        except (AttributeError, IndexError, TypeError):
            # This is expected if condition_func is not from `duration()` or has no closure.
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
            if self.on_condition_met:
                self.on_condition_met(None)
            return

        # For positive duration, set the initial value on all sprites.
        self.for_each_sprite(set_initial_value)
        self._elapsed = 0.0

    def update_effect(self, delta_time: float):
        if self.done:
            return
        self._elapsed += delta_time * self._factor
        t = min(self._elapsed / self._duration, 1.0)
        eased_t = self.ease_function(t)

        # Determine the value to set based on progress
        if t < 1.0:
            value = self.start_value + (self.end_value - self.start_value) * eased_t
        else:
            value = self.end_value

        # Apply the value to all target sprites
        self.for_each_sprite(lambda sprite: setattr(sprite, self.property_name, value))

        # Check for completion
        if t >= 1.0:
            self.done = True
            if self.on_condition_met:
                self.on_condition_met(None)

    def remove_effect(self) -> None:
        pass

    def clone(self) -> "TweenUntil":
        return TweenUntil(
            self.start_value,
            self.end_value,
            self.property_name,
            self.condition_func,
            self.on_condition_met,
            self.check_interval,
            self.ease_function,
        )

    def set_duration(self, duration: float) -> None:
        raise NotImplementedError


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

    return condition
