import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite, sequence
from actions.interval import MoveBy, RotateBy


def create_sprite():
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = 0
    sprite.center_y = 0
    return sprite


def test_do_and_step_velocity_change():
    sprite = create_sprite()
    action = MoveBy((100, 0), 1.0)
    sprite.do(action)

    # Simulate game update cycle
    sprite.update(0.1)
    assert sprite.change_x == pytest.approx(100.0)

    # Step to completion
    for _ in range(9):
        sprite.update(0.1)
    assert action.is_done()
    assert sprite.change_x == pytest.approx(0.0)


def test_sequence_behavior_on_sprite():
    sprite = create_sprite()
    action = sequence(MoveBy((60, 0), 0.5), RotateBy(90, 0.5))
    sprite.do(action)

    sprite.update(0.5)
    assert sprite.change_x == pytest.approx(0.0)
    assert sprite.change_angle == pytest.approx(180.0)

    sprite.update(0.5)
    assert sprite.change_angle == pytest.approx(0.0)
    assert not sprite.has_active_actions()


def test_clear_actions_stops_all():
    sprite = create_sprite()
    sprite.do(MoveBy((100, 0), 2.0))
    sprite.do(RotateBy(360, 2.0))

    sprite.clear_actions()

    assert not sprite.has_active_actions()
    assert sprite.change_x == 0.0
    assert sprite.change_angle == 0.0


def test_has_active_actions_tracking():
    sprite = create_sprite()
    act = MoveBy((50, 0), 0.2)
    sprite.do(act)

    assert sprite.has_active_actions()
    sprite.update(0.2)
    assert not sprite.has_active_actions()
