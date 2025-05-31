"""Test suite for base.py - Core Action system architecture."""

import copy

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

    def update(self, delta_time: float) -> float:
        self.update_called = True
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.done = True
        return delta_time

    def stop(self) -> None:
        self.stop_called = True
        super().stop()


class MockIntervalAction(IntervalAction):
    """Mock interval action for testing."""

    def __init__(self, duration: float = 1.0):
        super().__init__(duration)
        self.start_called = False
        self.stop_called = False
        self.update_called = False

    def start(self) -> None:
        self.start_called = True

    def update(self, delta_time: float) -> float:
        self.update_called = True
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.done = True
        return delta_time

    def stop(self) -> None:
        self.stop_called = True
        super().stop()


class MockInstantAction(InstantAction):
    """Mock instant action for testing."""

    def __init__(self):
        super().__init__()
        self.update_called = False
        self.done = True  # Instant actions are done immediately

    def start(self) -> None:
        """Start the instant action."""
        self.done = True

    def update(self, delta_time: float) -> float:
        self.update_called = True
        self.done = True
        return delta_time


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
        assert not action.done
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
        assert not action.done

        # Complete
        action.update(0.5)
        assert action.done

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
        action.done = True  # Set completion directly
        action.update(1.0)  # Trigger callback
        assert callback_called

    def test_action_reset(self, action):
        """Test action reset functionality."""
        action.start()
        action.update(0.5)
        action.reset()

        assert action._elapsed == 0.0
        assert not action.done
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
        assert not interval_action.done

        interval_action.update(0.5)
        assert not interval_action.done

        interval_action.update(0.5)
        assert interval_action.done


class TestInstantAction:
    """Test suite for InstantAction class."""

    @pytest.fixture
    def instant_action(self):
        return MockInstantAction()

    def test_instant_action_completion(self, instant_action):
        """Test instant action immediate completion."""
        assert instant_action.done
        instant_action.update(0.0)
        assert instant_action.done


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
        sprite1 = ActionSprite(filename=":resources:images/items/star.png")
        sprite2 = ActionSprite(filename=":resources:images/items/star.png")
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        # Start
        group_action.start()
        assert len(group_action.actions) == 2
        assert all(action.start_called for action in group_action.actions)

        # Update
        group_action.update(0.5)
        assert all(action.update_called for action in group_action.actions)
        assert not group_action.done

        # Complete
        group_action.update(0.5)
        assert group_action.done

        # Stop
        group_action.stop()
        assert len(group_action.actions) == 0


class TestActionSprite:
    """Test suite for ActionSprite class."""

    @pytest.fixture
    def action_sprite(self):
        sprite = ActionSprite(filename=":resources:images/items/star.png")
        sprite.texture = Texture.create_empty("test", (1, 1))
        return sprite

    @pytest.fixture
    def mock_action(self):
        return MockAction()

    @pytest.fixture
    def game_clock(self):
        return GameClock()

    def test_action_sprite_initialization(self, action_sprite):
        """Test action sprite initialization."""
        assert isinstance(action_sprite, arcade.Sprite)
        assert action_sprite._actions == []
        assert action_sprite._action is None
        assert not action_sprite._paused

    def test_action_sprite_do_action(self, action_sprite, mock_action):
        """Test applying action to sprite."""
        action = action_sprite.do(mock_action)
        assert len(action_sprite._actions) == 1
        assert mock_action.target == action_sprite
        assert action_sprite._action == mock_action
        assert action == mock_action

    def test_action_sprite_update(self, action_sprite, mock_action):
        """Test sprite action updates."""
        action_sprite.do(mock_action)
        action_sprite.update(0.5)
        assert mock_action.update_called
        assert mock_action._elapsed == 0.5

    def test_action_sprite_clear_actions(self, action_sprite, mock_action):
        """Test clearing sprite actions."""
        action_sprite.do(mock_action)
        action_sprite.clear_actions()
        assert len(action_sprite._actions) == 0
        assert action_sprite._action is None
        assert mock_action.stop_called

    def test_action_sprite_pause_resume(self, action_sprite, mock_action):
        """Test sprite action pause/resume."""
        action_sprite.do(mock_action)

        action_sprite.pause()
        assert action_sprite._paused
        assert mock_action._paused

        action_sprite.resume()
        assert not action_sprite._paused
        assert not mock_action._paused

    def test_action_sprite_game_clock_integration(self, action_sprite, mock_action, game_clock):
        """Test sprite integration with game clock."""
        action_sprite = ActionSprite(filename=":resources:images/items/star.png", clock=game_clock)
        action_sprite.do(mock_action)

        game_clock.paused = True
        assert action_sprite._paused
        assert mock_action._paused

        game_clock.paused = False
        assert not action_sprite._paused
        assert not mock_action._paused

    def test_action_sprite_multiple_actions(self, action_sprite):
        """Test handling multiple actions."""
        action1 = MockAction()
        action2 = MockAction()

        action_sprite.do(action1)
        action_sprite.do(action2)

        assert len(action_sprite._actions) == 2
        assert action_sprite._action == action2  # Most recent action

        action_sprite.update(0.5)
        assert action1.update_called
        assert action2.update_called

    def test_action_sprite_action_completion(self, action_sprite):
        """Test action completion handling."""
        action = MockAction()
        action.done = True  # Simulate completed action

        action_sprite.do(action)
        action_sprite.update(0.5)

        # Action should be removed after update
        assert len(action_sprite._actions) == 0
        assert action_sprite._action is None
        assert action.stop_called

    def test_action_sprite_cleanup(self, game_clock):
        """Test sprite cleanup on deletion."""
        sprite = ActionSprite(filename=":resources:images/items/star.png", clock=game_clock)
        action = MockAction()
        sprite.do(action)

        # Store callback before cleanup
        callback = sprite._on_pause_state_changed

        # Explicitly clean up
        sprite.cleanup()
        assert callback not in game_clock._subscribers

    def test_action_sprite_has_active_actions(self, action_sprite, mock_action):
        """Test checking for active actions."""
        assert not action_sprite.has_active_actions()

        action_sprite.do(mock_action)
        assert action_sprite.has_active_actions()

        mock_action.done = True
        action_sprite.update(0.5)  # This should remove the completed action
        assert not action_sprite.has_active_actions()

    def test_action_sprite_is_busy(self, action_sprite, mock_action):
        """Test checking if sprite is busy with current action."""
        assert not action_sprite.is_busy()

        action_sprite.do(mock_action)
        assert action_sprite.is_busy()

        mock_action.done = True
        action_sprite.update(0.5)  # This should remove the completed action
        assert not action_sprite.is_busy()

    def test_action_sprite_action_sequence(self, action_sprite):
        """Test running a sequence of actions."""
        action1 = MockAction()
        action2 = MockAction()
        action3 = MockAction()

        # Run actions in sequence
        action_sprite.do(action1)
        action_sprite.update(0.5)
        action1.done = True
        action_sprite.update(0.5)

        action_sprite.do(action2)
        action_sprite.update(0.5)
        action2.done = True
        action_sprite.update(0.5)

        action_sprite.do(action3)
        action_sprite.update(0.5)

        assert len(action_sprite._actions) == 1
        assert action_sprite._action == action3
        assert action1.stop_called
        assert action2.stop_called
        assert not action3.stop_called


class GroupAction(Action):
    """Apply an action to all sprites in a sprite list."""

    def __init__(self, sprite_list: arcade.SpriteList, action: Action):
        super().__init__()
        self.sprite_list = sprite_list
        self.action = action
        self.actions: list[Action] = []

    def start(self) -> None:
        """Start the action on all sprites."""
        self.actions = []
        for sprite in self.sprite_list:
            if isinstance(sprite, ActionSprite):
                action = copy.deepcopy(self.action)
                sprite.do(action)
                self.actions.append(action)

    def update(self, delta_time: float) -> None:
        """Update all sprite actions."""
        for action in self.actions:
            action.update(delta_time)
        # Check if all child actions are done
        self.done = all(action.done for action in self.actions)

    def stop(self) -> None:
        """Stop all sprite actions and clear the actions list."""
        for action in self.actions:
            action.stop()
        self.actions = []
        super().stop()
