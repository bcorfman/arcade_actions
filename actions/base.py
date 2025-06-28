"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import arcade

if TYPE_CHECKING:
    from .composite import Sequence, Spawn


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

    # Action management - can be either old-style single action or new-style slots
    _action: "Action | None"  # Backward compatibility
    _actions: dict[str, "Action | None"]  # New named slots system

    def update(self, delta_time: float) -> None: ...


@runtime_checkable
class GroupTarget(Protocol):
    """Protocol for group targets that can have group actions."""

    _group_actions: list["Action"]

    def __iter__(self): ...
    def __len__(self) -> int: ...


class Action:
    """Base class for all actions.

    Actions modify sprite properties over time using Arcade's velocity-based
    movement system (change_x, change_y, change_angle, etc.) rather than
    directly modifying position/angle/scale.

    Actions can be applied to individual sprites or sprite lists.

    This class can be instantiated directly to create no-op actions that participate
    in the action lifecycle but perform no behavior. This is useful for testing,
    placeholders, and debugging.

    For custom actions, inherit from this class and override the appropriate methods:
        - start(): Called when the action begins (optional, defaults to no-op)
        - update(): Called each frame (optional, base implementation handles timing)
        - clone(): Must be overridden to support action copying

    Example usage:
        sprite = ActionSprite(...)
        action = MoveBy((100, 0), duration=1.0)
        sprite.do(action)  # This is the correct way to use actions
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

    def start(self) -> None:
        """Called when the action begins.

        Default implementation does nothing - suitable for no-op actions and
        actions that don't need initialization. Override this method to add
        custom setup behavior for your action.
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

    def clone(self) -> "Action":
        """Create a copy of this action for independent use.

        The base Action class provides a default implementation that creates a new
        Action instance with the same duration. Action subclasses should override
        this method to properly copy their specific configuration.

        Returns:
            A new Action instance with the same configuration as this one

        Raises:
            NotImplementedError: If a subclass doesn't override this method and
            requires specific cloning behavior
        """
        if self.__class__ is Action:
            # Base Action class can be cloned directly
            cloned = Action()
            cloned.duration = self.duration
            return cloned
        else:
            # Subclasses should implement their own cloning
            raise NotImplementedError(
                f"Action subclass {self.__class__.__name__} must override clone() method. "
                f"This ensures proper action copying without fragile runtime type checks."
            )

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

    def clone(self) -> "IntervalAction":
        """Create a copy of this IntervalAction."""
        if self.__class__ is IntervalAction:
            return IntervalAction(self.duration)
        else:
            # Subclasses should implement their own cloning
            return super().clone()

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

    def clone(self) -> "InstantAction":
        """Create a copy of this InstantAction."""
        if self.__class__ is InstantAction:
            return InstantAction()
        else:
            # Subclasses should implement their own cloning
            return super().clone()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class ActionSprite(arcade.Sprite):
    """A sprite that supports time-based Actions like MoveBy, RotateBy, etc.

    This class extends arcade.Sprite to add action management capabilities.
    It supports both single actions (for backward compatibility) and multiple
    named action slots for complex orthogonal behaviors.

    Basic usage (single action):
        sprite.do(action1)
        sprite.do(action2)  # Replaces action1

    Named slots usage (multiple concurrent actions):
        sprite.do(movement_action, slot="movement")
        sprite.do(damage_flash, slot="effects")
        sprite.clear_action(slot="effects")  # Stop just the flash
        sprite.clear_actions()  # Stop everything

    For composite behaviors without slots, use Spawn or Sequence:
        # Run two actions in parallel
        sprite.do(action1 | action2)
        # Run actions in sequence
        sprite.do(action1 + action2)

    Scale Behavior:
        ActionSprite provides enhanced scale handling that maintains compatibility
        with Arcade's rendering pipeline:

        - Supports both uniform scaling: sprite.scale = 2.0
        - Supports non-uniform scaling: sprite.scale = (2.0, 1.5)
        - Automatically syncs with Arcade's native scale for rendering compatibility
        - Uses duck typing (no runtime type checking) for input handling
        - Maintains separate _scale_x/_scale_y values internally
        - Updates width/height attributes automatically

        The scale property returns a _ScaleVector with .x/.y access for test compatibility.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Named action slots - "default" slot maintains backward compatibility
        self._actions: dict[str, Action | None] = {"default": None}
        self._is_paused: bool = False
        self._is_cleaning_up: bool = False

        # Ensure change_angle exists with a default value (Arcade defines it, but we
        # set it explicitly to avoid runtime attribute checks.)
        self.change_angle = 0.0

        # Internal scale representation (separate x / y) to support tests requiring
        # attribute access like `sprite.scale.x` and `sprite.scale.y` while
        # avoiding runtime attribute checks elsewhere.
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

        # Ensure Arcade's scale stays in sync for rendering pipeline
        self._sync_arcade_scale()

    @property
    def _action(self) -> Action | None:
        """Backward compatibility property for the default action slot."""
        return self._actions["default"]

    @_action.setter
    def _action(self, value: Action | None) -> None:
        """Backward compatibility setter for the default action slot."""
        self._actions["default"] = value

    def do(self, action: Action, slot: str = "default") -> Action:
        """Start an action on this sprite.

        If another action is currently running in the specified slot, it will be
        stopped before starting the new action.

        Args:
            action: The action to start
            slot: The named slot to assign the action to (default: "default")

        Returns:
            The started action instance
        """
        # Stop any existing action in this slot
        if self._actions.get(slot):
            self._actions[slot].stop()

        action.target = self
        action.start()
        self._actions[slot] = action
        # Set initial pause state
        if self._is_paused:
            action.pause()
        return action

    def update(self, delta_time: float = 1 / 60):
        """Update all active actions.

        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if self._is_paused:
            return

        # Update all active actions and collect completed ones
        completed_slots = []
        for slot, action in self._actions.items():
            if action is not None:
                action.update(delta_time)
                if action.done:
                    action.stop()
                    completed_slots.append(slot)

        # Clear completed actions
        for slot in completed_slots:
            self._actions[slot] = None

    def clear_action(self, slot: str = "default") -> None:
        """Stop and clear the action in the specified slot.

        Args:
            slot: The named slot to clear (default: "default")
        """
        if self._actions.get(slot):
            self._actions[slot].stop()
            self._actions[slot] = None

    def clear_actions(self):
        """Stop and clear all actions in all slots."""
        for slot in list(self._actions.keys()):
            self.clear_action(slot)

    def has_active_actions(self) -> bool:
        """Return True if any action is currently running."""
        return any(action is not None and not action.done for action in self._actions.values())

    def pause(self):
        """Pause all active actions."""
        self._is_paused = True
        for action in self._actions.values():
            if action:
                action.pause()

    def resume(self):
        """Resume all active actions."""
        self._is_paused = False
        for action in self._actions.values():
            if action:
                action.resume()

    def is_busy(self) -> bool:
        """Return True if any action is currently running and not done."""
        return any(action is not None and not action.done for action in self._actions.values())

    def cleanup(self):
        pass

    def __del__(self):
        """Ensure cleanup is called when the sprite is garbage collected."""
        self.cleanup()

    # ------------------------------------------------------------------
    # Scale helpers
    # ------------------------------------------------------------------

    def _sync_arcade_scale(self) -> None:
        """Keep Arcade's native scale in sync for rendering compatibility."""
        # Set Arcade's scale to match our scale values for rendering pipeline compatibility
        # Arcade expects a tuple (scale_x, scale_y) or float for uniform scaling
        arcade.Sprite.scale.fset(self, (self._scale_x, self._scale_y))

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
        """Return scale as consistent 2-component vector."""
        return ActionSprite._ScaleVector((self._scale_x, self._scale_y))

    @scale.setter  # type: ignore[override]
    def scale(self, value) -> None:  # type: ignore[override]
        """Set scale - accepts float for uniform or tuple for non-uniform.

        Uses duck typing to determine input type - no runtime type checking.
        Maintains sync with Arcade's native scale for rendering compatibility.
        """
        # No isinstance checking - use duck typing
        try:
            # Try tuple unpacking first
            x, y = value
            self._scale_x, self._scale_y = float(x), float(y)
        except (TypeError, ValueError):
            # Single value - uniform scaling
            uniform = float(value)
            self._scale_x = self._scale_y = uniform

        # Update width/height attributes so test assertions remain valid. The
        # Arcade `Sprite` class exposes `width`/`height` as plain attributes, so
        # updating them directly is safe and efficient.
        if self.texture:
            self.width = self.texture.width * self._scale_x
            self.height = self.texture.height * self._scale_y

        # Keep Arcade's scale in sync for rendering pipeline
        self._sync_arcade_scale()
