from .base import IntervalAction

__all__ = [
    "WrappedMove",
    "BoundedMove",
]


class _Move(IntervalAction):
    def __init__(self, delta: tuple[float, float], duration: float):
        super().__init__(duration)
        self.delta = delta

    def start(self, target):
        super().start(target)
        self.start_pos = (target.center_x, target.center_y)

    def step(self, t: float):
        dx = self.delta[0] * t
        dy = self.delta[1] * t
        self.target.center_x = self.start_pos[0] + dx
        self.target.center_y = self.start_pos[1] + dy

    def __reversed__(self):
        return _Move((-self.delta[0], -self.delta[1]), self.duration)

    def __invert__(self):
        return self.__reversed__()


class WrappedMove(_Move):
    def __init__(self, delta: tuple[float, float], bounds: tuple[float, float, float, float], duration: float):
        super().__init__(delta, duration)
        self.bounds = bounds  # (min_x, max_x, min_y, max_y)

    def step(self, t: float):
        super().step(t)
        min_x, max_x, min_y, max_y = self.bounds

        if self.target.center_x < min_x:
            self.target.center_x = max_x
        elif self.target.center_x > max_x:
            self.target.center_x = min_x

        if self.target.center_y < min_y:
            self.target.center_y = max_y
        elif self.target.center_y > max_y:
            self.target.center_y = min_y


class BoundedMove(_Move):
    def __init__(self, delta: tuple[float, float], bounds: tuple[float, float, float, float], duration: float):
        super().__init__(delta, duration)
        self.bounds = bounds

    def step(self, t: float):
        super().step(t)
        min_x, max_x, min_y, max_y = self.bounds

        if self.target.center_x < min_x:
            self.target.center_x = min_x
            self.delta = (-self.delta[0], self.delta[1])
        elif self.target.center_x > max_x:
            self.target.center_x = max_x
            self.delta = (-self.delta[0], self.delta[1])

        if self.target.center_y < min_y:
            self.target.center_y = min_y
            self.delta = (self.delta[0], -self.delta[1])
        elif self.target.center_y > max_y:
            self.target.center_y = max_y
            self.delta = (self.delta[0], -self.delta[1])
