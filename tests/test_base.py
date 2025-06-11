"""Test suite for base.py - Core Action system architecture."""

import arcade
import pytest
from arcade.texture import Texture

from actions.base import ActionSprite
from actions.game_clock import GameClock
from actions.group import SpriteGroup
from actions.interval import MoveBy


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with a 1x1 transparent texture for testing."""
    texture = Texture.create_empty("test", (1, 1))
    sprite = arcade.Sprite()
    sprite.texture = texture
    return sprite


class TestAction:
    """Test suite for base Action class."""

    @pytest.fixture
    def action(self):
        # Use a real, simple action for testing
        return MoveBy((100, 0), duration=1.0)

    @pytest.fixture
    def sprite(self):
        return ActionSprite(":resources:images/items/star.png")

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

    def test_action_lifecycle(self, action, sprite):
        """Test complete action lifecycle."""
        sprite.do(action)
        assert action.target == sprite
        assert not action.done

        sprite.update(0.5)
        assert action._elapsed == 0.5
        assert not action.done

        sprite.update(0.5)
        assert action.done

        sprite.clear_actions()
        assert action.target is None

    def test_action_pause_resume(self, action, sprite, clock):
        """Test action pause/resume functionality."""
        sprite._clock = clock
        sprite.do(action)
        sprite.update(0.5)
        assert action._elapsed == 0.5

        sprite.pause()
        assert action._paused
        sprite.update(0.5)
        assert action._elapsed == 0.5

        sprite.resume()
        assert not action._paused
        sprite.update(0.5)
        assert action._elapsed == 1.0

    def test_action_completion_callback(self, action, sprite):
        """Test action completion callback."""
        callback_called = False

        def on_complete():
            nonlocal callback_called
            callback_called = True

        action.on_complete(on_complete)
        sprite.do(action)
        sprite.update(1.0)
        assert callback_called

    def test_action_reset(self, action, sprite):
        """Test action reset functionality."""
        sprite.do(action)
        sprite.update(0.5)
        action.reset()

        assert action._elapsed == 0.0
        assert not action.done
        assert not action._paused
        assert not action._on_complete_called


class TestIntervalAction:
    """Test suite for IntervalAction class."""

    @pytest.fixture
    def interval_action(self):
        return MoveBy((100, 0), duration=1.0)

    @pytest.fixture
    def sprite(self):
        return ActionSprite(":resources:images/items/star.png")

    def test_interval_action_duration(self, interval_action, sprite):
        """Test interval action duration handling."""
        assert interval_action.duration == 1.0
        assert not interval_action.done

        sprite.do(interval_action)
        sprite.update(0.5)
        assert not interval_action.done

        sprite.update(0.5)
        assert interval_action.done


class TestGroupAction:
    """Test suite for GroupAction class."""

    @pytest.fixture
    def move_action(self):
        return MoveBy((100, 0), duration=1.0)

    @pytest.fixture
    def sprite_group(self):
        return SpriteGroup()

    def test_group_action_initialization(self, sprite_group, move_action):
        """Test group action initialization."""
        group_action = sprite_group.do(move_action)
        assert group_action.group == list(sprite_group)
        assert group_action.template == move_action
        assert group_action.actions == []

    def test_group_action_lifecycle(self, sprite_group, move_action):
        """Test group action lifecycle with multiple sprites."""
        sprite1 = ActionSprite(":resources:images/items/star.png")
        sprite2 = ActionSprite(":resources:images/items/star.png")
        sprite_group.append(sprite1)
        sprite_group.append(sprite2)

        group_action = sprite_group.do(move_action)
        assert len(group_action.actions) == 2
        assert all(isinstance(a, MoveBy) for a in group_action.actions)

        group_action.update(0.5)
        assert all(a._elapsed > 0 for a in group_action.actions)
        assert not group_action.done()

        group_action.update(0.5)
        assert group_action.done()

        group_action.stop()
        assert len(group_action.actions) == 0


class TestActionSprite:
    """Test suite for ActionSprite class."""

    @pytest.fixture
    def action_sprite(self):
        """Fixture for creating a test ActionSprite."""
        # Use a real image file for the sprite
        return ActionSprite(":resources:images/items/star.png", scale=1.0)

    @pytest.fixture
    def game_clock(self):
        """Fixture for creating a GameClock."""
        return GameClock()

    def test_action_sprite_initialization(self, action_sprite):
        """Test ActionSprite initialization."""
        assert action_sprite._action is None
        assert not action_sprite.is_busy()

    def test_action_sprite_do_action(self, action_sprite):
        """Test applying an action to the sprite."""
        move_action = MoveBy((100, 0), 1.0)
        action_sprite.do(move_action)
        assert action_sprite._action == move_action
        assert action_sprite.is_busy()

    def test_action_sprite_update(self, action_sprite):
        """Test updating the sprite's action."""
        move_action = MoveBy((100, 0), 1.0)
        action_sprite.do(move_action)
        action_sprite.update(0.5)
        assert action_sprite.center_x > 0
        assert not action_sprite._action.done

    def test_action_sprite_clear_actions(self, action_sprite):
        """Test clearing actions from the sprite."""
        move_action = MoveBy((100, 0), 1.0)
        action_sprite.do(move_action)
        action_sprite.clear_actions()
        assert action_sprite._action is None
        assert not action_sprite.is_busy()

    def test_action_sprite_pause_resume(self, action_sprite):
        """Test pausing and resuming the sprite's action."""
        move_action = MoveBy((100, 0), 1.0)
        action_sprite.do(move_action)
        action_sprite.update(0.5)
        initial_x = action_sprite.center_x

        action_sprite.pause()
        action_sprite.update(0.5)
        assert action_sprite.center_x == initial_x

        action_sprite.resume()
        action_sprite.update(0.5)
        assert action_sprite.center_x > initial_x

    def test_action_sprite_game_clock_integration(self, action_sprite, game_clock):
        """Test integration with a game clock for pause/resume."""
        sprite_with_clock = ActionSprite(":resources:images/items/star.png", scale=1.0, clock=game_clock)
        move_action = MoveBy((100, 0), 1.0)
        sprite_with_clock.do(move_action)
        sprite_with_clock.update(0.5)
        initial_x = sprite_with_clock.center_x

        game_clock.paused = True
        sprite_with_clock.update(0.5)
        assert sprite_with_clock.center_x == initial_x

        game_clock.paused = False
        sprite_with_clock.update(0.5)
        assert sprite_with_clock.center_x > initial_x

    def test_action_sprite_action_replacement(self, action_sprite):
        """Test replacing an existing action with a new one."""
        move_action1 = MoveBy((100, 0), 1.0)
        move_action2 = MoveBy((0, 100), 1.0)

        action_sprite.do(move_action1)
        action_sprite.do(move_action2)
        assert action_sprite._action == move_action2

        action_sprite.update(0.5)
        assert action_sprite.center_x == 0
        assert action_sprite.center_y > 0

    def test_action_sprite_action_completion(self, action_sprite):
        """Test action completion and cleanup."""
        move_action = MoveBy((100, 0), 1.0)
        action_sprite.do(move_action)

        # Before completion, action should exist and not be done
        assert action_sprite._action == move_action
        assert not move_action.done
        assert action_sprite.is_busy()

        # After completion, action should be cleaned up automatically
        action_sprite.update(1.0)
        assert move_action.done  # The action instance itself is done
        assert action_sprite._action is None  # But ActionSprite cleaned it up
        assert not action_sprite.is_busy()  # Sprite is no longer busy

    def test_action_sprite_action_sequence(self, action_sprite):
        """Test running a sequence of actions."""
        move1 = MoveBy((100, 0), 1.0)
        move2 = MoveBy((0, 100), 1.0)
        sequence = move1 + move2

        action_sprite.do(sequence)

        # After first action completes, sprite should be at (100, 0) and still busy with second action
        action_sprite.update(1.0)
        assert action_sprite.center_x == 100
        assert action_sprite.center_y == 0
        assert action_sprite.is_busy()  # Still busy with second action

        # After second action completes, sprite should be at (100, 100) and no longer busy
        action_sprite.update(1.0)
        assert action_sprite.center_x == 100
        assert action_sprite.center_y == 100
        assert not action_sprite.is_busy()  # No longer busy
