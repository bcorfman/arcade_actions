"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

try:
    from typing import Protocol
except ImportError:
    from typing import Protocol

import arcade

if TYPE_CHECKING:
    import arcade

    SpriteTarget = arcade.Sprite | arcade.SpriteList


_T = TypeVar("_T", bound="Action")


def _debug_log_action(action, level: int, message: str) -> None:
    """Centralized debug logger with level and per-Action filtering."""
    try:
        action_name = action if isinstance(action, str) else type(action).__name__
    except Exception:
        action_name = "Action"

    # Level gate
    if Action.debug_level < level:
        return

    # Filter gate
    if not Action.debug_all:
        include = Action.debug_include_classes
        if not include or action_name not in include:
            return

    print(f"[AA L{level} {action_name}] {message}")


class VelocityControllable(Protocol):
    """Protocol for actions that support velocity control."""

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Set the current velocity for this action."""
        ...


class Action(ABC, Generic[_T]):
    """
    Base class for all actions.

    An action is a self-contained unit of behavior that can be applied to a
    sprite or a list of sprites. Actions can be started, stopped, and updated
    over time. They can also be composed into more complex actions using
    sequences and parallels.

    Operator Overloading:
        - The `+` operator is overloaded to create a `Sequence` of actions.
        - The `|` operator is overloaded to create a `Parallel` composition of actions.
        - Note: `+` and `|` have the same precedence. Use parentheses to
          enforce the desired order of operations, e.g., `a + (b | c)`.
    """

    num_active_actions = 0
    debug_level: int = 0
    debug_include_classes: set[str] | None = None
    debug_all: bool = False
    _active_actions: list[Action] = []
    _pending_actions: list[Action] = []
    _is_updating: bool = False
    _previous_actions: set[Action] | None = None
    _warned_bad_callbacks: set[Callable] = set()
    _last_counts: dict[str, int] | None = None

    def __init__(
        self,
        condition: Callable[[], Any],
        on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
        tag: str | None = None,
    ):
        self.target: arcade.Sprite | arcade.SpriteList | None = None
        self.condition = condition
        self.on_stop = on_stop
        self.tag = tag
        self.done = False
        self._is_active = False
        self._callbacks_active = True
        self._paused = False
        self._factor = 1.0  # Multiplier for speed/rate, 1.0 = normal
        self._condition_met = False
        self._elapsed = 0.0
        self.condition_data: Any = None

    # Note on local imports in operator overloads:
    # These imports are done locally (not at module level) to avoid circular
    # dependencies. Since composite.py imports Action from this module (base.py),
    # we cannot import from composite.py at the top level without creating a
    # circular import that would fail at module load time.

    def __add__(self, other: Action) -> Action:
        """Create a sequence of actions using the '+' operator."""
        from actions.composite import sequence

        return sequence(self, other)

    def __radd__(self, other: Action) -> Action:
        """Create a sequence of actions using the '+' operator (right-hand)."""
        # This will be sequence(other, self)
        return other.__add__(self)

    def __or__(self, other: Action) -> Action:
        """Create a parallel composition of actions using the '|' operator."""
        from actions.composite import parallel

        return parallel(self, other)

    def __ror__(self, other: Action) -> Action:
        """Create a parallel composition of actions using the '|' operator (right-hand)."""
        # this will be parallel(other, self)
        return other.__or__(self)

    def apply(self, target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> Action:
        """
        Apply this action to a sprite or sprite list.

        This will add the action to the global action manager, which will then
        update it every frame.
        """
        self.target = target
        self.tag = tag
        if Action._is_updating:
            # Defer activation until end of update loop
            Action._pending_actions.append(self)
        else:
            Action._active_actions.append(self)
            self.start()
        return self

    def start(self) -> None:
        """Called when the action begins."""
        _debug_log_action(self, 2, f"start() target={self.target} tag={self.tag}")
        self._is_active = True
        self.apply_effect()
        _debug_log_action(self, 2, f"start() completed _is_active={self._is_active}")

    def apply_effect(self) -> None:
        """Apply the action's effect to the target."""
        pass

    def update(self, delta_time: float) -> None:
        """
        Update the action.

        This is called every frame by the global action manager.
        """
        if not self._is_active or self.done or self._paused:
            return

        self.update_effect(delta_time)

        if self.condition and not self._condition_met:
            condition_result = self.condition()
            if condition_result:
                self._condition_met = True
                self.condition_data = condition_result
                self.remove_effect()
                self.done = True
                if self.on_stop:
                    if condition_result is not True:
                        self._safe_call(self.on_stop, condition_result)
                    else:
                        self._safe_call(self.on_stop)

    def update_effect(self, delta_time: float) -> None:
        """
        Update the action's effect.

        This is called every frame by the update method.
        """
        pass

    def remove_effect(self) -> None:
        """
        Remove the action's effect from the target.

        This is called when the action is finished or stopped.
        """
        pass

    def stop(self) -> None:
        """Stop the action and remove it from the global action manager."""
        _debug_log_action(self, 2, f"stop() called done={self.done} _is_active={self._is_active}")
        if self in Action._active_actions:
            Action._active_actions.remove(self)
            _debug_log_action(self, 2, "removed from _active_actions")
        self._callbacks_active = False
        self.done = True
        self._is_active = False
        self.remove_effect()
        _debug_log_action(self, 2, f"stop() completed done={self.done} _is_active={self._is_active}")

    @staticmethod
    def get_actions_for_target(target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> list[Action]:
        """Get all actions for a given target, optionally filtered by tag."""
        if tag:
            return [action for action in Action._active_actions if action.target == target and action.tag == tag]
        return [action for action in Action._active_actions if action.target == target]

    @staticmethod
    def stop_actions_for_target(target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> None:
        """Stop all actions for a given target, optionally filtered by tag."""
        for action in Action.get_actions_for_target(target, tag):
            action.stop()

    @classmethod
    def update_all(cls, delta_time: float) -> None:
        """Update all active actions. Call this once per frame."""
        cls._is_updating = True
        try:
            # Level 1: per-class counts and total, only on change
            if cls.debug_level >= 1:
                counts: dict[str, int] = {}
                for a in cls._active_actions:
                    name = type(a).__name__
                    counts[name] = counts.get(name, 0) + 1
                if counts != (cls._last_counts or {}):
                    total = sum(counts.values())
                    parts = [f"Total={total}"] + [f"{k}={v}" for k, v in sorted(counts.items())]
                    print("[AA L1 summary] " + ", ".join(parts))
                    cls._last_counts = counts

            # Level 2: creation/removal notifications (filtered)
            if cls.debug_level >= 2:
                if cls._previous_actions is None:
                    cls._previous_actions = set()
                current_actions = set(cls._active_actions)
                new_actions = current_actions - cls._previous_actions
                removed_actions = cls._previous_actions - current_actions
                for a in new_actions:
                    _debug_log_action(a, 2, f"created target={cls._describe_target(a.target)} tag='{a.tag}'")
                for a in removed_actions:
                    _debug_log_action(a, 2, f"removed target={cls._describe_target(a.target)} tag='{a.tag}'")
                cls._previous_actions = current_actions

            # Phase 1: Deactivate callbacks for actions marked as done
            for action in cls._active_actions[:]:
                if action.done:
                    action._callbacks_active = False

            # Phase 2: Update all actions (stopped actions' callbacks won't fire)
            # Update easing/wrapper actions first so they can adjust factors before wrapped actions run
            current = cls._active_actions[:]
            wrappers = [a for a in current if hasattr(a, "wrapped_action")]
            non_wrappers = [a for a in current if not hasattr(a, "wrapped_action")]
            for action in wrappers:
                action.update(delta_time)
            for action in non_wrappers:
                action.update(delta_time)

            # Phase 3: Remove completed actions (safe, callbacks already deactivated)
            cls._active_actions[:] = [action for action in cls._active_actions if not action.done]
            cls.num_active_actions = len(cls._active_actions)

            # Phase 4: Activate any actions that were applied during this update
            if cls._pending_actions:
                for action in cls._pending_actions:
                    cls._active_actions.append(action)
                    action.start()
                cls._pending_actions.clear()
        finally:
            cls._is_updating = False

    @classmethod
    def _describe_target(cls, target: arcade.Sprite | arcade.SpriteList | None) -> str:
        if target is None:
            return "None"
        # Check type directly - this is debug-only code and performance matters
        if type(target).__name__ == "SpriteList":
            return cls._get_sprite_list_name(target)
        return f"{type(target).__name__}"

    @classmethod
    def _get_sprite_list_name(cls, sprite_list: arcade.SpriteList) -> str:
        """Attempt to find an attribute name that refers to this SpriteList.

        This is best-effort and only used for debug output.
        """
        try:
            import gc  # Imported here to avoid overhead unless debugging is enabled

            for obj in gc.get_objects():
                try:
                    # Use EAFP - try to access __dict__ directly
                    obj_dict = obj.__dict__
                    for attr_name, attr_value in obj_dict.items():
                        if attr_value is sprite_list:
                            return f"{type(obj).__name__}.{attr_name}"
                except AttributeError:
                    # Object has no __dict__, skip it
                    continue
                except Exception:
                    # Best-effort only; ignore objects that raise during inspection
                    continue
        except Exception:
            pass
        # Fallback description
        try:
            return f"SpriteList(len={len(sprite_list)})"
        except Exception:
            return "SpriteList"

    @classmethod
    def stop_all(cls) -> None:
        """Stop and remove all active actions."""
        for action in list(cls._active_actions):
            action.stop()

    @abstractmethod
    def clone(self) -> Action:
        """Return a new instance of this action."""
        raise NotImplementedError

    def for_each_sprite(self, func: Callable[[arcade.Sprite], None]) -> None:
        """
        Run a function on each sprite in the target.

        If the target is a single sprite, the function is run on that sprite.
        If the target is a sprite list, the function is run on each sprite in
        the list.
        """
        if self.target is None:
            return
        # Use duck typing - try list behavior first, fall back to single sprite
        try:
            # Try to iterate (SpriteList behavior)
            for sprite in self.target:
                func(sprite)
        except TypeError:
            # Not iterable, treat as single sprite
            func(self.target)

    def set_factor(self, factor: float) -> None:
        """
        Set the speed/rate multiplier for this action.

        This can be used to implement easing.
        """
        self._factor = factor

    @property
    def condition_met(self) -> bool:
        """Return True if the action's condition has been met."""
        return self._condition_met

    @condition_met.setter
    def condition_met(self, value: bool) -> None:
        """Set whether the action's condition has been met."""
        self._condition_met = value

    def pause(self) -> None:
        """Pause the action."""
        self._paused = True

    def resume(self) -> None:
        """Resume the action."""
        self._paused = False

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Set the current velocity for this action.

        Base implementation does nothing. Override in subclasses that support velocity control.

        Args:
            velocity: (dx, dy) velocity tuple to apply
        """

        pass

    def _safe_call(self, fn: Callable, *args) -> None:
        """
        Safely call a callback function with exception handling.

        Guards against callbacks executing after action has been stopped.
        TypeError exceptions get a one-time debug warning about parameter mismatches.
        All other exceptions are silently caught to prevent crashes.
        """
        # Guard against stopped actions - do not execute callbacks
        # Check if this is an instance call (has _callbacks_active) vs class call (for testing)
        if hasattr(self, "_callbacks_active") and not self._callbacks_active:
            return

        Action._execute_callback_impl(fn, *args)

    @staticmethod
    def _execute_callback_impl(fn: Callable, *args) -> None:
        """Execute callback with exception handling - for internal use and testing.

        Optimized to try no-parameter callbacks first (most common case),
        then fall back to with-parameter callbacks if that fails.
        """
        try:
            # If no args or only None provided, optimize for no-parameter callbacks
            if not args or (len(args) == 1 and args[0] is None):
                # Try without parameters first (common case)
                try:
                    fn()
                    return
                except TypeError as exc:
                    # Callback expects parameters, try with them if provided
                    if args:
                        # Warn about signature mismatch if debug enabled
                        if fn not in Action._warned_bad_callbacks and Action.debug_level >= 1:
                            import warnings

                            Action._warned_bad_callbacks.add(fn)
                            warnings.warn(
                                f"Callback '{fn.__name__}' failed with TypeError - "
                                f"check its parameter list matches the Action callback contract. "
                                f"Details: {exc}",
                                RuntimeWarning,
                                stacklevel=3,
                            )
                        fn(*args)
                    else:
                        raise  # Re-raise if no args to try
            else:
                # Meaningful data provided - try with parameters first
                try:
                    fn(*args)
                    return
                except TypeError as exc:
                    # Callback doesn't accept parameters, warn and try without
                    if fn not in Action._warned_bad_callbacks and Action.debug_level >= 1:
                        import warnings

                        Action._warned_bad_callbacks.add(fn)
                        warnings.warn(
                            f"Callback '{fn.__name__}' failed with TypeError - "
                            f"check its parameter list matches the Action callback contract. "
                            f"Details: {exc}",
                            RuntimeWarning,
                            stacklevel=3,
                        )
                    fn()
        except TypeError as exc:
            # Both attempts failed - warn about signature mismatch
            if fn not in Action._warned_bad_callbacks and Action.debug_level >= 1:
                import warnings

                Action._warned_bad_callbacks.add(fn)
                warnings.warn(
                    f"Callback '{fn.__name__}' failed with TypeError - "
                    f"check its parameter list matches the Action callback contract. "
                    f"Details: {exc}",
                    RuntimeWarning,
                    stacklevel=3,
                )
        except Exception:
            # Silently catch all other exceptions to prevent crashes
            pass


class CompositeAction(Action):
    """Base class for composite actions that manage multiple sub-actions."""

    def __init__(self):
        # Composite actions manage their own completion - no external condition
        super().__init__(condition=None, on_stop=None)
        self._on_complete_called = False

    def _check_complete(self) -> None:
        """Mark the composite action as complete."""
        if not self._on_complete_called:
            self._on_complete_called = True
            self.done = True

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement for boundary bouncing. Override in subclasses."""
        pass

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self.done = False
        self._on_complete_called = False

    def clone(self) -> CompositeAction:
        """Create a copy of this CompositeAction."""
        raise NotImplementedError("Subclasses must implement clone()")

    def apply_effect(self) -> None:
        pass
