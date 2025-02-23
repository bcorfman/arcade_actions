import pytest

from actions.base import Action
from actions.interval import FadeOut, MoveTo, RotateBy, ScaleTo


class MockSprite:
    def __init__(self):
        self.center_x = 0
        self.center_y = 0
        self.angle = 0
        self.scale = 1.0
        self.alpha = 255
        self.actions = []

    def update(self, delta_time: float = 1 / 60):
        for action in self.actions[:]:
            action.step(delta_time)
            if action.done():
                action.stop()
                self.actions.remove(action)

    def do(self, action: Action):
        action.target = self
        action.start()
        self.actions.append(action)


@pytest.fixture
def mock_sprite():
    return MockSprite()


def test_sequence_timing(mock_sprite):
    """Test that a sequence of three actions executes with correct timing"""
    # Create three actions with different durations
    move = MoveTo((100, 100), duration=2.0)
    rotate = RotateBy(330, duration=1.0)
    scale = ScaleTo(2.0, duration=3.0)

    # Verify first action (MoveTo)
    move.target = mock_sprite
    move.start()
    move.update(0.5)  # Test in-between state
    assert mock_sprite.center_x == pytest.approx(50, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(50, rel=1e-2)
    assert mock_sprite.angle == 0
    assert mock_sprite.scale == 1.0

    move.update(1.0)  # Complete the action
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)
    assert mock_sprite.angle == 0
    assert mock_sprite.scale == 1.0

    # Verify second action (RotateBy)
    rotate.target = mock_sprite
    rotate.start()
    rotate.update(0.75)  # Test in-between state
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)
    assert mock_sprite.angle == pytest.approx(247.5, rel=1e-2)
    assert mock_sprite.scale == 1.0

    rotate.update(1.0)  # Test in-between state
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)
    assert mock_sprite.angle == pytest.approx(330, rel=1e-2)
    assert mock_sprite.scale == 1.0

    # Verify third action (ScaleTo)
    scale.target = mock_sprite
    scale.start()
    scale.update(0.5)  # Complete the action
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)
    assert mock_sprite.angle == pytest.approx(330, rel=1e-2)
    assert mock_sprite.scale == pytest.approx(1.5, rel=1e-2)

    scale.update(1.0)  # Complete the action
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)
    assert mock_sprite.angle == pytest.approx(330, rel=1e-2)
    assert mock_sprite.scale == pytest.approx(2.0, rel=1e-2)
    assert not mock_sprite.actions  # All actions should be complete


def test_spawn_timing(mock_sprite):
    """Test that spawned actions execute independently with correct timing"""
    # First let's test seq1 components independently
    move1 = MoveTo((100, 100), duration=2.0)
    rotate1 = RotateBy(180, duration=1.0)

    # Test MoveTo
    move1.target = mock_sprite
    move1.start()
    move1.update(0.5)  # Test in-between state
    assert mock_sprite.center_x == pytest.approx(50, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(50, rel=1e-2)
    assert mock_sprite.angle == 0
    assert mock_sprite.scale == 1.0

    move1.update(1.0)  # Complete
    assert mock_sprite.center_x == pytest.approx(100, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(100, rel=1e-2)

    # Test RotateBy
    rotate1.target = mock_sprite
    rotate1.start()
    rotate1.update(0.5)  # Test in-between state
    assert mock_sprite.angle == pytest.approx(90, rel=1e-2)

    rotate1.update(1.0)  # Complete
    assert mock_sprite.angle == pytest.approx(180, rel=1e-2)

    # Now test seq2 components
    scale2 = ScaleTo(2.0, duration=1.0)
    fade2 = FadeOut(3.0)

    # Test ScaleTo
    scale2.target = mock_sprite
    scale2.start()
    scale2.update(0.5)  # Test in-between state
    assert mock_sprite.scale == pytest.approx(1.5, rel=1e-2)

    scale2.update(1.0)  # Complete
    assert mock_sprite.scale == pytest.approx(2.0, rel=1e-2)

    # Test FadeOut
    fade2.target = mock_sprite
    fade2.start()
    fade2.update(0.25)  # Test early state
    assert mock_sprite.alpha == pytest.approx(191, rel=1e-2)  # int(255 * 0.75)

    fade2.update(0.5)  # Test middle state
    assert mock_sprite.alpha == pytest.approx(128, rel=1e-2)  # int(255 * 0.5)

    fade2.update(0.75)  # Test late state
    assert mock_sprite.alpha == pytest.approx(63, rel=1e-2)  # int(255 * 0.25) truncated to 63
    # Finally test seq3 components
    move3 = MoveTo((200, 200), duration=2.0)
    rotate3 = RotateBy(90, duration=1.0)
    scale3 = ScaleTo(0.5, duration=3.0)

    # Test MoveTo
    move3.target = mock_sprite
    move3.start()
    move3.update(0.5)  # Test in-between state
    assert mock_sprite.center_x == pytest.approx(150, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(150, rel=1e-2)

    move3.update(1.0)  # Complete
    assert mock_sprite.center_x == pytest.approx(200, rel=1e-2)
    assert mock_sprite.center_y == pytest.approx(200, rel=1e-2)

    # Test RotateBy
    rotate3.target = mock_sprite
    rotate3.start()
    rotate3.update(0.5)  # Test in-between state
    assert mock_sprite.angle == pytest.approx(225, rel=1e-2)  # 180 + 45

    rotate3.update(1.0)  # Complete
    assert mock_sprite.angle == pytest.approx(270, rel=1e-2)  # 180 + 90

    # Test ScaleTo
    scale3.target = mock_sprite
    scale3.start()
    scale3.update(0.5)  # Test in-between state
    assert mock_sprite.scale == pytest.approx(1.25, rel=1e-2)  # Halfway between 2.0 and 0.5

    scale3.update(1.0)  # Complete
    assert mock_sprite.scale == pytest.approx(0.5, rel=1e-2)

    assert not mock_sprite.actions  # All actions should be complete


if __name__ == "__main__":
    pytest.main([__file__])
