"""
Group actions and sprite groups for managing multiple sprites together.
"""

import math
from collections.abc import Callable
from typing import Optional

import arcade

from .base import Action
from .protocols import ArcadeCollisionDetector, CollisionDetector


class SpriteGroup(arcade.SpriteList):
    """A container for managing groups of sprites and their actions.

    This class extends `arcade.SpriteList`, providing a simple interface for
    managing multiple sprites as a group and allowing actions to be applied
    to all sprites in the group simultaneously.

    Implements GroupTarget protocol for consistent interface.
    """

    def __init__(self, sprites: list[arcade.Sprite] | None = None, collision_detector: CollisionDetector | None = None):
        super().__init__()
        if sprites:
            for sprite in sprites:
                self.append(sprite)
        self._collision_handlers: list[tuple[arcade.SpriteList | list[arcade.Sprite], Callable]] = []
        self._group_actions: list[Action] = []  # Track active GroupAction instances - implements GroupTarget
        self._collision_detector = collision_detector or ArcadeCollisionDetector()

    def update(self, delta_time: float = 1 / 60):
        """Update all sprites in the group and any active GroupActions.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # Update individual sprites
        for sprite in self:
            sprite.update(delta_time)

        # Update active GroupActions and remove completed ones
        active_actions = []
        for group_action in self._group_actions:
            group_action.update(delta_time)
            if not group_action.done:
                active_actions.append(group_action)
        self._group_actions = active_actions

    def center(self) -> tuple[float, float]:
        """Get the center point of all sprites in the group."""
        if not self:
            return (0, 0)
        avg_x = sum(sprite.center_x for sprite in self) / len(self)
        avg_y = sum(sprite.center_y for sprite in self) / len(self)
        return avg_x, avg_y

    def do(self, action: Action) -> Action:
        """Apply an action to all sprites in the group.

        Args:
            action: The action to apply to all sprites

        Returns:
            The GroupAction instance managing the action - SAME INTERFACE as individual actions
        """
        group_action = GroupAction(self, action)
        group_action.start()
        # Track this GroupAction so it gets updated automatically
        self._group_actions.append(group_action)
        return group_action

    def clear_actions(self):
        """Clear all actions from sprites in the group and stop any GroupActions."""
        # Clear individual sprite actions
        for sprite in self:
            sprite.clear_actions()

        # Stop and clear all GroupActions
        for group_action in self._group_actions:
            group_action.stop()
        self._group_actions.clear()

    def on_collision_with(
        self, other_group: arcade.SpriteList | list[arcade.Sprite], callback: Callable
    ) -> "SpriteGroup":
        """Register a collision handler between this group and another.

        Args:
            other_group: The sprite list or group to check collisions against
            callback: Function to call when collision occurs. Should accept (colliding_sprite, hit_sprites)

        Returns:
            Self to allow method chaining
        """
        self._collision_handlers.append((other_group, callback))
        return self

    def update_collisions(self):
        """Update collision detection for all registered handlers."""
        for other_group, callback in self._collision_handlers:
            for sprite in self:
                hit_list = self._collision_detector.check_collision(sprite, other_group)
                if hit_list:
                    callback(sprite, hit_list)

    def breakaway(self, breakaway_sprites: list) -> "SpriteGroup":
        """Remove given sprites and create a new SpriteGroup."""
        new_group = SpriteGroup()
        for sprite in breakaway_sprites:
            if sprite in self:
                self.remove(sprite)
                new_group.append(sprite)
        return new_group


class GroupAction(Action):
    """A high-level controller for running a shared Action over a group of sprites.

    This class is automatically created by SpriteGroup.do() and implements the same
    interface as individual actions, making group and individual actions indistinguishable.

    Users rarely need to create GroupAction instances directly - they are automatically
    managed by SpriteGroup.do() and cleaned up when actions complete.

    Key features:
    - Batch optimization for movement actions (significant performance improvement)
    - Consistent interface with individual actions (same methods, same behavior)
    - Automatic cleanup when actions complete
    - Pause/resume support for coordinated group behavior

    Example:
        enemies = SpriteGroup([sprite1, sprite2, sprite3])
        group_action = enemies.do(MoveBy((100, 0), 2.0))  # Returns GroupAction
        # group_action automatically coordinates movement across all sprites
    """

    def __init__(self, group: arcade.SpriteList | list[arcade.Sprite], action: Action):
        super().__init__()
        self.group = list(group)
        self.template = action
        self._actions: list[Action] = []  # Individual actions for each sprite

        # Implement consistent interface - same as MovementAction, CompositeAction, etc.
        self.delta: tuple[float, float] = (0.0, 0.0)
        self.total_change: tuple[float, float] = (0.0, 0.0)
        self.end_position: tuple[float, float] | None = None
        self.current_action: Action | None = None
        self.current_index: int = 0
        self.other: Action | None = None

        # Batch optimization state
        self._use_batch_optimization = False
        self._batch_start_positions: list[tuple[float, float]] = []
        self._batch_total_change: tuple[float, float] = (0.0, 0.0)

    @property
    def actions(self) -> list[Action]:
        """Get the list of individual actions.

        When using batch optimization, this returns an empty list since individual
        actions aren't created. Use sprite_count property to get the number of sprites.
        """
        return self._actions

    @actions.setter
    def actions(self, value: list[Action]) -> None:
        """Set the list of individual actions."""
        self._actions = value

    @property
    def sprite_count(self) -> int:
        """Get the number of sprites in the group regardless of optimization mode."""
        return len(self.group)

    def start(self):
        """Start the action on the group."""
        super().start()

        # Check if we can use batch optimization for movement actions
        if self._can_use_batch_optimization():
            self._setup_batch_optimization()
        else:
            self._setup_individual_actions()

    def _can_use_batch_optimization(self) -> bool:
        """Check if the template action can be optimized with batch processing.

        Returns True for movement actions that apply the same transformation
        to all sprites (MoveBy, MoveTo, etc.).
        """
        from .interval import MoveBy, MoveTo
        from .move import MovementAction

        # Check for direct movement actions
        if isinstance(self.template, (MoveBy, MoveTo)):
            return True

        # Check for MovementAction base class (covers custom movement actions)
        if isinstance(self.template, MovementAction):
            return True

        return False

    def _setup_batch_optimization(self):
        """Set up batch optimization for movement actions."""
        self._use_batch_optimization = True
        self._actions = []  # Don't create individual actions

        # Store initial positions for all sprites
        self._batch_start_positions = [sprite.position for sprite in self.group]

        # Initialize the template action with a dummy target to get its parameters
        # We'll calculate the movement delta and apply it to all sprites manually
        if hasattr(self.template, "delta"):
            self._batch_total_change = self.template.delta
        elif hasattr(self.template, "total_change"):
            self._batch_total_change = self.template.total_change
        else:
            # Fallback: start the template with first sprite to get its parameters
            if self.group:
                temp_template = self.template.clone()
                temp_template.target = self.group[0]
                temp_template.start()
                if hasattr(temp_template, "total_change"):
                    self._batch_total_change = temp_template.total_change
                elif hasattr(temp_template, "delta"):
                    self._batch_total_change = temp_template.delta

    def _setup_individual_actions(self):
        """Set up individual actions for each sprite (fallback for non-movement actions)."""
        self._use_batch_optimization = False
        self._actions = []
        for sprite in self.group:
            # Create a clone of the action
            action_copy = self.template.clone()
            action_copy.target = sprite
            action_copy.start()
            self._actions.append(action_copy)

    def update(self, delta_time: float):
        """Update the group action using batch optimization when possible."""
        if self._paused:
            return

        # Update elapsed time
        self._elapsed += delta_time

        if self._use_batch_optimization:
            self._update_batch_movement(delta_time)
        else:
            self._update_individual_actions(delta_time)

    def _update_batch_movement(self, delta_time: float):
        """Update movement for all sprites using batch optimization."""
        if not self.group:
            self.done = True
            return

        # Calculate progress based on template action's duration
        if hasattr(self.template, "duration") and self.template.duration > 0:
            progress = min(self._elapsed / self.template.duration, 1.0)

            # Check if we're done
            if self._elapsed >= self.template.duration:
                self.done = True
        else:
            # Instant action or no duration - complete immediately
            progress = 1.0
            self.done = True

        # Apply the same movement calculation to all sprites
        for i, sprite in enumerate(self.group):
            start_pos = self._batch_start_positions[i]

            # Calculate new position using the same logic as individual movement actions
            new_x = start_pos[0] + self._batch_total_change[0] * progress
            new_y = start_pos[1] + self._batch_total_change[1] * progress

            sprite.position = (new_x, new_y)

        # Check for completion callback (after setting done state)
        self._check_complete()

    def _update_individual_actions(self, delta_time: float):
        """Update individual actions (fallback for non-movement actions)."""
        if not self._actions:
            return

        # Update each sprite's action
        for action in self._actions:
            if not action.done:
                action.update(delta_time)

        # Check if all actions are now done (after updating)
        all_done = all(action.done for action in self._actions)

        # Set completion state and check for completion callback
        if all_done:
            self.done = True

        # Check for completion callback (after setting done state)
        self._check_complete()

    def stop(self):
        """Stop the current group action."""
        if not self._use_batch_optimization:
            for action in self._actions:
                action.stop()
        self._actions = []
        self._batch_start_positions = []
        super().stop()

    def reset(self):
        """Reset and restart the group action."""
        self.stop()
        super().reset()
        self.start()

    def replace(self, new_action: Action):
        """Replace the current group action with a new one (auto-started).

        Args:
            new_action: The new action to apply to the group
        """
        self.stop()
        self.template = new_action
        self.start()

    def pause(self):
        """Pause all actions in the group."""
        super().pause()
        if not self._use_batch_optimization:
            for action in self._actions:
                action.pause()

    def resume(self):
        """Resume all actions in the group."""
        super().resume()
        if not self._use_batch_optimization:
            for action in self._actions:
                action.resume()

    # Implement consistent interface methods for type-based dispatch
    def get_movement_delta(self) -> tuple[float, float]:
        """Get the movement delta for this action - consistent with MovementAction."""
        return self.delta

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement for the specified axis - consistent with MovementAction."""
        if axis == "x":
            self.delta = (-self.delta[0], self.delta[1])
            self.total_change = (-self.total_change[0], self.total_change[1])
            # Update batch optimization state
            if self._use_batch_optimization:
                # Just reverse the total change like the base implementation
                self._batch_total_change = (-self._batch_total_change[0], self._batch_total_change[1])
        else:  # axis == "y"
            self.delta = (self.delta[0], -self.delta[1])
            self.total_change = (self.total_change[0], -self.total_change[1])
            # Update batch optimization state
            if self._use_batch_optimization:
                # Just reverse the total change like the base implementation
                self._batch_total_change = (self._batch_total_change[0], -self._batch_total_change[1])

        # Also reverse all individual actions if using individual mode
        if not self._use_batch_optimization:
            for action in self._actions:
                action.reverse_movement(axis)

    def get_movement_actions(self) -> list[Action]:
        """Get all movement actions from this group - consistent with CompositeAction."""
        return [action for action in self._actions if action.get_movement_delta() != (0.0, 0.0)]

    def get_wrapped_action(self) -> Action:
        """Get the wrapped action - consistent with EasingAction."""
        return self.template

    def clone(self) -> "GroupAction":
        """Create a copy of this GroupAction."""
        return GroupAction(self.group.copy(), self.template.clone())

    def __repr__(self) -> str:
        return f"GroupAction(group={len(self.group)} sprites, action={self.template})"

    # Polymorphic hooks ---------------------------------------------------

    def extract_movement_direction(self, collector):  # type: ignore[override]
        # Delegate to the template and all live actions so direction detection
        # logic sees the same data it did before.
        self.template.extract_movement_direction(collector)
        if not self._use_batch_optimization:
            for action in self._actions:
                action.extract_movement_direction(collector)
        else:
            # For batch optimization, report our own movement delta
            collector(self._batch_total_change)

    def adjust_for_position_delta(self, position_delta: tuple[float, float]) -> None:  # noqa: D401
        self.template.adjust_for_position_delta(position_delta)
        if not self._use_batch_optimization:
            for action in self._actions:
                action.adjust_for_position_delta(position_delta)
        else:
            # For batch optimization, adjust our cached start positions
            self._batch_start_positions = [
                (pos[0] + position_delta[0], pos[1] + position_delta[1]) for pos in self._batch_start_positions
            ]


class _Pattern:
    """Base class for attack patterns."""

    def __init__(self, name: str):
        self.name = name

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        raise NotImplementedError("Subclasses must implement apply()")


class LinePattern(_Pattern):
    """Pattern for arranging sprites in a horizontal line.

    Positions sprites in a straight line with configurable spacing between them.
    Useful for creating horizontal formations, bullet patterns, or UI elements.

    Args:
        spacing: Distance between sprite centers in pixels (default: 50.0)

    Example:
        pattern = LinePattern(spacing=80.0)
        pattern.apply(attack_group, start_x=100, start_y=300)
        # Sprites positioned at (100,300), (180,300), (260,300), etc.
    """

    def __init__(self, spacing: float = 50.0):
        super().__init__("line")
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", start_x: float = 0, start_y: float = 0):
        """Apply line pattern to the attack group."""
        for i, sprite in enumerate(attack_group.sprites):
            sprite.center_x = start_x + i * self.spacing
            sprite.center_y = start_y


class GridPattern(_Pattern):
    """Pattern for arranging sprites in a rectangular grid formation.

    Creates rows and columns of sprites with configurable spacing.
    Perfect for Space Invaders-style enemy formations or organized layouts.

    Args:
        rows: Number of rows in the grid (default: 5)
        cols: Number of columns in the grid (default: 10)
        spacing_x: Horizontal spacing between sprites in pixels (default: 60.0)
        spacing_y: Vertical spacing between sprites in pixels (default: 50.0)

    Example:
        pattern = GridPattern(rows=3, cols=5, spacing_x=80, spacing_y=60)
        pattern.apply(attack_group, start_x=200, start_y=400)
        # Creates 3x5 grid starting at (200,400)
    """

    def __init__(self, rows: int = 5, cols: int = 10, spacing_x: float = 60.0, spacing_y: float = 50.0):
        super().__init__("grid")
        self.rows = rows
        self.cols = cols
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

    def apply(self, attack_group: "AttackGroup", start_x: float = 100, start_y: float = 500):
        """Apply grid pattern to the attack group."""
        for i, sprite in enumerate(attack_group.sprites):
            row = i // self.cols
            col = i % self.cols
            sprite.center_x = start_x + col * self.spacing_x
            sprite.center_y = start_y - row * self.spacing_y


class CirclePattern(_Pattern):
    """Pattern for arranging sprites in a circular formation.

    Distributes sprites evenly around a circle with configurable radius.
    Great for radial bullet patterns or defensive formations.

    Args:
        radius: Radius of the circle in pixels (default: 100.0)

    Example:
        pattern = CirclePattern(radius=150.0)
        pattern.apply(attack_group, center_x=400, center_y=300)
        # Sprites arranged in circle around (400,300) with radius 150
    """

    def __init__(self, radius: float = 100.0):
        super().__init__("circle")
        self.radius = radius

    def apply(self, attack_group: "AttackGroup", center_x: float = 400, center_y: float = 300):
        """Apply circle pattern to the attack group."""
        count = len(attack_group.sprites)
        if count == 0:
            return

        angle_step = 2 * math.pi / count
        for i, sprite in enumerate(attack_group.sprites):
            angle = i * angle_step
            sprite.center_x = center_x + math.cos(angle) * self.radius
            sprite.center_y = center_y + math.sin(angle) * self.radius


class VFormationPattern(_Pattern):
    """Pattern for arranging sprites in a V or wedge formation.

    Creates a V-shaped formation with one sprite at the apex and others
    arranged alternately on left and right sides. Useful for flying formations
    or arrow-like attack patterns.

    Args:
        angle: Angle of the V formation in degrees (default: 45.0)
        spacing: Distance between sprites in the formation (default: 50.0)

    Example:
        pattern = VFormationPattern(angle=30.0, spacing=60.0)
        pattern.apply(attack_group, apex_x=400, apex_y=500)
        # Creates V formation with apex at (400,500)
    """

    def __init__(self, angle: float = 45.0, spacing: float = 50.0):
        super().__init__("v_formation")
        self.angle = math.radians(angle)
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", apex_x: float = 400, apex_y: float = 500):
        """Apply V formation pattern to the attack group."""
        sprites = list(attack_group.sprites)
        count = len(sprites)
        if count == 0:
            return

        # Place the first sprite at the apex
        sprites[0].center_x = apex_x
        sprites[0].center_y = apex_y

        # Place remaining sprites alternating on left and right sides
        for i in range(1, count):
            side = 1 if i % 2 == 1 else -1  # Alternate sides
            distance = (i + 1) // 2 * self.spacing

            offset_x = side * math.cos(self.angle) * distance
            offset_y = -math.sin(self.angle) * distance

            sprites[i].center_x = apex_x + offset_x
            sprites[i].center_y = apex_y + offset_y


class AttackGroup:
    """A high-level controller for managing groups of sprites with attack patterns.

    AttackGroup provides a game-oriented wrapper around SpriteGroup with additional
    features for managing sprite lifecycles, attack patterns, scheduling, and hierarchical
    group relationships. It's designed for complex game scenarios like enemy formations,
    bullet patterns, and coordinated attacks.

    Key features:
    - Automatic lifecycle management (birth time, destruction)
    - Attack pattern application (LinePattern, GridPattern, etc.)
    - Event scheduling for delayed actions
    - Hierarchical relationships (parent/child groups)
    - Breakaway mechanics for dynamic group splitting
    - Pause/resume support

    Args:
        sprite_group: The SpriteGroup to manage
        name: Optional name for debugging and identification
        parent: Optional parent AttackGroup for hierarchical management

    Example:
        enemies = SpriteGroup([enemy1, enemy2, enemy3])
        formation = AttackGroup(enemies, name="enemy_wave_1")

        # Apply formation pattern
        pattern = GridPattern(rows=2, cols=3)
        pattern.apply(formation, start_x=200, start_y=400)

        # Schedule coordinated movement
        formation.schedule_attack(2.0, formation.do, MoveBy((100, -50), 1.5))

        # Update in game loop
        formation.update(delta_time)
    """

    def __init__(
        self,
        sprite_group: SpriteGroup,
        name: str | None = None,
        parent: Optional["AttackGroup"] = None,
    ):
        self.sprites = sprite_group
        self.time_of_birth = arcade.clock.GLOBAL_CLOCK.time
        self.is_destroyed = False
        self.name = name
        self._scheduled_wrappers: list[tuple[Callable, bool]] = []  # (wrapper, repeat)
        self.actions: list[Action] = []  # Track running group actions
        self.parent = parent
        self.children: list[AttackGroup] = []  # Child attack groups
        self.on_destroy_callbacks: list[Callable[[AttackGroup], None]] = []
        self.on_breakaway_callbacks: list[Callable[[AttackGroup], None]] = []
        self._paused = False

    def update(self, delta_time: float):
        """Update the attack group and its actions."""
        if self._paused:
            return

        self.sprites.update(delta_time)
        for wrapper, _ in self._scheduled_wrappers:
            wrapper(delta_time)

        for action in self.actions:
            action.update(delta_time)

        if len(self.sprites) == 0:
            self.destroy()

    def do(self, action: Action) -> Action:
        """Assign an action to all sprites in the group - SAME INTERFACE as individual sprites."""
        group_action = self.sprites.do(action)
        # Track and handle pause
        self.actions.append(group_action)
        if self._paused:
            group_action.pause()
        return group_action

    def schedule_attack(self, delay: float, func: Callable, *args, **kwargs) -> int:
        """Schedule an attack event after X seconds."""

        # Implement scheduling via arcade.schedule_once
        def _wrapper(_dt):
            func(*args, **kwargs)

        arcade.schedule_once(_wrapper, delay)
        self._scheduled_wrappers.append((_wrapper, False))
        return len(self._scheduled_wrappers) - 1

    def breakaway(self, breakaway_sprites: list) -> "AttackGroup":
        """Remove given sprites and create a new AttackGroup."""
        new_sprite_group = self.sprites.breakaway(breakaway_sprites)
        new_group = AttackGroup(
            new_sprite_group,
            name=f"{self.name}_breakaway",
            parent=self,
        )
        self.children.append(new_group)
        # Unschedule arcade callbacks
        for wrapper, _ in self._scheduled_wrappers:
            arcade.unschedule(wrapper)
        self._scheduled_wrappers.clear()
        # Stop running actions
        for action in self.actions:
            action.stop()
        self.actions.clear()
        for callback in self.on_breakaway_callbacks:
            callback(new_group)
        return new_group

    def destroy(self):
        """Clean up resources."""
        if self.is_destroyed:
            return
        self.is_destroyed = True
        # Stop all actions
        for action in self.actions:
            action.stop()
        self.actions.clear()
        # Notify callbacks
        for callback in self.on_destroy_callbacks:
            callback(self)

    def on_destroy(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when the group is destroyed."""
        self.on_destroy_callbacks.append(callback)

    def on_breakaway(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when sprites break away."""
        self.on_breakaway_callbacks.append(callback)

    def __repr__(self):
        return f"<AttackGroup name={self.name} sprites={len(self.sprites)} actions={len(self.actions)}>"
