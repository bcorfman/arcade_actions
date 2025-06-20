"""
Actions for continuous movement and physics-based movement.
"""

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

    def get_movement_actions(self) -> list["Action"]:
        """Return self as the movement action."""
        return [self]


class CompositeAction(Action):
    """Base class for composite actions with consistent interface."""

    def __init__(self):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.actions: list[Action] = []
        self.current_action: Action | None = None
        self.current_index: int = 0

    def get_movement_actions(self) -> list["Action"]:
        """Get all movement actions from this composite - uses polymorphism instead of isinstance."""
        movement_actions = []
        for action in self.actions:
            # Use polymorphic method instead of isinstance checking
            action_movements = action.get_movement_actions()
            if action_movements:
                movement_actions.extend(action_movements)
            elif action.get_movement_delta() != (0.0, 0.0):
                # This action itself is a movement action
                movement_actions.append(action)
        return movement_actions

    def get_sub_actions(self) -> list["Action"]:
        """Get sub-actions for composite actions."""
        return self.actions

    def extract_movement_direction(self, extractor) -> None:
        """Extract movement direction from composite action."""
        current = self.get_current_action()
        if current:
            current.extract_movement_direction(extractor)
        # Also check all actions in the composite
        for child_action in self.actions:
            child_action.extract_movement_direction(extractor)


class EasingAction(Action):
    """Base class for easing wrapper actions with consistent interface."""

    def __init__(self, other: Action):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.other = other

    def get_wrapped_action(self) -> Action:
        """Get the wrapped action."""
        return self.other

    def get_movement_delta(self) -> tuple[float, float]:
        """Delegate to wrapped action."""
        return self.other.get_movement_delta()

    def reverse_movement(self, axis: str) -> None:
        """Delegate to wrapped action."""
        self.other.reverse_movement(axis)

    def get_movement_actions(self) -> list["Action"]:
        """Delegate to wrapped action."""
        return self.other.get_movement_actions()

    def update_start_position(self, position_delta: tuple[float, float]) -> None:
        """Delegate to wrapped action."""
        self.other.update_start_position(position_delta)

    def extract_movement_direction(self, extractor) -> None:
        """Delegate to wrapped action."""
        self.other.extract_movement_direction(extractor)


class GroupBehaviorAction(Action):
    """Base class for actions that need to detect edge sprites in groups.

    Provides common functionality for determining which sprites are on the edges
    of a group formation, which is useful for both wrapping and bouncing behaviors.
    """

    def __init__(self):
        super().__init__()
        # Guaranteed interface attributes
        self.duration = None  # Continuous action, no fixed duration

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
        # Use polymorphic interface - all targets support this through proper interface design
        # For single sprites, they are always edge sprites
        # For groups, check position relative to other sprites
        if not _is_group_target(self.target):
            return True  # Single sprite is always an edge sprite

        sprites = list(self.target)
        if not sprites:
            return True

        # Check if sprite is still in the target - if not, it's not an edge sprite
        if sprite not in sprites:
            return False

        # If only one sprite left, it's always an edge sprite
        if len(sprites) == 1:
            return True

        tolerance = 5  # Pixel tolerance for edge detection

        # Filter wrapped sprites if requested
        if filter_wrapped and bounds:
            width, height = bounds
            if edge == "left":
                # Filter out sprites that have wrapped to the right side
                sprites = [s for s in sprites if s.center_x < width]
            elif edge == "right":
                # Filter out sprites that have wrapped to the left side
                sprites = [s for s in sprites if s.center_x > 0]
            elif edge == "top":
                # Filter out sprites that have wrapped to the bottom
                sprites = [s for s in sprites if s.center_y > 0]
            elif edge == "bottom":
                # Filter out sprites that have wrapped to the top
                sprites = [s for s in sprites if s.center_y < height]

            if not sprites:
                return True  # All sprites wrapped, treat as edge sprite

        # Additional check - if sprite is no longer in filtered list, it's not an edge sprite
        if sprite not in sprites:
            return False

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


def _is_iterable_target(target) -> bool:
    """Check if target is iterable (list/group) using duck typing."""
    try:
        iter(target)
        return True
    except TypeError:
        return False


def _is_group_target(target) -> bool:
    """Check if target is a group target using duck typing."""
    try:
        # GroupTargets are iterable, have length, AND have _group_actions
        iter(target)
        len(target)
        target._group_actions
        return True
    except (TypeError, AttributeError):
        return False


class WrappedMove(GroupBehaviorAction):
    """Action that wraps sprites around screen boundaries."""

    def __init__(self, bounds_func, wrap_horizontal=True, wrap_vertical=True, on_wrap=None):
        super().__init__()
        self.bounds_func = bounds_func
        self.wrap_horizontal = wrap_horizontal
        self.wrap_vertical = wrap_vertical
        self._on_wrap = on_wrap  # Use _on_wrap to match test expectations

        # Current screen bounds cache
        self._current_bounds = None

        # Guaranteed interface attributes
        self.duration = None  # Continuous action, no fixed duration

        # Initialize tracking sets for recursion prevention - guaranteed interface
        self._processed_wrap_actions = None

    def get_bounds(self):
        """Get current screen boundaries."""
        if callable(self.bounds_func):
            self._current_bounds = self.bounds_func()
        else:  # Assume it's a tuple/list
            self._current_bounds = self.bounds_func
        return self._current_bounds

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

        if _is_iterable_target(self.target):
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

        # Use polymorphic interface design - no runtime checking needed

        # Horizontal wrapping
        if self.wrap_horizontal:
            if max_x < 0:  # Sprite has moved completely off left edge
                # Check edge status BEFORE wrapping - use unified interface
                if self._is_edge_sprite(sprite, "left", True, (width, height)):
                    old_position = sprite.position
                    sprite.center_x = width + bbox_width / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")
            elif min_x > width:  # Sprite has moved completely off right edge
                # Check edge status BEFORE wrapping - use unified interface
                if self._is_edge_sprite(sprite, "right", True, (width, height)):
                    old_position = sprite.position
                    sprite.center_x = -bbox_width / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "x")

        # Vertical wrapping
        if self.wrap_vertical:
            if max_y < 0:  # Sprite has moved completely off bottom edge
                # Check edge status BEFORE wrapping - use unified interface
                if self._is_edge_sprite(sprite, "bottom", True, (width, height)):
                    old_position = sprite.position
                    sprite.center_y = height + bbox_height / 2
                    self._notify_movement_actions_of_wrap(sprite, old_position, sprite.position)
                    if self._on_wrap:
                        self._on_wrap(sprite, "y")
            elif min_y > height:  # Sprite has moved completely off top edge
                # Check edge status BEFORE wrapping - use unified interface
                if self._is_edge_sprite(sprite, "top", True, (width, height)):
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
        # Get the sprite's current action - ActionTarget protocol guarantees _action exists
        if not sprite._action:
            return

        # Calculate the position delta from wrapping
        position_delta = (new_position[0] - old_position[0], new_position[1] - old_position[1])

        # Send message to update movement actions
        self._update_movement_action_positions(sprite._action, position_delta)

    def _update_movement_action_positions(self, action: Action, position_delta: tuple[float, float]) -> None:
        """Recursively update movement action positions after wrapping.

        Args:
            action: The action to update
            position_delta: The position change from wrapping
        """
        # Avoid infinite recursion by tracking processed actions
        # Initialize tracking set on first use - guaranteed interface
        if self._processed_wrap_actions is None:
            self._processed_wrap_actions = set()

        # Skip if we've already processed this action
        action_id = id(action)
        if action_id in self._processed_wrap_actions:
            return

        self._processed_wrap_actions.add(action_id)

        try:
            # Use polymorphic method instead of isinstance/hasattr checks
            action.update_start_position(position_delta)

            # Handle composite actions without recursion issues
            wrapped_action = action.get_wrapped_action()
            if wrapped_action != action and id(wrapped_action) not in self._processed_wrap_actions:
                # This is an easing action - update the wrapped action
                self._update_movement_action_positions(wrapped_action, position_delta)
                return

            # Handle composite actions with movement actions
            movement_actions = action.get_movement_actions()
            if movement_actions:
                for sub_action in movement_actions:
                    if id(sub_action) not in self._processed_wrap_actions:
                        self._update_movement_action_positions(sub_action, position_delta)
                return

            # Handle composite actions with sub-actions
            sub_actions = action.get_sub_actions()
            if sub_actions:
                for sub_action in sub_actions:
                    if id(sub_action) not in self._processed_wrap_actions:
                        self._update_movement_action_positions(sub_action, position_delta)
        finally:
            # Clear the processed actions set when we're done with the top-level call
            if len(self._processed_wrap_actions) == 1:
                self._processed_wrap_actions = None

    def __repr__(self) -> str:
        return f"WrappedMove(wrap_horizontal={self.wrap_horizontal}, wrap_vertical={self.wrap_vertical})"


class BoundedMove(GroupBehaviorAction):
    """Action that creates bouncing movement within boundaries.

    This action detects when sprites hit boundaries and reverses their movement
    actions to create bouncing behavior. It follows the same cooperative pattern
    as WrappedMove, working alongside existing movement actions rather than
    overriding them.

    The bouncing behavior works by:
    - Detecting when sprites hit boundaries
    - Adjusting sprite position to the boundary
    - Reversing movement direction in the affected axis
    - Calling bounce callbacks when bounces occur

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
            get_bounds: Function that returns current screen bounds (left, bottom, right, top).
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

        # Track movement directions for bounce fix
        self._horizontal_direction = 1  # 1 for right, -1 for left
        self._vertical_direction = 1  # 1 for up, -1 for down

        # Track last bounce to prevent rapid bouncing
        self._last_bounce_time = 0.0
        self._bounce_cooldown = 0.2  # Minimum time between bounces
        self._total_time = 0.0

        # Track group composition to prevent bouncing right after sprite removal
        self._last_group_size = 0
        self._group_change_cooldown = 0.5  # Longer cooldown after group composition changes
        self._last_group_change_time = 0.0

        # Initialize tracking sets for recursion prevention - guaranteed interface
        self._processed_bounce_actions = None

    def start(self) -> None:
        """Start the bounded movement action."""
        super().start()

    def update(self, delta_time: float) -> None:
        """Update sprite bouncing behavior."""
        if self._paused:
            return

        # Track total time for bounce cooldown
        self._total_time += delta_time

        if _is_iterable_target(self.target):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        """Update all sprites in a sprite list."""
        # Create a copy of the sprite list to avoid issues with concurrent modification
        # (when sprites are removed during iteration)
        sprites_to_check = list(self.target)

        # Check for group composition changes
        current_group_size = len(sprites_to_check)
        if current_group_size != self._last_group_size:
            # Group composition changed, set both bounce time and group change time
            self._last_bounce_time = self._total_time
            self._last_group_change_time = self._total_time
            self._last_group_size = current_group_size

        for sprite in sprites_to_check:
            # Skip sprites that are no longer in the target list
            if sprite not in self.target:
                continue
            self._update_sprite_bouncing(sprite, delta_time)

    def _update_single_sprite(self, delta_time: float) -> None:
        """Update a single sprite's bouncing behavior."""
        self._update_sprite_bouncing(self.target, delta_time)

    def _update_sprite_bouncing(self, sprite: ActionSprite, delta_time: float) -> None:
        """Update sprite by checking for bounces and adjusting movement actions."""
        # Check for bounces and reverse movement actions when they occur
        self._check_and_handle_bounces(sprite)

    def _sprite_in_target(self, sprite: ActionSprite) -> bool:
        """Check if sprite is still in the target group."""
        if _is_iterable_target(self.target):
            return sprite in self.target
        else:
            return self.target == sprite

    def _should_debug_sprite(self, sprite: ActionSprite) -> bool:
        """Check if sprite debugging is enabled - unified interface."""
        # Use polymorphic interface - sprites can implement debugging through proper protocols
        try:
            return sprite._debug_bounce
        except AttributeError:
            return False  # Default to no debugging

    def _get_legitimate_boundary_hits(
        self, sprite: ActionSprite, horizontal_direction: int, vertical_direction: int
    ) -> list[str]:
        """Check which boundary collisions are legitimate and not caused by sprite removal.

        This prevents rapid bouncing when edge sprites are removed and new edge sprites
        suddenly appear to be at boundaries. Returns a list of all legitimate boundary
        hits to support corner collisions.

        Args:
            sprite: The sprite to check for boundary collisions
            horizontal_direction: Current horizontal movement direction (1=right, -1=left, 0=none)
            vertical_direction: Current vertical movement direction (1=up, -1=down, 0=none)

        Returns:
            List of boundary edges that are legitimately hit ("right", "left", "top", "bottom")
        """
        hit_edges = []

        # For single sprites, always check all boundaries
        if not _is_group_target(self.target):
            bounds = self.get_bounds()
            left, bottom, right, top = bounds

            # Check each boundary independently - only if moving toward that boundary
            if self.bounce_horizontal:
                sprite_right = sprite.center_x + sprite.width / 2
                sprite_left = sprite.center_x - sprite.width / 2

                if sprite_right >= right and horizontal_direction > 0:
                    hit_edges.append("right")
                if sprite_left <= left and horizontal_direction < 0:
                    hit_edges.append("left")

            if self.bounce_vertical:
                sprite_top = sprite.center_y + sprite.height / 2
                sprite_bottom = sprite.center_y - sprite.height / 2

                if sprite_top >= top and vertical_direction > 0:
                    hit_edges.append("top")
                if sprite_bottom <= bottom and vertical_direction < 0:
                    hit_edges.append("bottom")

            return hit_edges

        # For group targets, be more strict about legitimate hits
        bounds = self.get_bounds()
        left, bottom, right, top = bounds

        # Check right boundary - only if sprite is beyond boundary AND moving right
        if self.bounce_horizontal:
            sprite_right = sprite.center_x + sprite.width / 2
            if sprite_right >= right and horizontal_direction > 0:
                hit_edges.append("right")

            # Check left boundary - only if sprite is beyond boundary AND moving left
            sprite_left = sprite.center_x - sprite.width / 2
            if sprite_left <= left and horizontal_direction < 0:
                hit_edges.append("left")

        # Check vertical boundaries - only if sprite is beyond boundary AND moving in that direction
        if self.bounce_vertical:
            sprite_top = sprite.center_y + sprite.height / 2
            if sprite_top >= top and vertical_direction > 0:
                hit_edges.append("top")

            sprite_bottom = sprite.center_y - sprite.height / 2
            if sprite_bottom <= bottom and vertical_direction < 0:
                hit_edges.append("bottom")

        return hit_edges

    def _check_and_handle_bounces(self, sprite: ActionSprite) -> None:
        """Check if sprite hits boundaries and reverse movement actions."""
        # Get boundaries
        bounds = self.get_bounds()
        left, bottom, right, top = bounds

        # Get sprite dimensions and hit box
        hit_box = sprite.hit_box
        min_x = hit_box.left
        max_x = hit_box.right
        min_y = hit_box.bottom
        max_y = hit_box.top
        bbox_width = sprite.width
        bbox_height = sprite.height

        # Check if this is a group target
        is_group_target = _is_group_target(self.target)

        # Determine current movement direction from the sprite's action or group actions
        current_horizontal_direction = 0
        current_vertical_direction = 0

        # First try to get movement direction from sprite's direct action
        if sprite._action:
            movement_actions = sprite._action.get_movement_actions()
            if movement_actions:
                for action in movement_actions:
                    delta = action.get_movement_delta()
                    if delta[0] > 0:
                        current_horizontal_direction = 1
                    elif delta[0] < 0:
                        current_horizontal_direction = -1
                    if delta[1] > 0:
                        current_vertical_direction = 1
                    elif delta[1] < 0:
                        current_vertical_direction = -1
                    # Break after finding the first movement action
                    if current_horizontal_direction != 0 or current_vertical_direction != 0:
                        break

        # If no movement direction from sprite action, try group actions
        # Use polymorphic interface - all group targets guarantee proper interface
        if current_horizontal_direction == 0 and current_vertical_direction == 0 and is_group_target:
                for group_action in self.target._group_actions:
                        movement_actions = group_action.template.get_movement_actions()
                        if movement_actions:
                            for action in movement_actions:
                                delta = action.get_movement_delta()
                                if delta[0] > 0:
                                    current_horizontal_direction = 1
                                elif delta[0] < 0:
                                    current_horizontal_direction = -1
                                if delta[1] > 0:
                                    current_vertical_direction = 1
                                elif delta[1] < 0:
                                    current_vertical_direction = -1
                                # Break after finding the first movement action
                                if current_horizontal_direction != 0 or current_vertical_direction != 0:
                                    break
                        if current_horizontal_direction != 0 or current_vertical_direction != 0:
                            break

        # If no movement direction detected from actions, use stored direction
        # This handles cases where sprites are removed but group should still move
        if current_horizontal_direction == 0:
            current_horizontal_direction = self._horizontal_direction
        if current_vertical_direction == 0:
            current_vertical_direction = self._vertical_direction

        # Detect all boundary conditions first (for corner bouncing)
        will_bounce_horizontal = False
        will_bounce_vertical = False
        bounce_horizontal_direction = 0
        bounce_vertical_direction = 0

        # Get all legitimate boundary hits for this sprite
        # This allows simultaneous detection of multiple edges for corner bouncing
        legitimate_hits = self._get_legitimate_boundary_hits(
            sprite, current_horizontal_direction, current_vertical_direction
        )

        # Process horizontal boundaries
        if self.bounce_horizontal:
            if "right" in legitimate_hits and current_horizontal_direction > 0:  # Hit right boundary while moving right
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "right")
                if is_edge_sprite:
                    will_bounce_horizontal = True
                    bounce_horizontal_direction = -1
                    # Debug output (optional debug capability with protocol)
                    if self._should_debug_sprite(sprite):
                        print(f"DEBUG: Right bounce - max_x={max_x}, right={right}, edge_sprite={is_edge_sprite}")

            if "left" in legitimate_hits and current_horizontal_direction < 0:  # Hit left boundary while moving left
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "left")
                # Additional check for rapid bounce prevention
                # If we just bounced right and are now moving left, don't immediately bounce left
                # unless the sprite is truly at the left boundary AND has been moving for a reasonable time
                legitimate_left_hit = True
                if is_group_target and self._horizontal_direction == -1:
                    # We just bounced from right wall, be much more strict about left wall bouncing
                    # Only bounce if sprite is well past the boundary to prevent rapid bouncing
                    sprite_left_edge = sprite.center_x - sprite.width / 2
                    legitimate_left_hit = sprite_left_edge <= left - 10  # More margin to prevent rapid bounce

                    # Also check if there are still other sprites in the group
                    # If the group only has one sprite left, be less strict
                    if len(list(self.target)) <= 1:
                        legitimate_left_hit = sprite_left_edge <= left + 5

                if is_edge_sprite and legitimate_left_hit:
                    will_bounce_horizontal = True
                    bounce_horizontal_direction = 1
                    # Debug output (optional debug capability with protocol)
                    if self._should_debug_sprite(sprite):
                        print(f"DEBUG: Left bounce - min_x={min_x}, left={left}, edge_sprite={is_edge_sprite}")

        # Process vertical boundaries
        if self.bounce_vertical:
            if "top" in legitimate_hits and current_vertical_direction > 0:  # Hit top boundary while moving up
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "top")
                if is_edge_sprite:
                    will_bounce_vertical = True
                    bounce_vertical_direction = -1

            if "bottom" in legitimate_hits and current_vertical_direction < 0:  # Hit bottom boundary while moving down
                is_edge_sprite = not is_group_target or self._is_edge_sprite(sprite, "bottom")
                if is_edge_sprite:
                    will_bounce_vertical = True
                    bounce_vertical_direction = 1

                    # Check bounce cooldown to prevent rapid bouncing ONLY for group target
        # and ONLY when bouncing in opposite direction soon after last bounce
        if _is_group_target(self.target):
            time_since_last_bounce = self._total_time - self._last_bounce_time
            time_since_group_change = self._total_time - self._last_group_change_time

            # Use longer cooldown if there was a recent group composition change
            effective_cooldown = (
                self._group_change_cooldown
                if time_since_group_change < self._group_change_cooldown
                else self._bounce_cooldown
            )

            if time_since_last_bounce < effective_cooldown:
                # Check if this would be a rapid bounce in opposite direction
                would_be_rapid_bounce = False
                if will_bounce_horizontal:
                    # Check if bouncing in opposite direction to recent bounce
                    if (bounce_horizontal_direction == 1 and self._horizontal_direction == -1) or (
                        bounce_horizontal_direction == -1 and self._horizontal_direction == 1
                    ):
                        would_be_rapid_bounce = True

                if would_be_rapid_bounce:
                    # Too soon since last bounce in opposite direction, skip this bounce
                    return

        # Process bounces simultaneously for corner bouncing
        bounced_axes = []
        if will_bounce_horizontal or will_bounce_vertical:
            old_position = sprite.position

            # Adjust position to boundaries
            if will_bounce_horizontal:
                old_x = sprite.center_x
                if bounce_horizontal_direction == -1:  # Hit right boundary
                    sprite.center_x = right - bbox_width / 2
                else:  # Hit left boundary
                    sprite.center_x = left + bbox_width / 2
                self._horizontal_direction = bounce_horizontal_direction
                bounced_axes.append("x")

            if will_bounce_vertical:
                old_y = sprite.center_y
                if bounce_vertical_direction == -1:  # Hit top boundary
                    sprite.center_y = top - bbox_height / 2
                else:  # Hit bottom boundary
                    sprite.center_y = bottom + bbox_height / 2
                self._vertical_direction = bounce_vertical_direction
                bounced_axes.append("y")

            # Update last bounce time
            self._last_bounce_time = self._total_time

            # Notify movement actions of bounces (handle all axes simultaneously)
            if bounced_axes:
                self._notify_movement_actions_of_bounce(sprite, old_position, sprite.position, bounced_axes)

                # IMPORTANT: Since the movement action has already applied movement this frame
                # in the wrong direction, we need to apply one frame of corrected movement
                # immediately to show the bounce effect
                self._apply_corrected_movement_immediately(sprite, bounced_axes)

            # Call bounce callbacks
            if self._on_bounce and self._sprite_in_target(sprite):
                for axis in bounced_axes:
                    self._on_bounce(sprite, axis)

    def _apply_corrected_movement_immediately(self, sprite: ActionSprite, bounced_axes: list[str]) -> None:
        """Apply corrected movement immediately after bounce to show immediate direction change.

        This compensates for the fact that the movement action already applied movement this frame
        before the bounce was detected. We need to apply movement in the new direction immediately.
        """
        # Find the movement action and apply one step of movement in the new direction
        if sprite._action:
            movement_actions = sprite._action.get_movement_actions()
            if movement_actions:
                for action in movement_actions:
                    # Get the current movement delta (which should now be reversed)
                    delta = action.get_movement_delta()

                    # Apply a small amount of movement in the new direction to show immediate bounce effect
                    # Use a fraction of the normal delta to show the direction change
                    bounce_step = 0.1  # Small step to show direction change
                    if "x" in bounced_axes and delta[0] != 0:
                        sprite.center_x += delta[0] * bounce_step
                    if "y" in bounced_axes and delta[1] != 0:
                        sprite.center_y += delta[1] * bounce_step

                    # Reset the start position to current sprite position for future movement
                    action.start_position = sprite.position

    def _notify_movement_actions_of_bounce(
        self,
        sprite: ActionSprite,
        old_position: tuple[float, float],
        new_position: tuple[float, float],
        axes: list[str],
    ) -> None:
        """Notify movement actions that a bounce occurred and they need to reverse direction and update positions.

        For GroupActions, this reverses the entire group's movement template.
        For individual sprite actions, this reverses just that sprite's action.

        Args:
            sprite: The sprite that bounced
            old_position: The position before bouncing
            new_position: The position after bouncing
            axes: The axes that bounced (["x"], ["y"], or ["x", "y"] for simultaneous corner bounce)
        """
        # Calculate the position delta from bouncing
        position_delta = (new_position[0] - old_position[0], new_position[1] - old_position[1])

        # For GroupActions, reverse the entire group's movement
        # Use polymorphic interface with proper fallback logic
        if _is_group_target(self.target):
            # _is_group_target already confirmed _group_actions exists
                for group_action in self.target._group_actions:
                # All group actions guarantee template interface
                self._update_movement_action_bounce(group_action.template, position_delta, axes)
                # All group actions guarantee actions interface
                            for action in group_action.actions:
                    self._update_movement_action_bounce(action, position_delta, axes)

        # Also handle individual sprite actions (for non-group or mixed scenarios)
        if sprite._action:
            # Send message to update movement actions and reverse direction
            self._update_movement_action_bounce(sprite._action, position_delta, axes)

    def _update_movement_action_bounce(
        self, action: Action, position_delta: tuple[float, float], axes: list[str]
    ) -> None:
        """Recursively update movement action positions after bouncing and reverse direction.

        Args:
            action: The action to update
            position_delta: The position change from bouncing
            axes: The axes that bounced (["x"], ["y"], or ["x", "y"] for simultaneous corner bounce)
        """
        # Avoid infinite recursion by tracking processed actions
        if self._processed_bounce_actions is None:
            self._processed_bounce_actions = set()

        # Skip if we've already processed this action
        action_id = id(action)
        if action_id in self._processed_bounce_actions:
            return

        self._processed_bounce_actions.add(action_id)

        try:
            # Update position reference first (like WrappedMove does)
            action.update_start_position(position_delta)

            # Then reverse movement direction for all axes simultaneously
            # For corner bounces (both x and y), this ensures both directions are reversed at once
            for axis in axes:
            action.reverse_movement(axis)

            # Handle wrapped actions (like Easing)
            wrapped_action = action.get_wrapped_action()
            if wrapped_action != action and id(wrapped_action) not in self._processed_bounce_actions:
                self._update_movement_action_bounce(wrapped_action, position_delta, axes)
                return

            # Handle composite actions with movement actions
            movement_actions = action.get_movement_actions()
            if movement_actions:
                for sub_action in movement_actions:
                    if id(sub_action) not in self._processed_bounce_actions:
                        self._update_movement_action_bounce(sub_action, position_delta, axes)
                return

            # Handle composite actions with sub-actions
            sub_actions = action.get_sub_actions()
            if sub_actions:
                for sub_action in sub_actions:
                    if id(sub_action) not in self._processed_bounce_actions:
                        self._update_movement_action_bounce(sub_action, position_delta, axes)
        finally:
            # Clear the processed actions set when we're done with the top-level call
            if self._processed_bounce_actions and len(self._processed_bounce_actions) == 1:
                self._processed_bounce_actions = None

    def __repr__(self) -> str:
        return f"BoundedMove(bounce_horizontal={self.bounce_horizontal}, bounce_vertical={self.bounce_vertical})"
