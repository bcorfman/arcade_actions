"""Test suite for named action slots functionality in ActionSprite.

This module tests the new named slots feature that allows sprites to run
multiple orthogonal actions simultaneously while maintaining full backward
compatibility with the existing single-action API.
"""

import pytest

from actions.base import ActionSprite
from actions.instant import Hide
from actions.interval import FadeTo, MoveBy, RotateBy


class TestNamedSlots:
    """Test suite for named action slots functionality."""

    @pytest.fixture
    def sprite(self):
        """Create a test sprite."""
        return ActionSprite(":resources:images/items/star.png")

    def test_backward_compatibility_single_action(self, sprite):
        """Test that single actions still work exactly as before."""
        move_action = MoveBy((100, 0), 1.0)

        # Old API should still work
        sprite.do(move_action)
        assert sprite._action == move_action
        assert sprite.is_busy()
        assert sprite.has_active_actions()

        # Update and verify
        sprite.update(0.5)
        assert sprite.center_x > 0
        assert not move_action.done

        # Clear and verify
        sprite.clear_actions()
        assert sprite._action is None
        assert not sprite.is_busy()

    def test_named_slots_basic_usage(self, sprite):
        """Test basic named slots functionality."""
        move_action = MoveBy((100, 0), 1.0)
        rotate_action = RotateBy(90, 1.0)

        # Apply actions to different slots
        sprite.do(move_action, slot="movement")
        sprite.do(rotate_action, slot="rotation")

        # Both actions should be active
        assert sprite.has_active_actions()
        assert sprite.is_busy()

        # Check that both actions are in their respective slots
        assert sprite._actions["movement"] == move_action
        assert sprite._actions["rotation"] == rotate_action

        # Default slot should be empty
        assert sprite._actions["default"] is None
        assert sprite._action is None

    def test_named_slots_independent_updates(self, sprite):
        """Test that actions in different slots update independently."""
        quick_move = MoveBy((50, 0), 0.5)  # Short action
        slow_rotate = RotateBy(180, 2.0)  # Long action

        sprite.do(quick_move, slot="movement")
        sprite.do(slow_rotate, slot="rotation")

        # Update for half the quick action duration
        sprite.update(0.25)
        assert not quick_move.done
        assert not slow_rotate.done
        assert sprite.center_x > 0
        assert sprite.angle > 0

        # Update to complete the quick action
        sprite.update(0.25)
        assert quick_move.done
        assert not slow_rotate.done

        # Movement slot should be cleared, rotation still active
        assert sprite._actions["movement"] is None
        assert sprite._actions["rotation"] == slow_rotate
        assert sprite.has_active_actions()  # Still busy with rotation

    def test_named_slots_slot_replacement(self, sprite):
        """Test that new actions replace existing actions in the same slot."""
        move1 = MoveBy((50, 0), 1.0)
        move2 = MoveBy((0, 50), 1.0)

        # Apply first action
        sprite.do(move1, slot="movement")
        assert sprite._actions["movement"] == move1

        # Replace with second action in same slot
        sprite.do(move2, slot="movement")
        assert sprite._actions["movement"] == move2
        assert move1.target is None  # First action should be stopped

        # Update and verify only the second action is running
        sprite.update(0.5)
        assert sprite.center_x == 0  # No horizontal movement
        assert sprite.center_y > 0  # Vertical movement from move2

    def test_clear_specific_slot(self, sprite):
        """Test clearing a specific action slot."""
        move_action = MoveBy((100, 0), 1.0)
        rotate_action = RotateBy(90, 1.0)
        fade_action = FadeTo(128, 1.0)

        # Apply multiple actions
        sprite.do(move_action, slot="movement")
        sprite.do(rotate_action, slot="rotation")
        sprite.do(fade_action, slot="effects")

        # Clear just the effects slot
        sprite.clear_action(slot="effects")

        # Effects should be cleared, others should remain
        assert sprite._actions["effects"] is None
        assert sprite._actions["movement"] == move_action
        assert sprite._actions["rotation"] == rotate_action
        assert sprite.has_active_actions()

        # Fade action should be stopped
        assert fade_action.target is None

    def test_clear_all_actions_with_slots(self, sprite):
        """Test that clear_actions() clears all slots."""
        move_action = MoveBy((100, 0), 1.0)
        rotate_action = RotateBy(90, 1.0)
        fade_action = FadeTo(128, 1.0)

        # Apply actions to different slots
        sprite.do(move_action, slot="movement")
        sprite.do(rotate_action, slot="rotation")
        sprite.do(fade_action, slot="effects")

        # Clear all actions
        sprite.clear_actions()

        # All slots should be cleared
        assert sprite._actions["movement"] is None
        assert sprite._actions["rotation"] is None
        assert sprite._actions["effects"] is None
        assert not sprite.has_active_actions()
        assert not sprite.is_busy()

    def test_pause_resume_all_slots(self, sprite):
        """Test that pause/resume affects all active slots."""
        move_action = MoveBy((100, 0), 2.0)
        rotate_action = RotateBy(180, 2.0)

        sprite.do(move_action, slot="movement")
        sprite.do(rotate_action, slot="rotation")

        # Update to start movement
        sprite.update(0.5)
        initial_x = sprite.center_x
        initial_angle = sprite.angle

        # Pause all actions
        sprite.pause()

        # Update should not change position/angle
        sprite.update(0.5)
        assert sprite.center_x == initial_x
        assert sprite.angle == initial_angle

        # Resume all actions
        sprite.resume()

        # Update should continue movement
        sprite.update(0.5)
        assert sprite.center_x > initial_x
        assert sprite.angle > initial_angle

    def test_mixed_default_and_named_slots(self, sprite):
        """Test mixing default slot usage with named slots."""
        default_action = MoveBy((50, 0), 1.0)
        named_action = RotateBy(90, 1.0)

        # Use default slot (backward compatibility)
        sprite.do(default_action)

        # Use named slot
        sprite.do(named_action, slot="rotation")

        # Both should be active
        assert sprite._action == default_action  # Backward compatibility
        assert sprite._actions["default"] == default_action
        assert sprite._actions["rotation"] == named_action
        assert sprite.has_active_actions()

        # Clear just the default slot
        sprite.clear_action()  # Uses default slot

        # Default should be cleared, named should remain
        assert sprite._action is None
        assert sprite._actions["default"] is None
        assert sprite._actions["rotation"] == named_action
        assert sprite.has_active_actions()  # Still has rotation action

    def test_orthogonal_behaviors_scenario(self, sprite):
        """Test a realistic scenario with orthogonal behaviors."""
        # Simulate a game where a sprite needs to:
        # 1. Follow a movement path (from AI system)
        # 2. Flash red when damaged (from combat system)
        # 3. Fade out when dying (from health system)

        movement_path = MoveBy((200, 100), 3.0)
        damage_flash = Hide()  # Simulate flashing by hiding briefly
        death_fade = FadeTo(0, 1.0)

        # Apply orthogonal behaviors
        sprite.do(movement_path, slot="ai_movement")
        sprite.do(damage_flash, slot="combat_effects")
        sprite.do(death_fade, slot="health_effects")

        # All systems should be active
        assert len([a for a in sprite._actions.values() if a is not None]) == 3

        # Combat system can stop just the damage flash
        sprite.clear_action(slot="combat_effects")

        # Movement and death fade should continue
        assert sprite._actions["ai_movement"] == movement_path
        assert sprite._actions["health_effects"] == death_fade
        assert sprite._actions["combat_effects"] is None

        # Health system can stop just the death fade
        sprite.clear_action(slot="health_effects")

        # Only movement should remain
        assert sprite._actions["ai_movement"] == movement_path
        assert sprite._actions["health_effects"] is None
        assert sprite.has_active_actions()

    def test_slot_action_completion_cleanup(self, sprite):
        """Test that completed actions are automatically cleaned up."""
        quick_action = MoveBy((10, 0), 0.1)  # Very quick
        slow_action = RotateBy(360, 2.0)  # Much slower

        sprite.do(quick_action, slot="quick")
        sprite.do(slow_action, slot="slow")

        # Update to complete the quick action
        sprite.update(0.1)

        # Quick action should be completed and cleaned up
        assert quick_action.done
        assert sprite._actions["quick"] is None

        # Slow action should still be active
        assert not slow_action.done
        assert sprite._actions["slow"] == slow_action
        assert sprite.has_active_actions()

    def test_empty_slot_operations(self, sprite):
        """Test operations on empty slots don't cause errors."""
        # Clearing an empty slot should not error
        sprite.clear_action(slot="nonexistent")

        # Operations on sprite with no actions should work
        assert not sprite.has_active_actions()
        assert not sprite.is_busy()

        # Pause/resume with no actions should work
        sprite.pause()
        sprite.resume()

        # Clear all with no actions should work
        sprite.clear_actions()
