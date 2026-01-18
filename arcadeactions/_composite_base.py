from __future__ import annotations

from ._action_core import Action


class CompositeAction(Action):
    """Base class for composite actions that manage multiple sub-actions."""

    def __init__(self):
        super().__init__(condition=None, on_stop=None)
        self._on_complete_called = False
        self.actions: list[Action] = []

    def _check_complete(self) -> None:
        if not self._on_complete_called:
            self._on_complete_called = True
            self.done = True

    def reverse_movement(self, axis: str) -> None:
        pass

    def sub_actions(self) -> list[Action]:
        return self.actions

    def reset(self) -> None:
        self.done = False
        self._on_complete_called = False

    def clone(self) -> "CompositeAction":
        raise NotImplementedError("Subclasses must implement clone()")

    def apply_effect(self) -> None:
        pass
