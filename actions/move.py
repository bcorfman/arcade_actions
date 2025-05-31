"""
Actions for continuous movement and physics-based movement.
"""

import math
from collections.abc import Callable
from enum import Enum, auto

import arcade

from actions.base import Action, ActionSprite


class Boundary(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class _Move(Action):
    """Base class for continuous movement actions.

    This action updates sprite position based on velocity and acceleration.
    It can work with both regular sprites and physics-enabled sprites.
    """

    def start(self) -> None:
        """Start the movement action."""
        # No initialization needed, just call parent's start
        super().start()

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        # Regular sprite - update position based on velocity
        x, y = self.target.position
        dx, dy = self.target.change_x, self.target.change_y

        # Apply acceleration if present
        if hasattr(self.target, "acceleration"):
            ax, ay = self.target.acceleration
            dx += ax * delta_time
            dy += ay * delta_time

        # Apply gravity if present
        if hasattr(self.target, "gravity"):
            dy += self.target.gravity * delta_time

        # Update velocity
        self.target.change_x = dx
        self.target.change_y = dy

        # Update position
        self.target.position = (x + dx * delta_time, y + dy * delta_time)

        # Update rotation if needed
        if hasattr(self.target, "change_angle"):
            self.target.angle += self.target.change_angle * delta_time


class WrappedMove(_Move):
    """Move sprites with wrapping at screen bounds.

    This action moves sprites continuously across the screen, wrapping them to the opposite
    edge when they move completely off-screen. The wrapping behavior ensures that sprites
    must be fully off-screen before wrapping occurs, and when they wrap, they appear at
    the opposite edge with their appropriate edge aligned to the boundary.

    For example, if a sprite moves off the left edge (right < 0), it will wrap to the right
    edge with its left edge aligned to the right boundary. Similarly, if a sprite moves off
    the right edge (left > width), it will wrap to the left edge with its right edge aligned
    to the left boundary. The same behavior applies to vertical wrapping.

    This action can work with both individual sprites and sprite lists. When used with a
    sprite list, each sprite is wrapped independently.

    Note: This action only handles wrapping behavior. The sprite's position should be updated
    by other actions or directly before this action is updated.

    Attributes:
        get_bounds (Callable[[], Tuple[float, float]]): Function that returns current screen bounds.
        wrap_horizontal (bool): Whether to enable horizontal wrapping.
        wrap_vertical (bool): Whether to enable vertical wrapping.
        on_wrap (Optional[Callable[[ActionSprite, str], None]]): Callback for wrap events.
    """

    def __init__(
        self,
        get_bounds: Callable[[], tuple[float, float]],
        wrap_horizontal: bool = True,
        wrap_vertical: bool = True,
        on_wrap: Callable[[ActionSprite, str], None] | None = None,
    ):
        """Initialize the WrappedMove action.

        Args:
            get_bounds: Function that returns current screen bounds (width, height).
            wrap_horizontal: Whether to enable horizontal wrapping.
            wrap_vertical: Whether to enable vertical wrapping.
            on_wrap: Optional callback function called when a wrap occurs.
                Signature: on_wrap(sprite: ActionSprite, axis: str) -> None
                Where axis is "x" or "y" depending on which direction the wrap occurred.
        """
        super().__init__()
        self.get_bounds = get_bounds
        self.wrap_horizontal = wrap_horizontal
        self.wrap_vertical = wrap_vertical
        self._on_wrap = on_wrap

    def start(self) -> None:
        """Start the wrapping action."""
        super().start()

    def update(self, delta_time: float) -> None:
        """Update sprite positions with wrapping.

        Note: This method only handles wrapping behavior. The sprite's position should be
        updated by other actions or directly before this method is called.
        """
        if self._paused:
            return

        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list()
        else:
            self._update_single_sprite()

    def _update_sprite_list(self) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            self._wrap_sprite(sprite)

    def _update_single_sprite(self) -> None:
        """Update a single sprite's position with wrapping."""
        self._wrap_sprite(self.target)

    def _wrap_sprite(self, sprite: ActionSprite) -> None:
        """Wrap a sprite if it has crossed any boundaries.

        Args:
            sprite: The sprite to check and wrap.
        """
        # Get current screen bounds
        width, height = self.get_bounds()

        # Get sprite's hit box and calculate bounding box
        hit_box = sprite.hit_box
        min_x = hit_box.left
        max_x = hit_box.right
        min_y = hit_box.bottom
        max_y = hit_box.top
        bbox_width = sprite.width
        bbox_height = sprite.height

        # Check horizontal wrapping
        if self.wrap_horizontal:
            if max_x < 0:
                sprite.center_x = width + bbox_width / 2
                if self._on_wrap:
                    self._on_wrap(sprite, "x")
            elif min_x > width:
                sprite.center_x = -bbox_width / 2
                if self._on_wrap:
                    self._on_wrap(sprite, "x")

        # Check vertical wrapping
        if self.wrap_vertical:
            if max_y < 0:
                sprite.center_y = height + bbox_height / 2
                if self._on_wrap:
                    self._on_wrap(sprite, "y")
            elif min_y > height:
                sprite.center_y = -bbox_height / 2
                if self._on_wrap:
                    self._on_wrap(sprite, "y")

    def __repr__(self) -> str:
        return f"WrappedMove(wrap_horizontal={self.wrap_horizontal}, wrap_vertical={self.wrap_vertical})"


class BoundedMove(_Move):
    """Move sprites with bouncing at screen bounds.

    This action moves sprites within screen boundaries, bouncing them off the edges
    when they collide. The bounce behavior is determined by the sprite's movement
    direction and its hit box:

    - When moving right, the sprite bounces when its right edge hits the right boundary
    - When moving left, the sprite bounces when its left edge hits the left boundary
    - When moving up, the sprite bounces when its top edge hits the top boundary
    - When moving down, the sprite bounces when its bottom edge hits the bottom boundary

    This action can work with both individual sprites and sprite lists. When used with a
    sprite list, each sprite bounces independently.

    Note: This action only handles bouncing behavior. The sprite's position should be
    updated by other actions or directly before this action is updated.

    Attributes:
        get_bounds (Callable[[], Tuple[float, float, float, float]]): Function that returns
            current bounding zone (left, bottom, right, top).
        bounce_horizontal (bool): Whether to enable horizontal bouncing.
        bounce_vertical (bool): Whether to enable vertical bouncing.
        on_bounce (Optional[Callable[[ActionSprite, str], None]]): Callback for bounce events.
    """

    def __init__(
        self,
        get_bounds: Callable[[], tuple[float, float, float, float]],
        bounce_horizontal: bool = True,
        bounce_vertical: bool = True,
        on_bounce: Callable[[ActionSprite, str], None] | None = None,
    ):
        """Initialize the BoundedMove action.

        Args:
            get_bounds: Function that returns current bounding zone (left, bottom, right, top).
            bounce_horizontal: Whether to enable horizontal bouncing.
            bounce_vertical: Whether to enable vertical bouncing.
            on_bounce: Optional callback function called when a bounce occurs.
                Signature: on_bounce(sprite: ActionSprite, axis: str) -> None
                Where axis is "x" or "y" depending on which direction the bounce occurred.
        """
        super().__init__()
        self.get_bounds = get_bounds
        self.bounce_horizontal = bounce_horizontal
        self.bounce_vertical = bounce_vertical
        self._on_bounce = on_bounce

    def start(self) -> None:
        """Start the bounded movement action."""
        super().start()

    def update(self, delta_time: float) -> None:
        """Update sprite positions with boundary bouncing."""
        if self._paused:
            return

        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list()
        else:
            self._update_single_sprite()

    def _update_sprite_list(self) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            self._bounce_sprite(sprite)

    def _update_single_sprite(self) -> None:
        """Update a single sprite's position with boundary bouncing."""
        self._bounce_sprite(self.target)

    def _bounce_sprite(self, sprite: ActionSprite) -> None:
        """Bounce a sprite if it has collided with any boundaries.

        Args:
            sprite: The sprite to check and bounce.
        """
        # Get current bounding zone
        left, bottom, right, top = self.get_bounds()

        # Get sprite's hit box and calculate bounding box
        hit_box = sprite.hit_box
        min_x = hit_box.left
        max_x = hit_box.right
        min_y = hit_box.bottom
        max_y = hit_box.top

        # Check horizontal bouncing
        if self.bounce_horizontal:
            if min_x < left:
                # Bounce off left boundary
                sprite.center_x += 2 * (left - min_x)
                sprite.change_x *= -1
                if self._on_bounce:
                    self._on_bounce(sprite, "x")
            elif max_x > right:
                # Bounce off right boundary
                sprite.center_x -= 2 * (max_x - right)
                sprite.change_x *= -1
                if self._on_bounce:
                    self._on_bounce(sprite, "x")

        # Check vertical bouncing
        if self.bounce_vertical:
            if min_y < bottom:
                # Bounce off bottom boundary
                sprite.center_y += 2 * (bottom - min_y)
                sprite.change_y *= -1
                if self._on_bounce:
                    self._on_bounce(sprite, "y")
            elif max_y > top:
                # Bounce off top boundary
                sprite.center_y -= 2 * (max_y - top)
                sprite.change_y *= -1
                if self._on_bounce:
                    self._on_bounce(sprite, "y")

    def __repr__(self) -> str:
        return f"BoundedMove(bounce_horizontal={self.bounce_horizontal}, bounce_vertical={self.bounce_vertical})"


class Driver(Action):
    """Drive sprites like cars, moving in the direction they're facing.

    This action can work with both individual sprites and sprite lists.
    Each sprite will move independently based on its own speed, acceleration,
    and facing direction.
    """

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            self._drive_sprite(sprite, delta_time)

    def _update_single_sprite(self, delta_time: float) -> None:
        """Update a single sprite."""
        self._drive_sprite(self.target, delta_time)

    def _drive_sprite(self, sprite, delta_time: float) -> None:
        """Drive a single sprite based on its speed and direction."""
        # Get current speed and acceleration
        speed = getattr(sprite, "speed", 0)
        acceleration = getattr(sprite, "acceleration", 0)

        # Apply acceleration
        if acceleration:
            speed += acceleration * delta_time

            # Apply speed limits if present
            max_forward = getattr(sprite, "max_forward_speed", None)
            max_reverse = getattr(sprite, "max_reverse_speed", None)

            if max_forward is not None:
                speed = min(speed, max_forward)
            if max_reverse is not None:
                speed = max(speed, max_reverse)

        # Convert angle to radians
        angle_rad = math.radians(sprite.angle)

        # Calculate velocity components
        dx = math.sin(angle_rad) * speed * delta_time
        dy = math.cos(angle_rad) * speed * delta_time

        # Update position
        x, y = sprite.position
        sprite.position = (x + dx, y + dy)

        # Store current speed
        sprite.speed = speed

    def __repr__(self) -> str:
        return "Driver()"
