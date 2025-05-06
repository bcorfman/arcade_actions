"""
Composite actions that combine other actions.
"""

import copy
from typing import List, Optional
import arcade
from .base import Action, IntervalAction


class Sequence(IntervalAction):
    """Run a sequence of actions one after another."""

    def __init__(self, *actions: Action):
        super().__init__(sum(getattr(a, "duration", 0) for a in actions))
        self.actions = list(actions)
        self.current_action: Optional[Action] = None
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
        if self._done and self._on_complete and not self._on_complete_called:
            self._on_complete_called = True
            self._on_complete(*self._on_complete_args, **self._on_complete_kwargs)

    def start(self) -> None:
        if self.actions:
            self.current_action = self.actions[0]
            self.current_action.target = self.target
            self.current_action.start()

    def update(self, delta_time: float) -> None:
        if not self.current_action:
            self._done = True
            self._check_complete()
            return

        self.current_action.update(delta_time)

        if self.current_action.done():
            self.current_action.stop()
            self.current_index += 1

            if self.current_index < len(self.actions):
                self.current_action = self.actions[self.current_index]
                self.current_action.target = self.target
                self.current_action.start()
            else:
                self.current_action = None
                self._done = True
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
        super().__init__(max(getattr(a, "duration", 0) for a in actions))
        self.actions = list(actions)

    def start(self) -> None:
        for action in self.actions:
            action.target = self.target
            action.start()

    def update(self, delta_time: float) -> None:
        all_done = True
        for action in self.actions:
            if not action.done():
                action.update(delta_time)
                all_done = False
        self._done = all_done

    def stop(self) -> None:
        for action in self.actions:
            action.stop()
        super().stop()

    def reset(self) -> None:
        for action in self.actions:
            action.reset()
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
        if self.action.done():
            self.current_times += 1
            if self.current_times >= self.times:
                self._done = True
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
