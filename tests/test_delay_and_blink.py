import arcade
from PIL import Image

from actions.base import ActionSprite
from actions.interval import Blink, Delay, RandomDelay


class DummyTexture:
    width = 1
    height = 1


def create_sprite():
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.visible = True
    return sprite


def test_delay_ends_after_duration():
    sprite = create_sprite()
    action = Delay(1.0)
    sprite.do(action)

    assert not action.is_done()
    for _ in range(60):
        sprite.update(1 / 60.0)
    assert action.is_done()


def test_randomdelay_duration_variability():
    sprite = create_sprite()
    action = RandomDelay(0.5, 1.0)
    sprite.do(action)
    duration = action.duration
    assert 0.5 <= duration <= 1.0

    for _ in range(int(duration / (1 / 60.0)) + 5):
        sprite.update(1 / 60.0)
    assert action.is_done()


def test_blink_toggles_visibility():
    sprite = create_sprite()
    sprite.visible = True
    sprite.do(Blink(times=4, duration=2.0))

    toggles = []
    for _ in range(120):  # 2 seconds @ 60 FPS
        sprite.update(1 / 60.0)
        toggles.append(sprite.visible)

    assert toggles.count(True) > 0
    assert toggles.count(False) > 0
    assert sprite.visible  # should restore original
