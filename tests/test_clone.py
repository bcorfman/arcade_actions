import pytest

from actions.base import Action, Actionable
from actions.interval import MoveBy


class MockSprite(Actionable):
    def __init__(self):
        self.center_x = 0
        self.center_y = 0
        self._actions = []

    def do(self, action: Action):
        action = action.clone()
        action.target = self
        action.start()
        self._actions.append(action)

    def update(self, dt):
        for action in self._actions[:]:
            action.step(dt)
            if action.is_done():
                self._actions.remove(action)


def test_reuse_action_instance():
    move = MoveBy((100, 0), 1.0)
    sprite1 = MockSprite()
    sprite2 = MockSprite()

    sprite1.do(move)
    sprite2.do(move)  # Should trigger .clone()

    for _ in range(10):
        sprite1.update(0.1)
        sprite2.update(0.1)

    # Expect each sprite to have moved independently
    assert sprite1.center_x > 0
    assert sprite2.center_x > 0
    assert sprite1.center_x == pytest.approx(sprite2.center_x)
