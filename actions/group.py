"""
Group actions and sprite groups for managing multiple sprites together.
"""

import copy
import math
from collections.abc import Callable
from typing import Optional

import arcade

from .base import Action
from .composite import Sequence
from .game_clock import GameClock, Scheduler
from .interval import MoveBy, MoveTo


class SpriteGroup(arcade.SpriteList):
    """A container for managing groups of sprites and their actions.

    This class extends `arcade.SpriteList`, providing a simple interface for
    managing multiple sprites as a group and allowing actions to be applied
    to all sprites in the group simultaneously.
    """

    def __init__(self, sprites: list[arcade.Sprite] | None = None):
        super().__init__()
        if sprites:
            for sprite in sprites:
                self.append(sprite)
        self._collision_handlers: list[tuple[arcade.SpriteList | list[arcade.Sprite], Callable]] = []
        self._group_actions: list[GroupAction] = []  # Track active GroupAction instances

    def update(self, delta_time: float = 1 / 60):
        """Update all sprites in the group and any active GroupActions.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # Update individual sprites
        for sprite in self:
            if hasattr(sprite, "update"):
                sprite.update(delta_time)

        # Update active GroupActions and remove completed ones
        active_actions = []
        for group_action in self._group_actions:
            group_action.update(delta_time)
            if not group_action.done():
                active_actions.append(group_action)
        self._group_actions = active_actions

    def center(self) -> tuple[float, float]:
        """Get the center point of all sprites in the group."""
        if not self:
            return (0, 0)
        avg_x = sum(sprite.center_x for sprite in self) / len(self)
        avg_y = sum(sprite.center_y for sprite in self) / len(self)
        return avg_x, avg_y

    def do(self, action: Action) -> "GroupAction":
        """Apply an action to all sprites in the group.

        Args:
            action: The action to apply to all sprites

        Returns:
            The GroupAction instance managing the action
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
            if hasattr(sprite, "clear_actions"):
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
        """Check for collisions and trigger callbacks."""
        for sprite in self:
            for other_group, callback in self._collision_handlers:
                # Convert regular lists to SpriteList for arcade compatibility
                if isinstance(other_group, list) and not isinstance(other_group, arcade.SpriteList):
                    # Create a temporary SpriteList
                    temp_sprite_list = arcade.SpriteList()
                    for s in other_group:
                        temp_sprite_list.append(s)
                    hits = arcade.check_for_collision_with_list(sprite, temp_sprite_list)
                else:
                    hits = arcade.check_for_collision_with_list(sprite, other_group)
                if hits:
                    callback(sprite, hits)

    def breakaway(self, breakaway_sprites: list[arcade.Sprite]) -> "SpriteGroup":
        """Remove given sprites and return a new SpriteGroup.

        Args:
            breakaway_sprites: List of sprites to remove from this group

        Returns:
            A new SpriteGroup containing the removed sprites
        """
        for sprite in breakaway_sprites:
            if sprite in self:
                self.remove(sprite)
        return SpriteGroup(breakaway_sprites)


class GroupAction:
    """A high-level controller for running a shared Action over a group of sprites."""

    def __init__(self, group: arcade.SpriteList | list[arcade.Sprite], action: Action):
        self.group = list(group)
        self.template = action
        self.actions: list[Action] = []  # Individual actions for each sprite

    def start(self):
        """Start the action on the group."""
        # Create an action instance for each sprite
        self.actions = []
        for sprite in self.group:
            # Instead of deepcopy, create a shallow copy and handle special cases
            action_copy = self._safe_copy_action(self.template)
            action_copy.target = sprite
            action_copy.start()
            self.actions.append(action_copy)

    def _safe_copy_action(self, action: Action) -> Action:
        """Create a safe copy of an action that avoids deepcopy issues with callbacks.

        This method creates a new instance of the same action type with the same
        parameters, but handles composite actions like Sequence properly.
        """
        from .composite import Loop, Sequence, Spawn
        from .move import BoundedMove, WrappedMove

        # Handle composite actions specially
        if isinstance(action, Sequence):
            # For Sequence, recursively copy each sub-action
            copied_actions = [self._safe_copy_action(sub_action) for sub_action in action.actions]
            new_sequence = Sequence(*copied_actions)
            # Copy completion callbacks
            if hasattr(action, "_on_complete"):
                new_sequence._on_complete = action._on_complete
                new_sequence._on_complete_args = action._on_complete_args
                new_sequence._on_complete_kwargs = action._on_complete_kwargs
            return new_sequence

        elif isinstance(action, Spawn):
            # For Spawn, recursively copy each sub-action
            copied_actions = [self._safe_copy_action(sub_action) for sub_action in action.actions]
            new_spawn = Spawn(*copied_actions)
            return new_spawn

        elif isinstance(action, Loop):
            # For Loop, copy the wrapped action
            copied_action = self._safe_copy_action(action.action)
            new_loop = Loop(copied_action, action.times)
            return new_loop

        elif isinstance(action, BoundedMove):
            # Create a new BoundedMove with the same parameters but preserve callbacks by reference
            new_action = BoundedMove(
                action.get_bounds,
                bounce_horizontal=action.bounce_horizontal,
                bounce_vertical=action.bounce_vertical,
                on_bounce=action._on_bounce,  # Preserve callback by reference
            )
            return new_action

        elif isinstance(action, WrappedMove):
            # Create a new WrappedMove with the same parameters but preserve callbacks by reference
            new_action = WrappedMove(
                action.get_bounds,
                wrap_horizontal=action.wrap_horizontal,
                wrap_vertical=action.wrap_vertical,
                on_wrap=action._on_wrap,  # Preserve callback by reference
            )
            return new_action

        else:
            # For basic actions, try shallow copy first
            try:
                new_action = copy.copy(action)
                # Reset target to None
                new_action.target = None
                return new_action
            except Exception:
                # If copy fails, try to create a new instance with same parameters
                try:
                    action_type = type(action)
                    new_action = action_type()

                    # Copy safe attributes
                    for key, value in action.__dict__.items():
                        if key.startswith("_") and ("callback" in key.lower() or "bounce" in key.lower()):
                            # For callback functions, keep the reference (don't deep copy)
                            setattr(new_action, key, value)
                        elif not callable(value) and not key.startswith("target"):
                            # Copy non-callable, non-target attributes
                            try:
                                setattr(new_action, key, copy.deepcopy(value))
                            except (TypeError, ValueError):
                                # If deepcopy fails, just use reference
                                setattr(new_action, key, value)
                        else:
                            # For other attributes, use reference
                            setattr(new_action, key, value)

                    return new_action
                except Exception:
                    # Last resort: just return the original action (not ideal but works)
                    return action

    def update(self, delta_time: float):
        """Update the group action."""
        if not self.actions:
            return

        # Update each sprite's action
        all_done = True
        for action in self.actions:
            if not action.done:
                action.update(delta_time)
                all_done = False

    def stop(self):
        """Stop the current group action."""
        for action in self.actions:
            action.stop()
        self.actions = []

    def reset(self):
        """Reset and restart the group action."""
        self.stop()
        self.start()

    def done(self) -> bool:
        """Check if the group action is complete."""
        return all(action.done for action in self.actions) if self.actions else True

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
        for action in self.actions:
            action.pause()

    def resume(self):
        """Resume all actions in the group."""
        for action in self.actions:
            action.resume()

    def __repr__(self) -> str:
        return f"GroupAction(group={len(self.group)} sprites, action={self.template})"


class Pattern:
    """Base class for attack patterns."""

    def __init__(self, name: str):
        self.name = name

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        raise NotImplementedError("Subclasses must implement apply()")


class DivePattern(Pattern):
    """Pattern for diving attacks."""

    def __init__(self, speed: float, angle: float):
        super().__init__("dive")
        self.speed = speed
        self.angle = angle

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        # Early return if no sprites to apply pattern to
        if not attack_group.sprites:
            return

        rad_angle = math.radians(self.angle)
        dx = self.speed * math.cos(rad_angle)
        dy = self.speed * math.sin(rad_angle)
        dive_action = MoveBy((dx, dy), 1.0)
        attack_group.do(dive_action)


class CirclePattern(Pattern):
    """Pattern for circular movement around a center point."""

    def __init__(self, radius: float, speed: float, clockwise: bool = True):
        super().__init__("circle")
        self.radius = radius
        self.speed = speed
        self.clockwise = clockwise
        self._current_angle = 0.0

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        # Early return if no sprites to apply pattern to
        if not attack_group.sprites:
            return

        center = attack_group.sprites.center()

        # Calculate the time needed for one complete circle
        circumference = 2 * math.pi * self.radius
        duration = circumference / self.speed

        # Create a sequence of moves that approximate a circle
        num_segments = 8  # Number of segments to approximate the circle
        actions = []

        for i in range(num_segments):
            angle = (2 * math.pi * i / num_segments) * (1 if self.clockwise else -1)
            x = center[0] + self.radius * math.cos(angle)
            y = center[1] + self.radius * math.sin(angle)
            move_action = MoveTo((x, y), duration / num_segments)
            actions.append(move_action)

        # Create a repeating sequence
        circle_action = Sequence(*actions)
        attack_group.do(circle_action)


class ZigzagPattern(Pattern):
    """Pattern for zigzag movement."""

    def __init__(self, width: float, height: float, speed: float):
        super().__init__("zigzag")
        self.width = width
        self.height = height
        self.speed = speed

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        # Early return if no sprites to apply pattern to
        if not attack_group.sprites:
            return

        # Calculate the time needed for one complete zigzag
        distance = math.sqrt(self.width**2 + self.height**2)
        duration = distance / self.speed

        # Create a sequence of moves that form a zigzag
        actions = [
            MoveBy((self.width, self.height), duration / 2),
            MoveBy((-self.width, self.height), duration / 2),
        ]

        zigzag_action = Sequence(*actions)
        attack_group.do(zigzag_action)


class FormationPattern(Pattern):
    """Pattern for maintaining a specific formation while moving."""

    def __init__(self, formation_type: str, spacing: float = 50.0):
        super().__init__("formation")
        self.formation_type = formation_type
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        sprites = list(attack_group.sprites)
        if not sprites:
            return

        # Calculate formation positions based on type
        positions = self._calculate_formation_positions(len(sprites), self.formation_type, self.spacing)

        # Create move actions for each sprite
        actions = []
        for sprite, pos in zip(sprites, positions, strict=False):
            move_action = MoveTo(pos, 1.0)
            actions.append(move_action)

        # Apply the formation
        formation_action = Sequence(*actions)
        attack_group.do(formation_action)

    def _calculate_formation_positions(
        self, num_sprites: int, formation_type: str, spacing: float
    ) -> list[tuple[float, float]]:
        """Calculate positions for different formation types."""
        positions = []

        if formation_type == "v":
            # V formation
            for i in range(num_sprites):
                x = (i - num_sprites / 2) * spacing
                y = -abs(x) * 0.5
                positions.append((x, y))

        elif formation_type == "line":
            # Horizontal line
            for i in range(num_sprites):
                x = (i - num_sprites / 2) * spacing
                positions.append((x, 0))

        elif formation_type == "circle":
            # Circular formation
            for i in range(num_sprites):
                angle = 2 * math.pi * i / num_sprites
                x = spacing * math.cos(angle)
                y = spacing * math.sin(angle)
                positions.append((x, y))

        elif formation_type == "diamond":
            # Diamond formation
            side = int(math.sqrt(num_sprites))
            for i in range(side):
                for j in range(side):
                    x = (j - side / 2) * spacing
                    y = (i - side / 2) * spacing
                    positions.append((x, y))

        return positions


class WavePattern(Pattern):
    """Pattern for wave-like movement."""

    def __init__(self, amplitude: float, frequency: float, speed: float):
        super().__init__("wave")
        self.amplitude = amplitude
        self.frequency = frequency
        self.speed = speed

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        # Early return if no sprites to apply pattern to
        if not attack_group.sprites:
            return

        # Create a sequence of moves that form a wave
        num_points = 8
        actions = []

        for i in range(num_points):
            t = i / num_points
            x = self.speed * t
            y = self.amplitude * math.sin(2 * math.pi * self.frequency * t)
            move_action = MoveBy((x, y), 1.0 / num_points)
            actions.append(move_action)

        wave_action = Sequence(*actions)
        attack_group.do(wave_action)


class AttackGroup:
    """A high-level controller for managing groups of sprites with attack patterns."""

    def __init__(
        self,
        sprite_group: SpriteGroup,
        clock: "GameClock",
        scheduler: "Scheduler",
        name: str | None = None,
        parent: Optional["AttackGroup"] = None,
    ):
        self.sprites = sprite_group
        self.clock = clock
        self.scheduler = scheduler
        self.actions: list[GroupAction] = []  # Attached GroupAction instances
        self.time_of_birth = clock.time
        self.is_destroyed = False
        self.name = name
        self.scheduled_tasks: list[int] = []  # Track scheduled tasks for cleanup
        self.parent = parent
        self.children: list[AttackGroup] = []  # Child attack groups
        self.on_destroy_callbacks: list[Callable[[AttackGroup], None]] = []
        self.on_breakaway_callbacks: list[Callable[[AttackGroup], None]] = []
        self._paused = False
        # Subscribe to clock's pause state
        self.clock.subscribe(self._on_pause_state_changed)

    def _on_pause_state_changed(self, paused: bool) -> None:
        """Handle pause state changes from the game clock."""
        self._paused = paused
        # Pause/resume all actions
        for action in self.actions:
            if paused:
                action.pause()
            else:
                action.resume()
        # Propagate to children
        for child in self.children:
            child._on_pause_state_changed(paused)

    def update(self, delta_time: float):
        """Update the attack group and its actions."""
        if self._paused:
            return

        self.sprites.update(delta_time)
        for action in self.actions:
            action.update(delta_time)

        if len(self.sprites) == 0:
            self.destroy()

    def do(self, action: Action) -> GroupAction:
        """Assign an action to all sprites in the group."""
        group_action = self.sprites.do(action)
        self.actions.append(group_action)
        # Set initial pause state
        if self._paused:
            group_action.pause()
        return group_action

    def schedule_attack(self, delay: float, func: Callable, *args, **kwargs) -> int:
        """Schedule an attack event after X seconds."""
        task_id = self.scheduler.schedule(delay, func, *args, **kwargs)
        self.scheduled_tasks.append(task_id)
        return task_id

    def breakaway(self, breakaway_sprites: list) -> "AttackGroup":
        """Remove given sprites and create a new AttackGroup."""
        new_sprite_group = self.sprites.breakaway(breakaway_sprites)
        new_group = AttackGroup(
            new_sprite_group,
            self.clock,
            self.scheduler,
            name=f"{self.name}_breakaway",
            parent=self,
        )
        self.children.append(new_group)
        # Set initial pause state
        if self._paused:
            new_group._on_pause_state_changed(True)
        for callback in self.on_breakaway_callbacks:
            callback(new_group)
        return new_group

    def destroy(self):
        """Clean up resources."""
        if self.is_destroyed:
            return
        self.is_destroyed = True
        # Unsubscribe from clock
        self.clock.unsubscribe(self._on_pause_state_changed)
        # Cancel all scheduled tasks
        for task_id in self.scheduled_tasks:
            self.scheduler.cancel(task_id)
        self.scheduled_tasks.clear()
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
        return f"<AttackGroup name={self.name} sprites={len(self.sprites)} actions={len(self.actions)} paused={self._paused}>"
