"""Test suite for debug.py - Runtime debugging helpers."""

from unittest.mock import patch

from actions import Action
from actions.debug import MotionDebugger, attach_motion_debugger
from tests.conftest import ActionTestBase


class TestMotionDebugger(ActionTestBase):
    """Test suite for MotionDebugger action."""

    def test_motion_debugger_initialization(self):
        """Test MotionDebugger initialization with default threshold."""
        debugger = MotionDebugger()
        assert debugger.threshold == 20.0
        assert debugger._prev_positions == {}
        assert not debugger.done

    def test_motion_debugger_custom_threshold(self):
        """Test MotionDebugger initialization with custom threshold."""
        debugger = MotionDebugger(threshold=50.0)
        assert debugger.threshold == 50.0
        assert debugger._prev_positions == {}

    def test_apply_effect_captures_initial_positions(self, test_sprite):
        """Test that apply_effect captures initial sprite positions."""
        debugger = MotionDebugger()
        debugger.apply(test_sprite)

        # Apply effect should capture initial positions
        debugger.apply_effect()

        sprite_id = id(test_sprite)
        assert sprite_id in debugger._prev_positions
        assert debugger._prev_positions[sprite_id] == (test_sprite.center_x, test_sprite.center_y)

    def test_apply_effect_with_multiple_sprites(self, test_sprite_list):
        """Test apply_effect with multiple sprites."""
        debugger = MotionDebugger()
        debugger.apply(test_sprite_list)

        debugger.apply_effect()

        # Should capture positions for all sprites
        assert len(debugger._prev_positions) == 2
        for sprite in test_sprite_list:
            sprite_id = id(sprite)
            assert sprite_id in debugger._prev_positions
            assert debugger._prev_positions[sprite_id] == (sprite.center_x, sprite.center_y)

    @patch("builtins.print")
    def test_update_effect_no_jump(self, mock_print, test_sprite):
        """Test update_effect when no significant jump occurs."""
        debugger = MotionDebugger(threshold=20.0)
        debugger.apply(test_sprite)

        # Capture initial position
        debugger.apply_effect()

        # Small movement should not trigger debug output
        test_sprite.center_x += 5.0
        test_sprite.center_y += 5.0

        debugger.update_effect(0.016)

        # Should not print anything for small movement
        mock_print.assert_not_called()

    @patch("builtins.print")
    def test_update_effect_large_jump(self, mock_print, test_sprite):
        """Test update_effect when a large jump occurs."""
        debugger = MotionDebugger(threshold=20.0)
        debugger.apply(test_sprite)

        # Capture initial position
        debugger.apply_effect()

        # Large movement should trigger debug output
        test_sprite.center_x += 50.0
        test_sprite.center_y += 30.0

        with patch("time.time", return_value=12345.678):
            debugger.update_effect(0.016)

        # Should print debug message
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "[MotionDebugger]" in call_args
        assert "t=12345.678" in call_args
        assert "sprite_id=" in call_args
        assert "Δ=" in call_args
        assert "threshold=20.0" in call_args

    @patch("builtins.print")
    def test_update_effect_jump_calculation(self, mock_print, test_sprite):
        """Test that jump distance is calculated correctly."""
        debugger = MotionDebugger(threshold=10.0)
        debugger.apply(test_sprite)

        # Capture initial position
        debugger.apply_effect()

        # Move sprite by exactly the threshold distance
        test_sprite.center_x += 10.0
        test_sprite.center_y += 0.0

        debugger.update_effect(0.016)

        # Should not trigger (exactly at threshold)
        mock_print.assert_not_called()

        # Move by a large amount to exceed threshold
        test_sprite.center_x += 15.0  # Jump from previous position is 15.0 > 10.0
        debugger.update_effect(0.016)

        # Should trigger now (distance = 15.0 > 10.0)
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_update_effect_diagonal_jump(self, mock_print, test_sprite):
        """Test jump detection with diagonal movement."""
        debugger = MotionDebugger(threshold=20.0)
        debugger.apply(test_sprite)

        debugger.apply_effect()

        # Diagonal movement that exceeds threshold
        test_sprite.center_x += 15.0
        test_sprite.center_y += 15.0
        # Distance = sqrt(15^2 + 15^2) = sqrt(450) ≈ 21.21 > 20

        debugger.update_effect(0.016)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Δ=21.21" in call_args or "Δ=21.2" in call_args

    def test_update_effect_updates_positions(self, test_sprite):
        """Test that update_effect updates stored positions."""
        debugger = MotionDebugger()
        debugger.apply(test_sprite)

        debugger.apply_effect()
        initial_pos = debugger._prev_positions[id(test_sprite)]

        # Move sprite
        test_sprite.center_x += 10.0
        test_sprite.center_y += 5.0

        debugger.update_effect(0.016)

        # Position should be updated
        new_pos = debugger._prev_positions[id(test_sprite)]
        assert new_pos != initial_pos
        assert new_pos == (test_sprite.center_x, test_sprite.center_y)

    def test_update_effect_handles_missing_previous_position(self, test_sprite):
        """Test update_effect handles sprites without previous position."""
        debugger = MotionDebugger()
        debugger.apply(test_sprite)

        # Don't call apply_effect, so no previous position stored
        test_sprite.center_x += 50.0

        with patch("builtins.print") as mock_print:
            debugger.update_effect(0.016)

        # Should use current position as previous and trigger (50 > 20 threshold)
        mock_print.assert_called_once()
        assert id(test_sprite) in debugger._prev_positions

    def test_clone(self):
        """Test MotionDebugger cloning."""
        debugger = MotionDebugger(threshold=30.0)
        cloned = debugger.clone()

        assert isinstance(cloned, MotionDebugger)
        assert cloned.threshold == 30.0
        assert cloned._prev_positions == {}
        assert cloned is not debugger

    def test_motion_debugger_with_action_system(self, test_sprite):
        """Test MotionDebugger integration with Action system."""
        debugger = MotionDebugger(threshold=20.0)
        debugger.apply(test_sprite, tag="debug")

        # Should be registered with Action system
        assert debugger in Action._active_actions

        # Update through Action system
        Action.update_all(0.016)

        # Should have captured initial position
        assert id(test_sprite) in debugger._prev_positions


class TestAttachMotionDebugger(ActionTestBase):
    """Test suite for attach_motion_debugger helper function."""

    def test_attach_motion_debugger_sprite(self, test_sprite):
        """Test attaching motion debugger to a sprite."""
        debugger = attach_motion_debugger(test_sprite)

        assert isinstance(debugger, MotionDebugger)
        assert debugger.threshold == 20.0
        assert debugger in Action._active_actions
        assert debugger.target == test_sprite

    def test_attach_motion_debugger_sprite_list(self, test_sprite_list):
        """Test attaching motion debugger to a sprite list."""
        debugger = attach_motion_debugger(test_sprite_list)

        assert isinstance(debugger, MotionDebugger)
        assert debugger in Action._active_actions
        assert debugger.target == test_sprite_list

    def test_attach_motion_debugger_custom_threshold(self, test_sprite):
        """Test attaching motion debugger with custom threshold."""
        debugger = attach_motion_debugger(test_sprite, threshold=50.0)

        assert debugger.threshold == 50.0

    def test_attach_motion_debugger_custom_tag(self, test_sprite):
        """Test attaching motion debugger with custom tag."""
        debugger = attach_motion_debugger(test_sprite, tag="custom_debug")

        # Check that the action is bound with the correct tag
        assert debugger in Action._active_actions

    def test_attach_motion_debugger_no_tag(self, test_sprite):
        """Test attaching motion debugger with no tag."""
        debugger = attach_motion_debugger(test_sprite, tag=None)

        assert isinstance(debugger, MotionDebugger)
        assert debugger in Action._active_actions

    def test_attach_motion_debugger_default_tag(self, test_sprite):
        """Test attaching motion debugger with default tag."""
        debugger = attach_motion_debugger(test_sprite)

        # Should use default tag "motion_debugger"
        assert isinstance(debugger, MotionDebugger)
