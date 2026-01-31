"""Helpers for applying action metadata in DevVisualizer."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import arcade

from arcadeactions.dev.visualizer_helpers import resolve_callback, resolve_condition
from arcadeactions.dev.visualizer_protocols import SpriteWithActionConfigs


def apply_metadata_actions(
    sprite: arcade.Sprite,
    ctx: Any,
    resolver: Callable[[str], Any] | None = None,
) -> None:
    """Convert sprite metadata configs into active actions."""
    if not isinstance(sprite, SpriteWithActionConfigs):
        return

    from arcadeactions import (
        blink_until,
        callback_until,
        cycle_textures_until,
        delay_until,
        emit_particles_until,
        fade_until,
        follow_path_until,
        glow_until,
        move_until,
        rotate_until,
        scale_until,
        tween_until,
    )
    from arcadeactions.dev import get_preset_registry

    handlers = {
        "MoveUntil": _apply_move_until,
        "FollowPathUntil": _apply_follow_path_until,
        "CycleTexturesUntil": _apply_cycle_textures_until,
        "FadeUntil": _apply_fade_until,
        "BlinkUntil": _apply_blink_until,
        "RotateUntil": _apply_rotate_until,
        "TweenUntil": _apply_tween_until,
        "ScaleUntil": _apply_scale_until,
        "CallbackUntil": _apply_callback_until,
        "DelayUntil": _apply_delay_until,
        "EmitParticlesUntil": _apply_emit_particles_until,
        "GlowUntil": _apply_glow_until,
    }

    for config in sprite._action_configs:
        preset_id = config.get("preset")
        if preset_id:
            if _apply_preset_action(sprite, config, ctx, resolver, get_preset_registry):
                continue
            continue

        action_type = config.get("action_type")
        condition_spec = config.get("condition", "infinite")
        condition_callable = resolve_condition(condition_spec)

        handler = handlers.get(action_type)
        if handler is None:
            continue
        handler(
            sprite,
            config,
            condition_callable,
            resolver,
            move_until,
            follow_path_until,
            cycle_textures_until,
            fade_until,
            blink_until,
            rotate_until,
            tween_until,
            scale_until,
            callback_until,
            delay_until,
            emit_particles_until,
            glow_until,
        )


def _apply_preset_action(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    ctx: Any,
    resolver: Callable[[str], Any] | None,
    preset_registry_provider: Callable[[], Any],
) -> bool:
    preset_id = config.get("preset")
    if not preset_id:
        return False

    params = config.get("params", {}) or {}
    try:
        preset_action = preset_registry_provider().create(preset_id, ctx, **params)
        _apply_preset_overrides(preset_action, config, resolver)
        preset_action.apply(sprite)
    except Exception:
        return False
    return True


def _apply_preset_overrides(preset_action: Any, config: dict[str, Any], resolver: Callable[[str], Any] | None) -> None:
    cond = resolve_condition(config.get("condition", None))
    if cond is not None:
        try:
            preset_action.condition = cond
        except Exception:
            pass

    _assign_callback(preset_action, "on_stop", config.get("on_stop", None), resolver)

    tag = config.get("tag", None)
    if tag is not None:
        try:
            preset_action.tag = tag
        except Exception:
            pass

    velocity = config.get("velocity", None)
    if velocity is not None and hasattr(preset_action, "target_velocity"):
        try:
            preset_action.target_velocity = velocity
            preset_action.current_velocity = velocity
        except Exception:
            pass

    bounds = config.get("bounds", None)
    if bounds is not None and hasattr(preset_action, "bounds"):
        try:
            preset_action.bounds = bounds
        except Exception:
            pass

    boundary_behavior = config.get("boundary_behavior", None)
    if boundary_behavior is not None and hasattr(preset_action, "boundary_behavior"):
        try:
            preset_action.boundary_behavior = boundary_behavior
        except Exception:
            pass

    velocity_provider = config.get("velocity_provider", None)
    if velocity_provider is not None and hasattr(preset_action, "velocity_provider"):
        try:
            preset_action.velocity_provider = velocity_provider
        except Exception:
            pass

    _assign_callback(preset_action, "on_boundary_enter", config.get("on_boundary_enter", None), resolver)
    _assign_callback(preset_action, "on_boundary_exit", config.get("on_boundary_exit", None), resolver)


def _assign_callback(preset_action: Any, attr: str, spec: Any, resolver: Callable[[str], Any] | None) -> None:
    callback = resolve_callback(spec, resolver)
    if callback is not None and hasattr(preset_action, attr):
        try:
            setattr(preset_action, attr, callback)
        except Exception:
            pass


def _apply_move_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    move_until,
    *_args,
) -> None:
    velocity = config.get("velocity", (0, 0))
    bounds = config.get("bounds", None)
    boundary_behavior = config.get("boundary_behavior", None)
    tag = config.get("tag", None)
    velocity_provider = config.get("velocity_provider", None)
    on_boundary_enter = resolve_callback(config.get("on_boundary_enter", None), resolver)
    on_boundary_exit = resolve_callback(config.get("on_boundary_exit", None), resolver)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)

    move_until(
        sprite,
        velocity=velocity,
        condition=condition_callable,
        bounds=bounds,
        boundary_behavior=boundary_behavior,
        tag=tag,
        velocity_provider=velocity_provider,
        on_boundary_enter=on_boundary_enter,
        on_boundary_exit=on_boundary_exit,
        on_stop=on_stop,
    )


def _apply_follow_path_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    follow_path_until,
    *_args,
) -> None:
    control_points = config.get("control_points")
    velocity = config.get("velocity")
    rotate_with_path = config.get("rotate_with_path", False)
    rotation_offset = config.get("rotation_offset", 0.0)
    use_physics = config.get("use_physics", False)
    steering_gain = config.get("steering_gain", 5.0)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)

    if control_points and velocity is not None:
        follow_path_until(
            sprite,
            control_points=control_points,
            velocity=velocity,
            condition=condition_callable,
            on_stop=on_stop,
            rotate_with_path=rotate_with_path,
            rotation_offset=rotation_offset,
            use_physics=use_physics,
            steering_gain=steering_gain,
        )


def _apply_cycle_textures_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    cycle_textures_until,
    *_args,
) -> None:
    textures = config.get("textures")
    frames_per_texture = config.get("frames_per_texture", 1)
    direction = config.get("direction", 1)
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if textures:
        cycle_textures_until(
            sprite,
            textures=textures,
            frames_per_texture=frames_per_texture,
            direction=direction,
            condition=condition_callable,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_fade_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    fade_until,
    *_args,
) -> None:
    fade_velocity = config.get("fade_velocity")
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if fade_velocity is not None:
        fade_until(
            sprite,
            velocity=fade_velocity,
            condition=condition_callable,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_blink_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    blink_until,
    *_args,
) -> None:
    frames_until_change = config.get("frames_until_change")
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    on_blink_enter = resolve_callback(config.get("on_blink_enter", None), resolver)
    on_blink_exit = resolve_callback(config.get("on_blink_exit", None), resolver)
    if frames_until_change is not None:
        blink_until(
            sprite,
            frames_until_change=frames_until_change,
            condition=condition_callable,
            on_stop=on_stop,
            on_blink_enter=on_blink_enter,
            on_blink_exit=on_blink_exit,
            tag=tag,
        )


def _apply_rotate_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    rotate_until,
    *_args,
) -> None:
    angular_velocity = config.get("angular_velocity")
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if angular_velocity is not None:
        rotate_until(
            sprite,
            angular_velocity=angular_velocity,
            condition=condition_callable,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_tween_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    tween_until,
    *_args,
) -> None:
    start_value = config.get("start_value")
    end_value = config.get("end_value")
    property_name = config.get("property_name")
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if start_value is not None and end_value is not None and property_name:
        tween_until(
            sprite,
            start_value=start_value,
            end_value=end_value,
            property_name=property_name,
            condition=condition_callable,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_scale_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    _tween_until,
    scale_until,
    *_args,
) -> None:
    velocity = config.get("velocity")
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if velocity is not None:
        scale_until(
            sprite,
            velocity=velocity,
            condition=condition_callable,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_callback_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    _tween_until,
    _scale_until,
    callback_until,
    *_args,
) -> None:
    callback = config.get("callback")
    seconds_between_calls = config.get("seconds_between_calls", None)
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if callback is not None:
        callback_until(
            sprite,
            callback=callback,
            condition=condition_callable,
            seconds_between_calls=seconds_between_calls,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_delay_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    _tween_until,
    _scale_until,
    _callback_until,
    delay_until,
    *_args,
) -> None:
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    delay_until(
        sprite,
        condition=condition_callable,
        on_stop=on_stop,
        tag=tag,
    )


def _apply_emit_particles_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    _tween_until,
    _scale_until,
    _callback_until,
    _delay_until,
    emit_particles_until,
    *_args,
) -> None:
    emitter_factory = config.get("emitter_factory")
    anchor = config.get("anchor", "center")
    follow_rotation = config.get("follow_rotation", False)
    start_paused = config.get("start_paused", False)
    destroy_on_stop = config.get("destroy_on_stop", True)
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if emitter_factory is not None:
        emit_particles_until(
            sprite,
            emitter_factory=emitter_factory,
            condition=condition_callable,
            anchor=anchor,
            follow_rotation=follow_rotation,
            start_paused=start_paused,
            destroy_on_stop=destroy_on_stop,
            on_stop=on_stop,
            tag=tag,
        )


def _apply_glow_until(
    sprite: arcade.Sprite,
    config: dict[str, Any],
    condition_callable: Callable[[], bool] | None,
    resolver: Callable[[str], Any] | None,
    _move_until,
    _follow_path_until,
    _cycle_textures_until,
    _fade_until,
    _blink_until,
    _rotate_until,
    _tween_until,
    _scale_until,
    _callback_until,
    _delay_until,
    _emit_particles_until,
    glow_until,
) -> None:
    shadertoy_factory = config.get("shadertoy_factory")
    uniforms_provider = config.get("uniforms_provider", None)
    get_camera_bottom_left = config.get("get_camera_bottom_left", None)
    auto_resize = config.get("auto_resize", True)
    tag = config.get("tag", None)
    on_stop = resolve_callback(config.get("on_stop", None), resolver)
    if shadertoy_factory is not None:
        glow_until(
            sprite,
            shadertoy_factory=shadertoy_factory,
            condition=condition_callable,
            uniforms_provider=uniforms_provider,
            get_camera_bottom_left=get_camera_bottom_left,
            auto_resize=auto_resize,
            on_stop=on_stop,
            tag=tag,
        )
