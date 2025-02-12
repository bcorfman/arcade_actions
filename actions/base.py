from __future__ import annotations

import copy
from typing import Any


class Action:
    """Base class for all actions."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.duration = None
        self.init(*args, **kwargs)
        self.target = None
        self._elapsed = 0.0
        self._done = False
        self.scheduled_to_remove = False

    def init(self, *args: Any, **kwargs: Any) -> None:
        """Hook for subclasses to initialize with custom parameters."""
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        self.target = None

    def step(self, dt: float) -> None:
        self._elapsed += dt

    def done(self) -> bool:
        return self._done

    def __add__(self, action: Action) -> Action:
        return sequence(self, action)

    def __mul__(self, other: int) -> Action:
        if not isinstance(other, int):
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        return Loop_Action(self, other)

    def __or__(self, action: Action) -> Action:
        return spawn(self, action)

    def __reversed__(self) -> Action:
        raise Exception(f"Action {self.__class__.__name__} cannot be reversed")


class IntervalAction(Action):
    """Base class for actions with fixed duration."""

    def step(self, dt: float) -> None:
        """
        Don't customize this method: it will not be called when in the component
        role for certain composite actions (like Sequence_IntervalAction).
        In such situation the composite will calculate the suitable t and
        directly call .update(t)
        You customize the action stepping by overriding .update
        """
        self._elapsed += dt
        try:
            self.update(min(1, self._elapsed / self.duration))
        except ZeroDivisionError:
            self.update(1.0)

    def update(self, t: float) -> None:
        """Gets called on every frame
        't' is the time elapsed normalized to [0, 1]
        If this action takes 5 seconds to execute, `t` will be equal to 0
        at 0 seconds. `t` will be 0.5 at 2.5 seconds and `t` will be 1 at 5sec.
        This method must not use self._elapsed, which is not guaranted to be
        updated.
        """
        pass

    def done(self) -> bool:
        """
        When in the worker role, this method is reliable.
        When in the component role, if the composite spares the call to
        step this method cannot be relied (an then the composite must decide
        by itself when the action is done).
        Example of later situation is Sequence_IntervalAction.
        """
        return self._elapsed >= self.duration

    def __mul__(self, other: int) -> IntervalAction:
        if not isinstance(other, int):
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        return Loop_IntervalAction(self, other)


class InstantAction(IntervalAction):
    """
    Instant actions are actions that promises to do nothing when the
    methods step, update, and stop are called.
    Any changes that the action must perform on his target will be done in the
    .start() method
    The interface must be keept compatible with IntervalAction to allow the
    basic operators to combine an InstantAction with an IntervalAction and
    give an IntervalAction as a result.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.duration = 0.0

    def step(self, dt: float) -> None:
        pass

    def update(self, t: float) -> None:
        pass

    def done(self) -> bool:
        return True


class MoveTo(IntervalAction):
    """Moves a sprite to an absolute position."""

    def init(self, position: tuple[float, float], duration: float = 5.0) -> None:
        """Initialize MoveTo action."""
        self.position = position
        self.duration = duration

        # Validate parameters
        if position is None:
            raise ValueError("Position cannot be None")
        if not isinstance(position, (tuple, list)) or len(position) != 2:
            raise ValueError("Position must be a tuple of (x, y) coordinates")
        if not all(isinstance(coord, (int, float)) for coord in position):
            raise ValueError("Position coordinates must be numeric")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

    def start(self) -> None:
        """Initialize movement by storing start position."""
        if self.target is None:
            raise AttributeError("Target cannot be None")
        self._start_pos = (self.target.center_x, self.target.center_y)
        self._delta = (self.position[0] - self._start_pos[0], self.position[1] - self._start_pos[1])

    def update(self, t: float) -> None:
        """Update position based on elapsed time fraction."""
        x = self._start_pos[0] + self._delta[0] * t
        y = self._start_pos[1] + self._delta[1] * t
        self.target.center = (x, y)

    def __reversed__(self) -> MoveTo:
        """Returns a MoveTo action that returns to the start position."""
        if not hasattr(self, "_start_pos"):
            raise RuntimeError("Cannot reverse MoveTo action before it starts")
        return MoveTo(self._start_pos, self.duration)


class MoveBy(MoveTo):
    """Moves a sprite by a relative offset."""

    def init(self, delta: tuple[float, float], duration: float = 5.0) -> None:
        """Initialize MoveBy action."""
        self.delta = delta
        self.duration = duration

        # Validate parameters
        if delta is None:
            raise ValueError("Delta cannot be None")
        if not isinstance(delta, (tuple, list)) or len(delta) != 2:
            raise ValueError("Delta must be a tuple of (dx, dy) coordinates")
        if not all(isinstance(d, (int, float)) for d in delta):
            raise ValueError("Delta values must be numeric")
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

    def start(self) -> None:
        """Initialize movement by storing start position."""
        if self.target is None:
            raise AttributeError("Target cannot be None")
        self._start_pos = (self.target.center_x, self.target.center_y)
        self.position = (self._start_pos[0] + self.delta[0], self._start_pos[1] + self.delta[1])

    def __reversed__(self) -> MoveBy:
        """Returns a MoveBy action with negated delta."""
        return MoveBy((-self.delta[0], -self.delta[1]), self.duration)


class RotateBy(IntervalAction):
    """Rotates a sprite by a relative angle."""

    def init(self, angle: float, duration: float) -> None:
        """Initialize RotateBy action."""
        self.angle = angle
        self.duration = duration

        if duration < 0:
            raise ValueError(f"Duration must be non-negative, got {duration}")

    def start(self) -> None:
        """Store initial rotation."""
        if self.target is None:
            raise AttributeError("Target cannot be None")
        self._start_angle = self.target.angle

    def update(self, t: float) -> None:
        """Update rotation based on elapsed time fraction."""
        new_angle = (self._start_angle + (self.angle * t)) % 360
        self.target.angle = new_angle

    def __reversed__(self) -> RotateBy:
        """Returns a RotateBy action with negated angle."""
        return RotateBy(-self.angle, self.duration)


class Loop_Action(Action):
    """Repeats an action n times."""

    def init(self, action: Action, times: int) -> None:
        self.original = action
        self.times = times
        self.current_action = None

    def start(self) -> None:
        self.current_action = copy.deepcopy(self.original)
        self.current_action.target = self.target
        self.current_action.start()

    def step(self, dt: float) -> None:
        self._elapsed += dt
        self.current_action.step(dt)
        if self.current_action.done():
            self.current_action.stop()
            self.times -= 1
            if self.times == 0:
                self._done = True
            else:
                self.current_action = copy.deepcopy(self.original)
                self.current_action.target = self.target
                self.current_action.start()


class Loop_Action(Action):
    """Repeats one Action for n times"""

    def init(self, one: Action, times: int) -> None:
        """Initialize the loop action.

        Args:
            one: The action to repeat
            times: Number of times to repeat the action
        """
        self.one = one
        self.times = times
        self.current_action: Action | None = None

    def start(self) -> None:
        """Start the loop by creating and starting first action copy"""
        self.current_action = copy.deepcopy(self.one)
        self.current_action.target = self.target
        self.current_action.start()

    def step(self, dt: float) -> None:
        """Update current action and handle transitions between repetitions.

        Args:
            dt: Time elapsed since last frame in seconds
        """
        self._elapsed += dt
        assert self.current_action is not None
        self.current_action.step(dt)
        if self.current_action.done():
            self.current_action.stop()
            self.times -= 1
            if self.times == 0:
                self._done = True
            else:
                self.current_action = copy.deepcopy(self.one)
                self.current_action.target = self.target
                self.current_action.start()

    def stop(self) -> None:
        """Stop the current action if not already done"""
        if not self._done and self.current_action is not None:
            self.current_action.stop()


class Loop_InstantAction(InstantAction):
    """Repeats one InstantAction for n times

    All repetitions are performed immediately during the start() call,
    maintaining the "instant" nature of the action.
    """

    def init(self, one: InstantAction, times: int) -> None:
        """Initialize the loop instant action.

        Args:
            one: The instant action to repeat
            times: Number of times to repeat the action
        """
        self.one = one
        self.times = times

    def start(self) -> None:
        """Execute all repetitions of the action immediately."""
        for _ in range(self.times):
            cpy = copy.deepcopy(self.one)
            cpy.target = self.target  # Need to set target for each copy
            cpy.start()


class Loop_IntervalAction(IntervalAction):
    """Repeats an interval action n times."""

    def init(self, action: IntervalAction, times: int) -> None:
        self.original = action
        self.times = times

        if not hasattr(self.original, "duration"):
            raise Exception("Can only loop actions with finite duration")

        self.duration = self.original.duration * times
        self.current_action = None
        self.current = None
        self.last = None

    def start(self) -> None:
        self.last = 0
        self.current_action = copy.deepcopy(self.original)
        self.current_action.target = self.target
        self.current_action.start()

    def update(self, t: float) -> None:
        current = int(t * self.times)
        new_t = (t - (current * (1.0 / self.times))) * self.times

        if current >= self.times:
            return
        elif current == self.last:
            self.current_action.update(new_t)
        else:
            self.current_action.update(1.0)
            self.current_action.stop()

            for i in range(self.last + 1, current):
                temp = copy.deepcopy(self.original)
                temp.target = self.target
                temp.start()
                temp.update(1.0)
                temp.stop()

            self.current_action = copy.deepcopy(self.original)
            self.current_action.target = self.target
            self.last = current
            self.current_action.start()
            self.current_action.update(new_t)


def sequence(action_1: Action, action_2: Action) -> Action:
    """Returns an action that runs action_1 and then action_2."""
    if isinstance(action_1, InstantAction) and isinstance(action_2, InstantAction):
        return Sequence_InstantAction(action_1, action_2)
    elif isinstance(action_1, IntervalAction) and isinstance(action_2, IntervalAction):
        return Sequence_IntervalAction(action_1, action_2)
    return Sequence_Action(action_1, action_2)


class Sequence_Action(Action):
    """Implements sequence for actions that can't be expressed as IntervalAction.
    At least one operand must have duration == None"""

    def init(self, one: Action, two: Action, **kwargs) -> None:
        """Initialize sequence with two actions."""
        self.one = copy.deepcopy(one)
        self.two = copy.deepcopy(two)
        self.first = True
        self.current_action = None

    def start(self) -> None:
        """Start the sequence by initializing both actions."""
        self.one.target = self.target
        self.two.target = self.target
        self.current_action = self.one
        self.current_action.start()

    def step(self, dt: float) -> None:
        """Update current action and handle transition between actions."""
        self._elapsed += dt
        self.current_action.step(dt)
        if self.current_action.done():
            self._next_action()

    def _next_action(self) -> None:
        """Handle transition to next action in sequence."""
        self.current_action.stop()
        if self.first:
            self.first = False
            self.current_action = self.two
            self.current_action.start()
            if self.current_action.done():
                self._done = True
        else:
            self.current_action = None
            self._done = True

    def stop(self) -> None:
        """Stop the current action if one is active."""
        if self.current_action:
            self.current_action.stop()

    def __reversed__(self) -> Sequence_Action:
        """Return a reversed version of this sequence."""
        return sequence(Reverse(self.two), Reverse(self.one))


class Sequence_InstantAction(InstantAction):
    """Implements sequence for InstantActions;
    both operands must be InstantActions."""

    def init(self, one: InstantAction, two: InstantAction, **kwargs) -> None:
        """Initialize sequence with two instant actions."""
        self.one = copy.deepcopy(one)
        self.two = copy.deepcopy(two)

    def start(self) -> None:
        """Execute both actions immediately in sequence."""
        self.one.target = self.target
        self.two.target = self.target
        self.one.start()
        self.two.start()

    def __reversed__(self) -> Sequence_InstantAction:
        """Return a reversed version of this sequence."""
        return Sequence_InstantAction(Reverse(self.two), Reverse(self.one))


class Sequence_IntervalAction(IntervalAction):
    """Implements sequence for IntervalActions."""

    def init(self, one: IntervalAction, two: IntervalAction) -> None:
        """Initialize sequence with two interval actions."""
        self.one = copy.deepcopy(one)
        self.two = copy.deepcopy(two)
        self.actions = [self.one, self.two]

        if not hasattr(self.one, "duration") or not hasattr(self.two, "duration"):
            raise Exception("Can only sequence actions with finite duration, not repeats or others like that")

        self.duration = float(self.one.duration + self.two.duration)
        try:
            self.split = self.one.duration / self.duration
        except ZeroDivisionError:
            self.split = 0.0
        self.last = None

    def start(self) -> None:
        """Start the sequence."""
        self.one.target = self.target
        self.two.target = self.target
        self.one.start()
        self.last = 0  # index in self.actions
        if self.one.duration == 0.0:
            self.one.update(1.0)
            self.one.stop()
            self.two.start()
            self.last = 1

    def __repr__(self):
        return "( %s + %s )" % (self.one, self.two)

    def update(self, t: float) -> None:
        """Update the sequence based on normalized time."""
        current = t >= self.split
        if current != self.last:
            self.actions[self.last].update(1.0)
            self.actions[self.last].stop()
            self.last = current
            self.actions[self.last].start()
        if not current:
            try:
                sub_t = t / self.split
            except ZeroDivisionError:
                sub_t = 1.0
        else:
            try:
                sub_t = (t - self.split) / (1.0 - self.split)
            except ZeroDivisionError:
                sub_t = 1.0
        self.actions[current].update(sub_t)

    def stop(self) -> None:
        """Stop the currently active action."""
        if self.last:
            self.two.stop()
        else:
            self.one.stop()

    def __reversed__(self) -> Sequence_IntervalAction:
        """Return a reversed version of this sequence."""
        return Sequence_IntervalAction(Reverse(self.two), Reverse(self.one))


def spawn(action_1: Action, action_2: Action) -> Action:
    """Returns an action that runs action_1 and action_2 in parallel.
    The returned action will be instance of the most narrow class
    possible in InstantAction, IntervalAction, Action"""
    if isinstance(action_1, InstantAction) and isinstance(action_2, InstantAction):
        cls = Spawn_InstantAction
    elif isinstance(action_1, IntervalAction) and isinstance(action_2, IntervalAction):
        cls = Spawn_IntervalAction
    else:
        cls = Spawn_Action
    return cls(action_1, action_2)


class Spawn_Action(Action):
    """Implements spawn for actions that can't be expressed as IntervalAction.
    At least one operand must have duration==None"""

    def init(self, one: Action, two: Action) -> None:
        """Initialize spawn with two actions."""
        one = copy.deepcopy(one)
        two = copy.deepcopy(two)
        self.actions = [one, two]

    def start(self) -> None:
        """Start all actions in parallel."""
        for action in self.actions:
            action.target = self.target
            action.start()

    def step(self, dt: float) -> None:
        """Update all active actions."""
        if len(self.actions) == 2:
            self.actions[0].step(dt)
            if self.actions[0].done():
                self.actions[0].stop()
                self.actions = self.actions[1:]
        if self.actions:
            self.actions[-1].step(dt)
            if self.actions[-1].done():
                self.actions[-1].stop()
                self.actions = self.actions[:-1]
        self._done = len(self.actions) == 0

    def stop(self) -> None:
        """Stop all active actions."""
        for action in self.actions:
            action.stop()

    def __reversed__(self) -> Spawn_Action:
        """Return a reversed version of this spawn."""
        return Reverse(self.actions[0]) | Reverse(self.actions[1])


class Spawn_InstantAction(InstantAction):
    """Implements spawn for InstantActions."""

    def init(self, one: InstantAction, two: InstantAction) -> None:
        """Initialize spawn with two instant actions."""
        one = copy.deepcopy(one)
        two = copy.deepcopy(two)
        self.actions = [one, two]

    def start(self) -> None:
        """Execute all actions immediately in parallel."""
        for action in self.actions:
            action.target = self.target
            action.start()


class Spawn_IntervalAction(IntervalAction):
    """Implements spawn for IntervalActions."""

    def init(self, one: IntervalAction, two: IntervalAction) -> None:
        """Initialize spawn with two interval actions."""
        from .interval import Delay  # Import here to avoid circular dependency

        one = copy.deepcopy(one)
        two = copy.deepcopy(two)
        self.duration = max(one.duration, two.duration)

        # Pad shorter action with Delay to match durations
        if one.duration > two.duration:
            two = two + Delay(one.duration - two.duration)
        elif two.duration > one.duration:
            one = one + Delay(two.duration - one.duration)

        self.actions = [one, two]

    def start(self) -> None:
        """Start all actions in parallel."""
        for action in self.actions:
            action.target = self.target
            action.start()

    def update(self, t: float) -> None:
        """Update all actions with same time fraction."""
        self.actions[0].update(t)
        self.actions[1].update(t)
        self._done = t >= 1.0
        if self._done:
            self.actions[0].stop()
            self.actions[1].stop()

    def __reversed__(self) -> Spawn_IntervalAction:
        """Return a reversed version of this spawn."""
        return Reverse(self.actions[0]) | Reverse(self.actions[1])


def Reverse(action: Action) -> Action:
    """Returns a reversed version of the action.
    Example::

    # rotates the sprite 180 degrees in 2 seconds counter clockwise
    action = Reverse( RotateBy( 180, 2 ) )
    sprite.do( action )"""
    return action.__reversed__()


class _ReverseTime(IntervalAction):
    """Helper class to execute an action in reverse order."""

    def init(self, other: IntervalAction, *args: Any, **kwargs: Any) -> None:
        """Initialize with the action to reverse."""
        super(_ReverseTime, self).init(*args, **kwargs)
        self.other = other
        self.duration = self.other.duration

    def start(self) -> None:
        """Start both this action and the other action."""
        self.other.target = self.target
        super(_ReverseTime, self).start()
        self.other.start()

    def update(self, t: float) -> None:
        """Update the other action with reversed time."""
        self.other.update(1 - t)

    def __reversed__(self) -> IntervalAction:
        """Return the original action."""
        return self.other
