import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import AccelDecel, Accelerate, Lerp, MoveBy, Speed


class DummyTexture:
    width = 1
    height = 1


def create_sprite():
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = 0
    sprite.center_y = 0
    sprite.angle = 0
    sprite.scale = 1.0
    sprite.alpha = 255
    return sprite


def test_speed_scales_inner_action_duration():
    sprite = create_sprite()
    move = MoveBy((60, 0), 1.0)
    fast = Speed(move, speed=2.0)  # duration becomes 0.5
    sprite.do(fast)

    for _ in range(30):  # 0.5 seconds @ 60 FPS
        sprite.update(1 / 60.0)

    assert sprite.change_x == pytest.approx(0.0)
    assert fast.is_done()


def test_accelerate_applies_curve():
    sprite = create_sprite()
    move = MoveBy((60, 0), 1.0)
    curved = Accelerate(move, rate=3.0)
    sprite.do(curved)

    t_early = []
    for i in range(30):  # first 0.5 seconds
        sprite.update(1 / 60.0)
        t_early.append(sprite.change_x)
    assert t_early[0] < t_early[-1]


def test_acceldecel_symmetric_velocity():
    sprite = create_sprite()
    move = MoveBy((60, 0), 1.0)
    smoothed = AccelDecel(move)
    sprite.do(smoothed)

    half1, half2 = [], []
    for i in range(60):
        sprite.update(1 / 60.0)
        if i < 30:
            half1.append(sprite.change_x)
        else:
            half2.append(sprite.change_x)

    # Motion should rise and fall symmetrically
    assert max(half1) == pytest.approx(max(half2), abs=2.0)


def test_lerp_angle_over_time():
    sprite = create_sprite()
    sprite.angle = 10
    sprite.do(Lerp("angle", 190, 1.0))

    for _ in range(60):
        sprite.update(1 / 60.0)

    assert sprite.angle == pytest.approx(190, abs=1.0)
