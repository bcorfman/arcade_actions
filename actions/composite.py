"""
Composite actions that combine other actions.
"""

from .base import Action, CompositeAction


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


class Sequence(CompositeAction):
    """Run a sequence of actions one after another.

    This action runs each sub-action in order, waiting for each to complete
    before starting the next one.
    """

    def __init__(self, *actions: Action):
        # Allow empty sequences - they complete immediately
        if not actions:
            CompositeAction.__init__(self)
            self.actions = []
            self.current_action = None
            self.current_index = 0
            return

        CompositeAction.__init__(self)

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


class Spawn(CompositeAction):
    """Run multiple actions simultaneously.

    This action starts all sub-actions at the same time and completes when
    all sub-actions have completed.
    """

    def __init__(self, *actions: Action):
        # Allow empty spawn - they complete immediately
        if not actions:
            CompositeAction.__init__(self)
            self.actions = []
            return

        CompositeAction.__init__(self)

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
