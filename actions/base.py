"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import arcade

if TYPE_CHECKING:
    from .composite import Sequence, Spawn


class PhysicsProperties:
    """Standard physics properties for all sprites."""

    def __init__(self):
        self.acceleration: tuple[float, float] = (0.0, 0.0)
        self.gravity: float = 0.0
        self.speed: float = 0.0
        self.max_forward_speed: float | None = None
        self.max_reverse_speed: float | None = None


class ActionTarget(Protocol):
    """Protocol defining the interface all action targets must implement."""

    # Position and movement
    position: tuple[float, float]
    center_x: float
    center_y: float
    change_x: float
    change_y: float

    # Rotation
    angle: float
    change_angle: float

    # Physics properties (guaranteed to exist)
    physics: PhysicsProperties

    # Action management
    _action: "Action | None"

    def update(self, delta_time: float) -> None: ...


@runtime_checkable
class GroupTarget(Protocol):
    """Protocol for group targets that can have group actions."""

    _group_actions: list["Action"]

    def __iter__(self): ...
    def __len__(self) -> int: ...


class Action(ABC):
    """Base class for all actions.

    Actions modify sprite properties over time using Arcade's velocity-based
    movement system (change_x, change_y, change_angle, etc.) rather than
    directly modifying position/angle/scale.

    Actions can be applied to individual sprites or sprite lists.

    Important: Actions are not meant to be used directly. They must be applied to
    an ActionSprite using the sprite's do() method. For example:
        sprite = ActionSprite(...)
        action = MoveBy((100, 0), duration=1.0)
        sprite.do(action)  # This is the correct way to use actions

    Attempting to use actions directly (e.g. calling start() or update() manually)
    will result in errors since the action requires a valid target sprite.
    """

    def __init__(self):
        self.target: ActionTarget | GroupTarget | None = None
        self._elapsed: float = 0.0
        self.done: bool = False  # Public completion state
        # Default duration for all actions (may be overridden by subclasses)
        self.duration: float = 0.0
        self._paused: bool = False
        self._on_complete = None
        self._on_complete_args = ()
        self._on_complete_kwargs = {}
        self._on_complete_called = False

    def on_complete(self, func, *args, **kwargs):
        """Register a callback to be triggered when the action completes."""
        self._on_complete = func
        self._on_complete_args = args
        self._on_complete_kwargs = kwargs
        return self

    def when_done(self, func, *args, **kwargs):
        """Alias for on_complete(), more readable for game scripting."""
        return self.on_complete(func, *args, **kwargs)

    def _check_complete(self):
        if self.done and self._on_complete and not self._on_complete_called:
            self._on_complete_called = True
            self._on_complete(*self._on_complete_args, **self._on_complete_kwargs)

    @abstractmethod
    def start(self) -> None:
        """Called when the action begins.

        Override this to set up initial state and velocities.
        """
        pass

    def update(self, delta_time: float) -> None:
        """Called each frame to update the action.

        This base implementation handles:
        - Pause state checking
        - Elapsed time tracking
        - Completion callback triggering

        Override this method to add custom update behavior, but be sure to call
        super().update(delta_time) to maintain the base functionality.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if not self._paused:
            self._elapsed += delta_time
            self._check_complete()

    def stop(self) -> None:
        """Called when the action ends.

        This base implementation handles:
        - Target cleanup
        - Completion callback triggering

        Override this method to add custom cleanup behavior, but be sure to call
        super().stop() to maintain the base functionality.
        """
        self.target = None
        self._check_complete()

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self._elapsed = 0.0
        self.done = False
        self._paused = False
        self._on_complete_called = False

    def pause(self) -> None:
        """Pause the action."""
        self._paused = True

    def resume(self) -> None:
        """Resume the action."""
        self._paused = False

    def __add__(self, other: "Action") -> "Sequence":
        """Sequence operator - concatenates actions.

        action1 + action2 -> action_result
        where action_result performs as:
        first do all that action1 would do; then
        perform all that action2 would do
        """
        from .composite import sequence

        return sequence(self, other)

    def __mul__(self, other: int) -> "Loop":
        """Repeat operator - repeats the action n times.

        action * n -> action_result
        where action result performs as:
        repeat n times the changes that action would do
        """
        if type(other) is not int:
            raise TypeError("Can only multiply actions by ints")
        if other <= 1:
            return self
        from .composite import loop

        return loop(self, other)

    def __or__(self, other: "Action") -> "Spawn":
        """Spawn operator - runs two actions in parallel.

        action1 | action2 -> action_result
        """
        from .composite import spawn

        return spawn(self, other)

    def __reversed__(self) -> "Action":
        """Returns a reversed version of this action.

        Not all actions can be reversed. Override this method
        to implement reversal.
        """
        raise NotImplementedError(f"Action {self.__class__.__name__} cannot be reversed")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}()"

    # ------------------------------------------------------------------
    # Polymorphic movement hooks (implemented by movement-capable actions).
    # ------------------------------------------------------------------

    def reverse_movement(self, axis: str) -> None:  # noqa: D401 – simple verb form
        """Reverse any internal movement state along *axis*.

        The default implementation is a no-op so that any action may receive
        the call without requiring fragile ``isinstance`` checks upstream.
        Subclasses that apply deltas over time should override this.
        """

    def extract_movement_direction(self, collector):  # noqa: D401
        """Report movement deltas to *collector*.

        ``collector`` is any callable accepting ``(dx, dy)``.  Overriding
        implementations should call ``collector`` zero or more times with the
        deltas they control.
        """

    # ------------------------------------------------------------------
    # Capability defaults to avoid fragile hasattr/isinstance checks
    # ------------------------------------------------------------------

    def get_movement_delta(self) -> tuple[float, float]:  # noqa: D401 – simple helper
        """Return this action's movement delta.

        Base implementation returns ``(0.0, 0.0)`` so callers can rely on the
        method existing without runtime inspection.
        """
        return 0.0, 0.0

    def get_movement_actions(self) -> list["Action"]:  # noqa: D401 – simple helper
        """Return any nested movement actions (empty by default)."""
        return []

    def get_wrapped_action(self) -> "Action":  # noqa: D401 – simple helper
        """Return the wrapped action for decorator-style wrappers (self by default)."""
        return self

    def adjust_for_position_delta(self, position_delta: tuple[float, float]) -> None:  # noqa: D401
        """Hook for actions to update internal positions when sprite wraps.

        Default implementation is a no-op so callers can invoke unconditionally
        without runtime type checks.
        """
        # Intentionally no behaviour in base class.
        return


class IntervalAction(Action):
    """Base class for actions that have a fixed duration."""

    def __init__(self, duration: float):
        super().__init__()
        self.duration = duration

    def update(self, delta_time: float) -> None:
        """Update the action and check for completion."""
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.done = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(duration={self.duration})"


class InstantAction(Action):
    """Base class for actions that happen instantly."""

    def __init__(self):
        super().__init__()
        self.duration = 0.0

    def update(self, delta_time: float) -> None:
        """Instant actions complete immediately."""
        super().update(delta_time)
        self.done = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class ActionSprite(arcade.Sprite):
    """A sprite that supports time-based Actions like MoveBy, RotateBy, etc.

    This class extends arcade.Sprite to add action management capabilities.
    It allows sprites to have a single action applied to them and handles the
    updating and cleanup of that action automatically.

    Note: This class is designed to manage only one action at a time. To achieve
    multiple behaviors simultaneously, use composite actions like Spawn or Sequence.
    For example:
        # Run two actions in parallel
        sprite.do(action1 | action2)
        # Run actions in sequence
        sprite.do(action1 + action2)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._action: Action | None = None
        self._is_paused: bool = False
        self._is_cleaning_up: bool = False

        # Initialize physics properties
        self.physics = PhysicsProperties()

        # Ensure change_angle exists with a default value (Arcade defines it, but we
        # set it explicitly to avoid runtime attribute checks.)
        self.change_angle = 0.0

        # Internal scale representation (separate x / y) to support tests requiring
        # attribute access like `sprite.scale.x` and `sprite.scale.y` while
        # avoiding runtime attribute checks elsewhere.
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

    def do(self, action: Action) -> Action:
        """Start an action on this sprite.

        If another action is currently running, it will be stopped before
        starting the new action.

        Args:
            action: The action to start

        Returns:
            The started action instance
        """
        # Stop any existing action
        if self._action:
            self._action.stop()

        action.target = self
        action.start()
        self._action = action
        # Set initial pause state
        if self._is_paused:
            action.pause()
        return action

    def update(self, delta_time: float = 1 / 60):
        """Update the current action.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if self._is_paused or not self._action:
            return

        self._action.update(delta_time)
        if self._action.done:
            self._action.stop()
            self._action = None

    def clear_actions(self):
        """Cancel the current action if any."""
        if self._action:
            self._action.stop()
            self._action = None

    def has_active_actions(self) -> bool:
        """Return True if an action is currently running."""
        return self._action is not None and not self._action.done

    def pause(self):
        """Pause the current action."""
        self._is_paused = True
        if self._action:
            self._action.pause()

    def resume(self):
        """Resume the current action."""
        self._is_paused = False
        if self._action:
            self._action.resume()

    def is_busy(self) -> bool:
        """Return True if an action is currently running and not done."""
        return self._action is not None and not self._action.done

    def cleanup(self):
        pass

    def __del__(self):
        """Ensure cleanup is called when the sprite is garbage collected."""
        self.cleanup()

    # ------------------------------------------------------------------
    # Scale helpers
    # ------------------------------------------------------------------

    class _ScaleVector(tuple):
        """Lightweight 2-tuple with `.x` / `.y` attribute access to satisfy tests."""

        __slots__ = ()

        @property
        def x(self) -> float:  # type: ignore[override]
            return self[0]

        @property
        def y(self) -> float:  # type: ignore[override]
            return self[1]

    @property
    def scale(self) -> "ActionSprite._ScaleVector":  # type: ignore[name-defined]
        """Return the current scale as a 2-component vector with `.x` / `.y`."""
        return ActionSprite._ScaleVector((self._scale_x, self._scale_y))

    @scale.setter  # type: ignore[override]
    def scale(self, value):  # type: ignore[override]
        """Set uniform or non-uniform scale.

        Accepts either a float/int for uniform scaling or a 2-tuple for
        independent x / y scaling.
        """
        if type(value) is tuple:
            self._scale_x, self._scale_y = float(value[0]), float(value[1])
        else:
            uniform = float(value)
            self._scale_x = self._scale_y = uniform

        # Update width/height attributes so test assertions remain valid. The
        # Arcade `Sprite` class exposes `width`/`height` as plain attributes, so
        # updating them directly is safe and efficient.
        if self.texture:
            self.width = self.texture.width * self._scale_x
            self.height = self.texture.height * self._scale_y
