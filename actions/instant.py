import copy
from collections.abc import Callable
from typing import Any

import arcade

from .base import InstantAction


class Place(InstantAction):
    def __init__(self, position: tuple[float, float]):
        super().__init__()
        self.position = position

    def start(self):
        self.target.center_x, self.target.center_y = self.position


class Hide(InstantAction):
    def start(self):
        self.target.visible = False

    def __reversed__(self):
        return Show()


class Show(InstantAction):
    def start(self):
        self.target.visible = True

    def __reversed__(self):
        return Hide()


class ToggleVisibility(InstantAction):
    def start(self):
        self.target.visible = not self.target.visible


class CallFunc(InstantAction):
    def __init__(self, func: Callable, *args: Any, **kwargs: Any):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def start(self):
        self.func(*self.args, **self.kwargs)

    def __deepcopy__(self, memo):
        return copy.copy(self)


class CallFuncS(CallFunc):
    def start(self):
        self.func(self.target, *self.args, **self.kwargs)


# Usage example
if __name__ == "__main__":
    window = arcade.Window(800, 600, "Instant Actions Example")

    sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    sprite.center_x = 400
    sprite.center_y = 300

    def print_message(target):
        print(f"Hello from {target}")

    action = Place((200, 200)) + CallFuncS(print_message) + Hide() + Show() + ToggleVisibility()

    sprite.do(action)

    @window.event
    def on_draw():
        arcade.start_render()
        sprite.draw()

    def update(delta_time):
        sprite.update()

    arcade.schedule(update, 1 / 60)

    arcade.run()
