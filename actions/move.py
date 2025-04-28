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

    def update(self, delta_time: float):
        dx = self.delta[0] * delta_time
        dy = self.delta[1] * delta_time
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

    def update(self, delta_time: float):
        super().update(delta_time)
        min_x, max_x, min_y, max_y = self.bounds

        if self.target.center_x < min_x:
            self.target.center_x = max_x
        elif self.target.center_x > max_x:
            self.target.center_x = min_x

        if self.target.center_y < min_y:
            self.target.center_y = max_y
        elif self.target.center_y > max_y:
            self.target.center_y = min_y


class BoundedMove(IntervalAction):
    def __init__(self, velocity=(100, 0), bounds=(0, 800), on_hit_left=None, on_hit_right=None):
        super().__init__(duration=0)  # Infinite duration
        self.velocity = velocity
        self.bounds = bounds
        self.on_hit_left = on_hit_left
        self.on_hit_right = on_hit_right
        self.group = None
        self.reversed = False

    def start(self, target):
        self.group = list(target) if hasattr(target, "__iter__") else [target]
        for sprite in self.group:
            sprite.change_x = self.velocity[0]
            sprite.change_y = self.velocity[1]

    def update(self, delta_time: float):
        self.check_bounds()

    def stop(self):
        for sprite in self.group:
            sprite.change_x = 0
            sprite.change_y = 0
        super().stop()

    def check_bounds(self):
        left, right = self.bounds
        hit_edge = any(s.left <= left or s.right >= right for s in self.group)

        if hit_edge and not self.reversed:
            self.reversed = True
            for sprite in self.group:
                sprite.change_x *= -1

            for sprite in self.group:
                if sprite.left <= left and self.on_hit_left:
                    self.on_hit_left(sprite)
                if sprite.right >= right and self.on_hit_right:
                    self.on_hit_right(sprite)

        elif not hit_edge:
            self.reversed = False
