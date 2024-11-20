from __future__ import annotations

import arcade


class Action:
    """
    Base class for all actions, providing core timing, update, and composition methods.

    This class serves as the foundation for both instant and interval actions. It manages
    the lifecycle of an action and provides utility methods to ensure frame-rate independence
    and correct handling of delta time (dt).

    Key Features:
        - Tracks elapsed time to control action progression.
        - Converts elapsed time to a normalized time (t) in the range [0, 1] for smooth timing.
        - Provides composition operators (`+`, `|`, `*`) for complex action sequences.
        - Handles edge cases for timing, such as zero duration actions and negative dt values.
    """

    def __init__(self) -> None:
        """Initialize an Action instance with default values."""
        self.target: ActionSprite | None = None  # The ActionSprite this action applies to
        self.elapsed: float = 0.0  # Tracks time since the action started
        self._done: bool = False  # Marks if the action is complete

    def start(self, target: ActionSprite) -> None:
        """
        Initializes the action with a target, preparing it for execution.

        Parameters:
            target (ActionSprite): The ActionSprite this action will affect.

        Sets the target and resets elapsed time and done state, allowing the action
        to begin from a fresh state. This method should be called before `step()` is invoked.
        """
        self.target = target
        self.elapsed = 0.0
        self._done = False

    def step(self, dt: float) -> None:
        """
        Updates the action's progress using delta time (dt).

        Parameters:
            dt (float): Time elapsed since the last frame, in seconds.

        This method accumulates elapsed time and converts it to a normalized time `t`
        (in the range [0, 1]). The `update(t)` method is called with the calculated `t` to
        allow derived classes to implement their specific action behavior.

        Raises:
            ValueError: If dt is negative, which is invalid for action progression.
        """
        if dt < 0:
            raise ValueError("Delta time (dt) must be non-negative.")
        if self.done():
            return
        self.elapsed += dt
        t: float = self._clamp_time(self.elapsed / self.duration())  # Normalizes time for update
        self.update(t)

    def done(self) -> bool:
        """
        Checks if the action is complete.

        Returns:
            bool: True if the action has finished executing, False otherwise.
        """
        return self._done

    def stop(self) -> None:
        """Immediately ends the action, marking it as complete."""
        self._done = True

    def duration(self) -> float:
        """
        Returns the duration of the action in seconds.

        Returns:
            float: The duration of the action. Defaults to 0 for instant actions.

        Derived classes with time-based behaviors should override this method to
        provide the correct duration. Interval actions, for instance, return their
        specified duration, while instant actions typically have a duration of zero.
        """
        return 0  # Default duration for InstantAction

    def update(self, t: float) -> None:
        """
        Performs the action's behavior based on normalized time `t`.

        Parameters:
            t (float): Normalized time, ranging from 0 (start) to 1 (end).

        This method should be overridden by derived classes to implement the specific
        action logic. The normalized `t` parameter allows frame-rate independent
        updates by indicating the action's progress as a percentage.

        Notes:
            Derived classes should avoid directly using elapsed time and should rely
            on `t` for consistent, frame-rate independent updates.
        """
        pass

    def _clamp_time(self, t: float) -> float:
        """
        Ensures the normalized time `t` is clamped to the range [0, 1].

        Parameters:
            t (float): The calculated time value to clamp.

        Returns:
            float: A clamped time value between 0 and 1.

        This method is essential for ensuring time-based actions do not exceed their
        intended range, especially in cases of long dt values or zero duration.
        """
        return max(0, min(1, t))

    def __add__(self, other: Action) -> Sequence:
        """
        Combines actions sequentially, executing one after the other.

        Returns:
            Sequence: A composite action that executes this action followed by `other`.

        This operator overloads the `+` symbol to create a `Sequence` action,
        allowing for easy chaining of actions to run in sequence.
        """
        return Sequence(self, other)

    def __or__(self, other: Action) -> Spawn:
        """
        Combines actions to run in parallel.

        Returns:
            Spawn: A composite action that executes this action and `other` simultaneously.

        This operator overloads the `|` symbol to create a `Spawn` action,
        allowing multiple actions to be executed at the same time.
        """
        return Spawn(self, other)

    def __mul__(self, times: int) -> Repeat:
        """
        Repeats the action a specified number of times.

        Parameters:
            times (int): The number of times to repeat the action.

        Returns:
            Repeat: A composite action that repeats this action the specified number of times.

        Raises:
            ValueError: If `times` is less than 1, as repeating zero times is invalid.

        This operator overloads the `*` symbol, making it easy to repeat actions
        using a multiplication-like syntax.
        """
        if times < 1:
            raise ValueError("Repeat times must be at least 1.")
        return Repeat(self, times)


class ActionSprite(arcade.Sprite):
    """
    An extended Sprite class that supports actions for movement, rotation,
    scaling, and other animations.

    This class manages a list of active actions, updating each one every frame
    based on delta time (dt) to ensure frame-rate independent behavior.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the ActionSprite, inheriting from arcade.Sprite.

        All standard Sprite initialization parameters are passed through.
        """
        super().__init__(*args, **kwargs)
        self.actions: list[Action] = []  # List of active actions on the sprite

    def do(self, action: Action) -> None:
        """
        Start an action on this sprite.

        Parameters:
            action (Action): The action to be executed on the sprite.

        The action is added to the list of active actions and initialized with
        this sprite as its target.
        """
        action.start(self)
        self.actions.append(action)

    def update(self, dt: float) -> None:
        """
        Update all active actions with the given delta time (dt).

        Parameters:
            dt (float): Time elapsed since the last frame, in seconds.

        Advances each action by dt. Completed actions are automatically removed.
        """
        # Filter out completed actions while updating each one
        active_actions = []
        for action in self.actions:
            action.step(dt)
            if not action.done():
                active_actions.append(action)
        self.actions = active_actions

    def remove_action(self, action: Action) -> None:
        """
        Stop and remove a specified action from this sprite.

        Parameters:
            action (Action): The action to be removed.

        If the action is active, it is stopped and removed from the list.
        """
        if action in self.actions:
            action.stop()
            self.actions.remove(action)

    def clear_actions(self) -> None:
        """Stop and remove all actions from this sprite."""
        for action in self.actions:
            action.stop()
        self.actions.clear()


class Sequence(Action):
    """
    A composite action that executes multiple actions in sequence.

    Moves to the next action only when the current action is completed.
    Sequence completes when all actions in the list have been executed.

    Attributes:
        actions (List[Action]): List of actions to be executed in order.
        current_action (Optional[Action]): The action currently being executed.
        current_index (int): Index of the current action in the sequence.
    """

    def __init__(self, *actions: Action) -> None:
        """Initialize with a list of actions to execute in sequence."""
        super().__init__()
        self.actions: list[Action] = list(actions)
        self.current_action: Action | None = None
        self.current_index: int = 0

    def start(self, target: arcade.Sprite) -> None:
        """
        Initialize each action in sequence and start the first action.

        Parameters:
            target (arcade.Sprite): The sprite or target object for the action.
        """
        super().start(target)
        for action in self.actions:
            action.start(target)
        self._advance_to_next_action()

    def step(self, dt: float) -> None:
        """
        Advance the current action, moving to the next when done.

        Parameters:
            dt (float): Delta time since the last frame.
        """
        if self.done():
            return
        if self.current_action:
            self.current_action.step(dt)
            if self.current_action.done():
                self._advance_to_next_action()

    def _advance_to_next_action(self) -> None:
        """
        Move to the next action in the sequence or mark the sequence as done
        if all actions have been completed.
        """
        if self.current_index < len(self.actions):
            self.current_action = self.actions[self.current_index]
            self.current_index += 1
        else:
            self._done = True

    def stop(self) -> None:
        """Stop the current action and end the sequence early."""
        if self.current_action:
            self.current_action.stop()
        self._done = True


class Spawn(Action):
    """
    A composite action that runs multiple actions in parallel.

    Completes only when all child actions have finished executing.

    Attributes:
        actions (List[Action]): List of actions to run in parallel.
        active_actions (List[Action]): List of currently active actions.
    """

    def __init__(self, *actions: Action) -> None:
        """Initialize with a list of actions to run in parallel."""
        super().__init__()
        self.actions: list[Action] = list(actions)
        self.active_actions: list[Action] = list(actions)

    def start(self, target: arcade.Sprite) -> None:
        """
        Initialize all actions to run in parallel.

        Parameters:
            target (arcade.Sprite): The sprite or target object for the action.
        """
        super().start(target)
        for action in self.active_actions:
            action.start(target)

    def step(self, dt: float) -> None:
        """
        Advance each active action, removing it when done.

        Parameters:
            dt (float): Delta time since the last frame.
        """
        if self.done():
            return
        still_active: list[Action] = []
        for action in self.active_actions:
            action.step(dt)
            if not action.done():
                still_active.append(action)
        self.active_actions = still_active
        if not self.active_actions:
            self._done = True

    def stop(self) -> None:
        """Stop all actions and mark the spawn as done."""
        for action in self.active_actions:
            action.stop()
        self._done = True


class Repeat(Action):
    """
    A composite action that repeats another action a specified number of times.

    Can repeat indefinitely if `times` is set to None.

    Attributes:
        action (Action): The action to be repeated.
        times (Optional[int]): Number of times to repeat the action. Infinite if None.
        current_count (int): Counter for the number of repetitions completed.
    """

    def __init__(self, action: Action, times: int | None = None) -> None:
        """
        Initialize with an action to repeat and an optional repeat count.

        Parameters:
            action (Action): The action to be repeated.
            times (Optional[int]): The number of times to repeat the action.
        """
        super().__init__()
        self.action: Action = action
        self.times: int = times if times is not None else float("inf")
        self.current_count: int = 0

    def start(self, target: arcade.Sprite) -> None:
        """
        Initialize the repeated action and start it.

        Parameters:
            target (arcade.Sprite): The sprite or target object for the action.
        """
        super().start(target)
        self.current_count = 0
        self.action.start(target)

    def step(self, dt: float) -> None:
        """
        Advance the action, restarting it if necessary, until repetitions are done.

        Parameters:
            dt (float): Delta time since the last frame.
        """
        if self.done():
            return
        self.action.step(dt)
        if self.action.done():
            self.current_count += 1
            if self.current_count >= self.times:
                self._done = True
            else:
                self.action.start(self.target)  # Restart the action

    def stop(self) -> None:
        """Stop the action and mark the repeat as done."""
        self.action.stop()
        self._done = True


class InstantAction(Action):
    """
    Base class for instant actions that complete immediately upon being started.
    """

    def step(self, dt: float) -> None:
        """
        Execute the action immediately and mark it as done.

        Parameters:
            dt (float): Time elapsed since the last frame (not used here).
        """
        if not self.done():
            self.update(1)  # Immediate completion
            self._done = True
