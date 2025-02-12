import pytest

from actions.interval import JumpTo, MoveBy, MoveTo, RotateBy, RotateTo


class MockSprite:
    """Mock sprite class for testing"""

    def __init__(self):
        self.center_x = 0
        self.center_y = 0
        self.position = (0, 0)
        self.velocity = (0, 0)
        self.rotation = 0
        self.angle = 0
        self.width = 10
        self.height = 10

    @property
    def center(self):
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, value):
        self.center_x, self.center_y = value
        self.position = value


@pytest.fixture
def mock_sprite():
    return MockSprite()


class TestSequenceActions:
    def test_move_rotate_sequence(self, mock_sprite):
        """Test sequence of MoveTo followed by RotateBy"""
        jump = JumpTo((0, 0), duration=0.0)
        start_rot = RotateTo(0, duration=0.0)
        move = MoveTo((100, 0), duration=1.0)
        rotate = RotateBy(90, duration=1.0)
        sequence_action = start_rot + jump + move + rotate  # Total duration = 2.0
        sequence_action.target = mock_sprite
        sequence_action.start()

        # Test during move (t=0.25 = halfway through move since move is first half)
        sequence_action.update(0.25)
        assert pytest.approx(mock_sprite.center[0]) == 50
        assert pytest.approx(mock_sprite.angle) == 0

        # Test during rotation (t=0.75 = halfway through rotation)
        sequence_action.update(0.75)
        assert pytest.approx(mock_sprite.center[0]) == 100
        assert pytest.approx(mock_sprite.angle) == 45

    def test_complex_movement_sequence(self, mock_sprite):
        """Test sequence of multiple movements"""
        # Total duration = 3.0, each action takes 1/3 of total time
        actions = (
            JumpTo((0, 0), duration=0)
            + RotateTo(0, duration=0)
            + MoveTo((100, 0), duration=1.0)
            + MoveBy((0, 100), duration=1.0)
            + RotateBy(180, duration=1.0)
        )
        actions.target = mock_sprite
        actions.start()

        # Test halfway through first movement (t=0.16 ~= 1/6 = halfway through first third)
        actions.update(0.16)
        assert pytest.approx(mock_sprite.center[0]) == 48  # 48% through first move


class TestSpawnActions:
    def test_multiple_parallel_actions(self, mock_sprite):
        """Test three parallel actions happening in parallel"""
        mock_sprite.center = (0, 0)
        mock_sprite.angle = 0
        move_xy = MoveBy((50, 100), duration=1.0)
        rotate = RotateBy(360, duration=1.0)
        parallel_action = move_xy | rotate
        parallel_action.target = mock_sprite
        parallel_action.start()

        # All actions progress independently using same time value
        parallel_action.update(0.5)  # Halfway through all actions
        assert pytest.approx(mock_sprite.angle) == 180  # Half rotation
        assert pytest.approx(mock_sprite.center[0]) == 25  # Both movements at 50%
        assert pytest.approx(mock_sprite.center[1]) == 50  # Both movements at 50%


class TestComplexComposites:
    def test_sequence_with_repeats(self, mock_sprite):
        """Test sequence containing repeated actions"""
        move = MoveTo((50, 0), duration=1.0)
        rotate = RotateBy(90, duration=1.0)
        # (move * 2) takes first half, (rotate * 2) takes second half
        action = (move * 2) + (rotate * 2)
        action.target = mock_sprite
        action.start()

        # Test during first move repetition
        action.update(0.25)  # 25% through total = halfway through first half = completed first move
        assert pytest.approx(mock_sprite.center[0]) == 50  # First move completed

        # Test at transition point
        action.update(0.5)  # Half done = moves completed, starting rotations
        assert pytest.approx(mock_sprite.center[0]) == 50
        assert pytest.approx(mock_sprite.angle) == 0  # Just starting rotations

        # Test during rotations
        action.update(0.75)  # 75% through = halfway through rotations = first rotation done
        assert pytest.approx(mock_sprite.angle) == 90

    def test_complex_movement_pattern(self, mock_sprite):
        """Test complex pattern combining sequence, spawn, and repeat"""
        # Each move takes 1/4 of sequence time
        mock_sprite.center = (0, 0)
        mock_sprite.angle = 0
        move_right = MoveTo((100, 0), duration=1.0)
        move_up = MoveTo((100, 100), duration=1.0)
        move_left = MoveTo((0, 100), duration=1.0)
        move_down = MoveTo((0, 0), duration=1.0)
        # Full rotation matches total sequence time
        rotate = RotateBy(90, duration=4.0)

        # Square pattern repeated twice with constant rotation
        square = move_right + move_up + move_left + move_down
        action = square | rotate
        action.target = mock_sprite
        action.start()

        # Test key points in pattern - movement completes each step
        # while rotation progresses linearly
        positions = [
            (0.50 / 4, (50, 0), 11.25),
            (1.0 / 4, (100, 0), 22.5),
            (1.5 / 4, (100, 50), 33.75),
            (2.0 / 4, (100, 100), 45.0),
            (2.5 / 4, (50, 100), 56.25),
            (3.0 / 4, (0, 100), 67.5),
            (3.5 / 4, (0, 50), 78.75),
            (4.0 / 4, (0, 0), 90.0),
        ]

        for t, expected_pos, expected_angle in positions:
            action.update(t)
            assert pytest.approx(mock_sprite.center[0]) == expected_pos[0]
            assert pytest.approx(mock_sprite.angle) == expected_angle


if __name__ == "__main__":
    pytest.main(["-v"])
