"""
Tests for Action class instrumentation integration.

Tests that actions properly record events and evaluations to an injected
debug store following dependency injection patterns.
"""

import arcade

from actions.base import Action
from actions.visualizer.instrumentation import DebugDataStore


class MockAction(Action):
    """Mock action for testing instrumentation."""

    def __init__(self, condition, *, tag: str | None = None):
        super().__init__(condition=condition, tag=tag)
        self.apply_effect_called = False
        self.update_effect_called = False

    def apply_effect(self):
        self.apply_effect_called = True

    def update_effect(self, delta_time):
        self.update_effect_called = True

    def clone(self):
        """Create a copy of this action."""
        return MockAction(condition=self.condition, tag=self.tag)


class TestActionInstrumentation:
    """Test Action class integration with debug store."""

    def setup_method(self):
        """Clean up action state before each test."""
        Action._active_actions.clear()
        Action._pending_actions.clear()
        Action._enable_visualizer = False
        Action._frame_counter = 0

    def teardown_method(self):
        """Clean up after each test."""
        Action._active_actions.clear()
        Action._pending_actions.clear()
        Action._enable_visualizer = False
        Action._frame_counter = 0

    def test_action_without_instrumentation(self):
        """Test that actions work normally without instrumentation enabled."""
        sprite = arcade.Sprite()
        store = DebugDataStore()

        # Create action with instrumentation disabled
        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        # No events should be recorded
        assert len(store.events) == 0
        assert len(store.active_snapshots) == 0

    def test_action_records_created_event(self):
        """Test that action records creation event when instrumentation enabled."""
        sprite = arcade.Sprite()
        store = DebugDataStore()
        Action._enable_visualizer = True

        # Inject the debug store via dependency injection
        Action.set_debug_store(store)

        action = MockAction(condition=lambda: False)
        action.apply(sprite, tag="test")

        # Should record created and started events
        assert len(store.events) >= 1
        created_event = [e for e in store.events if e.event_type == "created"][0]
        assert created_event.action_type == "MockAction"
        assert created_event.tag == "test"

    def test_action_records_started_event(self):
        """Test that action records started event."""
        sprite = arcade.Sprite()
        store = DebugDataStore()
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        # Should have created and started events
        assert len(store.events) == 2
        assert store.events[0].event_type == "created"
        assert store.events[1].event_type == "started"

    def test_action_creates_snapshot(self):
        """Test that action creates snapshot on start."""
        sprite = arcade.Sprite()
        store = DebugDataStore()
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        # Should create snapshot
        assert len(store.active_snapshots) == 1
        snapshot = list(store.active_snapshots.values())[0]
        assert snapshot.action_type == "MockAction"
        assert snapshot.is_active is True

    def test_action_records_condition_evaluation(self):
        """Test that action records condition evaluations."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        store = DebugDataStore()
        store.update_frame(1, 0.016)
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        # Create action with condition that will evaluate False
        action = MockAction(condition=lambda: sprite.center_x > 200)
        action.apply(sprite)

        # Update action - should evaluate condition
        action.update(0.016)

        # Should record evaluation
        assert len(store.evaluations) >= 1
        eval_result = store.evaluations[-1]
        assert eval_result.result is False

    def test_action_records_stopped_event(self):
        """Test that action records stopped event when condition met."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        store = DebugDataStore()
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        # Condition that will become True
        condition_met = [False]

        def condition():
            return condition_met[0]

        action = MockAction(condition=condition)
        action.apply(sprite)

        # Trigger condition
        condition_met[0] = True
        action.update(0.016)

        # Should record stopped event
        events = [e for e in store.events if e.event_type == "stopped"]
        assert len(events) == 1

    def test_action_records_removed_event(self):
        """Test that action records removed event on stop."""
        sprite = arcade.Sprite()
        store = DebugDataStore()
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        action = MockAction(condition=lambda: False)
        action.apply(sprite)

        # Stop action
        action.stop()

        # Should record removed event
        events = [e for e in store.events if e.event_type == "removed"]
        assert len(events) == 1

        # Should remove snapshot
        assert len(store.active_snapshots) == 0

    def test_update_all_updates_frame_counter(self):
        """Test that Action.update_all increments frame counter."""
        store = DebugDataStore()
        Action._enable_visualizer = True
        Action.set_debug_store(store)

        initial_frame = Action._frame_counter

        Action.update_all(0.016)

        assert Action._frame_counter == initial_frame + 1
        assert store.current_frame == Action._frame_counter

    def test_instrumentation_can_be_disabled(self):
        """Test that instrumentation can be toggled off."""
        sprite = arcade.Sprite()
        store = DebugDataStore()

        # Enable, create action
        Action._enable_visualizer = True
        Action.set_debug_store(store)
        action1 = MockAction(condition=lambda: False)
        action1.apply(sprite)

        event_count_1 = len(store.events)
        assert event_count_1 > 0

        # Disable instrumentation
        Action._enable_visualizer = False
        action2 = MockAction(condition=lambda: False)
        action2.apply(sprite)

        # Should not add more events
        assert len(store.events) == event_count_1

    def test_apply_preserves_init_tag_without_override(self):
        """Applying without a tag should keep the tag provided at initialization."""
        sprite = arcade.Sprite()
        action = MockAction(condition=lambda: False, tag="init_tag")

        action.apply(sprite)

        assert action.tag == "init_tag"

    def test_apply_overrides_tag_when_provided(self):
        """Supplying a tag during apply should override the initialization tag."""
        sprite = arcade.Sprite()
        action = MockAction(condition=lambda: False, tag="init_tag")

        action.apply(sprite, tag="override")

        assert action.tag == "override"
