import pytest

from actions.move import BoundedMove, Move, WrappedMove


class MockSprite:
    """Mock sprite class for testing"""

    def __init__(self):
        self.position = (0, 0)
        self.velocity = (0, 0)
        self.acceleration = (0, 0)
        self.gravity = 0
        self.rotation = 0
        self.dr = 0
        self.ddr = 0
        self.width = 10
        self.height = 10
        self.speed = 0
        self.max_forward_speed = None
        self.max_reverse_speed = None


@pytest.fixture
def mock_sprite():
    return MockSprite()


@pytest.fixture
def basic_move():
    return Move()


@pytest.fixture
def wrapped_move():
    # Initialize with default values
    move = WrappedMove()
    move.init(800, 600)  # match Cocos2D style initialization
    return move


@pytest.fixture
def bounded_move():
    # Initialize with default values
    move = BoundedMove()
    move.init(800, 600)  # match Cocos2D style initialization
    return move


class TestMove:
    @pytest.mark.parametrize(
        "initial_pos,velocity,dt,expected_pos",
        [
            ((0, 0), (10, 0), 1.0, (10, 0)),
            ((100, 100), (10, 20), 0.5, (105, 110)),
            ((0, 0), (-10, -10), 1.0, (-10, -10)),
        ],
    )
    def test_basic_movement(self, mock_sprite, basic_move, initial_pos, velocity, dt, expected_pos):
        """Test basic movement with different velocities"""
        mock_sprite.position = initial_pos
        mock_sprite.velocity = velocity
        basic_move.target = mock_sprite

        basic_move.step(dt)
        assert pytest.approx(mock_sprite.position) == expected_pos

    @pytest.mark.parametrize(
        "initial_pos,initial_vel,accel,dt,expected_pos,expected_vel",
        [
            ((0, 0), (0, 0), (10, 0), 1.0, (5, 0), (10, 0)),
            ((0, 0), (0, 0), (0, -9.8), 1.0, (0, -4.9), (0, -9.8)),
            ((10, 10), (5, 5), (2, 2), 0.5, (11.25, 11.25), (6, 6)),
        ],
    )
    def test_movement_with_acceleration(
        self, mock_sprite, basic_move, initial_pos, initial_vel, accel, dt, expected_pos, expected_vel
    ):
        """Test movement with acceleration"""
        mock_sprite.position = initial_pos
        mock_sprite.velocity = initial_vel
        mock_sprite.acceleration = accel
        basic_move.target = mock_sprite

        basic_move.step(dt)
        assert pytest.approx(mock_sprite.position) == expected_pos
        assert pytest.approx(mock_sprite.velocity) == expected_vel

    def test_no_target(self, basic_move):
        """Test movement with no target"""
        with pytest.raises(ValueError):
            basic_move.step(1.0)


class TestWrappedMove:
    @pytest.mark.parametrize(
        "initial_pos,expected_pos",
        [
            ((850, 300), (40, 300)),  # Wrap right to left
            ((-50, 300), (760, 300)),  # Wrap left to right
            ((400, 650), (400, 40)),  # Wrap top to bottom
            ((400, -50), (400, 560)),  # Wrap bottom to top
            ((850, 650), (40, 40)),  # Wrap both directions
        ],
    )
    def test_position_wrapping(self, mock_sprite, wrapped_move, initial_pos, expected_pos):
        """Test position wrapping at boundaries"""
        mock_sprite.position = initial_pos
        wrapped_move.target = mock_sprite
        wrapped_move.step(0)  # Force wrap check
        assert pytest.approx(mock_sprite.position) == expected_pos

    @pytest.mark.parametrize(
        "width,height",
        [
            (-100, 600),  # Negative width
            (800, -100),  # Negative height
            (0, 0),  # Zero dimensions
        ],
    )
    def test_invalid_boundaries(self, width, height):
        """Test invalid boundary initialization"""
        move = WrappedMove()
        with pytest.raises(ValueError):
            move.init(width, height)  # Use init() method like Cocos2D

    def test_missing_initialization(self, mock_sprite):
        """Test movement without initialization"""
        move = WrappedMove()  # Don't initialize
        move.target = mock_sprite
        with pytest.raises(ValueError):
            move.step(1.0)


class TestBoundedMove:
    @pytest.mark.parametrize(
        "initial_pos,expected_pos",
        [
            ((850, 300), (795, 300)),  # Clamp right
            ((-50, 300), (5, 300)),  # Clamp left
            ((400, 650), (400, 595)),  # Clamp top
            ((400, -50), (400, 5)),  # Clamp bottom
            ((850, 650), (795, 595)),  # Clamp both directions
        ],
    )
    def test_position_bounding(self, mock_sprite, bounded_move, initial_pos, expected_pos):
        """Test position clamping at boundaries"""
        mock_sprite.position = initial_pos
        bounded_move.target = mock_sprite
        bounded_move.step(0)  # Force bounds check
        assert pytest.approx(mock_sprite.position) == expected_pos

    @pytest.mark.parametrize(
        "width,height",
        [
            (-100, 600),  # Negative width
            (800, -100),  # Negative height
            (0, 0),  # Zero dimensions
        ],
    )
    def test_invalid_boundaries(self, width, height):
        """Test invalid boundary initialization"""
        move = BoundedMove()
        with pytest.raises(ValueError):
            move.init(width, height)  # Use init() method like Cocos2D


if __name__ == "__main__":
    pytest.main(["-v"])
