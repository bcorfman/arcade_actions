import arcade
from PIL import Image

from actions.base import ActionSprite
from actions.instant import CallFunc, CallFuncS, Hide, Place, Show, ToggleVisibility


class DummyTexture:
    width = 1
    height = 1


def create_sprite(x=0, y=0, visible=True):
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = x
    sprite.center_y = y
    sprite.visible = visible
    return sprite


def test_place_sets_position_immediately():
    sprite = create_sprite(0, 0)
    sprite.do(Place((200, 100)))
    sprite.update(0.016)
    assert sprite.center_x == 200
    assert sprite.center_y == 100


def test_hide_and_show():
    sprite = create_sprite(visible=True)
    sprite.do(Hide())
    sprite.update(0.016)
    assert not sprite.visible

    sprite.do(Show())
    sprite.update(0.016)
    assert sprite.visible


def test_toggle_visibility():
    sprite = create_sprite(visible=True)
    sprite.do(ToggleVisibility())
    sprite.update(0.016)
    assert not sprite.visible

    sprite.do(ToggleVisibility())
    sprite.update(0.016)
    assert sprite.visible


def test_callfunc_runs_once():
    result = {"called": False}

    def cb():
        result["called"] = True

    sprite = create_sprite()
    sprite.do(CallFunc(cb))
    sprite.update(0.016)
    assert result["called"]


def test_callfuncs_passes_sprite():
    result = {"received": None}

    def cb(s):
        result["received"] = s

    sprite = create_sprite()
    sprite.do(CallFuncS(cb))
    sprite.update(0.016)
    assert result["received"] == sprite
