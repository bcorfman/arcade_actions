"""Test suite for base.py - Core Action system architecture."""

import arcade

from actions.base import Action


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class MockAction(Action):
    """A concrete Action subclass for testing."""

    def apply_effect(self) -> None:
        pass

    def clone(self) -> Action:
        new_action = MockAction(
            condition_func=self.condition_func,
            on_condition_met=self.on_condition_met,
            check_interval=self.check_interval,
        )
        new_action.tag = self.tag
        return new_action


class TestAction:
    """Test suite for base Action class."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_action_initialization(self):
        """Test basic action initialization."""

        def condition_func():
            return False

        action = MockAction(condition_func=condition_func)
        action.tag = "test"

        assert action.target is None
        assert action.tag == "test"
        assert not action._is_active
        assert not action.done
        assert action.condition_func == condition_func
        assert not action._condition_met

    def test_action_apply_registration(self):
        """Test that applying an action registers it globally."""
        sprite = create_test_sprite()
        action = MockAction(condition_func=lambda: False)

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

        action = MockAction(condition_func=time_condition)
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

        def on_condition_met(data=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        def condition():
            return {"result": "success"}

        action = MockAction(condition_func=condition, on_condition_met=on_condition_met)
        action.apply(sprite)

        Action.update_all(0.016)

        assert callback_called
        assert callback_data == {"result": "success"}

    def test_action_stop_instance(self):
        """Test stopping a specific action instance."""
        sprite = create_test_sprite()
        action = MockAction(condition_func=lambda: False)
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
        action1 = MockAction(condition_func=lambda: False)
        action2 = MockAction(condition_func=lambda: False)

        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="effects")

        Action.stop_actions_for_target(sprite, "movement")

        assert not action1._is_active
        assert action2._is_active

    def test_action_stop_all_target(self):
        """Test stopping all actions for a target."""
        sprite = create_test_sprite()
        action1 = MockAction(condition_func=lambda: False)
        action2 = MockAction(condition_func=lambda: False)

        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="effects")

        Action.stop_actions_for_target(sprite)

        assert not action1._is_active
        assert not action2._is_active

    def test_action_clear_all(self):
        """Test clearing all active actions."""
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        action1 = MockAction(condition_func=lambda: False)
        action2 = MockAction(condition_func=lambda: False)

        action1.apply(sprite1)
        action2.apply(sprite2)

        assert len(Action._active_actions) == 2

        Action.clear_all()

        assert len(Action._active_actions) == 0

    def test_action_get_active_count(self):
        """Test getting the count of active actions."""
        sprite = create_test_sprite()

        assert len(Action._active_actions) == 0

        action1 = MockAction(condition_func=lambda: False)
        action2 = MockAction(condition_func=lambda: False)
        action1.apply(sprite)
        action2.apply(sprite)

        assert len(Action._active_actions) == 2

    def test_action_get_actions_for_target(self):
        """Test getting actions for target by tag."""
        sprite = create_test_sprite()
        action1 = MockAction(condition_func=lambda: False)
        action2 = MockAction(condition_func=lambda: False)

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
        action = MockAction(condition_func=lambda: False)

        # No actions yet
        assert len(Action.get_actions_for_target(sprite, "movement")) == 0

        action.apply(sprite, tag="movement")

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

        action = MockAction(condition_func=condition_func, on_condition_met=on_condition_met, check_interval=0.5)
        action.tag = "test"

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

        action = MockAction(condition_func=lambda: False)
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
        action = MockAction(condition_func=lambda: False)

        assert not action.condition_met
        assert action.condition_data is None

        # Simulate condition being met
        action._condition_met = True
        action._condition_data = "test_data"

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
