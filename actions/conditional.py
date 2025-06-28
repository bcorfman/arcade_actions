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
        self.velocity = velocity
        self.current_velocity = velocity  # Enable future easing wrapper compatibility

        # Boundary checking
        self.bounds = bounds  # (left, bottom, right, top)
        self.boundary_behavior = boundary_behavior
        self.on_boundary = on_boundary

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
            self.velocity,
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

    Args:
        control_points: List of (x, y) points defining the Bezier curve
        velocity: Speed in pixels per second along the curve
        condition_func: Function that returns truthy value when path following should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        control_points: list[tuple[float, float]],
        velocity: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        if len(control_points) < 2:
            raise ValueError("Must specify at least 2 control points")

        self.control_points = control_points
        self.velocity = velocity

        # Path traversal state
        self._curve_progress = 0.0  # 0.0 to 1.0 along the curve
        self._curve_length = 0.0
        self._last_position = None

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
        """Initialize path following."""
        # Calculate curve length for constant velocity
        self._curve_length = self._calculate_curve_length()
        self._curve_progress = 0.0

        # Set initial position
        start_point = self._bezier_point(0.0)
        self._last_position = start_point

    def update_effect(self, delta_time: float) -> None:
        """Update path following with constant velocity."""
        if self._curve_length <= 0:
            return

        # Calculate how far to move along curve based on velocity
        distance_per_frame = self.velocity * delta_time
        progress_delta = distance_per_frame / self._curve_length
        self._curve_progress = min(1.0, self._curve_progress + progress_delta)

        # Calculate new position on curve
        current_point = self._bezier_point(self._curve_progress)

        # Apply relative movement to sprite(s)
        if self._last_position:
            dx = current_point[0] - self._last_position[0]
            dy = current_point[1] - self._last_position[1]

            def apply_movement(sprite):
                sprite.center_x += dx
                sprite.center_y += dy

            self.for_each_sprite(apply_movement)

        self._last_position = current_point

        # Check if we've reached the end of the path
        if self._curve_progress >= 1.0:
            # Path completed - trigger condition
            self._condition_met = True
            self.done = True

    def clone(self) -> "FollowPathUntil":
        """Create a copy of this FollowPathUntil action."""
        return FollowPathUntil(
            self.control_points.copy(), self.velocity, self.condition_func, self.on_condition_met, self.check_interval
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
        self.angular_velocity = angular_velocity

    def apply_effect(self) -> None:
        """Apply angular velocity to all sprites."""

        def set_angular_velocity(sprite):
            sprite.change_angle = self.angular_velocity

        self.for_each_sprite(set_angular_velocity)

    def remove_effect(self) -> None:
        """Stop rotation by clearing angular velocity on all sprites."""

        def clear_angular_velocity(sprite):
            sprite.change_angle = 0

        self.for_each_sprite(clear_angular_velocity)

    def clone(self) -> "RotateUntil":
        """Create a copy of this RotateUntil action."""
        return RotateUntil(self.angular_velocity, self.condition_func, self.on_condition_met, self.check_interval)


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
            self.scale_velocity = (scale_velocity, scale_velocity)
        else:
            self.scale_velocity = scale_velocity
        self._original_scales = {}

    def apply_effect(self) -> None:
        """Start scaling - store original scales for velocity calculation."""

        def store_original_scale(sprite):
            self._original_scales[id(sprite)] = (sprite.scale, sprite.scale)

        self.for_each_sprite(store_original_scale)

    def update_effect(self, delta_time: float) -> None:
        """Apply scaling based on velocity."""
        sx, sy = self.scale_velocity
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
        return ScaleUntil(self.scale_velocity, self.condition_func, self.on_condition_met, self.check_interval)


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
        self.fade_velocity = fade_velocity

    def update_effect(self, delta_time: float) -> None:
        """Apply fading based on velocity."""
        alpha_delta = self.fade_velocity * delta_time

        def apply_fade(sprite):
            new_alpha = sprite.alpha + alpha_delta
            sprite.alpha = max(0, min(255, new_alpha))  # Clamp to valid range

        self.for_each_sprite(apply_fade)

    def clone(self) -> "FadeUntil":
        """Create a copy of this FadeUntil action."""
        return FadeUntil(self.fade_velocity, self.condition_func, self.on_condition_met, self.check_interval)


class BlinkUntil(_Action):
    """Blink sprites (toggle visibility) until a condition is satisfied.

    Args:
        blink_rate: Blinks per second
        condition_func: Function that returns truthy value when blinking should stop
        on_condition_met: Optional callback called when condition is satisfied
        check_interval: How often to check condition (in seconds)
    """

    def __init__(
        self,
        blink_rate: float,
        condition_func: Callable[[], Any],
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
    ):
        super().__init__(condition_func, on_condition_met, check_interval)
        self.blink_rate = blink_rate
        self._blink_time = 0.0
        self._original_visibility = {}

    def apply_effect(self) -> None:
        """Store original visibility for all sprites."""

        def store_visibility(sprite):
            self._original_visibility[id(sprite)] = sprite.visible

        self.for_each_sprite(store_visibility)

    def update_effect(self, delta_time: float) -> None:
        """Apply blinking effect."""
        self._blink_time += delta_time
        blink_interval = 1.0 / (self.blink_rate * 2)  # Divide by 2 for on/off cycle
        current_blink_cycle = int(self._blink_time / blink_interval) % 2

        def apply_blink(sprite):
            original_visible = self._original_visibility.get(id(sprite), True)
            sprite.visible = original_visible if current_blink_cycle == 0 else not original_visible

        self.for_each_sprite(apply_blink)

    def remove_effect(self) -> None:
        """Restore original visibility for all sprites."""

        def restore_visibility(sprite):
            original_visible = self._original_visibility.get(id(sprite), True)
            sprite.visible = original_visible

        self.for_each_sprite(restore_visibility)

    def clone(self) -> "BlinkUntil":
        """Create a copy of this BlinkUntil action."""
        return BlinkUntil(self.blink_rate, self.condition_func, self.on_condition_met, self.check_interval)


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


# Common condition functions
def duration(seconds: float):
    """Create a condition function that returns True after a specified duration.

    Usage:
        # Move for 2 seconds
        MoveUntil((100, 0), duration(2.0))

        # Blink for 3 seconds
        BlinkUntil(2.0, duration(3.0))

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
