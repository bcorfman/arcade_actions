"""
Instant actions that happen immediately.
"""

import copy
from collections.abc import Callable
from typing import Any

from .base import InstantAction


class Place(InstantAction):
    """Place the sprite at a specific position."""

    def __init__(self, position: tuple[float, float] = None):
        if position is None:
            raise ValueError("Must specify position")

        super().__init__()
        self.position = position

    def start(self) -> None:
        self.target.position = self.position

    def stop(self) -> None:
        super().stop()

    def __repr__(self) -> str:
        return f"Place(position={self.position})"


class Hide(InstantAction):
    """Hide the sprite."""

    def start(self) -> None:
        self.target.visible = False

    def stop(self) -> None:
        super().stop()

    def __reversed__(self) -> "Show":
        return Show()

    def __repr__(self) -> str:
        return "Hide()"


class Show(InstantAction):
    """Show the sprite."""

    def start(self) -> None:
        self.target.visible = True

    def stop(self) -> None:
        super().stop()

    def __reversed__(self) -> "Hide":
        return Hide()

    def __repr__(self) -> str:
        return "Show()"


class ToggleVisibility(InstantAction):
    """Toggle the sprite's visibility."""

    def start(self) -> None:
        self.target.visible = not self.target.visible

    def stop(self) -> None:
        super().stop()

    def __reversed__(self) -> "ToggleVisibility":
        return self

    def __repr__(self) -> str:
        return "ToggleVisibility()"


class CallFunc(InstantAction):
    """Call a function when the action starts."""

    def __init__(self, func: Callable = None, *args: Any, **kwargs: Any):
        if func is None:
            raise ValueError("Must specify func")

        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def start(self) -> None:
        self.func(*self.args, **self.kwargs)

    def stop(self) -> None:
        super().stop()

    def __deepcopy__(self, memo) -> "CallFunc":
        return copy.copy(self)

    def __reversed__(self) -> "CallFunc":
        return self

    def __repr__(self) -> str:
        return f"CallFunc(func={self.func.__name__})"


class CallFuncS(CallFunc):
    """Call a function with the sprite as the first argument."""

    def start(self) -> None:
        self.func(self.target, *self.args, **self.kwargs)

    def stop(self) -> None:
        super().stop()

    def __repr__(self) -> str:
        return f"CallFuncS(func={self.func.__name__})"
