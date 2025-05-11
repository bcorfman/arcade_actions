"""Test suite for base.py - Core Action system architecture."""

import arcade
import pytest
from arcade.texture import Texture

from actions.base import Action, ActionSprite, GroupAction, InstantAction, IntervalAction
from actions.game_clock import GameClock


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with a 1x1 transparent texture for testing."""
    texture = Texture.create_empty("test", (1, 1))
    sprite = arcade.Sprite()
    sprite.texture = texture
    return sprite


class MockAction(Action):
    """Mock action for testing base Action functionality."""

    def __init__(self, duration: float = 1.0, clock: GameClock = None):
        super().__init__(clock=clock)
        self.duration = duration
        self.start_called = False
        self.update_called = False
        self.stop_called = False

    def start(self) -> None:
        self.start_called = True

    def update(self, delta_time: float) -> None:
        self.update_called = True
        super().update(delta_time)

    def stop(self) -> None:
        self.stop_called = True
        super().stop()

    def done(self) -> bool:
        return self._elapsed >= self.duration


class MockIntervalAction(IntervalAction):
    """Mock interval action for testing."""

    def __init__(self, duration: float = 1.0):
        super().__init__(duration)
        self.start_called = False
        self.stop_called = False
        self.update_called = False

    def start(self) -> None:
        self.start_called = True

    def update(self, delta_time: float) -> None:
        self.update_called = True
        super().update(delta_time)

    def stop(self) -> None:
        self.stop_called = True
        super().stop()


class MockInstantAction(InstantAction):
    """Mock instant action for testing."""

    def __init__(self):
        super().__init__()
        self.start_called = False
        self.stop_called = False

    def start(self) -> None:
        self.start_called = True

    def stop(self) -> None:
        self.stop_called = True


class TestAction:
    """Test suite for base Action class."""

    @pytest.fixture
    def action(self):
        return MockAction()

    @pytest.fixture
    def clock(self):
        return GameClock()

    def test_action_initialization(self, action):
        """Test basic action initialization."""
        assert action.target is None
        assert action._elapsed == 0.0
        assert not action._done
        assert not action._paused
        assert action._on_complete is None

    def test_action_lifecycle(self, action):
        """Test complete action lifecycle."""
        # Start
        action.start()
        assert action.start_called

        # Update
        action.update(0.5)
        assert action.update_called
        assert action._elapsed == 0.5
        assert not action._done

        # Complete
        action.update(0.5)
        assert action._done

        # Stop
        action.stop()
        assert action.stop_called
        assert action.target is None

    def test_action_pause_resume(self, action, clock):
        """Test action pause/resume functionality."""
        action = MockAction(clock=clock)

        # Start and update
        action.start()
        action.update(0.5)
        assert action._elapsed == 0.5

        # Pause
        action.pause()
        assert action._paused
        action.update(0.5)
        assert action._elapsed == 0.5  # Should not update while paused

        # Resume
        action.resume()
        assert not action._paused
        action.update(0.5)
        assert action._elapsed == 1.0

    def test_action_completion_callback(self, action):
        """Test action completion callback."""
        callback_called = False

        def on_complete():
            nonlocal callback_called
            callback_called = True

        action.on_complete(on_complete)
        action.start()
        action.update(1.0)  # Complete the action
        assert callback_called

    def test_action_reset(self, action):
        """Test action reset functionality."""
        action.start()
        action.update(0.5)
        action.reset()

        assert action._elapsed == 0.0
        assert not action._done
        assert not action._paused
        assert not action._on_complete_called


class TestIntervalAction:
    """Test suite for IntervalAction class."""

    @pytest.fixture
    def interval_action(self):
        return MockIntervalAction(duration=1.0)

    def test_interval_action_duration(self, interval_action):
        """Test interval action duration handling."""
        assert interval_action.duration == 1.0
        assert not interval_action.done()

        interval_action.update(0.5)
        assert not interval_action.done()

        interval_action.update(0.5)
        assert interval_action.done()


class TestInstantAction:
    """Test suite for InstantAction class."""

    @pytest.fixture
    def instant_action(self):
        return MockInstantAction()

    def test_instant_action_completion(self, instant_action):
        """Test instant action immediate completion."""
        assert instant_action.done()
        instant_action.update(0.0)
        assert instant_action.done()


class TestGroupAction:
    """Test suite for GroupAction class."""

    @pytest.fixture
    def sprite_list(self):
        return arcade.SpriteList()

    @pytest.fixture
    def mock_action(self):
        return MockAction()

    @pytest.fixture
    def group_action(self, sprite_list, mock_action):
        return GroupAction(sprite_list, mock_action)

    def test_group_action_initialization(self, group_action, sprite_list, mock_action):
        """Test group action initialization."""
        assert group_action.sprite_list == sprite_list
        assert group_action.action == mock_action
        assert group_action.actions == []

    def test_group_action_lifecycle(self, group_action, sprite_list):
        """Test group action lifecycle with multiple sprites."""
        # Add sprites
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        # Start
        group_action.start()
        assert len(group_action.actions) == 2
        assert all(action.start_called for action in group_action.actions)

        # Update
        group_action.update(0.5)
        assert all(action.update_called for action in group_action.actions)
        assert not group_action.done()

        # Complete
        group_action.update(0.5)
        assert group_action.done()

        # Stop
        group_action.stop()
        assert len(group_action.actions) == 0


class TestActionSprite:
    """Test suite for ActionSprite class."""

    @pytest.fixture
    def action_sprite(self):
        sprite = ActionSprite(filename=":resources:images/items/star.png")  # Using a dummy filename
        sprite.texture = Texture.create_empty("test", (1, 1))
        return sprite

    @pytest.fixture
    def mock_action(self):
        return MockAction()

    def test_action_sprite_initialization(self, action_sprite):
        """Test action sprite initialization."""
        assert isinstance(action_sprite, arcade.Sprite)
        assert action_sprite._actions == []

    def test_action_sprite_do_action(self, action_sprite, mock_action):
        """Test applying action to sprite."""
        action_sprite.do(mock_action)
        assert len(action_sprite._actions) == 1
        assert mock_action.target == action_sprite

    def test_action_sprite_update(self, action_sprite, mock_action):
        """Test sprite action updates."""
        action_sprite.do(mock_action)
        action_sprite.update(0.5)
        assert mock_action.update_called

    def test_action_sprite_clear_actions(self, action_sprite, mock_action):
        """Test clearing sprite actions."""
        action_sprite.do(mock_action)
        action_sprite.clear_actions()
        assert len(action_sprite._actions) == 0

    def test_action_sprite_pause_resume(self, action_sprite, mock_action):
        """Test sprite action pause/resume."""
        action_sprite.do(mock_action)

        action_sprite.pause()
        assert mock_action._paused

        action_sprite.resume()
        assert not mock_action._paused
