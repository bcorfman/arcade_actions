import heapq
import itertools
from collections.abc import Callable

import arcade


class TimeProvider:
    """Interface for time providers."""

    def get_time(self) -> float:
        """Get the current time."""
        raise NotImplementedError


class ArcadeTimeProvider(TimeProvider):
    """Time provider that uses Arcade's global clock."""

    def get_time(self) -> float:
        """Get the current time from Arcade's global clock."""
        if hasattr(arcade, "clock") and hasattr(arcade.clock, "GLOBAL_CLOCK"):
            return arcade.clock.GLOBAL_CLOCK.time
        return 0.0


class GameClock:
    """Central game clock that manages time and pause state for the entire game.

    This class implements a publish/subscribe model where objects can subscribe
    to pause/resume events. When the clock is paused or resumed, all subscribers
    are notified and should update their state accordingly.
    """

    def __init__(self, time_provider: TimeProvider | None = None):
        self._time = 0.0
        self._paused = False
        self._subscribers: set[Callable[[bool], None]] = set()
        self._time_provider = time_provider or ArcadeTimeProvider()
        self._sync_with_arcade = False
        self._paused_time = 0.0  # Time when the clock was paused

    def enable_arcade_sync(self) -> None:
        """Enable synchronization with Arcade's global clock."""
        self._sync_with_arcade = True
        if hasattr(arcade, "clock") and hasattr(arcade.clock, "GLOBAL_CLOCK"):
            self._time = arcade.clock.GLOBAL_CLOCK.time

    def disable_arcade_sync(self) -> None:
        """Disable synchronization with Arcade's global clock."""
        self._sync_with_arcade = False

    def subscribe(self, callback: Callable[[bool], None]) -> None:
        """Subscribe to pause/resume events.

        Args:
            callback: Function that takes a boolean parameter indicating if the game is paused
        """
        self._subscribers.add(callback)
        # Notify new subscriber of current state
        callback(self._paused)

    def unsubscribe(self, callback: Callable[[bool], None]) -> None:
        """Unsubscribe from pause/resume events."""
        self._subscribers.discard(callback)

    @property
    def paused(self) -> bool:
        """Get the current pause state."""
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """Set the pause state and notify all subscribers."""
        if self._paused != value:
            self._paused = value
            if value:  # If pausing, store the current time
                self._paused_time = self._time
            for callback in self._subscribers:
                callback(value)

    def update(self, delta_time: float) -> None:
        """Update the game time if not paused."""
        if not self._paused:
            self._time += delta_time
            # Only sync with Arcade's clock if enabled and in a real game context
            if self._sync_with_arcade and hasattr(arcade, "clock") and hasattr(arcade.clock, "GLOBAL_CLOCK"):
                if abs(self._time - arcade.clock.GLOBAL_CLOCK.time) > 0.001:
                    self._time = arcade.clock.GLOBAL_CLOCK.time

    @property
    def time(self) -> float:
        """Get the current game time."""
        return self._time

    def reset(self) -> None:
        """Reset the game time to 0."""
        self._time = 0.0
        self._paused_time = 0.0

    def __repr__(self) -> str:
        return f"<GameClock time={self._time:.2f} paused={self._paused} subscribers={len(self._subscribers)}>"


class Scheduler:
    """Scheduler that respects the game clock's pause state."""

    def __init__(self, clock: GameClock):
        self.clock = clock
        self._counter = itertools.count()
        self._queue = []
        self._tasks = {}
        self._paused = False
        self._last_update_time = 0.0
        self._paused_time = 0.0
        # Subscribe to clock's pause state after all variables are initialized
        self.clock.subscribe(self._on_pause_state_changed)

    def _on_pause_state_changed(self, paused: bool) -> None:
        """Handle pause state changes from the game clock."""
        self._paused = paused
        if paused:
            self._paused_time = self.clock.time
        else:
            # When resuming, we need to adjust task times by the pause duration
            pause_duration = self.clock.time - self._paused_time
            if pause_duration > 0:
                # Adjust all task times by the pause duration
                new_queue = []
                for execute_at, task_id, func, args, kwargs, repeat, interval in self._queue:
                    new_execute_at = execute_at + pause_duration
                    heapq.heappush(new_queue, (new_execute_at, task_id, func, args, kwargs, repeat, interval))
                    if task_id in self._tasks:
                        self._tasks[task_id] = (new_execute_at, func, args, kwargs)
                self._queue = new_queue
            self._last_update_time = self.clock.time
            self.update()

    def schedule(self, delay: float, func: Callable, *args, **kwargs) -> int:
        """Schedule a one-time task."""
        execute_at = self.clock.time + delay
        task_id = next(self._counter)
        heapq.heappush(self._queue, (execute_at, task_id, func, args, kwargs, False, None))
        self._tasks[task_id] = (execute_at, func, args, kwargs)
        return task_id

    def schedule_interval(self, interval: float, func: Callable, *args, **kwargs) -> int:
        """Schedule a repeating task."""
        execute_at = self.clock.time + interval
        task_id = next(self._counter)
        heapq.heappush(self._queue, (execute_at, task_id, func, args, kwargs, True, interval))
        self._tasks[task_id] = (execute_at, func, args, kwargs)
        return task_id

    def cancel(self, task_id: int) -> None:
        """Cancel a scheduled task."""
        self._tasks.pop(task_id, None)

    def update(self) -> None:
        """Update scheduled tasks if not paused."""
        if self._paused:
            return

        now = self.clock.time
        # Process all tasks that should have executed by now
        while self._queue and self._queue[0][0] <= now:
            execute_at, task_id, func, args, kwargs, repeat, interval = heapq.heappop(self._queue)
            if task_id not in self._tasks:
                continue  # Task was cancelled
            # Execute the task
            func(*args, **kwargs)
            if repeat:
                # For repeating tasks, schedule the next execution
                next_time = now + interval
                heapq.heappush(
                    self._queue,
                    (next_time, task_id, func, args, kwargs, True, interval),
                )
                self._tasks[task_id] = (next_time, func, args, kwargs)
            else:
                # For one-time tasks, remove from tracking
                self._tasks.pop(task_id, None)
        self._last_update_time = now

    def schedule_arcade(self, delay: float, func: Callable, *args, **kwargs) -> None:
        """Schedule a task using Arcade's scheduling system.

        This is useful for tasks that don't need to respect the pause state,
        like UI updates or non-game-critical operations.

        Args:
            delay: Time in seconds before the task executes
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        arcade.schedule(func, delay, *args, **kwargs)

    def schedule_arcade_interval(self, interval: float, func: Callable, *args, **kwargs) -> None:
        """Schedule a repeating task using Arcade's scheduling system.

        This is useful for tasks that don't need to respect the pause state,
        like UI updates or non-game-critical operations.

        Args:
            interval: Time in seconds between executions
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        arcade.schedule(func, interval, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<Scheduler tasks={len(self._tasks)} paused={self._paused}>"
