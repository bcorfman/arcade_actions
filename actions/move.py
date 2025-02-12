from .base import Action


class Move(Action):
    """Move the target based on parameters on the target.

    For movement parameters:
    target.position = (x, y)     # Current position
    target.velocity = (dx, dy)   # Current velocity
    target.acceleration = (ddx, ddy) = (0, 0)  # Optional acceleration
    target.gravity = 0          # Optional gravity

    For rotation:
    target.rotation   # Current rotation angle
    target.dr        # Angular velocity
    target.ddr       # Angular acceleration
    """

    def step(self, dt: float) -> None:
        """Update position and rotation based on physics parameters.

        Args:
            dt: Time delta since last update in seconds
        """
        if self.target is None:
            raise ValueError("Target must not be None")

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


class WrappedMove(Move):
    """Move the target with position wrapping at boundaries.

    When the target moves beyond the specified boundaries, its position
    wraps around to the opposite side, taking the target's dimensions
    into account. Wrapping occurs outside of 0 < x < width and
    0 < y < height.
    """

    def init(self, width: float = None, height: float = None) -> None:
        """Initialize the wrapping boundaries.

        Args:
            width: The width boundary for wrapping
            height: The height boundary for wrapping

        Raises:
            ValueError: If width or height are not positive
        """
        if width is not None and height is not None:
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be positive")

        self.width = width
        self.height = height

    def step(self, dt: float) -> None:
        """Update position with wrapping at boundaries.

        Args:
            dt: Time delta since last update in seconds

        Raises:
            ValueError: If boundaries not initialized
            AttributeError: If target lacks required dimensions
        """
        if self.width is None or self.height is None:
            raise ValueError("Must call init() before step()")

        # Perform normal movement
        super().step(dt)

        if not hasattr(self.target, "width") or not hasattr(self.target, "height"):
            raise AttributeError("Target must have width and height attributes")

        # Get current state
        x, y = self.target.position
        w, h = self.target.width, self.target.height

        # Wrap horizontally
        if x > self.width + w / 2:
            x -= self.width + w
        elif x < 0 - w / 2:
            x += self.width + w

        # Wrap vertically
        if y > self.height + h / 2:
            y -= self.height + h
        elif y < 0 - h / 2:
            y += self.height + h

        self.target.position = (x, y)


class BoundedMove(Move):
    """Move the target with position bounded by boundaries.

    When the target moves beyond the specified boundaries, its position
    is clamped to the boundary edges, taking the target's dimensions
    into account. Position is bounded to 0 < x < width and 0 < y < height.
    """

    def init(self, width: float = None, height: float = None) -> None:
        """Initialize the boundary limits.

        Args:
            width: The width boundary for position limiting
            height: The height boundary for position limiting

        Raises:
            ValueError: If width or height are not positive
        """
        if width is not None and height is not None:
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be positive")

        self.width = width
        self.height = height

    def step(self, dt: float) -> None:
        """Update position with boundary clamping.

        Args:
            dt: Time delta since last update in seconds

        Raises:
            ValueError: If boundaries not initialized
            AttributeError: If target lacks required dimensions
        """
        if self.width is None or self.height is None:
            raise ValueError("Must call init() before step()")

        # Perform normal movement
        super().step(dt)

        if not hasattr(self.target, "width") or not hasattr(self.target, "height"):
            raise AttributeError("Target must have width and height attributes")

        # Get current state
        x, y = self.target.position
        w, h = self.target.width, self.target.height

        # Bound horizontally
        if x > self.width - w / 2:
            x = self.width - w / 2
        elif x < w / 2:
            x = w / 2

        # Bound vertically
        if y > self.height - h / 2:
            y = self.height - h / 2
        elif y < h / 2:
            y = h / 2

        self.target.position = (x, y)
