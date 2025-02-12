from typing import Any

import pytest

from actions.base import sequence
from actions.interval import (
    IntervalAction,
)

# Global event record
rec: list[tuple[str, str, Any]] = []


class MockSprite:
    """Mock Arcade Sprite for testing"""

    def __init__(self):
        self.position = (0, 0)
        self.rotation = 0
        self.visible = False
        self._actions = []  # Track active actions

    def do(self, action):
        """Helper to start an action"""
        action.target = self
        self._actions.append(action)  # Store action for step updates
        action.start()
        return action

    def _step(self, dt):
        """Test helper to advance time"""
        for action in self._actions:  # Update all active actions
            action.step(dt)


@pytest.fixture
def mock_sprite():
    return MockSprite()


class UIntervalAction(IntervalAction):
    def init(self, name, duration):
        rec.append((name, "init"))
        self.duration = duration
        self.name = name

    def start(self):
        rec.append((self.name, "start"))

    def step(self, dt):
        rec.append((self.name, "step", dt))
        super().step(dt)

    def update(self, fraction):
        rec.append((self.name, "update", fraction))

    def stop(self):
        rec.append((self.name, "stop"))


@pytest.mark.parametrize("duration1,duration2", [(0.0, 0.0), (0.0, 3.0), (3.0, 0.0), (3.0, 5.0)])
class Test_Sequence_IntervalAction:
    """Tests for sequence action composition"""

    def test_instantiation(self, duration1: float, duration2: float) -> None:
        """Test sequence creation and duration calculation"""
        global rec

        name1, name2 = "1", "2"
        a1 = UIntervalAction(name1, duration1)
        assert isinstance(a1, IntervalAction)
        assert a1.duration == pytest.approx(duration1)

        a2 = UIntervalAction(name2, duration2)

        rec = []  # Clear event record
        composite = sequence(a1, a2)

        assert isinstance(composite, IntervalAction)
        assert composite.duration == pytest.approx(duration1 + duration2)
        assert len(rec) == 0, "Sequence creation should not trigger events"

    def test_start(self, duration1: float, duration2: float) -> None:
        global rec
        sprite = MockSprite()
        name1, name2 = "1", "2"
        a1 = UIntervalAction(name1, duration1)
        a2 = UIntervalAction(name2, duration2)
        composite = sequence(a1, a2)

        rec = []
        sprite.do(composite)
        num = 0
        assert rec[num] == (name1, "start")
        if duration1 == 0.0:
            assert rec[num + 1] == (name1, "update", 1.0)
            assert rec[num + 2] == (name1, "stop")
            assert rec[num + 3] == (name2, "start")
            num = num + 3
        assert len(rec) == num + 1

    def test_target_set(self, duration1: float, duration2: float) -> None:
        global rec
        sprite = MockSprite()
        name1, name2 = "1", "2"
        a1 = UIntervalAction(name1, duration1)
        a2 = UIntervalAction(name2, duration2)
        composite = sequence(a1, a2)

        rec = []
        action_copy = sprite.do(composite)
        assert action_copy.one.target == sprite
        assert action_copy.two.target == sprite

    def test_update_below_duration1(self, duration1: float, duration2: float) -> None:
        global rec
        if duration1 == 0.0:
            return

        sprite = MockSprite()
        name1, name2 = "1", "2"
        a1 = UIntervalAction(name1, duration1)
        a2 = UIntervalAction(name2, duration2)
        composite = sequence(a1, a2)
        sprite.do(composite)
        elapsed = 0.0

        for next_elapsed in [duration1 * 0.5, duration1 * 0.75]:
            dt = next_elapsed - elapsed
            rec = []
            sprite._step(dt)
            rec = [e for e in rec if e[1] != "step"]
            assert rec[0][1] == "update"
            assert abs(rec[0][2] - next_elapsed / duration1) < 1.0e-6
            assert len(rec) == 1
            elapsed = next_elapsed
