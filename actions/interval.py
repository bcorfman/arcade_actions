from __future__ import annotations

import random

import arcade

from .base import ActionSprite, IntervalAction


class MoveTo(IntervalAction):
    """
    Moves the sprite to a specified (x, y) position over time.

    Attributes:
        target_position (Tuple[float, float]): Target (x, y) coordinates.
        start_position (Tuple[float, float]): Initial position, set when the action starts.
    """

    def __init__(self, x: float, y: float, duration: float) -> None:
        """Initialize with target position and duration."""
        super().__init__(duration)
        self.target_position: tuple[float, float] = (x, y)
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Set the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Interpolate the sprite's position from start to target."""
        if self.target:
            self.target.center_x = self.start_position[0] + (self.target_position[0] - self.start_position[0]) * t
            self.target.center_y = self.start_position[1] + (self.target_position[1] - self.start_position[1]) * t


class MoveBy(IntervalAction):
    """
    Moves the sprite by a specified (dx, dy) offset over time.

    Attributes:
        delta (Tuple[float, float]): (dx, dy) movement offset.
        start_position (Tuple[float, float]): Initial position, set when the action starts.
    """

    def __init__(self, dx: float, dy: float, duration: float) -> None:
        """Initialize with movement offset and duration."""
        super().__init__(duration)
        self.delta: tuple[float, float] = (dx, dy)
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Set the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Move the sprite by the specified offset over time."""
        if self.target:
            self.target.center_x = self.start_position[0] + self.delta[0] * t
            self.target.center_y = self.start_position[1] + self.delta[1] * t


class RotateTo(IntervalAction):
    """
    Rotates the sprite to a specific angle over time.

    Attributes:
        target_angle (float): The target angle in degrees.
        start_angle (float): The initial angle, set when the action starts.
    """

    def __init__(self, angle: float, duration: float) -> None:
        """Initialize with target angle and duration."""
        super().__init__(duration)
        self.target_angle: float = angle
        self.start_angle: float = 0

    def start(self, target: ActionSprite) -> None:
        """Set the initial angle when the action starts."""
        super().start(target)
        if self.target:
            self.start_angle = self.target.angle

    def update(self, t: float) -> None:
        """Interpolate the sprite's angle from start to target."""
        if self.target:
            self.target.angle = self.start_angle + (self.target_angle - self.start_angle) * t


class RotateBy(IntervalAction):
    """
    Rotates the sprite by a relative angle over time.

    Attributes:
        delta_angle (float): The angle to rotate by, in degrees.
        start_angle (float): The initial angle, set when the action starts.
    """

    def __init__(self, delta_angle: float, duration: float) -> None:
        """Initialize with delta angle and duration."""
        super().__init__(duration)
        self.delta_angle: float = delta_angle
        self.start_angle: float = 0

    def start(self, target: ActionSprite) -> None:
        """Set the initial angle when the action starts."""
        super().start(target)
        if self.target:
            self.start_angle = self.target.angle

    def update(self, t: float) -> None:
        """Rotate the sprite by the specified angle over time."""
        if self.target:
            self.target.angle = self.start_angle + self.delta_angle * t


class ScaleTo(IntervalAction):
    """
    Scales the sprite to a specified scale factor over time.

    Attributes:
        target_scale (float): The target scale factor.
        start_scale (float): The initial scale, set when the action starts.
    """

    def __init__(self, scale: float, duration: float) -> None:
        """Initialize with target scale and duration."""
        super().__init__(duration)
        self.target_scale: float = scale
        self.start_scale: float = 1

    def start(self, target: ActionSprite) -> None:
        """Set the initial scale when the action starts."""
        super().start(target)
        if self.target:
            self.start_scale = self.target.scale

    def update(self, t: float) -> None:
        """Interpolate the sprite's scale from start to target."""
        if self.target:
            self.target.scale = self.start_scale + (self.target_scale - self.start_scale) * t


class ScaleBy(IntervalAction):
    """
    Scales the sprite by a specified relative factor over time.

    Attributes:
        scale_factor (float): The factor by which to scale the sprite (e.g., 2.0 doubles the size).
        start_scale (float): The initial scale of the sprite, set when the action starts.
    """

    def __init__(self, scale_factor: float, duration: float) -> None:
        """Initialize with scale factor and duration."""
        super().__init__(duration)
        self.scale_factor: float = scale_factor
        self.start_scale: float = 1.0  # Placeholder; actual value is set in start()

    def start(self, target: ActionSprite) -> None:
        """Set the initial scale when the action starts."""
        super().start(target)
        if self.target:
            self.start_scale = self.target.scale

    def update(self, t: float) -> None:
        """
        Interpolate the sprite's scale from start to the target scale.

        This gradually applies the scale change over the duration.
        """
        if self.target:
            # The target scale at t=1 is start_scale * scale_factor
            self.target.scale = self.start_scale * (1 + (self.scale_factor - 1) * t)


class FadeTo(IntervalAction):
    """
    Fades the sprite to a specified alpha (transparency) level over time.

    Attributes:
        target_alpha (int): The target alpha value (0-255).
        start_alpha (int): The initial alpha, set when the action starts.
    """

    def __init__(self, alpha: int, duration: float) -> None:
        """Initialize with target alpha and duration."""
        super().__init__(duration)
        self.target_alpha: int = alpha
        self.start_alpha: int = 255

    def start(self, target: ActionSprite) -> None:
        """Set the initial alpha when the action starts."""
        super().start(target)
        if self.target:
            self.start_alpha = self.target.alpha

    def update(self, t: float) -> None:
        """Interpolate the sprite's alpha from start to target."""
        if self.target:
            self.target.alpha = int(self.start_alpha + (self.target_alpha - self.start_alpha) * t)


class FadeIn(FadeTo):
    """Fades the sprite to fully visible (alpha = 255) over time."""

    def __init__(self, duration: float) -> None:
        super().__init__(255, duration)


class FadeOut(FadeTo):
    """Fades the sprite to fully transparent (alpha = 0) over time."""

    def __init__(self, duration: float) -> None:
        super().__init__(0, duration)


class JumpTo(IntervalAction):
    """
    Makes the sprite jump to a specific position, following a parabolic arc.

    Attributes:
        target_position (Tuple[float, float]): Target (x, y) coordinates for the sprite.
        height (float): Maximum height of the jump arc.
        start_position (Tuple[float, float]): Initial position, set when the action starts.
    """

    def __init__(self, x: float, y: float, height: float, duration: float) -> None:
        """Initialize with target position, height, and duration."""
        super().__init__(duration)
        self.target_position: tuple[float, float] = (x, y)
        self.height: float = height
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Set the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Calculate the parabolic arc for the jump."""
        if self.target:
            x0, y0 = self.start_position
            x1, y1 = self.target_position
            self.target.center_x = x0 + (x1 - x0) * t
            self.target.center_y = y0 + (y1 - y0) * t + self.height * 4 * (t - t * t)


class JumpBy(IntervalAction):
    """
    Makes the sprite jump by a specific (dx, dy) offset, following a parabolic arc.

    Attributes:
        delta (Tuple[float, float]): Movement offset (dx, dy).
        height (float): Maximum height of the jump arc.
        start_position (Tuple[float, float]): Initial position, set when the action starts.
    """

    def __init__(self, dx: float, dy: float, height: float, duration: float) -> None:
        """Initialize with movement offset, height, and duration."""
        super().__init__(duration)
        self.delta: tuple[float, float] = (dx, dy)
        self.height: float = height
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Set the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Calculate the parabolic arc for the jump."""
        if self.target:
            x0, y0 = self.start_position
            dx, dy = self.delta
            self.target.center_x = x0 + dx * t
            self.target.center_y = y0 + dy * t + self.height * 4 * (t - t * t)


class Bezier(IntervalAction):
    """
    Moves the sprite along a Bezier curve defined by control points.

    Attributes:
        control_points (List[Tuple[float, float]]): List of control points for the curve.
        start_position (Tuple[float, float]): Initial position, set when the action starts.
    """

    def __init__(self, control_points: list[tuple[float, float]], duration: float) -> None:
        """Initialize with control points and duration."""
        super().__init__(duration)
        self.control_points: list[tuple[float, float]] = control_points
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Set the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def _calculate_bezier_point(self, t: float) -> tuple[float, float]:
        """Recursively calculate a point on the Bezier curve at time t."""
        points = [self.start_position] + self.control_points
        while len(points) > 1:
            points = [
                (
                    points[i][0] + (points[i + 1][0] - points[i][0]) * t,
                    points[i][1] + (points[i + 1][1] - points[i][1]) * t,
                )
                for i in range(len(points) - 1)
            ]
        return points[0]

    def update(self, t: float) -> None:
        """Move the sprite along the Bezier curve."""
        if self.target:
            self.target.center_x, self.target.center_y = self._calculate_bezier_point(t)


class Delay(IntervalAction):
    """
    Pauses the sprite's actions for a specified duration.
    """

    def __init__(self, duration: float) -> None:
        """Initialize with delay duration."""
        super().__init__(duration)

    def update(self, t: float) -> None:
        """No update needed, just a pause."""
        pass  # Delay action does nothing except wait for time to elapse


class RandomDelay(IntervalAction):
    """
    Pauses the sprite's actions for a random duration within a specified range.

    Attributes:
        min_duration (float): Minimum duration of the delay.
        max_duration (float): Maximum duration of the delay.
    """

    def __init__(self, min_duration: float, max_duration: float) -> None:
        """Initialize with minimum and maximum duration for the random delay."""
        duration = random.uniform(min_duration, max_duration)
        super().__init__(duration)

    def update(self, t: float) -> None:
        """No update needed, just a random pause."""
        pass


class Blink(IntervalAction):
    """
    Causes the sprite to blink (appear and disappear) a specified number of times.

    Attributes:
        times (int): The number of times to blink.
    """

    def __init__(self, times: int, duration: float) -> None:
        """Initialize with blink count and duration."""
        super().__init__(duration)
        self.times: int = times

    def update(self, t: float) -> None:
        """Toggle visibility based on elapsed time."""
        if self.target:
            interval = 1.0 / self.times
            self.target.alpha = 255 if int(t / interval) % 2 == 0 else 0


class Speed(IntervalAction):
    """
    Adjusts the speed of another action by a multiplier.

    Attributes:
        action (IntervalAction): The action whose speed will be modified.
        speed_factor (float): The multiplier for the action's speed.
    """

    def __init__(self, action: IntervalAction, speed_factor: float) -> None:
        """Initialize with an action and a speed multiplier."""
        super().__init__(action.duration() / speed_factor)
        self.action: IntervalAction = action
        self.speed_factor: float = speed_factor

    def start(self, target: ActionSprite) -> None:
        """Start the action with the adjusted speed."""
        super().start(target)
        self.action.start(target)

    def step(self, dt: float) -> None:
        """Advance the action based on the adjusted speed."""
        if not self.done():
            self.action.step(dt * self.speed_factor)
            if self.action.done():
                self._done = True

    def stop(self) -> None:
        """Stop the action and mark the speed adjustment as done."""
        self.action.stop()
        self._done = True

    def update(self, t: float) -> None:
        """No-op to satisfy IntervalAction's requirement for an update method."""
        pass


class WrappedMove(IntervalAction):
    """
    Moves the sprite to a target position with screen wrapping.

    Attributes:
        target_position (Tuple[float, float]): The target (x, y) coordinates.
        start_position (Tuple[float, float]): The initial position of the sprite.
    """

    def __init__(self, x: float, y: float, duration: float) -> None:
        """Initialize with target position and duration."""
        super().__init__(duration)
        self.target_position: tuple[float, float] = (x, y)
        self.start_position: tuple[float, float] = (0, 0)

    def start(self, target: ActionSprite) -> None:
        """Sets the initial position when the action starts."""
        super().start(target)
        if self.target:
            self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float) -> None:
        """Interpolates position with wrapping when reaching screen edges."""
        if self.target:
            # Calculate the new position with wrapping
            new_x = self._wrap_position(
                self.start_position[0], self.target_position[0], t, arcade.get_display_size()[0]
            )
            new_y = self._wrap_position(
                self.start_position[1], self.target_position[1], t, arcade.get_display_size()[1]
            )
            self.target.center_x = new_x
            self.target.center_y = new_y

    def _wrap_position(self, start: float, end: float, t: float, screen_size: float) -> float:
        """Calculate wrapped position between start and end coordinates on a screen with a specific size."""
        interpolated = start + (end - start) * t
        return interpolated % screen_size


class Accelerate(IntervalAction):
    """
    Speeds up an action progressively from slow to fast.

    Attributes:
        action (IntervalAction): The action to accelerate.
    """

    def __init__(self, action: IntervalAction) -> None:
        """Initialize with the action to accelerate."""
        super().__init__(action.duration())
        self.action: IntervalAction = action

    def start(self, target: ActionSprite) -> None:
        """Start the action with acceleration."""
        super().start(target)
        self.action.start(target)

    def step(self, dt: float) -> None:
        """Advance the action with increasing speed."""
        if not self.done():
            super().step(dt)
            t = self.elapsed / self.duration()
            accelerated_dt = dt * t  # Increase speed over time
            self.action.step(accelerated_dt)
            if self.action.done():
                self._done = True

    def stop(self) -> None:
        """Stop the action and mark it as done."""
        self.action.stop()
        self._done = True

    def update(self, t: float) -> None:
        """No-op to satisfy IntervalAction's requirement for an update method."""
        pass


import math


class AccelDecel(IntervalAction):
    """
    Modifies an action to accelerate at the start, decelerate toward the end, using a sigmoid-based easing.
    """

    def __init__(self, action: IntervalAction) -> None:
        """Initialize with the action to be modified."""
        super().__init__(action.duration())
        self.action: IntervalAction = action

    def start(self, target: ActionSprite) -> None:
        """Start the action with accel-decel effect."""
        super().start(target)
        self.action.start(target)

    def step(self, dt: float) -> None:
        """Advance the action, applying acceleration and deceleration."""
        if not self.done():
            self.elapsed += dt
            t = self.elapsed / self.duration()

            # Apply sigmoid easing for acceleration and deceleration
            if t != 1.0:
                ft = (t - 0.5) * 12
                eased_t = 1.0 / (1.0 + math.exp(-ft))
            else:
                eased_t = t

            # Directly update the wrapped action with the eased time
            self.action.update(eased_t)

            # Mark done if time has fully elapsed
            if t >= 1.0:
                self._done = True

    def stop(self) -> None:
        """Stop the action and mark it as done."""
        self.action.stop()
        self._done = True

    def update(self, t: float) -> None:
        """No-op to satisfy IntervalAction's requirement for an update method."""
        pass
