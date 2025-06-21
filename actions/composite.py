"""
Composite actions that combine other actions.
"""

from .base import Action, IntervalAction
from .move import CompositeAction


def sequence(action_1: Action, action_2: Action) -> "Sequence":
    """Returns an action that runs first action_1 and then action_2.

    The returned action will be a Sequence that performs action_1 followed by action_2.
    Both actions are cloned to ensure independence.

    Args:
        action_1: The first action to execute
        action_2: The second action to execute

    Returns:
        A new Sequence action that runs action_1 followed by action_2
    """
    return Sequence(action_1.clone(), action_2.clone())


def spawn(action_1: Action, action_2: Action) -> "Spawn":
    """Returns an action that runs action_1 and action_2 in parallel.

    The returned action will be a Spawn that performs both actions simultaneously.
    Both actions are cloned to ensure independence.

    Args:
        action_1: The first action to execute in parallel
        action_2: The second action to execute in parallel

    Returns:
        A new Spawn action that runs both actions simultaneously
    """
    return Spawn(action_1.clone(), action_2.clone())


def loop(action: Action, times: int) -> "Loop":
    """Returns an action that repeats another action a specified number of times.

    The returned action will be a Loop that repeats the given action the specified
    number of times. The action is cloned to ensure independence.

    Args:
        action: The action to repeat
        times: Number of times to repeat the action

    Returns:
        A new Loop action that repeats the given action
    """
    return Loop(action.clone(), times)


def repeat(action: Action, times: int) -> "Repeat":
    """Returns an action that repeats another action a specified number of times.

    The returned action will be a Repeat that repeats the given action the specified
    number of times. The action is copied to ensure independence.

    Args:
        action: The action to repeat
        times: Number of times to repeat the action

    Returns:
        A new Repeat action that repeats the given action
    """
    return Repeat(action, times)


class Loop(IntervalAction):
    """Repeats an action a specified number of times."""

    def __init__(self, action: Action, times: int):
        """Initialize a Loop action.

        Args:
            action: The action to repeat
            times: Number of times to repeat the action
        """
        # Numeric validation (avoid fragile isinstance checks)
        if type(times) is not int:
            raise TypeError("times must be an integer")  # Ensures predictable behaviour
        if times < 1:
            raise ValueError("times must be at least 1")

        # Calculate total duration based on action's duration. If the wrapped action
        # has a zero duration (instant action), we propagate `None` to indicate
        # an indeterminate total duration consistent with previous behaviour and
        # existing tests.
        total_duration = action.duration * times if action.duration > 0 else None

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

    def clone(self) -> "Loop":
        """Create a copy of this Loop action."""
        return Loop(self.action.clone(), self.times)

    def __repr__(self) -> str:
        return f"Loop(action={self.action}, times={self.times})"


class Sequence(CompositeAction, IntervalAction):
    """Run a sequence of actions one after another.

    This action runs each sub-action in order, waiting for each to complete
    before starting the next one.
    """

    def __init__(self, *actions: Action):
        # Allow empty sequences - they complete immediately
        if not actions:
            CompositeAction.__init__(self)
            IntervalAction.__init__(self, 0.0)  # No duration for empty sequence
            self.actions = []
            self.current_action = None
            self.current_index = 0
            return

        # Calculate total duration (all actions guarantee a duration attribute).
        total_duration = sum(action.duration for action in actions)

        CompositeAction.__init__(self)
        IntervalAction.__init__(self, total_duration)

        self.actions = list(actions)
        self.current_action = None
        self.current_index = 0

    def start(self) -> None:
        """Start the sequence by starting the first action."""
        super().start()
        if self.actions:
            self.current_index = 0
            self.current_action = self.actions[0]
            self.current_action.target = self.target
            self.current_action.start()
        else:
            # Empty sequence completes immediately
            self.done = True
            self._check_complete()

    def update(self, delta_time: float) -> None:
        """Update the current action and advance to next when done."""
        super().update(delta_time)

        # Handle empty sequence
        if not self.actions:
            if not self.done:
                self.done = True
                self._check_complete()
            return

        # Check if current action is already done (handles manual completion)
        if self.current_action and self.current_action.done:
            self.current_action.stop()
            self.current_index += 1

            # Start next action if available
            if self.current_index < len(self.actions):
                self.current_action = self.actions[self.current_index]
                self.current_action.target = self.target
                self.current_action.start()
            else:
                # All actions complete
                self.current_action = None
                self.done = True
                self._check_complete()
                return

        # Update current action if it's not done
        if self.current_action and not self.current_action.done:
            self.current_action.update(delta_time)

            # Check if current action is done after update
            if self.current_action.done:
                self.current_action.stop()
                self.current_index += 1

                # Start next action if available
                if self.current_index < len(self.actions):
                    self.current_action = self.actions[self.current_index]
                    self.current_action.target = self.target
                    self.current_action.start()
                else:
                    # All actions complete
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

    def clone(self) -> "Sequence":
        """Create a copy of this Sequence action."""
        return Sequence(*(action.clone() for action in self.actions))

    def __repr__(self) -> str:
        return f"Sequence(actions={self.actions})"


class Spawn(CompositeAction, IntervalAction):
    """Run multiple actions simultaneously.

    This action starts all sub-actions at the same time and completes when
    all sub-actions have completed.
    """

    def __init__(self, *actions: Action):
        # Allow empty spawn - they complete immediately
        if not actions:
            CompositeAction.__init__(self)
            IntervalAction.__init__(self, 0.0)  # No duration for empty spawn
            self.actions = []
            return

        # Duration is the maximum duration of all actions
        max_duration = max(action.duration for action in actions)

        CompositeAction.__init__(self)
        IntervalAction.__init__(self, max_duration)

        self.actions = list(actions)

    def start(self) -> None:
        """Start all actions simultaneously."""
        super().start()
        if self.actions:
            for action in self.actions:
                action.target = self.target
                action.start()
        else:
            # Empty spawn completes immediately
            self.done = True
            self._check_complete()

    def update(self, delta_time: float) -> None:
        """Update all actions and check for completion."""
        super().update(delta_time)

        # Handle empty spawn
        if not self.actions:
            if not self.done:
                self.done = True
                self._check_complete()
            return

        all_done = True
        for action in self.actions:
            if not action.done:
                action.update(delta_time)
                all_done = False

        if all_done:
            self.done = True
            self._check_complete()

    def stop(self) -> None:
        for action in self.actions:
            action.stop()
        super().stop()

    def reset(self) -> None:
        for action in self.actions:
            action.reset()
        super().reset()

    def clone(self) -> "Spawn":
        """Create a copy of this Spawn action."""
        return Spawn(*(action.clone() for action in self.actions))

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

    def clone(self) -> "Repeat":
        """Create a copy of this Repeat action."""
        return Repeat(self.action.clone(), self.times)

    def __repr__(self) -> str:
        return f"Repeat(action={self.action}, times={self.times})"
