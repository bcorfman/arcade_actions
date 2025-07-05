"""
Composite actions that combine other actions.
"""

from .base import Action, CompositeAction


class _Sequence(CompositeAction):
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

        # Start current action if needed
        if self.current_action is None and self.current_index < len(self.actions):
            self.current_action = self.actions[self.current_index]
            self.current_action.target = self.target
            self.current_action.start()

        # Update current action if it exists and isn't done
        if self.current_action and not self.current_action.done:
            self.current_action.update(delta_time)

        # Check if current action completed after update
        if self.current_action and self.current_action.done:
            # Don't call stop() - let the action complete naturally
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

    def clone(self) -> "_Sequence":
        """Create a copy of this _Sequence action."""
        return _Sequence(*(action.clone() for action in self.actions))

    def __repr__(self) -> str:
        actions_repr = ", ".join(repr(a) for a in self.actions)
        return f"_Sequence(actions=[{actions_repr}])"


class _Parallel(CompositeAction):
    """Run multiple actions simultaneously.

    This action starts all sub-actions at the same time and completes when
    all sub-actions have completed.
    """

    def __init__(self, *actions: Action):
        # Allow empty parallel - they complete immediately
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
            # Empty parallel completes immediately
            self.done = True
            self._check_complete()

    def update(self, delta_time: float) -> None:
        """Update all actions and check for completion."""
        super().update(delta_time)

        # Handle empty parallel
        if not self.actions:
            if not self.done:
                self.done = True
                self._check_complete()
            return

        # Update all actions that aren't done yet
        for action in self.actions:
            if not action.done:
                action.update(delta_time)

        # Then check if all are done
        all_done = True
        for action in self.actions:
            if not action.done:
                all_done = False
                break

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

    def clone(self) -> "_Parallel":
        """Create a copy of this _Parallel action."""
        return _Parallel(*(action.clone() for action in self.actions))

    def __repr__(self) -> str:
        actions_repr = ", ".join(repr(a) for a in self.actions)
        return f"_Parallel(actions=[{actions_repr}])"


def sequence(*actions: Action) -> _Sequence:
    """Create a sequence that runs actions one after another.

    Args:
        *actions: Actions to run in sequence

    Returns:
        Sequence action that runs each action in order

    Example:
        seq = sequence(
            MoveUntil((100, 0), time_elapsed(2.0)),
            RotateUntil(90, time_elapsed(1.0)),
            FadeUntil(-50, time_elapsed(1.5))
        )
        seq.apply(sprite, tag="complex_movement")
    """
    return _Sequence(*actions)


def parallel(*actions: Action) -> _Parallel:
    """Create a parallel composition that runs actions simultaneously.

    Args:
        *actions: Actions to run in parallel

    Returns:
        Parallel action that runs all actions at the same time

    Example:
        par = parallel(
            MoveUntil((50, 25), time_elapsed(3.0)),
            FadeUntil(-30, time_elapsed(2.0)),
            RotateUntil(180, time_elapsed(3.0))
        )
        par.apply(sprite, tag="multi_effect")
    """
    return _Parallel(*actions)
