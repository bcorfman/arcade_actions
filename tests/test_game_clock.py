"""Test suite for game_clock.py - Game clock and scheduler functionality."""

from unittest.mock import Mock

import pytest

from actions.game_clock import GameClock, Scheduler, TimeProvider


class MockTimeProvider(TimeProvider):
    """Mock time provider for testing."""

    def __init__(self, initial_time: float = 0.0):
        self._time = initial_time

    def get_time(self) -> float:
        return self._time

    def set_time(self, time: float) -> None:
        self._time = time


@pytest.fixture
def time_provider():
    return MockTimeProvider()


@pytest.fixture
def clock(time_provider):
    return GameClock(time_provider)


@pytest.fixture
def scheduler(clock):
    return Scheduler(clock)


class TestGameClock:
    """Test suite for GameClock class."""

    def test_initialization(self, clock):
        """Test clock initialization."""
        assert clock.time == 0.0
        assert not clock.paused
        assert len(clock._subscribers) == 0

    def test_time_tracking(self, clock):
        """Test time tracking functionality."""
        # Update time
        clock.update(0.5)
        assert clock.time == 0.5

        # Update again
        clock.update(0.3)
        assert clock.time == 0.8

    def test_pause_resume(self, clock):
        """Test pause/resume functionality."""
        # Start with some time
        clock.update(0.5)
        initial_time = clock.time

        # Pause
        clock.paused = True
        assert clock.paused
        clock.update(0.3)
        assert clock.time == initial_time  # Time should not change

        # Resume
        clock.paused = False
        assert not clock.paused
        clock.update(0.3)
        assert clock.time == initial_time + 0.3

    def test_subscriber_management(self, clock):
        """Test subscriber management."""
        # Test subscribe
        callback = Mock()
        clock.subscribe(callback)
        assert callback in clock._subscribers
        callback.assert_called_once_with(False)  # Should be notified of initial state

        # Test unsubscribe
        clock.unsubscribe(callback)
        assert callback not in clock._subscribers

    def test_subscriber_notification(self, clock):
        """Test subscriber notification on pause state changes."""
        callback = Mock()
        clock.subscribe(callback)

        # Test pause notification
        clock.paused = True
        callback.assert_called_with(True)

        # Test resume notification
        clock.paused = False
        callback.assert_called_with(False)

    def test_reset(self, clock):
        """Test clock reset functionality."""
        # Add some time
        clock.update(0.5)
        assert clock.time == 0.5

        # Reset
        clock.reset()
        assert clock.time == 0.0

    def test_arcade_sync(self, clock):
        """Test Arcade clock synchronization."""
        # Enable sync
        clock.enable_arcade_sync()
        assert clock._sync_with_arcade

        # Disable sync
        clock.disable_arcade_sync()
        assert not clock._sync_with_arcade


class TestScheduler:
    """Test suite for Scheduler class."""

    def test_initialization(self, scheduler):
        """Test scheduler initialization."""
        assert scheduler.clock is not None
        assert len(scheduler._tasks) == 0
        assert len(scheduler._queue) == 0
        assert not scheduler._paused

    def test_one_time_task(self, scheduler):
        """Test one-time task scheduling and execution."""
        task_called = False

        def task():
            nonlocal task_called
            task_called = True

        # Schedule task
        task_id = scheduler.schedule(0.5, task)
        assert task_id in scheduler._tasks
        assert len(scheduler._queue) == 1

        # Update before task time
        scheduler.update()
        assert not task_called

        # Update clock to task time
        scheduler.clock.update(0.5)
        scheduler.update()
        assert task_called

    def test_interval_task(self, scheduler):
        """Test interval task scheduling and execution."""
        call_count = 0

        def task():
            nonlocal call_count
            call_count += 1

        # Schedule repeating task
        task_id = scheduler.schedule_interval(0.5, task)
        assert task_id in scheduler._tasks
        assert len(scheduler._queue) == 1

        # First execution
        scheduler.clock.update(0.5)
        scheduler.update()
        assert call_count == 1

        # Second execution
        scheduler.clock.update(0.5)
        scheduler.update()
        assert call_count == 2

    def test_task_cancellation(self, scheduler):
        """Test task cancellation."""
        task_called = False

        def task():
            nonlocal task_called
            task_called = True

        # Schedule and cancel task
        task_id = scheduler.schedule(0.5, task)
        scheduler.cancel(task_id)
        assert task_id not in scheduler._tasks

        # Task should not execute
        scheduler.clock.update(0.5)
        scheduler.update()
        assert not task_called

    def test_pause_handling(self, scheduler):
        """Test pause state handling."""
        task_called = False

        def task():
            nonlocal task_called
            task_called = True

        # Schedule task
        scheduler.schedule(0.5, task)

        # Pause before task time
        scheduler.clock.paused = True
        scheduler.clock.update(0.5)
        scheduler.update()
        assert not task_called

        # Resume and execute
        scheduler.clock.paused = False
        scheduler.update()
        assert task_called

    def test_task_cleanup(self, scheduler):
        """Test task cleanup after execution."""

        def task():
            pass

        # Schedule one-time task
        task_id = scheduler.schedule(0.5, task)
        assert task_id in scheduler._tasks

        # Execute task
        scheduler.clock.update(0.5)
        scheduler.update()
        assert task_id not in scheduler._tasks

    def test_arcade_scheduling(self, scheduler):
        """Test Arcade scheduling integration."""

        def task():
            pass

        # Schedule using Arcade's system
        scheduler.schedule_arcade(0.5, task)
        # Note: We can't test actual execution since it depends on Arcade's scheduling system
        # In a real game, this would be handled by Arcade's event loop

    def test_arcade_interval_scheduling(self, scheduler):
        """Test Arcade interval scheduling integration."""

        def task():
            pass

        # Schedule using Arcade's system
        scheduler.schedule_arcade_interval(0.5, task)
        # Note: We can't test actual execution since it depends on Arcade's scheduling system
        # In a real game, this would be handled by Arcade's event loop
