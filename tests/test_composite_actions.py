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


class MockAction(IntervalAction):
    """Mock action for testing interval-based behaviors.

    This mock action allows precise control over duration, completion state,
    and update behavior for testing composite actions.
    """

    def __init__(self, duration=1.0):
        super().__init__(duration)
        self.start_called = False
        self.update_called = False
        self.stop_called = False
        self.reset_called = False
        self.done = False
        self._elapsed = 0.0

    def start(self):
        self.start_called = True
        self._elapsed = 0.0

    def update(self, delta_time):
        self.update_called = True
        self._elapsed += delta_time
        if self._elapsed >= self.duration:
            self.done = True

    def stop(self):
        self.stop_called = True

    def reset(self):
        self.reset_called = True
        self.done = False
        self._elapsed = 0.0

    def clone(self):
        """Create a copy of this MockAction."""
        cloned = MockAction(self.duration)
        return cloned


@pytest.fixture
def mock_action1():
    """Fixture providing a 1-second duration mock action."""
    return MockAction(1.0)


@pytest.fixture
def mock_action2():
    """Fixture providing a 2-second duration mock action."""
    return MockAction(2.0)


@pytest.fixture
def mock_sprite():
    """Fixture providing a mock Arcade sprite."""
    return arcade.Sprite()


class TestHelperFunctions:
    """Tests for composite action helper functions."""

    def test_sequence_helper(self, mock_action1, mock_action2):
        """Test sequence helper function creates proper sequence with independent actions."""
        seq = sequence(mock_action1, mock_action2)

        assert isinstance(seq, Sequence)
        assert len(seq.actions) == 2
        assert seq.actions[0] is not mock_action1
        assert seq.actions[1] is not mock_action2
        assert seq.duration == 3.0  # 1.0 + 2.0

    def test_spawn_helper(self, mock_action1, mock_action2):
        """Test spawn helper function creates proper parallel actions."""
        sp = spawn(mock_action1, mock_action2)

        assert isinstance(sp, Spawn)
        assert len(sp.actions) == 2
        assert sp.actions[0] is not mock_action1
        assert sp.actions[1] is not mock_action2
        assert sp.duration == 2.0  # max(1.0, 2.0)

    def test_loop_helper(self, mock_action1):
        """Test loop helper function creates proper repeating action."""
        lp = loop(mock_action1, 3)

        assert isinstance(lp, Loop)
        assert lp.times == 3
        assert lp.action is not mock_action1
        assert lp.duration == 3.0  # 1.0 * 3

    def test_repeat_helper(self, mock_action1):
        """Test repeat helper function creates proper repeating action."""
        rp = repeat(mock_action1, 3)

        assert isinstance(rp, Repeat)
        assert rp.times == 3
        assert rp.action is mock_action1  # Repeat uses reference, not deepcopy
        assert rp.duration == 3.0  # 1.0 * 3


class TestSequence:
    """Tests for Sequence composite action."""

    def test_execution(self, mock_action1, mock_action2, mock_sprite):
        """Test sequence executes actions in order with proper timing."""
        seq = sequence(mock_action1, mock_action2)
        seq.target = mock_sprite

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

    def test_completion_callback(self, mock_action1, mock_action2, mock_sprite):
        """Test sequence completion callback."""
        callback = Mock()
        seq = sequence(mock_action1, mock_action2)
        seq.on_complete(callback)
        seq.target = mock_sprite

        seq.start()
        seq.actions[0].done = True
        seq.update(0.1)
        seq.actions[1].done = True
        seq.update(0.1)

        callback.assert_called_once()


class TestSpawn:
    """Tests for Spawn composite action."""

    def test_execution(self, mock_action1, mock_action2, mock_sprite):
        """Test spawn executes actions in parallel with proper timing."""
        sp = spawn(mock_action1, mock_action2)
        sp.target = mock_sprite

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

    def test_completion_callback(self, mock_action1, mock_action2, mock_sprite):
        """Test spawn completion callback."""
        callback = Mock()
        sp = spawn(mock_action1, mock_action2)
        sp.on_complete(callback)
        sp.target = mock_sprite

        sp.start()
        sp.actions[0].done = True
        sp.actions[1].done = True
        sp.update(0.1)

        callback.assert_called_once()


class TestLoop:
    """Tests for Loop composite action."""

    def test_execution(self, mock_action1, mock_sprite):
        """Test loop repeats action specified number of times."""
        lp = loop(mock_action1, 3)
        lp.target = mock_sprite

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

    def test_completion_callback(self, mock_action1, mock_sprite):
        """Test loop completion callback."""
        callback = Mock()
        lp = loop(mock_action1, 2)
        lp.on_complete(callback)
        lp.target = mock_sprite

        lp.start()
        lp.action.done = True
        lp.update(0.1)
        lp.action.done = True
        lp.update(0.1)

        callback.assert_called_once()


class TestRepeat:
    """Tests for Repeat composite action."""

    def test_initialization(self, mock_action1):
        """Test proper initialization of Repeat action."""
        repeat_action = Repeat(mock_action1, 3)

        assert repeat_action.action is mock_action1
        assert repeat_action.times == 3
        assert repeat_action.current_times == 0
        assert repeat_action.duration == 3.0  # 1.0 * 3
        assert not repeat_action.done

    def test_execution(self, mock_action1, mock_sprite):
        """Test repeat executes action specified number of times."""
        repeat_action = Repeat(mock_action1, 3)
        repeat_action.target = mock_sprite

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

    def test_update_during_action(self, mock_action1, mock_sprite):
        """Test update behavior while action is running."""
        repeat_action = Repeat(mock_action1, 2)
        repeat_action.target = mock_sprite

        repeat_action.start()

        # Update while action is running
        repeat_action.update(0.5)
        assert repeat_action.action.update_called
        assert not repeat_action.done
        assert repeat_action.current_times == 0

    def test_stop(self, mock_action1, mock_sprite):
        """Test stop method properly stops the contained action."""
        repeat_action = Repeat(mock_action1, 3)
        repeat_action.target = mock_sprite

        repeat_action.start()
        repeat_action.stop()

        assert repeat_action.action.stop_called

    def test_reset(self, mock_action1, mock_sprite):
        """Test reset method properly resets state and contained action."""
        repeat_action = Repeat(mock_action1, 3)
        repeat_action.target = mock_sprite

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

    def test_single_iteration(self, mock_action1, mock_sprite):
        """Test repeat with times=1 completes after single execution."""
        repeat_action = Repeat(mock_action1, 1)
        repeat_action.target = mock_sprite

        repeat_action.start()
        repeat_action.action.done = True
        repeat_action.update(0.1)

        assert repeat_action.current_times == 1
        assert repeat_action.done

    def test_target_assignment(self, mock_action1, mock_sprite):
        """Test that target is properly assigned to contained action."""
        repeat_action = Repeat(mock_action1, 2)
        repeat_action.target = mock_sprite

        repeat_action.start()
        assert repeat_action.action.target is mock_sprite

    def test_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors."""
        mock_action = MockAction(1.0)

        # Test None action
        with pytest.raises(ValueError, match="Must specify action"):
            Repeat(None, 3)

        # Test None times
        with pytest.raises(ValueError, match="Must specify times"):
            Repeat(mock_action, None)

    def test_duration_calculation(self):
        """Test duration is calculated correctly."""
        action_2s = MockAction(2.0)
        repeat_action = Repeat(action_2s, 4)

        assert repeat_action.duration == 8.0  # 2.0 * 4

    def test_repr(self, mock_action1):
        """Test string representation."""
        repeat_action = Repeat(mock_action1, 3)
        repr_str = repr(repeat_action)

        assert "Repeat" in repr_str
        assert "times=3" in repr_str
        assert str(mock_action1) in repr_str

    def test_completion_callback(self, mock_action1, mock_sprite):
        """Test repeat completion callback (if supported)."""
        repeat_action = Repeat(mock_action1, 2)
        repeat_action.target = mock_sprite

        # Note: Repeat class doesn't have on_complete method like Loop,
        # so we just test that it completes properly
        repeat_action.start()
        repeat_action.action.done = True
        repeat_action.update(0.1)
        repeat_action.action.done = True
        repeat_action.update(0.1)

        assert repeat_action.done


class TestActionLifecycle:
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
    def test_lifecycle(self, action_class, create_action, mock_action1, mock_action2, mock_sprite):
        """Test proper lifecycle management (start/update/stop/reset) for all composites."""
        action = create_action(mock_action1, mock_action2)
        action.target = mock_sprite

        # Test start
        action.start()
        if isinstance(action, (Loop, Repeat)):
            assert action.action.start_called
        elif isinstance(action, Sequence):
            # Sequence only starts the first action
            assert action.actions[0].start_called
            assert not action.actions[1].start_called
        else:  # Spawn
            # Spawn starts all actions
            assert all(a.start_called for a in action.actions)

        # Test update
        action.update(0.1)
        if isinstance(action, (Loop, Repeat)):
            assert action.action.update_called
        elif isinstance(action, Sequence):
            # Sequence only updates the current action
            assert action.actions[0].update_called
            assert not action.actions[1].update_called
        else:  # Spawn
            # Spawn updates all actions
            assert all(a.update_called for a in action.actions)

        # Test stop
        action.stop()
        if isinstance(action, (Loop, Repeat)):
            assert action.action.stop_called
        elif isinstance(action, Sequence):
            # Sequence only stops the current action
            assert action.actions[0].stop_called
            assert not action.actions[1].stop_called
        else:  # Spawn
            # Spawn stops all actions
            assert all(a.stop_called for a in action.actions)

        # Test reset
        action.reset()
        if isinstance(action, (Loop, Repeat)):
            assert action.action.reset_called
            assert action.current_times == 0
        elif isinstance(action, Sequence):
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

    def test_operators(self, mock_action1, mock_action2):
        """Test operator overloading for composite actions."""
        # Test sequence operator
        seq = mock_action1 + mock_action2
        assert isinstance(seq, Sequence)

        # Test spawn operator
        sp = mock_action1 | mock_action2
        assert isinstance(sp, Spawn)

        # Test loop operator
        lp = mock_action1 * 3
        assert isinstance(lp, Loop)
        assert lp.times == 3


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_invalid_loop_times(self, mock_action1):
        """Test invalid loop times raise appropriate errors."""
        with pytest.raises(TypeError):
            Loop(mock_action1, "3")
        with pytest.raises(ValueError):
            Loop(mock_action1, 0)

    def test_empty_composites(self, mock_sprite):
        """Test behavior of empty composite actions."""
        # Test empty sequence
        seq = Sequence()
        seq.target = mock_sprite
        seq.start()
        seq.update(0.1)  # Need to call update to trigger completion logic
        assert seq.done  # Should complete immediately
        assert seq.current_action is None

        # Test empty spawn
        sp = Spawn()
        sp.target = mock_sprite
        sp.start()
        sp.update(0.1)  # Need to call update to trigger completion logic
        assert sp.done  # Should complete immediately

    def test_no_duration_action(self, mock_sprite):
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
        lp.target = mock_sprite
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
