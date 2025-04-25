# instant.py

from .base import InstantAction

__all__ = [
    "Place",
    "Hide",
    "Show",
    "ToggleVisibility",
    "CallFunc",
    "CallFuncS",
]


class Place(InstantAction):
    def __init__(self, position):
        super().__init__()
        self.position = position

    def update(self, t: float):
        self.target.center_x, self.target.center_y = self.position


class Hide(InstantAction):
    def update(self, t: float):
        self.target.visible = False

    def __reversed__(self):
        return Show()


class Show(InstantAction):
    def update(self, t: float):
        self.target.visible = True

    def __reversed__(self):
        return Hide()


class ToggleVisibility(InstantAction):
    def update(self, t: float):
        self.target.visible = not self.target.visible


class CallFunc(InstantAction):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def update(self, t: float):
        self.func()


class CallFuncS(InstantAction):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def update(self, t: float):
        self.func(self.target)
