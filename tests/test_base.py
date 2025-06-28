"""Test suite for base.py - Core Action system architecture."""


import arcade
import pytest
from arcade.texture import Texture

from actions.base import ActionSprite
from actions.group import (
    AttackGroup,
    CirclePattern,
    GridPattern,
    LinePattern,
    SpriteGroup,
)
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

    def test_action_initialization(self, action):
        """Test basic action initialization."""

        def condition_func():
            return False

        action = Action(condition_func=condition_func, tag="test")

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

        # With batch optimization, movement actions don't create individual actions
        if group_action._use_batch_optimization:
            # Verify batch optimization is working
            assert len(group_action.actions) == 0
            assert len(group_action._batch_start_positions) == 2
            assert group_action._batch_total_change == (100, 0)
        else:
            # Fallback behavior for non-movement actions
            assert len(group_action.actions) == 2
            # Verify all actions are MoveBy by checking they have the same delta and duration
            for action in group_action.actions:
                assert action.delta == (100, 0)
                assert action.duration == 1.0

        # Test update behavior
        group_action.update(0.5)
        assert not group_action.done

        group_action.update(0.5)
        assert group_action.done

        group_action.stop()
        if group_action._use_batch_optimization:
            assert len(group_action._batch_start_positions) == 0
        else:
            assert len(group_action.actions) == 0


class TestActionSprite:
    """Test suite for ActionSprite class."""

    @pytest.fixture
    def action_sprite(self):
        """Fixture for creating a test ActionSprite."""
        # Use a real image file for the sprite
        return ActionSprite(":resources:images/items/star.png", scale=1.0)

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


class TestPatterns:
    """Test suite for attack patterns."""

    @pytest.fixture
    def sprite_group(self):
        """Create a sprite group with test sprites."""
        group = SpriteGroup()
        for i in range(5):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.center_x = 100 + i * 50
            sprite.center_y = 300
            group.append(sprite)
        return group

    @pytest.fixture
    def attack_group(self, sprite_group):
        """Create an attack group for testing."""
        return AttackGroup(sprite_group, name="test_group")

    def test_line_pattern_initialization(self):
        """Test LinePattern initialization."""
        pattern = LinePattern(spacing=75.0)
        assert pattern.name == "line"
        assert pattern.spacing == 75.0

    def test_line_pattern_apply(self, attack_group):
        """Test LinePattern apply method."""
        pattern = LinePattern(spacing=50.0)
        pattern.apply(attack_group, start_x=100, start_y=200)

        # Check that sprites are positioned in a line
        for i, sprite in enumerate(attack_group.sprites):
            expected_x = 100 + i * 50.0
            assert sprite.center_x == expected_x
            assert sprite.center_y == 200

    def test_grid_pattern_initialization(self):
        """Test GridPattern initialization."""
        pattern = GridPattern(rows=3, cols=4, spacing_x=60.0, spacing_y=40.0)
        assert pattern.name == "grid"
        assert pattern.rows == 3
        assert pattern.cols == 4
        assert pattern.spacing_x == 60.0
        assert pattern.spacing_y == 40.0

    def test_grid_pattern_apply(self, attack_group):
        """Test GridPattern apply method."""
        pattern = GridPattern(rows=2, cols=3, spacing_x=60.0, spacing_y=50.0)
        pattern.apply(attack_group, start_x=100, start_y=500)

        # Check that sprites are positioned in a grid
        for i, sprite in enumerate(attack_group.sprites):
            row = i // 3
            col = i % 3
            expected_x = 100 + col * 60.0
            expected_y = 500 - row * 50.0
            assert sprite.center_x == expected_x
            assert sprite.center_y == expected_y

    def test_circle_pattern_initialization(self):
        """Test CirclePattern initialization."""
        pattern = CirclePattern(radius=120.0)
        assert pattern.name == "circle"
        assert pattern.radius == 120.0

    def test_circle_pattern_apply(self, attack_group):
        """Test CirclePattern apply method."""
        pattern = CirclePattern(radius=100.0)
        pattern.apply(attack_group, center_x=400, center_y=300)

        # Action with movement tag exists
        assert len(Action.get_actions_for_target(sprite, "movement")) == 1
        # No actions with effects tag
        assert len(Action.get_actions_for_target(sprite, "effects")) == 0

    def test_action_clone(self):
        """Test action cloning."""

        def condition_func():
            return False

        def on_condition_met():
            pass

        action = Action(
            condition_func=condition_func, on_condition_met=on_condition_met, check_interval=0.5, tag="test"
        )

        cloned = action.clone()

        assert cloned is not action
        assert cloned.condition_func == condition_func
        assert cloned.on_condition_met == on_condition_met
        assert cloned.check_interval == 0.5
        assert cloned.tag == "test"

    def test_action_for_each_sprite(self):
        """Test for_each_sprite helper method."""
        sprite_list = arcade.SpriteList()
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        action = Action(condition_func=lambda: False)
        action.target = sprite_list

        visited_sprites = []

        def visit_sprite(sprite):
            visited_sprites.append(sprite)

        action.for_each_sprite(visit_sprite)

        assert len(visited_sprites) == 2
        assert sprite1 in visited_sprites
        assert sprite2 in visited_sprites

    def test_action_condition_properties(self):
        """Test action condition properties."""
        action = Action(condition_func=lambda: False)

        assert not action.condition_met
        assert action.condition_data is None

        # Simulate condition being met
        action._condition_met = True
        action._condition_data = "test_data"

        assert action.condition_met
        assert action.condition_data == "test_data"
