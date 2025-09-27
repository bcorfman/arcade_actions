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
from typing import Any

import arcade
from arcade import easing

from actions import (
    Action,
    BlinkUntil,
    CallbackUntil,
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


def move_by(target: SpriteTarget, *, dx_or_offset, dy=None, on_stop: Any | None = None):
    """Instantly offset a sprite or all sprites in a sprite list by (dx, dy).

    Usage:
        move_by(sprite, (dx, dy))
        move_by(sprite_list, dx, dy)      # Also accepts separate arguments for convenience
    """
    from actions.instant import MoveBy

    action = MoveBy(dx_or_offset, dy, on_stop=on_stop)
    action.apply(target)
    return action


def move_to(target: SpriteTarget, *, x_or_position, y=None, on_stop: Any | None = None):
    """Instantly move a sprite or all sprites in a sprite list to an absolute position.
    Probably not useful for a sprite list. but there you go.

    Usage:
        move_to(sprite, (x, y))
        move_to(sprite, x, y)      # Also accepts separate arguments for convenience
    """
    from actions.instant import MoveTo

    action = MoveTo(x_or_position, y, on_stop=on_stop)
    action.apply(target)
    return action


def move_until(
    target: SpriteTarget,
    *,
    velocity: tuple[float, float],
    condition: Callable[[], Any],
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    velocity_provider: Callable[[], tuple[float, float]] | None = None,
    on_boundary_enter: Callable[[Any, str, str], None] | None = None,
    on_boundary_exit: Callable[[Any, str, str], None] | None = None,
    **kwargs,
) -> MoveUntil:
    """
    Creates and applies a MoveUntil action to the target.

    This is a convenience wrapper for the MoveUntil class that immediately applies
    the action to the target sprite or sprite list.

    Args:
        target: The sprite (arcade.Sprite) or sprite list (arcade.SpriteList) to move.
        velocity: The (dx, dy) velocity.
        condition: The condition to stop moving.
        on_stop: An optional callback to run when the condition is met.
        tag: An optional tag for the action.
        velocity_provider: Optional function returning (dx, dy) velocity each frame.
        on_boundary_enter: Optional callback(sprite, axis, side) for boundary enter events.
        on_boundary_exit: Optional callback(sprite, axis, side) for boundary exit events.
        **kwargs: Additional arguments passed to MoveUntil (bounds, boundary_behavior, etc.)

    Returns:
        The created MoveUntil action instance.

    Example:
        # Basic movement
        move_until(sprite, velocity=(5, 0), condition=lambda: sprite.center_x > 500)

        # With boundary callbacks
        move_until(
            sprite,
            velocity=(10, 0),
            condition=infinite,
            bounds=(0, 0, 800, 600),
            boundary_behavior="bounce",
            on_boundary_enter=lambda s, axis, side: print(f"Hit {side} {axis} boundary"),
            on_boundary_exit=lambda s, axis, side: print(f"Left {side} {axis} boundary")
        )
    """
    action = MoveUntil(
        velocity=velocity,
        condition=condition,
        on_stop=on_stop,
        velocity_provider=velocity_provider,
        on_boundary_enter=on_boundary_enter,
        on_boundary_exit=on_boundary_exit,
        **kwargs,
    )
    action.apply(target, tag=tag)
    return action


def rotate_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    angular_velocity: float,
    condition: Callable[[], Any],
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> RotateUntil:
    """
    Creates and applies a RotateUntil action to the target.

    This is a convenience wrapper for the RotateUntil class that immediately applies
    the action to the target sprite or sprite list.

    Args:
        target: The sprite (arcade.Sprite) or sprite list (arcade.SpriteList) to rotate.
        angular_velocity: The angular velocity.
        condition: The condition to stop rotating.
        on_stop: An optional callback.
        tag: An optional tag.

    Returns:
        The created RotateUntil action instance.

    Example:
        rotate_until(sprite, angular_velocity=180, condition=duration(1.0))
    """
    action = RotateUntil(angular_velocity=angular_velocity, condition=condition, on_stop=on_stop, **kwargs)
    action.apply(target, tag=tag)
    return action


def follow_path_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    control_points: list[tuple[float, float]],
    velocity: float,
    condition: Callable[[], Any],
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
    **kwargs,
) -> FollowPathUntil:
    """
    Creates and applies a FollowPathUntil action to the target.

    This is a convenience wrapper for the FollowPathUntil class that immediately applies
    the action to the target sprite or sprite list.

    Args:
        target: The sprite (arcade.Sprite) or sprite list (arcade.SpriteList) to follow the path.
        control_points: The control points defining the path.
        velocity: The velocity along the path.
        condition: The condition to stop following the path.
        on_stop: An optional callback.
        tag: An optional tag.

    Returns:
        The created FollowPathUntil action instance.

    Example:
        path_points = [(100, 100), (200, 200), (300, 100)]
        follow_path_until(sprite, path_points, velocity=200, condition=duration(3.0))
    """
    action = FollowPathUntil(
        control_points=control_points,
        velocity=velocity,
        condition=condition,
        on_stop=on_stop,
        **kwargs,
    )
    action.apply(target, tag=tag)
    return action


def blink_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    seconds_until_change: float,
    condition: Callable[[], Any],
    on_stop: Callable = None,
    on_blink_enter: Callable[[Any], None] | None = None,
    on_blink_exit: Callable[[Any], None] | None = None,
    tag: str | None = None,
) -> BlinkUntil:
    """Creates and applies a BlinkUntil action with optional visibility callbacks.

    Args:
        target: Sprite or SpriteList to apply blinking to
        seconds_until_change: Seconds to wait before toggling visibility
        condition: Function that returns truthy value when blinking should stop
        on_stop: Optional callback called when condition is satisfied
        on_blink_enter: Optional callback(target) when visibility toggles to True
        on_blink_exit: Optional callback(target) when visibility toggles to False
        tag: Optional tag for the action

    Returns:
        The BlinkUntil action that was created and applied
    """
    action = BlinkUntil(
        seconds_until_change=seconds_until_change,
        condition=condition,
        on_stop=on_stop,
        on_blink_enter=on_blink_enter,
        on_blink_exit=on_blink_exit,
    )
    action.apply(target, tag=tag)
    return action


def delay_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    condition: Callable[[], Any],
    on_stop: Callable = None,
    tag: str | None = None,
) -> DelayUntil:
    """Creates and applies a DelayUntil action."""
    action = DelayUntil(condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def tween_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    start_value: float,
    end_value: float,
    property_name: str,
    condition: Callable[[], Any],
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
    target: arcade.Sprite | arcade.SpriteList,
    *,
    velocity: tuple[float, float] | float,
    condition: Callable[[], Any],
    on_stop: Callable = None,
    tag: str | None = None,
) -> ScaleUntil:
    """Creates and applies a ScaleUntil action."""
    action = ScaleUntil(scale_velocity=velocity, condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def fade_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    velocity: float,
    condition: Callable[[], Any],
    on_stop: Callable = None,
    tag: str | None = None,
) -> FadeUntil:
    """Creates and applies a FadeUntil action."""
    action = FadeUntil(fade_velocity=velocity, condition=condition, on_stop=on_stop)
    action.apply(target, tag=tag)
    return action


def callback_until(
    target: SpriteTarget,
    *,
    callback: Callable[..., None],
    condition: Callable[[], Any],
    seconds_between_calls: float | None = None,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
) -> CallbackUntil:
    """Creates and applies a CallbackUntil action to the target.

    Args:
        target: Sprite or SpriteList the callback pertains to (passed as argument)
        callback: Function called per frame or per interval; receives target when signature allows
        condition: Function that returns truthy value when callbacks should stop
        seconds_between_calls: Optional seconds between calls; None → every frame
        on_stop: Optional callback called when condition is satisfied
        tag: Optional tag for the action

    Returns:
        The CallbackUntil action that was created and applied
    """
    action = CallbackUntil(
        callback=callback,
        condition=condition,
        seconds_between_calls=seconds_between_calls,
        on_stop=on_stop,
    )
    action.apply(target, tag=tag)
    return action


def ease(
    target: arcade.Sprite | arcade.SpriteList,
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


def cycle_textures_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    textures: list,
    frames_per_second: float = 60.0,
    direction: int = 1,
    condition: Callable[[], Any] = None,
    on_stop: Callable[[Any], None] | Callable[[], None] | None = None,
    tag: str | None = None,
) -> CycleTexturesUntil:
    """Creates and applies a CycleTexturesUntil action to the target.

    This is a convenience wrapper for the CycleTexturesUntil class that immediately applies
    the action to the target sprite or sprite list.

    Args:
        target: The sprite (arcade.Sprite) or sprite list (arcade.SpriteList) to animate.
        textures: List of arcade.Texture objects to cycle through.
        frames_per_second: How many texture indices to advance per second (default: 60.0).
        direction: Direction of cycling - 1 for forward, -1 for backward (default: 1).
        condition: The condition to stop cycling. If None, cycles infinitely.
        on_stop: An optional callback to run when the condition is met.
        tag: An optional tag for the action.

    Returns:
        The created CycleTexturesUntil action instance.

    Example:
        # Simple infinite texture cycling
        cycle_textures_until(sprite, textures=texture_list)

        # Cycle backward for 3 seconds
        cycle_textures_until(
            sprite,
            textures=texture_list,
            direction=-1,
            condition=duration(3.0)
        )
    """
    from actions.conditional import CycleTexturesUntil, infinite

    if condition is None:
        condition = infinite

    action = CycleTexturesUntil(
        textures=textures,
        frames_per_second=frames_per_second,
        direction=direction,
        condition=condition,
        on_stop=on_stop,
    )
    action.apply(target, tag=tag)
    return action
