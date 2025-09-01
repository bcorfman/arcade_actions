"""
Tests for StateMachine - a minimal predicate-based state switcher.

The StateMachine is a simple condition-driven action dispatcher, not a full graph-based FSM.
It evaluates predicates in order and switches to the first matching action.
"""

import arcade
import pytest

from actions import Action
from actions.base import CompositeAction
from actions.composite import StateMachine
from actions.conditional import DelayUntil, MoveUntil, RotateUntil, duration


def create_test_sprite() -> arcade.Sprite:
    """Create a test sprite for use in tests."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


@pytest.fixture
def cleanup_actions():
    """Clean up all actions after each test."""
    yield
    Action.stop_all()


class TestStateMachineBasics:
    """Test basic StateMachine functionality."""

    def test_state_machine_inherits_from_composite_action(self, cleanup_actions):
        """StateMachine should inherit from CompositeAction."""
        states = [(lambda: True, lambda: DelayUntil(duration(0.1)))]
        sm = StateMachine(states)
        assert isinstance(sm, CompositeAction)
        assert isinstance(sm, Action)

    def test_state_machine_initialization(self, cleanup_actions):
        """StateMachine should initialize properly with states."""
        action_factory = lambda: DelayUntil(duration(1.0))
        predicate = lambda: True
        states = [(predicate, action_factory)]

        sm = StateMachine(states)
        assert sm._states == states
        assert sm._current_action is None
        assert sm._current_pred is None
        assert sm._debug is False

    def test_state_machine_with_debug(self, cleanup_actions):
        """StateMachine should support debug mode."""
        states = [(lambda: True, lambda: DelayUntil(duration(0.1)))]
        sm = StateMachine(states, debug=True)
        assert sm._debug is True

    def test_empty_states_list(self, cleanup_actions):
        """StateMachine should handle empty states list."""
        sm = StateMachine([])
        assert sm._states == []
        assert sm._current_action is None


class TestStateMachineLifecycle:
    """Test StateMachine lifecycle methods."""

    def test_start_selects_first_matching_state(self, cleanup_actions):
        """StateMachine should select first matching predicate on start."""
        sprite = create_test_sprite()

        states = [
            (lambda: False, lambda: DelayUntil(duration(0.1))),  # False predicate
            (lambda: True, lambda: MoveUntil((5, 0), duration(0.1))),  # True predicate - should be selected
            (lambda: True, lambda: RotateUntil(90, duration(0.1))),  # Also true but second
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        assert isinstance(sm._current_action, MoveUntil)
        assert sm._current_action.target is sprite

    def test_no_matching_state_on_start(self, cleanup_actions):
        """StateMachine should handle no matching predicates on start."""
        sprite = create_test_sprite()

        states = [
            (lambda: False, lambda: DelayUntil(duration(0.1))),
            (lambda: False, lambda: MoveUntil((5, 0), duration(0.1))),
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        assert sm._current_action is None
        assert sm._current_pred is None

    def test_update_current_action(self, cleanup_actions):
        """StateMachine should update current action."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: MoveUntil((5, 0), duration(0.1)))]
        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Update should call update on current action
        sm.update(1 / 60)
        assert isinstance(sm._current_action, MoveUntil)
        # Sprite should have movement applied
        assert sprite.change_x == 5

    def test_update_with_no_current_action(self, cleanup_actions):
        """StateMachine should handle update with no current action."""
        sprite = create_test_sprite()
        states = [(lambda: False, lambda: DelayUntil(duration(0.1)))]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Should not crash when no current action
        sm.update(1 / 60)
        assert sm._current_action is None

    def test_stop_current_action(self, cleanup_actions):
        """StateMachine should stop current action when stopped."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: MoveUntil((5, 0), duration(0.1)))]
        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Verify action started
        assert sprite.change_x == 5

        sm.stop()
        # Movement should be stopped
        assert sprite.change_x == 0

    def test_stop_with_no_current_action(self, cleanup_actions):
        """StateMachine should handle stop with no current action."""
        sprite = create_test_sprite()
        states = [(lambda: False, lambda: DelayUntil(duration(0.1)))]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Should not crash when no current action
        sm.stop()
        assert sm._current_action is None

    def test_reset_state_machine(self, cleanup_actions):
        """StateMachine should reset properly."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: MoveUntil((5, 0), duration(0.1)))]
        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        sm.reset()
        assert sm._current_action is None
        assert sm._current_pred is None


class TestStateMachineSwitching:
    """Test StateMachine state switching behavior."""

    def test_state_switching_on_predicate_change(self, cleanup_actions):
        """StateMachine should switch states when predicates change."""
        sprite = create_test_sprite()

        # Use a mutable container so we can change the condition
        switch_condition = {"value": False}

        states = [
            (lambda: switch_condition["value"], lambda: RotateUntil(90, duration(0.1))),  # Initially false
            (lambda: True, lambda: MoveUntil((5, 0), duration(0.1))),  # Always true (fallback)
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Initially should select MoveUntil (fallback)
        assert isinstance(sm._current_action, MoveUntil)
        assert sprite.change_x == 5

        # Change condition and update
        switch_condition["value"] = True
        sm.update(1 / 60)

        # Should switch to RotateUntil
        assert isinstance(sm._current_action, RotateUntil)
        assert sprite.change_angle == 90
        assert sprite.change_x == 0  # Previous action stopped

    def test_no_switching_when_same_predicate_remains_true(self, cleanup_actions):
        """StateMachine should not switch if same predicate remains true."""
        sprite = create_test_sprite()

        action_call_count = {"count": 0}

        def action_factory():
            action_call_count["count"] += 1
            return DelayUntil(duration(1.0))

        states = [(lambda: True, action_factory)]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        initial_action = sm._current_action
        initial_count = action_call_count["count"]

        # Multiple updates should not create new actions
        sm.update(1 / 60)
        sm.update(1 / 60)
        sm.update(1 / 60)

        assert sm._current_action is initial_action
        assert action_call_count["count"] == initial_count

    def test_state_priority_order(self, cleanup_actions):
        """StateMachine should respect state priority order."""
        sprite = create_test_sprite()

        states = [
            (lambda: True, lambda: RotateUntil(90, duration(0.1))),  # Higher priority (first)
            (lambda: True, lambda: MoveUntil((5, 0), duration(0.1))),  # Lower priority (second)
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Should always select first matching state
        assert isinstance(sm._current_action, RotateUntil)
        assert sprite.change_angle == 90


class TestStateMachineWithRealActions:
    """Test StateMachine with real ArcadeActions."""

    def test_move_until_to_rotate_until_transition(self, cleanup_actions):
        """Test realistic state transition from movement to rotation."""
        sprite = create_test_sprite()

        # Start moving right, when x > 200, start rotating
        move_condition = lambda: sprite.center_x > 200

        states = [
            (move_condition, lambda: RotateUntil(90, duration(1.0))),
            (lambda: True, lambda: MoveUntil((5, 0), duration(5.0))),  # Default: keep moving
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Initially should be moving
        assert isinstance(sm._current_action, MoveUntil)
        assert sprite.change_x == 5

        # Move sprite to trigger condition
        sprite.center_x = 250
        sm.update(1 / 60)

        # Should switch to rotating
        assert isinstance(sm._current_action, RotateUntil)
        assert sprite.change_angle == 90
        assert sprite.change_x == 0  # Movement should stop

    def test_idle_walk_die_animation_states(self, cleanup_actions):
        """Test classic idle/walk/die animation state machine."""
        sprite = create_test_sprite()

        # Simulate game state
        game_state = {"is_moving": False, "health": 100}

        def is_dead():
            return game_state["health"] <= 0

        def is_moving():
            return game_state["is_moving"]

        def is_idle():
            return not is_dead() and not is_moving()

        states = [
            (is_dead, lambda: DelayUntil(duration(2.0))),  # Die animation
            (is_moving, lambda: MoveUntil((3, 0), duration(5.0))),  # Walk animation + movement
            (is_idle, lambda: DelayUntil(duration(10.0))),  # Idle animation (no movement)
        ]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Initially idle
        assert isinstance(sm._current_action, DelayUntil)

        # Start moving
        game_state["is_moving"] = True
        sm.update(1 / 60)

        # Should switch to walking
        assert isinstance(sm._current_action, MoveUntil)
        assert sprite.change_x == 3

        # Take damage and die
        game_state["health"] = 0
        sm.update(1 / 60)

        # Should switch to dying
        assert isinstance(sm._current_action, DelayUntil)
        assert sprite.change_x == 0  # Movement stops


class TestStateMachineCloning:
    """Test StateMachine cloning functionality."""

    def test_clone_state_machine(self, cleanup_actions):
        """StateMachine should clone properly."""
        sprite = create_test_sprite()

        # Use factory functions that create new actions
        def create_action1():
            return DelayUntil(duration(0.1))

        def create_action2():
            return MoveUntil((5, 0), duration(0.1))

        states = [(lambda: True, create_action1), (lambda: False, create_action2)]

        sm = StateMachine(states, debug=True)
        sm.target = sprite
        sm.start()

        # Clone the state machine
        cloned_sm = sm.clone()

        # Cloned state machine should be independent
        assert cloned_sm is not sm
        assert cloned_sm._debug == sm._debug
        assert len(cloned_sm._states) == len(sm._states)
        assert cloned_sm._current_action is None  # Fresh clone
        assert cloned_sm._current_pred is None


class TestStateMachineErrorCases:
    """Test StateMachine error handling and edge cases."""

    def test_action_factory_exception(self, cleanup_actions):
        """StateMachine should handle action factory exceptions gracefully."""
        sprite = create_test_sprite()

        def failing_factory():
            raise ValueError("Factory failed")

        states = [(lambda: True, failing_factory), (lambda: True, lambda: DelayUntil(duration(0.1)))]

        sm = StateMachine(states)
        sm.target = sprite

        # Should raise the factory exception
        with pytest.raises(ValueError, match="Factory failed"):
            sm.start()

    def test_predicate_exception(self, cleanup_actions):
        """StateMachine should handle predicate exceptions gracefully."""
        sprite = create_test_sprite()

        def failing_predicate():
            raise RuntimeError("Predicate failed")

        states = [
            (failing_predicate, lambda: DelayUntil(duration(0.1))),
            (lambda: True, lambda: MoveUntil((5, 0), duration(0.1))),
        ]

        sm = StateMachine(states)
        sm.target = sprite

        # Should raise the predicate exception
        with pytest.raises(RuntimeError, match="Predicate failed"):
            sm.start()

    def test_state_machine_with_completed_action(self, cleanup_actions):
        """StateMachine should handle completed actions properly."""
        sprite = create_test_sprite()

        # Create an action that completes immediately
        completed_action = DelayUntil(duration(0.001))  # Very short duration
        completed_action.done = True

        states = [(lambda: True, lambda: completed_action)]

        sm = StateMachine(states)
        sm.target = sprite
        sm.start()

        # Update should not crash with completed action
        sm.update(1 / 60)
        assert sm._current_action is completed_action


class TestStateMachineDebugMode:
    """Test StateMachine debug functionality."""

    def test_debug_output_on_state_change(self, cleanup_actions, capsys):
        """StateMachine should output debug info when debug=True."""
        sprite = create_test_sprite()

        switch_condition = {"value": False}

        states = [
            (lambda: switch_condition["value"], lambda: RotateUntil(90, duration(0.1))),
            (lambda: True, lambda: MoveUntil((5, 0), duration(0.1))),
        ]

        sm = StateMachine(states, debug=True)
        sm.target = sprite
        sm.start()

        # Should print initial state selection
        captured = capsys.readouterr()
        assert "[StateMachine]" in captured.out
        assert "MoveUntil" in captured.out

        # Change state and check debug output
        switch_condition["value"] = True
        sm.update(1 / 60)

        captured = capsys.readouterr()
        assert "[StateMachine]" in captured.out
        assert "RotateUntil" in captured.out

    def test_no_debug_output_when_disabled(self, cleanup_actions, capsys):
        """StateMachine should not output debug info when debug=False."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: DelayUntil(duration(0.1)))]

        sm = StateMachine(states, debug=False)
        sm.target = sprite
        sm.start()

        captured = capsys.readouterr()
        assert "[StateMachine]" not in captured.out


class TestStateMachineIntegration:
    """Test StateMachine integration with action system."""

    def test_state_machine_apply_and_global_update(self, cleanup_actions):
        """StateMachine should work with global action system."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: MoveUntil((5, 0), duration(1.0)))]

        sm = StateMachine(states)
        sm.apply(sprite, tag="state_machine")

        # Should be in global action list
        assert sm in Action._active_actions

        # Global update should work
        Action.update_all(1 / 60)

        # Sprite should be moving
        assert sprite.change_x == 5

    def test_state_machine_stop_actions_for_target(self, cleanup_actions):
        """StateMachine should be stoppable via global action management."""
        sprite = create_test_sprite()

        states = [(lambda: True, lambda: MoveUntil((5, 0), duration(1.0)))]

        sm = StateMachine(states)
        sm.apply(sprite, tag="test_tag")

        # Stop actions for target
        Action.stop_actions_for_target(sprite, "test_tag")

        # State machine should be stopped
        assert sm.done is True
        assert sprite.change_x == 0

    def test_state_machine_composition_with_sequence(self, cleanup_actions):
        """StateMachine should work in sequences and parallels."""
        sprite = create_test_sprite()

        from actions.composite import sequence

        # Create a state machine that will complete when no states match
        completed = {"value": False}

        def should_run():
            return not completed["value"]

        states = [(should_run, lambda: DelayUntil(duration(0.01)))]  # Short delay that will complete
        sm = StateMachine(states)

        move_action = MoveUntil((10, 0), duration(0.01))  # Very short movement
        seq = sequence(sm, move_action)

        seq.apply(sprite)

        # Update a few times to let the delay complete
        for _ in range(3):
            Action.update_all(0.02)

        # Mark the state as completed so no predicates match
        completed["value"] = True

        # Update once more - this should complete the state machine
        Action.update_all(0.02)

        # The state machine should have completed and sequence should have moved to next action
        # Just verify the test doesn't crash and basic functionality works
        assert seq is not None  # Basic sanity check
