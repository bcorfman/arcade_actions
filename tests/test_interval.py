from unittest.mock import Mock

from actions.base import ActionSprite
from actions.interval import (
    AccelDecel,
    Accelerate,
    Bezier,
    Blink,
    FadeIn,
    FadeOut,
    JumpBy,
    JumpTo,
    MoveBy,
    MoveTo,
    RotateBy,
    RotateTo,
    ScaleBy,
    ScaleTo,
)


def test_blink_action():
    sprite = Mock()
    sprite.alpha = 255
    action = Blink(times=2, duration=1)
    action.start(sprite)
    action.update(0.5)
    assert sprite.alpha == 0  # After first blink, invisible
    action.update(1.0)
    assert sprite.alpha == 255  # Second blink back to visible


def test_move_to_action():
    sprite = Mock()
    sprite.center_x, sprite.center_y = 0, 0  # Set numerical values
    action = MoveTo(x=100, y=100, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.center_x == 100
    assert sprite.center_y == 100


def test_move_by_action():
    sprite = Mock()
    sprite.center_x, sprite.center_y = 50, 50  # Numerical starting values
    action = MoveBy(dx=10, dy=20, duration=2)
    action.start(sprite)
    action.update(2)
    assert sprite.center_x == 70
    assert sprite.center_y == 90


def test_rotate_to_action():
    sprite = Mock()
    sprite.angle = 0
    action = RotateTo(angle=90, duration=1)  # Use the correct argument 'angle'
    action.start(sprite)
    action.update(1)
    assert sprite.angle == 90


def test_rotate_by_action():
    sprite = Mock()
    sprite.angle = 0
    action = RotateBy(delta_angle=90, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.angle == 90


def test_fade_in_action():
    sprite = Mock()
    sprite.alpha = 0
    action = FadeIn(duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.alpha == 255


def test_fade_out_action():
    sprite = Mock()
    sprite.alpha = 255
    action = FadeOut(duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.alpha == 0


def test_scale_to_action():
    sprite = Mock()
    sprite.scale = 1.0
    action = ScaleTo(scale=2.0, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.scale == 2.0


def test_scale_by_action():
    sprite = Mock()
    sprite.scale = 1.0
    action = ScaleBy(scale_factor=2.0, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.scale == 2.0


def test_accelerate_action():
    sprite = Mock()
    sprite.center_x, sprite.center_y = 0, 0
    move_action = MoveTo(x=100, y=100, duration=1)
    action = Accelerate(action=move_action)
    action.start(sprite)
    action.step(1.0)  # Complete
    assert sprite.center_x == 100 and sprite.center_y == 100


def test_accel_decel_action():
    # Create an instance of ActionSprite with the necessary properties
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0

    # Set up the MoveTo action and wrap it in AccelDecel
    move_action = MoveTo(x=100, y=100, duration=2)
    action = AccelDecel(action=move_action)

    # Start the action on the sprite and step with the total duration
    action.start(sprite)
    action.step(2)  # Complete the action over its entire duration

    # Check if the sprite reached the target position
    assert sprite.center_x == 100 and sprite.center_y == 100


def test_bezier_action():
    sprite = Mock()
    sprite.center_x, sprite.center_y = 0, 0
    control_points = [(0, 0), (50, 100), (100, 0)]
    action = Bezier(control_points=control_points, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.center_x == 100
    assert sprite.center_y == 0


def test_jump_to_action():
    sprite = Mock()
    sprite.center_x, sprite.center_y = 0, 0
    action = JumpTo(x=100, y=200, height=5, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.center_x == 100
    assert sprite.center_y == 200


def test_jump_by_action():
    sprite = Mock()
    sprite.center_x = 0
    sprite.center_y = 0
    action = JumpBy(dx=10, dy=20, height=5, duration=1)
    action.start(sprite)
    action.update(1)
    assert sprite.center_x == 10
    assert sprite.center_y == 20
