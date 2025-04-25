import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import FadeIn, FadeOut, FadeTo, ScaleBy, ScaleTo


class DummyTexture:
    width = 1
    height = 1


def create_sprite():
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.alpha = 255
    sprite.scale = 1.0
    return sprite


def test_fade_out_then_in():
    sprite = create_sprite()
    sprite.do(FadeOut(1.0) + FadeIn(1.0))

    for _ in range(120):
        sprite.update(1 / 60.0)

    assert sprite.alpha == 255


def test_fade_to_mid_alpha():
    sprite = create_sprite()
    sprite.alpha = 200
    sprite.do(FadeTo(100, 1.0))

    for _ in range(60):
        sprite.update(1 / 60.0)

    assert sprite.alpha == pytest.approx(100, abs=5)


def test_scale_to_final_size():
    sprite = create_sprite()
    sprite.scale = 1.0
    sprite.do(ScaleTo(2.0, 1.0))

    for _ in range(60):
        sprite.update(1 / 60.0)

    assert sprite.scale == pytest.approx(2.0, abs=0.05)


def test_scale_by_and_reverse():
    sprite = create_sprite()
    sprite.scale = 1.0
    sprite.do(ScaleBy(3.0, 1.0) + ScaleBy(1 / 3.0, 1.0))

    for _ in range(120):
        sprite.update(1 / 60.0)

    assert sprite.scale == pytest.approx(1.0, abs=0.05)
