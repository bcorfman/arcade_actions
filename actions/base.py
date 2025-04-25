from __future__ import annotations

import copy

import arcade


class Action:
    def __init__(self):
        self.target = None
        self._elapsed = 0.0
        self._done = False

    def start(self, target):
        """Begin the action on a given sprite."""
        self.target = target

    def step(self, delta_time: float):
        """Advance the action by delta time (in seconds)."""
        self._elapsed += delta_time

    def stop(self):
        """Cleanup logic when the action finishes or is cancelled."""
        self.target = None

    def is_done(self) -> bool:
        return self._done

    def reset(self):
        """Resets the action so it can be reused."""
        self._elapsed = 0.0
        self._done = False
        self.target = None

    @property
    def elapsed(self) -> float:
        """Seconds of time accumulated by this action."""
        return self._elapsed

    @property
    def progress(self) -> float:
        """Normalized time progress (0.0 to 1.0)."""
        return 1.0 if not hasattr(self, "duration") or self.duration == 0 else min(self._elapsed / self.duration, 1.0)

    def clone(self) -> Action:
        return copy.deepcopy(self)

    def reverse(self) -> Action:
        return self.__reversed__()

    def __reversed__(self):
        raise NotImplementedError(f"{type(self).__name__} does not support reversal.")

    def __add__(self, other: Action) -> Action:
        from .interval import Sequence

        return Sequence(self, other)

    def __or__(self, other: Action) -> Action:
        from .interval import Spawn

        return Spawn(self, other)

    def __mul__(self, times: int) -> Action:
        from .interval import Repeat

        return Repeat(self, times)

    def __repr__(self):
        return f"<{self.__class__.__name__}(done={self._done}, elapsed={self._elapsed:.2f})>"


class IntervalAction(Action):
    def __init__(self, duration: float):
        super().__init__()
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        self.duration = duration

    def step(self, delta_time: float):
        if self._done:
            return
        self._elapsed += delta_time
        t = self.progress
        self.update(t)
        if self._elapsed >= self.duration:
            self._done = True
            self.stop()

    def update(self, t: float):
        """Override to define normalized behavior (t in [0, 1])."""
        pass

    def stop(self):
        super().stop()


class InstantAction(IntervalAction):
    def __init__(self):
        super().__init__(duration=0)

    def step(self, delta_time: float):
        if not self._done:
            self.update(1.0)
            self._done = True
            self.stop()

    def update(self, t: float):
        pass

    def stop(self):
        super().stop()


class Repeat(IntervalAction):
    def __init__(self, action, times: int):
        if times <= 0:
            raise ValueError("Repeat count must be positive")
        super().__init__(action.duration * times)
        self.original = action
        self.times = times
        self.current_index = 0
        self.current = None

    def start(self, target):
        super().start(target)
        self._start_new_instance()

    def _start_new_instance(self):
        self.current = self.original.clone()
        self.current_index += 1
        self.current.start(self.target)

    def update(self, t: float):
        # Convert normalized time to repeated segment time
        total_time = t * self.duration
        segment_time = total_time % self.original.duration
        expected_index = int(total_time // self.original.duration) + 1

        if expected_index != self.current_index:
            self.current.stop()
            self._start_new_instance()

        self.current._elapsed = segment_time
        self.current.update(min(segment_time / self.original.duration, 1.0))

    def stop(self):
        if self.current:
            self.current.stop()
        super().stop()

    def __reversed__(self):
        return Repeat(reversed(self.original), self.times)


class Loop(Action):
    """Loops an action indefinitely."""

    def __init__(self, action: Action):
        super().__init__()
        self.inner_action = action

    def start(self, target):
        super().start(target)
        self.inner_action.start(target)

    def update(self, dt: float):
        self.inner_action.update(dt)
        if self.inner_action.is_done():
            self.inner_action = self.inner_action.clone()
            self.inner_action.start(self.target)


class Sequence(IntervalAction):
    def __init__(self, a, b):
        duration = a.duration + b.duration
        super().__init__(duration)
        self.a = a.clone()
        self.b = b.clone()
        self.split = a.duration / duration
        self.last_active = None

    def start(self, target):
        super().start(target)
        self.a.start(target)
        self.last_active = self.a

    def update(self, t: float):
        if t < self.split:
            sub_t = t / self.split if self.split > 0 else 1.0
            self.last_active = self.a
            self.a.update(sub_t)
        else:
            if self.last_active is self.a:
                self.a.stop()
                self.b.start(self.target)
            sub_t = (t - self.split) / (1 - self.split) if self.split < 1 else 1.0
            self.last_active = self.b
            self.b.update(sub_t)

    def stop(self):
        if self.last_active:
            self.last_active.stop()
        super().stop()

    def __reversed__(self):
        return Sequence(reversed(self.b), reversed(self.a))


class Spawn(IntervalAction):
    def __init__(self, a, b):
        duration = max(a.duration, b.duration)
        super().__init__(duration)
        self.a = a.clone()
        self.b = b.clone()

    def start(self, target):
        super().start(target)
        self.a.start(target)
        self.b.start(target)

    def update(self, t: float):
        self.a.update(min(t * self.duration / self.a.duration, 1.0) if self.a.duration > 0 else 1.0)
        self.b.update(min(t * self.duration / self.b.duration, 1.0) if self.b.duration > 0 else 1.0)

    def stop(self):
        self.a.stop()
        self.b.stop()
        super().stop()

    def __reversed__(self):
        return Spawn(reversed(self.a), reversed(self.b))


class ReverseTime(IntervalAction):
    def __init__(self, action: IntervalAction):
        super().__init__(action.duration)
        self.reversed_action = action

    def start(self, target):
        super().start(target)
        self.reversed_action.start(target)

    def step(self, t: float):
        self.reversed_action.step(1.0 - t)


# Glue functions
def sequence(*actions: Action | list[Action]) -> Action:
    flat: list[Action] = []
    for action in actions:
        if isinstance(action, Sequence):
            flat.extend([action.a, action.b])
        elif isinstance(action, (list, tuple)):
            flat.extend(action)
        elif isinstance(action, Action):
            flat.append(action)
        else:
            raise TypeError(f"Invalid action: {action}")

    if len(flat) == 0:
        raise ValueError("sequence() requires at least one action")
    if len(flat) == 1:
        return flat[0]

    result = flat[0]
    for next_action in flat[1:]:
        result = Sequence(result, next_action)
    return result


def spawn(*actions: Action | list[Action]) -> Action:
    flat: list[Action] = []
    for action in actions:
        if isinstance(action, Spawn):
            flat.extend([action.a, action.b])
        elif isinstance(action, (list, tuple)):
            flat.extend(action)
        elif isinstance(action, Action):
            flat.append(action)
        else:
            raise TypeError(f"Invalid action: {action}")

    if len(flat) == 0:
        raise ValueError("spawn() requires at least one action")
    if len(flat) == 1:
        return flat[0]

    result = flat[0]
    for next_action in flat[1:]:
        result = Spawn(result, next_action)
    return result


# Action integration with Arcade
class ArcadePropertyDefaultsMixin:
    def apply_arcade_defaults(self):
        defaults = {
            "center_x": 0.0,
            "center_y": 0.0,
            "angle": 0.0,
            "scale": 1.0,
            "alpha": 255,
            "velocity": (0.0, 0.0),
            "visible": True,
        }
        for attr, default in defaults.items():
            if not hasattr(self, attr):
                setattr(self, attr, default)


class Actionable:
    def __init__(self):
        self.actions: list[Action] = []

    def do(self, action: Action):
        action = action.clone()
        action.start(self)
        self.actions.append(action)

    def update(self, delta_time: float):
        for action in self.actions[:]:
            action.update(delta_time)
            if action.is_done():
                self.remove_action(action)

    def remove_action(self, action: Action):
        if action in self.actions:
            self.actions.remove(action)


class ActionSprite(arcade.Sprite):
    """A sprite that supports time-based Actions like MoveBy, RotateBy, etc."""

    def __init__(self, filename: str, scale: float = 1.0):
        super().__init__(filename, scale)
        self._actions: list[Action] = []

    def do(self, action: Action):
        """Clone and start an action on this sprite."""
        clone = action.clone()
        clone.start(self)
        self._actions.append(clone)

    def update(self, delta_time: float = 1 / 60):
        # Step all active actions
        for action in self._actions[:]:
            action.step(delta_time)
            if action.is_done():
                action.stop()
                self._actions.remove(action)

        # Then let Arcade apply velocities to position
        super().update()

    def clear_actions(self):
        """Cancel all actions currently running on this sprite."""
        for action in self._actions:
            action.stop()
        self._actions.clear()

    def has_active_actions(self) -> bool:
        return any(not act.is_done() for act in self._actions)
