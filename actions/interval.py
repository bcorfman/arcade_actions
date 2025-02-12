from __future__ import annotations

import copy
import math
from typing import Any, Generic, TypeVar

from arcade.sprite import Sprite

from .base import IntervalAction, Reverse


class RotateBy(IntervalAction):
    """Rotates a Sprite object clockwise by a specified angle over time.

    Args:
        angle (float): Degrees to rotate (positive = clockwise)
        duration (float): Time to complete rotation in seconds

    Raises:
        ValueError: If duration is negative
        TypeError: If target is not an Arcade Sprite
    """

    def init(self, angle: float, duration: float) -> None:
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.angle = angle
        self.duration = duration

    def start(self) -> None:
        if self.target is None:
            raise AttributeError("Target cannot be None")

        self._start_angle = self.target.angle

    def update(self, t: float) -> None:
        new_angle = (self._start_angle + (self.angle * t)) % 360
        self.target.angle = new_angle

    def __reversed__(self) -> RotateBy:
        return RotateBy(-self.angle, self.duration)


Rotate = RotateBy  # Alias for compatibility


class RotateTo(IntervalAction):
    """Rotates a Sprite to a specific angle using the shortest path.

    Args:
        angle (float): Target angle in degrees
        duration (float): Time to complete rotation in seconds

    Raises:
        ValueError: If duration is negative
        TypeError: If target is not an Arcade Sprite
    """

    angle: float
    duration: float
    target: Sprite | None = None
    _start_angle: float | None = None
    _delta_angle: float | None = None

    def init(self, angle: float, duration: float) -> None:
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.angle = angle % 360  # Normalize initial target angle
        self.duration = duration
        self._start_angle = None
        self._delta_angle = None

    def start(self) -> None:
        """Calculate shortest rotation path to target angle."""
        end_angle = self.angle
        self._start_angle = self.target.angle % 360
        self._delta_angle = (end_angle % 360) - (self._start_angle % 360)

        # Adjust for shortest path
        if self._delta_angle > 180:
            self._delta_angle = -360 + self._delta_angle
        if self._delta_angle < -180:
            self._delta_angle = 360 + self._delta_angle

        super().start()

    def update(self, t: float) -> None:
        """Update rotation based on elapsed time fraction.

        Args:
            t (float): Elapsed time fraction (0.0 to 1.0)
        """
        assert self.target is not None, "Target sprite cannot be None"
        assert self._start_angle is not None, "Start angle not initialized"
        assert self._delta_angle is not None, "Delta angle not initialized"

        # Calculate new angle with proper modulo
        new_angle = (self._start_angle + (self._delta_angle * t)) % 360
        self.target.angle = new_angle

    def __reversed__(self) -> RotateTo:
        """Create a reversed version of this rotation action."""
        if self._start_angle is None:
            raise RuntimeError("Cannot reverse RotateTo action before it starts")
        return RotateTo(angle=self._start_angle, duration=self.duration)


# Generic type for any IntervalAction
T = TypeVar("T", bound=IntervalAction)


class Speed(Generic[T], IntervalAction):
    """Modifies the execution speed of another action.

    Args:
        action (IntervalAction): The action to modify
        speed (float): Speed multiplier (>1 faster, <1 slower)

    Raises:
        ValueError: If speed is zero or negative
        TypeError: If action is not an IntervalAction
        ValueError: If action has no duration
    """

    def init(self, action: IntervalAction, speed: float) -> None:
        if not isinstance(action, IntervalAction):
            raise TypeError(f"Action must be an IntervalAction, got {type(action)}")
        if speed <= 0:
            raise ValueError(f"Speed must be positive, got {speed}")
        if getattr(action, "duration", None) is None:
            raise ValueError("Action must have a duration")

        self.action = action
        self.speed = speed
        self.duration = action.duration / speed

    def start(self) -> None:
        """Start the modified action."""
        assert self.target is not None, "Target cannot be None"

        # Pass target to wrapped action
        self.action.target = self.target
        self.action.start()

        super().start()

    def update(self, t: float) -> None:
        """Update wrapped action with current time fraction.

        Args:
            t (float): Elapsed time fraction (0.0 to 1.0)
        """
        assert 0 <= t <= 1, f"Time fraction must be between 0 and 1, got {t}"
        self.action.update(t)

    def stop(self) -> None:
        """Stop the wrapped action."""
        self.action.stop()
        super().stop()

    def __reversed__(self) -> Speed[T]:
        """Create a reversed version while maintaining speed modifier."""
        return Speed(action=Reverse(self.action), speed=self.speed)


class Accelerate(Generic[T], IntervalAction):
    """Modifies the acceleration of another action.

    Args:
        action (IntervalAction): The action to modify
        rate (float): Acceleration rate (>1: slow start, fast end; <1: fast start, slow end)

    Raises:
        ValueError: If rate is zero or negative
        TypeError: If action is not an IntervalAction
        ValueError: If action has no duration
    """

    def init(self, action: IntervalAction, rate: float = 2.0) -> None:
        if not isinstance(action, IntervalAction):
            raise TypeError(f"Action must be an IntervalAction, got {type(action)}")
        if rate <= 0:
            raise ValueError(f"Rate must be positive, got {rate}")
        if getattr(action, "duration", None) is None:
            raise ValueError("Action must have a duration")

        self.action = action
        self.rate = rate
        self.duration = action.duration

    def start(self) -> None:
        """Start the modified action."""
        assert self.target is not None, "Target cannot be None"

        # Pass target to wrapped action
        self.action.target = self.target
        self.action.start()

        super().start()

    def update(self, t: float) -> None:
        """Update wrapped action with accelerated time fraction.

        Args:
            t (float): Elapsed time fraction (0.0 to 1.0)

        The time fraction is modified by raising it to the power of rate,
        creating acceleration (rate>1) or deceleration (rate<1) effects.
        """
        assert 0 <= t <= 1, f"Time fraction must be between 0 and 1, got {t}"

        # Apply acceleration by modifying time value
        modified_time = t**self.rate
        self.action.update(modified_time)

    def stop(self) -> None:
        """Stop the wrapped action."""
        self.action.stop()
        super().stop()

    def __reversed__(self) -> Accelerate[T]:
        """Create a reversed version with reciprocal rate."""
        return Accelerate(action=Reverse(self.action), rate=1.0 / self.rate)


class AccelDecel(Generic[T], IntervalAction):
    """Creates an ease-in-ease-out effect for an action using a sigmoid curve.

    Args:
        action (IntervalAction): The action to modify with ease-in-ease-out timing

    Raises:
        TypeError: If action is not an IntervalAction
        ValueError: If action has no duration
    """

    def init(self, action: IntervalAction) -> None:
        if not isinstance(action, IntervalAction):
            raise TypeError(f"Action must be an IntervalAction, got {type(action)}")
        if getattr(action, "duration", None) is None:
            raise ValueError("Action must have a duration")

        self.action = action
        self.duration = action.duration

    def start(self) -> None:
        """Start the modified action."""
        assert self.target is not None, "Target cannot be None"

        # Pass target to wrapped action
        self.action.target = self.target
        self.action.start()

        super().start()

    def update(self, t: float) -> None:
        """Update wrapped action with modified time using sigmoid curve.

        Args:
            t (float): Elapsed time fraction (0.0 to 1.0)

        The time fraction is modified using a sigmoid-like function to create
        a smooth acceleration and deceleration effect. The action starts slow,
        speeds up in the middle, and slows down at the end.
        """
        assert 0 <= t <= 1, f"Time fraction must be between 0 and 1, got {t}"

        # Apply sigmoid-based timing modification
        modified_time = t
        if t != 1.0:  # Special case handling for end of animation
            # Center around 0 and scale for steeper curve
            ft = (t - 0.5) * 12
            # Apply sigmoid function
            modified_time = 1.0 / (1.0 + math.exp(-ft))

        self.action.update(modified_time)

    def stop(self) -> None:
        """Stop the wrapped action."""
        self.action.stop()
        super().stop()

    def __reversed__(self) -> AccelDecel[T]:
        """Create a reversed version maintaining the ease-in-ease-out effect."""
        return AccelDecel(action=Reverse(self.action))


class MoveTo(IntervalAction):
    """Moves a sprite to an absolute position using linear interpolation.

    Args:
        position: Target position as (x, y) coordinates
        duration: Time to complete movement in seconds (default: 5)

    Raises:
        ValueError: If position is None or contains invalid coordinates
        ValueError: If duration is negative
        AttributeError: If target sprite is not properly initialized
    """

    def init(self, position: tuple[float, float], duration: float = 5.0) -> None:
        if position is None:
            raise ValueError("Position cannot be None")
        if not isinstance(position, (tuple, list)) or len(position) != 2:
            raise ValueError("Position must be a tuple of (x, y) coordinates")
        if not all(isinstance(coord, (int, float)) for coord in position):
            raise ValueError("Position coordinates must be numeric")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.position = position
        self.duration = duration

    def start(self) -> None:
        """Initialize movement by calculating delta vector."""
        if self.target is None:
            raise AttributeError("Target sprite cannot be None")

        # Store start position
        self._start_pos = (self.target.center_x, self.target.center_y)
        self._delta = (self.position[0] - self._start_pos[0], self.position[1] - self._start_pos[1])

    def update(self, t: float) -> None:
        """Update sprite position based on elapsed time fraction.

        Args:
            t: Elapsed time fraction (0.0 to 1.0)

        Raises:
            AssertionError: If movement has not been properly initialized
        """
        assert 0 <= t <= 1, f"Time fraction must be between 0 and 1, got {t}"
        assert self.target is not None, "Target sprite cannot be None"
        assert self._start_pos is not None, "Start position not initialized"
        assert self._delta is not None, "Movement delta not initialized"

        x = self._start_pos[0] + (self._delta[0] * t)
        y = self._start_pos[1] + (self._delta[1] * t)
        self.target.center_x = x
        self.target.center_y = y

    def __reversed__(self) -> MoveTo:
        """Return a new MoveTo action that moves to the starting position."""
        if self._start_pos is None:
            raise RuntimeError("Cannot reverse MoveTo action before it starts")
        return MoveTo(position=self._start_pos, duration=self.duration)


class MoveBy(IntervalAction):
    """Moves a sprite by a relative offset using linear interpolation.

    Args:
        delta: Relative movement as (dx, dy) offset
        duration: Time to complete movement in seconds (default: 5)

    Raises:
        ValueError: If delta is None or contains invalid coordinates
        ValueError: If duration is negative
        AttributeError: If target sprite is not properly initialized
    """

    def init(self, delta: tuple[float, float], duration: float = 5.0) -> None:
        if delta is None:
            raise ValueError("Delta cannot be None")
        if not isinstance(delta, (tuple, list)) or len(delta) != 2:
            raise ValueError("Delta must be a tuple of (dx, dy) coordinates")
        if not all(isinstance(d, (int, float)) for d in delta):
            raise ValueError("Delta values must be numeric")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.delta = delta
        self.duration = duration

    def start(self) -> None:
        """Initialize movement by storing start position."""
        if self.target is None:
            raise AttributeError("Target sprite cannot be None")

        # Store start position
        self._start_x = self.target.center_x
        self._start_y = self.target.center_y

        super().start()

    def update(self, t: float) -> None:
        """Update sprite position based on elapsed time fraction.

        Args:
            t: Elapsed time fraction (0.0 to 1.0)

        Raises:
            AssertionError: If movement has not been properly initialized
        """
        assert 0 <= t <= 1, f"Time fraction must be between 0 and 1, got {t}"
        assert self.target is not None, "Target sprite cannot be None"
        assert None not in (self._start_x, self._start_y), "Start position not initialized"

        # Direct position update using linear interpolation of delta
        self.target.center_x = self._start_x + (self.delta[0] * t)
        self.target.center_y = self._start_y + (self.delta[1] * t)

    def __reversed__(self) -> MoveBy:
        """Return a new MoveBy action with negated delta.

        Returns:
            MoveBy: A new action that moves in the opposite direction
        """
        return MoveBy(delta=(-self.delta[0], -self.delta[1]), duration=self.duration)


class FadeOut(IntervalAction):
    """Fades out a Sprite object by modifying its opacity attribute.

    Args:
        duration (float): Time in seconds for the fade out effect

    Raises:
        ValueError: If duration is negative
        AttributeError: If target doesn't support opacity
    """

    def init(self, duration: float) -> None:
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")
        self.duration = duration

    def update(self, t: float) -> None:
        """Updates the sprite's opacity based on the elapsed time fraction.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If target sprite doesn't have opacity attribute
        """
        if not self.target:
            raise AttributeError("No target sprite set for FadeOut action")

        try:
            self.target.alpha = int(255 * (1 - t))
        except AttributeError:
            raise AttributeError(f"Target {self.target} doesn't support opacity changes")

    def __reversed__(self) -> FadeIn:
        """Returns a FadeIn action with the same duration."""
        from .interval import FadeIn  # Avoid circular import

        return FadeIn(self.duration)


class FadeTo(IntervalAction):
    """Fades a Sprite object to a specific alpha value.

    Args:
        alpha (int): Target alpha value (0-255)
        duration (float): Time in seconds for the fade effect

    Raises:
        ValueError: If alpha is outside 0-255 range or duration is negative
        AttributeError: If target doesn't support alpha changes
    """

    def init(self, alpha: int, duration: float) -> None:
        if not 0 <= alpha <= 255:
            raise ValueError(f"Alpha must be between 0 and 255, got {alpha}")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.alpha = alpha
        self.duration = duration
        self.start_alpha = None

    def start(self) -> None:
        """Captures the starting alpha value.

        Raises:
            AttributeError: If target sprite is not set or doesn't support alpha
        """
        if not self.target:
            raise AttributeError("No target sprite set for FadeTo action")

        try:
            self.start_alpha = self.target.alpha
        except AttributeError:
            raise AttributeError(f"Target {self.target} doesn't support alpha changes")

    def update(self, t: float) -> None:
        """Updates the sprite's alpha based on the elapsed time fraction.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If start_alpha is not set or target lacks alpha support
        """
        if self.start_alpha is None:
            raise AttributeError("FadeTo action hasn't been started")

        if not self.target:
            raise AttributeError("No target sprite set for FadeTo action")

        try:
            self.target.alpha = int(self.start_alpha + (self.alpha - self.start_alpha) * t)
        except AttributeError:
            raise AttributeError(f"Target {self.target} doesn't support alpha changes")


class FadeIn(FadeOut):
    """Fades in a Sprite object by modifying its alpha attribute.

    Args:
        duration (float): Time in seconds for the fade in effect

    Raises:
        ValueError: If duration is negative
        AttributeError: If target doesn't support alpha changes
    """

    def update(self, t: float) -> None:
        """Updates the sprite's alpha based on the elapsed time fraction.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If target sprite doesn't have alpha attribute
        """
        if not self.target:
            raise AttributeError("No target sprite set for FadeIn action")

        try:
            self.target.alpha = int(255 * t)
        except AttributeError:
            raise AttributeError(f"Target {self.target} doesn't support alpha changes")

    def __reversed__(self) -> FadeOut:
        """Returns a FadeOut action with the same duration."""
        from .interval import FadeOut  # Avoid circular import

        return FadeOut(self.duration)


class ScaleTo(IntervalAction):
    """Scales a Sprite object to a specific scale factor.

    Args:
        scale (float): Target scale factor
        duration (float): Time in seconds for scaling

    Raises:
        ValueError: If scale is negative or duration is negative
    """

    def init(self, scale: float, duration: float = 5) -> None:
        if scale < 0:
            raise ValueError(f"Scale must be non-negative, got {scale}")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.end_scale = scale
        self.duration = duration
        self.start_scale = None
        self.delta = None

    def start(self) -> None:
        """Captures the starting scale value.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for ScaleTo action")

        self.start_scale = self.target.scale
        self.delta = self.end_scale - self.start_scale

    def update(self, t: float) -> None:
        """Updates the sprite's scale based on the elapsed time fraction.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If action hasn't been started
        """
        if self.start_scale is None or self.delta is None:
            raise AttributeError("ScaleTo action hasn't been started")

        if not self.target:
            raise AttributeError("No target sprite set for ScaleTo action")

        try:
            self.target.scale = self.start_scale + self.delta * t
        except AttributeError:
            raise AttributeError(f"Target {self.target} doesn't support scale changes")


class ScaleBy(ScaleTo):
    """Scales a Sprite object by a scale factor.

    Args:
        scale (float): Scale factor to multiply by
        duration (float): Time in seconds for scaling

    Raises:
        ValueError: If scale is negative or duration is negative
    """

    def start(self) -> None:
        """Captures the starting scale and calculates relative scaling.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for ScaleBy action")

        self.start_scale = self.target.scale
        self.delta = self.start_scale * self.end_scale - self.start_scale

    def __reversed__(self) -> ScaleBy:
        """Returns a ScaleBy action with inverse scale."""
        return ScaleBy(1.0 / self.end_scale, self.duration)


class Blink(IntervalAction):
    """Blinks a Sprite object by modifying its visibility.

    Args:
        times (int): Number of blinks
        duration (float): Total time for all blinks

    Raises:
        ValueError: If times is not positive or duration is negative
    """

    def init(self, times: int, duration: float) -> None:
        if times <= 0:
            raise ValueError(f"Times must be positive, got {times}")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.times = times
        self.duration = duration
        self.end_invisible = None

    def start(self) -> None:
        """Captures initial visibility state.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for Blink action")

        self.end_invisible = not self.target.visible

    def update(self, t: float) -> None:
        """Updates sprite visibility based on blink timing.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If action hasn't been started
        """
        if self.end_invisible is None:
            raise AttributeError("Blink action hasn't been started")

        if not self.target:
            raise AttributeError("No target sprite set for Blink action")

        slice = 1.0 / self.times
        m = t % slice
        self.target.visible = self.end_invisible ^ (m < slice / 2.0)

    def __reversed__(self) -> Blink:
        """Returns itself since Blink is its own reverse."""
        return self


class Bezier(IntervalAction):
    """Moves a Sprite object through a bezier path.

    Args:
        bezier: Bezier path configuration
        duration (float): Time in seconds to complete path
        forward (bool): Direction of movement along path

    Raises:
        ValueError: If duration is negative
        TypeError: If bezier configuration is invalid
    """

    def init(self, bezier: Any, duration: float = 5, forward: bool = True) -> None:
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")
        if not hasattr(bezier, "at"):
            raise TypeError("Bezier configuration must have 'at' method")

        self.duration = duration
        self.bezier = bezier
        self.forward = forward
        self.start_position = None

    def start(self) -> None:
        """Captures starting position.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for Bezier action")

        self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Updates sprite position along bezier path.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If action hasn't been started
        """
        if self.start_position is None:
            raise AttributeError("Bezier action hasn't been started")

        if not self.target:
            raise AttributeError("No target sprite set for Bezier action")

        if self.forward:
            p = self.bezier.at(t)
        else:
            p = self.bezier.at(1 - t)

        self.target.center_x = self.start_position[0] + p[0]
        self.target.center_y = self.start_position[1] + p[1]

    def __reversed__(self) -> Bezier:
        """Returns a reversed Bezier action."""
        return Bezier(self.bezier, self.duration, not self.forward)


class JumpBy(IntervalAction):
    """Moves a Sprite object in a jump motion.

    Args:
        position (tuple[float, float]): Target (x,y) offset
        height (float): Jump height
        jumps (int): Number of jumps
        duration (float): Time in seconds for all jumps

    Raises:
        ValueError: If height is negative, jumps not positive, or duration negative
    """

    def init(
        self, position: tuple[float, float] = (0, 0), height: float = 100, jumps: int = 1, duration: float = 5
    ) -> None:
        if height < 0:
            raise ValueError(f"Height must be non-negative, got {height}")
        if jumps <= 0:
            raise ValueError(f"Jumps must be positive, got {jumps}")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

        self.position = position
        self.height = height
        self.duration = duration
        self.jumps = jumps
        self.start_position = None
        self.delta = None

    def start(self) -> None:
        """Captures starting position and calculates movement delta.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for JumpBy action")

        self.start_position = (self.target.center_x, self.target.center_y)
        self.delta = self.position

    def update(self, t: float) -> None:
        """Updates sprite position for jump animation.

        Args:
            t (float): Normalized time value between 0 and 1

        Raises:
            AttributeError: If action hasn't been started
        """
        if not self.start_position or not self.delta:
            raise AttributeError("JumpBy action hasn't been started")

        if not self.target:
            raise AttributeError("No target sprite set for JumpBy action")

        y = self.height * abs(math.sin(t * math.pi * self.jumps))
        y = int(y + self.delta[1] * t)
        x = self.delta[0] * t

        self.target.center_x = self.start_position[0] + x
        self.target.center_y = self.start_position[1] + y

    def __reversed__(self) -> JumpBy:
        """Returns a reversed JumpBy action."""
        return JumpBy((-self.position[0], -self.position[1]), self.height, self.jumps, self.duration)


class JumpTo(JumpBy):
    """Moves a Sprite object to a position in a jump motion.

    Inherits from JumpBy but calculates position delta from target position.
    """

    def start(self) -> None:
        """Captures starting position and calculates absolute movement.

        Raises:
            AttributeError: If target sprite is not set
        """
        if not self.target:
            raise AttributeError("No target sprite set for JumpTo action")

        self.start_position = (self.target.center_x, self.target.center_y)
        self.delta = (self.position[0] - self.start_position[0], self.position[1] - self.start_position[1])


class Delay(IntervalAction):
    """Delays the action for a specified duration.

    Args:
        delay (float): Time in seconds to delay

    Raises:
        ValueError: If delay is negative
    """

    def init(self, delay: float) -> None:
        if delay < 0:
            raise ValueError(f"Delay must be non-negative, got {delay}")
        self.duration = delay

    def __reversed__(self) -> Delay:
        """Returns itself since Delay is its own reverse."""
        return self


class RandomDelay(Delay):
    """Delays the action by a random duration between low and high values.

    Args:
        low (float): Minimum delay in seconds
        hi (float): Maximum delay in seconds

    Raises:
        ValueError: If low/hi are negative or low > hi
    """

    def init(self, low: float, hi: float) -> None:
        if low < 0 or hi < 0:
            raise ValueError("Delay bounds must be non-negative")
        if low > hi:
            raise ValueError(f"Low ({low}) must not exceed hi ({hi})")

        self.low = low
        self.hi = hi
        super().init(0)  # Duration will be set in __deepcopy__

    def __deepcopy__(self, memo: dict) -> RandomDelay:
        """Creates a new instance with random duration between bounds."""
        import random

        new = copy.copy(self)
        new.duration = self.low + (random.random() * (self.hi - self.low))
        return new

    def __mul__(self, other: int) -> RandomDelay:
        """Multiplies delay bounds by an integer factor."""
        if not isinstance(other, int):
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        return RandomDelay(self.low * other, self.hi * other)
