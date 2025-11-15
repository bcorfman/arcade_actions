"""Frame-based timing primitives for ArcadeActions.

This module provides frame-driven timing helpers that replace wall-clock timing.
All timing in ArcadeActions is based on frame counts from Action.update_all() calls,
ensuring deterministic behavior under varying performance conditions and enabling
proper pause/resume/step debugging functionality.

Key Principles:
- Frame counts never increment when actions are paused
- Timing is deterministic regardless of delta_time variations
- Debugger pause (F6) and step (F7) work correctly
- No wall-clock dependencies (no time.time() calls)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def after_frames(frame_count: int) -> Callable[[], bool]:
    """Create a condition that returns True after a specified number of frames.

    This is the primary timing primitive for frame-based actions. It counts
    frames from when the condition is first called, returning False until
    the specified frame count is reached.

    Args:
        frame_count: Number of frames to wait before returning True.
                    Zero or negative values return True immediately.

    Returns:
        A condition function that tracks frames and returns True when complete.

    Examples:
        # Move for 60 frames (1 second at 60 FPS)
        move_until(sprite, velocity=(5, 0), condition=after_frames(60))

        # Delay for 30 frames
        DelayUntil(condition=after_frames(30))

        # Blink for 120 frames
        blink_until(sprite, frames_until_change=15, condition=after_frames(120))

    Frame Timing:
        - Frames are counted by calls to the condition function
        - Each Action.update_all() call advances the frame counter
        - When paused, frame counter doesn't advance, so conditions don't progress
        - This ensures deterministic behavior and proper pause/step debugging
    """
    if frame_count <= 0:
        # Zero or negative frames: return True immediately
        return lambda: True

    frames_elapsed = 0

    def condition() -> bool:
        nonlocal frames_elapsed
        frames_elapsed += 1
        return frames_elapsed >= frame_count

    # Mark this as a frame-based condition for introspection
    condition._is_frame_condition = True  # type: ignore
    condition._frame_count = frame_count  # type: ignore

    return condition


def every_frames(interval: int, callback: Callable[..., None]) -> Callable[[], None]:
    """Create a callback wrapper that fires at regular frame intervals.

    This wraps a callback function to execute it only every N frames, rather than
    every frame. Useful for performance optimization and periodic updates.

    Args:
        interval: Number of frames between callback executions.
                 1 means every frame, 2 means every other frame, etc.
        callback: Function to call at intervals. Can accept 0 or 1 parameters.

    Returns:
        A wrapper function that calls the callback at the specified interval.

    Examples:
        # Update AI every 10 frames instead of every frame
        def update_ai():
            enemy.think()

        ai_ticker = every_frames(10, update_ai)
        callback_until(enemy, callback=ai_ticker, condition=infinite)

        # Spawn bullets every 60 frames (1 second at 60 FPS)
        def spawn_bullet():
            bullets.append(create_bullet())

        spawn_ticker = every_frames(60, spawn_bullet)
        callback_until(spawner, callback=spawn_ticker, condition=after_frames(600))

    Frame Timing:
        - First call executes immediately (frame 0)
        - Subsequent calls execute every 'interval' frames
        - When paused, the ticker doesn't advance
        - Deterministic regardless of delta_time variations
    """
    if interval < 1:
        interval = 1

    frames_since_last_call = interval  # Start at interval to fire immediately

    def ticker(*args, **kwargs) -> None:
        nonlocal frames_since_last_call
        frames_since_last_call += 1

        if frames_since_last_call >= interval:
            frames_since_last_call = 0
            # Try calling with args first, fall back to no args
            try:
                callback(*args, **kwargs)
            except TypeError:
                # Callback doesn't accept parameters
                callback()

    return ticker


def within_frames(start_frame: int, end_frame: int) -> Callable[[], bool]:
    """Create a condition that returns True only within a specific frame window.

    This is useful for time-limited effects or behaviors that should only occur
    during a specific period.

    Args:
        start_frame: First frame where condition returns True (inclusive).
        end_frame: Last frame where condition returns True (exclusive).

    Returns:
        A condition function that returns True only within the specified window.

    Examples:
        # Power-up active only during frames 60-120
        def power_up_active():
            return within_frames(60, 120)()

        # Invulnerability window after respawn
        invuln_condition = within_frames(0, 180)  # 3 seconds at 60 FPS
        blink_until(player, frames_until_change=5, condition=invuln_condition)

    Frame Timing:
        - Frame counting starts from first call (frame 0)
        - Returns False before start_frame
        - Returns True from start_frame to end_frame-1
        - Returns False from end_frame onward
        - When paused, frame doesn't advance, so window doesn't progress
    """
    current_frame = 0

    def condition() -> bool:
        nonlocal current_frame
        result = start_frame <= current_frame < end_frame
        current_frame += 1
        return result

    # Mark this as a frame-based condition
    condition._is_frame_condition = True  # type: ignore
    condition._frame_window = (start_frame, end_frame)  # type: ignore

    return condition


def frames_to_seconds(frame_count: int, fps: float = 60.0) -> float:
    """Convert frame count to approximate seconds (for display/logging only).

    This is a utility function for converting frame-based timing to human-readable
    seconds. It should ONLY be used for display purposes, never for actual timing.

    Args:
        frame_count: Number of frames.
        fps: Target frames per second (default: 60.0).

    Returns:
        Approximate duration in seconds.

    Warning:
        Do NOT use this for actual timing logic! Frame-based timing is deterministic,
        but converting to seconds and back introduces variability. This is only for
        displaying timing information to users or in logs.

    Examples:
        # Display how long an action will take
        frames = 180
        print(f"Action will take {frames_to_seconds(frames)} seconds")
        # Output: "Action will take 3.0 seconds"
    """
    return frame_count / fps


def seconds_to_frames(seconds: float, fps: float = 60.0) -> int:
    """Convert seconds to approximate frame count (for convenience only).

    This is a convenience function for developers who think in seconds but want
    to use frame-based timing. The conversion is approximate and assumes constant
    frame rate.

    Args:
        seconds: Duration in seconds.
        fps: Target frames per second (default: 60.0).

    Returns:
        Approximate frame count (rounded to nearest integer).

    Examples:
        # "I want this to last about 2 seconds"
        condition = after_frames(seconds_to_frames(2.0))

        # "Blink every quarter second"
        blink_until(sprite, frames_until_change=seconds_to_frames(0.25), ...)

    Note:
        This is a convenience helper for initial development. The actual timing
        will be frame-based and deterministic, regardless of actual frame rate.
        If you want exactly 2 seconds of wall-clock time, you're using the wrong
        approach - frame-based timing is about deterministic behavior, not wall-clock
        accuracy.
    """
    return round(seconds * fps)


# Convenience constants for common frame counts at 60 FPS
FRAMES_PER_SECOND = 60
FRAMES_PER_HALF_SECOND = 30
FRAMES_PER_QUARTER_SECOND = 15
FRAMES_PER_TWO_SECONDS = 120
FRAMES_PER_FIVE_SECONDS = 300


def infinite() -> Callable[[], bool]:
    """Create a condition that never returns True.

    Use this for actions that should run indefinitely until explicitly stopped.
    This is re-exported here for convenience alongside frame-based conditions.

    Returns:
        A condition function that always returns False.

    Examples:
        # Move forever
        move_until(sprite, velocity=(5, 0), condition=infinite)

        # Rotate continuously
        rotate_until(sprite, angular_velocity=90, condition=infinite)

    Note:
        This is the same as actions.conditional.infinite() but provided here
        for convenience when working with frame-based timing.
    """
    return lambda: False
