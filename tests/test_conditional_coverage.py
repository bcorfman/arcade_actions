"""Tests to cover missing branches and edge cases in conditional actions."""

import arcade
import pytest

from actions.base import Action
from actions.conditional import (
    MoveUntil,
    ParametricMotionUntil,
    TweenUntil,
    infinite,
)
from actions.frame_timing import after_frames, seconds_to_frames


class TestMoveUntilCoverage:
    """Tests for uncovered MoveUntil functionality."""

    def test_reverse_movement_x_axis(self):
        """Test reversing movement on X axis."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil((5, 0), infinite)
        action.apply(sprite, tag="move")
        Action.update_all(1 / 60)

        # Verify initial movement
        assert sprite.change_x == 5
        assert sprite.change_y == 0

        # Reverse X movement
        action.reverse_movement("x")
        assert sprite.change_x == -5
        assert sprite.change_y == 0

    def test_reverse_movement_y_axis(self):
        """Test reversing movement on Y axis."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil((0, 5), infinite)
        action.apply(sprite, tag="move")
        Action.update_all(1 / 60)

        # Verify initial movement
        assert sprite.change_x == 0
        assert sprite.change_y == 5

        # Reverse Y movement
        action.reverse_movement("y")
        assert sprite.change_x == 0
        assert sprite.change_y == -5

    def test_reverse_movement_invalid_axis(self):
        """Test that invalid axis raises ValueError."""
        sprite = arcade.Sprite()
        action = MoveUntil((5, 5), infinite)
        action.apply(sprite, tag="move")

        with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
            action.reverse_movement("z")

    def test_reset_velocity(self):
        """Test reset() restores target velocity after modification."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil((10, 20), infinite)
        action.apply(sprite, tag="move")

        # Modify velocity
        action.set_current_velocity((5, 10))
        assert sprite.change_x == 5
        assert sprite.change_y == 10

        # Reset to original
        action.reset()
        assert sprite.change_x == 10
        assert sprite.change_y == 20

    def test_limit_behavior_reaches_left_boundary(self):
        """Test _limit_behavior when sprite reaches left boundary using edge-based bounds."""
        sprite = arcade.Sprite()
        sprite.center_x = 50
        sprite.center_y = 100

        bounds = (100, 0, 800, 600)
        action = MoveUntil((-5, 0), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Move sprite past left boundary
        for _ in range(20):
            Action.update_all(1 / 60)

        # Should be clamped at left boundary (edge-based)
        assert sprite.left == 100
        assert sprite.change_x == 0

    def test_limit_behavior_reaches_right_boundary(self):
        """Test _limit_behavior when sprite reaches right boundary using edge-based bounds."""
        sprite = arcade.Sprite()
        sprite.center_x = 796  # Start closer to boundary
        sprite.center_y = 100

        bounds = (0, 0, 800, 600)
        action = MoveUntil((5, 0), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update to let sprite move toward boundary
        for _ in range(5):
            Action.update_all(1 / 60)

        # Should be clamped at right boundary (edge-based)
        assert sprite.right == 800
        assert sprite.change_x == 0

    def test_limit_behavior_reaches_bottom_boundary(self):
        """Test _limit_behavior when sprite reaches bottom boundary using edge-based bounds."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 50

        bounds = (0, 100, 800, 600)
        action = MoveUntil((0, -5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Move sprite past bottom boundary
        for _ in range(20):
            Action.update_all(1 / 60)

        # Should be clamped at bottom boundary (edge-based)
        assert sprite.bottom == 100
        assert sprite.change_y == 0

    def test_limit_behavior_reaches_top_boundary(self):
        """Test _limit_behavior when sprite reaches top boundary using edge-based bounds."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 596  # Start closer to boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, 5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update to let sprite move toward boundary
        for _ in range(5):
            Action.update_all(1 / 60)

        # Should be clamped at top boundary (edge-based)
        assert sprite.top == 600
        assert sprite.change_y == 0

    def test_duration_elapsed_calls_on_stop(self):
        """Test that on_stop is called when duration elapses."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        callback_called = []

        def on_stop():
            callback_called.append(True)

        action = MoveUntil((5, 0), condition=after_frames(seconds_to_frames(0.1)), on_stop=on_stop)
        action.apply(sprite, tag="move")

        # Update until duration elapses
        for _ in range(10):
            Action.update_all(1 / 60)

        assert len(callback_called) == 1
        assert action.done

    def test_velocity_provider_with_boundary_enter_callbacks(self):
        """Test velocity provider with boundary enter/exit callbacks."""
        sprite = arcade.Sprite()
        sprite.center_x = 795  # Start close to boundary
        sprite.center_y = 100

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        # Velocity provider that moves sprite right into boundary
        def velocity_provider():
            return (10, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (10, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # Move one frame - should hit boundary (795 + 10 > 800)
        Action.update_all(1 / 60)

        # Should have entered right boundary
        assert len(enter_calls) > 0
        assert enter_calls[0] == ("x", "right")

    def test_velocity_provider_boundary_exit_callback(self):
        """Test velocity provider with boundary exit callback - covers lines 267-271, 299-303."""
        sprite = arcade.Sprite()
        sprite.center_x = 805  # Start beyond right boundary
        sprite.center_y = 100

        exit_calls = []
        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def on_exit(s, axis, side):
            exit_calls.append((axis, side))

        # First move right to establish boundary state
        def velocity_provider():
            return (10, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (10, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
        )
        action.apply(sprite, tag="move")

        # First frame - should enter boundary (already beyond it)
        Action.update_all(1 / 60)
        assert len(enter_calls) > 0

        # Now change velocity provider to move left (away from boundary)
        action.velocity_provider = lambda: (-10, 0)

        # Next frame - should exit boundary
        Action.update_all(1 / 60)

        # Should have exited right boundary
        assert len(exit_calls) > 0
        assert exit_calls[0] == ("x", "right")

    def test_boundary_enter_callback_in_apply_effect(self):
        """Test boundary enter callback is triggered in apply_effect when starting at boundary."""
        sprite = arcade.Sprite()
        # Start beyond right boundary
        sprite.center_x = 850
        sprite.center_y = 100

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        bounds = (0, 0, 800, 600)
        # Try to move right (but already past boundary)
        action = MoveUntil(
            (10, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # Should trigger enter callback immediately
        assert len(enter_calls) > 0
        assert enter_calls[0][0] == "x"
        assert enter_calls[0][1] == "right"


class TestTweenUntilCoverage:
    """Tests for uncovered TweenUntil functionality."""

    def test_tween_external_condition_stops_early(self):
        """Test TweenUntil stopped by external condition before natural completion."""
        sprite = arcade.Sprite()
        sprite.center_x = 100

        # Condition that becomes true before duration completes
        frame_count = [0]

        def early_stop():
            frame_count[0] += 1
            return frame_count[0] >= 3  # Stop after 3 frames

        action = TweenUntil(100, 200, "center_x", early_stop)
        action.apply(sprite, tag="tween")

        # Run for 3 frames
        for _ in range(3):
            Action.update_all(1 / 60)

        # Should be stopped by condition (not natural completion)
        assert action.done
        # Should be reset to start value since not completed naturally
        assert sprite.center_x == 100

        Action.stop_actions_for_target(sprite)

        # Test 2: Early stop by condition resets to start value
        sprite.center_x = 100
        frame_count = [0]

        def early_condition():
            frame_count[0] += 1
            return frame_count[0] >= 2  # Stop after 2 frames

        action2 = TweenUntil(100, 200, "center_x", early_condition)
        action2.apply(sprite, tag="tween2")

        # Run for 2 frames
        for _ in range(2):
            Action.update_all(1 / 60)

        # Should be reset to start value since not completed naturally
        assert not action2._completed_naturally
        assert sprite.center_x == 100


class TestParametricMotionUntilCoverage:
    """Tests for uncovered ParametricMotionUntil functionality."""

    def test_parametric_motion_reset(self):
        """Test ParametricMotionUntil reset() restores initial state."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        def offset_fn(t):
            return (t * 100, t * 100)

        action = ParametricMotionUntil(offset_fn, condition=after_frames(seconds_to_frames(1.0)))
        action.apply(sprite, tag="motion")

        # Run for a bit
        for _ in range(10):
            Action.update_all(1 / 60)

        # Reset
        Action.stop_actions_for_target(sprite, tag="motion")
        action.reset()

        # Should be back to initial state
        assert action._elapsed == 0.0
        assert len(action._origins) == 0
        assert action._prev_offset is None
        assert not action._condition_met
        assert not action.done

    def test_parametric_motion_with_rotation(self):
        """Test ParametricMotionUntil with rotate_with_path enabled."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        sprite.angle = 0

        # Simple linear motion to the right
        def offset_fn(t):
            return (t * 100, 0)

        action = ParametricMotionUntil(
            offset_fn,
            after_frames(seconds_to_frames(1.0)),
            rotate_with_path=True,
        )
        action.apply(sprite, tag="motion")

        # Run for several frames
        for _ in range(10):
            Action.update_all(1 / 60)

        # Sprite should be rotated to face right (0 degrees)
        assert abs(sprite.angle) < 5  # Allow small tolerance

    def test_parametric_motion_with_rotation_offset(self):
        """Test ParametricMotionUntil with rotation_offset."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        sprite.angle = 0

        # Linear motion to the right
        def offset_fn(t):
            return (t * 100, 0)

        # Add 90 degree offset (e.g., sprite artwork points up by default)
        action = ParametricMotionUntil(
            offset_fn,
            after_frames(seconds_to_frames(1.0)),
            rotate_with_path=True,
            rotation_offset=90.0,
        )
        action.apply(sprite, tag="motion")

        # Run for several frames
        for _ in range(10):
            Action.update_all(1 / 60)

        # Sprite should be rotated 90 degrees more than facing right
        assert abs(sprite.angle - 90) < 5

    def test_parametric_motion_zero_duration_fallback(self):
        """Test ParametricMotionUntil with condition that has no extractable frame count."""

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        def offset_fn(t):
            return (t * 100, 0)

        # Use a condition without frame metadata (should default to 0 frames = instant)
        def custom_condition():
            return False

        action = ParametricMotionUntil(
            offset_fn,
            custom_condition,
        )
        action.apply(sprite, tag="motion")

        # Should default to 0 frames (instant completion)
        assert action._frame_duration == 0.0

    def test_parametric_motion_completes_naturally(self):
        """Test ParametricMotionUntil completes when duration elapses."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        completed = []

        def on_complete(data=None):
            completed.append(True)

        def offset_fn(t):
            return (t * 100, 0)

        frames = seconds_to_frames(0.1)
        action = ParametricMotionUntil(
            offset_fn,
            after_frames(frames),
            on_stop=on_complete,
        )
        action.apply(sprite, tag="motion")

        # Run until completion
        for _ in range(frames + 5):
            Action.update_all(1 / 60)
            if action.done:
                break

        assert action.done
        assert len(completed) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
