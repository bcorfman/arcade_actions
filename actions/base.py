"""
Base classes for Arcade Actions system.
Actions are used to animate sprites and sprite lists over time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar
import time

if TYPE_CHECKING:
    import arcade

    SpriteTarget = arcade.Sprite | arcade.SpriteList
else:
    SpriteTarget = Any  # Runtime fallback


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
    _enable_visualizer: bool = False  # Enable instrumentation hooks
    _frame_counter: int = 0  # Track frame count for visualization
    _debug_store = None  # Injected DebugDataStore dependency

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
        self._instrumented = False  # Set True when action is applied via Action.apply()

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
        if tag is not None:
            self.tag = tag
        self._instrumented = True

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
    def step_all(cls, delta_time: float, *, physics_engine=None) -> None:
        """Advance all actions by a single step while keeping them paused."""
        cls.resume_all()
        cls.update_all(delta_time, physics_engine=physics_engine)
        cls.pause_all()

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
            wrappers = [a for a in current if hasattr(a, "wrapped_action")]
            non_wrappers = [a for a in current if not hasattr(a, "wrapped_action")]
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
        try:
            condition_str = self.condition.__name__
        except AttributeError:
            # Fallback for lambda functions which don't have __name__
            try:
                if self.condition.__doc__:
                    condition_str = self.condition.__doc__.strip()
            except AttributeError:
                pass  # No name or doc available

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
