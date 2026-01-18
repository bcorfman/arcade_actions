from __future__ import annotations

import time
from typing import Any

from ._action_debug import _debug_log_action


class ActionManagerMixin:
    """Global action manager behavior."""

    @classmethod
    def get_actions_for_target(cls, target, tag: str | None = None):
        if tag:
            return [action for action in cls._active_actions if action.target == target and action.tag == tag]
        return [action for action in cls._active_actions if action.target == target]

    @classmethod
    def pause_all(cls) -> None:
        for action in cls._active_actions:
            action.pause()

    @classmethod
    def resume_all(cls) -> None:
        for action in cls._active_actions:
            action.resume()

    @classmethod
    def is_paused(cls) -> bool:
        if not cls._active_actions:
            return False
        return all(action._paused for action in cls._active_actions)

    @classmethod
    def step_all(cls, delta_time: float, *, physics_engine=None) -> None:
        cls._is_stepping = True
        try:
            cls.resume_all()
            cls.update_all(delta_time, physics_engine=physics_engine)
            cls.pause_all()
        finally:
            cls._is_stepping = False

    @classmethod
    def stop_actions_for_target(cls, target, tag: str | None = None) -> None:
        for action in cls.get_actions_for_target(target, tag):
            action.stop()

    @classmethod
    def current_frame(cls) -> int:
        return cls._frame_counter

    @classmethod
    def update_all(cls, delta_time: float, *, physics_engine=None) -> None:
        all_paused = cls._active_actions and all(action._paused for action in cls._active_actions)

        if not all_paused:
            cls._frame_counter += 1
            if cls._enable_visualizer and cls._debug_store:
                cls._record_debug_frame(cls._frame_counter, time.time())

        try:
            from arcadeactions.physics_adapter import set_current_engine
        except Exception:
            set_current_engine = None

        if set_current_engine is not None:
            set_current_engine(physics_engine)

        cls._is_updating = True
        try:
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

            for action in cls._active_actions[:]:
                if action.done:
                    action._callbacks_active = False

            current = cls._active_actions[:]
            wrappers = [a for a in current if a.wrapped_action is not None]
            non_wrappers = [a for a in current if a.wrapped_action is None]
            for action in wrappers:
                action.update(delta_time)
            for action in non_wrappers:
                action.update(delta_time)

            remaining_actions: list[Any] = []
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

            if cls._pending_actions:
                for action in cls._pending_actions:
                    cls._active_actions.append(action)
                    action.start()
                cls._pending_actions.clear()

            if physics_engine is not None:
                if delta_time <= 0:
                    return
                sprite_map = physics_engine.sprites
                for sprite, body in sprite_map.items():
                    if body.body.body_type == physics_engine.KINEMATIC:
                        velocity = (sprite.change_x / delta_time, sprite.change_y / delta_time)
                        physics_engine.set_velocity(sprite, velocity)
        finally:
            cls._is_updating = False
            if set_current_engine is not None:
                set_current_engine(None)

    @classmethod
    def stop_all(cls) -> None:
        for action in list(cls._active_actions):
            action.stop()
