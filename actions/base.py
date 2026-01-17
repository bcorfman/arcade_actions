"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

if TYPE_CHECKING:
    import arcade

    SpriteTarget = arcade.Sprite | arcade.SpriteList
else:
    SpriteTarget = Any  # Runtime fallback


_T = TypeVar("_T", bound="Action")


def _debug_log_action(action, level: int, message: str) -> None:
    """Centralized debug logger with level and per-Action filtering."""
    action_name = type(action).__name__

    # Level gate
    if Action.debug_level < level:
        return

    # Filter gate
    if not Action.debug_all:
        include = Action.debug_include_classes
        if not include or action_name not in include:
            return

    print(f"[AA L{level} {action_name}] {message}")


def _iter_target_sprites(target: Any) -> tuple[bool, list[Any]]:
    """Return (is_iterable_target, sprites) without runtime type checks."""
    try:
        return True, list(iter(target))
    except TypeError:
        return False, []


def _get_target_sprite_lists(target: Any) -> list[Any]:
    """Return sprite lists for a target."""
    return list(target.sprite_lists)


def _validate_target(target: Any) -> None:
    """Validate target supports required sprite interfaces."""
    try:
        iter(target)
        return
    except TypeError:
        try:
            target.sprite_lists
        except AttributeError as attr_exc:
            raise TypeError("Action target must be iterable or expose sprite_lists") from attr_exc
        return


class VelocityControllable(Protocol):
    """Protocol for actions that support velocity control."""

    def set_current_velocity(self, velocity: tuple[float, float]) -> None:
        """Set the current velocity for this action."""
        ...


class SpriteIterable(Protocol):
    """Protocol for iterable sprite targets."""

    def __iter__(self): ...


class SpriteListContainer(Protocol):
    """Protocol for sprite targets that expose sprite_lists."""

    sprite_lists: list[Any]


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

    # Class-level conflict declaration - subclasses should override
    # Declares which sprite properties this action mutates (e.g., "position", "velocity", "texture", "alpha", "angle")
    _conflicts_with: tuple[str, ...] = ()
    _requires_sprite_target: bool = True

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
    _enable_visualizer: bool = False  # Enable instrumentation hooks
    _frame_counter: int = 0  # Track frame count for visualization
    _debug_store = None  # Injected DebugDataStore dependency
    _is_stepping: bool = False  # Flag to track when we're in a step cycle

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
        self._duration: float | None = None
        self.bounds: tuple[float, float, float, float] | None = None
        self.condition_data: Any = None
        self._instrumented = False  # Set True when action is applied via Action.apply()
        self.wrapped_action: Action | None = None

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

    def apply(self, target: SpriteTarget | None, tag: str | None = None, replace: bool = False) -> Action:
        """
        Apply this action to a sprite or sprite list.

        This will add the action to the global action manager, which will then
        update it every frame.

        Args:
            target: The sprite or sprite list to apply the action to.
            tag: Optional tag for the action. If provided and replace=True,
                 existing actions with the same tag on the same target will be stopped.
            replace: If True and tag is provided, stop existing actions with the same
                     tag on the same target before applying this action.
        """
        if target is None:
            self.target = None
            if tag is not None:
                self.tag = tag
            return self

        if self._requires_sprite_target:
            _validate_target(target)
        self.target = target
        if tag is not None:
            self.tag = tag
        self._instrumented = True

        # Tag-based replacement: stop existing actions with same tag before applying
        if replace and tag is not None:
            Action.stop_actions_for_target(target, tag=tag)

        # Conflict detection: check for overlapping actions that mutate same properties
        if self._requires_sprite_target:
            _check_action_conflicts(self, target)

        # Instrumentation: record creation
        if self._instrumentation_active():
            self._record_event("created")

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

        # If all other active actions are paused, start this action paused too
        # This ensures new actions created during pause (e.g., from mouse clicks)
        # respect the global pause state without game code needing to know about it
        if Action._active_actions:
            # Check if all OTHER actions (not including self, which may already be in the list) are paused
            other_actions = [a for a in Action._active_actions if a is not self]
            if other_actions and all(a._paused for a in other_actions):
                self._paused = True
                self._on_start_paused()
                # Don't apply initial effects when starting paused
                _debug_log_action(self, 2, "starting in paused state (matching global pause)")

                # Instrumentation: record started and create snapshot
                if self._instrumentation_active():
                    self._record_event("started")
                    self._update_snapshot()
                return

        # Instrumentation: record started and create snapshot
        if self._instrumentation_active():
            self._record_event("started")
            self._update_snapshot()

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

            # Instrumentation: record condition evaluation
            if self._instrumentation_active():
                self._record_condition_evaluation(condition_result)

            if condition_result:
                self._condition_met = True
                self.condition_data = condition_result
                self.remove_effect()
                self.done = True

                # Instrumentation: record stopped
                if self._instrumentation_active():
                    self._record_event("stopped", condition_data=condition_result)

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

        # Set flags FIRST to prevent race conditions where _update_snapshot()
        # is called after _record_event("removed") removes the snapshot but
        # before the flags are set, allowing the snapshot to be recreated
        self._callbacks_active = False
        self.done = True
        self._is_active = False

        # Instrumentation: record removed (snapshot will be removed from store)
        if self._instrumentation_active():
            self._record_event("removed")

        if self in Action._active_actions:
            Action._active_actions.remove(self)
            _debug_log_action(self, 2, "removed from _active_actions")
        self.remove_effect()
        _debug_log_action(self, 2, f"stop() completed done={self.done} _is_active={self._is_active}")

    @staticmethod
    def get_actions_for_target(target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> list[Action]:
        """Get all actions for a given target, optionally filtered by tag."""
        if tag:
            return [action for action in Action._active_actions if action.target == target and action.tag == tag]
        return [action for action in Action._active_actions if action.target == target]

    @classmethod
    def pause_all(cls) -> None:
        """Pause all active actions."""
        for action in cls._active_actions:
            action.pause()

    @classmethod
    def resume_all(cls) -> None:
        """Resume all active actions."""
        for action in cls._active_actions:
            action.resume()

    @classmethod
    def is_paused(cls) -> bool:
        """Check if all active actions are paused.

        Returns:
            True if all active actions are paused, False otherwise.
            Returns False if there are no active actions.
        """
        if not cls._active_actions:
            return False
        return all(action._paused for action in cls._active_actions)

    @classmethod
    def step_all(cls, delta_time: float, *, physics_engine=None) -> None:
        """Advance all actions by a single step while keeping them paused."""
        cls._is_stepping = True
        try:
            cls.resume_all()
            cls.update_all(delta_time, physics_engine=physics_engine)
            cls.pause_all()
        finally:
            cls._is_stepping = False

    @staticmethod
    def stop_actions_for_target(target: arcade.Sprite | arcade.SpriteList, tag: str | None = None) -> None:
        """Stop all actions for a given target, optionally filtered by tag."""
        for action in Action.get_actions_for_target(target, tag):
            action.stop()

    @classmethod
    def current_frame(cls) -> int:
        """Get the current frame count.

        The frame counter increments with each call to update_all() and does not
        increment when actions are paused. This provides deterministic timing
        independent of wall-clock time or delta_time variations.

        Returns:
            Current frame count since initialization or last reset.

        Examples:
            # Check current frame in a condition
            def after_100_frames():
                return Action.current_frame() >= 100

            # Log frame count for debugging
            print(f"Action completed at frame {Action.current_frame()}")
        """
        return cls._frame_counter

    @classmethod
    def update_all(cls, delta_time: float, *, physics_engine=None) -> None:
        """Update all active actions. Call this once per frame.

        Args:
            delta_time: Time elapsed since last update in seconds.
            physics_engine: Physics engine for physics-aware action routing.
                When provided, velocity-based actions like MoveUntil and RotateUntil
                will route their operations through the engine. Additionally, Arcade
                velocities (change_x/change_y) are automatically synced to Pymunk
                for all kinematic bodies, eliminating the need for manual set_velocity
                calls. When omitted, actions manipulate sprite attributes directly.
        """
        # Check if ALL actions are paused - if so, don't increment frame counter
        # This ensures pause/resume/step behavior works correctly
        all_paused = cls._active_actions and all(action._paused for action in cls._active_actions)

        # Only increment frame counter if not all actions are paused
        if not all_paused:
            cls._frame_counter += 1

            # Update visualization instrumentation
            if cls._enable_visualizer and cls._debug_store:
                cls._record_debug_frame(cls._frame_counter, time.time())

        # Provide engine context for adapter-powered actions
        try:
            from actions.physics_adapter import set_current_engine  # local import to avoid hard dep
        except Exception:
            set_current_engine = None

        if set_current_engine is not None:
            set_current_engine(physics_engine)

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
            wrappers = [a for a in current if a.wrapped_action is not None]
            non_wrappers = [a for a in current if a.wrapped_action is None]
            for action in wrappers:
                action.update(delta_time)
            for action in non_wrappers:
                action.update(delta_time)

            # Phase 3: Remove completed actions (safe, callbacks already deactivated)
            remaining_actions: list[Action] = []
            if cls._enable_visualizer:
                for action in cls._active_actions:
                    if action.done:
                        action._record_event("removed")
                        action._is_active = False
                    else:
                        remaining_actions.append(action)
            else:
                for action in cls._active_actions:
                    if not action.done:
                        remaining_actions.append(action)
                    else:
                        action._is_active = False
            cls._active_actions[:] = remaining_actions
            cls.num_active_actions = len(cls._active_actions)

            # Phase 4: Activate any actions that were applied during this update
            if cls._pending_actions:
                for action in cls._pending_actions:
                    cls._active_actions.append(action)
                    action.start()
                cls._pending_actions.clear()

            # Phase 5: Sync Arcade velocities to Pymunk for kinematic bodies
            # This allows MoveUntil/RotateUntil to work seamlessly with kinematic sprites
            if physics_engine is not None:
                try:
                    # Access internal sprites dict to find kinematic bodies
                    for sprite in physics_engine._sprites.keys():
                        body = physics_engine._sprites[sprite]
                        # Only sync for kinematic bodies (user controls velocity)
                        if body.body_type == physics_engine.KINEMATIC:
                            # Convert Arcade's px/frame to Pymunk's px/sec
                            velocity = (sprite.change_x / delta_time, sprite.change_y / delta_time)
                            physics_engine.set_velocity(sprite, velocity)
                except (AttributeError, KeyError):
                    # Physics engine doesn't have expected structure, skip sync
                    pass
        finally:
            cls._is_updating = False
            if set_current_engine is not None:
                set_current_engine(None)

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

        Exception Strategy:
        - AttributeError: Expected for objects without __dict__, handled silently
        - Other exceptions: Propagate - they indicate real bugs that should be visible in debug mode

        Note: Uses gc.get_objects() which is expensive. Only called at debug_level >= 2.
        """
        import gc  # Imported here to avoid overhead unless debugging is enabled

        # Try to find which object holds this sprite_list
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

        # Fallback to simple description
        return f"SpriteList(len={len(sprite_list)})"

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

    def sub_actions(self) -> list[Action]:
        """Return child actions for composite types; empty for leaf actions."""
        return []

    def _safe_call(self, fn: Callable, *args) -> None:
        """
        Safely call a callback function with exception handling.

        Guards against callbacks executing after action has been stopped.
        TypeError exceptions get a one-time debug warning about parameter mismatches.
        All other exceptions are silently caught to prevent crashes.
        """
        # Guard against stopped actions - do not execute callbacks
        if not self._callbacks_active:
            return

        Action._execute_callback_impl(fn, *args)

    def _on_start_paused(self) -> None:
        """Hook for actions that need to capture state when starting paused."""
        pass

    def _instrumentation_active(self) -> bool:
        return self._instrumented and Action._enable_visualizer and Action._debug_store is not None

    @staticmethod
    def _execute_callback_impl(fn: Callable, *args) -> None:
        """Execute callback with exception handling - for internal use and testing.

        Exception Strategy:
        - TypeError (signature mismatch): Warn once per callback, try fallback signature
        - Other exceptions: Catch to prevent crashes, log at debug level 2+
        - Successful execution: Return immediately

        Supports both no-parameter and with-parameter callback signatures.
        Optimizes for the expected signature based on whether args are provided.
        """

        def _warn_signature_mismatch(exc: TypeError) -> None:
            """Warn about callback signature mismatch (once per callback)."""
            if fn not in Action._warned_bad_callbacks and Action.debug_level >= 1:
                import warnings

                Action._warned_bad_callbacks.add(fn)
                warnings.warn(
                    f"Callback '{fn.__name__}' failed with TypeError - signature mismatch: {exc}",
                    RuntimeWarning,
                    stacklevel=4,
                )

        try:
            # Determine preferred signature based on args
            has_meaningful_args = args and not (len(args) == 1 and args[0] is None)

            def _call_with_args(call_args: tuple[Any, ...] | None) -> tuple[bool, TypeError | None]:
                try:
                    if call_args is None:
                        fn()
                    else:
                        fn(*call_args)
                    return True, None
                except TypeError as error:
                    return False, error

            # Try preferred signature first
            initial_args = args if has_meaningful_args else None
            succeeded, error = _call_with_args(initial_args)
            if succeeded:
                return

            # Initial call failed - we'll need to warn if fallback succeeds
            initial_error = error
            fallback_error = error
            fallback_called = False

            fallback_variants: list[tuple[Any, ...]] = []
            if has_meaningful_args:
                for size in range(len(args) - 1, -1, -1):
                    fallback_variants.append(args[:size])
            else:
                if args:
                    fallback_variants.append(args)
                fallback_variants.append(tuple())

            for variant in fallback_variants:
                # Avoid retrying the same signature twice
                if has_meaningful_args and variant == args:
                    continue
                call_args = variant if variant else None
                succeeded, error = _call_with_args(call_args)
                if succeeded:
                    fallback_called = True
                    break
                fallback_error = error

            if fallback_called:
                # Fallback succeeded, but initial call failed - warn about mismatch
                _warn_signature_mismatch(initial_error)
                return

            if fallback_error is not None:
                # All fallbacks failed - warn about the final error
                _warn_signature_mismatch(fallback_error)
        except Exception as exc:
            # Catch other exceptions to prevent action system crashes
            # Log them at debug level 2+ to help troubleshoot bad callbacks
            if Action.debug_level >= 2:
                print(f"[AA] Callback '{fn.__name__}' raised {type(exc).__name__}: {exc}")

    @classmethod
    def set_debug_store(cls, debug_store) -> None:
        """
        Inject a DebugDataStore dependency for visualization instrumentation.

        This follows dependency injection principles by allowing the debug store
        to be provided externally rather than created as a global singleton.

        Args:
            debug_store: DebugDataStore instance to use for recording events
        """
        cls._debug_store = debug_store

    def _record_event(self, event_type: str, **details) -> None:
        """
        Record an action lifecycle event to the debug store.

        Args:
            event_type: Type of event ("created", "started", "stopped", "removed")
            **details: Additional event-specific details
        """
        if not self._instrumentation_active():
            return

        target_id = id(self.target) if self.target else 0
        # Use type name directly - let the store handle display logic
        target_type = type(self.target).__name__ if self.target else "None"

        store = Action._debug_store
        if not store:
            return

        try:
            store.record_event(
                event_type=event_type,
                action_id=id(self),
                action_type=type(self).__name__,
                target_id=target_id,
                target_type=target_type,
                tag=self.tag,
                **details,
            )
        except AttributeError:
            return

    def _record_condition_evaluation(self, result: Any) -> None:
        """
        Record a condition evaluation result to the debug store.

        Args:
            result: The value returned by the condition function
        """
        if not self._instrumentation_active():
            return

        # Get string representation of condition - use EAFP with genuine fallback
        condition_str = None
        condition_str = "<unknown>"
        try:
            condition_str = self.condition.__name__
        except AttributeError:
            # Fallback for lambda functions which don't have __name__
            try:
                condition_doc = self.condition.__doc__
            except AttributeError:
                condition_doc = None
            if condition_doc:
                condition_str = condition_doc.strip()

        store = Action._debug_store
        if not store:
            return

        try:
            store.record_condition_evaluation(
                action_id=id(self), action_type=type(self).__name__, result=result, condition_str=condition_str
            )
        except AttributeError:
            return

    def _update_snapshot(self, **kwargs) -> None:
        """
        Update or create a snapshot of this action's current state.

        Args:
            **kwargs: Additional snapshot fields to update
        """
        if not self._instrumentation_active():
            return

        # Don't update snapshot if action is done or not active
        # This prevents race conditions where stop() removes the snapshot
        # but _update_snapshot() is called afterward and recreates it
        if self.done or not self._is_active:
            return

        target_id = id(self.target) if self.target else 0
        # Use type name directly - let the store handle display logic
        target_type = type(self.target).__name__ if self.target else "None"

        # Build snapshot data
        snapshot_data = {
            "action_id": id(self),
            "action_type": type(self).__name__,
            "target_id": target_id,
            "target_type": target_type,
            "tag": self.tag,
            "is_active": self._is_active,
            "is_paused": self._paused,
            "factor": self._factor,
            "elapsed": self._elapsed,
            "progress": None,  # Subclasses can override
        }
        snapshot_data.update(kwargs)

        store = Action._debug_store
        if not store:
            return

        try:
            store.update_snapshot(**snapshot_data)
        except AttributeError:
            return

    @classmethod
    def _record_debug_frame(cls, frame_number: int, timestamp: float) -> None:
        store = cls._debug_store
        if not store:
            return

        try:
            store.update_frame(frame_number, timestamp)
        except AttributeError:
            return


def _check_action_conflicts(new_action: Action, target: arcade.Sprite | arcade.SpriteList) -> None:
    """Check for conflicts between the new action and existing actions on the target.

    If ACTIONS_WARN_CONFLICTS environment variable is set, warns when actions
    that mutate the same sprite properties are detected on the same target.

    Args:
        new_action: The action being applied
        target: The target sprite or sprite list
    """
    import os
    import warnings

    # Only check conflicts if env var is set
    if not os.getenv("ACTIONS_WARN_CONFLICTS"):
        return

    # Get conflicts declared by the new action
    new_conflicts = getattr(new_action.__class__, "_conflicts_with", ())
    if not new_conflicts:
        return  # No conflicts declared, nothing to check

    # Convert to set for efficient intersection
    new_conflict_set = set(new_conflicts)

    # Check existing actions on the same target
    existing_actions = Action.get_actions_for_target(target)
    conflicting_actions = []

    for existing_action in existing_actions:
        if existing_action is new_action:
            continue  # Skip self

        existing_conflicts = getattr(existing_action.__class__, "_conflicts_with", ())
        existing_conflict_set = set(existing_conflicts)

        # Check if there's any overlap in conflict sets
        if new_conflict_set & existing_conflict_set:
            conflicting_actions.append(existing_action)

    # Also check per-sprite actions if target is iterable (SpriteList-like).
    is_iterable_target, sprites = _iter_target_sprites(target)
    if is_iterable_target:
        for sprite in sprites:
            sprite_actions = Action.get_actions_for_target(sprite)
            for sprite_action in sprite_actions:
                sprite_conflicts = getattr(sprite_action.__class__, "_conflicts_with", ())
                sprite_conflict_set = set(sprite_conflicts)
                if new_conflict_set & sprite_conflict_set:
                    conflicting_actions.append(sprite_action)
    else:
        # Also check SpriteList actions if target is a sprite (reverse direction).
        for sprite_list in _get_target_sprite_lists(target):
            list_actions = Action.get_actions_for_target(sprite_list)
            for list_action in list_actions:
                list_conflicts = getattr(list_action.__class__, "_conflicts_with", ())
                list_conflict_set = set(list_conflicts)
                if new_conflict_set & list_conflict_set:
                    conflicting_actions.append(list_action)

    # Warn about conflicts
    if conflicting_actions:
        conflict_names = ", ".join(set(new_conflicts))
        existing_class_names = ", ".join(set(type(a).__name__ for a in conflicting_actions))
        new_class_name = type(new_action).__name__

        warnings.warn(
            f"Detected overlapping action conflicts ({conflict_names}): "
            f"{new_class_name}(tag={new_action.tag!r}) conflicts with {existing_class_names} "
            f"on the same target. Consider using replace=True or stopping existing actions first.",
            RuntimeWarning,
            stacklevel=3,
        )


class CompositeAction(Action):
    """Base class for composite actions that manage multiple sub-actions."""

    def __init__(self):
        # Composite actions manage their own completion - no external condition
        super().__init__(condition=None, on_stop=None)
        self._on_complete_called = False
        self.actions: list[Action] = []

    def _check_complete(self) -> None:
        """Mark the composite action as complete."""
        if not self._on_complete_called:
            self._on_complete_called = True
            self.done = True

    def reverse_movement(self, axis: str) -> None:
        """Reverse movement for boundary bouncing. Override in subclasses."""
        pass

    def sub_actions(self) -> list[Action]:
        """Return child actions for composite types."""
        return self.actions

    def reset(self) -> None:
        """Reset the action to its initial state."""
        self.done = False
        self._on_complete_called = False

    def clone(self) -> CompositeAction:
        """Create a copy of this CompositeAction."""
        raise NotImplementedError("Subclasses must implement clone()")

    def apply_effect(self) -> None:
        pass
