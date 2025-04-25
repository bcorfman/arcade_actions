import pytest

from actions.base import Repeat, sequence, spawn
from actions.interval import MoveBy, RotateBy


class MockSprite:
    def __init__(self):
        self.change_x = 0.0
        self.change_y = 0.0
        self.change_angle = 0.0
        self.reset()

    def reset(self):
        self.change_x = 0.0
        self.change_y = 0.0
        self.change_angle = 0.0


def step_until_done(action, sprite, dt=0.1):
    frames = 0
    while not action.is_done():
        action.step(dt)
        frames += 1
    return frames


def test_sequence_transition():
    sprite = MockSprite()
    act = sequence(MoveBy((100, 0), 1.0), RotateBy(90, 1.0))
    act.start(sprite)

    # First half — movement
    act.step(0.5)
    assert sprite.change_x == pytest.approx(100.0)

    act.step(0.5)
    assert sprite.change_x == pytest.approx(0.0)  # movement phase done
    assert sprite.change_angle == pytest.approx(90.0)

    act.step(1.0)
    assert sprite.change_angle == pytest.approx(0.0)
    assert act.is_done()


def test_spawn_parallel_motion():
    sprite = MockSprite()
    act = spawn(MoveBy((100, 0), 1.0), RotateBy(180, 2.0))
    act.start(sprite)

    act.step(0.5)
    assert sprite.change_x == pytest.approx(100.0)
    assert sprite.change_angle == pytest.approx(90.0)

    act.step(0.5)
    assert sprite.change_x == pytest.approx(0.0)
    assert sprite.change_angle == pytest.approx(90.0)

    act.step(1.0)
    assert sprite.change_angle == pytest.approx(0.0)
    assert act.is_done()


def test_repeat_action():
    sprite = MockSprite()
    act = Repeat(MoveBy((60, 0), 0.5), 2)
    act.start(sprite)

    act.step(0.25)
    assert sprite.change_x == pytest.approx(120.0)  # 60 / 0.5 * 2

    act.step(0.25)
    assert sprite.change_x == pytest.approx(0.0)

    act.step(0.5)
    assert sprite.change_x == pytest.approx(0.0)
    assert act.is_done()


def test_reset_reusability():
    sprite = MockSprite()
    move = MoveBy((50, 0), 1.0)
    move.start(sprite)

    move.step(0.5)
    assert sprite.change_x == pytest.approx(50.0)

    move.stop()
    move.reset()
    sprite.reset()

    move.start(sprite)
    move.step(1.0)
    assert sprite.change_x == pytest.approx(0.0)
    assert move.is_done()
