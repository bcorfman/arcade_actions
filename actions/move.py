"""
Actions for continuous movement and physics-based movement.
"""

import math
from collections.abc import Callable
from enum import Enum, auto

import arcade

from actions.base import Action, ActionSprite, GroupTarget


class MovementDirection(Enum):
    """Enumeration for movement directions."""

    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


class MovementAction(Action):
    """Base class for movement actions with consistent interface."""

    def __init__(self):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.delta: tuple[float, float] = (0.0, 0.0)
        self.total_change: tuple[float, float] = (0.0, 0.0)
        self.end_position: tuple[float, float] | None = None

    def get_movement_delta(self) -> tuple[float, float]:
        """Get the movement delta for this action."""
        return self.delta

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement for the specified axis."""
        if axis == "x":
            self.delta = (-self.delta[0], self.delta[1])
            self.total_change = (-self.total_change[0], self.total_change[1])
        else:  # axis == "y"
            self.delta = (self.delta[0], -self.delta[1])
            self.total_change = (self.total_change[0], -self.total_change[1])


class CompositeAction(Action):
    """Base class for composite actions with consistent interface."""

    def __init__(self):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.actions: list[Action] = []
        self.current_action: Action | None = None
        self.current_index: int = 0

    def get_movement_actions(self) -> list[MovementAction]:
        """Get all movement actions from this composite."""
        movement_actions = []
        for action in self.actions:
            if isinstance(action, MovementAction):
                movement_actions.append(action)
            elif isinstance(action, CompositeAction):
                movement_actions.extend(action.get_movement_actions())
        return movement_actions


class EasingAction(Action):
    """Base class for easing wrapper actions with consistent interface."""

    def __init__(self, other: Action):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.other = other

    def get_wrapped_action(self) -> Action:
        """Get the wrapped action."""
        return self.other


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
        target = self.target

        # Regular sprite - update position based on velocity
        x, y = target.position
        dx, dy = target.change_x, target.change_y

        # Apply acceleration - NO MORE hasattr CHECKING
        ax, ay = target.physics.acceleration
        dx += ax * delta_time
        dy += ay * delta_time

        # Apply gravity - NO MORE hasattr CHECKING
        dy += target.physics.gravity * delta_time

        # Update velocity
        target.change_x = dx
        target.change_y = dy

        # Update position
        target.position = (x + dx * delta_time, y + dy * delta_time)

        # Update rotation - NO MORE hasattr CHECKING
        target.angle += target.change_angle * delta_time

    def _move_sprite_list(self, delta_time: float) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            # Create temporary target for consistent interface
            temp_target = self.target
            self.target = sprite
            self._move_single_sprite(delta_time)
            self.target = temp_target


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

        # Check if we're working with a GroupTarget - NO MORE getattr CHECKING
        is_group_target = isinstance(self.target, GroupTarget)

        # Horizontal wrapping
        if self.wrap_horizontal:
            if max_x < 0:  # Sprite has moved completely off left edge
                # Only wrap if this is an edge sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "left"):
                    sprite.center_x = width + bbox_width / 2
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")
            elif min_x > width:  # Sprite has moved completely off right edge
                # Only wrap if this is an edge sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "right"):
                    sprite.center_x = -bbox_width / 2
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")

        # Vertical wrapping
        if self.wrap_vertical:
            if max_y < 0:  # Sprite has moved completely off bottom edge
                # Only wrap if this is an edge sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "bottom"):
                    sprite.center_y = height + bbox_height / 2
                    if self._on_wrap:
                        self._on_wrap(sprite, "y")
            elif min_y > height:  # Sprite has moved completely off top edge
                # Only wrap if this is an edge sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "top"):
                    sprite.center_y = -bbox_height / 2
                    if self._on_wrap:
                        self._on_wrap(sprite, "y")

    def _is_edge_sprite(self, sprite: ActionSprite, edge: str) -> bool:
        """Check if a sprite is on the specified edge of the group.

        Args:
            sprite: The sprite to check
            edge: The edge to check ("left", "right", "top", "bottom")

        Returns:
            True if the sprite is on the specified edge
        """
        if not isinstance(self.target, GroupTarget):
            return True  # Not a GroupTarget, treat as edge sprite

        sprites = list(self.target)
        if not sprites:
            return True

        tolerance = 5  # Pixel tolerance for edge detection

        if edge == "left":
            leftmost_x = min(s.center_x for s in sprites)
            return abs(sprite.center_x - leftmost_x) < tolerance
        elif edge == "right":
            rightmost_x = max(s.center_x for s in sprites)
            return abs(sprite.center_x - rightmost_x) < tolerance
        elif edge == "top":
            topmost_y = max(s.center_y for s in sprites)
            return abs(sprite.center_y - topmost_y) < tolerance
        elif edge == "bottom":
            bottommost_y = min(s.center_y for s in sprites)
            return abs(sprite.center_y - bottommost_y) < tolerance

        return False

    def __repr__(self) -> str:
        return f"WrappedMove(wrap_horizontal={self.wrap_horizontal}, wrap_vertical={self.wrap_vertical})"


class BoundedMove(Action):
    """Action controller that adds bouncing behavior to movement actions.

    This action works by monitoring sprite positions and bouncing them when they
    hit boundaries. It can work with any movement action and provides callbacks
    for bounce events.

    The bouncing behavior is optimized for group formations like Space Invaders:
    - Only edge sprites trigger bounce detection
    - Callbacks can coordinate entire group behavior
    - Movement direction is tracked to optimize boundary checking

    Attributes:
        get_bounds (Callable[[], Tuple[float, float, float, float]]): Function that returns bounding zone.
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

        # Track movement direction to determine which boundary to check
        self._horizontal_direction: MovementDirection | None = None
        self._vertical_direction: MovementDirection | None = None

    def update(self, delta_time: float) -> None:
        """Update sprite positions with boundary bouncing."""
        if self._paused:
            return

        # Update movement direction based on current movement
        self._update_movement_direction()

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

    def _update_movement_direction(self) -> None:
        """Update the tracked movement direction based on current sprite movement."""
        representative_sprite = self._get_representative_sprite()
        if representative_sprite is None:
            return

        # Try to determine direction from sprite velocity first
        self._set_direction_from_velocity(representative_sprite)

        # If no velocity info, try to infer from active actions
        if self._horizontal_direction is None or self._vertical_direction is None:
            self._infer_direction_from_actions(representative_sprite)

    def _get_representative_sprite(self) -> ActionSprite | None:
        """Get a representative sprite for direction detection."""
        if isinstance(self.target, (arcade.SpriteList, list)):
            if not self.target:
                return None
            return next(iter(self.target))
        else:
            return self.target

    def _set_direction_from_velocity(self, sprite: ActionSprite) -> None:
        """Set movement direction based on sprite velocity."""
        if isinstance(self.target, (arcade.SpriteList, list)):
            # For sprite lists, check all sprites for movement
            for list_sprite in self.target:
                change_x = list_sprite.change_x
                change_y = list_sprite.change_y

                if self._horizontal_direction is None and change_x != 0:
                    self._horizontal_direction = MovementDirection.RIGHT if change_x > 0 else MovementDirection.LEFT

                if self._vertical_direction is None and change_y != 0:
                    self._vertical_direction = MovementDirection.UP if change_y > 0 else MovementDirection.DOWN

                # Stop once we have both directions
                if self._horizontal_direction and self._vertical_direction:
                    break
        else:
            # For single sprites, check the sprite velocity
            change_x = sprite.change_x
            change_y = sprite.change_y

            if change_x != 0:
                self._horizontal_direction = MovementDirection.RIGHT if change_x > 0 else MovementDirection.LEFT

            if change_y != 0:
                self._vertical_direction = MovementDirection.UP if change_y > 0 else MovementDirection.DOWN

    def _infer_direction_from_actions(self, sprite: ActionSprite) -> None:
        """Infer movement direction from active actions on the sprite."""
        # Check if we're working with a GroupTarget that has group actions
        if isinstance(self.target, GroupTarget):
            self._extract_from_group_actions()
        elif isinstance(self.target, (arcade.SpriteList, list)):
            # For sprite lists, check all sprites for actions
            for list_sprite in self.target:
                sprite_action = list_sprite._action
                if sprite_action:
                    self._extract_direction_from_action(sprite_action)
                    # Stop once we have both directions
                    if self._horizontal_direction and self._vertical_direction:
                        break
        else:
            # Check individual sprite actions
            sprite_action = sprite._action
            if sprite_action:
                self._extract_direction_from_action(sprite_action)

    def _extract_from_group_actions(self) -> None:
        """Extract direction from group actions."""
        if isinstance(self.target, GroupTarget):
            for group_action in self.target._group_actions:
                if isinstance(group_action, CompositeAction):
                    for action in group_action.actions:
                        self._extract_direction_from_action(action)
                else:
                    self._extract_direction_from_action(group_action)

    def _extract_direction_from_action(self, action: Action) -> None:
        """Extract movement direction from a specific action using type-based dispatch."""
        if isinstance(action, MovementAction):
            self._handle_movement_action(action)
        elif isinstance(action, CompositeAction):
            self._handle_composite_action(action)
        elif isinstance(action, EasingAction):
            self._handle_easing_action(action)

    def _handle_movement_action(self, action: MovementAction) -> None:
        """Handle movement actions."""
        delta = action.get_movement_delta()
        if self._horizontal_direction is None and delta[0] != 0:
            self._horizontal_direction = MovementDirection.RIGHT if delta[0] > 0 else MovementDirection.LEFT
        if self._vertical_direction is None and delta[1] != 0:
            self._vertical_direction = MovementDirection.UP if delta[1] > 0 else MovementDirection.DOWN

    def _handle_composite_action(self, action: CompositeAction) -> None:
        """Handle composite actions."""
        if action.current_action:
            self._extract_direction_from_action(action.current_action)

        # Also check all actions in the composite
        for child_action in action.actions:
            self._extract_direction_from_action(child_action)

    def _handle_easing_action(self, action: EasingAction) -> None:
        """Handle easing wrapper actions."""
        wrapped_action = action.get_wrapped_action()
        if wrapped_action:
            self._extract_direction_from_action(wrapped_action)

    def _reverse_sprite_velocity(self, sprite: ActionSprite, axis: str, direction: int) -> None:
        """Reverse sprite velocity for bouncing.

        Args:
            sprite: The sprite to modify
            axis: 'x' or 'y'
            direction: 1 for positive, -1 for negative
        """
        if axis == "x":
            current_velocity = sprite.change_x
            if current_velocity != 0:
                sprite.change_x = direction * abs(current_velocity)
        else:  # axis == "y"
            current_velocity = sprite.change_y
            if current_velocity != 0:
                sprite.change_y = direction * abs(current_velocity)

    def _bounce_sprite(self, sprite: ActionSprite) -> None:
        """Bounce a sprite if it has collided with any boundaries.

        Only checks the boundary that corresponds to the current movement direction.
        For example, when moving right, only check right boundary collisions
        on the rightmost sprites.

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

        # Check if we're working with a GroupTarget
        is_group_target = isinstance(self.target, GroupTarget)

        # Check horizontal bouncing - only check boundary for current direction
        if self.bounce_horizontal and self._horizontal_direction:
            if self._horizontal_direction == MovementDirection.RIGHT and max_x > right:
                # Moving right and hit right boundary
                # Only process if this is a rightmost sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "right"):
                    # For GroupTarget, skip position correction - let callback handle it
                    if not is_group_target:
                        # Bounce off right boundary
                        sprite.center_x -= 2 * (max_x - right)
                        # Reverse horizontal velocity if present
                        self._reverse_sprite_velocity(sprite, "x", -1)

                    self._reverse_movement_actions(sprite, "x")
                    # Update direction to left since we bounced
                    self._horizontal_direction = MovementDirection.LEFT

                    if self._on_bounce:
                        self._on_bounce(sprite, "x")

            elif self._horizontal_direction == MovementDirection.LEFT and min_x < left:
                # Moving left and hit left boundary
                # Only process if this is a leftmost sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "left"):
                    # For GroupTarget, skip position correction - let callback handle it
                    if not is_group_target:
                        # Bounce off left boundary
                        sprite.center_x += 2 * (left - min_x)
                        # Reverse horizontal velocity if present
                        self._reverse_sprite_velocity(sprite, "x", 1)

                    self._reverse_movement_actions(sprite, "x")
                    # Update direction to right since we bounced
                    self._horizontal_direction = MovementDirection.RIGHT

                    if self._on_bounce:
                        self._on_bounce(sprite, "x")

        # Check vertical bouncing - only check boundary for current direction
        if self.bounce_vertical and self._vertical_direction:
            if self._vertical_direction == MovementDirection.UP and max_y > top:
                # Moving up and hit top boundary
                # Only process if this is a topmost sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "top"):
                    # For GroupTarget, skip position correction - let callback handle it
                    if not is_group_target:
                        # Bounce off top boundary
                        sprite.center_y -= 2 * (max_y - top)
                        # Reverse vertical velocity if present
                        self._reverse_sprite_velocity(sprite, "y", -1)

                    self._reverse_movement_actions(sprite, "y")
                    # Update direction to down since we bounced
                    self._vertical_direction = MovementDirection.DOWN

                    if self._on_bounce:
                        self._on_bounce(sprite, "y")

            elif self._vertical_direction == MovementDirection.DOWN and min_y < bottom:
                # Moving down and hit bottom boundary
                # Only process if this is a bottommost sprite (or not a group)
                if not is_group_target or self._is_edge_sprite(sprite, "bottom"):
                    # For GroupTarget, skip position correction - let callback handle it
                    if not is_group_target:
                        # Bounce off bottom boundary
                        sprite.center_y += 2 * (bottom - min_y)
                        # Reverse vertical velocity if present
                        self._reverse_sprite_velocity(sprite, "y", 1)

                    self._reverse_movement_actions(sprite, "y")
                    # Update direction to up since we bounced
                    self._vertical_direction = MovementDirection.UP

                    if self._on_bounce:
                        self._on_bounce(sprite, "y")

        # Store current position for next frame
        sprite._prev_x = sprite.center_x
        sprite._prev_y = sprite.center_y

    def _is_edge_sprite(self, sprite: ActionSprite, edge: str) -> bool:
        """Check if a sprite is on the specified edge of the group.

        Args:
            sprite: The sprite to check
            edge: The edge to check ("left", "right", "top", "bottom")

        Returns:
            True if the sprite is on the specified edge
        """
        if not isinstance(self.target, GroupTarget):
            return True  # Not a GroupTarget, treat as edge sprite

        sprites = list(self.target)
        if not sprites:
            return True

        tolerance = 5  # Pixel tolerance for edge detection

        if edge == "left":
            leftmost_x = min(s.center_x for s in sprites)
            return abs(sprite.center_x - leftmost_x) < tolerance
        elif edge == "right":
            rightmost_x = max(s.center_x for s in sprites)
            return abs(sprite.center_x - rightmost_x) < tolerance
        elif edge == "top":
            topmost_y = max(s.center_y for s in sprites)
            return abs(sprite.center_y - topmost_y) < tolerance
        elif edge == "bottom":
            bottommost_y = min(s.center_y for s in sprites)
            return abs(sprite.center_y - bottommost_y) < tolerance

        return False

    def _reverse_movement_actions(self, sprite: ActionSprite, axis: str) -> None:
        """Reverse movement actions for the specified axis.

        Args:
            sprite: The sprite whose actions to reverse
            axis: 'x' for horizontal, 'y' for vertical
        """
        # Check if we're working with a GroupTarget that has group actions
        if isinstance(self.target, GroupTarget):
            # Reverse all group actions for the entire group
            for group_action in self.target._group_actions:
                if isinstance(group_action, CompositeAction):
                    for action in group_action.actions:
                        self._reverse_action_movement(action, axis)
                else:
                    self._reverse_action_movement(group_action, axis)
        else:
            # Find and reverse any actions that are currently running for individual sprite
            sprite_action = sprite._action
            if sprite_action:
                self._reverse_action_movement(sprite_action, axis)

    def _reverse_action_movement(self, action: Action, axis: str) -> None:
        """Reverse movement for a specific action using type-based dispatch.

        Args:
            action: The action to reverse
            axis: 'x' for horizontal, 'y' for vertical
        """
        if isinstance(action, MovementAction):
            action.reverse_movement(axis)
        elif isinstance(action, CompositeAction):
            self._reverse_composite_action(action, axis)
        elif isinstance(action, EasingAction):
            self._reverse_easing_action(action, axis)

    def _reverse_composite_action(self, action: CompositeAction, axis: str) -> None:
        """Reverse composite actions."""
        if action.current_action:
            self._reverse_action_movement(action.current_action, axis)

        # Also reverse any remaining actions in the composite
        for child_action in action.actions[action.current_index :]:
            self._reverse_action_movement(child_action, axis)

    def _reverse_easing_action(self, action: EasingAction, axis: str) -> None:
        """Reverse easing actions by recursing to their wrapped action."""
        wrapped_action = action.get_wrapped_action()
        if wrapped_action:
            self._reverse_action_movement(wrapped_action, axis)

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
        # Get current speed and acceleration - NO MORE getattr CHECKING
        speed = sprite.physics.speed
        acceleration = sprite.physics.acceleration[0]  # Use x component for forward acceleration

        # Apply acceleration
        if acceleration:
            speed += acceleration * delta_time

            # Apply speed limits - NO MORE getattr CHECKING
            max_forward = sprite.physics.max_forward_speed
            max_reverse = sprite.physics.max_reverse_speed

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
        sprite.physics.speed = speed

    def __repr__(self) -> str:
        return "Driver()"
