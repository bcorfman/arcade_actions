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

        # Handle both individual sprites and sprite lists
        if isinstance(self.target, (arcade.SpriteList, list)):
            self._move_sprite_list(delta_time)
        else:
            self._move_single_sprite(delta_time)

    def _move_single_sprite(self, delta_time: float) -> None:
        """Update a single sprite's position based on velocity and physics."""
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

    def _move_sprite_list(self, delta_time: float) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            # Store current target
            original_target = self.target
            # Temporarily set target to individual sprite
            self.target = sprite
            # Update the sprite
            self._move_single_sprite(delta_time)
            # Restore original target
            self.target = original_target


class WrappedMove(Action):
    """Action controller that adds wrapping behavior to movement actions.

    This action works by monitoring sprite positions and wrapping them when they
    move off-screen. It can work with any movement action including IntervalActions
    like MoveBy, MoveTo, and eased movements.

    The wrapping behavior ensures that sprites must be fully off-screen before
    wrapping occurs, and when they wrap, they appear at the opposite edge.

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

        This method only handles wrapping behavior. The sprite's position should be
        updated by other actions before this method is called.
        """
        if self._paused:
            return

        if isinstance(self.target, (arcade.SpriteList, list)):
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


class BoundedMove(Action):
    """Action controller that adds bouncing behavior to movement actions.

    This action works by monitoring sprite positions and velocities, reversing
    movement direction when boundaries are hit. It can work with any movement
    action including IntervalActions like MoveBy, MoveTo, and eased movements.

    When a boundary is hit, this action:
    1. Adjusts the sprite position to be within bounds
    2. Reverses the sprite's change_x or change_y velocity
    3. If working with IntervalActions, modifies them to continue in the opposite direction

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
        # Initialize previous position tracking for all target sprites
        if isinstance(self.target, (arcade.SpriteList, list)):
            for sprite in self.target:
                sprite._prev_x = sprite.center_x
                sprite._prev_y = sprite.center_y
        else:
            self.target._prev_x = self.target.center_x
            self.target._prev_y = self.target.center_y

    def update(self, delta_time: float) -> None:
        """Update sprite positions with boundary bouncing."""
        if self._paused:
            return

        if isinstance(self.target, (arcade.SpriteList, list)):
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

        # Track the sprite's previous position to determine movement direction
        prev_x = getattr(sprite, "_prev_x", sprite.center_x)
        prev_y = getattr(sprite, "_prev_y", sprite.center_y)

        # Calculate movement direction from position change
        dx = sprite.center_x - prev_x
        dy = sprite.center_y - prev_y

        # Check horizontal bouncing
        if self.bounce_horizontal:
            bounced_x = False

            if max_x > right:  # Right edge beyond right boundary
                # Bounce off right boundary
                sprite.center_x -= 2 * (max_x - right)
                # Reverse horizontal velocity if present
                if hasattr(sprite, "change_x"):
                    sprite.change_x = -abs(sprite.change_x)
                self._reverse_movement_actions(sprite, "x")
                bounced_x = True
                if self._on_bounce:
                    self._on_bounce(sprite, "x")
            elif min_x < left:  # Left edge beyond left boundary
                # Bounce off left boundary
                sprite.center_x += 2 * (left - min_x)
                # Reverse horizontal velocity if present
                if hasattr(sprite, "change_x"):
                    sprite.change_x = abs(sprite.change_x)
                self._reverse_movement_actions(sprite, "x")
                bounced_x = True
                if self._on_bounce:
                    self._on_bounce(sprite, "x")

        # Check vertical bouncing
        if self.bounce_vertical:
            bounced_y = False

            if max_y > top:  # Top edge beyond top boundary
                # Bounce off top boundary
                sprite.center_y -= 2 * (max_y - top)
                # Reverse vertical velocity if present
                if hasattr(sprite, "change_y"):
                    sprite.change_y = -abs(sprite.change_y)
                self._reverse_movement_actions(sprite, "y")
                bounced_y = True
                if self._on_bounce:
                    self._on_bounce(sprite, "y")
            elif min_y < bottom:  # Bottom edge beyond bottom boundary
                # Bounce off bottom boundary
                sprite.center_y += 2 * (bottom - min_y)
                # Reverse vertical velocity if present
                if hasattr(sprite, "change_y"):
                    sprite.change_y = abs(sprite.change_y)
                self._reverse_movement_actions(sprite, "y")
                bounced_y = True
                if self._on_bounce:
                    self._on_bounce(sprite, "y")

        # Store current position for next frame
        sprite._prev_x = sprite.center_x
        sprite._prev_y = sprite.center_y

    def _reverse_movement_actions(self, sprite: ActionSprite, axis: str) -> None:
        """Reverse movement actions for the specified axis.

        Args:
            sprite: The sprite whose actions to reverse
            axis: 'x' for horizontal, 'y' for vertical
        """
        # Find and reverse any IntervalActions that are currently running
        if hasattr(sprite, "_action") and sprite._action:
            self._reverse_action_movement(sprite._action, axis)

    def _reverse_action_movement(self, action, axis: str) -> None:
        """Reverse movement for a specific action.

        Args:
            action: The action to reverse
            axis: 'x' for horizontal, 'y' for vertical
        """
        # Handle Spawn actions (created by | operator)
        if hasattr(action, "actions"):
            for child_action in action.actions:
                self._reverse_action_movement(child_action, axis)
            return

        # Handle MoveBy actions
        if hasattr(action, "delta") and hasattr(action, "total_change"):
            if axis == "x":
                # Reverse horizontal movement
                action.delta = (-action.delta[0], action.delta[1])
                action.total_change = (-action.total_change[0], action.total_change[1])
            else:
                # Reverse vertical movement
                action.delta = (action.delta[0], -action.delta[1])
                action.total_change = (action.total_change[0], -action.total_change[1])

        # Handle MoveTo actions by reversing their target
        elif hasattr(action, "end_position") and hasattr(action, "total_change"):
            if axis == "x":
                # Calculate new end position for horizontal reversal
                current_x = action.target.center_x
                remaining_x = action.total_change[0] * (1.0 - action._elapsed / action.duration)
                new_end_x = current_x - remaining_x
                action.end_position = (new_end_x, action.end_position[1])
                action.total_change = (-action.total_change[0], action.total_change[1])
            else:
                # Calculate new end position for vertical reversal
                current_y = action.target.center_y
                remaining_y = action.total_change[1] * (1.0 - action._elapsed / action.duration)
                new_end_y = current_y - remaining_y
                action.end_position = (action.end_position[0], new_end_y)
                action.total_change = (action.total_change[0], -action.total_change[1])

        # Handle Easing actions by recursing to their wrapped action
        elif hasattr(action, "other"):
            self._reverse_action_movement(action.other, axis)

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

        if isinstance(self.target, (arcade.SpriteList, list)):
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
