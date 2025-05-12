"""
Interval actions that happen over time.
"""

import math
import random

from .base import IntervalAction


class MoveTo(IntervalAction):
    """Move the sprite to a specific position over time."""

    def __init__(
        self,
        position: tuple[float, float] = None,
        duration: float = None,
        use_physics: bool = False,
    ):
        if position is None:
            raise ValueError("Must specify position")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.end_position = position
        self.use_physics = use_physics

    def start(self) -> None:
        self.start_position = self.target.position
        dx = self.end_position[0] - self.start_position[0]
        dy = self.end_position[1] - self.start_position[1]

        if self.use_physics and hasattr(self.target, "pymunk"):
            # Apply force to physics body
            force = (dx / self.duration, dy / self.duration)
            self.target.pymunk.apply_force_at_local_point(force)
        else:
            # Set velocity directly
            self.target.change_x = dx / self.duration
            self.target.change_y = dy / self.duration

    def update(self, delta_time: float) -> None:
        super().update(delta_time)

    def stop(self) -> None:
        if self.use_physics and hasattr(self.target, "pymunk"):
            # Clear any applied forces
            self.target.pymunk.force = (0, 0)
        else:
            self.target.change_x = 0
            self.target.change_y = 0
        super().stop()

    def __repr__(self) -> str:
        return f"MoveTo(position={self.end_position}, duration={self.duration}, use_physics={self.use_physics})"


class MoveBy(MoveTo):
    """Move the sprite by a relative amount over time."""

    def __init__(
        self,
        delta: tuple[float, float] = None,
        duration: float = None,
        use_physics: bool = False,
    ):
        if delta is None:
            raise ValueError("Must specify delta")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(delta, duration, use_physics)
        self.delta = delta

    def start(self) -> None:
        self.start_position = self.target.position
        dx, dy = self.delta

        if self.use_physics and hasattr(self.target, "pymunk"):
            # Apply force to physics body
            force = (dx / self.duration, dy / self.duration)
            self.target.pymunk.apply_force_at_local_point(force)
        else:
            # Set velocity directly
            self.target.change_x = dx / self.duration
            self.target.change_y = dy / self.duration

    def update(self, delta_time: float) -> None:
        super().update(delta_time)

    def __reversed__(self) -> "MoveBy":
        return MoveBy((-self.delta[0], -self.delta[1]), self.duration, self.use_physics)

    def __repr__(self) -> str:
        return f"MoveBy(delta={self.delta}, duration={self.duration}, use_physics={self.use_physics})"


class RotateTo(IntervalAction):
    """Rotate the sprite to a specific angle over time."""

    def __init__(self, angle: float = None, duration: float = None, use_physics: bool = False):
        if angle is None:
            raise ValueError("Must specify angle")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.end_angle = angle % 360
        self.use_physics = use_physics

    def start(self) -> None:
        self.start_angle = self.target.angle % 360
        # Calculate shortest rotation path
        angle_diff = ((self.end_angle - self.start_angle + 180) % 360) - 180

        if self.use_physics and hasattr(self.target, "pymunk"):
            # Apply torque to physics body
            torque = angle_diff / self.duration
            self.target.pymunk.torque = torque
        else:
            # Set angular velocity directly
            self.target.change_angle = angle_diff / self.duration

    def update(self, delta_time: float) -> None:
        super().update(delta_time)

    def stop(self) -> None:
        if self.use_physics and hasattr(self.target, "pymunk"):
            self.target.pymunk.torque = 0
        else:
            self.target.change_angle = 0
        super().stop()

    def __repr__(self) -> str:
        return f"RotateTo(angle={self.end_angle}, duration={self.duration}, use_physics={self.use_physics})"


class RotateBy(RotateTo):
    """Rotate the sprite by a relative amount over time."""

    def __init__(self, angle: float = None, duration: float = None, use_physics: bool = False):
        if angle is None:
            raise ValueError("Must specify angle")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(angle, duration, use_physics)
        self.angle = angle

    def start(self) -> None:
        if self.use_physics and hasattr(self.target, "pymunk"):
            # Apply torque to physics body
            torque = self.angle / self.duration
            self.target.pymunk.torque = torque
        else:
            # Set angular velocity directly
            self.target.change_angle = self.angle / self.duration

    def update(self, delta_time: float) -> None:
        super().update(delta_time)

    def __reversed__(self) -> "RotateBy":
        return RotateBy(-self.angle, self.duration, self.use_physics)

    def __repr__(self) -> str:
        return f"RotateBy(angle={self.angle}, duration={self.duration}, use_physics={self.use_physics})"


class ScaleTo(IntervalAction):
    """Scale the sprite to a specific size over time."""

    def __init__(self, scale: float = None, duration: float = None):
        if scale is None:
            raise ValueError("Must specify scale")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.end_scale = scale

    def start(self) -> None:
        self.start_scale = self.target.scale

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        # Linear interpolation between start and end scale
        progress = min(1.0, self._elapsed / self.duration)
        self.target.scale = self.start_scale + (self.end_scale - self.start_scale) * progress

    def stop(self) -> None:
        # Ensure we end exactly at the target scale
        self.target.scale = self.end_scale
        super().stop()

    def __repr__(self) -> str:
        return f"ScaleTo(scale={self.end_scale}, duration={self.duration})"


class ScaleBy(ScaleTo):
    """Scale the sprite by a relative amount over time."""

    def __init__(self, scale: float = None, duration: float = None):
        if scale is None:
            raise ValueError("Must specify scale")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(scale, duration)
        self.scale = scale

    def start(self) -> None:
        self.start_scale = self.target.scale
        self.end_scale = self.start_scale * self.scale

    def __reversed__(self) -> "ScaleBy":
        return ScaleBy(1.0 / self.scale, self.duration)

    def __repr__(self) -> str:
        return f"ScaleBy(scale={self.scale}, duration={self.duration})"


class FadeOut(IntervalAction):
    """Fade out the sprite over time."""

    def __init__(self, duration: float = None):
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)

    def start(self) -> None:
        self.start_alpha = self.target.alpha

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        # Linear interpolation from start alpha to 0
        progress = min(1.0, self._elapsed / self.duration)
        self.target.alpha = int(self.start_alpha * (1 - progress))

    def stop(self) -> None:
        # Ensure we end completely transparent
        self.target.alpha = 0
        super().stop()

    def __reversed__(self) -> "FadeIn":
        return FadeIn(self.duration)

    def __repr__(self) -> str:
        return f"FadeOut(duration={self.duration})"


class FadeIn(FadeOut):
    """Fade in the sprite over time."""

    def start(self) -> None:
        self.start_alpha = self.target.alpha

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        # Linear interpolation from start alpha to 255
        progress = min(1.0, self._elapsed / self.duration)
        self.target.alpha = int(self.start_alpha + (255 - self.start_alpha) * progress)

    def stop(self) -> None:
        # Ensure we end completely opaque
        self.target.alpha = 255
        super().stop()

    def __reversed__(self) -> "FadeOut":
        return FadeOut(self.duration)

    def __repr__(self) -> str:
        return f"FadeIn(duration={self.duration})"


class FadeTo(IntervalAction):
    """Fade the sprite to a specific alpha value over time."""

    def __init__(self, alpha: int = None, duration: float = None):
        if alpha is None:
            raise ValueError("Must specify alpha")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.alpha = min(255, max(0, alpha))

    def start(self) -> None:
        self.start_alpha = self.target.alpha

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        # Linear interpolation between start and target alpha
        progress = min(1.0, self._elapsed / self.duration)
        self.target.alpha = int(self.start_alpha + (self.alpha - self.start_alpha) * progress)

    def stop(self) -> None:
        # Ensure we end exactly at the target alpha
        self.target.alpha = self.alpha
        super().stop()

    def __repr__(self) -> str:
        return f"FadeTo(alpha={self.alpha}, duration={self.duration})"


class Blink(IntervalAction):
    """Blink the sprite by toggling visibility."""

    def __init__(self, times: int = None, duration: float = None):
        if times is None:
            raise ValueError("Must specify times")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.times = times

    def start(self) -> None:
        self.original_visible = self.target.visible
        self.interval = self.duration / self.times

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.target.visible = self.original_visible
            self._done = True
        else:
            self.target.visible = self.original_visible ^ (int(self._elapsed / self.interval) % 2 == 0)

    def stop(self) -> None:
        self.target.visible = self.original_visible
        super().stop()

    def __reversed__(self) -> "Blink":
        return self

    def __repr__(self) -> str:
        return f"Blink(times={self.times}, duration={self.duration})"


class Bezier(IntervalAction):
    """Move the sprite along a Bezier curve path over time.

    A Bezier curve is defined by control points. The sprite will follow
    the smooth curve defined by these points.
    """

    def __init__(
        self,
        control_points: list[tuple[float, float]],
        duration: float = None,
        use_physics: bool = False,
    ):
        if not control_points or len(control_points) < 2:
            raise ValueError("Must specify at least 2 control points")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.control_points = control_points
        self.use_physics = use_physics

    def _bezier_point(self, t: float) -> tuple[float, float]:
        """Calculate point on Bezier curve at time t (0-1)."""
        n = len(self.control_points) - 1
        x = y = 0
        for i, point in enumerate(self.control_points):
            # Binomial coefficient * (1-t)^(n-i) * t^i
            coef = math.comb(n, i) * (1 - t) ** (n - i) * t**i
            x += point[0] * coef
            y += point[1] * coef
        return (x, y)

    def start(self) -> None:
        self.start_position = self.target.position
        # Calculate initial velocity for physics
        if self.use_physics and hasattr(self.target, "pymunk"):
            next_point = self._bezier_point(0.1)  # Point slightly ahead
            dx = next_point[0] - self.start_position[0]
            dy = next_point[1] - self.start_position[1]
            force = (dx / (self.duration * 0.1), dy / (self.duration * 0.1))
            self.target.pymunk.apply_force_at_local_point(force)

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        progress = min(1.0, self._elapsed / self.duration)

        if self.use_physics and hasattr(self.target, "pymunk"):
            # For physics, we need to calculate the next point to apply force
            next_progress = min(1.0, (self._elapsed + 0.1) / self.duration)
            current = self._bezier_point(progress)
            next_point = self._bezier_point(next_progress)
            dx = next_point[0] - current[0]
            dy = next_point[1] - current[1]
            force = (dx / 0.1, dy / 0.1)  # Force to reach next point in 0.1 seconds
            self.target.pymunk.apply_force_at_local_point(force)
        else:
            # For non-physics, directly set position
            point = self._bezier_point(progress)
            self.target.position = point

    def stop(self) -> None:
        if self.use_physics and hasattr(self.target, "pymunk"):
            self.target.pymunk.force = (0, 0)
        super().stop()

    def __repr__(self) -> str:
        return f"Bezier(control_points={self.control_points}, duration={self.duration}, use_physics={self.use_physics})"


class Delay(IntervalAction):
    """Delay execution for a specified duration.

    This action does nothing but wait for the specified duration.
    Useful in sequences to create pauses between actions.
    """

    def __init__(self, duration: float = None):
        if duration is None:
            raise ValueError("Must specify duration")
        super().__init__(duration)

    def start(self) -> None:
        pass  # Nothing to do

    def update(self, delta_time: float) -> None:
        super().update(delta_time)

    def __repr__(self) -> str:
        return f"Delay(duration={self.duration})"


class RandomDelay(Delay):
    """Delay execution for a random duration between min and max values.

    Useful for creating natural-looking variations in timing.
    """

    def __init__(self, min_duration: float = None, max_duration: float = None):
        if min_duration is None or max_duration is None:
            raise ValueError("Must specify both min and max duration")
        if min_duration > max_duration:
            raise ValueError("Min duration must be less than max duration")

        # Choose random duration between min and max
        duration = min_duration + random.random() * (max_duration - min_duration)
        super().__init__(duration)
        self.min_duration = min_duration
        self.max_duration = max_duration

    def __repr__(self) -> str:
        return f"RandomDelay(min={self.min_duration}, max={self.max_duration})"


class Accelerate(IntervalAction):
    """Modify the speed of another action using a power function.

    The action will start slow and accelerate over time.
    The rate parameter controls how quickly it accelerates.
    """

    def __init__(self, action: IntervalAction, rate: float = 2.0):
        if not isinstance(action, IntervalAction):
            raise TypeError("Action must be an IntervalAction")
        if rate <= 0:
            raise ValueError("Rate must be positive")

        super().__init__(action.duration)
        self.action = action
        self.rate = rate

    def start(self) -> None:
        self.action.target = self.target
        self.action.start()

    def update(self, delta_time: float) -> None:
        # Calculate modified time using power function
        progress = min(1.0, self._elapsed / self.duration)
        modified_progress = progress**self.rate

        # Update elapsed time to match modified progress
        self.action._elapsed = modified_progress * self.action.duration
        self.action.update(delta_time)

        super().update(delta_time)

    def stop(self) -> None:
        self.action.stop()
        super().stop()

    def __repr__(self) -> str:
        return f"Accelerate(action={self.action}, rate={self.rate})"


class AccelDecel(IntervalAction):
    """Modify the speed of another action using a smooth acceleration and deceleration curve.

    The action will start slow, accelerate in the middle, and slow down at the end.
    Uses a sigmoid function for smooth transitions.
    """

    def __init__(self, action: IntervalAction):
        if not isinstance(action, IntervalAction):
            raise TypeError("Action must be an IntervalAction")

        super().__init__(action.duration)
        self.action = action

    def start(self) -> None:
        self.action.target = self.target
        self.action.start()

    def update(self, delta_time: float) -> None:
        # Calculate modified time using sigmoid function
        progress = min(1.0, self._elapsed / self.duration)
        if progress != 1.0:
            # Sigmoid function: 1 / (1 + e^(-12(x-0.5)))
            modified_progress = 1.0 / (1.0 + math.exp(-12 * (progress - 0.5)))
        else:
            modified_progress = 1.0

        # Update elapsed time to match modified progress
        self.action._elapsed = modified_progress * self.action.duration
        self.action.update(delta_time)

        super().update(delta_time)

    def stop(self) -> None:
        self.action.stop()
        super().stop()

    def __repr__(self) -> str:
        return f"AccelDecel(action={self.action})"
