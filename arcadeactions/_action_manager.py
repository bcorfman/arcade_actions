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
        cls._update_frame_counter()
        set_current_engine = cls._configure_physics_engine(physics_engine)

        cls._is_updating = True
        try:
            cls._log_debug_summary()
            cls._log_debug_diff()
            cls._deactivate_done_callbacks()
            cls._update_actions(delta_time)
            cls._rebuild_active_actions()
            cls._append_pending_actions()
            cls._sync_physics_engine(physics_engine, delta_time)
        finally:
            cls._is_updating = False
            cls._reset_physics_engine(set_current_engine)

    @classmethod
    def _update_frame_counter(cls) -> None:
        all_paused = cls._active_actions and all(action._paused for action in cls._active_actions)
        if all_paused:
            return
        cls._frame_counter += 1
        if cls._enable_visualizer and cls._debug_store:
            cls._record_debug_frame(cls._frame_counter, time.time())

    @classmethod
    def _configure_physics_engine(cls, physics_engine):
        try:
            from arcadeactions.physics_adapter import set_current_engine
        except Exception:
            set_current_engine = None
        if set_current_engine is not None:
            set_current_engine(physics_engine)
        return set_current_engine

    @classmethod
    def _reset_physics_engine(cls, set_current_engine) -> None:
        if set_current_engine is not None:
            set_current_engine(None)

    @classmethod
    def _log_debug_summary(cls) -> None:
        if cls.debug_level < 1:
            return
        counts: dict[str, int] = {}
        for action in cls._active_actions:
            name = type(action).__name__
            counts[name] = counts.get(name, 0) + 1
        if counts != (cls._last_counts or {}):
            total = sum(counts.values())
            parts = [f"Total={total}"] + [f"{k}={v}" for k, v in sorted(counts.items())]
            print("[AA L1 summary] " + ", ".join(parts))
            cls._last_counts = counts

    @classmethod
    def _log_debug_diff(cls) -> None:
        if cls.debug_level < 2:
            return
        if cls._previous_actions is None:
            cls._previous_actions = set()
        current_actions = set(cls._active_actions)
        new_actions = current_actions - cls._previous_actions
        removed_actions = cls._previous_actions - current_actions
        for action in new_actions:
            _debug_log_action(action, 2, f"created target={cls._describe_target(action.target)} tag='{action.tag}'")
        for action in removed_actions:
            _debug_log_action(action, 2, f"removed target={cls._describe_target(action.target)} tag='{action.tag}'")
        cls._previous_actions = current_actions

    @classmethod
    def _deactivate_done_callbacks(cls) -> None:
        for action in cls._active_actions[:]:
            if action.done:
                action._callbacks_active = False

    @classmethod
    def _update_actions(cls, delta_time: float) -> None:
        current = cls._active_actions[:]
        wrappers = [action for action in current if action.wrapped_action is not None]
        non_wrappers = [action for action in current if action.wrapped_action is None]
        for action in wrappers:
            action.update(delta_time)
        for action in non_wrappers:
            action.update(delta_time)

    @classmethod
    def _rebuild_active_actions(cls) -> None:
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

    @classmethod
    def _append_pending_actions(cls) -> None:
        if not cls._pending_actions:
            return
        for action in cls._pending_actions:
            cls._active_actions.append(action)
            action.start()
        cls._pending_actions.clear()

    @classmethod
    def _sync_physics_engine(cls, physics_engine, delta_time: float) -> None:
        if physics_engine is None or delta_time <= 0:
            return
        sprite_map = physics_engine.sprites
        for sprite, body in sprite_map.items():
            if body.body.body_type == physics_engine.KINEMATIC:
                velocity = (sprite.change_x / delta_time, sprite.change_y / delta_time)
                physics_engine.set_velocity(sprite, velocity)

    @classmethod
    def stop_all(cls) -> None:
        for action in list(cls._active_actions):
            action.stop()
