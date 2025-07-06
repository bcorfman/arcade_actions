"""
This module provides thin convenience wrappers for the main Action classes,
making the API more intuitive by prioritizing the target of the action first.

For example, instead of:
    action = MoveUntil(velocity=(5, 0), condition=lambda: False)
    action.apply(sprite)

You can write:
    move_until(sprite, velocity=(5, 0), condition=lambda: False)

This improves readability while still returning the action instance for
potential chaining or modification.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, overload

import arcade
from arcade import easing

from actions import (
    Action,
    BlinkUntil,
    DelayUntil,
    Ease,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    TweenUntil,
)

SpriteTarget = arcade.Sprite | arcade.SpriteList


@overload
def move_until(
    velocity: tuple[float, float],
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> MoveUntil: ...


@overload
def move_until(
    target: SpriteTarget,
    velocity: tuple[float, float],
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> MoveUntil: ...


def move_until(
    target: SpriteTarget | tuple[float, float],
    velocity: tuple[float, float] | Callable[[], Any],
    condition: Callable[[], Any] | None = None,
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> MoveUntil:
    """
    Creates and optionally applies a MoveUntil action.

    This is a convenience wrapper for the MoveUntil class. It can be used in two ways:

    1. With a target: Creates a MoveUntil action and immediately applies it to the
       target sprite or sprite list. This is the recommended, more readable usage.

       move_until(sprite, velocity=(5, 0), condition=lambda: sprite.center_x > 500)

    2. Without a target: Creates a "raw" MoveUntil action that is not yet applied
       to any target. This is useful for creating reusable action templates.

       template_move = move_until(velocity=(10, 0), condition=some_condition)
       template_move.apply(enemy1)
       template_move.clone().apply(enemy2)

    Args:
        target: The sprite or sprite list to move, or the velocity if used w/o a target.
        velocity: The (dx, dy) velocity, or the condition if used w/o a target.
        condition: The condition to stop moving.
        on_stop: An optional callback to run when the condition is met.
        tag: An optional tag for the action.

    Returns:
        The created MoveUntil action instance.
    """
    final_target: SpriteTarget | None = None
    final_velocity: tuple[float, float]
    final_condition: Callable[[], Any]

    if callable(velocity):
        # Overload 1: move_until(velocity, condition, ...)
        if not isinstance(target, tuple):
            raise TypeError("Expected velocity as the first argument (a tuple) when no target is provided.")
        final_velocity = target
        final_condition = velocity
    else:
        # Overload 2: move_until(target, velocity, condition, ...)
        if not condition:
            raise TypeError("A condition function must be provided.")
        if not isinstance(target, (arcade.Sprite, arcade.SpriteList)):
            raise TypeError("Expected a Sprite or SpriteList as the first argument.")
        if not isinstance(velocity, tuple):
            raise TypeError("Expected velocity as the second argument (a tuple).")

        final_target = target
        final_velocity = velocity
        final_condition = condition

    action = MoveUntil(velocity=final_velocity, condition=final_condition, on_stop=on_stop, **kwargs)

    if final_target:
        action.apply(final_target, tag=tag)

    return action


@overload
def rotate_until(
    velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil: ...


@overload
def rotate_until(
    target: SpriteTarget,
    velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil: ...


def rotate_until(
    target: SpriteTarget | float,
    velocity: float | Callable[[], Any],
    condition: Callable[[], Any] | None = None,
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil:
    """
    Creates and optionally applies a RotateUntil action.

    See `move_until` for detailed usage patterns.

    Args:
        target: The sprite/list to rotate, or the velocity if used w/o a target.
        velocity: The angular velocity, or the condition if used w/o a target.
        condition: The condition to stop rotating.
        on_stop: An optional callback.
        tag: An optional tag.

    Returns:
        The created RotateUntil action instance.
    """
    final_target: SpriteTarget | None = None
    final_velocity: float
    final_condition: Callable[[], Any]

    if callable(velocity):
        # Overload 1: rotate_until(velocity, condition, ...)
        if not isinstance(target, (int, float)):
            raise TypeError("Expected velocity as the first argument when no target is provided.")
        final_velocity = target
        final_condition = velocity
    else:
        # Overload 2: rotate_until(target, velocity, condition, ...)
        if not condition:
            raise TypeError("A condition function must be provided.")
        if not isinstance(target, (arcade.Sprite, arcade.SpriteList)):
            raise TypeError("Expected a Sprite or SpriteList as the first argument.")
        if not isinstance(velocity, (int, float)):
            raise TypeError("Expected velocity as the second argument.")

        final_target = target
        final_velocity = velocity
        final_condition = condition

    action = RotateUntil(angular_velocity=final_velocity, condition=final_condition, on_stop=on_stop, **kwargs)

    if final_target:
        action.apply(final_target, tag=tag)

    return action


@overload
def follow_path_until(
    control_points: list[tuple[float, float]],
    velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> FollowPathUntil: ...


@overload
def follow_path_until(
    target: SpriteTarget,
    control_points: list[tuple[float, float]],
    velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> FollowPathUntil: ...


def follow_path_until(
    target: SpriteTarget | list[tuple[float, float]],
    control_points: list[tuple[float, float]] | float | Callable[[], Any],
    velocity: float | Callable[[], Any] | None = None,
    condition: Callable[[], Any] | None = None,
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> FollowPathUntil:
    """
    Creates and optionally applies a FollowPathUntil action.

    See `move_until` for detailed usage patterns.

    Args:
        target: The sprite/list, or the control points if used w/o a target.
        control_points: The control points, or velocity if used w/o a target.
        velocity: The velocity, or condition if used w/o a target.
        condition: The condition to stop.
        on_stop: An optional callback.
        tag: An optional tag.

    Returns:
        The created FollowPathUntil action instance.
    """
    final_target: SpriteTarget | None = None
    final_control_points: list[tuple[float, float]]
    final_velocity: float
    final_condition: Callable[[], Any]

    if isinstance(target, list) and isinstance(control_points, (int, float)) and callable(velocity):
        # Overload 1: follow_path_until(control_points, velocity, condition, ...)
        final_control_points = target
        final_velocity = control_points
        final_condition = velocity
    else:
        # Overload 2: follow_path_until(target, control_points, velocity, condition, ...)
        if not condition or not velocity:
            raise TypeError("A velocity and condition function must be provided.")
        if not isinstance(target, (arcade.Sprite, arcade.SpriteList)):
            raise TypeError("Expected a Sprite or SpriteList as the first argument.")
        if not isinstance(control_points, list):
            raise TypeError("Expected control_points as the second argument.")
        if not isinstance(velocity, (int, float)):
            raise TypeError("Expected velocity as the third argument.")

        final_target = target
        final_control_points = control_points
        final_velocity = velocity
        final_condition = condition

    action = FollowPathUntil(
        control_points=final_control_points,
        velocity=final_velocity,
        condition=final_condition,
        on_stop=on_stop,
        **kwargs,
    )

    if final_target:
        action.apply(final_target, tag=tag)

    return action


def blink_until(
    target: SpriteTarget,
    time: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable = None,
    tag: str | None = None,
) -> BlinkUntil:
    """Creates and applies a BlinkUntil action."""
    action = BlinkUntil(seconds_until_change=time, condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def delay_until(
    target: SpriteTarget,
    condition: Callable[[], Any],
    *,
    on_stop: Callable = None,
    tag: str | None = None,
) -> DelayUntil:
    """Creates and applies a DelayUntil action."""
    action = DelayUntil(condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def tween_until(
    target: SpriteTarget,
    start_value: float,
    end_value: float,
    property_name: str,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> TweenUntil:
    """Creates and applies a TweenUntil action."""
    action = TweenUntil(
        start_value=start_value,
        end_value=end_value,
        property_name=property_name,
        condition=condition,
        on_stop=on_stop,
        **kwargs,
    )
    action.apply(target, tag=tag)
    return action


def scale_until(
    target: SpriteTarget,
    velocity: tuple[float, float] | float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable = None,
    tag: str | None = None,
) -> ScaleUntil:
    """Creates and applies a ScaleUntil action."""
    action = ScaleUntil(scale_velocity=velocity, condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def fade_until(
    target: SpriteTarget,
    velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable = None,
    tag: str | None = None,
) -> FadeUntil:
    """Creates and applies a FadeUntil action."""
    action = FadeUntil(fade_velocity=velocity, condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def ease(
    target: SpriteTarget,
    action: Action,
    duration: float,
    *,
    ease_function: Callable[[float], float] | None = easing.ease_in_out,
    on_complete: Callable[[], Any] | None = None,
    tag: str | None = None,
) -> Ease:
    """Creates and applies an Ease action."""
    ease_action = Ease(action, duration=duration, ease_function=ease_function, on_complete=on_complete, tag=tag)
    ease_action.apply(target, tag=tag)
    return ease_action
