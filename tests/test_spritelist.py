import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import MoveBy


def create_sprite():
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = 0
    sprite.center_y = 0
    return sprite


def test_spritelist_applies_actions():
    sprite1 = create_sprite()
    sprite2 = create_sprite()
    for s in (sprite1, sprite2):
        s.do(MoveBy((60, 0), 1.0))

    sprite_list = arcade.SpriteList()
    sprite_list.extend([sprite1, sprite2])

    for _ in range(60):  # 1 second @ 60 FPS
        sprite_list.update(1 / 60.0)

    assert sprite1.center_x == pytest.approx(60.0, abs=1.0)
    assert sprite2.center_x == pytest.approx(60.0, abs=1.0)
