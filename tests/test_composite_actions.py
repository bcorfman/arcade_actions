"""Unit tests for composite actions.

These tests verify the behavior of composite actions (Sequence, Spawn, Loop) that
combine multiple actions into complex behaviors. The tests ensure frame-independent
accuracy through delta-time updates and proper integration with Arcade's sprite system.
"""

from unittest.mock import Mock

import arcade
import pytest

from actions.base import Action, IntervalAction
from actions.composite import Loop, Repeat, Sequence, Spawn, loop, repeat, sequence, spawn


class ObservableAction(IntervalAction):
    """Test action with observability for testing composite action behaviors.

    This action extends the base IntervalAction with flags to observe
    which lifecycle methods have been called, allowing precise testing
    of composite action control flow.
    """

    def __init__(self, duration=1.0):
        super().__init__(duration)
        self.start_called = False
        self.update_called = False
        self.stop_called = False
        self.reset_called = False

    def start(self):
        super().start()
        self.start_called = True

    def update(self, delta_time):
        super().update(delta_time)
        self.update_called = True

    def stop(self):
        super().stop()
        self.stop_called = True

    def reset(self):
        super().reset()
        self.reset_called = True

    def clone(self):
        """Create a copy of this ObservableAction."""
        return ObservableAction(self.duration)


@pytest.fixture
def test_action1():
    """Fixture providing a 1-second duration test action."""
    return ObservableAction(1.0)


@pytest.fixture
def test_action2():
    """Fixture providing a 2-second duration test action."""
    return ObservableAction(2.0)


@pytest.fixture
def test_sprite():
    """Fixture providing a test Arcade sprite."""
    return arcade.Sprite()


class TestHelperFunctions:
    """Tests for composite action helper functions."""

    def test_sequence_helper(self, test_action1, test_action2):
        """Test sequence helper function."""
        seq = sequence(test_action1, test_action2)
        # Verify it's a sequence by checking its behavior
        assert len(seq.actions) == 2
        # Check durations match since actions may be cloned
        assert seq.actions[0].duration == test_action1.duration
        assert seq.actions[1].duration == test_action2.duration
        # Sequences have current_index attribute
        assert seq.current_index == 0

    def test_spawn_helper(self, test_action1, test_action2):
        """Test spawn helper function."""
        sp = spawn(test_action1, test_action2)
        # Verify it's a spawn by checking its behavior
        assert len(sp.actions) == 2
        # Check durations match since actions may be cloned
        assert sp.actions[0].duration == test_action1.duration
        assert sp.actions[1].duration == test_action2.duration

    def test_loop_helper(self, test_action1):
        """Test loop helper function."""
        lp = loop(test_action1, 3)
        # Verify it's a loop by checking its behavior
        # Check duration matches since action may be cloned
        assert lp.action.duration == test_action1.duration
        assert lp.times == 3
        # Loops have current_times attribute
        assert lp.current_times == 0

    def test_repeat_helper(self, test_action1):
        """Test repeat helper function."""
        rp = repeat(test_action1, 2)
        # Verify it's a repeat by checking its behavior
        assert rp.action is test_action1
        assert rp.times == 2
        # Repeats have current_times attribute
        assert rp.current_times == 0


class TestSequence:
    """Tests for Sequence composite action."""

    def test_execution(self, test_action1, test_action2, test_sprite):
        """Test sequence executes actions in order with proper timing."""
        seq = sequence(test_action1, test_action2)
        seq.target = test_sprite

        # Start sequence
        seq.start()
        assert seq.actions[0].start_called
        assert not seq.actions[1].start_called

        # First action completes
        seq.actions[0].done = True
        seq.update(0.1)
        assert seq.actions[1].start_called
        assert not seq.done

        # Second action completes
        seq.actions[1].done = True
        seq.update(0.1)
        assert seq.done

    def test_completion_callback(self, test_action1, test_action2, test_sprite):
        """Test sequence completion callback."""
        callback = Mock()
        seq = sequence(test_action1, test_action2)
        seq.on_complete(callback)
        seq.target = test_sprite

        seq.start()
        seq.actions[0].done = True
        seq.update(0.1)
        seq.actions[1].done = True
        seq.update(0.1)

        callback.assert_called_once()


class TestSpawn:
    """Tests for Spawn composite action."""

    def test_execution(self, test_action1, test_action2, test_sprite):
        """Test spawn executes actions in parallel with proper timing."""
        sp = spawn(test_action1, test_action2)
        sp.target = test_sprite

        # Start spawn
        sp.start()
        assert sp.actions[0].start_called
        assert sp.actions[1].start_called

        # Update both actions
        sp.update(0.5)
        assert sp.actions[0].update_called
        assert sp.actions[1].update_called
        assert not sp.done

        # Complete first action
        sp.actions[0].done = True
        sp.update(0.5)
        assert not sp.done

        # Complete second action
        sp.actions[1].done = True
        sp.update(0.5)
        assert sp.done

    def test_completion_callback(self, test_action1, test_action2, test_sprite):
        """Test spawn completion callback."""
        callback = Mock()
        sp = spawn(test_action1, test_action2)
        sp.on_complete(callback)
        sp.target = test_sprite

        sp.start()
        sp.actions[0].done = True
        sp.actions[1].done = True
        sp.update(0.1)

        callback.assert_called_once()


class TestLoop:
    """Tests for Loop composite action."""

    def test_execution(self, test_action1, test_sprite):
        """Test loop repeats action specified number of times."""
        lp = loop(test_action1, 3)
        lp.target = test_sprite

        # Start loop
        lp.start()
        assert lp.action.start_called

        # Complete first iteration
        lp.action.done = True
        lp.update(0.1)
        assert lp.current_times == 1
        assert not lp.done
        assert lp.action.reset_called

        # Complete second iteration
        lp.action.done = True
        lp.update(0.1)
        assert lp.current_times == 2
        assert not lp.done

        # Complete final iteration
        lp.action.done = True
        lp.update(0.1)
        assert lp.current_times == 3
        assert lp.done

    def test_completion_callback(self, test_action1, test_sprite):
        """Test loop completion callback."""
        callback = Mock()
        lp = loop(test_action1, 2)
        lp.on_complete(callback)
        lp.target = test_sprite

        lp.start()
        lp.action.done = True
        lp.update(0.1)
        lp.action.done = True
        lp.update(0.1)

        callback.assert_called_once()


class TestRepeat:
    """Tests for Repeat composite action."""

    def test_initialization(self, test_action1):
        """Test proper initialization of Repeat action."""
        repeat_action = Repeat(test_action1, 3)

        assert repeat_action.action is test_action1
        assert repeat_action.times == 3
        assert repeat_action.current_times == 0
        assert repeat_action.duration == 3.0  # 1.0 * 3
        assert not repeat_action.done

    def test_execution(self, test_action1, test_sprite):
        """Test repeat executes action specified number of times."""
        repeat_action = Repeat(test_action1, 3)
        repeat_action.target = test_sprite

        # Start repeat
        repeat_action.start()
        assert repeat_action.action.start_called

        # Complete first iteration
        repeat_action.action.done = True
        repeat_action.update(0.1)
        assert repeat_action.current_times == 1
        assert not repeat_action.done
        assert repeat_action.action.reset_called

        # Complete second iteration
        repeat_action.action.done = True
        repeat_action.update(0.1)
        assert repeat_action.current_times == 2
        assert not repeat_action.done

        # Complete final iteration
        repeat_action.action.done = True
        repeat_action.update(0.1)
        assert repeat_action.current_times == 3
        assert repeat_action.done

    def test_update_during_action(self, test_action1, test_sprite):
        """Test update behavior while action is running."""
        repeat_action = Repeat(test_action1, 2)
        repeat_action.target = test_sprite

        repeat_action.start()

        # Update while action is running
        repeat_action.update(0.5)
        assert repeat_action.action.update_called
        assert not repeat_action.done
        assert repeat_action.current_times == 0

    def test_stop(self, test_action1, test_sprite):
        """Test stop method properly stops the contained action."""
        repeat_action = Repeat(test_action1, 3)
        repeat_action.target = test_sprite

        repeat_action.start()
        repeat_action.stop()

        assert repeat_action.action.stop_called

    def test_reset(self, test_action1, test_sprite):
        """Test reset method properly resets state and contained action."""
        repeat_action = Repeat(test_action1, 3)
        repeat_action.target = test_sprite

        # Progress through some iterations
        repeat_action.start()
        repeat_action.action.done = True
        repeat_action.update(0.1)
        assert repeat_action.current_times == 1

        # Reset and verify state
        repeat_action.reset()
        assert repeat_action.current_times == 0
        assert repeat_action.action.reset_called
        assert not repeat_action.done

    def test_single_iteration(self, test_action1, test_sprite):
        """Test repeat with times=1 completes after single execution."""
        repeat_action = Repeat(test_action1, 1)
        repeat_action.target = test_sprite

        repeat_action.start()
        repeat_action.action.done = True
        repeat_action.update(0.1)

        assert repeat_action.current_times == 1
        assert repeat_action.done

    def test_target_assignment(self, test_action1, test_sprite):
        """Test that target is properly assigned to contained action."""
        repeat_action = Repeat(test_action1, 2)
        repeat_action.target = test_sprite

        repeat_action.start()
        assert repeat_action.action.target is test_sprite

    def test_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors."""
        test_action = ObservableAction(1.0)

        # Test None action
        with pytest.raises(ValueError, match="Must specify action"):
            Repeat(None, 3)

        # Test None times
        with pytest.raises(ValueError, match="Must specify times"):
            Repeat(test_action, None)

    def test_duration_calculation(self):
        """Test duration is calculated correctly."""
        action_2s = ObservableAction(2.0)
        repeat_action = Repeat(action_2s, 4)

        assert repeat_action.duration == 8.0  # 2.0 * 4

    def test_repr(self, test_action1):
        """Test string representation."""
        repeat_action = Repeat(test_action1, 3)
        repr_str = repr(repeat_action)

        assert "Repeat" in repr_str
        assert "times=3" in repr_str
        assert str(test_action1) in repr_str

    def test_completion_callback(self, test_action1, test_sprite):
        """Test repeat completion callback (if supported)."""
        repeat_action = Repeat(test_action1, 2)
        repeat_action.target = test_sprite

        # Note: Repeat class doesn't have on_complete method like Loop,
        # so we just test that it completes properly
        repeat_action.start()
        repeat_action.action.done = True
        repeat_action.update(0.1)
        repeat_action.action.done = True
        repeat_action.update(0.1)

        assert repeat_action.done


class ObservableActionLifecycle:
    """Tests for action lifecycle management across all composite types."""

    @pytest.mark.parametrize(
        "action_class,create_action",
        [
            (Sequence, lambda a1, a2: sequence(a1, a2)),
            (Spawn, lambda a1, a2: spawn(a1, a2)),
            (Loop, lambda a1, _: loop(a1, 2)),
            (Repeat, lambda a1, _: repeat(a1, 2)),
        ],
    )
    def test_lifecycle(self, action_class, create_action, test_action1, test_action2, test_sprite):
        """Test proper lifecycle management (start/update/stop/reset) for all composites."""
        action = create_action(test_action1, test_action2)
        action.target = test_sprite

        # Test start
        action.start()
        # Use duck typing to determine action type behavior
        try:
            single_action = action.action  # Loop or Repeat - single action wrapper
            assert single_action.start_called
            is_single_wrapper = True
            is_sequence = False
        except AttributeError:
            is_single_wrapper = False

            # Try to distinguish between Sequence and Spawn
            # Sequence manages a current_action field that gets set to the active action
            # Spawn doesn't manage current_action in the same way
            try:
                current_action = action.current_action  # Both have this, but only Sequence uses it meaningfully
                # Check if current_action is set to the first action (Sequence behavior)
                if current_action is not None and len(action.actions) > 1 and current_action is action.actions[0]:
                    is_sequence = True
                    # Sequence only starts the first action
                    assert action.actions[0].start_called
                    assert not action.actions[1].start_called
                else:
                    # This is likely Spawn - doesn't use current_action meaningfully
                    is_sequence = False
                    # For Spawn, all actions should be started
                    assert all(a.start_called for a in action.actions)
            except AttributeError:
                # Fallback: neither Sequence nor Spawn pattern
                is_sequence = False
                # For Spawn, all actions should be started
                assert all(a.start_called for a in action.actions)

        # Test update
        action.update(0.1)
        if is_single_wrapper:
            assert action.action.update_called
        elif is_sequence:
            # Sequence only updates the current action
            assert action.actions[0].update_called
            assert not action.actions[1].update_called
        else:  # Spawn
            # Spawn updates all actions
            assert all(a.update_called for a in action.actions)

        # Test stop
        action.stop()
        if is_single_wrapper:
            assert action.action.stop_called
        elif is_sequence:
            # Sequence only stops the current action
            assert action.actions[0].stop_called
            assert not action.actions[1].stop_called
        else:  # Spawn
            # Spawn stops all actions
            assert all(a.stop_called for a in action.actions)

        # Test reset
        action.reset()
        if is_single_wrapper:
            assert action.action.reset_called
            assert action.current_times == 0
        elif is_sequence:
            # Sequence resets all actions and resets its state
            assert all(a.reset_called for a in action.actions)
            assert action.current_index == 0
            assert action.current_action is None
        else:  # Spawn
            # Spawn resets all actions
            assert all(a.reset_called for a in action.actions)
        assert not action.done


class TestOperatorOverloading:
    """Tests for operator overloading in composite actions."""

    def test_operators(self, test_action1, test_action2):
        """Test operator overloading for composite actions."""
        # Test sequence operator
        seq = test_action1 + test_action2
        # Verify it's a sequence by checking behavior, not type
        assert len(seq.actions) == 2
        # Check durations match since actions may be cloned
        assert seq.actions[0].duration == test_action1.duration
        assert seq.actions[1].duration == test_action2.duration

        # Test spawn operator
        sp = test_action1 | test_action2
        # Verify it's a spawn by checking behavior, not type
        assert len(sp.actions) == 2
        # Check durations match since actions may be cloned
        assert sp.actions[0].duration == test_action1.duration
        assert sp.actions[1].duration == test_action2.duration

        # Test loop operator
        lp = test_action1 * 3
        # Verify it's a loop by checking behavior, not type
        assert lp.times == 3
        # Check duration matches since action may be cloned
        assert lp.action.duration == test_action1.duration


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_invalid_loop_times(self, test_action1):
        """Test invalid loop times raise appropriate errors."""
        with pytest.raises(TypeError):
            Loop(test_action1, "3")
        with pytest.raises(ValueError):
            Loop(test_action1, 0)

    def test_empty_composites(self, test_sprite):
        """Test behavior of empty composite actions."""
        # Test empty sequence
        seq = Sequence()
        seq.target = test_sprite
        seq.start()
        seq.update(0.1)  # Need to call update to trigger completion logic
        assert seq.done  # Should complete immediately
        assert seq.current_action is None

        # Test empty spawn
        sp = Spawn()
        sp.target = test_sprite
        sp.start()
        sp.update(0.1)  # Need to call update to trigger completion logic
        assert sp.done  # Should complete immediately

    def test_no_duration_action(self, test_sprite):
        """Test loop with an action that has no duration."""

        class NoDurationAction(Action):
            def start(self):
                pass

            def update(self, dt):
                self.done = True

            def clone(self):
                return NoDurationAction()

        action = NoDurationAction()
        lp = Loop(action, 3)
        assert lp.duration is None

        # Verify execution still works
        lp.target = test_sprite
        lp.start()
        lp.update(0.1)
        assert lp.current_times == 1
        assert not lp.done

        # Complete all iterations
        for _ in range(2):
            action.done = True
            lp.update(0.1)

        assert lp.done
        assert lp.current_times == 3

    def test_base_action_for_simple_testing(self, test_sprite):
        """Test that base Action can be used directly for simple testing scenarios.

        This demonstrates the benefit of making Action concrete - we can now
        create no-op actions directly without needing test doubles for simple cases.
        """
        from actions.base import Action, IntervalAction

        # Test that Action can be instantiated directly (was impossible with ABC)
        action = Action()
        assert action is not None
        assert action.duration == 0.0

        # Test basic action lifecycle
        action.target = test_sprite
        action.start()  # Should not raise error
        action.update(0.1)  # Should not raise error
        action.stop()  # Should not raise error
        action.reset()  # Should not raise error

        # Test cloning works
        cloned_action = action.clone()
        assert cloned_action.duration == action.duration
        assert cloned_action is not action

        # Test manual completion for testing scenarios
        action.done = True
        assert action.done

        # Test with IntervalAction for timed behaviors
        timed_action = IntervalAction(1.0)
        timed_action.target = test_sprite
        timed_action.start()
        assert not timed_action.done

        # Simulate time passage
        timed_action._elapsed = 1.0
        timed_action.update(0.1)
        assert timed_action.done  # Should auto-complete based on duration
