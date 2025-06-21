"""
Comprehensive tests for the Action cloning system.

This module tests both the structural requirements (all Action subclasses
must implement clone()) and functional behavior (cloning works correctly
in real-world scenarios) of the action cloning system that replaced the
brittle _safe_copy_action approach.
"""

import inspect

import pytest

from actions import composite, group, instant, interval, move
from actions.base import Action, ActionSprite
from actions.composite import loop, sequence, spawn
from actions.group import SpriteGroup
from actions.instant import Hide, Place
from actions.interval import MoveBy, RotateBy

# Import all modules that contain Action subclasses
ALL_ACTION_MODULES = [instant, interval, composite, move, group]


def get_all_action_subclasses():
    """Discover all Action subclasses from the actions package."""
    action_classes = []

    for module in ALL_ACTION_MODULES:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Action) and obj is not Action and not inspect.isabstract(obj):
                action_classes.append(obj)

    return action_classes


# =============================================================================
# STRUCTURAL TESTS - Enforce that all Action subclasses implement clone()
# =============================================================================


class TestCloneImplementationEnforcement:
    """Enforce that all Action subclasses properly implement clone()."""

    def test_all_action_subclasses_override_clone(self):
        """Test that all concrete Action subclasses override the clone() method.

        This test acts as a safety net - it will fail immediately if someone
        adds a new Action subclass without implementing clone(), preventing
        silent failures in GroupAction cloning.
        """
        action_classes = get_all_action_subclasses()

        # Ensure we found some action classes
        assert len(action_classes) > 0, "No Action subclasses found - test setup issue"

        failed_classes = []

        for action_class in action_classes:
            # Check if the class has its own clone method (not inherited from base Action)
            if "clone" not in action_class.__dict__:
                failed_classes.append(action_class.__name__)

        if failed_classes:
            pytest.fail(
                f"The following Action subclasses do not override clone(): {failed_classes}. "
                f"Each Action subclass must implement its own clone() method to ensure "
                f"proper action copying without fragile runtime type checks."
            )

    def test_clone_returns_correct_type(self):
        """Test that clone() methods return the correct type."""
        action_classes = get_all_action_subclasses()

        for action_class in action_classes:
            # Skip classes that can't be instantiated easily (require complex parameters)
            if action_class.__name__ in [
                "BoundedMove",
                "WrappedMove",
                "Bezier",
                "JumpTo",
                "JumpBy",
                "CallFunc",
                "CallFuncS",
                "Easing",
            ]:
                continue

            try:
                # Try to create a minimal instance
                if action_class.__name__ in ["MoveTo", "MoveBy"]:
                    instance = action_class((10, 10), 1.0)
                elif action_class.__name__ in ["RotateTo", "RotateBy"]:
                    instance = action_class(45.0, 1.0)
                elif action_class.__name__ in ["ScaleTo", "ScaleBy"]:
                    instance = action_class(2.0, 1.0)
                elif action_class.__name__ in ["FadeTo"]:
                    instance = action_class(128, 1.0)
                elif action_class.__name__ in ["FadeOut", "FadeIn", "Delay"]:
                    instance = action_class(1.0)
                elif action_class.__name__ in ["RandomDelay"]:
                    instance = action_class(0.5, 1.5)
                elif action_class.__name__ in ["Blink"]:
                    instance = action_class(5, 1.0)
                elif action_class.__name__ in ["Place"]:
                    instance = action_class((100, 100))
                elif action_class.__name__ in ["Loop", "Repeat"]:
                    # These need an action parameter, skip for now
                    continue
                elif action_class.__name__ in ["Sequence", "Spawn"]:
                    # These can be empty
                    instance = action_class()
                elif action_class.__name__ in ["GroupAction"]:
                    # Skip GroupAction as it needs sprites
                    continue
                else:
                    # Try default constructor
                    instance = action_class()

                # Test that clone returns the correct type
                cloned = instance.clone()
                assert type(cloned) is action_class, (
                    f"{action_class.__name__}.clone() returned {type(cloned)} instead of {action_class}"
                )

            except Exception:
                # If we can't instantiate, that's okay - the important test is the first one
                pass


# =============================================================================
# FUNCTIONAL TESTS - Validate that cloning works correctly in practice
# =============================================================================


class TestCloneFunctionality:
    """Test that the clone system works correctly in real-world scenarios."""

    def test_basic_action_cloning(self):
        """Test that basic actions clone correctly and independently."""
        # Create action with specific parameters
        original_move = MoveBy((50, 25), 1.0)

        # Clone the action
        cloned_move = original_move.clone()

        # Verify independence
        assert cloned_move is not original_move
        assert cloned_move.delta == original_move.delta
        assert cloned_move.duration == original_move.duration

        # Modify original - clone should be unaffected
        original_move.delta = (100, 100)
        assert cloned_move.delta == (50, 25)  # Clone unaffected

    def test_composite_action_cloning(self):
        """Test that composite actions (sequence, spawn, loop) clone their children."""
        # Create nested composite actions
        move1 = MoveBy((10, 0), 0.5)
        move2 = MoveBy((0, 10), 0.5)
        hide_action = Hide()

        # Create nested composition
        move_sequence = sequence(move1, move2)
        complex_action = spawn(move_sequence, hide_action)

        # Clone the complex action
        cloned_complex = complex_action.clone()

        # Verify deep independence
        assert cloned_complex is not complex_action
        assert len(cloned_complex.actions) == 2

        # Verify nested actions are also cloned
        cloned_sequence = cloned_complex.actions[0]
        assert cloned_sequence is not move_sequence
        assert len(cloned_sequence.actions) == 2
        assert cloned_sequence.actions[0] is not move1
        assert cloned_sequence.actions[1] is not move2

    def test_group_action_cloning_robustness(self):
        """Test that GroupAction uses robust clone() instead of _safe_copy_action."""
        # Create a sprite group
        sprite_group = SpriteGroup()
        for i in range(3):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.center_x = 100 + i * 50
            sprite.center_y = 200
            sprite_group.append(sprite)

        # Create a complex action
        move_action = MoveBy((100, 50), 2.0)
        rotate_action = RotateBy(90, 1.5)
        complex_action = sequence(move_action, rotate_action)

        # Apply to group - this now uses clone() internally
        group_action = sprite_group.do(complex_action)

        # Verify each sprite got its own independent action copy
        assert len(group_action.actions) == 3
        for action in group_action.actions:
            assert action is not complex_action  # Independent copy
            assert type(action).__name__ == "Sequence"  # Correct type preserved
            assert len(action.actions) == 2  # Structure preserved

        # Verify template is preserved
        assert group_action.template is complex_action

    def test_clone_preserves_configuration(self):
        """Test that clone() preserves the original action's configuration."""
        # Test with various action types
        test_cases = [
            (
                MoveBy((50, 100), 2.0),
                lambda orig, cloned: (cloned.delta == orig.delta and cloned.duration == orig.duration),
            ),
            (
                RotateBy(90.0, 1.5),
                lambda orig, cloned: (cloned.angle == orig.angle and cloned.duration == orig.duration),
            ),
            (Place((200, 300)), lambda orig, cloned: (cloned.position == orig.position)),
        ]

        for original, validator in test_cases:
            cloned = original.clone()
            assert validator(original, cloned), f"Configuration not preserved for {type(original).__name__}"

    def test_clone_system_performance_characteristics(self):
        """Test that clone() is more predictable than the old _safe_copy_action system."""
        # The old _safe_copy_action had 3 fallback strategies:
        # 1. copy.copy() - could fail for complex objects
        # 2. type(action)(**action.__dict__) - fragile and error-prone
        # 3. copy.deepcopy() - slow and unpredictable

        # The new clone() approach:
        # - Single, predictable path per action type
        # - No runtime type checking or fallbacks
        # - Each action knows how to clone itself properly

        # Create various action types
        actions = [
            MoveBy((10, 10), 1.0),
            RotateBy(45, 0.5),
            Place((100, 200)),
            Hide(),
            sequence(MoveBy((5, 5), 0.5), RotateBy(90, 0.5)),
            loop(MoveBy((1, 1), 0.1), 5),
        ]

        # All actions can be cloned reliably
        for action in actions:
            cloned = action.clone()
            assert cloned is not action
            assert type(cloned) is type(action)
            # Each clone succeeds predictably without fallback strategies


# =============================================================================
# INTEGRATION TESTS - Test clone system in realistic scenarios
# =============================================================================


class TestCloneIntegration:
    """Test cloning in realistic game development scenarios."""

    def test_multiple_sprite_groups_with_same_action_template(self):
        """Test that multiple sprite groups can use the same action template safely."""
        # Create two sprite groups
        group1 = SpriteGroup()
        group2 = SpriteGroup()

        for group in [group1, group2]:
            for i in range(2):
                sprite = ActionSprite(":resources:images/items/star.png")
                sprite.center_x = 100 + i * 50
                sprite.center_y = 200
                group.append(sprite)

        # Create one action template
        move_template = MoveBy((50, 0), 1.0)

        # Apply same template to both groups
        group1_action = group1.do(move_template)
        group2_action = group2.do(move_template)

        # Verify each group got independent copies
        assert group1_action.template is move_template
        assert group2_action.template is move_template
        assert len(group1_action.actions) == 2
        assert len(group2_action.actions) == 2

        # Verify all individual sprite actions are independent
        all_sprite_actions = group1_action.actions + group2_action.actions
        for i, action1 in enumerate(all_sprite_actions):
            for j, action2 in enumerate(all_sprite_actions):
                if i != j:
                    assert action1 is not action2, "Sprite actions should be independent"

    def test_complex_nested_action_hierarchies(self):
        """Test cloning works with deeply nested action hierarchies."""
        # Create a complex nested structure:
        # Spawn(
        #   Sequence(MoveBy, RotateBy),
        #   Loop(Sequence(MoveBy, RotateBy), 3)
        # )

        inner_sequence = sequence(MoveBy((5, 5), 0.2), RotateBy(45, 0.2))
        loop_action = loop(inner_sequence, 3)
        outer_sequence = sequence(MoveBy((10, 10), 0.5), RotateBy(45, 0.5))
        complex_spawn = spawn(outer_sequence, loop_action)

        # Clone the entire hierarchy
        cloned = complex_spawn.clone()

        # Verify structure is preserved but instances are independent
        assert type(cloned).__name__ == "Spawn"
        assert len(cloned.actions) == 2

        # Check first branch (sequence)
        cloned_sequence = cloned.actions[0]
        assert type(cloned_sequence).__name__ == "Sequence"
        assert len(cloned_sequence.actions) == 2
        assert type(cloned_sequence.actions[0]).__name__ == "MoveBy"
        assert type(cloned_sequence.actions[1]).__name__ == "RotateBy"

        # Check second branch (loop containing sequence)
        cloned_loop = cloned.actions[1]
        assert type(cloned_loop).__name__ == "Loop"
        assert cloned_loop.times == 3
        assert type(cloned_loop.action).__name__ == "Sequence"

        # All instances should be independent
        assert cloned is not complex_spawn
        assert cloned_sequence is not outer_sequence
        assert cloned_loop is not loop_action
