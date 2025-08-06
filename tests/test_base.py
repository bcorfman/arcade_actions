"""Test suite for base.py - Core Action system architecture."""

import arcade

from actions import Action


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class MockAction(Action):
    """A concrete Action subclass for testing."""

    def __init__(self, duration=0.1, name="mock", condition=None, on_stop=None):
        if condition is None:
            condition = lambda: False  # Never stop by default
        super().__init__(
            condition=condition,
            on_stop=on_stop,
        )
        self.duration = duration
        self.name = name
        self.time_elapsed = 0.0
        self.started = False
        self.stopped = False

    def start(self) -> None:
        """Called when the action begins."""
        super().start()
        self.started = True

    def stop(self) -> None:
        """Called when the action ends."""
        super().stop()
        self.stopped = True

    def update_effect(self, delta_time: float) -> None:
        self.time_elapsed += delta_time
        if self.time_elapsed >= self.duration:
            self.done = True

    def clone(self) -> Action:
        cloned = MockAction(
            duration=self.duration,
            name=self.name,
            condition=self.condition,
            on_stop=self.on_stop,
        )
        cloned.tag = self.tag
        return cloned


class TestAction:
    """Test suite for base Action class."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_action_initialization(self):
        """Test basic action initialization."""

        def condition():
            return False

        action = MockAction(condition=condition)
        action.tag = "test"

        assert action.target is None
        assert action.tag == "test"
        assert not action._is_active
        assert not action.done
        assert action.condition == condition
        assert not action._condition_met

    def test_action_apply_registration(self):
        """Test that applying an action registers it globally."""
        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)

        action.apply(sprite, tag="test")

        assert action.target == sprite
        assert action.tag == "test"
        assert action._is_active
        assert action in Action._active_actions

    def test_action_global_update(self):
        """Test global action update system."""
        sprite = create_test_sprite()

        # Create action that completes after some time
        time_elapsed = 0

        def time_condition():
            nonlocal time_elapsed
            time_elapsed += 0.016  # Simulate frame time
            return time_elapsed >= 1.0

        action = MockAction(condition=time_condition)
        action.apply(sprite)

        # Update multiple times - allow extra iterations for the math to work out
        for _ in range(70):  # ~1 second at 60fps with some buffer
            Action.update_all(0.016)
            if action.done:
                break

        assert action.done
        assert action not in Action._active_actions

    def test_action_condition_callback(self):
        """Test action condition callback."""
        sprite = create_test_sprite()
        callback_called = False
        callback_data = None

        def on_stop(data=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        def condition():
            return {"result": "success"}

        action = MockAction(condition=condition, on_stop=on_stop)
        action.apply(sprite)

        Action.update_all(0.016)

        assert callback_called
        assert callback_data == {"result": "success"}

    def test_action_stop_instance(self):
        """Test stopping a specific action instance."""
        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        assert action._is_active
        assert action in Action._active_actions

        action.stop()

        assert not action._is_active
        assert action.done
        assert action not in Action._active_actions

    def test_action_stop_by_tag(self):
        """Test stopping actions by tag."""
        sprite = create_test_sprite()
        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)

        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="effects")

        Action.stop_actions_for_target(sprite, "movement")

        assert not action1._is_active
        assert action2._is_active

    def test_action_stop_all_target(self):
        """Test stopping all actions for a target."""
        sprite = create_test_sprite()
        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)

        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="effects")

        Action.stop_actions_for_target(sprite)

        assert not action1._is_active
        assert not action2._is_active

    def test_action_stop_all(self):
        """Test clearing all active actions."""
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)

        action1.apply(sprite1)
        action2.apply(sprite2)

        assert len(Action._active_actions) == 2

        Action.stop_all()

        assert len(Action._active_actions) == 0

    def test_action_get_active_count(self):
        """Test getting the count of active actions."""
        sprite = create_test_sprite()

        assert len(Action._active_actions) == 0

        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)
        action1.apply(sprite)
        action2.apply(sprite)

        assert len(Action._active_actions) == 2

    def test_action_get_actions_for_target(self):
        """Test getting actions for target by tag."""
        sprite = create_test_sprite()
        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)

        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="effects")

        movement_actions = Action.get_actions_for_target(sprite, "movement")
        assert len(movement_actions) == 1
        assert action1 in movement_actions

        effects_actions = Action.get_actions_for_target(sprite, "effects")
        assert len(effects_actions) == 1
        assert action2 in effects_actions

    def test_action_check_tag_exists(self):
        """Test checking if actions with a tag exist for a target."""
        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)

        # No actions yet
        assert len(Action.get_actions_for_target(sprite, "movement")) == 0

        action.apply(sprite, tag="movement")

        # Action with movement tag exists
        assert len(Action.get_actions_for_target(sprite, "movement")) == 1
        # No actions with effects tag
        assert len(Action.get_actions_for_target(sprite, "effects")) == 0

    def test_action_clone(self):
        """Test action cloning."""

        def condition():
            return False

        def on_stop():
            pass

        action = MockAction(condition=condition, on_stop=on_stop)
        action.tag = "test"

        cloned = action.clone()

        assert cloned is not action
        assert cloned.condition == condition
        assert cloned.on_stop == on_stop
        assert cloned.tag == "test"

    def test_action_for_each_sprite(self):
        """Test for_each_sprite helper method."""
        sprite_list = arcade.SpriteList()
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        action = MockAction(condition=lambda: False)
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
        action = MockAction(condition=lambda: False)

        assert not action.condition_met
        assert action.condition_data is None

        # Simulate condition being met
        action.condition_met = True
        action.condition_data = "test_data"

        assert action.condition_met
        assert action.condition_data == "test_data"

    def test_action_set_factor_base(self):
        """Test that the base Action's set_factor does nothing."""
        action = MockAction()
        action.set_factor(0.5)  # Should not raise an error
        assert action._factor == 0.5

    def test_action_pause_resume(self):
        """Test pausing and resuming an action."""
        action = MockAction()
        assert not action._paused
        action.pause()
        assert action._paused
        action.resume()
        assert not action._paused
