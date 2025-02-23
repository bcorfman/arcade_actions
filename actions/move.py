from actions.interval import IntervalAction


class BoundedMove(IntervalAction):
    def __init__(self, bounds: tuple[float, float, float, float]):
        super().__init__(float("inf"))
        self.bounds = bounds

    def update(self, t: float):
        # Get current position
        x, y = self.target.center_x, self.target.center_y
        w, h = self.target.width, self.target.height

        # Enforce bounds
        left, right, bottom, top = self.bounds
        x = min(max(x, left + w / 2), right - w / 2)
        y = min(max(y, bottom + h / 2), top - h / 2)

        self.target.center_x = x
        self.target.center_y = y
