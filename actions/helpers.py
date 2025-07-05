"""
This module provides thin convenience wrappers for the main Action classes,
making the API more intuitive by prioritizing the target of the action first.

For example, instead of:
    action = MoveUntil((5, 0), lambda: False)
    action.apply(sprite)

You can write:
    move_until(sprite, (5, 0), lambda: False)

This improves readability while still returning the action instance for
potential chaining or modification.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, overload

import arcade

from actions.base import Action
from actions.conditional import (
    BlinkUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    TweenUntil,
)
from actions.easing import Ease

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

       move_until(sprite, (5, 0), lambda: sprite.center_x > 500)

    2. Without a target: Creates a "raw" MoveUntil action that is not yet applied
       to any target. This is useful for creating reusable action templates.

       template_move = move_until((10, 0), some_condition)
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

    action = MoveUntil(final_velocity, final_condition, on_condition_met=on_stop, **kwargs)

    if final_target:
        action.apply(final_target, tag=tag)

    return action


@overload
def rotate_until(
    angular_velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil: ...


@overload
def rotate_until(
    target: SpriteTarget,
    angular_velocity: float,
    condition: Callable[[], Any],
    *,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil: ...


def rotate_until(
    target: SpriteTarget | float,
    angular_velocity: float | Callable[[], Any],
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
        target: The sprite/list to rotate, or the angular velocity if used w/o a target.
        angular_velocity: The angular velocity, or the condition if used w/o a target.
        condition: The condition to stop rotating.
        on_stop: An optional callback.
        tag: An optional tag.

    Returns:
        The created RotateUntil action instance.
    """
    final_target: SpriteTarget | None = None
    final_angular_velocity: float
    final_condition: Callable[[], Any]

    if callable(angular_velocity):
        # Overload 1: rotate_until(angular_velocity, condition, ...)
        if not isinstance(target, (int, float)):
            raise TypeError("Expected angular_velocity as the first argument when no target is provided.")
        final_angular_velocity = target
        final_condition = angular_velocity
    else:
        # Overload 2: rotate_until(target, angular_velocity, condition, ...)
        if not condition:
            raise TypeError("A condition function must be provided.")
        if not isinstance(target, (arcade.Sprite, arcade.SpriteList)):
            raise TypeError("Expected a Sprite or SpriteList as the first argument.")
        if not isinstance(angular_velocity, (int, float)):
            raise TypeError("Expected angular_velocity as the second argument.")

        final_target = target
        final_angular_velocity = angular_velocity
        final_condition = condition

    action = RotateUntil(final_angular_velocity, final_condition, on_condition_met=on_stop, **kwargs)

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

    action = FollowPathUntil(final_control_points, final_velocity, final_condition, on_condition_met=on_stop, **kwargs)

    if final_target:
        action.apply(final_target, tag=tag)

    return action


def blink_until(
    target: SpriteTarget,
    time: float,
    condition_func: Callable[[], Any],
    on_condition_met: Callable = None,
    tag: str | None = None,
) -> BlinkUntil:
    action = BlinkUntil(time, condition_func, on_condition_met)
    action.apply(target, tag=tag)
    return action


def delay_until(
    target: SpriteTarget, condition_func: Callable[[], Any], on_condition_met: Callable = None, tag: str | None = None
) -> DelayUntil:
    action = DelayUntil(condition_func, on_condition_met)
    action.apply(target, tag=tag)
    return action


def tween_until(
    target: SpriteTarget,
    start_value: float,
    end_value: float,
    property_name: str,
    condition_func: Callable[[], Any],
    on_condition_met: Callable = None,
    ease_function=arcade.easing.linear,
    tag: str | None = None,
) -> TweenUntil:
    action = TweenUntil(
        start_value, end_value, property_name, condition_func, on_condition_met, ease_function=ease_function
    )
    action.apply(target, tag=tag)
    return action


def scale_until(
    target: SpriteTarget,
    scale_velocity: tuple[float, float] | float,
    condition_func: Callable[[], Any],
    on_condition_met: Callable = None,
    tag: str | None = None,
) -> ScaleUntil:
    action = ScaleUntil(scale_velocity, condition_func, on_condition_met)
    action.apply(target, tag=tag)
    return action


def fade_until(
    target: SpriteTarget,
    fade_velocity: float,
    condition_func: Callable[[], Any],
    on_condition_met: Callable = None,
    tag: str | None = None,
) -> FadeUntil:
    action = FadeUntil(fade_velocity, condition_func, on_condition_met)
    action.apply(target, tag=tag)
    return action


def ease(
    target: SpriteTarget, action: Action, seconds: float, ease_function=arcade.easing.linear, tag: str | None = None
) -> Ease:
    eased_action = Ease(action, seconds, ease_function=ease_function)
    eased_action.apply(target, tag=tag)
    return eased_action
