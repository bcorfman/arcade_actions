"""Shared contract tests covering common Action behaviors.

These tests focus on behaviors that should be identical across multiple
derived ``Action`` types (e.g. ``clone()`` preserving configuration).  The
goal is to avoid repeating the same assertions in every action specific test
module.
"""

from __future__ import annotations

import arcade
import pytest

from actions import Action, duration
from actions.conditional import (
    BlinkUntil,
    CallbackUntil,
    CycleTexturesUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    ParametricMotionUntil,
    RotateUntil,
    ScaleUntil,
    TweenUntil,
)
from actions.debug import MotionDebugger
from actions.instant import MoveBy, MoveTo


def _make_texture(name: str) -> arcade.Texture:
    """Create a tiny solid-colour texture for CycleTexturesUntil tests."""

    color = (255, 0, 0, 255)
    return arcade.Texture.create_empty(f"clone_contract_{name}", (2, 2), color)


def _make_condition_false():
    return lambda: False


def _noop(*_args, **_kwargs):
    return None


def _identity(value):
    return value


def _assert_equal(actual, expected):
    assert actual == expected


CLONE_CASES: list[pytest.Param] = [
    pytest.param(
        lambda: MoveUntil(
            (12.5, -3.25),
            _make_condition_false(),
            on_stop=_noop,
            bounds=(0, 0, 640, 480),
            boundary_behavior="wrap",
            velocity_provider=lambda: (1.0, 2.0),
            on_boundary_enter=_noop,
            on_boundary_exit=_noop,
        ),
        lambda action, cloned: (
            _assert_equal(cloned.target_velocity, action.target_velocity),
            _assert_equal(cloned.bounds, action.bounds),
            _assert_equal(cloned.boundary_behavior, action.boundary_behavior),
            _assert_equal(cloned.velocity_provider, action.velocity_provider),
            _assert_equal(cloned.on_boundary_enter, action.on_boundary_enter),
            _assert_equal(cloned.on_boundary_exit, action.on_boundary_exit),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="move_until",
    ),
    pytest.param(
        lambda: FollowPathUntil(
            [(0, 0), (100, 100), (150, 50)],
            120.0,
            _make_condition_false(),
            on_stop=_noop,
            rotate_with_path=True,
            rotation_offset=-90.0,
        ),
        lambda action, cloned: (
            _assert_equal(cloned.control_points, action.control_points),
            _assert_equal(cloned.target_velocity, action.target_velocity),
            _assert_equal(cloned.rotate_with_path, action.rotate_with_path),
            _assert_equal(cloned.rotation_offset, action.rotation_offset),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="follow_path_until",
    ),
    pytest.param(
        lambda: RotateUntil(45.0, _make_condition_false(), on_stop=_noop),
        lambda action, cloned: (
            _assert_equal(cloned.target_angular_velocity, action.target_angular_velocity),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="rotate_until",
    ),
    pytest.param(
        lambda: ScaleUntil((1.2, 0.75), _make_condition_false(), on_stop=_noop),
        lambda action, cloned: (
            _assert_equal(cloned.target_scale_velocity, action.target_scale_velocity),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="scale_until",
    ),
    pytest.param(
        lambda: FadeUntil(-25.0, _make_condition_false(), on_stop=_noop),
        lambda action, cloned: (
            _assert_equal(cloned.target_fade_velocity, action.target_fade_velocity),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="fade_until",
    ),
    pytest.param(
        lambda: BlinkUntil(
            0.5,
            _make_condition_false(),
            on_stop=_noop,
            on_blink_enter=_identity,
            on_blink_exit=_identity,
        ),
        lambda action, cloned: (
            _assert_equal(cloned.target_seconds_until_change, action.target_seconds_until_change),
            _assert_equal(cloned.on_blink_enter, action.on_blink_enter),
            _assert_equal(cloned.on_blink_exit, action.on_blink_exit),
        ),
        id="blink_until",
    ),
    pytest.param(
        lambda: DelayUntil(duration(0.25), on_stop=_noop),
        lambda action, cloned: (_assert_equal(cloned.on_stop, action.on_stop),),
        id="delay_until",
    ),
    pytest.param(
        lambda: TweenUntil(
            0.0,
            100.0,
            "center_x",
            duration(1.0),
            on_stop=_noop,
            ease_function=lambda t: t * t,
        ),
        lambda action, cloned: (
            _assert_equal(cloned.start_value, action.start_value),
            _assert_equal(cloned.end_value, action.end_value),
            _assert_equal(cloned.property_name, action.property_name),
            _assert_equal(cloned.ease_function, action.ease_function),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="tween_until",
    ),
    pytest.param(
        lambda: CallbackUntil(
            _noop,
            duration(0.5),
            on_stop=_noop,
            seconds_between_calls=0.2,
        ),
        lambda action, cloned: (
            _assert_equal(cloned.callback, action.callback),
            _assert_equal(cloned.target_seconds_between_calls, action.target_seconds_between_calls),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="callback_until",
    ),
    pytest.param(
        lambda: ParametricMotionUntil(
            lambda t: (t * 10.0, t * 5.0),
            duration(1.5),
            on_stop=_noop,
            explicit_duration=1.5,
            rotate_with_path=True,
            rotation_offset=15.0,
            debug=True,
            debug_threshold=42.0,
        ),
        lambda action, cloned: (
            _assert_equal(cloned._offset_fn, action._offset_fn),
            _assert_equal(cloned.rotate_with_path, action.rotate_with_path),
            _assert_equal(cloned.rotation_offset, action.rotation_offset),
            _assert_equal(cloned._duration, action._duration),
            _assert_equal(cloned._debug, action._debug),
            _assert_equal(cloned._debug_threshold, action._debug_threshold),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="parametric_motion_until",
    ),
    pytest.param(
        lambda: CycleTexturesUntil(
            [_make_texture("0"), _make_texture("1"), _make_texture("2")],
            frames_per_second=24.0,
            direction=-1,
            condition=duration(0.75),
            on_stop=_noop,
        ),
        lambda action, cloned: (
            _assert_equal(cloned._textures, action._textures),
            _assert_equal(cloned._fps, action._fps),
            _assert_equal(cloned._direction, action._direction),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="cycle_textures_until",
    ),
    pytest.param(
        lambda: MoveTo((320, 240), on_stop=_noop),
        lambda action, cloned: (
            _assert_equal(cloned.target_position, action.target_position),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="move_to",
    ),
    pytest.param(
        lambda: MoveBy((15, -5), on_stop=_noop),
        lambda action, cloned: (
            _assert_equal(cloned.offset, action.offset),
            _assert_equal(cloned.on_stop, action.on_stop),
        ),
        id="move_by",
    ),
    pytest.param(
        lambda: MotionDebugger(threshold=55.0),
        lambda action, cloned: (_assert_equal(cloned.threshold, action.threshold),),
        id="motion_debugger",
    ),
]


@pytest.mark.parametrize("factory, assertion_fn", CLONE_CASES)
def test_action_clone_contract(factory, assertion_fn):
    """All actions should return a structurally identical clone."""

    action = factory()
    cloned = action.clone()

    assert type(cloned) is type(action)
    assert cloned is not action

    # Perform action-specific assertions supplied by the test case
    assertion_fn(action, cloned)


SET_FACTOR_CASES = [
    pytest.param(
        lambda sprite: MoveUntil((10.0, -4.0), lambda: False),
        lambda action: action.current_velocity,
        {0.0: (0.0, 0.0), 0.5: (5.0, -2.0), -1.0: (-10.0, 4.0)},
        id="move_until",
    ),
    pytest.param(
        lambda sprite: RotateUntil(90.0, lambda: False),
        lambda action: action.current_angular_velocity,
        {0.0: 0.0, 0.5: 45.0, 2.0: 180.0},
        id="rotate_until",
    ),
    pytest.param(
        lambda sprite: ScaleUntil((1.0, 2.0), lambda: False),
        lambda action: action.current_scale_velocity,
        {0.0: (0.0, 0.0), 0.5: (0.5, 1.0), 2.0: (2.0, 4.0)},
        id="scale_until",
    ),
    pytest.param(
        lambda sprite: FadeUntil(-40.0, lambda: False),
        lambda action: action.current_fade_velocity,
        {0.0: 0.0, 0.5: -20.0, -1.0: 40.0},
        id="fade_until",
    ),
    pytest.param(
        lambda sprite: FollowPathUntil(
            [(0, 0), (100, 50), (200, 0)],
            120.0,
            lambda: False,
        ),
        lambda action: action.current_velocity,
        {0.0: 0.0, 0.5: 60.0, 2.0: 240.0},
        id="follow_path_until",
    ),
    pytest.param(
        lambda sprite: BlinkUntil(0.5, lambda: False),
        lambda action: action.current_seconds_until_change,
        {2.0: 0.25, 0.5: 1.0, 0.0: float("inf"), -1.0: float("inf")},
        id="blink_until",
    ),
    pytest.param(
        lambda sprite: CallbackUntil(
            _noop,
            duration(1.0),
            seconds_between_calls=0.2,
        ),
        lambda action: action.current_seconds_between_calls,
        {2.0: 0.1, 1.0: 0.2, 0.0: float("inf"), -1.0: float("inf")},
        id="callback_until",
    ),
    pytest.param(
        lambda sprite: CycleTexturesUntil(
            [_make_texture("a"), _make_texture("b")],
            frames_per_second=30.0,
            direction=1,
            condition=duration(1.0),
        ),
        lambda action: action._factor,
        {0.0: 0.0, 2.0: 2.0},
        id="cycle_textures_until",
    ),
    pytest.param(
        lambda sprite: TweenUntil(0.0, 10.0, "center_x", duration(1.0)),
        lambda action: action._factor,
        {0.0: 0.0, 1.0: 1.0, 2.0: 2.0},
        id="tween_until",
    ),
    pytest.param(
        lambda sprite: ParametricMotionUntil(
            lambda t: (t * 5.0, t * 2.5),
            duration(1.0),
            explicit_duration=1.0,
        ),
        lambda action: action._factor,
        {0.0: 0.0, 0.5: 0.5, 2.0: 2.0},
        id="parametric_motion_until",
    ),
]


@pytest.mark.parametrize("factory, value_getter, expectations", SET_FACTOR_CASES)
def test_action_set_factor_contract(factory, value_getter, expectations, test_sprite):
    Action.stop_all()

    action = factory(test_sprite)
    if isinstance(action, Action) and action.target is None:
        action.apply(test_sprite)

    for factor, expected in expectations.items():
        action.set_factor(factor)
        actual = value_getter(action)

        if isinstance(expected, tuple):
            assert actual == pytest.approx(expected)
        else:
            if expected == float("inf"):
                assert actual == float("inf")
            else:
                assert actual == pytest.approx(expected)

    Action.stop_all()
