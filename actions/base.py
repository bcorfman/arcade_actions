import arcade


class Action:
    def __init__(self):
        self.target = None
        self._elapsed = 0.0
        self._done = False
        self.scheduled_to_remove = False

    def start(self):
        pass

    def step(self, dt: float):
        self._elapsed += dt

    def done(self) -> bool:
        return self._done

    def stop(self):
        self.target = None

    def __add__(self, other):
        return sequence(self, other)

    def __mul__(self, other: int):
        if not isinstance(other, int):
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        return Loop(self, other)

    def __or__(self, other):
        return spawn(self, other)

    def __reversed__(self):
        raise NotImplementedError(f"Action {self.__class__.__name__} cannot be reversed")


class IntervalAction(Action):
    def __init__(self, duration: float):
        super().__init__()
        self.duration = duration

    def step(self, dt: float):
        super().step(dt)
        try:
            t = min(1, self._elapsed / self.duration)
            self.update(t)
        except ZeroDivisionError:
            self.update(1.0)

    def done(self):
        done = self._elapsed >= self.duration
        return done

    def update(self, t: float):
        pass


class InstantAction(IntervalAction):
    def __init__(self):
        super().__init__(0)
        self.duration = 0.0

    def step(self, dt: float):
        pass

    def start(self):
        self._done = True

    def update(self, t: float):
        pass

    def stop(self):
        pass

    def done(self):
        return True


class Loop(Action):
    def __init__(self, action: Action, times: int):
        super().__init__()
        self.action = action
        self.times = times
        self.current_action = None

    def start(self):
        self.current_action = self.action
        self.current_action.target = self.target
        self.current_action.start()

    def step(self, dt: float):
        super().step(dt)
        self.current_action.step(dt)
        if self.current_action.done():
            self.current_action.stop()
            self.times -= 1
            if self.times == 0:
                self._done = True
            else:
                self.current_action = self.action
                self.current_action.target = self.target
                self.current_action.start()

    def stop(self):
        if not self._done:
            self.current_action.stop()
        super().stop()


def sequence(*actions: Action) -> Action:
    if len(actions) < 2:
        return actions[0] if actions else None
    return Sequence(actions)


class Sequence(Action):
    def __init__(self, actions: list[Action]):
        super().__init__()
        self.actions = actions
        self.current_index = 0

    def start(self):
        for action in self.actions:
            action.target = self.target
        self.actions[0].start()

    def step(self, dt: float):
        super().step(dt)
        current_action = self.actions[self.current_index]
        current_action.step(dt)
        if current_action.done():
            # Ensure the action gets to its final state
            if isinstance(current_action, IntervalAction):
                current_action.update(1.0)
            current_action.stop()
            self.current_index += 1
            if self.current_index < len(self.actions):
                self.actions[self.current_index].start()
            else:
                self._done = True

    def stop(self):
        if not self._done:
            self.actions[self.current_index].stop()
        super().stop()


def spawn(*actions: Action) -> Action:
    return Spawn(actions)


class Spawn(Action):
    def __init__(self, actions: list[Action]):
        super().__init__()
        self.actions = actions

    def start(self):
        for action in self.actions:
            action.target = self.target
            action.start()

    def step(self, dt: float):
        super().step(dt)
        all_done = True
        for action in self.actions:
            if not action.done():
                action.step(dt)
                all_done = False
        self._done = all_done

    def stop(self):
        for action in self.actions:
            action.stop()
        super().stop()


class Repeat(Action):
    def __init__(self, action: Action):
        super().__init__()
        self.action = action
        self.current_action = None

    def start(self):
        self.current_action = self.action
        self.current_action.target = self.target
        self.current_action.start()

    def step(self, dt: float):
        super().step(dt)
        self.current_action.step(dt)
        if self.current_action.done():
            self.current_action.stop()
            self.current_action = self.action
            self.current_action.target = self.target
            self.current_action.start()

    def stop(self):
        if self.current_action:
            self.current_action.stop()
        super().stop()


# Integrate with Arcade Sprite
class ActionSprite(arcade.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions: list[Action] = []

    def do(self, action: Action):
        action.target = self
        action.start()
        self.actions.append(action)

    def update(self, delta_time: float = 1 / 60):
        super().update()
        for action in self.actions[:]:
            try:
                action.step(delta_time)
                if action.done():
                    self.remove_action(action)
            except Exception as e:
                print(f"Error updating action: {e}")
                self.remove_action(action)

    def remove_action(self, action: Action):
        if action in self.actions:
            action.stop()
            self.actions.remove(action)


# Usage example
if __name__ == "__main__":
    window = arcade.Window(800, 600, "Base Action System Example")

    sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    sprite.center_x = 400
    sprite.center_y = 300

    class SimpleMove(IntervalAction):
        def __init__(self, dx: float, dy: float, duration: float):
            super().__init__(duration)
            self.dx = dx
            self.dy = dy

        def update(self, t: float):
            self.target.center_x += self.dx * t
            self.target.center_y += self.dy * t

    action = SimpleMove(100, 100, 2.0) + SimpleMove(-100, -100, 2.0)
    repeated_action = Repeat(action)

    sprite.do(repeated_action)

    @window.event
    def on_draw():
        arcade.start_render()
        sprite.draw()

    def update(delta_time):
        sprite.update()

    arcade.schedule(update, 1 / 60)

    arcade.run()
