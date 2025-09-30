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

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Forward velocity setting to the currently running action."""
        if self.current_action is not None:
            try:
                self.current_action.set_current_velocity(velocity)
            except AttributeError:
                # Current action doesn't support velocity control
                pass

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

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Forward velocity setting to all child actions that support it."""
        for action in self.actions:
            action.set_current_velocity(velocity)

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

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Forward velocity setting to the currently running action."""
        if self.current_action is not None:
            try:
                self.current_action.set_current_velocity(velocity)
            except AttributeError:
                # Current action doesn't support velocity control
                pass

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


class StateMachine(CompositeAction):
    """A minimal predicate-based state switcher for simple animation and behavior states.

    StateMachine is NOT a full graph-based finite state machine with transitions, guards,
    history, or nested states. It's a simple condition-driven action dispatcher that
    evaluates predicates in order each frame and switches to the first matching action.

    This is designed for common game scenarios like idle/walk/die animations, not complex AI.
    For complex AI behaviors, consider using a proper Behavior Tree or full FSM library.

    Key characteristics:
    - Evaluates predicates in order (first match wins)
    - Switches actions when predicates change
    - No explicit transitions or state graph
    - Lightweight and easy to debug
    - Perfect for sprite animation states

    Args:
        states: List of (predicate_function, action_factory) tuples
        debug: When True, prints state transitions to console

    Example:
        # Classic idle/walk/die animation states
        def is_dead(): return sprite.health <= 0
        def is_moving(): return sprite.change_x != 0 or sprite.change_y != 0

        states = [
            (is_dead, lambda: DelayUntil(duration(2.0))),      # Die animation
            (is_moving, lambda: MoveUntil((3, 0), infinite)),  # Walk animation
            (infinite, lambda: DelayUntil(infinite))           # Idle animation (default)
        ]

        state_machine = StateMachine(states)
        state_machine.apply(player_sprite, tag="animation")
    """

    def __init__(
        self,
        states: list[tuple[callable, callable]],
        *,
        debug: bool = False,
    ):
        super().__init__()
        self._states = list(states)
        self._current_action: Action | None = None
        self._current_pred = None
        self._debug = debug

    def start(self) -> None:
        """Start the state machine by evaluating predicates and selecting first match."""
        super().start()
        self._pick_state(first=True)

    def update(self, delta_time: float) -> None:
        """Update current action and re-evaluate predicates for state changes."""
        super().update(delta_time)

        # Update current action if it exists and isn't done
        if self._current_action and not self._current_action.done:
            self._current_action.update(delta_time)

        # Check if current action completed
        if self._current_action and self._current_action.done:
            # Current action completed, try to find a new state
            self._current_action = None
            self._current_pred = None
            self._pick_state()

            # If no new state was found, mark the state machine as complete
            if self._current_action is None:
                self.done = True
                self._check_complete()
                return

        # Re-evaluate predicates to check for state changes (only if still active)
        if not self.done:
            self._pick_state()

    def stop(self) -> None:
        """Stop the state machine and current action."""
        if self._current_action:
            self._current_action.stop()
        super().stop()

    def reset(self) -> None:
        """Reset the state machine to initial state."""
        if self._current_action:
            self._current_action.reset()
        self._current_action = None
        self._current_pred = None
        super().reset()

    def clone(self) -> "StateMachine":
        """Create a copy of this StateMachine with fresh action factories."""
        # Clone the state list with fresh factories that clone their actions
        cloned_states = []
        for pred, factory in self._states:
            # Create a new factory that clones the action from the original factory
            def cloned_factory(original_factory=factory):
                return original_factory().clone()

            cloned_states.append((pred, cloned_factory))

        return StateMachine(cloned_states, debug=self._debug)

    def _pick_state(self, *, first: bool = False) -> None:
        """Evaluate predicates and switch to first matching state."""
        for pred, factory in self._states:
            try:
                if pred():
                    # Check if this is the same predicate as current (avoid unnecessary switches)
                    if pred is self._current_pred and not first:
                        return  # Stay in current state

                    # Switch to new state
                    if self._current_action:
                        self._current_action.stop()

                    self._current_pred = pred
                    self._current_action = factory()
                    self._current_action.target = self.target
                    self._current_action.start()

                    if self._debug:
                        print(f"[StateMachine] --> {self._current_action}")

                    return  # Found matching state, stop evaluating

            except Exception:
                # Re-raise predicate/factory exceptions for debugging
                raise

        # No matching predicates found
        if first:
            # On first evaluation, it's okay to have no matching state
            self._current_action = None
            self._current_pred = None

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Forward velocity setting to the currently active action."""
        if self._current_action is not None:
            try:
                self._current_action.set_current_velocity(velocity)
            except AttributeError:
                # Current action doesn't support velocity control
                pass
