"""
Interval actions that happen over time.
"""

import math
import random

from arcade import easing

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
        self.start_position = None  # Will be set in start()
        self.total_change = None  # Will be set in start()

    def start(self) -> None:
        """Start the movement action.

        Store the initial position and calculate total change.
        """
        self.start_position = self.target.position
        self.total_change = (
            self.end_position[0] - self.start_position[0],
            self.end_position[1] - self.start_position[1],
        )

    def update(self, delta_time: float) -> None:
        """Update the action's progress.

        Calculate new position based on elapsed time ratio.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate progress ratio
            progress = self._elapsed / self.duration
            # Calculate new position
            self.target.position = (
                self.start_position[0] + self.total_change[0] * progress,
                self.start_position[1] + self.total_change[1] * progress,
            )

    def stop(self) -> None:
        """Stop the movement action.

        Ensure we end exactly at the target position.
        """
        self.target.position = self.end_position
        super().stop()

    def __reversed__(self) -> "MoveTo":
        """Returns a reversed version of this action.

        The reversed action will move from the end position back to the start position.
        If the action hasn't started yet, it will create a MoveTo that goes from the
        current position to the negative of the target position.
        """
        if self.start_position is None:
            # If we haven't started yet, create a MoveTo that goes from current to negative
            return MoveTo((-self.end_position[0], -self.end_position[1]), self.duration, self.use_physics)
        # If we have started, create a MoveTo that goes from end to start
        return MoveTo(self.start_position, self.duration, self.use_physics)

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

        self.delta = delta
        super().__init__(delta, duration, use_physics)

    def start(self) -> None:
        """Start the movement action.

        Calculate the target position as current position plus delta.
        Store the initial position and total change.
        """
        self.start_position = self.target.position
        self.end_position = (self.start_position[0] + self.delta[0], self.start_position[1] + self.delta[1])
        self.total_change = self.delta

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
        self.start_angle = None  # Will be set in start()
        self.total_change = None  # Will be set in start()

    def start(self) -> None:
        """Start the rotation action.

        Store the initial angle and calculate total change.
        """
        self.start_angle = self.target.angle % 360
        # Calculate shortest rotation path
        angle_diff = ((self.end_angle - self.start_angle + 180) % 360) - 180
        self.total_change = angle_diff

    def update(self, delta_time: float) -> None:
        """Update the action's progress.

        Calculate new angle based on elapsed time ratio.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate progress ratio
            progress = self._elapsed / self.duration
            # Calculate new angle
            self.target.angle = (self.start_angle + self.total_change * progress) % 360

    def stop(self) -> None:
        """Stop the rotation action.

        Ensure we end exactly at the target angle.
        """
        self.target.angle = self.end_angle
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
        """Start the rotation action.

        Calculate the target angle as current angle plus delta.
        Store the initial angle and total change.
        """
        self.start_angle = self.target.angle
        self.total_change = self.angle

    def stop(self) -> None:
        """Stop the rotation action.

        Ensure we end exactly at the target angle.
        """
        self.target.angle = (self.start_angle + self.angle) % 360
        super().stop()

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
        """Start the scale action.

        Store the initial scale and calculate the rate of change.
        """
        # Store initial scale as a float (average of x and y)
        self.start_scale = (self.target.scale.x + self.target.scale.y) / 2
        # Calculate how much scale should change per second
        self.scale_change_rate = (self.end_scale - self.start_scale) / self.duration

    def update(self, delta_time: float) -> None:
        """Update the scale action.

        Calculate new scale based on elapsed time and rate of change.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate new scale based on time elapsed
            new_scale = self.start_scale + (self.scale_change_rate * self._elapsed)
            # Ensure scale stays positive
            new_scale = max(0.001, new_scale)
            # Apply same scale to both x and y
            self.target.scale = (new_scale, new_scale)

    def stop(self) -> None:
        """Stop the scale action.

        Ensure we end exactly at the target scale.
        """
        self.target.scale = (self.end_scale, self.end_scale)
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
        """Start the scale action.

        Store the initial scale and calculate the rate of change.
        """
        # Store initial scale as a float (average of x and y)
        self.start_scale = (self.target.scale.x + self.target.scale.y) / 2
        # Calculate target scale as relative change
        self.end_scale = self.start_scale * self.scale
        # Calculate how much scale should change per second
        self.scale_change_rate = (self.end_scale - self.start_scale) / self.duration

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
        """Start the fade out action.

        Store the initial alpha value and calculate the rate of change.
        """
        self.start_alpha = self.target.alpha
        # Calculate how much alpha should change per second
        self.alpha_change_rate = -self.start_alpha / self.duration

    def update(self, delta_time: float) -> None:
        """Update the fade out action.

        Calculate new alpha based on elapsed time and rate of change.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate new alpha based on time elapsed
            new_alpha = max(0, self.start_alpha + (self.alpha_change_rate * self._elapsed))
            self.target.alpha = int(new_alpha)

    def stop(self) -> None:
        """Stop the fade out action.

        Ensure we end completely transparent.
        """
        self.target.alpha = 0
        super().stop()

    def __reversed__(self) -> "FadeIn":
        return FadeIn(self.duration)

    def __repr__(self) -> str:
        return f"FadeOut(duration={self.duration})"


class FadeIn(IntervalAction):
    """Fade in the sprite over time."""

    def __init__(self, duration: float = None):
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)

    def start(self) -> None:
        """Start the fade in action.

        Store the initial alpha value and calculate the rate of change.
        """
        self.start_alpha = self.target.alpha
        # Calculate how much alpha should change per second
        self.alpha_change_rate = (255 - self.start_alpha) / self.duration

    def update(self, delta_time: float) -> None:
        """Update the fade in action.

        Calculate new alpha based on elapsed time and rate of change.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate new alpha based on time elapsed
            new_alpha = min(255, self.start_alpha + (self.alpha_change_rate * self._elapsed))
            self.target.alpha = int(new_alpha)

    def stop(self) -> None:
        """Stop the fade in action.

        Ensure we end completely opaque.
        """
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
        """Start the fade to action.

        Store the initial alpha value and calculate the rate of change.
        """
        self.start_alpha = self.target.alpha
        # Calculate how much alpha should change per second
        self.alpha_change_rate = (self.alpha - self.start_alpha) / self.duration

    def update(self, delta_time: float) -> None:
        """Update the fade to action.

        Calculate new alpha based on elapsed time and rate of change.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate new alpha based on time elapsed
            new_alpha = self.start_alpha + (self.alpha_change_rate * self._elapsed)
            # Clamp to valid range
            new_alpha = max(0, min(255, new_alpha))
            self.target.alpha = int(new_alpha)

    def stop(self) -> None:
        """Stop the fade to action.

        Ensure we end exactly at the target alpha.
        """
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
        """Start the blink action.

        Store the initial visibility and calculate blink interval.
        """
        self.original_visible = self.target.visible
        # Calculate how long each blink should last
        self.blink_interval = self.duration / self.times
        # Track the last blink time
        self.last_blink_time = 0

    def update(self, delta_time: float) -> None:
        """Update the blink action.

        Toggle visibility based on elapsed time and blink interval.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate how many blinks should have occurred
            current_blink = int(self._elapsed / self.blink_interval)
            # Toggle visibility based on even/odd blink count
            self.target.visible = self.original_visible ^ (current_blink % 2 == 0)

    def stop(self) -> None:
        """Stop the blink action.

        Restore original visibility state.
        """
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
        """Start the Bezier movement.

        Store the initial position.
        """
        self.start_position = self.target.position

    def update(self, delta_time: float) -> None:
        """Update the Bezier movement.

        Calculate new position based on progress along the curve.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate progress ratio
            progress = self._elapsed / self.duration
            # Calculate point on curve
            point = self._bezier_point(progress)
            # Set position
            self.target.position = point

    def stop(self) -> None:
        """Stop the Bezier movement.

        Ensure we end at the final control point.
        """
        self.target.position = self.control_points[-1]
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


class Easing(IntervalAction):
    """
    Wraps an IntervalAction and modulates its rate of progress using an easing function.

    This allows the wrapped action to appear to accelerate, decelerate, or both — depending
    on the easing curve used. The easing function transforms normalized time (t in [0,1])
    into a new eased value, which is used to distort the time flow passed to the inner action.

    The underlying action must implement update(delta_time) and respond consistently to timing.

    Parameters:
        action (IntervalAction): The action to be wrapped and time-warped.
        ease_function (Callable[[float], float]): Easing function taking t ∈ [0, 1] and returning eased t.

    Example:
        >>> from actions.move import MoveTo
        >>> from arcade import easing
        >>> move = MoveTo((100, 200), duration=2.0)
        >>> wrapped = Easing(move, ease_function=easing.ease_in_out)
        >>> wrapped.duration
        2.0
        >>> isinstance(wrapped.other, MoveTo)
        True
        >>> wrapped.ease_function == easing.ease_in_out
        True

        >>> reversed = -wrapped
        >>> isinstance(reversed, Easing)
        True
        >>> repr(reversed).startswith("<Easing(")
        True
    """

    def __init__(self, action: IntervalAction, ease_function=easing.ease_in_out):
        super().__init__(action.duration)
        self.other = action
        self.ease_function = ease_function
        self.elapsed = 0.0
        self.prev_eased = 0.0

    def start(self):
        self.other.target = self.target
        self.other.start()
        self.elapsed = 0.0
        self.prev_eased = 0.0

    def update(self, delta_time: float):
        if self.done:
            return delta_time

        self.elapsed += delta_time
        raw_t = min(self.elapsed / self.duration, 1.0)
        eased_t = self.ease_function(raw_t)

        # Convert eased progress to an eased delta_time
        eased_elapsed = eased_t * self.duration
        eased_delta = eased_elapsed - self.prev_eased
        self.prev_eased = eased_elapsed

        self.other.update(eased_delta)

        # Mark as done when we reach the end
        if raw_t >= 1.0:
            self.done = True

        return eased_delta

    def __neg__(self):
        return Easing(self.other.__reversed__(), ease_function=self.ease_function)

    def __repr__(self):
        ease_name = getattr(self.ease_function, "__name__", repr(self.ease_function))
        return f"<Easing(duration={self.duration}, ease_function={ease_name}, wrapped={repr(self.other)})>"
