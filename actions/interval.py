"""
Interval actions that happen over time.
"""

import math
import random

from arcade import easing

from actions.base import IntervalAction
from actions.move import MovementAction

from .base import IntervalAction


class MoveTo(MovementAction, IntervalAction):
    """Move the sprite to a specific position over time.

    This action moves a sprite to the specified end position over the given duration.
    The movement is linear and frame-independent.
    """

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

        # Initialize both parent classes properly
        MovementAction.__init__(self)
        IntervalAction.__init__(self, duration)

        self.end_position = position
        self.use_physics = use_physics
        self.total_change = None  # Will be set in start()
        self.last_progress = 0.0  # Initialize here
        self.start_position: tuple[float, float] | None = None

    def start(self) -> None:
        """Start the movement action.

        Calculate total change needed to reach target position.
        """
        super().start()
        self.start_position = self.target.position
        self.total_change = (
            self.end_position[0] - self.target.position[0],
            self.end_position[1] - self.target.position[1],
        )
        self.delta = self.total_change
        self.last_progress = 0.0  # Reset on start

    def update(self, delta_time: float) -> None:
        """Update the sprite's position based on elapsed time."""
        # Update elapsed time first
        if not self._paused:
            self._elapsed += delta_time

        # Calculate progress ratio
        progress = min(self._elapsed / self.duration, 1.0)
        # Calculate absolute position based on total progress
        start_x, start_y = self.start_position
        new_x = start_x + self.total_change[0] * progress
        new_y = start_y + self.total_change[1] * progress
        # Update sprite position
        self.target.position = (new_x, new_y)

        # Check for completion
        if self._elapsed >= self.duration:
            self.done = True

        # Handle completion callbacks
        self._check_complete()

    def stop(self) -> None:
        """Stop the movement action.

        Leave the sprite at its current position without jumping to the end.
        """
        super().stop()

    def __reversed__(self) -> "MoveTo":
        """Return a MoveTo action that moves to the original start position.

        This creates a MoveTo action that will move the sprite from its
        current position to the negative of the target position.
        """
        if self.start_position:
            return MoveTo(self.start_position, self.duration, self.use_physics)
        else:
            # If we don't have a start position yet, return a move to the negative of the end position
            return MoveTo((-self.end_position[0], -self.end_position[1]), self.duration, self.use_physics)

    def __repr__(self) -> str:
        return f"MoveTo(position={self.end_position}, duration={self.duration}, use_physics={self.use_physics})"


class MoveBy(MovementAction, IntervalAction):
    """Move the sprite by a relative amount over time.

    This action moves a sprite by the specified delta over the given duration.
    The movement is linear and frame-independent.
    """

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

        # Initialize both parent classes properly
        MovementAction.__init__(self)
        IntervalAction.__init__(self, duration)

        self.delta = delta
        self.use_physics = use_physics
        self.total_change = delta
        self.start_position: tuple[float, float] | None = None

    def start(self) -> None:
        """Start the move action."""
        super().start()
        self.start_position = self.target.position

    def update(self, delta_time: float) -> None:
        """Update the sprite's position."""
        # Calculate progress BEFORE calling super() to avoid early return
        if not self._paused:
            self._elapsed += delta_time

        # Calculate progress (0.0 to 1.0)
        progress = min(self._elapsed / self.duration, 1.0)

        # Calculate new position
        start_x, start_y = self.start_position
        delta_x, delta_y = self.delta
        new_x = start_x + delta_x * progress
        new_y = start_y + delta_y * progress

        # Update sprite position
        self.target.position = (new_x, new_y)

        # Now check for completion
        if self._elapsed >= self.duration:
            self.done = True

        # Handle completion callbacks
        self._check_complete()

    def __reversed__(self) -> "MoveBy":
        """Return a MoveBy action that moves in the opposite direction."""
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

        Leave the sprite at its current angle without jumping to the end.
        """
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

        Leave the sprite at its current angle without jumping to the end.
        """
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

        Leave the sprite at its current scale without jumping to the end.
        """
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

        Leave the sprite at its current alpha without jumping to the end.
        """
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

        Leave the sprite at its current alpha without jumping to the end.
        """
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

        Leave the sprite at its current alpha without jumping to the end.
        """
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
        self.last_point = None  # Will store last calculated point for relative movement

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

        Calculate initial point on curve for relative movement.
        """
        self.last_point = self._bezier_point(0)

    def update(self, delta_time: float) -> None:
        """Update the Bezier movement.

        Calculate new position based on progress along the curve.
        Use relative movement from last position to handle intermediate changes.
        """
        super().update(delta_time)
        if not self._paused:
            # Calculate progress ratio
            progress = self._elapsed / self.duration
            # Calculate current point on curve
            current_point = self._bezier_point(progress)

            # Calculate relative movement from last point
            dx = current_point[0] - self.last_point[0]
            dy = current_point[1] - self.last_point[1]

            # Apply relative movement
            self.target.center_x += dx
            self.target.center_y += dy

            # Store current point for next update
            self.last_point = current_point

    def stop(self) -> None:
        """Stop the Bezier movement.

        Leave the sprite at its current position without jumping to the end.
        """
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
            return

        self.elapsed += delta_time
        raw_t = min(self.elapsed / self.duration, 1.0)
        eased_t = self.ease_function(raw_t)

        # Calculate the eased delta time based on the change in eased progress
        eased_delta = (eased_t - self.prev_eased) * self.duration
        self.prev_eased = eased_t

        self.other.update(eased_delta)

        # Mark as done when we reach the end
        if raw_t >= 1.0:
            self.done = True

    def __neg__(self):
        return Easing(self.other.__reversed__(), ease_function=self.ease_function)

    def __repr__(self):
        ease_name = getattr(self.ease_function, "__name__", repr(self.ease_function))
        return f"<Easing(duration={self.duration}, ease_function={ease_name}, wrapped={repr(self.other)})>"


class JumpTo(IntervalAction):
    """Moves a sprite to a specific position, simulating a series of jumps."""

    def __init__(
        self,
        position: tuple[float, float],
        height: float,
        jumps: int,
        duration: float,
    ):
        """
        Initialize the JumpTo action.

        :param position: The target (x, y) coordinates.
        :param height: The height of each jump.
        :param jumps: The number of jumps to perform.
        :param duration: The total time for the action in seconds.
        """
        if position is None:
            raise ValueError("Must specify position")
        if height is None:
            raise ValueError("Must specify height")
        if jumps is None or jumps < 1:
            raise ValueError("Must specify at least one jump")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__(duration)
        self.end_position = position
        self.height = height
        self.jumps = jumps
        self.delta = (0, 0)

    def start(self) -> None:
        """Called when the action begins."""
        self.start_x = self.target.center_x
        self.start_y = self.target.center_y
        self.delta = (
            self.end_position[0] - self.start_x,
            self.end_position[1] - self.start_y,
        )
        self.last_progress = 0.0

    def update(self, delta_time: float) -> None:
        """Called each frame to update the action."""
        super().update(delta_time)
        if self._paused:
            return

        progress = min(1.0, self._elapsed / self.duration) if self.duration > 0 else 1.0

        # Previous position based on last progress
        prev_x_component = self.delta[0] * self.last_progress
        prev_y_component = self.delta[1] * self.last_progress
        prev_jump_y = self.height * abs(math.sin(self.last_progress * math.pi * self.jumps))

        # Current position based on current progress
        x_component = self.delta[0] * progress
        y_component = self.delta[1] * progress
        jump_y = self.height * abs(math.sin(progress * math.pi * self.jumps))

        # Calculate the change since last update
        dx = x_component - prev_x_component
        dy = (y_component + jump_y) - (prev_y_component + prev_jump_y)

        self.target.center_x += dx
        self.target.center_y += dy

        self.last_progress = progress

    def stop(self) -> None:
        """Called when the action ends.

        Leave the sprite at its current position without jumping to the end.
        """
        super().stop()

    def __reversed__(self) -> "JumpTo":
        """Returns a reversed version of this action."""
        # Note: Reversing a JumpTo is not fully supported as it depends on
        # the sprite's position when the reversal happens. This is a placeholder.
        raise NotImplementedError("JumpTo cannot be reversed.")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"JumpTo(position={self.end_position}, height={self.height}, jumps={self.jumps}, duration={self.duration})"
        )


class JumpBy(JumpTo):
    """Moves a sprite by a relative amount, simulating a series of jumps."""

    def __init__(
        self,
        delta: tuple[float, float],
        height: float,
        jumps: int,
        duration: float,
    ):
        """
        Initialize the JumpBy action.

        :param delta: The relative (dx, dy) amount to move.
        :param height: The height of each jump.
        :param jumps: The number of jumps to perform.
        :param duration: The total time for the action in seconds.
        """
        if delta is None:
            raise ValueError("Must specify delta")
        if height is None:
            raise ValueError("Must specify height")
        if jumps is None or jumps < 1:
            raise ValueError("Must specify at least one jump")
        if duration is None:
            raise ValueError("Must specify duration")

        super().__init__((0, 0), height, jumps, duration)
        self.delta = delta

    def start(self) -> None:
        """Called when the action begins."""
        self.start_x = self.target.center_x
        self.start_y = self.target.center_y
        self.end_position = (
            self.start_x + self.delta[0],
            self.start_y + self.delta[1],
        )
        self.last_progress = 0.0

    def __reversed__(self) -> "JumpBy":
        """Returns a reversed version of this action."""
        return JumpBy((-self.delta[0], -self.delta[1]), self.height, self.jumps, self.duration)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"JumpBy(delta={self.delta}, height={self.height}, jumps={self.jumps}, duration={self.duration})"
