import math
import random

from .base import IntervalAction

__all__ = [
    "MoveBy",
    "MoveTo",
    "JumpBy",
    "JumpTo",
    "Bezier",
    "Blink",
    "RotateTo",
    "RotateBy",
    "ScaleTo",
    "ScaleBy",
    "FadeTo",
    "FadeIn",
    "FadeOut",
    "Delay",
    "RandomDelay",
    "Lerp",
    "Accelerate",
    "AccelDecel",
    "Speed",
    "Move",
    "Rotate",
    "Scale",
]


class MoveTo(IntervalAction):
    """Moves a sprite to a specific location using Arcade's velocity system."""

    def __init__(self, destination: tuple[float, float], duration: float):
        super().__init__(duration)
        self.destination = destination
        self.vx, self.vy = 0.0, 0.0

    def start(self, target):
        super().start(target)
        dx = self.destination[0] - target.center_x
        dy = self.destination[1] - target.center_y
        self.vx = dx / self.duration
        self.vy = dy / self.duration
        target.change_x += self.vx
        target.change_y += self.vy

    def update(self, t: float):
        pass

    def finish(self):
        self.target.change_x -= self.vx
        self.target.change_y -= self.vy


class MoveBy(IntervalAction):
    """Moves a sprite by a delta using Arcade's velocity system (change_x/y)."""

    def __init__(self, delta: tuple[float, float], duration: float):
        super().__init__(duration)
        self.dx, self.dy = delta
        self.vx, self.vy = 0.0, 0.0

    def start(self, target):
        super().start(target)
        self.vx = self.dx / self.duration
        self.vy = self.dy / self.duration
        target.change_x += self.vx
        target.change_y += self.vy

    def update(self, t: float):
        pass  # Let Arcade handle position via velocity

    def finish(self):
        # Remove our contribution to velocity
        self.target.change_x -= self.vx
        self.target.change_y -= self.vy


class JumpBy(IntervalAction):
    """
    Jumps a sprite along a curved path using Arcade-style velocity.
    """

    def __init__(self, delta=(0, 0), height=50, jumps=1, duration=1.0):
        super().__init__(duration)
        self.delta = delta
        self.height = height
        self.jumps = jumps

        self._vx = 0.0
        self._vy_base = 0.0

    def start(self, target):
        super().start(target)
        dx, dy = self.delta
        self._vx = dx / self.duration
        self._vy_base = dy / self.duration
        target.change_x += self._vx

    def update(self, t: float):
        # Vertical sinusoidal curve overlaying constant motion
        jump_sin = abs(math.sin(t * math.pi * self.jumps))
        vy = self._vy_base + (self.height * jump_sin) / self.duration
        self.target.change_y = vy

    def stop(self):
        self.target.change_x -= self._vx
        self.target.change_y = 0.0
        super().stop()


class JumpTo(JumpBy):
    """
    Jumps a sprite to an absolute position using Arcade-style velocity.
    """

    def __init__(self, destination=(0, 0), height=50, jumps=1, duration=1.0):
        super().__init__((0, 0), height, jumps, duration)
        self.destination = destination

    def start(self, target):
        dx = self.destination[0] - target.center_x
        dy = self.destination[1] - target.center_y
        self.delta = (dx, dy)
        super().start(target)


class Bezier(IntervalAction):
    """
    Moves a sprite along a bezier path by dynamically computing velocity.
    """

    def __init__(self, bezier_func, duration=1.0):
        """
        :param bezier_func: A function bezier(t) -> (x, y) for t ∈ [0, 1]
        """
        super().__init__(duration)
        self.bezier = bezier_func
        self.last_position = (0, 0)

    def start(self, target):
        super().start(target)
        self.last_position = target.center_x, target.center_y

    def update(self, t: float):
        cx, cy = self.last_position
        bx, by = self.bezier(t)
        dx = bx - cx
        dy = by - cy
        self.target.change_x = dx / self.duration
        self.target.change_y = dy / self.duration
        self.last_position = (bx, by)

    def stop(self):
        self.target.change_x = 0.0
        self.target.change_y = 0.0
        super().stop()


class Blink(IntervalAction):
    """Toggles sprite.visible N times over the given duration."""

    def __init__(self, times: int, duration: float):
        super().__init__(duration)
        self.times = times
        self.original_visibility = True

    def start(self, target):
        super().start(target)
        self.original_visibility = target.visible

    def update(self, t: float):
        slice_len = 1.0 / self.times
        slice_index = int(t / slice_len)
        # Toggle every other slice
        self.target.visible = slice_index % 2 == 0

    def stop(self):
        self.target.visible = self.original_visibility
        super().stop()

    def __reversed__(self):
        return self  # Blink is symmetrical


class RotateTo(IntervalAction):
    def __init__(self, target_angle: float, duration: float):
        super().__init__(duration)
        self.target_angle = target_angle

    def start(self, target):
        super().start(target)
        self.start_angle = getattr(target, "angle", 0)

    def step(self, t: float):
        delta = self.target_angle - self.start_angle
        self.target.angle = self.start_angle + delta * t


class RotateBy(IntervalAction):
    """Rotates the sprite by a given number of degrees using change_angle."""

    def __init__(self, angle: float, duration: float):
        super().__init__(duration)
        self.angle = angle
        self.d_angle = 0.0

    def start(self, target):
        super().start(target)
        self.d_angle = self.angle / self.duration
        target.change_angle += self.d_angle

    def update(self, t: float):
        pass

    def finish(self):
        self.target.change_angle -= self.d_angle


class ScaleTo(IntervalAction):
    """Scales a sprite to a target zoom factor using .scale"""

    def __init__(self, scale: float, duration: float):
        super().__init__(duration)
        self.end_scale = scale
        self.start_scale = 1.0

    def start(self, target):
        super().start(target)
        self.start_scale = target.scale

    def update(self, t: float):
        new_scale = self.start_scale + (self.end_scale - self.start_scale) * t
        self.target.scale = new_scale

    def stop(self):
        self.target.scale = self.end_scale
        super().stop()


class ScaleBy(ScaleTo):
    """Scales a sprite *by* a factor relative to current scale."""

    def __init__(self, scale_factor: float, duration: float):
        super().__init__(scale=scale_factor, duration=duration)
        self.scale_factor = scale_factor

    def start(self, target):
        self.start_scale = target.scale
        self.end_scale = self.start_scale * self.scale_factor
        super().start(target)

    def __reversed__(self):
        return ScaleBy(1.0 / self.scale_factor, self.duration)


class FadeTo(IntervalAction):
    """Fades the sprite to a specific alpha (0–255) using Arcade's .alpha."""

    def __init__(self, alpha: float, duration: float):
        super().__init__(duration)
        self.alpha = alpha
        self.start_alpha = 255

    def start(self, target):
        super().start(target)
        self.start_alpha = target.alpha

    def update(self, t: float):
        new_alpha = self.start_alpha + (self.alpha - self.start_alpha) * t
        self.target.alpha = int(new_alpha)

    def stop(self):
        self.target.alpha = int(self.alpha)
        super().stop()


class FadeIn(FadeTo):
    """Fades sprite alpha to 255 over time."""

    def __init__(self, duration: float):
        super().__init__(alpha=255, duration=duration)

    def __reversed__(self):
        return FadeOut(self.duration)


class FadeOut(FadeTo):
    """Fades sprite alpha to 0 over time."""

    def __init__(self, duration: float):
        super().__init__(alpha=0, duration=duration)

    def __reversed__(self):
        return FadeIn(self.duration)


class Delay(IntervalAction):
    """Pauses for a fixed time. Does nothing but consume time."""

    def __init__(self, duration: float):
        super().__init__(duration)

    def update(self, t: float):
        pass  # Do nothing

    def __reversed__(self):
        return self


class RandomDelay(Delay):
    """Pauses for a random amount of time between low and high."""

    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high
        super().__init__(random.uniform(low, high))

    def __deepcopy__(self, memo):
        return RandomDelay(self.low, self.high)

    def __mul__(self, other: int):
        if not isinstance(other, int):
            raise TypeError("Can only multiply RandomDelay by an integer.")
        return RandomDelay(self.low * other, self.high * other)


class Lerp(IntervalAction):
    """
    Generic interpolator that sets any float attribute on the sprite.
    Useful for angle, alpha, scale, or custom attributes.
    """

    def __init__(self, attr: str, end_value: float, duration: float):
        super().__init__(duration)
        self.attr = attr
        self.end_value = end_value
        self.start_value = 0.0

    def start(self, target):
        super().start(target)
        self.start_value = getattr(target, self.attr, 0.0)

    def update(self, t: float):
        new_val = self.start_value + (self.end_value - self.start_value) * t
        setattr(self.target, self.attr, new_val)

    def stop(self):
        setattr(self.target, self.attr, self.end_value)
        super().stop()


class Accelerate(IntervalAction):
    """Eases in using t^rate to make the action start slow and speed up."""

    def __init__(self, action: IntervalAction, rate: float = 2.0):
        super().__init__(action.duration)
        self.action = action.clone()
        self.rate = rate

    def start(self, target):
        super().start(target)
        self.action.start(target)

    def update(self, t: float):
        self.action.update(t**self.rate)

    def stop(self):
        self.action.stop()
        super().stop()

    def __reversed__(self):
        return Accelerate(reversed(self.action), self.rate)


class AccelDecel(IntervalAction):
    """Eases in and out with a symmetric curve (cosine-based)."""

    def __init__(self, action: IntervalAction):
        super().__init__(action.duration)
        self.action = action.clone()

    def start(self, target):
        super().start(target)
        self.action.start(target)

    def update(self, t: float):
        eased = (math.cos((t + 1) * math.pi) / 2.0) + 0.5
        self.action.update(eased)

    def stop(self):
        self.action.stop()
        super().stop()

    def __reversed__(self):
        return AccelDecel(reversed(self.action))


class Speed(IntervalAction):
    """Modifies the perceived duration of another action."""

    def __init__(self, action: IntervalAction, speed: float):
        if speed <= 0:
            raise ValueError("Speed must be positive")
        super().__init__(action.duration / speed)
        self.action = action.clone()
        self.speed = speed

    def start(self, target):
        super().start(target)
        self.action.start(target)

    def update(self, t: float):
        # Scale t to real time
        self.action.update(t * self.speed)

    def stop(self):
        self.action.stop()
        super().stop()

    def __reversed__(self):
        return Speed(reversed(self.action), self.speed)


Move = JumpBy
Rotate = RotateBy
Scale = ScaleBy
