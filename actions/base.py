"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import arcade

from .game_clock import GameClock

if TYPE_CHECKING:
    from .composite import Sequence, Spawn


class Action(ABC):
    """Base class for all actions.

    Actions modify sprite properties over time using Arcade's velocity-based
    movement system (change_x, change_y, change_angle, etc.) rather than
    directly modifying position/angle/scale.

    Actions can be applied to individual sprites or sprite lists.
    """

    def __init__(self, clock: GameClock | None = None):
        self.target: arcade.Sprite | arcade.SpriteList | None = None
        self._elapsed: float = 0.0
        self.done: bool = False  # Public completion state
        self._paused: bool = False
        self._on_complete = None
        self._on_complete_args = ()
        self._on_complete_kwargs = {}
        self._on_complete_called = False
        self._clock = clock
        if clock:
            clock.subscribe(self._on_pause_state_changed)

    def _on_pause_state_changed(self, paused: bool) -> None:
        """Handle pause state changes from the game clock."""
        self._paused = paused

    def on_complete(self, func, *args, **kwargs):
        """Register a callback to be triggered when the action completes."""
        self._on_complete = func
        self._on_complete_args = args
        self._on_complete_kwargs = kwargs
        return self

    def when_done(self, func, *args, **kwargs):
        """Alias for on_complete(), more readable for game scripting."""
        return self.on_complete(func, *args, **kwargs)

    def _check_complete(self):
        if self.done and self._on_complete and not self._on_complete_called:
            self._on_complete_called = True
            self._on_complete(*self._on_complete_args, **self._on_complete_kwargs)

    @abstractmethod
    def start(self) -> None:
        """Called when the action begins.

        Override this to set up initial state and velocities.
        """
        pass

    def update(self, delta_time: float) -> None:
        """Called each frame to update the action.

        This base implementation handles:
        - Pause state checking
        - Elapsed time tracking
        - Completion callback triggering

        Override this method to add custom update behavior, but be sure to call
        super().update(delta_time) to maintain the base functionality.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if not self._paused:
            self._elapsed += delta_time
            self._check_complete()

    def stop(self) -> None:
        """Called when the action ends.

        This base implementation handles:
        - Clock unsubscription
        - Target cleanup
        - Completion callback triggering

        Override this method to add custom cleanup behavior, but be sure to call
        super().stop() to maintain the base functionality.
        """
        if self._clock:
            self._clock.unsubscribe(self._on_pause_state_changed)
        self.target = None
        self._check_complete()

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self._elapsed = 0.0
        self.done = False
        self._paused = False
        self._on_complete_called = False

    def pause(self) -> None:
        """Pause the action."""
        self._paused = True

    def resume(self) -> None:
        """Resume the action."""
        self._paused = False

    def __add__(self, other: "Action") -> "Sequence":
        """Sequence operator - concatenates actions.

        action1 + action2 -> action_result
        where action_result performs as:
        first do all that action1 would do; then
        perform all that action2 would do
        """
        from .composite import sequence

        return sequence(self, other)

    def __mul__(self, other: int) -> "Loop":
        """Repeat operator - repeats the action n times.

        action * n -> action_result
        where action result performs as:
        repeat n times the changes that action would do
        """
        if not isinstance(other, int):
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        from .composite import loop

        return loop(self, other)

    def __or__(self, other: "Action") -> "Spawn":
        """Spawn operator - runs two actions in parallel.

        action1 | action2 -> action_result
        """
        from .composite import spawn

        return spawn(self, other)

    def __reversed__(self) -> "Action":
        """Returns a reversed version of this action.

        Not all actions can be reversed. Override this method
        to implement reversal.
        """
        raise NotImplementedError(f"Action {self.__class__.__name__} cannot be reversed")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}()"


class IntervalAction(Action):
    """Base class for actions that have a fixed duration."""

    def __init__(self, duration: float):
        super().__init__()
        self.duration = duration

    def update(self, delta_time: float) -> None:
        """Update the action and check for completion."""
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.done = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(duration={self.duration})"


class InstantAction(Action):
    """Base class for actions that happen instantly."""

    def __init__(self):
        super().__init__()
        self.duration = 0.0

    def update(self, delta_time: float) -> None:
        """Instant actions complete immediately."""
        super().update(delta_time)
        self.done = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class GroupAction(Action):
    """Applies an action to all sprites in a sprite list."""

    def __init__(self, sprite_list: arcade.SpriteList, action: Action):
        super().__init__()
        self.sprite_list = sprite_list
        self.action = action
        self.actions: list[Action] = []

    def start(self) -> None:
        # Create an action instance for each sprite
        self.actions = []
        for sprite in self.sprite_list:
            action_copy = copy.deepcopy(self.action)
            action_copy.target = sprite
            action_copy.start()
            self.actions.append(action_copy)

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        # Update each sprite's action
        all_done = True
        for action in self.actions:
            if not action.done:
                action.update(delta_time)
                all_done = False

        self.done = all_done

    def __repr__(self) -> str:
        return f"GroupAction(sprite_list={self.sprite_list}, action={self.action})"


class ActionSprite(arcade.Sprite):
    """A sprite that supports time-based Actions like MoveBy, RotateBy, etc.

    This class extends arcade.Sprite to add action management capabilities.
    It allows sprites to have a single action applied to them and handles the
    updating and cleanup of that action automatically.

    Note: This class is designed to manage only one action at a time. To achieve
    multiple behaviors simultaneously, use composite actions like Spawn or Sequence.
    For example:
        # Run two actions in parallel
        sprite.do(action1 | action2)
        # Run actions in sequence
        sprite.do(action1 + action2)
    """

    def __init__(self, *args, **kwargs):
        # Pop the clock if provided, otherwise create a default one
        self._clock = kwargs.pop("clock", GameClock())
        super().__init__(*args, **kwargs)

        self._action: Action | None = None
        self._is_paused: bool = False
        self._is_cleaning_up: bool = False

        # Subscribe to the clock's pause state
        if self._clock:
            self._clock.subscribe(self._on_pause_state_changed)

    def _on_pause_state_changed(self, paused: bool) -> None:
        """Handle pause state changes from the game clock."""
        self._is_paused = paused
        # Pause/resume current action
        if self._action:
            if paused:
                self._action.pause()
            else:
                self._action.resume()

    def do(self, action: Action) -> Action:
        """Start an action on this sprite.

        If another action is currently running, it will be stopped before
        starting the new action.

        Args:
            action: The action to start

        Returns:
            The started action instance
        """
        # Stop any existing action
        if self._action:
            self._action.stop()

        action.target = self
        action.start()
        self._action = action
        # Set initial pause state
        if self._is_paused:
            action.pause()
        return action

    def update(self, delta_time: float = 1 / 60):
        """Update the current action.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if self._is_paused or not self._action:
            return

        self._action.update(delta_time)
        if self._action.done:
            self._action.stop()
            self._action = None

    def clear_actions(self):
        """Cancel the current action if any."""
        if self._action:
            self._action.stop()
            self._action = None

    def has_active_actions(self) -> bool:
        """Return True if an action is currently running."""
        return self._action is not None and not self._action.done

    def pause(self):
        """Pause the current action."""
        self._is_paused = True
        if self._action:
            self._action.pause()

    def resume(self):
        """Resume the current action."""
        self._is_paused = False
        if self._action:
            self._action.resume()

    def is_busy(self) -> bool:
        """Return True if an action is currently running and not done."""
        return self._action is not None and not self._action.done

    def cleanup(self):
        """Explicitly unsubscribe from the game clock."""
        if self._clock:
            self._clock.unsubscribe(self._on_pause_state_changed)

    def __del__(self):
        """Ensure cleanup is called when the sprite is garbage collected."""
        self.cleanup()
