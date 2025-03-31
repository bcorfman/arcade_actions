import arcade

from .base import Action, ActionSprite, auto_clone

__all__ = [
    "Move",
    "WrappedMove",
    "BoundedMove",
    "ReversedMove",
]


@auto_clone
class Move(Action):
    """Move the target based on parameters on the target.

    For movement the parameters are::

        target.position = (x, y)
        target.velocity = (dx, dy)
        target.acceleration = (ddx, ddy) = (0, 0)
        target.gravity = 0

    And rotation::

        target.rotation
        target.dr
        target.ddr
    """

    def step(self, dt):
        x, y = self.target.position
        dx, dy = self.target.velocity
        ddx, ddy = getattr(self.target, "acceleration", (0, 0))
        gravity = getattr(self.target, "gravity", 0)
        dx += ddx * dt
        dy += (ddy + gravity) * dt
        self.target.velocity = (dx, dy)
        x += dx * dt
        y += dy * dt
        self.target.position = (x, y)
        dr = getattr(self.target, "dr", 0)
        ddr = getattr(self.target, "ddr", 0)
        if dr or ddr:
            dr = self.target.dr = dr + ddr * dt
        if dr:
            self.target.rotation += dr * dt


@auto_clone
class WrappedMove(Move):
    """Move the target but wrap position when it hits certain bounds.

    Wrap occurs outside of 0 < x < width and 0 < y < height taking into
    account the dimenstions of the target."""

    def __init__(self, width: int, height: int):
        """Init method.

        :Parameters:
            `width` : integer
                The width to wrap position at.
            `height` : integer
                The height to wrap position at.
        """
        super().__init__(float("inf"))
        self.width, self.height = width, height

    def step(self, dt):
        super(WrappedMove, self).step(dt)
        x, y = self.target.center_x, self.target.center_y
        w, h = self.target.width, self.target.height

        # Enforce bounds
        if x > self.width + w / 2:
            x -= self.width + w
        elif x < 0 - w / 2:
            x += self.width + w
        if y > self.height + h / 2:
            y -= self.height + h
        elif y < 0 - h / 2:
            y += self.height + h

        self.target.center_x = x
        self.target.center_y = y


@auto_clone
class BoundedMove(Move):
    """Move the target but limit position when it hits certain bounds."""

    def __init__(self, bounds: tuple[float, float, float, float]):
        super().__init__(float("inf"))
        self.bounds = bounds

    def step(self, dt):
        super(BoundedMove, self).step(dt)
        x, y = self.target.center_x, self.target.center_y
        w, h = self.target.width, self.target.height

        # Enforce bounds
        left, right, bottom, top = self.bounds
        x = min(max(x, left + w / 2), right - w / 2)
        y = min(max(y, bottom + h / 2), top - h / 2)

        self.target.center_x = x
        self.target.center_y = y


@auto_clone
class ReversedMove(Move):
    """Move the target but reverse direction when it hits certain bounds."""

    # How does this apply to a SpriteList?
    # query single representative sprite that is leftmost or rightmost
    # then apply velocity reversal to all sprites in list ... or there is only one group velocity that everyone "uses"?
    def __init__(self, bounds: tuple[float, float, float, float]):
        super().__init__(float("inf"))
        self.bounds = bounds

    def step(self, dt):
        left, right, bottom, top = self.bounds
        if isinstance(self.target, arcade.SpriteList) and len(self.target):
            first: ActionSprite = self.target[0]
            if first:
                boundary_x, boundary_y, min_y, max_y = 999999, -999999, 999999, -999999
            minx_maxwidth, maxx_maxwidth, miny_maxwidth, maxy_maxwidth = 0, 0, 0, 0
            for sprite in self.target:
                if sprite.center_x < min_x:
                    min_x = sprite.center_x
                    minx_maxwidth = sprite.width
                elif sprite.center_x == min_x:
                    minx_maxwidth = max(minx_maxwidth, sprite.width)
                if sprite.center_x > max_x:
                    max_x = sprite.center_x
                    maxx_maxwidth = sprite.width
                elif sprite.center_x == max_x:
                    maxx_maxwidth = max(maxx_maxwidth, sprite.width)
                if sprite.center_y < min_y:
                    min_y = sprite.center_y
                    miny_maxwidth = sprite.width
                elif sprite.center_y == min_y:
                    miny_maxwidth = max(miny_maxwidth, sprite.width)
                if sprite.center_y > max_y:
                    max_y = sprite.center_y
                    maxy_maxwidth = sprite.width
                elif sprite.center_y == max_y:
                    maxy_maxwidth = max(maxy_maxwidth, sprite.width)

            if min_x < left - w / 2 or x > right + w / 2:
                dx = -dx
            if y < bottom - h / 2 or y > top + h / 2:
                dy = -dy

        elif isinstance(self.target, ActionSprite):
            x, y = self.target.center_x, self.target.center_y
            w, h = self.target.width, self.target.height
            dx, dy = self.target.velocity

            # Enforce bounds
            if x < left - w / 2 or x > right + w / 2:
                dx = -dx
            if y < bottom - h / 2 or y > top + h / 2:
                dy = -dy

        self.target.velocity = (dx, dy)
        super(ReversedMove, self).step(dt)
