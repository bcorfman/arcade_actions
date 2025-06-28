"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

import arcade

"""
Arcade-compatible action system with global action management.

This module provides condition-based actions that work directly with arcade.Sprite
and arcade.SpriteList, using Arcade's native velocity system. All actions are
managed globally to eliminate the need for manual action list bookkeeping.

The new paradigm replaces duration-based actions with condition-based ones:
- MoveUntil(velocity, condition) instead of MoveBy(delta, duration)
- RotateUntil(angular_velocity, condition) instead of RotateBy(angle, duration)
- ScaleUntil(scale_velocity, condition) instead of ScaleBy(scale, duration)
- FadeUntil(fade_velocity, condition) instead of FadeBy(alpha, duration)

Plus "While" variants that continue until condition becomes False:
- MoveWhile, RotateWhile, ScaleWhile, FadeWhile

Composite actions work with individual condition-based actions:
- Sequence runs actions one after another until each condition is met
- Spawn runs actions in parallel until each individual condition is met
"""

from collections.abc import Callable
from typing import Any


class StopMethod:
    """Descriptor that creates a method working both as instance and class method."""

    def __get__(self, instance, owner):
        if instance is None:
            # Called on the class: Action.stop(...)
            return lambda target=None, tag=None: owner._stop_classmethod(target, tag)
        else:
            # Called on an instance: action.stop()
            return lambda: owner._stop_instance(instance)


class Action:
    """Base class for actions that work with Arcade's native sprite system.

    This replaces the old Action class and provides global action management.
    All actions are condition-based rather than duration-based, supporting
    both simple actions and composite actions (Sequence, Spawn).

    The base class handles all condition-related logic to eliminate duplication.

    Named tags allow multiple actions to be grouped and managed together:
    - action.apply(sprite, tag="movement")
    - action.apply(sprite, tag="effects")
    - Action.stop(sprite, tag="effects")
    """

    _active_actions: list["Action"] = []
    _target_tags: dict[arcade.Sprite | arcade.SpriteList, dict[str, list["Action"]]] = {}

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

        # Common condition logic
        self.condition_func = condition_func
        self.on_condition_met = on_condition_met
        self.check_interval = check_interval
        self._condition_met = False
        self._condition_data = None
        self._last_check_time = 0.0

    def apply(self, target: arcade.Sprite | arcade.SpriteList, tag: str = "default") -> "Action":
        """Apply this action to a sprite or sprite list with the specified tag.

        Multiple actions can share the same tag and will run simultaneously.

        Args:
            target: The sprite or sprite list to apply the action to
            tag: The tag name (default: "default")

        Returns:
            The applied action

        Example:
            action.apply(sprite, tag="movement")
            other_action.apply(sprite, tag="movement")  # Both run together
        """
        # Set up this action
        self.target = target
        self.tag = tag
        self.start()

        # Add to global tracking
        if self not in Action._active_actions:
            Action._active_actions.append(self)

        # Track in tag registry
        if target not in Action._target_tags:
            Action._target_tags[target] = {}
        if tag not in Action._target_tags[target]:
            Action._target_tags[target][tag] = []
        Action._target_tags[target][tag].append(self)

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
        if not self._is_active or self._condition_met:
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
                    # Use EAFP for callback parameter handling
                    try:
                        if condition_result is not True:
                            self.on_condition_met(condition_result)
                        else:
                            self.on_condition_met()
                    except TypeError:
                        # Callback doesn't accept parameters
                        self.on_condition_met()

    def remove_effect(self) -> None:
        """Remove the action's effect from the target. Override in subclasses."""
        pass

    # Create the hybrid stop method using descriptor
    stop = StopMethod()

    @classmethod
    def _stop_instance(cls, instance):
        """Stop a specific action instance."""
        if instance._is_active:
            instance.remove_effect()
        instance._is_active = False
        instance.done = True
        if instance in cls._active_actions:
            cls._active_actions.remove(instance)

        # Clean up tag tracking
        if instance.target and instance.target in cls._target_tags:
            if instance.tag in cls._target_tags[instance.target]:
                if instance in cls._target_tags[instance.target][instance.tag]:
                    cls._target_tags[instance.target][instance.tag].remove(instance)

                    # Clean up empty tag lists
                    if not cls._target_tags[instance.target][instance.tag]:
                        del cls._target_tags[instance.target][instance.tag]

                    # Clean up empty target entries
                    if not cls._target_tags[instance.target]:
                        del cls._target_tags[instance.target]

    @classmethod
    def _stop_classmethod(cls, target: arcade.Sprite | arcade.SpriteList | None = None, tag: str | None = None) -> None:
        """Stop actions globally with optional filtering."""
        # Validate mutually exclusive parameters
        if target is not None and tag is not None:
            raise ValueError("target and tag parameters are mutually exclusive")

        if target is None and tag is None:
            # Stop all actions globally
            for action in cls._active_actions[:]:  # Copy to avoid modification during iteration
                cls._stop_instance(action)
        elif target is not None:
            # Stop all actions on target
            if target in cls._target_tags:
                for actions_list in cls._target_tags[target].values():
                    for action in actions_list[:]:  # Copy to avoid modification during iteration
                        cls._stop_instance(action)
        elif tag is not None:
            # Stop all actions with this tag globally
            for sprite_tags in cls._target_tags.values():
                if tag in sprite_tags:
                    for action in sprite_tags[tag][:]:  # Copy to avoid modification during iteration
                        cls._stop_instance(action)

    @classmethod
    def update_all(cls, delta_time: float) -> None:
        """Update all active actions. Call this in your game loop."""
        for action in cls._active_actions:
            if action._is_active and not action.done:
                action.update(delta_time)
            if action.done:
                cls._stop_instance(action)

    @classmethod
    def clear_all(cls) -> None:
        """Clear all actions globally."""
        cls._stop_classmethod()
        cls._active_actions.clear()
        cls._target_tags.clear()

    @classmethod
    def get_active_count(cls) -> int:
        """Get the number of active actions."""
        return len(cls._active_actions)

    @classmethod
    def get_tag_actions(cls, tag: str, target: arcade.Sprite | arcade.SpriteList | None = None) -> list["Action"]:
        """Get all actions currently running with a specific tag.

        Args:
            tag: The tag name
            target: If provided, only get actions on this target

        Returns:
            List of actions with the tag (empty list if none)

        Examples:
            Action.get_tag_actions("effects")  # Get all effects across all sprites
            Action.get_tag_actions("effects", target=sprite)  # Get effects on specific sprite
        """
        if target is None:
            # Get all actions with this tag globally
            actions = []
            for sprite_tags in cls._target_tags.values():
                if tag in sprite_tags:
                    actions.extend(sprite_tags[tag])
            return actions
        else:
            # Get actions with tag on specific target
            if target in cls._target_tags and tag in cls._target_tags[target]:
                return cls._target_tags[target][tag][:]  # Return a copy
            return []

    @classmethod
    def has_tag(cls, tag: str, target: arcade.Sprite | arcade.SpriteList | None = None) -> bool:
        """Check if any actions are running with a specific tag.

        Args:
            tag: The tag name
            target: If provided, only check actions on this target

        Returns:
            True if any actions are running with the tag

        Examples:
            Action.has_tag("effects")  # Check if any effects are running anywhere
            Action.has_tag("effects", target=sprite)  # Check if sprite has effects
        """
        return len(cls.get_tag_actions(tag, target)) > 0

    @classmethod
    def get_target_tags(cls, target: arcade.Sprite | arcade.SpriteList) -> dict[str, list["Action"]]:
        """Get all tags and their actions for a target.

        Args:
            target: The sprite or sprite list

        Returns:
            Dictionary mapping tag names to lists of actions
        """
        if target not in cls._target_tags:
            return {}
        return {tag: actions[:] for tag, actions in cls._target_tags[target].items()}  # Return copies

    @classmethod
    def get_all_tags(cls) -> dict[str, list["Action"]]:
        """Get all tags and their actions across all targets.

        Returns:
            Dictionary mapping tag names to lists of actions from all sprites
        """
        all_tags = {}
        for sprite_tags in cls._target_tags.values():
            for tag, actions in sprite_tags.items():
                if tag not in all_tags:
                    all_tags[tag] = []
                all_tags[tag].extend(actions)
        return all_tags

    def clone(self) -> "Action":
        """Create a copy of this action. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement clone()")

    # Support for composite actions using existing operators
    def __add__(self, other: "Action") -> "Sequence":
        """Sequence operator - concatenates actions."""
        return Sequence(self, other)

    def __or__(self, other: "Action") -> "Spawn":
        """Spawn operator - runs actions in parallel."""
        return Spawn(self, other)

    def for_each_sprite(self, func: Callable[[arcade.Sprite], None]) -> None:
        """Apply a function to all sprites in the target using EAFP."""
        try:
            # Try as sprite list first (most common case for actions)
            for sprite in self.target:
                func(sprite)
        except TypeError:
            # Single sprite
            func(self.target)

    @property
    def condition_met(self) -> bool:
        """Check if the condition has been satisfied."""
        return self._condition_met

    @property
    def condition_data(self):
        """Get the data returned by the condition function (if any)."""
        return self._condition_data


class CompositeAction(Action):
    """Base class for composite actions with consistent interface."""

    def __init__(self):
        # Don't call super().__init__() here since this will be used in multiple inheritance
        # The concrete classes will handle calling the appropriate parent constructors
        self.actions: list[Action] = []
        self.current_action: Action | None = None
        self.current_index: int = 0

    def reverse_movement(self, axis: str) -> None:
        if self.current_action:
            self.current_action.reverse_movement(axis)
        for child in self.actions[self.current_index :]:
            child.reverse_movement(axis)

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
