import math
import random

import arcade

from .base import IntervalAction


class Lerp(IntervalAction):
    def __init__(self, attrib: str, start: float, end: float, duration: float):
        super().__init__(duration)
        self.attrib = attrib
        self.start_value = start
        self.end_value = end
        self.delta = end - start

    def update(self, t: float):
        setattr(self.target, self.attrib, self.start_value + self.delta * t)

    def __reversed__(self):
        return Lerp(self.attrib, self.end_value, self.start_value, self.duration)


class RotateBy(IntervalAction):
    def __init__(self, angle: float, duration: float):
        super().__init__(duration)
        self.angle = angle

    def start(self):
        self.start_angle = self.target.angle

    def update(self, t: float):
        self.target.angle = (self.start_angle + self.angle * t) % 360

    def __reversed__(self):
        return RotateBy(-self.angle, self.duration)


class RotateTo(IntervalAction):
    def __init__(self, angle: float, duration: float):
        super().__init__(duration)
        self.angle = angle % 360

    def start(self):
        sa = self.start_angle = self.target.angle % 360
        ea = self.angle
        self.angle = (ea % 360) - (sa % 360)
        if self.angle > 180:
            self.angle = -360 + self.angle
        if self.angle < -180:
            self.angle = 360 + self.angle

    def update(self, t: float):
        self.target.angle = (self.start_angle + self.angle * t) % 360

    def __reversed__(self):
        return RotateTo(self.start_angle, self.duration)


class Speed(IntervalAction):
    def __init__(self, other: IntervalAction, speed: float):
        super().__init__(other.duration / speed)
        self.other = other
        self.speed = speed

    def start(self):
        self.other.target = self.target
        self.other.start()

    def update(self, t: float):
        self.other.update(t)

    def __reversed__(self):
        return Speed(self.other.__reversed__(), self.speed)


class Accelerate(IntervalAction):
    def __init__(self, other: IntervalAction, rate: float = 2):
        super().__init__(other.duration)
        self.other = other
        self.rate = rate

    def start(self):
        self.other.target = self.target
        self.other.start()

    def update(self, t: float):
        self.other.update(t**self.rate)

    def __reversed__(self):
        return Accelerate(self.other.__reversed__(), 1.0 / self.rate)


class AccelDecel(IntervalAction):
    def __init__(self, other: IntervalAction):
        super().__init__(other.duration)
        self.other = other

    def start(self):
        self.other.target = self.target
        self.other.start()

    def update(self, t: float):
        if t != 1.0:
            ft = (t - 0.5) * 12
            t = 1.0 / (1.0 + math.exp(-ft))
        self.other.update(t)

    def __reversed__(self):
        return AccelDecel(self.other.__reversed__())


class MoveTo(IntervalAction):
    def __init__(self, position: tuple[float, float], duration: float = 5):
        super().__init__(duration)
        self.end_position = position

    def start(self):
        self.start_position = (self.target.center_x, self.target.center_y)
        self.delta = (self.end_position[0] - self.start_position[0], self.end_position[1] - self.start_position[1])

    def update(self, t: float):
        new_x = self.start_position[0] + self.delta[0] * t
        new_y = self.start_position[1] + self.delta[1] * t
        self.target.center_x, self.target.center_y = new_x, new_y

    def update_delta(self, dx: float, dy: float):
        self.delta = dx, dy
        # Recalculate end position from current position
        self.end_position = (self.start_position[0] + self.delta[0], self.start_position[1] + self.delta[1])


class MoveBy(MoveTo):
    def __init__(self, delta: tuple[float, float], duration: float = 5):
        super().__init__(delta, duration)
        self.delta = delta

    def start(self):
        self.start_position = (self.target.center_x, self.target.center_y)
        self.end_position = (self.start_position[0] + self.delta[0], self.start_position[1] + self.delta[1])

    def __reversed__(self):
        return MoveBy((-self.delta[0], -self.delta[1]), self.duration)


class FadeOut(IntervalAction):
    def __init__(self, duration: float):
        super().__init__(duration)

    def update(self, t: float):
        self.target.alpha = int(255 * (1 - t))

    def __reversed__(self):
        return FadeIn(self.duration)


class FadeTo(IntervalAction):
    def __init__(self, alpha: int, duration: float):
        super().__init__(duration)
        self.end_alpha = alpha

    def start(self):
        self.start_alpha = self.target.alpha

    def update(self, t: float):
        self.target.alpha = int(self.start_alpha + (self.end_alpha - self.start_alpha) * t)


class FadeIn(FadeOut):
    def update(self, t: float):
        self.target.alpha = int(255 * t)

    def __reversed__(self):
        return FadeOut(self.duration)


class ScaleTo(IntervalAction):
    def __init__(self, scale: float, duration: float = 5):
        super().__init__(duration)
        self.end_scale = scale

    def start(self):
        self.start_scale = self.target.scale

    def update(self, t: float):
        self.target.scale = self.start_scale + (self.end_scale - self.start_scale) * t


class ScaleBy(ScaleTo):
    def start(self):
        self.start_scale = self.target.scale
        self.end_scale = self.start_scale * self.end_scale

    def __reversed__(self):
        return ScaleBy(1.0 / self.end_scale, self.duration)


class Blink(IntervalAction):
    def __init__(self, times: int, duration: float):
        super().__init__(duration)
        self.times = times

    def update(self, t: float):
        slice = 1.0 / self.times
        m = t % slice
        self.target.visible = m > slice / 2.0

    def __reversed__(self):
        return self


class Bezier(IntervalAction):
    def __init__(self, bezier: list[tuple[float, float]], duration: float = 5):
        super().__init__(duration)
        self.bezier = bezier

    def start(self):
        self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float):
        p = self._bezier_at(t)
        self.target.center_x = self.start_position[0] + p[0]
        self.target.center_y = self.start_position[1] + p[1]

    def _bezier_at(self, t: float) -> tuple[float, float]:
        # Simple implementation for cubic Bezier curve
        cx = 3 * (self.bezier[1][0] - self.bezier[0][0])
        bx = 3 * (self.bezier[2][0] - self.bezier[1][0]) - cx
        ax = self.bezier[3][0] - self.bezier[0][0] - cx - bx
        cy = 3 * (self.bezier[1][1] - self.bezier[0][1])
        by = 3 * (self.bezier[2][1] - self.bezier[1][1]) - cy
        ay = self.bezier[3][1] - self.bezier[0][1] - cy - by

        x = ax * (t**3) + bx * (t**2) + cx * t + self.bezier[0][0]
        y = ay * (t**3) + by * (t**2) + cy * t + self.bezier[0][1]
        return (x, y)

    def __reversed__(self):
        return Bezier(list(reversed(self.bezier)), self.duration)


class JumpBy(IntervalAction):
    def __init__(self, position: tuple[float, float], height: float, jumps: int, duration: float):
        super().__init__(duration)
        self.delta = position
        self.height = height
        self.jumps = jumps

    def start(self):
        self.start_position = (self.target.center_x, self.target.center_y)

    def update(self, t: float):
        y = self.height * abs(math.sin(t * math.pi * self.jumps))
        x = self.delta[0] * t
        y += self.delta[1] * t
        self.target.center_x = self.start_position[0] + x
        self.target.center_y = self.start_position[1] + y

    def __reversed__(self):
        return JumpBy((-self.delta[0], -self.delta[1]), self.height, self.jumps, self.duration)


class JumpTo(JumpBy):
    def start(self):
        super().start()
        self.delta = (self.delta[0] - self.start_position[0], self.delta[1] - self.start_position[1])


class Delay(IntervalAction):
    def __init__(self, delay: float):
        super().__init__(delay)

    def __reversed__(self):
        return self


class RandomDelay(Delay):
    def __init__(self, low: float, high: float):
        super().__init__(random.uniform(low, high))


# Usage example
if __name__ == "__main__":
    window = arcade.Window(800, 600, "Interval Actions Example")

    sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    sprite.center_x = 400
    sprite.center_y = 300

    action = MoveTo((600, 400), 2.0) + RotateBy(360, 1.0) | ScaleTo(2, 3.0) + FadeOut(1.0) + FadeIn(1.0) + JumpBy(
        (0, 100), 50, 2, 1.0
    ) + Blink(5, 1.0) + Delay(1.0) + ScaleTo(1, 1.0)

    sprite.do(action)

    @window.event
    def on_draw():
        arcade.start_render()
        sprite.draw()

    def update(delta_time):
        sprite.update()

    arcade.schedule(update, 1 / 60)

    arcade.run()
