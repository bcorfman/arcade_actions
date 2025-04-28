import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import FadeTo, MoveBy, ScaleTo


def make_test_sprite(x=0, y=0):
    sprite = ActionSprite(filename=None)
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = x
    sprite.center_y = y
    sprite.alpha = 255
    sprite.scale = 1.0
    return sprite


def test_stop_clears_velocity():
    sprite = make_test_sprite()
    action = MoveBy((100, 0), 2.0)
    sprite.do(action)

    # Run to near completion but not fully finished
    for _ in range(59):
        sprite.update(1 / 60)

    # Now manually stop
    for a in sprite._actions:
        a.stop()

    assert sprite.change_x == pytest.approx(0.0)
    assert sprite.change_y == pytest.approx(0.0)


def test_stop_finalizes_alpha():
    sprite = make_test_sprite()
    action = FadeTo(100, 2.0)
    sprite.do(action)

    # Step partially
    for _ in range(30):
        sprite.update(1 / 60)

    # Force stop
    for a in sprite._actions:
        a.stop()

    assert sprite.alpha == pytest.approx(100, abs=2)


def test_stop_finalizes_scale():
    sprite = make_test_sprite()
    action = ScaleTo(2.0, 2.0)
    sprite.do(action)

    for _ in range(30):
        sprite.update(1 / 60)

    for a in sprite._actions:
        a.stop()

    assert sprite.scale == pytest.approx(2.0, abs=0.05)
