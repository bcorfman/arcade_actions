import heapq
import itertools
from typing import Callable, List, Optional, Dict, Any, Set


class GameClock:
    """Central game clock that manages time and pause state for the entire game.

    This class implements a publish/subscribe model where objects can subscribe
    to pause/resume events. When the clock is paused or resumed, all subscribers
    are notified and should update their state accordingly.
    """

    def __init__(self):
        self._time = 0.0
        self._paused = False
        self._subscribers: Set[Callable[[bool], None]] = set()

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
            for callback in self._subscribers:
                callback(value)

    def update(self, delta_time: float) -> None:
        """Update the game time if not paused."""
        if not self._paused:
            self._time += delta_time

    def time(self) -> float:
        """Get the current game time."""
        return self._time

    def reset(self) -> None:
        """Reset the game time to 0."""
        self._time = 0.0

    def __repr__(self) -> str:
        return f"<GameClock time={self._time:.2f} paused={self._paused} subscribers={len(self._subscribers)}>"


class Scheduler:
    """Scheduler that respects the game clock's pause state."""

    def __init__(self, clock: GameClock):
        self.clock = clock
        self._counter = itertools.count()
        self._queue = []
        self._tasks = {}
        # Subscribe to clock's pause state
        self.clock.subscribe(self._on_pause_state_changed)
        self._paused = False

    def _on_pause_state_changed(self, paused: bool) -> None:
        """Handle pause state changes from the game clock."""
        self._paused = paused

    def schedule(self, delay: float, func: Callable, *args, **kwargs) -> int:
        """Schedule a one-time task."""
        execute_at = self.clock.time() + delay
        task_id = next(self._counter)
        heapq.heappush(
            self._queue, (execute_at, task_id, func, args, kwargs, False, None)
        )
        self._tasks[task_id] = (execute_at, func, args, kwargs)
        return task_id

    def schedule_interval(
        self, interval: float, func: Callable, *args, **kwargs
    ) -> int:
        """Schedule a repeating task."""
        execute_at = self.clock.time() + interval
        task_id = next(self._counter)
        heapq.heappush(
            self._queue, (execute_at, task_id, func, args, kwargs, True, interval)
        )
        self._tasks[task_id] = (execute_at, func, args, kwargs)
        return task_id

    def cancel(self, task_id: int) -> None:
        """Cancel a scheduled task."""
        self._tasks.pop(task_id, None)

    def update(self) -> None:
        """Update scheduled tasks if not paused."""
        if self._paused:
            return

        now = self.clock.time()
        while self._queue and self._queue[0][0] <= now:
            execute_at, task_id, func, args, kwargs, repeat, interval = heapq.heappop(
                self._queue
            )
            if task_id not in self._tasks:
                continue  # Task was cancelled
            func(*args, **kwargs)
            if repeat:
                next_time = now + interval
                heapq.heappush(
                    self._queue,
                    (next_time, task_id, func, args, kwargs, True, interval),
                )
                self._tasks[task_id] = (next_time, func, args, kwargs)
            else:
                self._tasks.pop(task_id, None)

    def __repr__(self) -> str:
        return f"<Scheduler tasks={len(self._tasks)} paused={self._paused}>"
