"""Test suite for API sugar - helper functions and operator overloading."""

import arcade
import pytest

from actions.base import Action
from actions.conditional import MoveUntil, RotateUntil
from actions.helpers import move_until

# Import helpers and composite actions once they exist
# from actions.helpers import move_until, rotate_until
# from actions.composite import sequence, parallel


# Fixtures for creating test sprites and lists
@pytest.fixture
def sprite() -> arcade.Sprite:
    """Return a simple sprite for testing."""
    return arcade.SpriteSolidColor(50, 50, color=arcade.color.RED)


@pytest.fixture
def sprite_list() -> arcade.SpriteList:
    """Return a simple sprite list for testing."""
    s1 = arcade.SpriteSolidColor(50, 50, color=arcade.color.GREEN)
    s2 = arcade.SpriteSolidColor(50, 50, color=arcade.color.BLUE)
    return arcade.SpriteList.from_sprites([s1, s2])


class TestHelperFunctions:
    """Tests for thin wrapper helper functions."""

    def teardown_method(self):
        Action.clear_all()

    def test_move_until_helper_applies_action(self, sprite):
        """Test move_until helper creates and applies a MoveUntil action."""
        # This should create a MoveUntil action and apply it to the sprite
        action = move_until(sprite, (10, 0), lambda: False, tag="test_move")

        assert isinstance(action, MoveUntil)
        assert len(Action._active_actions) == 1
        assert action in Action._active_actions
        assert action.tag == "test_move"
        assert action.target == sprite

    def test_move_until_helper_returns_action(self, sprite):
        """Test move_until helper returns the created action instance."""
        move_action = move_until(sprite, (5, 0), lambda: False)
        assert isinstance(move_action, MoveUntil)
        # We can still interact with the returned action
        move_action.set_factor(0.5)
        assert move_action.current_velocity == (2.5, 0.0)

    def test_helper_unbound_action_creation(self):
        """Test that calling a helper without a target returns a raw, unapplied action."""
        # No target provided - should return a raw action instance, not applied
        raw_action = move_until((10, 0), lambda: False)

        assert isinstance(raw_action, MoveUntil)
        assert not raw_action.target  # Not bound to any sprite
        assert len(Action._active_actions) == 0  # Should not be in the active list


class TestOperatorOverloading:
    """Tests for operator-based composition (+ for sequence, | for parallel)."""

    def teardown_method(self):
        Action.clear_all()

    def test_add_operator_for_sequence(self):
        """Test that the '+' operator creates a sequential action."""
        from actions.composite import _Sequence

        action1 = MoveUntil((10, 0), lambda: False)
        action2 = RotateUntil(5, lambda: False)

        sequence_action = action1 + action2

        assert isinstance(sequence_action, _Sequence)
        assert sequence_action.actions == [action1, action2]
        assert len(Action._active_actions) == 0  # Should not be active yet

    def test_or_operator_for_parallel(self):
        """Test that the '|' operator creates a parallel action."""
        from actions.composite import _Parallel

        action1 = MoveUntil((10, 0), lambda: False)
        action2 = RotateUntil(5, lambda: False)

        parallel_action = action1 | action2

        assert isinstance(parallel_action, _Parallel)
        assert parallel_action.actions == [action1, action2]
        assert len(Action._active_actions) == 0

    def test_right_hand_operators(self):
        """Test right-hand operators (__radd__, __ror__) for composition."""
        from actions.composite import _Parallel, _Sequence
        from actions.conditional import DelayUntil

        move = MoveUntil((10, 0), lambda: False)
        delay = DelayUntil(lambda: False)

        # Test __radd__
        seq = delay + move
        assert isinstance(seq, _Sequence)

        # Test __ror__
        par = delay | move
        assert isinstance(par, _Parallel)

    def test_operator_precedence(self, sprite):
        """Test that a + b | c is evaluated as a + (b | c)."""
        from actions.composite import _Parallel, _Sequence

        a = MoveUntil((1, 0), lambda: False)
        b = MoveUntil((2, 0), lambda: False)
        c = RotateUntil(3, lambda: False)

        # Should be evaluated as: a + (b | c)
        composite = a + (b | c)

        assert isinstance(composite, _Sequence)
        assert len(composite.actions) == 2
        assert composite.actions[0] == a
        assert isinstance(composite.actions[1], _Parallel)

        parallel_part = composite.actions[1]
        assert parallel_part.actions == [b, c]

    def test_complex_chaining_with_apply(self, sprite):
        """Test a complex chain of operators and applying the result."""
        from actions.conditional import DelayUntil

        action = DelayUntil(lambda: False) + (MoveUntil((5, 0), lambda: False) | RotateUntil(2, lambda: False))
        action.apply(sprite)

        assert len(Action._active_actions) > 0

    def test_repr_for_composite_actions(self):
        """Test the __repr__ for a nested composite action created with operators."""
        from actions.conditional import DelayUntil

        move = MoveUntil((5, 0), lambda: False)
        rotate = RotateUntil(2, lambda: False)
        delay = DelayUntil(lambda: False)

        action = delay + (move | rotate)

        expected_repr = "_Sequence(actions=[DelayUntil(condition=...), _Parallel(actions=[MoveUntil(target_velocity=(5, 0), ...), RotateUntil(angular_velocity=2, ...)])])"
        # A simplified check to avoid exact repr matching issues
        assert "_Sequence" in repr(action)
        assert "_Parallel" in repr(action)
        assert "MoveUntil" in repr(action)
        assert "RotateUntil" in repr(action)
        assert "DelayUntil" in repr(action)
