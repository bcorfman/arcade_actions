"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import arcade

if TYPE_CHECKING:
    pass

"""
Arcade-compatible action system with global action management.

This module provides condition-based actions that work directly with arcade.Sprite
and arcade.SpriteList, using Arcade's native velocity system. All actions are
managed globally to eliminate the need for manual action list bookkeeping.

The condition-based paradigm uses conditions to determine when actions complete:
- MoveUntil(velocity, condition) - move until condition is met
- RotateUntil(angular_velocity, condition) - rotate until condition is met  
- ScaleUntil(scale_velocity, condition) - scale until condition is met
- FadeUntil(fade_velocity, condition) - fade until condition is met

Composite actions work with individual condition-based actions:
- sequence() runs actions one after another until each condition is met
- parallel() runs actions simultaneously until each individual condition is met
"""


class Action:
    """Base class for all actions in the ArcadeActions system.

    Actions are condition-based behaviors that apply effects to sprites or sprite lists
    until specified conditions are met. They integrate with global action management
    for automatic lifecycle handling.

    Args:
        condition_func: Function that returns truthy value when action should complete
        on_condition_met: Optional callback when condition is satisfied
        check_interval: How often to check condition in seconds (default: 0.0 for every frame)
        tag: Tag for organizing actions (default: "default")
    """

    _active_actions: list[Action] = []

    def __init__(
        self,
        condition_func: Callable[[], Any] | None = None,
        on_condition_met: Callable[[Any], None] | Callable[[], None] | None = None,
        check_interval: float = 0.0,
        tag: str = "default",
    ):
        self.target: arcade.Sprite | arcade.SpriteList | None = None
        self.tag = tag
        self._is_active = False
        self.done = False
        self._paused = False

        # Common condition logic
        self.condition_func = condition_func
        self.on_condition_met = on_condition_met
        self.check_interval = check_interval
        self._condition_met = False
        self._condition_data = None
        self._last_check_time = 0.0

    def apply(self, target: arcade.Sprite | arcade.SpriteList, tag: str = "default") -> Action:
        """Apply this action to a sprite or sprite list with the specified tag.

        Args:
            target: The sprite or sprite list to apply the action to
            tag: The tag name (default: "default")

        Returns:
            The applied action

        Example:
            action.apply(sprite, tag="movement")
        """
        self.target = target
        self.tag = tag
        self.start()

        # Add to simplified global tracking
        if self not in Action._active_actions:
            Action._active_actions.append(self)

        return self

    def start(self) -> None:
        """Called when the action begins. Override in subclasses."""
        self._is_active = True
        if self._condition_met:
            return
        self.apply_effect()

    def apply_effect(self) -> None:
        """Apply the action's effect to the target. Override in subclasses."""
        pass

    def update(self, delta_time: float) -> None:
        """Called each frame. Handles condition checking and delegates to update_effect."""
        if not self._is_active or self._condition_met or self._paused:
            return

        # Let subclass update its effect
        self.update_effect(delta_time)

        # Check condition if we have one
        if self.condition_func is not None:
            self._update_condition_check(delta_time)

    def update_effect(self, delta_time: float) -> None:
        """Update the action's effect. Override in subclasses if needed."""
        pass

    def _update_condition_check(self, delta_time: float) -> None:
        """Handle condition checking logic - common to all actions."""
        self._last_check_time += delta_time
        if self._last_check_time >= self.check_interval:
            self._last_check_time = 0.0

            condition_result = self.condition_func()

            # Any truthy value means condition is met
            if condition_result:
                self._condition_met = True
                self._condition_data = condition_result
                self.remove_effect()
                self.done = True

                if self.on_condition_met:
                    # Simplified callback handling - just call with result if not True
                    if condition_result is not True:
                        self.on_condition_met(condition_result)
                    else:
                        self.on_condition_met()

    def remove_effect(self) -> None:
        """Remove the action's effect from the target. Override in subclasses."""
        pass

    def stop(self) -> None:
        """Stop this action instance."""
        if self._is_active:
            self.remove_effect()
        self._is_active = False
        self.done = True
        if self in Action._active_actions:
            Action._active_actions.remove(self)

    @classmethod
    def stop_by_tag(cls, target: arcade.Sprite | arcade.SpriteList, tag: str) -> None:
        """Stop all actions with the specified tag on the target.

        Args:
            target: The sprite or sprite list
            tag: The tag to stop
        """
        to_stop = []
        for action in cls._active_actions:
            if action.target == target and action.tag == tag:
                to_stop.append(action)

        for action in to_stop:
            action.stop()

    @classmethod
    def stop_all_for_target(cls, target: arcade.Sprite | arcade.SpriteList) -> None:
        """Stop all actions for the specified target.

        Args:
            target: The sprite or sprite list
        """
        to_stop = []
        for action in cls._active_actions:
            if action.target == target:
                to_stop.append(action)

        for action in to_stop:
            action.stop()

    @classmethod
    def update_all(cls, delta_time: float) -> None:
        """Update all active actions. Call this once per frame."""
        # Update all actions
        for action in cls._active_actions[:]:  # Copy to avoid modification during iteration
            action.update(delta_time)

        # Remove completed actions
        cls._active_actions[:] = [action for action in cls._active_actions if not action.done]

    @classmethod
    def clear_all(cls) -> None:
        """Stop and clear all active actions."""
        for action in cls._active_actions[:]:
            action.stop()
        cls._active_actions.clear()

    @classmethod
    def get_active_count(cls) -> int:
        """Get the total number of active actions."""
        return len(cls._active_actions)

    @classmethod
    def get_actions_for_target(cls, target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> list[Action]:
        """Get all actions for a target, optionally filtered by tag.

        Args:
            target: The sprite or sprite list
            tag: Optional tag filter

        Returns:
            List of matching actions
        """
        actions = [action for action in cls._active_actions if action.target == target]
        if tag is not None:
            actions = [action for action in actions if action.tag == tag]
        return actions

    def clone(self) -> Action:
        """Create a copy of this action."""
        return Action(self.condition_func, self.on_condition_met, self.check_interval, self.tag)

    def for_each_sprite(self, func: Callable[[arcade.Sprite], None]) -> None:
        """Apply a function to each sprite in the target.

        Args:
            func: Function to apply to each sprite

        Raises:
            ValueError: If target is not set
        """
        if self.target is None:
            raise ValueError("Action target is not set")

        if isinstance(self.target, arcade.Sprite):
            func(self.target)
        elif isinstance(self.target, arcade.SpriteList):
            for sprite in self.target:
                func(sprite)

    def set_factor(self, factor: float) -> None:
        """Set a scaling factor for this action's intensity/rate.

        This provides a universal interface for easing wrappers to modulate
        action behavior over time. Factor of 0.0 means no effect, 1.0 means
        full effect, values >1.0 can provide overdrive if supported.

        Base implementation does nothing - actions that support factor scaling
        should override this method.

        Args:
            factor: Scaling factor (typically 0.0 to 1.0, but can be any float)
        """
        # Default implementation is a no-op so any action can receive the call
        # without requiring runtime type checks
        pass

    @property
    def condition_met(self) -> bool:
        """Whether the action's condition has been met."""
        return self._condition_met

    @property
    def condition_data(self):
        """Data returned by the condition function when it was met."""
        return self._condition_data

    def pause(self) -> None:
        """Pause the action."""
        self._paused = True

    def resume(self) -> None:
        """Resume the action."""
        self._paused = False


class CompositeAction(Action):
    """Base class for composite actions that manage multiple sub-actions."""

    def __init__(self):
        # Composite actions manage their own completion - no external condition
        super().__init__(condition_func=None)
        self._on_complete_called = False

    def _check_complete(self) -> None:
        """Mark the composite action as complete."""
        if not self._on_complete_called:
            self._on_complete_called = True
            self.done = True

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement for boundary bouncing. Override in subclasses."""
        pass

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self.done = False
        self._on_complete_called = False

    def clone(self) -> CompositeAction:
        """Create a copy of this CompositeAction."""
        raise NotImplementedError("Subclasses must implement clone()")
