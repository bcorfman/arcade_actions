"""Test suite for composite.py - Composite actions."""

import arcade

from actions.base import Action
from actions.composite import parallel, repeat, sequence


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestSequenceFunction:
    """Test suite for sequence() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_empty_initialization(self):
        """Test empty sequence initialization."""
        seq = sequence()
        assert len(seq.actions) == 0
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_with_actions_initialization(self):
        """Test sequence initialization with actions."""
        from actions.conditional import DelayUntil, duration

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        assert len(seq.actions) == 2
        assert seq.actions[0] == action1
        assert seq.actions[1] == action2
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_empty_completes_immediately(self):
        """Test that empty sequence completes immediately."""
        sprite = create_test_sprite()
        seq = sequence()
        seq.target = sprite
        seq.start()

        assert seq.done

    def test_sequence_starts_first_action(self):
        """Test that sequence starts the first action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        assert seq.current_action == action1
        assert seq.current_index == 0

    def test_sequence_advances_to_next_action(self):
        """Test that sequence advances to next action when current completes."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until first action completes
        seq.update(0.06)

        assert action1.done
        assert seq.current_action == action2
        assert seq.current_index == 1

    def test_sequence_completes_when_all_actions_done(self):
        """Test that sequence completes when all actions are done."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until both actions complete
        seq.update(0.06)  # Complete first action
        seq.update(0.06)  # Complete second action

        assert action1.done
        assert action2.done
        assert seq.done
        assert seq.current_action is None

    def test_sequence_stop_stops_current_action(self):
        """Test that stopping sequence stops the current action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(1.0))  # Long duration so it won't complete
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()
        seq.stop()

        assert action1.done  # Should be marked done by stop()

    def test_sequence_clone(self):
        """Test sequence cloning."""
        from actions.conditional import DelayUntil, duration

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        cloned = seq.clone()

        assert cloned is not seq
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2


class TestParallelFunction:
    """Test suite for parallel() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_empty_initialization(self):
        """Test empty parallel initialization."""
        par = parallel()
        assert len(par.actions) == 0

    def test_parallel_with_actions_initialization(self):
        """Test parallel initialization with actions."""
        from actions.conditional import DelayUntil, duration

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        assert len(par.actions) == 2
        assert par.actions[0] == action1
        assert par.actions[1] == action2

    def test_parallel_empty_completes_immediately(self):
        """Test that empty parallel completes immediately."""
        sprite = create_test_sprite()
        par = parallel()
        par.target = sprite
        par.start()

        assert par.done

    def test_parallel_starts_all_actions(self):
        """Test that parallel starts all actions simultaneously."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        par.target = sprite
        par.start()

        # Both actions should be started (can't check internal state easily, but they should be running)
        assert not par.done  # Parallel shouldn't be done immediately

    def test_parallel_completes_when_all_actions_done(self):
        """Test that parallel completes when all actions are done."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.1))  # Longer duration
        par = parallel(action1, action2)

        par.target = sprite
        par.start()

        # Update until first action completes
        par.update(0.06)
        assert action1.done
        assert not par.done  # Parallel not done until all actions done

        # Update until second action completes
        par.update(0.05)
        assert action2.done
        assert par.done

    def test_parallel_stops_all_actions(self):
        """Test that stopping parallel stops all actions."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(1.0))  # Long duration
        action2 = DelayUntil(duration(1.0))  # Long duration
        par = parallel(action1, action2)

        par.target = sprite
        par.start()
        par.stop()

        assert action1.done  # Should be marked done by stop()
        assert action2.done  # Should be marked done by stop()

    def test_parallel_clone(self):
        """Test parallel cloning."""
        from actions.conditional import DelayUntil, duration

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        cloned = par.clone()

        assert cloned is not par
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2


class TestOperatorOverloading:
    """Test suite for operator-based composition (+ for sequence, | for parallel)."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_plus_operator_creates_sequence(self):
        """Test that the '+' operator creates a sequential action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))

        # Use + operator to create sequence
        sequence_action = action1 + action2
        sequence_action.apply(sprite)

        # Should behave like a sequence - first action runs, then second
        Action.update_all(0.06)  # Complete first action
        assert action1.done

        Action.update_all(0.06)  # Complete second action
        assert action2.done

    def test_pipe_operator_creates_parallel(self):
        """Test that the '|' operator creates a parallel action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.1))  # Different duration

        # Use | operator to create parallel
        parallel_action = action1 | action2
        parallel_action.apply(sprite)

        # Should behave like a parallel - both run simultaneously
        Action.update_all(0.06)  # Complete first action
        assert action1.done
        assert not action2.done  # Second still running

        Action.update_all(0.05)  # Complete second action
        assert action2.done

    def test_mixed_operator_composition(self):
        """Test mixing + and | operators for complex compositions."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))

        # Create a sequence where the second step is parallel actions
        complex_action = action1 + (action2 | action3)
        complex_action.apply(sprite)

        # First action should complete first
        Action.update_all(0.06)
        assert action1.done

        # After first action completes, parallel actions should run and complete
        Action.update_all(0.06)
        assert action2.done
        assert action3.done

    def test_operator_precedence_with_parentheses(self):
        """Test operator precedence with explicit parentheses."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))

        # Test a + (b | c) - explicit parentheses
        composed = action1 + (action2 | action3)
        composed.apply(sprite)

        # First action completes
        Action.update_all(0.06)
        assert action1.done

        # Then parallel actions complete
        Action.update_all(0.06)
        assert action2.done
        assert action3.done


class TestNestedComposites:
    """Test suite for nested composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_of_parallels_with_operators(self):
        """Test sequence containing parallel actions using operators."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))
        action4 = DelayUntil(duration(0.05))

        # Create sequence of parallels using operators
        composed = (action1 | action2) + (action3 | action4)
        composed.apply(sprite)

        # Update until first parallel completes
        Action.update_all(0.06)
        assert action1.done
        assert action2.done

        # Update until second parallel completes
        Action.update_all(0.06)
        assert action3.done
        assert action4.done

    def test_parallel_of_sequences_with_operators(self):
        """Test parallel containing sequence actions using operators."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))
        action4 = DelayUntil(duration(0.05))

        # Create parallel of sequences using operators
        composed = (action1 + action2) | (action3 + action4)
        composed.apply(sprite)

        # Both sequences run in parallel, each taking 2 updates (0.05 + 0.05)
        Action.update_all(0.06)  # Complete first actions in each sequence
        Action.update_all(0.06)  # Complete second actions in each sequence

        # All actions should be done
        assert action1.done
        assert action2.done
        assert action3.done
        assert action4.done

    def test_traditional_vs_operator_equivalence(self):
        """Test that operator syntax produces equivalent results to function syntax."""
        from actions.conditional import DelayUntil, duration

        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()

        # Traditional function approach
        action1_func = DelayUntil(duration(0.05))
        action2_func = DelayUntil(duration(0.05))
        traditional = sequence(action1_func, action2_func)
        traditional.apply(sprite1)

        # Operator approach
        action1_op = DelayUntil(duration(0.05))
        action2_op = DelayUntil(duration(0.05))
        operator_based = action1_op + action2_op
        operator_based.apply(sprite2)

        # Both should behave identically - complete first actions
        Action.update_all(0.06)
        assert action1_func.done == action1_op.done

        # Complete second actions
        Action.update_all(0.06)
        assert action2_func.done == action2_op.done


class TestRepeatFunction:
    """Test suite for repeat() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeat_initialization(self):
        """Test repeat initialization."""
        from actions.conditional import DelayUntil, duration

        action = DelayUntil(duration(0.1))
        rep = repeat(action)

        assert rep.action == action
        assert rep.current_action is None
        assert not rep.done

    def test_repeat_starts_first_iteration(self):
        """Test that repeat starts the first iteration of the action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        assert rep.current_action is not None
        assert rep.current_action is not action  # Should be a clone
        assert not rep.done

    def test_repeat_restarts_action_when_completed(self):
        """Test that repeat restarts the action when it completes."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        # Get the first iteration
        first_iteration = rep.current_action

        # Update until first iteration completes
        rep.update(0.06)
        assert first_iteration.done

        # Should have started a new iteration
        assert rep.current_action is not first_iteration
        assert not rep.done

    def test_repeat_continues_indefinitely(self):
        """Test that repeat continues indefinitely."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        # Run multiple iterations
        for i in range(5):
            current_action = rep.current_action
            assert not rep.done

            # Complete this iteration
            rep.update(0.06)
            assert current_action.done

            # Trigger start of next iteration (may be deferred one frame)
            if rep.current_action is None:
                rep.update(0.0)

            assert rep.current_action is not current_action

    def test_repeat_stop_stops_current_action(self):
        """Test that stopping repeat stops the current action."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action = DelayUntil(duration(1.0))  # Long duration
        rep = repeat(action)

        rep.target = sprite
        rep.start()
        rep.stop()

        assert rep.current_action.done
        assert rep.done

    def test_repeat_clone(self):
        """Test repeat cloning."""
        from actions.conditional import DelayUntil, duration

        action = DelayUntil(duration(0.1))
        rep = repeat(action)

        cloned = rep.clone()

        assert cloned is not rep
        assert cloned.action is not action
        assert cloned.current_action is None

    def test_repeat_with_no_action(self):
        """Test repeat with no action (should complete immediately)."""
        sprite = create_test_sprite()
        rep = repeat(None)

        rep.target = sprite
        rep.start()

        assert rep.done

    def test_repeat_with_composite_action(self):
        """Test repeat with a composite action (sequence)."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)
        rep = repeat(seq)

        rep.target = sprite
        rep.start()

        # First iteration should start
        assert rep.current_action is not None
        assert rep.current_action is not seq  # Should be a clone
        assert not rep.done

        # Complete first iteration (both delays)
        rep.update(0.06)  # Complete first delay
        rep.update(0.06)  # Complete second delay, complete sequence

        # Ensure the repeat schedules a new iteration (might begin next frame)
        if rep.current_action is None:
            rep.update(0.0)

        assert rep.current_action is not None
        assert not rep.done

    def test_repeat_with_move_action(self):
        """Test repeat with a MoveUntil action."""
        from actions.conditional import MoveUntil, duration

        sprite = create_test_sprite()

        # Move right for a short duration
        move_action = MoveUntil(velocity=(100, 0), condition=duration(0.05))
        rep = repeat(move_action)
        rep.apply(sprite, tag="test_repeat")

        # Update to complete first iteration
        Action.update_all(0.06)

        # Ensure a new iteration has started (may require zero-dt tick)
        if sprite.change_x == 0:
            Action.update_all(0.0)

        assert sprite.change_x == 100  # Velocity should be set by new iteration

        # Update again with partial duration - iteration should still be running
        Action.update_all(0.03)

        # Should still have velocity from repeat cycles
        assert sprite.change_x == 100


class TestRepeatIntegration:
    """Integration tests for repeat with other composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeat_in_sequence(self):
        """Test repeat action used within a sequence."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        setup_action = DelayUntil(duration(0.05))
        repeating_action = DelayUntil(duration(0.05))

        # Create sequence: setup action + repeating action
        rep = repeat(repeating_action)
        seq = sequence(setup_action, rep)

        seq.apply(sprite)

        # First, setup action should run
        Action.update_all(0.06)  # Complete setup

        # Now repeat should start and run indefinitely
        # Since repeat never completes, sequence never completes
        Action.update_all(0.06)  # First repeat iteration
        Action.update_all(0.06)  # Second repeat iteration

        # Sequence should still be running the repeat
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1  # The sequence is still active

    def test_repeat_in_parallel(self):
        """Test repeat action used within a parallel."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        finite_action = DelayUntil(duration(0.1))
        repeating_action = DelayUntil(duration(0.05))

        # Create parallel: finite action + repeating action
        rep = repeat(repeating_action)
        par = parallel(finite_action, rep)

        par.apply(sprite)

        # Both should start
        Action.update_all(0.06)  # First repeat cycle completes, finite still running
        Action.update_all(0.06)  # Finite action completes, second repeat cycle

        # Since repeat never completes, parallel never completes naturally
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1  # The parallel is still active

    def test_operator_overloading_with_repeat(self):
        """Test that repeat works with operator overloading (+, |)."""
        from actions.conditional import DelayUntil, duration

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))

        # Create complex composition using operators
        rep = repeat(action1)
        composed = action2 + rep  # Sequence: action2 then infinite repeat

        composed.apply(sprite)

        # Update to complete first action
        Action.update_all(0.06)

        # Now repeat should be running
        Action.update_all(0.06)  # First repeat iteration
        Action.update_all(0.06)  # Second repeat iteration

        # Should still be active
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
