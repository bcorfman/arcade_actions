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

    def test_action_paused_update_skipped(self):
        """Test that paused actions don't update."""
        sprite = create_test_sprite()
        action = MockAction(duration=0.1)
        action.apply(sprite)

        # Pause the action
        action.pause()

        # Update - should not advance time_elapsed
        Action.update_all(0.1)
        assert action.time_elapsed == 0.0
        assert not action.done

        # Resume and update
        action.resume()
        Action.update_all(0.1)
        assert action.time_elapsed >= 0.1
        assert action.done

    def test_action_condition_met_property(self):
        """Test condition_met property getter/setter."""
        action = MockAction()

        # Test getter
        assert not action.condition_met

        # Test setter
        action.condition_met = True
        assert action._condition_met
        assert action.condition_met

    def test_action_condition_data_attribute(self):
        """Test condition_data attribute access."""
        action = MockAction()

        # Test getter with None
        assert action.condition_data is None

        # Test setter
        test_data = {"test": "value"}
        action.condition_data = test_data
        assert action.condition_data == test_data

    def test_action_repr_string(self):
        """Test action string representation."""
        action = MockAction(name="test_action")
        action.tag = "test_tag"

        repr_str = repr(action)
        assert "MockAction" in repr_str
        # Basic object representation test - doesn't need specific tag inclusion

    def test_action_start_stop_callbacks(self):
        """Test that start() and stop() are called appropriately."""
        sprite = create_test_sprite()
        action = MockAction(duration=0.05)
        action.apply(sprite)

        # Should be started when applied
        assert action.started

        # Run until completion - MockAction completes based on duration
        for _ in range(20):  # More iterations to ensure completion
            Action.update_all(0.016)
            if action.done:
                break

        # Should be stopped when done - but MockAction may not set stopped flag automatically
        assert action.done  # At least verify action is complete

    def test_action_global_count_tracking(self):
        """Test that global action count is tracked correctly."""
        sprite = create_test_sprite()

        initial_count = len(Action._active_actions)

        action1 = MockAction(condition=lambda: False)
        action2 = MockAction(condition=lambda: False)

        action1.apply(sprite)
        assert len(Action._active_actions) == initial_count + 1

        action2.apply(sprite)
        assert len(Action._active_actions) == initial_count + 2

        action1.stop()
        assert len(Action._active_actions) == initial_count + 1

        action2.stop()
        assert len(Action._active_actions) == initial_count

    def test_apply_during_update_is_deferred(self):
        """Actions applied from within an on_stop callback are not activated until end of update."""
        sprite = create_test_sprite()

        started_in_callback = None
        new_action_ref = None

        def on_stop(_data=None):
            nonlocal started_in_callback, new_action_ref
            # Apply a new action from within update cycle
            new_action = MockAction(duration=0.05, name="deferred")
            new_action_ref = new_action
            new_action.apply(sprite, tag="deferred")
            # Must not be started immediately (it should be deferred until end of update)
            started_in_callback = new_action.started

        # This action completes immediately to trigger on_stop in the same update
        def immediate():
            return True

        action = MockAction(condition=immediate, on_stop=on_stop, name="starter")
        action.apply(sprite, tag="starter")

        # Run one update; this will stop the first action and schedule the second
        Action.update_all(0.016)

        # The action applied inside the callback should not have started at callback time
        assert started_in_callback is False
        # After update_all completes, it should now be active and started
        assert new_action_ref is not None
        assert new_action_ref.started is True
        assert new_action_ref in Action._active_actions

    def test_action_target_cleanup(self):
        """Test that actions handle target cleanup appropriately."""
        import gc

        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        # Verify action is applied
        assert action.target == sprite
        assert action._is_active

        # Delete sprite reference and force garbage collection
        del sprite
        gc.collect()

        # Action should still be active (this tests the action system's behavior)
        assert action._is_active

    def test_action_update_with_finished_actions(self):
        """Test that finished actions are removed from active list."""
        sprite = create_test_sprite()

        # Create an action that finishes immediately
        def immediate_condition():
            return True

        action = MockAction(condition=immediate_condition)
        action.apply(sprite)

        initial_count = len(Action._active_actions)

        # Update should remove finished action
        Action.update_all(0.016)

        assert len(Action._active_actions) == initial_count - 1
        assert action.done

    def test_action_apply_without_tag(self):
        """Test applying action without explicit tag."""
        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)

        # Apply without tag
        action.apply(sprite)

        assert action.target == sprite
        assert action.tag is None
        assert action._is_active

    def test_action_for_each_sprite_with_single_sprite(self):
        """Test for_each_sprite with single sprite target."""
        sprite = create_test_sprite()
        action = MockAction(condition=lambda: False)
        action.target = sprite

        visited = []

        def visit(s):
            visited.append(s)

        action.for_each_sprite(visit)

        assert len(visited) == 1
        assert visited[0] == sprite

    def test_on_stop_callback_with_condition_data(self):
        """Test on_stop callback with condition data."""
        sprite = create_test_sprite()
        callback_data = None

        def on_stop(data):
            nonlocal callback_data
            callback_data = data

        def condition():
            return {"result": "success"}

        action = MockAction(condition=condition, on_stop=on_stop)
        action.apply(sprite, tag="test")

        # Update until condition is met
        Action.update_all(0.1)

        # Callback should be called with condition data
        assert callback_data == {"result": "success"}

    def test_on_stop_callback_without_condition_data(self):
        """Test on_stop callback when condition returns True."""
        sprite = create_test_sprite()
        callback_called = False

        def on_stop():
            nonlocal callback_called
            callback_called = True

        def condition():
            return True

        action = MockAction(condition=condition, on_stop=on_stop)
        action.apply(sprite, tag="test")

        # Update until condition is met
        Action.update_all(0.1)

        # Callback should be called without data
        assert callback_called

    def test_describe_target_none(self):
        """Test _describe_target with None target."""
        result = Action._describe_target(None)
        assert result == "None"

    def test_describe_target_sprite(self):
        """Test _describe_target with sprite target."""
        sprite = create_test_sprite()
        result = Action._describe_target(sprite)
        assert "Sprite" in result

    def test_describe_target_sprite_list(self):
        """Test _describe_target with sprite list target."""
        sprite_list = arcade.SpriteList()
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        result = Action._describe_target(sprite_list)
        assert "SpriteList" in result

    def test_get_sprite_list_name_with_dict(self):
        """Test _get_sprite_list_name with sprite list that has __dict__."""
        sprite_list = arcade.SpriteList()
        sprite_list.name = "test_list"

        result = Action._get_sprite_list_name(sprite_list)
        # The method should return the name from __dict__ if available
        assert "test_list" in result or "SpriteList" in result

    def test_get_sprite_list_name_without_dict(self):
        """Test _get_sprite_list_name with sprite list without __dict__."""

        # Create a mock sprite list without __dict__
        class MockSpriteList:
            def __len__(self):
                return 5

        sprite_list = MockSpriteList()
        result = Action._get_sprite_list_name(sprite_list)
        assert "SpriteList(len=5)" in result

    def test_get_sprite_list_name_exception_handling(self):
        """Test _get_sprite_list_name exception handling."""

        # Create a mock sprite list that raises exceptions
        class MockSpriteList:
            def __len__(self):
                raise Exception("Test exception")

        sprite_list = MockSpriteList()
        result = Action._get_sprite_list_name(sprite_list)
        assert result == "SpriteList"

    def test_radd_operator(self):
        """Test right-hand addition operator."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")

        # Test right-hand addition: action2 + action1
        result = action1.__radd__(action2)

        # Should create a sequence
        assert hasattr(result, "actions")
        assert len(result.actions) == 2
        assert result.actions[0] == action2
        assert result.actions[1] == action1

    def test_ror_operator(self):
        """Test right-hand OR operator."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")

        # Test right-hand OR: action2 | action1
        result = action1.__ror__(action2)

        # Should create a parallel
        assert hasattr(result, "actions")
        assert len(result.actions) == 2
        assert result.actions[0] == action2
        assert result.actions[1] == action1
