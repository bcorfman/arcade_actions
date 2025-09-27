"""Test suite for CycleTexturesUntil action and cycle_textures_until helper."""

import arcade
import pytest

from actions import Action, duration, infinite
from tests.conftest import ActionTestBase


def create_test_textures(count: int = 5) -> list[arcade.Texture]:
    """Create a list of test textures for cycling."""
    textures = []
    for i in range(count):
        # Create simple colored textures for testing using Arcade 3.x API
        color = (255, min(i * 50, 255), 0, 255)  # Ensure color values don't exceed 255
        texture = arcade.Texture.create_empty(f"test_texture_{i}", (10, 10), color)
        textures.append(texture)
    return textures


class TestCycleTexturesUntil(ActionTestBase):
    """Test suite for CycleTexturesUntil action."""

    def test_cycle_textures_init(self):
        """Test CycleTexturesUntil initialization."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(textures=textures, frames_per_second=30.0, direction=1, condition=infinite)

        assert action._textures == textures
        assert action._fps == 30.0
        assert action._direction == 1
        assert action._count == 3
        assert action._cursor == 0.0
        assert not action.done

    def test_cycle_textures_init_with_negative_direction(self):
        """Test CycleTexturesUntil initialization with negative direction."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(textures=textures, frames_per_second=60.0, direction=-1, condition=infinite)

        assert action._fps == -60.0  # direction affects fps
        assert action._direction == -1

    def test_cycle_textures_init_validation(self):
        """Test CycleTexturesUntil initialization validation."""
        from actions.conditional import CycleTexturesUntil

        # Test empty textures list
        with pytest.raises(ValueError, match="textures list cannot be empty"):
            CycleTexturesUntil(textures=[], frames_per_second=60.0, direction=1, condition=infinite)

        # Test invalid direction
        with pytest.raises(ValueError, match="direction must be 1 or -1"):
            CycleTexturesUntil(
                textures=create_test_textures(3), frames_per_second=60.0, direction=0, condition=infinite
            )

    def test_cycle_textures_apply_effect_single_sprite(self, test_sprite):
        """Test CycleTexturesUntil apply_effect method with single sprite."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(textures=textures, frames_per_second=60.0, direction=1, condition=infinite)
        action.target = test_sprite  # Set target before calling apply_effect

        action.apply_effect()

        assert test_sprite.textures == textures
        assert test_sprite.texture == textures[0]

    def test_cycle_textures_apply_effect_sprite_list(self, test_sprite_list):
        """Test CycleTexturesUntil apply_effect method with sprite list."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(textures=textures, frames_per_second=60.0, direction=1, condition=infinite)
        action.target = test_sprite_list  # Set target before calling apply_effect

        action.apply_effect()

        for sprite in test_sprite_list:
            assert sprite.textures == textures
            assert sprite.texture == textures[0]

    def test_cycle_textures_update_effect_forward(self, test_sprite):
        """Test CycleTexturesUntil update_effect method moving forward."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=120.0,  # 2 frames per 1/60th second
            direction=1,
            condition=infinite,
        )
        action.target = test_sprite  # Set target before calling methods

        action.apply_effect()

        # Initial state
        assert test_sprite.texture == textures[0]
        assert action._cursor == 0.0

        # Update with 1/60th second (should advance by 2 frames)
        dt = 1.0 / 60.0
        action.update_effect(dt)

        assert action._cursor == 2.0
        assert test_sprite.texture == textures[2]  # floor(2.0) = 2

        # Update again (should wrap around)
        action.update_effect(dt)

        expected_cursor = (2.0 + 2.0) % 4  # = 0.0
        assert action._cursor == expected_cursor
        assert test_sprite.texture == textures[0]

    def test_cycle_textures_update_effect_backward(self, test_sprite):
        """Test CycleTexturesUntil update_effect method moving backward."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,  # 1 frame per 1/60th second
            direction=-1,
            condition=infinite,
        )
        action.target = test_sprite  # Set target before calling methods

        action.apply_effect()

        # Initial state
        assert test_sprite.texture == textures[0]
        assert action._cursor == 0.0

        # Update with 1/60th second (should move backward by 1 frame)
        dt = 1.0 / 60.0
        action.update_effect(dt)

        expected_cursor = (0.0 - 1.0) % 4  # = 3.0
        assert action._cursor == expected_cursor
        assert test_sprite.texture == textures[3]  # floor(3.0) = 3

        # Update again
        action.update_effect(dt)

        expected_cursor = (3.0 - 1.0) % 4  # = 2.0
        assert action._cursor == expected_cursor
        assert test_sprite.texture == textures[2]

    def test_cycle_textures_fractional_cursor(self, test_sprite):
        """Test CycleTexturesUntil with fractional cursor values."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=30.0,  # 0.5 frames per 1/60th second
            direction=1,
            condition=infinite,
        )
        action.target = test_sprite  # Set target before calling methods

        action.apply_effect()

        # Update multiple times to test fractional advancement
        dt = 1.0 / 60.0

        # First update: cursor = 0.5, texture index = floor(0.5) = 0
        action.update_effect(dt)
        assert action._cursor == 0.5
        assert test_sprite.texture == textures[0]

        # Second update: cursor = 1.0, texture index = floor(1.0) = 1
        action.update_effect(dt)
        assert action._cursor == 1.0
        assert test_sprite.texture == textures[1]

        # Third update: cursor = 1.5, texture index = floor(1.5) = 1
        action.update_effect(dt)
        assert action._cursor == 1.5
        assert test_sprite.texture == textures[1]

    def test_cycle_textures_wrapping_behavior(self, test_sprite):
        """Test texture cycling wraps correctly after N + ε frames."""
        from actions.conditional import CycleTexturesUntil

        texture_count = 5
        textures = create_test_textures(texture_count)
        action = CycleTexturesUntil(textures=textures, frames_per_second=60.0, direction=1, condition=infinite)

        action.target = test_sprite  # Set target before calling methods
        action.apply_effect()

        dt = 1.0 / 60.0  # 1 frame per update

        # Update through exactly N frames
        for i in range(texture_count):
            expected_texture = textures[i]
            assert test_sprite.texture == expected_texture
            action.update_effect(dt)

        # After N frames, should wrap back to texture 0
        assert test_sprite.texture == textures[0]
        assert action._cursor == 0.0  # Should wrap to 0 due to modulo

        # Update by epsilon (small fractional amount)
        epsilon = 0.1 / 60.0  # Small time increment
        action.update_effect(epsilon)

        # Should still be on texture 0 since cursor is still < 1.0
        expected_cursor = (texture_count + 0.1) % texture_count  # ≈ 0.1
        assert abs(action._cursor - expected_cursor) < 1e-10
        assert test_sprite.texture == textures[0]

    def test_cycle_textures_with_sprite_list(self, test_sprite_list):
        """Test CycleTexturesUntil with multiple sprites."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(textures=textures, frames_per_second=60.0, direction=1, condition=infinite)

        action.target = test_sprite_list  # Set target before calling methods
        action.apply_effect()

        # All sprites should start with first texture
        for sprite in test_sprite_list:
            assert sprite.texture == textures[0]

        # Update and verify all sprites have same texture
        dt = 1.0 / 60.0
        action.update_effect(dt)

        for sprite in test_sprite_list:
            assert sprite.texture == textures[1]

    def test_cycle_textures_condition_completion(self, test_sprite):
        """Test CycleTexturesUntil stops when condition is met."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)

        # Create a condition that becomes true after some updates
        update_count = 0

        def stop_after_updates():
            nonlocal update_count
            update_count += 1
            return update_count >= 3

        action = CycleTexturesUntil(
            textures=textures, frames_per_second=60.0, direction=1, condition=stop_after_updates
        )

        action.apply(test_sprite, tag="test_cycle")

        # Update until condition is met
        dt = 1.0 / 60.0
        for _ in range(5):  # More than enough updates
            Action.update_all(dt)
            if action.done:
                break

        assert action.done
        assert update_count >= 3

    def test_cycle_textures_integration_with_action_system(self, test_sprite):
        """Test CycleTexturesUntil integrates properly with Action system."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=240.0,  # 4 frames per 1/60th second
            direction=1,
            condition=infinite,
        )

        # Apply action to sprite
        action.apply(test_sprite, tag="cycle_test")

        # Verify action is active
        assert not action.done
        assert len(Action._active_actions) == 1

        # Update through action system
        dt = 1.0 / 60.0
        Action.update_all(dt)

        # Should have advanced by 4 frames (wrapping around 4-texture list)
        assert test_sprite.texture == textures[0]  # 4 % 4 = 0

        # Stop action and verify cleanup
        Action.stop_actions_for_target(test_sprite, "cycle_test")
        assert len(Action._active_actions) == 0


class TestCycleTexturesUntilHelper(ActionTestBase):
    """Test suite for cycle_textures_until helper function."""

    def test_cycle_textures_until_helper_basic(self, test_sprite):
        """Test basic cycle_textures_until helper functionality."""
        from actions import cycle_textures_until

        textures = create_test_textures(3)

        # Apply using helper function
        cycle_textures_until(test_sprite, textures=textures, frames_per_second=60.0, direction=1, tag="helper_test")

        # Verify action was applied
        assert len(Action._active_actions) == 1
        assert test_sprite.texture == textures[0]

        # Update and verify cycling
        dt = 1.0 / 60.0
        Action.update_all(dt)
        assert test_sprite.texture == textures[1]

    def test_cycle_textures_until_helper_with_condition(self, test_sprite):
        """Test cycle_textures_until helper with custom condition."""
        from actions import cycle_textures_until

        textures = create_test_textures(5)

        # Create condition that stops after some time
        elapsed = 0.0

        def time_condition():
            nonlocal elapsed
            return elapsed >= 0.1  # Stop after 0.1 seconds

        cycle_textures_until(
            test_sprite,
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=time_condition,
            tag="timed_cycle",
        )

        # Update for several frames
        dt = 1.0 / 60.0
        for _ in range(10):
            elapsed += dt
            Action.update_all(dt)
            if not Action._active_actions:  # Action completed
                break

        # Action should have stopped due to condition
        assert len(Action._active_actions) == 0

    def test_cycle_textures_until_helper_with_sprite_list(self, test_sprite_list):
        """Test cycle_textures_until helper with sprite list."""
        from actions import cycle_textures_until

        textures = create_test_textures(4)

        cycle_textures_until(
            test_sprite_list,
            textures=textures,
            frames_per_second=120.0,  # 2 frames per update
            direction=-1,  # Backward
            tag="list_cycle",
        )

        # All sprites should start with first texture
        for sprite in test_sprite_list:
            assert sprite.texture == textures[0]

        # Update and verify backward cycling
        dt = 1.0 / 60.0
        Action.update_all(dt)

        # Should have moved backward by 2 frames: (0 - 2) % 4 = 2
        for sprite in test_sprite_list:
            assert sprite.texture == textures[2]

    def test_cycle_textures_until_helper_default_parameters(self, test_sprite):
        """Test cycle_textures_until helper with default parameters."""
        from actions import cycle_textures_until

        textures = create_test_textures(3)

        # Use defaults: frames_per_second=60.0, direction=1, condition=infinite
        cycle_textures_until(test_sprite, textures=textures)

        assert len(Action._active_actions) == 1

        # Should advance by 1 frame per 1/60th second
        dt = 1.0 / 60.0
        Action.update_all(dt)
        assert test_sprite.texture == textures[1]

    def test_cycle_textures_until_helper_tagging(self, test_sprite):
        """Test cycle_textures_until helper with action tagging."""
        from actions import cycle_textures_until

        textures = create_test_textures(2)

        # Apply two different cycling actions with different tags
        cycle_textures_until(test_sprite, textures=textures, frames_per_second=30.0, tag="cycle1")

        cycle_textures_until(test_sprite, textures=textures, frames_per_second=60.0, tag="cycle2")

        # Should have two active actions
        assert len(Action._active_actions) == 2

        # Stop one tag
        Action.stop_actions_for_target(test_sprite, "cycle1")
        assert len(Action._active_actions) == 1

        # Stop the other tag
        Action.stop_actions_for_target(test_sprite, "cycle2")
        assert len(Action._active_actions) == 0

    def test_cycle_textures_until_helper_invalid_parameters(self, test_sprite):
        """Test cycle_textures_until helper with invalid parameters."""
        from actions import cycle_textures_until

        # Test with empty textures
        with pytest.raises(ValueError, match="textures list cannot be empty"):
            cycle_textures_until(test_sprite, textures=[])

        # Test with invalid direction
        with pytest.raises(ValueError, match="direction must be 1 or -1"):
            cycle_textures_until(test_sprite, textures=create_test_textures(3), direction=2)

    def test_cycle_textures_until_helper_on_stop_callback(self, test_sprite):
        """Test cycle_textures_until helper with on_stop callback."""
        from actions import cycle_textures_until

        textures = create_test_textures(3)
        callback_called = False

        def on_stop_callback():
            nonlocal callback_called
            callback_called = True

        cycle_textures_until(
            test_sprite,
            textures=textures,
            frames_per_second=60.0,
            condition=duration(0.05),  # Very short duration
            on_stop=on_stop_callback,
            tag="callback_test",
        )

        # Update until action completes (need real time for duration condition)
        import time

        start_time = time.time()
        dt = 1.0 / 60.0
        while time.time() - start_time < 0.1:  # Run for up to 0.1 seconds
            Action.update_all(dt)
            if not Action._active_actions:
                break
            time.sleep(0.001)  # Small delay for real time to pass

        assert callback_called
        assert len(Action._active_actions) == 0


class TestCycleTexturesUntilDurationSupport(ActionTestBase):
    """Test suite for CycleTexturesUntil duration support (simulation time)."""

    def test_cycle_textures_duration_extraction_basic(self, test_sprite):
        """Test that CycleTexturesUntil extracts duration from duration() condition."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.5),  # 0.5 seconds
        )
        action.apply(test_sprite, tag="duration_test")

        # Check that duration was extracted
        assert hasattr(action, "_duration")
        assert action._duration == 0.5
        assert hasattr(action, "_elapsed")
        assert action._elapsed == 0.0

    def test_cycle_textures_duration_completion(self, test_sprite):
        """Test that CycleTexturesUntil completes after specified duration."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.1),  # 0.1 seconds
        )
        action.apply(test_sprite, tag="duration_completion")

        # Run for exactly 0.1 seconds at 60 FPS (6 frames)
        dt = 1.0 / 60.0
        for frame in range(6):
            Action.update_all(dt)
            if action.done:
                break

        # Should complete exactly at 0.1 seconds
        assert action.done
        assert abs(action._elapsed - 0.1) < 1e-9

    def test_cycle_textures_duration_scaling_with_factor(self, test_sprite):
        """Test that CycleTexturesUntil duration scales with set_factor."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.2),  # 0.2 seconds
        )
        action.apply(test_sprite, tag="factor_test")

        # Set factor to 2.0 (double speed)
        action.set_factor(2.0)

        # Run for 0.1 seconds of real time (should complete in half the time)
        dt = 1.0 / 60.0
        for frame in range(6):  # 6 frames = 0.1 seconds
            Action.update_all(dt)
            if action.done:
                break

        # Should complete in 0.1 seconds real time (0.2 seconds simulation time)
        assert action.done
        assert abs(action._elapsed - 0.2) < 1e-9  # _elapsed tracks simulation time

    def test_cycle_textures_factor_pausing(self, test_sprite):
        """Test that CycleTexturesUntil can be paused with factor=0."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.2),
        )
        action.apply(test_sprite, tag="pause_test")

        # Run for a few frames normally
        dt = 1.0 / 60.0
        for _ in range(3):
            Action.update_all(dt)

        elapsed_before_pause = action._elapsed
        texture_before_pause = test_sprite.texture

        # Pause the action
        action.set_factor(0.0)

        # Run more frames - should not advance
        for _ in range(5):
            Action.update_all(dt)

        # Should be paused
        assert action._elapsed == elapsed_before_pause
        assert test_sprite.texture == texture_before_pause
        assert not action.done

        # Resume the action
        action.set_factor(1.0)

        # Should continue from where it left off
        Action.update_all(dt)
        assert action._elapsed > elapsed_before_pause

    def test_cycle_textures_reset_functionality(self, test_sprite):
        """Test that CycleTexturesUntil can be reset to initial state."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.2),
        )
        action.apply(test_sprite, tag="reset_test")

        # Run for several frames
        dt = 1.0 / 60.0
        for _ in range(5):
            Action.update_all(dt)

        # State should have advanced
        assert action._elapsed > 0
        assert action._cursor > 0
        assert test_sprite.texture != textures[0]

        # Reset the action
        action.reset()

        # Should be back to initial state
        assert action._elapsed == 0.0
        assert action._cursor == 0.0
        assert not action.done

        # Reapply to restore sprite state
        action.apply_effect()
        assert test_sprite.texture == textures[0]

    def test_cycle_textures_duration_with_on_stop_callback(self, test_sprite):
        """Test that CycleTexturesUntil calls on_stop when duration completes."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        callback_called = False
        callback_data = None

        def on_stop(data=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.05),  # Very short duration
            on_stop=on_stop,
        )
        action.apply(test_sprite, tag="callback_test")

        # Run until completion
        dt = 1.0 / 60.0
        for _ in range(10):
            Action.update_all(dt)
            if action.done:
                break

        assert action.done
        assert callback_called

    def test_cycle_textures_duration_clone_preserves_state(self, test_sprite):
        """Test that cloning CycleTexturesUntil preserves duration state."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        original = CycleTexturesUntil(
            textures=textures,
            frames_per_second=120.0,
            direction=-1,
            condition=duration(0.3),
        )

        # Clone the action
        cloned = original.clone()

        # Both should have same configuration
        assert cloned._textures == original._textures
        assert cloned._fps == original._fps
        assert cloned._direction == original._direction
        assert cloned._count == original._count

        # Apply both and verify they work independently
        original.apply(test_sprite, tag="original")

        # Create a second sprite for the clone
        sprite2 = arcade.Sprite()
        cloned.apply(sprite2, tag="clone")

        # Both should have same initial state
        assert test_sprite.texture == textures[0]
        assert sprite2.texture == textures[0]

        # Update both
        dt = 1.0 / 60.0
        Action.update_all(dt)

        # Both should advance by 2 frames backward: (0 - 2) % 4 = 2
        assert test_sprite.texture == textures[2]
        assert sprite2.texture == textures[2]

    def test_cycle_textures_duration_mixed_with_custom_condition(self, test_sprite):
        """Test CycleTexturesUntil with non-duration condition (fallback behavior)."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)

        # Custom condition that doesn't use duration()
        frame_count = 0

        def custom_condition():
            nonlocal frame_count
            frame_count += 1
            return frame_count >= 8

        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=custom_condition,
        )
        action.apply(test_sprite, tag="custom_condition")

        # Should not have duration tracking for non-duration conditions
        assert not hasattr(action, "_duration") or action._duration is None

        # Should still work with the custom condition
        dt = 1.0 / 60.0
        for _ in range(10):
            Action.update_all(dt)
            if action.done:
                break

        assert action.done
        assert frame_count >= 8

    def test_cycle_textures_duration_zero_duration(self, test_sprite):
        """Test CycleTexturesUntil with zero duration completes immediately."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(3)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.0),  # Zero duration
        )
        action.apply(test_sprite, tag="zero_duration")

        # Should complete immediately
        assert action.done

    def test_cycle_textures_duration_simulation_time_independence(self, test_sprite):
        """Test that CycleTexturesUntil duration is independent of frame rate."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(5)

        # Test with different delta times but same total elapsed time
        for frame_rate in [30, 60, 120]:  # Different frame rates
            action = CycleTexturesUntil(
                textures=textures,
                frames_per_second=60.0,  # Texture animation rate
                direction=1,
                condition=duration(0.1),  # 0.1 seconds
            )
            action.apply(test_sprite, tag=f"framerate_{frame_rate}")

            # Update with different delta times to reach 0.1 seconds total
            dt = 1.0 / frame_rate
            frames_needed = int(0.1 * frame_rate)

            for _ in range(frames_needed):
                Action.update_all(dt)
                if action.done:
                    break

            # Should complete at roughly the same simulation time regardless of frame rate
            assert action.done
            assert abs(action._elapsed - 0.1) < 1e-9

            # Clean up for next iteration
            Action.stop_all()

    def test_cycle_textures_factor_affects_both_timing_and_animation(self, test_sprite):
        """Test that set_factor affects both duration timing and animation speed."""
        from actions.conditional import CycleTexturesUntil

        textures = create_test_textures(4)
        action = CycleTexturesUntil(
            textures=textures,
            frames_per_second=60.0,  # 1 frame per 1/60 second normally
            direction=1,
            condition=duration(0.2),  # 0.2 seconds duration
        )
        action.apply(test_sprite, tag="factor_both_test")

        # Set factor to 3.0 (triple speed)
        action.set_factor(3.0)

        # Run for 1 frame at normal rate
        dt = 1.0 / 60.0
        Action.update_all(dt)

        # Should advance by 3 frames in texture animation: 0 + 3 = 3
        expected_texture_index = 3 % len(textures)  # Should be texture 3
        assert test_sprite.texture == textures[expected_texture_index]

        # Duration should also be scaled: 1/60 * 3.0 = 3/60 = 0.05 seconds elapsed
        assert abs(action._elapsed - 0.05) < 1e-9

    def test_cycle_textures_helper_with_duration_support(self, test_sprite):
        """Test cycle_textures_until helper properly supports duration conditions."""
        from actions import cycle_textures_until

        textures = create_test_textures(3)

        # Use helper with duration condition
        action = cycle_textures_until(
            test_sprite,
            textures=textures,
            frames_per_second=60.0,
            direction=1,
            condition=duration(0.1),  # Should use simulation time
            tag="helper_duration",
        )

        # Should have duration tracking
        assert hasattr(action, "_duration")
        assert action._duration == 0.1

        # Run for 0.1 seconds
        dt = 1.0 / 60.0
        for _ in range(6):  # 6 frames = 0.1 seconds
            Action.update_all(dt)
            if action.done:
                break

        assert action.done
        assert abs(action._elapsed - 0.1) < 1e-9
