"""
Composite actions that combine other actions.
"""

import copy

from .base import Action, IntervalAction


def _safe_copy_action(action: Action) -> Action:
    """Create a safe copy of an action that avoids deepcopy issues with callbacks."""
    # Import here to avoid circular imports
    from .move import BoundedMove, WrappedMove

    # Handle specific action types that might have callback issues
    if isinstance(action, BoundedMove):
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
        # For other actions, try shallow copy first, fall back to creating new instance
        try:
            return copy.copy(action)
        except Exception:
            # If copy fails, create a new instance with same parameters
            return type(action)(**action.__dict__)


def sequence(action_1: Action, action_2: Action) -> "Sequence":
    """Returns an action that runs first action_1 and then action_2.

    The returned action will be a Sequence that performs action_1 followed by action_2.
    Both actions are deepcopied to ensure independence.

    Args:
        action_1: The first action to execute
        action_2: The second action to execute

    Returns:
        A new Sequence action that runs action_1 followed by action_2
    """
    return Sequence(copy.deepcopy(action_1), copy.deepcopy(action_2))


def spawn(action_1: Action, action_2: Action) -> "Spawn":
    """Returns an action that runs action_1 and action_2 in parallel.

    The returned action will be a Spawn that performs both actions simultaneously.
    Both actions are safely copied to ensure independence.

    Args:
        action_1: The first action to execute in parallel
        action_2: The second action to execute in parallel

    Returns:
        A new Spawn action that runs both actions simultaneously
    """
    return Spawn(_safe_copy_action(action_1), _safe_copy_action(action_2))


def loop(action: Action, times: int) -> "Loop":
    """Returns an action that repeats another action a specified number of times.

    The returned action will be a Loop that repeats the given action the specified
    number of times. The action is deepcopied to ensure independence.

    Args:
        action: The action to repeat
        times: Number of times to repeat the action

    Returns:
        A new Loop action that repeats the given action
    """
    return Loop(copy.deepcopy(action), times)


class Loop(IntervalAction):
    """Repeats an action a specified number of times."""

    def __init__(self, action: Action, times: int):
        """Initialize a Loop action.

        Args:
            action: The action to repeat
            times: Number of times to repeat the action
        """
        if not isinstance(times, int):
            raise TypeError("times must be an integer")
        if times < 1:
            raise ValueError("times must be at least 1")

        # Calculate total duration based on action's duration
        if hasattr(action, "duration"):
            total_duration = action.duration * times
        else:
            total_duration = None

        super().__init__(total_duration)
        self.action = action
        self.times = times
        self.current_times = 0
        self._on_complete = None
        self._on_complete_args = ()
        self._on_complete_kwargs = {}
        self._on_complete_called = False

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

    def start(self) -> None:
        """Start the loop action."""
        self.action.target = self.target
        self.action.start()

    def update(self, delta_time: float) -> None:
        """Update the loop action.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if self.action.done:
            self.current_times += 1
            if self.current_times >= self.times:
                self.done = True
                self._check_complete()
            else:
                self.action.reset()
                self.action.start()
        else:
            self.action.update(delta_time)
            # Check if action completed during this update
            if self.action.done:
                self.current_times += 1
                if self.current_times >= self.times:
                    self.done = True
                    self._check_complete()
                else:
                    self.action.reset()
                    self.action.start()

    def stop(self) -> None:
        """Stop the loop action."""
        self.action.stop()
        self._check_complete()
        super().stop()

    def reset(self) -> None:
        """Reset the loop action to its initial state."""
        self.current_times = 0
        self.action.reset()
        self._on_complete_called = False
        super().reset()

    def __repr__(self) -> str:
        return f"Loop(action={self.action}, times={self.times})"


class Sequence(IntervalAction):
    """Run a sequence of actions one after another."""

    def __init__(self, *actions: Action):
        super().__init__(sum(getattr(a, "duration", 0) for a in actions))
        self.actions = list(actions)
        self.current_action: Action | None = None
        self.current_index = 0
        self._on_complete = None
        self._on_complete_args = ()
        self._on_complete_kwargs = {}
        self._on_complete_called = False

    def on_complete(self, func, *args, **kwargs):
        self._on_complete = func
        self._on_complete_args = args
        self._on_complete_kwargs = kwargs
        return self

    def when_done(self, func, *args, **kwargs):
        return self.on_complete(func, *args, **kwargs)

    def _check_complete(self):
        if self.done and self._on_complete and not self._on_complete_called:
            self._on_complete_called = True
            self._on_complete(*self._on_complete_args, **self._on_complete_kwargs)

    def start(self) -> None:
        if self.actions:
            self.current_action = self.actions[0]
            self.current_action.target = self.target
            self.current_action.start()

    def update(self, delta_time: float) -> None:
        if not self.current_action:
            self.done = True
            self._check_complete()
            return

        self.current_action.update(delta_time)

        if self.current_action.done:
            self.current_action.stop()
            self.current_index += 1

            if self.current_index < len(self.actions):
                self.current_action = self.actions[self.current_index]
                self.current_action.target = self.target
                self.current_action.start()
            else:
                self.current_action = None
                self.done = True
                self._check_complete()

    def stop(self) -> None:
        if self.current_action:
            self.current_action.stop()
        self._check_complete()
        super().stop()

    def reset(self) -> None:
        self.current_index = 0
        self.current_action = None
        for action in self.actions:
            action.reset()
        self._on_complete_called = False
        super().reset()

    def __repr__(self) -> str:
        return f"Sequence(actions={self.actions})"


class Spawn(IntervalAction):
    """Run multiple actions in parallel."""

    def __init__(self, *actions: Action):
        self.actions = list(actions)
        # Handle empty action list case
        if not self.actions:
            super().__init__(0)
        else:
            super().__init__(max(getattr(a, "duration", 0) for a in self.actions))
        self._on_complete = None
        self._on_complete_args = ()
        self._on_complete_kwargs = {}
        self._on_complete_called = False

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

    def start(self) -> None:
        for action in self.actions:
            action.target = self.target
            action.start()

    def update(self, delta_time: float) -> None:
        all_done = True
        for action in self.actions:
            if not action.done:
                action.update(delta_time)
                all_done = False
        self.done = all_done
        self._check_complete()

    def stop(self) -> None:
        for action in self.actions:
            action.stop()
        self._check_complete()
        super().stop()

    def reset(self) -> None:
        for action in self.actions:
            action.reset()
        self._on_complete_called = False
        super().reset()

    def __repr__(self) -> str:
        return f"Spawn(actions={self.actions})"


class Repeat(IntervalAction):
    """Repeat an action a number of times."""

    def __init__(self, action: Action = None, times: int = None):
        if action is None:
            raise ValueError("Must specify action")
        if times is None:
            raise ValueError("Must specify times")

        super().__init__(action.duration * times)
        self.action = action
        self.times = times
        self.current_times = 0

    def start(self) -> None:
        self.action.target = self.target
        self.action.start()

    def update(self, delta_time: float) -> None:
        if self.action.done:
            self.current_times += 1
            if self.current_times >= self.times:
                self.done = True
            else:
                self.action.reset()
                self.action.start()
        else:
            self.action.update(delta_time)

    def stop(self) -> None:
        self.action.stop()
        super().stop()

    def reset(self) -> None:
        self.current_times = 0
        self.action.reset()
        super().reset()

    def __repr__(self) -> str:
        return f"Repeat(action={self.action}, times={self.times})"
