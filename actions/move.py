"""
Actions for continuous movement and physics-based movement.
"""

import math
from collections.abc import Callable
from enum import Enum, auto

from actions.base import Action, ActionSprite


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

    def extract_movement_direction(self, collector):
        """Report this action's movement delta to *collector*."""
        collector(self.delta)


class CompositeAction(Action):
    """Base class for composite actions with consistent interface."""

    def __init__(self):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.actions: list[Action] = []
        self.current_action: Action | None = None
        self.current_index: int = 0

    def get_movement_actions(self) -> list[MovementAction]:
        """Return child actions that report a non-zero movement delta."""
        collected: list[MovementAction] = []
        for child in self.actions:
            # Use capability methods instead of fragile runtime type checks.
            if child.get_movement_delta() != (0.0, 0.0):
                # Treat as movement-capable; cast for typing clarity.
                collected.append(child)  # type: ignore[arg-type]
            # Recurse into composites, relying on structural typing.
            collected.extend(child.get_movement_actions())
        return collected

    def reverse_movement(self, axis: str) -> None:
        if self.current_action:
            self.current_action.reverse_movement(axis)
        for child in self.actions[self.current_index :]:
            child.reverse_movement(axis)

    def extract_movement_direction(self, collector):
        if self.current_action:
            self.current_action.extract_movement_direction(collector)
        for child in self.actions:
            child.extract_movement_direction(collector)

    def adjust_for_position_delta(self, position_delta: tuple[float, float]) -> None:
        for child in self.actions:
            child.adjust_for_position_delta(position_delta)


class EasingAction(Action):
    """Base class for easing wrapper actions with consistent interface."""

    def __init__(self, other: Action):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.other = other

    def get_wrapped_action(self) -> Action:
        """Get the wrapped action."""
        return self.other

    def reverse_movement(self, axis: str) -> None:
        self.other.reverse_movement(axis)

    def extract_movement_direction(self, collector):
        self.other.extract_movement_direction(collector)


class _Move(Action):
    """Base class for continuous movement actions.

    This action updates sprite position based on velocity and acceleration.
    It can work with both regular sprites and physics-enabled sprites.
    """

    def start(self) -> None:
        """Start the movement action."""
        # No initialization needed, just call parent's start
        super().start()

    def _iter_sprites(self):
        """Yield all sprites controlled by this action (single or list)."""
        try:
            # If target is iterable (SpriteList or list), yield from it.
            for sprite in self.target:  # type: ignore[not-an-iterable]
                yield sprite
        except TypeError:
            # Not iterable – treat as single sprite.
            yield self.target

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        for sprite in self._iter_sprites():
            self._move_single_sprite_for(sprite, delta_time)

    def _move_single_sprite_for(self, sprite: ActionSprite, delta_time: float) -> None:
        # Duplicate body of _move_single_sprite but parameterised
        x, y = sprite.position
        dx, dy = sprite.change_x, sprite.change_y

        ax, ay = sprite.physics.acceleration
        dx += ax * delta_time
        dy += ay * delta_time

        dy += sprite.physics.gravity * delta_time

        sprite.change_x = dx
        sprite.change_y = dy

        sprite.position = (x + dx * delta_time, y + dy * delta_time)

        sprite.angle += sprite.change_angle * delta_time

    # Keep old _move_single_sprite for backward compatibility but delegate
    def _move_single_sprite(self, delta_time: float) -> None:
        self._move_single_sprite_for(self.target, delta_time)  # type: ignore[arg-type]

    # _move_sprite_list no longer needed, but retain for compat
    def _move_sprite_list(self, delta_time: float) -> None:
        for sprite in self._iter_sprites():
            self._move_single_sprite_for(sprite, delta_time)


class GroupBehaviorAction(Action):
    """Base class for actions that need to detect edge sprites in groups.

    Provides common functionality for determining which sprites are on the edges
    of a group formation, which is useful for both wrapping and bouncing behaviors.
    """

    def _iter_target(self):
        """Yield sprites from the *target* whether single sprite or collection."""
        try:
            for sprite in self.target:  # type: ignore[not-an-iterable]
                yield sprite
        except TypeError:
            yield self.target

    def _is_edge_sprite(
        self, sprite: ActionSprite, edge: str, filter_wrapped: bool = False, bounds: tuple[float, float] = None
    ) -> bool:
        """Check if a sprite is on the specified edge of the group.

        Args:
            sprite: The sprite to check
            edge: The edge to check ("left", "right", "top", "bottom")
            filter_wrapped: Whether to filter out wrapped sprites from edge calculations
            bounds: Screen bounds (width, height) for filtering wrapped sprites

        Returns:
            True if the sprite is on the specified edge
        """
        sprites = list(self._iter_target())
        if len(sprites) <= 1:
            return True

        tolerance = 5  # Pixel tolerance for edge detection

        # Filter wrapped sprites if requested
        if filter_wrapped and bounds:
            width, height = bounds
            if edge == "left":
                sprites = [s for s in sprites if s.center_x < width]
            elif edge == "right":
                sprites = [s for s in sprites if s.center_x > 0]
            elif edge == "top":
                sprites = [s for s in sprites if s.center_y > 0]
            elif edge == "bottom":
                sprites = [s for s in sprites if s.center_y < height]

            if not sprites:
                return True  # All sprites wrapped, treat as edge sprite

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


class WrappedMove(GroupBehaviorAction):
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

        for sprite in self._iter_target():
            self._wrap_sprite(sprite)

    def _wrap_sprite(self, sprite: ActionSprite) -> None:
        """Wrap a sprite around screen boundaries.

        Only wraps sprites that have completely moved off screen.

        Args:
            sprite: The sprite to wrap.
        """
        # Get screen dimensions from the bounds function
        width, height = self.get_bounds()

        # Get sprite's hit box and calculate bounding box
        hit_box = sprite.hit_box
        min_x = hit_box.left
        max_x = hit_box.right
        min_y = hit_box.bottom
        max_y = hit_box.top
        bbox_width = sprite.width
        bbox_height = sprite.height

        # Check if we're working with a group (SpriteGroup / SpriteList wrapper with shared actions)
        try:
            _ = self.target._group_actions  # type: ignore[attr-defined]
            is_group_target = True
        except AttributeError:
            is_group_target = False

        # Horizontal wrapping
        if self.wrap_horizontal:
            if max_x < 0:  # Sprite has moved completely off left edge
                # Check edge status BEFORE wrapping
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "left", True, (width, height))
                if is_edge_sprite:
                    old_position = sprite.position
                    sprite.center_x = width + bbox_width / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")
            elif min_x > width:  # Sprite has moved completely off right edge
                # Check edge status BEFORE wrapping
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "right", True, (width, height))
                if is_edge_sprite:
                    old_position = sprite.position
                    sprite.center_x = -bbox_width / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")

        # Vertical wrapping
        if self.wrap_vertical:
            if max_y < 0:  # Sprite has moved completely off bottom edge
                # Check edge status BEFORE wrapping
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "bottom", True, (width, height))
                if is_edge_sprite:
                    old_position = sprite.position
                    sprite.center_y = height + bbox_height / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "y")
            elif min_y > height:  # Sprite has moved completely off top edge
                # Check edge status BEFORE wrapping
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "top", True, (width, height))
                if is_edge_sprite:
                    old_position = sprite.position
                    sprite.center_y = -bbox_height / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "y")

    def _notify_movement_actions_of_wrap(
        self, sprite: ActionSprite, old_position: tuple[float, float], new_position: tuple[float, float]
    ) -> None:
        """Notify movement actions that a wrap occurred and they need to update their reference positions.

        This method sends a message to movement actions to update their start_position
        so they continue from the new wrapped position instead of the original position.

        Args:
            sprite: The sprite that was wrapped
            old_position: The position before wrapping
            new_position: The position after wrapping
        """
        # Get the sprite's current action (ActionSprite guarantees _action attribute)
        if sprite._action is None:
            return

        # Calculate the position delta from wrapping
        position_delta = (new_position[0] - old_position[0], new_position[1] - old_position[1])

        # Send message to update movement actions
        self._update_movement_action_positions(sprite._action, position_delta)

    def _update_movement_action_positions(self, action: Action, position_delta: tuple[float, float]) -> None:
        """Delegate to the polymorphic hook on *action*.

        Composite and group actions will propagate the adjustment to their
        children automatically; movement actions override the hook to shift
        cached positions.
        """
        action.adjust_for_position_delta(position_delta)

    def __repr__(self) -> str:
        return f"WrappedMove(wrap_horizontal={self.wrap_horizontal}, wrap_vertical={self.wrap_vertical})"


class BoundedMove(GroupBehaviorAction):
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
        self._is_group_target: bool = False
        self._group_actions_ref: list[Action] | None = None

    def start(self) -> None:
        """Start the bounded movement action."""
        super().start()
        # Initialize previous position tracking for all target sprites
        for sprite in self._iter_target():
            sprite._prev_x = sprite.center_x
            sprite._prev_y = sprite.center_y

        # Track initial group size to detect removals/insertions
        try:
            self._last_group_size = len(self.target)  # type: ignore[arg-type]
        except TypeError:
            self._last_group_size = 1

        # Track movement direction to determine which boundary to check
        self._horizontal_direction: MovementDirection | None = None
        self._vertical_direction: MovementDirection | None = None

        # Detect if the target provides shared group actions once; avoids per-frame EAFP cost
        try:
            self._group_actions_ref = self.target._group_actions  # type: ignore[attr-defined]
            self._is_group_target = True
        except AttributeError:
            self._group_actions_ref = None
            self._is_group_target = False

    def update(self, delta_time: float) -> None:
        """Update sprite positions with boundary bouncing."""
        if self._paused:
            return

        # Update movement direction based on current movement
        self._update_movement_direction()

        for sprite in self._iter_target():
            self._bounce_sprite(sprite)

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

        # Check if we're working with a group (SpriteGroup / SpriteList wrapper with shared actions)
        is_group_target = self._is_group_target

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

    def _reverse_movement_actions(self, sprite: ActionSprite, axis: str) -> None:
        """Reverse movement actions for the specified axis using polymorphic calls."""
        group_actions = self._group_actions_ref
        if group_actions is not None:
            for g_action in group_actions:
                g_action.reverse_movement(axis)
        else:
            try:
                act = sprite._action  # type: ignore[attr-defined]
            except AttributeError:
                act = None
            if act:
                act.reverse_movement(axis)

    def __repr__(self) -> str:
        return f"BoundedMove(bounce_horizontal={self.bounce_horizontal}, bounce_vertical={self.bounce_vertical})"

    # ------------------------------------------------------------------
    # Direction detection helpers (no runtime type checks)
    # ------------------------------------------------------------------

    def _update_movement_direction(self) -> None:
        representative_sprite = self._get_representative_sprite()
        if representative_sprite is None:
            return

        # Reset cached direction if group size changed.
        try:
            current_size = len(self.target)  # type: ignore[arg-type]
        except TypeError:
            current_size = 1

        previous_size = self._last_group_size  # Attribute guaranteed by start()
        if current_size != previous_size:
            self._horizontal_direction = None
            self._vertical_direction = None
            self._last_group_size = current_size

        # Determine direction from sprite velocities
        self._set_direction_from_velocity(representative_sprite)

        # Fallback to active actions if still unknown
        if self._horizontal_direction is None or self._vertical_direction is None:
            self._infer_direction_from_actions(representative_sprite)

    def _get_representative_sprite(self) -> ActionSprite | None:
        try:
            iterator = iter(self.target)  # type: ignore[not-an-iterable]
            return next(iterator, None)
        except TypeError:
            return self.target

    def _set_direction_from_velocity(self, sprite: ActionSprite) -> None:
        # Iterate over all sprites to sample velocity info
        for s in self._iter_target():
            cx, cy = s.change_x, s.change_y
            if self._horizontal_direction is None and cx != 0:
                self._horizontal_direction = MovementDirection.RIGHT if cx > 0 else MovementDirection.LEFT
            if self._vertical_direction is None and cy != 0:
                self._vertical_direction = MovementDirection.UP if cy > 0 else MovementDirection.DOWN
            if self._horizontal_direction and self._vertical_direction:
                break

        # Fallback to representative sprite if still unknown
        if self._horizontal_direction is None and sprite.change_x != 0:
            self._horizontal_direction = MovementDirection.RIGHT if sprite.change_x > 0 else MovementDirection.LEFT
        if self._vertical_direction is None and sprite.change_y != 0:
            self._vertical_direction = MovementDirection.UP if sprite.change_y > 0 else MovementDirection.DOWN

    def _infer_direction_from_actions(self, sprite: ActionSprite) -> None:
        def collect(delta: tuple[float, float]):
            if self._horizontal_direction is None and delta[0] != 0:
                self._horizontal_direction = MovementDirection.RIGHT if delta[0] > 0 else MovementDirection.LEFT
            if self._vertical_direction is None and delta[1] != 0:
                self._vertical_direction = MovementDirection.UP if delta[1] > 0 else MovementDirection.DOWN

        # Check group-level actions if present
        group_actions = self._group_actions_ref
        if group_actions:
            for g_action in group_actions:
                g_action.extract_movement_direction(collect)
                if self._horizontal_direction and self._vertical_direction:
                    return

        # Iterate sprites and their actions
        for s in self._iter_target():
            try:
                act = s._action  # type: ignore[attr-defined]
            except AttributeError:
                act = None
            if act:
                act.extract_movement_direction(collect)
                if self._horizontal_direction and self._vertical_direction:
                    return

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


class Driver(Action):
    """Drive sprites like cars, moving in the direction they're facing.

    This action can work with both individual sprites and sprite lists.
    Each sprite will move independently based on its own speed, acceleration,
    and facing direction.
    """

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        try:
            iterator = iter(self.target)  # type: ignore[not-an-iterable]
        except TypeError:
            self._drive_sprite(self.target, delta_time)
        else:
            for sprite in iterator:
                self._drive_sprite(sprite, delta_time)

    def _drive_sprite(self, sprite, delta_time: float) -> None:
        """Drive a single sprite based on its speed and direction."""
        # Get current speed and acceleration
        speed = sprite.physics.speed
        acceleration = sprite.physics.acceleration[0]  # Use x component for forward acceleration

        # Apply acceleration
        if acceleration:
            speed += acceleration * delta_time

        # Apply speed limits
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
