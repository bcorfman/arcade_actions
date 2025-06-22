"""
Actions for continuous movement and boundary behaviors.
"""

from collections.abc import Callable
from enum import Enum, auto
from typing import NamedTuple

from actions.base import Action, ActionSprite


class MovementDirection(Enum):
    """Enumeration for movement directions."""

    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


class BoundsInfo(NamedTuple):
    """Information about boundary collision or wrapping."""

    collision_axis: str  # "x" or "y"
    collision_edge: str  # "left", "right", "top", "bottom"
    original_position: tuple[float, float]
    corrected_position: tuple[float, float]  # For bouncing
    wrap_position: tuple[float, float]  # For wrapping
    fully_outside: bool  # True if sprite is completely outside bounds


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

    def clone(self) -> "MovementAction":
        """Create a copy of this MovementAction."""
        if self.__class__ is MovementAction:
            cloned = MovementAction()
            cloned.delta = self.delta
            cloned.total_change = self.total_change
            cloned.end_position = self.end_position
            return cloned
        else:
            # Subclasses should implement their own cloning
            raise NotImplementedError(f"Action subclass {self.__class__.__name__} must override clone() method.")


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

    def clone(self) -> "CompositeAction":
        """Create a copy of this CompositeAction."""
        if self.__class__ is CompositeAction:
            cloned = CompositeAction()
            cloned.actions = [action.clone() for action in self.actions]
            cloned.current_action = None
            cloned.current_index = 0
            return cloned
        else:
            # Subclasses should implement their own cloning
            raise NotImplementedError(f"Action subclass {self.__class__.__name__} must override clone() method.")


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

    def clone(self) -> "EasingAction":
        """Create a copy of this EasingAction."""
        if self.__class__ is EasingAction:
            return EasingAction(self.other.clone())
        else:
            # Subclasses should implement their own cloning
            raise NotImplementedError(f"Action subclass {self.__class__.__name__} must override clone() method.")


class BoundaryBehavior:
    """Base strategy class for handling sprite boundary interactions."""

    def __init__(
        self,
        horizontal: bool = True,
        vertical: bool = True,
        callback: Callable[[ActionSprite, str], None] | None = None,
    ):
        """Initialize boundary behavior.

        Args:
            horizontal: Whether to handle horizontal boundary interactions
            vertical: Whether to handle vertical boundary interactions
            callback: Optional callback function called when boundary interaction occurs.
                Signature: callback(sprite: ActionSprite, axis: str) -> None
        """
        self.horizontal = horizontal
        self.vertical = vertical
        self.callback = callback

    def handle_boundary_collision(
        self, sprite: ActionSprite, bounds_info: BoundsInfo, is_edge_sprite: bool, is_group_target: bool
    ) -> bool:
        """Handle boundary collision for a sprite.

        Args:
            sprite: The sprite that hit the boundary
            bounds_info: Information about the boundary collision
            is_edge_sprite: True if this sprite is on the edge of a group formation
            is_group_target: True if this action is applied to a group target

        Returns:
            True if the boundary interaction was handled, False otherwise
        """
        raise NotImplementedError("Subclasses must implement handle_boundary_collision()")

    def clone(self) -> "BoundaryBehavior":
        """Create a copy of this boundary behavior."""
        raise NotImplementedError("Subclasses must implement clone()")


class BounceBehavior(BoundaryBehavior):
    """Boundary behavior that bounces sprites off boundaries by reversing movement."""

    def handle_boundary_collision(
        self, sprite: ActionSprite, bounds_info: BoundsInfo, is_edge_sprite: bool, is_group_target: bool
    ) -> bool:
        """Handle boundary collision by bouncing the sprite."""
        axis = bounds_info.collision_axis

        # Skip if this axis is disabled
        if (axis == "x" and not self.horizontal) or (axis == "y" and not self.vertical):
            return False

        # Only process edge sprites for group targets
        if is_group_target and not is_edge_sprite:
            return False

        # For individual sprites, apply position correction and velocity reversal
        if not is_group_target:
            # Apply position correction
            sprite.center_x, sprite.center_y = bounds_info.corrected_position

            # Reverse velocity if present
            if axis == "x":
                if sprite.change_x != 0:
                    sprite.change_x = -sprite.change_x
            else:  # axis == "y"
                if sprite.change_y != 0:
                    sprite.change_y = -sprite.change_y

        # Callback is called for both individual and group targets
        if self.callback:
            self.callback(sprite, axis)

        return True

    def clone(self) -> "BounceBehavior":
        """Create a copy of this bounce behavior."""
        return BounceBehavior(horizontal=self.horizontal, vertical=self.vertical, callback=self.callback)


class WrapBehavior(BoundaryBehavior):
    """Boundary behavior that wraps sprites to the opposite side when they leave boundaries."""

    def handle_boundary_collision(
        self, sprite: ActionSprite, bounds_info: BoundsInfo, is_edge_sprite: bool, is_group_target: bool
    ) -> bool:
        """Handle boundary collision by wrapping the sprite."""
        axis = bounds_info.collision_axis

        # Skip if this axis is disabled
        if (axis == "x" and not self.horizontal) or (axis == "y" and not self.vertical):
            return False

        # Only wrap sprites that are fully outside bounds
        if not bounds_info.fully_outside:
            return False

        # Only process edge sprites for group targets
        if is_group_target and not is_edge_sprite:
            return False

        # Apply wrapping
        old_position = sprite.position
        sprite.center_x, sprite.center_y = bounds_info.wrap_position

        # Callback is called for both individual and group targets
        if self.callback:
            self.callback(sprite, axis)

        return True

    def clone(self) -> "WrapBehavior":
        """Create a copy of this wrap behavior."""
        return WrapBehavior(horizontal=self.horizontal, vertical=self.vertical, callback=self.callback)


class BoundaryAction(Action):
    """Unified action that applies boundary behavior using strategy pattern.

    This action replaces both BoundedMove and WrappedMove, using a strategy pattern
    to determine how sprites interact with boundaries. It acts as the outermost wrapper
    that contains and controls movement actions, checking for boundary violations after
    each movement update and correcting them as needed.
    """

    def __init__(self, get_bounds: Callable, behavior: BoundaryBehavior, movement_action: Action | None = None):
        """Initialize the boundary action.

        Args:
            get_bounds: Function that returns current bounds. For bouncing, should return
                (left, bottom, right, top). For wrapping, should return (width, height).
            behavior: The boundary behavior strategy to use
            movement_action: Optional movement action to wrap. If provided, this BoundaryAction
                will control the movement action and check for boundary violations after each update.
        """
        super().__init__()
        self.get_bounds = get_bounds
        self.behavior = behavior
        self.movement_action = movement_action

        # Direction tracking for optimization
        self._horizontal_direction: MovementDirection | None = None
        self._vertical_direction: MovementDirection | None = None
        self._last_group_size: int = 0

        # Group target detection
        self._is_group_target: bool = False
        self._group_actions_ref: list[Action] | None = None

    def start(self) -> None:
        """Start the boundary action and any contained movement action."""
        super().start()

        # Start the contained movement action if we have one
        if self.movement_action:
            self.movement_action.target = self.target
            self.movement_action.start()

        # Initialize position tracking for all target sprites
        for sprite in self._iter_target():
            sprite._prev_x = sprite.center_x
            sprite._prev_y = sprite.center_y

        # Track initial group size to detect changes
        try:
            self._last_group_size = len(self.target)  # type: ignore[arg-type]
        except TypeError:
            self._last_group_size = 1

        # Detect if the target provides shared group actions
        try:
            self._group_actions_ref = self.target._group_actions  # type: ignore[attr-defined]
            self._is_group_target = True
        except AttributeError:
            self._group_actions_ref = None
            self._is_group_target = False

    def update(self, delta_time: float) -> None:
        """Update the contained movement action first, then check and correct boundary violations."""
        if self._paused:
            return

        # First, update the contained movement action (if any)
        if self.movement_action and not self.movement_action.done:
            self.movement_action.update(delta_time)

        # Update movement direction for optimization
        self._update_movement_direction()

        # Process each sprite for boundary violations
        for sprite in self._iter_target():
            # Handle multiple collisions per frame (needed for corners)
            max_collisions_per_frame = 2  # Prevent infinite loops
            collisions_handled = 0

            while collisions_handled < max_collisions_per_frame:
                # Check for boundary collisions this iteration
                horizontal_bounds = self._get_horizontal_bounds_info(sprite)
                vertical_bounds = self._get_vertical_bounds_info(sprite)

                # If no collisions detected, we're done
                if not horizontal_bounds and not vertical_bounds:
                    break

                collision_handled = False

                # For corner cases (both collisions present), handle them simultaneously
                if horizontal_bounds and vertical_bounds:
                    # For bouncing, apply both corrections simultaneously to avoid conflicts
                    if isinstance(self.behavior, BounceBehavior):
                        h_edge = self._is_edge_sprite(sprite, horizontal_bounds.collision_edge)
                        v_edge = self._is_edge_sprite(sprite, vertical_bounds.collision_edge)

                        # Apply both position corrections at once
                        corrected_x = horizontal_bounds.corrected_position[0]
                        corrected_y = vertical_bounds.corrected_position[1]

                        # Always apply position corrections (whether individual or group)
                        sprite.center_x = corrected_x
                        sprite.center_y = corrected_y

                        # Reverse velocities for both axes
                        if sprite.change_x != 0:
                            sprite.change_x = -sprite.change_x
                        if sprite.change_y != 0:
                            sprite.change_y = -sprite.change_y

                        # Call callbacks for both collisions
                        if self.behavior.callback:
                            self.behavior.callback(sprite, "x")
                            self.behavior.callback(sprite, "y")

                        # Update direction tracking
                        self._reverse_direction("x")
                        self._reverse_direction("y")

                        # Reverse the contained movement action
                        if self.movement_action:
                            self.movement_action.reverse_movement("x")  # type: ignore[attr-defined]
                            self.movement_action.reverse_movement("y")  # type: ignore[attr-defined]

                        collision_handled = True

                    else:
                        # For wrapping, handle collisions separately as before
                        h_edge = self._is_edge_sprite(sprite, horizontal_bounds.collision_edge)
                        v_edge = self._is_edge_sprite(sprite, vertical_bounds.collision_edge)

                        h_handled = self.behavior.handle_boundary_collision(
                            sprite, horizontal_bounds, h_edge, self._is_group_target
                        )
                        v_handled = self.behavior.handle_boundary_collision(
                            sprite, vertical_bounds, v_edge, self._is_group_target
                        )

                        if h_handled or v_handled:
                            collision_handled = True

                            if h_handled:
                                position_delta = (
                                    horizontal_bounds.wrap_position[0] - horizontal_bounds.original_position[0],
                                    horizontal_bounds.wrap_position[1] - horizontal_bounds.original_position[1],
                                )
                                # Update the contained movement action
                                if self.movement_action:
                                    self.movement_action.reverse_movement("x")  # type: ignore[attr-defined]
                                    self.movement_action.adjust_for_position_delta(position_delta)  # type: ignore[attr-defined]
                            if v_handled:
                                position_delta = (
                                    vertical_bounds.wrap_position[0] - vertical_bounds.original_position[0],
                                    vertical_bounds.wrap_position[1] - vertical_bounds.original_position[1],
                                )
                                # Update the contained movement action
                                if self.movement_action:
                                    self.movement_action.reverse_movement("y")  # type: ignore[attr-defined]
                                    self.movement_action.adjust_for_position_delta(position_delta)  # type: ignore[attr-defined]

                else:
                    # Handle single collision (horizontal or vertical)
                    bounds_info = horizontal_bounds or vertical_bounds
                    if bounds_info:
                        is_edge_sprite = self._is_edge_sprite(sprite, bounds_info.collision_edge)
                        handled = self.behavior.handle_boundary_collision(
                            sprite, bounds_info, is_edge_sprite, self._is_group_target
                        )

                        if handled:
                            collision_handled = True

                            # Handle wrapping behavior
                            if isinstance(self.behavior, WrapBehavior):
                                position_delta = (
                                    bounds_info.wrap_position[0] - bounds_info.original_position[0],
                                    bounds_info.wrap_position[1] - bounds_info.original_position[1],
                                )
                                # Update the contained movement action
                                if self.movement_action:
                                    self.movement_action.reverse_movement(bounds_info.collision_axis)  # type: ignore[attr-defined]
                                    self.movement_action.adjust_for_position_delta(position_delta)  # type: ignore[attr-defined]

                            # Update direction tracking for bouncing
                            if isinstance(self.behavior, BounceBehavior):
                                self._reverse_direction(bounds_info.collision_axis)
                                # Reverse the contained movement action
                                if self.movement_action:
                                    self.movement_action.reverse_movement(bounds_info.collision_axis)  # type: ignore[attr-defined]

                # If no collision was handled this iteration, we're done with this sprite
                if not collision_handled:
                    break

                collisions_handled += 1

            # Store current position for next frame
            sprite._prev_x = sprite.center_x
            sprite._prev_y = sprite.center_y

        # Check if we're done based on the contained movement action
        if self.movement_action and self.movement_action.done:
            self.done = True

    def stop(self) -> None:
        """Stop the boundary action and any contained movement action."""
        if self.movement_action:
            self.movement_action.stop()
        super().stop()

    def pause(self) -> None:
        """Pause the boundary action and any contained movement action."""
        if self.movement_action:
            self.movement_action.pause()
        super().pause()

    def resume(self) -> None:
        """Resume the boundary action and any contained movement action."""
        if self.movement_action:
            self.movement_action.resume()
        super().resume()

    def clone(self) -> "BoundaryAction":
        """Create a copy of this boundary action."""
        movement_clone = self.movement_action.clone() if self.movement_action else None
        return BoundaryAction(self.get_bounds, self.behavior.clone(), movement_clone)

    def __repr__(self) -> str:
        return f"BoundaryAction(behavior={self.behavior.__class__.__name__})"

    def _iter_target(self):
        """Yield sprites from the target whether single sprite or collection."""
        try:
            for sprite in self.target:  # type: ignore[not-an-iterable]
                yield sprite
        except TypeError:
            yield self.target

    def _get_horizontal_bounds_info(self, sprite: ActionSprite) -> BoundsInfo | None:
        """Get horizontal boundary collision information for a sprite."""
        if not self.behavior.horizontal:
            return None

        bounds = self.get_bounds()

        # Handle different bounds formats
        if len(bounds) == 4:
            # Bounce format: (left, bottom, right, top)
            left, bottom, right, top = bounds
            width = right - left
        elif len(bounds) == 2:
            # Wrap format: (width, height)
            width, height = bounds
            left, right = 0, width
        else:
            return None

        # Get sprite bounding box
        hit_box = sprite.hit_box
        min_x, max_x = hit_box.left, hit_box.right
        bbox_width = sprite.width

        # Check right boundary collision
        if max_x > right:
            # Only check if moving right OR if direction is unknown
            if self._horizontal_direction == MovementDirection.RIGHT or self._horizontal_direction is None:
                return BoundsInfo(
                    collision_axis="x",
                    collision_edge="right",
                    original_position=sprite.position,
                    corrected_position=(sprite.center_x - 2 * (max_x - right), sprite.center_y),
                    wrap_position=(-bbox_width / 2, sprite.center_y),
                    fully_outside=min_x > right,
                )

        # Check left boundary collision
        elif min_x < left:
            # Only check if moving left OR if direction is unknown
            if self._horizontal_direction == MovementDirection.LEFT or self._horizontal_direction is None:
                return BoundsInfo(
                    collision_axis="x",
                    collision_edge="left",
                    original_position=sprite.position,
                    corrected_position=(sprite.center_x + 2 * (left - min_x), sprite.center_y),
                    wrap_position=(width + bbox_width / 2, sprite.center_y),
                    fully_outside=max_x < left,
                )

        return None

    def _get_vertical_bounds_info(self, sprite: ActionSprite) -> BoundsInfo | None:
        """Get vertical boundary collision information for a sprite."""
        if not self.behavior.vertical:
            return None

        bounds = self.get_bounds()

        # Handle different bounds formats
        if len(bounds) == 4:
            # Bounce format: (left, bottom, right, top)
            left, bottom, right, top = bounds
            height = top - bottom
        elif len(bounds) == 2:
            # Wrap format: (width, height)
            width, height = bounds
            bottom, top = 0, height
        else:
            return None

        # Get sprite bounding box
        hit_box = sprite.hit_box
        min_y, max_y = hit_box.bottom, hit_box.top
        bbox_height = sprite.height

        # Check top boundary collision
        if max_y > top:
            # Only check if moving up OR if direction is unknown
            if self._vertical_direction == MovementDirection.UP or self._vertical_direction is None:
                return BoundsInfo(
                    collision_axis="y",
                    collision_edge="top",
                    original_position=sprite.position,
                    corrected_position=(sprite.center_x, sprite.center_y - 2 * (max_y - top)),
                    wrap_position=(sprite.center_x, -bbox_height / 2),
                    fully_outside=min_y > top,
                )

        # Check bottom boundary collision
        elif min_y < bottom:
            # Only check if moving down OR if direction is unknown
            if self._vertical_direction == MovementDirection.DOWN or self._vertical_direction is None:
                return BoundsInfo(
                    collision_axis="y",
                    collision_edge="bottom",
                    original_position=sprite.position,
                    corrected_position=(sprite.center_x, sprite.center_y + 2 * (bottom - min_y)),
                    wrap_position=(sprite.center_x, height + bbox_height / 2),
                    fully_outside=max_y < bottom,
                )

        return None

    def _is_edge_sprite(self, sprite: ActionSprite, edge: str) -> bool:
        """Check if a sprite is on the specified edge of the group formation."""
        sprites = list(self._iter_target())
        if len(sprites) <= 1:
            return True

        tolerance = 5  # Pixel tolerance for edge detection

        # For wrapping, filter out wrapped sprites from edge calculations
        if isinstance(self.behavior, WrapBehavior):
            bounds = self.get_bounds()
            if len(bounds) == 2:
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

    def _reverse_direction(self, axis: str) -> None:
        """Reverse the tracked movement direction after a bounce."""
        if axis == "x":
            if self._horizontal_direction == MovementDirection.LEFT:
                self._horizontal_direction = MovementDirection.RIGHT
            elif self._horizontal_direction == MovementDirection.RIGHT:
                self._horizontal_direction = MovementDirection.LEFT
        else:  # axis == "y"
            if self._vertical_direction == MovementDirection.UP:
                self._vertical_direction = MovementDirection.DOWN
            elif self._vertical_direction == MovementDirection.DOWN:
                self._vertical_direction = MovementDirection.UP

    def _update_movement_direction(self) -> None:
        """Update movement direction based on current sprite movement."""
        representative_sprite = self._get_representative_sprite()
        if representative_sprite is None:
            return

        # Reset cached direction if group size changed
        try:
            current_size = len(self.target)  # type: ignore[arg-type]
        except TypeError:
            current_size = 1

        if current_size != self._last_group_size:
            self._horizontal_direction = None
            self._vertical_direction = None
            self._last_group_size = current_size

        # Determine direction from sprite velocities
        self._set_direction_from_velocity(representative_sprite)

        # Fallback to active actions if still unknown
        if self._horizontal_direction is None or self._vertical_direction is None:
            self._infer_direction_from_actions(representative_sprite)

    def _get_representative_sprite(self) -> ActionSprite | None:
        """Get a representative sprite from the target."""
        try:
            iterator = iter(self.target)  # type: ignore[not-an-iterable]
            return next(iterator, None)
        except TypeError:
            return self.target

    def _set_direction_from_velocity(self, sprite: ActionSprite) -> None:
        """Set movement direction based on sprite velocities."""
        for s in self._iter_target():
            cx, cy = s.change_x, s.change_y
            if self._horizontal_direction is None and cx != 0:
                self._horizontal_direction = MovementDirection.RIGHT if cx > 0 else MovementDirection.LEFT
            if self._vertical_direction is None and cy != 0:
                self._vertical_direction = MovementDirection.UP if cy > 0 else MovementDirection.DOWN
            if self._horizontal_direction and self._vertical_direction:
                break

        # Fallback to representative sprite
        if self._horizontal_direction is None and sprite.change_x != 0:
            self._horizontal_direction = MovementDirection.RIGHT if sprite.change_x > 0 else MovementDirection.LEFT
        if self._vertical_direction is None and sprite.change_y != 0:
            self._vertical_direction = MovementDirection.UP if sprite.change_y > 0 else MovementDirection.DOWN

    def _infer_direction_from_actions(self, sprite: ActionSprite) -> None:
        """Infer movement direction from active actions."""

        def collect(delta: tuple[float, float]):
            if self._horizontal_direction is None and delta[0] != 0:
                self._horizontal_direction = MovementDirection.RIGHT if delta[0] > 0 else MovementDirection.LEFT
            if self._vertical_direction is None and delta[1] != 0:
                self._vertical_direction = MovementDirection.UP if delta[1] > 0 else MovementDirection.DOWN

        # Check the contained movement action first
        if self.movement_action:
            self.movement_action.extract_movement_direction(collect)
            if self._horizontal_direction and self._vertical_direction:
                return

        # Check group-level actions as fallback
        group_actions = self._group_actions_ref
        if group_actions:
            for g_action in group_actions:
                g_action.extract_movement_direction(collect)
                if self._horizontal_direction and self._vertical_direction:
                    return

        # Check individual sprite actions as final fallback
        for s in self._iter_target():
            try:
                act = s._action  # type: ignore[attr-defined]
            except AttributeError:
                act = None
            if act:
                act.extract_movement_direction(collect)
                if self._horizontal_direction and self._vertical_direction:
                    return


# Convenience functions for backward compatibility and ease of use
def BoundedMove(
    get_bounds: Callable,
    *,
    bounce_horizontal: bool = True,
    bounce_vertical: bool = True,
    on_bounce: Callable[[ActionSprite, str], None] | None = None,
    movement_action: Action | None = None,
) -> BoundaryAction:
    """Create a bouncing boundary action.

    Args:
        get_bounds: Function returning (left, bottom, right, top) bounds
        bounce_horizontal: Whether to bounce on horizontal boundaries
        bounce_vertical: Whether to bounce on vertical boundaries
        on_bounce: Optional callback when bouncing occurs
        movement_action: Optional movement action to control

    Returns:
        BoundaryAction configured for bouncing behavior
    """
    behavior = BounceBehavior(horizontal=bounce_horizontal, vertical=bounce_vertical, callback=on_bounce)
    return BoundaryAction(get_bounds, behavior, movement_action)


def WrappedMove(
    get_bounds: Callable,
    *,
    wrap_horizontal: bool = True,
    wrap_vertical: bool = True,
    on_wrap: Callable[[ActionSprite, str], None] | None = None,
    movement_action: Action | None = None,
) -> BoundaryAction:
    """Create a wrapping boundary action.

    Args:
        get_bounds: Function returning (width, height) bounds
        wrap_horizontal: Whether to wrap on horizontal boundaries
        wrap_vertical: Whether to wrap on vertical boundaries
        on_wrap: Optional callback when wrapping occurs
        movement_action: Optional movement action to control

    Returns:
        BoundaryAction configured for wrapping behavior
    """
    behavior = WrapBehavior(horizontal=wrap_horizontal, vertical=wrap_vertical, callback=on_wrap)
    return BoundaryAction(get_bounds, behavior, movement_action)
