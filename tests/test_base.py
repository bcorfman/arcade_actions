"""Test suite for base.py - Core Action system architecture."""

import math

import arcade
import pytest
from arcade.texture import Texture

from actions.base import ActionSprite
from actions.game_clock import GameClock, Scheduler
from actions.group import (
    AttackGroup,
    CirclePattern,
    GridPattern,
    LinePattern,
    SpriteGroup,
    VFormationPattern,
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
        assert not group_action.done

        group_action.update(0.5)
        assert group_action.done

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
        clock = GameClock()
        scheduler = Scheduler(clock)
        return AttackGroup(sprite_group, clock, scheduler, name="test_group")

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

        # Check that sprites are positioned in a circle
        count = len(attack_group.sprites)
        angle_step = 2 * math.pi / count
        for i, sprite in enumerate(attack_group.sprites):
            angle = i * angle_step
            expected_x = 400 + math.cos(angle) * 100.0
            expected_y = 300 + math.sin(angle) * 100.0
            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1

    def test_circle_pattern_empty_group(self):
        """Test CirclePattern with empty sprite group."""
        empty_group = SpriteGroup()
        clock = GameClock()
        scheduler = Scheduler(clock)
        attack_group = AttackGroup(empty_group, clock, scheduler, name="empty_test")

        pattern = CirclePattern(radius=100.0)
        # Should not raise an exception
        pattern.apply(attack_group, center_x=400, center_y=300)

    def test_v_formation_pattern_initialization(self):
        """Test VFormationPattern initialization."""
        pattern = VFormationPattern(angle=60.0, spacing=75.0)
        assert pattern.name == "v_formation"
        assert pattern.spacing == 75.0

    def test_v_formation_pattern_apply(self, attack_group):
        """Test VFormationPattern apply method."""
        pattern = VFormationPattern(angle=45.0, spacing=50.0)
        pattern.apply(attack_group, apex_x=400, apex_y=500)

        sprites = list(attack_group.sprites)

        # First sprite should be at apex
        assert sprites[0].center_x == 400
        assert sprites[0].center_y == 500

        # Check that remaining sprites are positioned correctly
        for i in range(1, len(sprites)):
            side = 1 if i % 2 == 1 else -1  # Alternate sides
            distance = (i + 1) // 2 * 50.0

            offset_x = side * math.cos(math.radians(45.0)) * distance
            offset_y = -math.sin(math.radians(45.0)) * distance

            expected_x = 400 + offset_x
            expected_y = 500 + offset_y

            assert abs(sprites[i].center_x - expected_x) < 0.1
            assert abs(sprites[i].center_y - expected_y) < 0.1

    def test_v_formation_pattern_empty_group(self):
        """Test VFormationPattern with empty sprite group."""
        empty_group = SpriteGroup()
        clock = GameClock()
        scheduler = Scheduler(clock)
        attack_group = AttackGroup(empty_group, clock, scheduler, name="empty_test")

        pattern = VFormationPattern()
        # Should not raise an exception
        pattern.apply(attack_group, apex_x=400, apex_y=500)


class TestAttackGroup:
    """Test suite for AttackGroup class."""

    @pytest.fixture
    def sprite_group(self):
        """Create a sprite group with test sprites."""
        group = SpriteGroup()
        for i in range(2):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.center_x = i * 100
            sprite.center_y = i * 100
            group.append(sprite)
        return group

    @pytest.fixture
    def clock(self):
        """Create a game clock for testing."""
        return GameClock()

    @pytest.fixture
    def scheduler(self, clock):
        """Create a scheduler for testing."""
        return Scheduler(clock)

    @pytest.fixture
    def attack_group(self, sprite_group, clock, scheduler):
        """Create an attack group for testing."""
        return AttackGroup(sprite_group, clock, scheduler, name="test_attack_group")

    def test_attack_group_initialization(self, attack_group, sprite_group, clock, scheduler):
        """Test AttackGroup initialization."""
        assert attack_group.sprites == sprite_group
        assert attack_group.clock == clock
        assert attack_group.scheduler == scheduler
        assert attack_group.name == "test_attack_group"
        assert attack_group.actions == []
        assert not attack_group.is_destroyed
        assert attack_group.parent is None
        assert attack_group.children == []
        assert not attack_group._paused

    def test_attack_group_do_action(self, attack_group):
        """Test applying an action to the attack group."""
        move_action = MoveBy((50, 50), 1.0)
        group_action = attack_group.do(move_action)

        assert len(attack_group.actions) == 1
        assert attack_group.actions[0] == group_action
        assert len(group_action.actions) == len(attack_group.sprites)

    def test_attack_group_update(self, attack_group):
        """Test updating the attack group."""
        move_action = MoveBy((50, 50), 1.0)
        attack_group.do(move_action)

        # Store initial positions
        initial_positions = [(s.center_x, s.center_y) for s in attack_group.sprites]

        attack_group.update(0.5)

        # Positions should have changed
        current_positions = [(s.center_x, s.center_y) for s in attack_group.sprites]
        assert current_positions != initial_positions

    def test_attack_group_pause_resume(self, attack_group, clock):
        """Test pausing and resuming the attack group."""
        move_action = MoveBy((50, 50), 1.0)
        attack_group.do(move_action)

        # Pause via clock
        clock.paused = True
        attack_group.update(0.5)

        # Actions should be paused
        for action in attack_group.actions[0].actions:
            assert action._paused

    def test_attack_group_schedule_attack(self, attack_group):
        """Test scheduling attacks."""
        callback_called = False

        def test_callback():
            nonlocal callback_called
            callback_called = True

        task_id = attack_group.schedule_attack(0.1, test_callback)
        assert task_id in attack_group.scheduled_tasks

    def test_attack_group_breakaway(self, attack_group):
        """Test breaking away sprites from the group."""
        sprites_to_break = [attack_group.sprites[0]]
        new_group = attack_group.breakaway(sprites_to_break)

        assert len(attack_group.sprites) == 1
        assert len(new_group.sprites) == 1
        assert new_group in attack_group.children
        assert new_group.parent == attack_group

    def test_attack_group_destroy(self, attack_group):
        """Test destroying the attack group."""
        # Add some actions and schedule tasks
        move_action = MoveBy((50, 50), 1.0)
        attack_group.do(move_action)

        callback_called = False

        def on_destroy(group):
            nonlocal callback_called
            callback_called = True

        attack_group.on_destroy(on_destroy)
        attack_group.destroy()

        assert attack_group.is_destroyed
        assert len(attack_group.actions) == 0
        assert len(attack_group.scheduled_tasks) == 0
        assert callback_called

    def test_attack_group_callbacks(self, attack_group):
        """Test attack group callbacks."""
        destroy_called = False
        breakaway_called = False

        def on_destroy(group):
            nonlocal destroy_called
            destroy_called = True

        def on_breakaway(group):
            nonlocal breakaway_called
            breakaway_called = True

        attack_group.on_destroy(on_destroy)
        attack_group.on_breakaway(on_breakaway)

        # Test breakaway callback
        sprites_to_break = [attack_group.sprites[0]]
        attack_group.breakaway(sprites_to_break)
        assert breakaway_called

        # Test destroy callback
        attack_group.destroy()
        assert destroy_called

    def test_attack_group_empty_sprite_destruction(self, clock, scheduler):
        """Test that attack group destroys itself when no sprites remain."""
        # Create group with sprites
        sprite_group = SpriteGroup()
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite_group.append(sprite)

        attack_group = AttackGroup(sprite_group, clock, scheduler)

        # Remove all sprites
        sprite_group.clear()

        # Update should trigger destruction
        attack_group.update(0.1)
        assert attack_group.is_destroyed
