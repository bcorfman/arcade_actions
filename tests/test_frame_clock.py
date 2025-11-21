"""Test suite for FrameClock semantics and Action.current_frame().

This module pins down the frame counter semantics to ensure deterministic
behavior with pause/resume/step debugging functionality.
"""

import arcade
import pytest

from actions import Action
from actions.frame_timing import after_frames
from tests.conftest import ActionTestBase


class TestFrameClockSemantics(ActionTestBase):
    """Test suite for frame counter semantics (FrameClock behavior via Action.current_frame())."""

    def test_frame_counter_starts_at_zero(self):
        """Frame counter should start at 0."""
        Action._frame_counter = 0
        assert Action.current_frame() == 0

    def test_frame_counter_increments_on_every_update(self):
        """Frame counter should increment on every update_all() call."""
        Action._frame_counter = 0

        # Counter increments even with no actions
        Action.update_all(0.016)
        assert Action.current_frame() == 1

        Action.update_all(0.016)
        assert Action.current_frame() == 2

        # Add an action - counter continues incrementing
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until
        from actions.conditional import infinite

        action = move_until(sprite, velocity=(5, 0), condition=infinite, tag="test")
        Action.update_all(0.016)
        assert Action.current_frame() == 3

        Action.update_all(0.016)
        assert Action.current_frame() == 4

        Action.stop_all()

    def test_frame_counter_pauses_when_all_actions_paused(self):
        """Frame counter should not increment when all actions are paused."""
        Action._frame_counter = 0
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until
        from actions.conditional import infinite

        action = move_until(sprite, velocity=(5, 0), condition=infinite, tag="test")

        # Update a few frames
        for _ in range(5):
            Action.update_all(0.016)
        frame_before_pause = Action.current_frame()
        assert frame_before_pause == 5

        # Pause all actions
        Action.pause_all()

        # Counter should not increment
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause

        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause

        # Resume
        Action.resume_all()
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause + 1

        Action.stop_all()

    def test_frame_counter_resumes_when_any_action_resumes(self):
        """Frame counter should resume when any action is resumed."""
        Action._frame_counter = 0
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until
        from actions.conditional import infinite

        action1 = move_until(sprite, velocity=(5, 0), condition=infinite, tag="test1")
        action2 = move_until(sprite, velocity=(0, 5), condition=infinite, tag="test2")

        # Update a few frames
        for _ in range(3):
            Action.update_all(0.016)
        frame_before_pause = Action.current_frame()
        assert frame_before_pause == 3

        # Pause all
        Action.pause_all()

        # Counter should not increment
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause

        # Resume one action
        action1.resume()

        # Counter should increment again
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before_pause + 1

        Action.stop_all()

    def test_step_all_advances_exactly_one_frame(self):
        """step_all() should advance exactly one frame."""
        Action._frame_counter = 0
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until
        from actions.frame_timing import after_frames

        action = move_until(sprite, velocity=(5, 0), condition=after_frames(10), tag="test")
        initial_frame = Action.current_frame()

        # Step should advance exactly one frame
        Action.step_all(0.016)
        assert Action.current_frame() == initial_frame + 1

        # Another step
        Action.step_all(0.016)
        assert Action.current_frame() == initial_frame + 2

        # Actions should be paused after step
        assert action._paused

        Action.stop_all()

    def test_frame_counter_independent_of_delta_time(self):
        """Frame counter should be independent of delta_time value."""
        Action._frame_counter = 0
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until
        from actions.conditional import infinite

        action = move_until(sprite, velocity=(5, 0), condition=infinite, tag="test")

        # Update with different delta_time values
        Action.update_all(0.016)  # 60 FPS
        assert Action.current_frame() == 1

        Action.update_all(0.033)  # 30 FPS
        assert Action.current_frame() == 2

        Action.update_all(0.008)  # 120 FPS
        assert Action.current_frame() == 3

        # Frame counter should always increment by 1 per update, regardless of delta_time
        Action.stop_all()

    def test_after_frames_uses_frame_counter_indirectly(self):
        """after_frames conditions should work correctly with frame counter behavior."""
        Action._frame_counter = 0
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        from actions import move_until

        # Create action with frame-based condition
        condition = after_frames(10)
        action = move_until(sprite, velocity=(5, 0), condition=condition, tag="test")

        # Update 5 frames
        for _ in range(5):
            Action.update_all(0.016)
        assert not action.done
        assert Action.current_frame() == 5

        # Pause
        Action.pause_all()

        # Update while paused - condition should not progress
        for _ in range(10):
            Action.update_all(0.016)
        assert not action.done
        assert Action.current_frame() == 5  # Counter didn't increment

        # Resume and complete
        Action.resume_all()
        for _ in range(5):
            Action.update_all(0.016)
        assert action.done
        assert Action.current_frame() == 10

        Action.stop_all()
