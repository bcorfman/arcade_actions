"""Test suite for frame-based timing primitives.

This module tests the frame-driven API that replaces wall-clock timing.
All timing in ArcadeActions is based on frame counts, not seconds.
"""

import arcade

from arcadeactions import Action
from tests.conftest import ActionTestBase


class TestFrameCounter(ActionTestBase):
    """Test suite for Action.current_frame() and frame counter."""

    def test_frame_counter_starts_at_zero(self):
        """Test that frame counter starts at 0."""
        # Reset to ensure clean state
        Action._frame_counter = 0
        assert Action.current_frame() == 0

    def test_frame_counter_increments_on_update(self):
        """Test that frame counter increments with each update_all call."""
        Action._frame_counter = 0
        initial = Action.current_frame()

        Action.update_all(0.016)  # ~60 FPS
        assert Action.current_frame() == initial + 1

        Action.update_all(0.016)
        assert Action.current_frame() == initial + 2

        Action.update_all(0.016)
        assert Action.current_frame() == initial + 3

    def test_frame_counter_pauses_when_actions_paused(self, test_sprite):
        """Test that frame counter does NOT increment when actions are paused."""
        from arcadeactions import move_until
        from arcadeactions.conditional import infinite

        Action._frame_counter = 0
        sprite = test_sprite

        # Create an action so we have something to pause
        action = move_until(sprite, velocity=(10, 0), condition=infinite, tag="test_pause")

        Action.update_all(0.016)
        frame_before_pause = Action.current_frame()

        # Pause all actions
        Action.pause_all()

        # Update should not increment frame counter when paused
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause

        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause

        # Resume and verify counter increments again
        Action.resume_all()
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause + 1


class TestAfterFrames(ActionTestBase):
    """Test suite for after_frames() condition helper."""

    def test_after_frames_basic(self):
        """Test basic after_frames functionality."""
        from arcadeactions.frame_timing import after_frames

        condition = after_frames(3)

        # Should return False for first 2 frames
        assert condition() is False
        assert condition() is False

        # Should return True on 3rd call
        assert condition() is True

        # Should continue returning True
        assert condition() is True

    def test_after_frames_zero(self):
        """Test after_frames with zero frames."""
        from arcadeactions.frame_timing import after_frames

        condition = after_frames(0)

        # Should return True immediately
        assert condition() is True

    def test_after_frames_negative(self):
        """Test after_frames with negative frames (should behave like zero)."""
        from arcadeactions.frame_timing import after_frames

        condition = after_frames(-5)

        # Should return True immediately for negative frames
        assert condition() is True

    def test_after_frames_with_action(self, test_sprite):
        """Test after_frames as a condition in an action."""
        from arcadeactions import move_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        # Move for 5 frames at 10 px/frame
        action = move_until(sprite, velocity=(10, 0), condition=after_frames(5), tag="test_after_frames")

        # Update for 4 frames - action should still be active
        for _ in range(4):
            Action.update_all(0.016)
            sprite.update()

        assert not action.done
        assert 140 <= sprite.center_x <= 141  # ~4 frames of movement

        # 5th frame should complete the action (condition met, no movement applied)
        Action.update_all(0.016)
        sprite.update()

        assert action.done
        assert 140 <= sprite.center_x <= 141  # Still at 4 frames of movement (action stopped before applying frame 5)


class TestEveryFrames(ActionTestBase):
    """Test suite for every_frames() interval helper."""

    def test_every_frames_basic(self):
        """Test basic every_frames functionality."""
        from arcadeactions.frame_timing import every_frames

        counter = 0

        def increment():
            nonlocal counter
            counter += 1

        ticker = every_frames(3, increment)

        # First call should execute immediately
        ticker()
        assert counter == 1

        # Next 2 calls should not execute
        ticker()
        assert counter == 1
        ticker()
        assert counter == 1

        # 3rd call should execute
        ticker()
        assert counter == 2

        # Pattern repeats
        ticker()
        assert counter == 2
        ticker()
        assert counter == 2
        ticker()
        assert counter == 3

    def test_every_frames_one(self):
        """Test every_frames with interval of 1 (every frame)."""
        from arcadeactions.frame_timing import every_frames

        counter = 0

        def increment():
            nonlocal counter
            counter += 1

        ticker = every_frames(1, increment)

        # Should execute every call
        ticker()
        assert counter == 1
        ticker()
        assert counter == 2
        ticker()
        assert counter == 3

    def test_every_frames_with_callback_until(self, test_sprite):
        """Test every_frames with CallbackUntil action."""
        from arcadeactions import callback_until
        from arcadeactions.frame_timing import after_frames, every_frames

        sprite = test_sprite
        call_count = 0

        def on_interval():
            nonlocal call_count
            call_count += 1

        # Create ticker that fires every 3 frames
        ticker = every_frames(3, on_interval)

        # Run for 10 frames
        action = callback_until(sprite, callback=ticker, condition=after_frames(10), tag="test_every_frames")

        for _ in range(10):
            Action.update_all(0.016)

        # Should have fired on frames: 0, 3, 6, 9 = 4 times
        assert call_count == 4
        assert action.done


class TestWithinFrames(ActionTestBase):
    """Test suite for within_frames() window helper."""

    def test_within_frames_basic(self):
        """Test basic within_frames functionality."""
        from arcadeactions.frame_timing import within_frames

        condition = within_frames(2, 5)

        # Frame 0: False (before window)
        assert condition() is False

        # Frame 1: False (before window)
        assert condition() is False

        # Frames 2-4: True (within window)
        assert condition() is True
        assert condition() is True
        assert condition() is True

        # Frame 5+: False (after window)
        assert condition() is False
        assert condition() is False

    def test_within_frames_single_frame(self):
        """Test within_frames with single frame window."""
        from arcadeactions.frame_timing import within_frames

        condition = within_frames(3, 4)

        # Frames 0-2: False
        assert condition() is False
        assert condition() is False
        assert condition() is False

        # Frame 3: True
        assert condition() is True

        # Frame 4+: False
        assert condition() is False

    def test_within_frames_zero_start(self):
        """Test within_frames starting at frame 0."""
        from arcadeactions.frame_timing import within_frames

        condition = within_frames(0, 3)

        # Frames 0-2: True
        assert condition() is True
        assert condition() is True
        assert condition() is True

        # Frame 3+: False
        assert condition() is False


class TestPauseResumeStepBehavior(ActionTestBase):
    """Test suite for pause/resume/step behavior with frame timing."""

    def test_pause_halts_frame_counter(self, test_sprite):
        """Test that pausing stops frame counter and action progress."""
        from arcadeactions import move_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        action = move_until(sprite, velocity=(10, 0), condition=after_frames(10), tag="test_pause")

        # Run 3 frames
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        frame_at_pause = Action.current_frame()
        position_at_pause = sprite.center_x

        # Pause
        Action.pause_all()

        # Try to update - frame counter and position should not change
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Sprite still updates, but action doesn't apply velocity

        assert Action.current_frame() == frame_at_pause
        # Position might change slightly due to sprite.update(), but velocity should be 0
        assert sprite.change_x == 0  # Paused action doesn't set velocity

    def test_resume_continues_frame_counter(self, test_sprite):
        """Test that resuming continues frame counter and action progress."""
        from arcadeactions import move_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        action = move_until(sprite, velocity=(10, 0), condition=after_frames(10), tag="test_resume")

        # Run 3 frames
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        # Pause
        Action.pause_all()
        frame_at_pause = Action.current_frame()

        # Resume
        Action.resume_all()

        # Continue for 2 more frames
        for _ in range(2):
            Action.update_all(0.016)
            sprite.update()

        assert Action.current_frame() == frame_at_pause + 2
        assert not action.done  # Should still be running (3 + 2 = 5 < 10)

    def test_step_advances_one_frame(self, test_sprite):
        """Test that step_all advances exactly one frame while keeping paused."""
        from arcadeactions import move_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        action = move_until(sprite, velocity=(10, 0), condition=after_frames(10), tag="test_step")

        # Run 3 frames normally
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        # Pause
        Action.pause_all()
        frame_at_pause = Action.current_frame()

        # Step once
        Action.step_all(0.016)
        sprite.update()

        assert Action.current_frame() == frame_at_pause + 1

        # Actions should still be paused after step
        # Verify by trying normal update
        Action.update_all(0.016)
        assert Action.current_frame() == frame_at_pause + 1  # Should not advance

    def test_new_actions_inherit_pause_state(self, test_sprite):
        """Test that new actions created while paused start in paused state.

        This ensures game code doesn't need to know about pause state when
        creating new actions (e.g., firing bullets during pause).
        """
        from arcadeactions import move_until
        from arcadeactions.conditional import infinite

        # Create first sprite with action
        sprite1 = test_sprite
        sprite1.center_x = 100
        sprite1.center_y = 100

        action1 = move_until(sprite1, velocity=(2, 0), condition=infinite, tag="action1")

        # Run for a few frames
        for _ in range(3):
            Action.update_all(0.016)
            sprite1.update()

        position1_before_pause = sprite1.center_x

        # Pause all actions
        Action.pause_all()
        assert action1._paused
        assert sprite1.change_x == 0.0

        # Create a second sprite with action WHILE paused
        sprite2 = arcade.SpriteSolidColor(10, 10, arcade.color.WHITE)
        sprite2.center_x = 200
        sprite2.center_y = 200

        action2 = move_until(sprite2, velocity=(3, 0), condition=infinite, tag="action2")

        # The new action should automatically be paused
        assert action2._paused, "New action should inherit paused state"
        assert sprite2.change_x == 0.0, "New action should not set velocity when starting paused"

        # Update and verify neither sprite moves
        for _ in range(3):
            Action.update_all(0.016)
            sprite1.update()
            sprite2.update()

        assert sprite1.center_x == position1_before_pause, "First sprite should not move while paused"
        assert sprite2.center_x == 200, "Second sprite should not move (started paused)"

        # Resume and verify both sprites now move
        Action.resume_all()
        assert not action1._paused
        assert not action2._paused

        Action.update_all(0.016)
        sprite1.update()
        sprite2.update()

        assert sprite1.center_x > position1_before_pause, "First sprite should move after resume"
        assert sprite2.center_x > 200, "Second sprite should move after resume"

    def test_heavy_load_determinism(self, test_sprite):
        """Test that frame-based timing is deterministic regardless of delta_time."""
        from arcadeactions import move_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        action = move_until(sprite, velocity=(10, 0), condition=after_frames(5), tag="test_determinism")

        # Simulate varying frame times (performance hiccups)
        delta_times = [0.016, 0.016, 0.050, 0.016, 0.100]  # Varying performance

        for dt in delta_times:
            Action.update_all(dt)
            sprite.update()

        # Should complete after exactly 5 frames regardless of delta_time values
        assert action.done
        assert Action.current_frame() == 5

        # Position should be deterministic (4 frames of movement * 10 px/frame = 40 px)
        # Action completes on frame 5 but doesn't apply movement for that frame
        assert 140 <= sprite.center_x <= 141


class TestFrameTimingIntegration(ActionTestBase):
    """Integration tests for frame-based timing across multiple actions."""

    def test_multiple_actions_same_frame_timing(self, test_sprite):
        """Test multiple actions using frame timing complete at correct frames."""
        from arcadeactions import move_until, rotate_until
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100
        sprite.angle = 0

        # Two actions with different frame durations
        move_action = move_until(sprite, velocity=(10, 0), condition=after_frames(5), tag="move")
        rotate_action = rotate_until(sprite, angular_velocity=45, condition=after_frames(3), tag="rotate")

        # Run for 3 frames
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        # Rotate should be done, move should not
        assert rotate_action.done
        assert not move_action.done

        # Run 2 more frames
        for _ in range(2):
            Action.update_all(0.016)
            sprite.update()

        # Both should be done
        assert move_action.done
        assert rotate_action.done

    def test_frame_timing_with_sequences(self, test_sprite):
        """Test frame timing works correctly in sequences."""
        from arcadeactions import DelayUntil, MoveUntil, sequence
        from arcadeactions.frame_timing import after_frames

        sprite = test_sprite
        sprite.center_x = 100

        # Sequence: delay 3 frames, then move for 5 frames
        seq = sequence(DelayUntil(condition=after_frames(3)), MoveUntil(velocity=(10, 0), condition=after_frames(5)))
        seq.apply(sprite, tag="test_sequence")

        # Run for 3 frames (delay)
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        # Delay completes on frame 3, and MoveUntil starts in the same frame
        # So we get 1 frame of movement
        assert 109 <= sprite.center_x <= 111

        # Run for 4 more frames (move continues for frames 4-7, completes on frame 8)
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()

        # Total: 1 frame during delay completion + 4 frames of movement = 5 frames * 10 px = 50 px
        # (MoveUntil completes on frame 8 after applying movement for frames 4-7)
        assert 149 <= sprite.center_x <= 151
        assert seq.done
