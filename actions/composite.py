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
        self.done = False
        self._on_complete_called = False

    def clone(self) -> "_Parallel":
        """Create a copy of this _Parallel action."""
        return _Parallel(*(action.clone() for action in self.actions))

    def __repr__(self) -> str:
        actions_repr = ", ".join(repr(a) for a in self.actions)
        return f"_Parallel(actions=[{actions_repr}])"


class _Repeat(CompositeAction):
    """Repeat an action indefinitely until explicitly stopped.

    This action clones the given action and runs it repeatedly. When one
    iteration completes, it automatically starts a new iteration with a fresh
    clone of the action.
    """

    def __init__(self, action: Action | None):
        # Allow None action - it completes immediately
        if action is None:
            CompositeAction.__init__(self)
            self.action = None
            self.current_action = None
            return

        CompositeAction.__init__(self)

        self.action = action
        self.current_action = None

    def start(self) -> None:
        """Start the repeat by starting the first iteration."""
        super().start()
        if self.action:
            # Clone the action for the first iteration
            self.current_action = self.action.clone()
            self.current_action.target = self.target
            self.current_action.start()
        else:
            # No action to repeat - complete immediately
            self.done = True
            self._check_complete()

    def update(self, delta_time: float) -> None:
        """Update the current action and restart when done."""

        # ---------------------------------------------------------------
        super().update(delta_time)

        # Handle no action case
        if not self.action:
            if not self.done:
                self.done = True
                self._check_complete()
            return

        # Update current action if it exists and isn't done
        if self.current_action and not self.current_action.done:
            self.current_action.update(delta_time)

        # Check if current action completed after update
        if self.current_action and self.current_action.done:
            # Action finished. Immediately start the next iteration.
            self.current_action = self.action.clone()
            self.current_action.target = self.target
            self.current_action.start()

        # Start current action if needed
        if self.current_action is None:
            self.current_action = self.action.clone()
            self.current_action.target = self.target
            self.current_action.start()

    def stop(self) -> None:
        """Stop the repeat action and the current iteration."""
        if self.current_action:
            self.current_action.stop()
        self.done = True
        self._check_complete()
        super().stop()

    def reset(self) -> None:
        """Reset the repeat action to its initial state."""
        if self.current_action:
            self.current_action.reset()
        self.current_action = None
        self._on_complete_called = False
        super().reset()

    def clone(self) -> "_Repeat":
        """Create a copy of this _Repeat action."""
        return _Repeat(self.action.clone() if self.action else None)

    def __repr__(self) -> str:
        return f"_Repeat(action={repr(self.action)})"


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


def repeat(action: Action) -> _Repeat:
    """Create a repeat composition that runs an action indefinitely.

    Args:
        action: Action to repeat indefinitely

    Returns:
        Repeat action that runs the action repeatedly

    Example:
        # Repeat a single action
        rep = repeat(MoveUntil((50, 0), time_elapsed(1.0)))
        rep.apply(sprite, tag="bouncing_movement")

        # Repeat a composite action (sequence/parallel)
        complex_action = sequence(
            MoveUntil((50, 0), time_elapsed(1.0)),
            MoveUntil((-50, 0), time_elapsed(1.0)),
            RotateUntil(90, time_elapsed(0.5))
        )
        rep = repeat(complex_action)
        rep.apply(sprite, tag="complex_cycle")

        # The action will repeat indefinitely until stopped
    """
    return _Repeat(action)
