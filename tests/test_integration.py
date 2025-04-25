import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import MoveBy, RotateBy


def create_sprite(x=0, y=0):
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = x
    sprite.center_y = y
    return sprite


def test_moveby_over_time():
    sprite = create_sprite()
    sprite.do(MoveBy((150, 50), 2.0))

    dt = 1 / 60.0
    for _ in range(120):  # Simulate 2 seconds
        sprite.update(dt)

    assert sprite.center_x == pytest.approx(200.0, abs=1.0)
    assert sprite.center_y == pytest.approx(150.0, abs=1.0)


def test_rotateby_ends_at_correct_angle():
    sprite = create_sprite()
    sprite.do(RotateBy(180, 1.5))

    dt = 1 / 60.0
    for _ in range(90):  # 1.5 seconds
        sprite.update(dt)

    assert sprite.angle == pytest.approx(180.0, abs=2.0)
