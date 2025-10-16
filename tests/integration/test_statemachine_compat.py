"""Integration test for python-statemachine compatibility with ArcadeActions.

This test ensures python-statemachine and ArcadeActions can coexist without
conflicts when used together for game state management. It's automatically
skipped if python-statemachine is not installed.
"""

import arcade
import pytest

# Gate the entire module on statemachine availability
pytest.importorskip("statemachine")

from statemachine import State, StateMachine

from actions import Action, CallbackUntil


class GameFlowStateMachine(StateMachine):
    """Simple two-state machine for testing ArcadeActions compatibility."""

    idle = State(initial=True)
    active = State()

    # Transitions
    activate = idle.to(active)
    deactivate = active.to(idle)

    def __init__(self):
        super().__init__()
        self.sprite = None
        self.callback_count = 0
        # Manually set up initial state since on_enter_idle won't be called during init
        self._setup_idle_state()

    def _setup_idle_state(self):
        """Set up sprite and action for idle state."""
        self.sprite = arcade.Sprite(":resources:images/items/star.png")
        self.sprite.center_x = 100
        self.sprite.center_y = 100

        # Apply a simple callback action that counts invocations
        def increment_callback():
            self.callback_count += 1

        action = CallbackUntil(increment_callback, condition=lambda: False)
        action.apply(self.sprite, tag="idle_action")

    def on_enter_idle(self):
        """Called when transitioning to idle state."""
        self._setup_idle_state()

    def on_enter_active(self):
        """Set up sprite and action when entering active state."""
        self.sprite = arcade.Sprite(":resources:images/items/star.png")
        self.sprite.center_x = 200
        self.sprite.center_y = 200

        # Apply another simple callback action
        def increment_callback():
            self.callback_count += 1

        action = CallbackUntil(increment_callback, condition=lambda: False)
        action.apply(self.sprite, tag="active_action")


def test_statemachine_basic_compatibility():
    """Verify python-statemachine and ArcadeActions work together without conflicts."""
    # Clean slate
    Action.stop_all()

    # Create and initialize the state machine
    sm = GameFlowStateMachine()
    assert sm.current_state == sm.idle
    assert sm.sprite is not None
    assert sm.sprite.center_x == 100

    # Run a few update cycles - actions should execute without exceptions
    for _ in range(5):
        Action.update_all(1 / 60)

    # Verify callbacks were executed
    assert sm.callback_count > 0
    initial_callback_count = sm.callback_count

    # Transition to active state
    sm.activate()
    assert sm.current_state == sm.active
    assert sm.sprite.center_x == 200

    # Run more update cycles in the new state
    for _ in range(5):
        Action.update_all(1 / 60)

    # Verify callbacks continued to execute in new state
    assert sm.callback_count > initial_callback_count

    # Transition back to idle
    sm.deactivate()
    assert sm.current_state == sm.idle

    # Clean up
    Action.stop_all()


def test_statemachine_action_lifecycle():
    """Verify actions are properly managed across state transitions."""
    Action.stop_all()

    sm = GameFlowStateMachine()

    # Start in idle with one action
    Action.update_all(1 / 60)
    active_count_idle = Action.num_active_actions
    assert active_count_idle > 0

    # Transition to active - new action is created
    sm.activate()
    Action.update_all(1 / 60)
    active_count_active = Action.num_active_actions
    # Both old and new actions may coexist depending on lifecycle management
    assert active_count_active >= active_count_idle

    # Clean up
    Action.stop_all()
    # Actions are removed during update cycle, so call update_all once more
    Action.update_all(1 / 60)
    assert Action.num_active_actions == 0


def test_statemachine_no_interference():
    """Verify StateMachine state is independent of Action state."""
    Action.stop_all()

    sm = GameFlowStateMachine()

    # Modify action state
    Action.update_all(1 / 60)
    Action.stop_all()

    # State machine state should be unaffected
    assert sm.current_state == sm.idle

    # State machine should still transition normally
    sm.activate()
    assert sm.current_state == sm.active

    sm.deactivate()
    assert sm.current_state == sm.idle
