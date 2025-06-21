"""
Group actions and sprite groups for managing multiple sprites together.
"""

import math
from collections.abc import Callable
from typing import Optional

import arcade

from .base import Action


class SpriteGroup(arcade.SpriteList):
    """A container for managing groups of sprites and their actions.

    This class extends `arcade.SpriteList`, providing a simple interface for
    managing multiple sprites as a group and allowing actions to be applied
    to all sprites in the group simultaneously.

    Implements GroupTarget protocol for consistent interface.
    """

    def __init__(self, sprites: list[arcade.Sprite] | None = None):
        super().__init__()
        if sprites:
            for sprite in sprites:
                self.append(sprite)
        self._collision_handlers: list[tuple[arcade.SpriteList | list[arcade.Sprite], Callable]] = []
        self._group_actions: list[Action] = []  # Track active GroupAction instances - implements GroupTarget

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
            # Ensure we have an Arcade SpriteList for collision API.
            temp_list = arcade.SpriteList()
            for sprite in other_group:
                temp_list.append(sprite)

            collision_group = temp_list

            for sprite in self:
                hit_list = arcade.check_for_collision_with_list(sprite, collision_group)
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

    This class implements the same interface as individual actions, making group and
    individual actions indistinguishable.
    """

    def __init__(self, group: arcade.SpriteList | list[arcade.Sprite], action: Action):
        super().__init__()
        self.group = list(group)
        self.template = action
        self.actions: list[Action] = []  # Individual actions for each sprite

        # Implement consistent interface - same as MovementAction, CompositeAction, etc.
        self.delta: tuple[float, float] = (0.0, 0.0)
        self.total_change: tuple[float, float] = (0.0, 0.0)
        self.end_position: tuple[float, float] | None = None
        self.current_action: Action | None = None
        self.current_index: int = 0
        self.other: Action | None = None

    def start(self):
        """Start the action on the group."""
        super().start()
        # Create an action instance for each sprite
        self.actions = []
        for sprite in self.group:
            # Create a clone of the action
            action_copy = self.template.clone()
            action_copy.target = sprite
            action_copy.start()
            self.actions.append(action_copy)

    def update(self, delta_time: float):
        """Update the group action."""
        if self._paused:
            return

        # Update elapsed time
        self._elapsed += delta_time

        if not self.actions:
            return

        # Update each sprite's action
        for action in self.actions:
            if not action.done:
                action.update(delta_time)

        # Check if all actions are now done (after updating)
        all_done = all(action.done for action in self.actions)

        # Set completion state and check for completion callback
        if all_done:
            self.done = True

        # Check for completion callback (after setting done state)
        self._check_complete()

    def stop(self):
        """Stop the current group action."""
        for action in self.actions:
            action.stop()
        self.actions = []
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
        for action in self.actions:
            action.pause()

    def resume(self):
        """Resume all actions in the group."""
        super().resume()
        for action in self.actions:
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
        else:  # axis == "y"
            self.delta = (self.delta[0], -self.delta[1])
            self.total_change = (self.total_change[0], -self.total_change[1])

        # Also reverse all individual actions
        for action in self.actions:
            action.reverse_movement(axis)

    def get_movement_actions(self) -> list[Action]:
        """Get all movement actions from this group - consistent with CompositeAction."""
        return [action for action in self.actions if action.get_movement_delta() != (0.0, 0.0)]

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
        for action in self.actions:
            action.extract_movement_direction(collector)

    def adjust_for_position_delta(self, position_delta: tuple[float, float]) -> None:  # noqa: D401
        self.template.adjust_for_position_delta(position_delta)
        for action in self.actions:
            action.adjust_for_position_delta(position_delta)


class Pattern:
    """Base class for attack patterns."""

    def __init__(self, name: str):
        self.name = name

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        raise NotImplementedError("Subclasses must implement apply()")


class LinePattern(Pattern):
    """Pattern for arranging sprites in a line."""

    def __init__(self, spacing: float = 50.0):
        super().__init__("line")
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", start_x: float = 0, start_y: float = 0):
        """Apply line pattern to the attack group."""
        for i, sprite in enumerate(attack_group.sprites):
            sprite.center_x = start_x + i * self.spacing
            sprite.center_y = start_y


class GridPattern(Pattern):
    """Pattern for arranging sprites in a grid."""

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


class CirclePattern(Pattern):
    """Pattern for arranging sprites in a circle."""

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


class VFormationPattern(Pattern):
    """Pattern for arranging sprites in a V formation."""

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
    """A high-level controller for managing groups of sprites with attack patterns."""

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
