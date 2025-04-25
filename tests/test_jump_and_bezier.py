import arcade
import pytest
from PIL import Image

from actions.base import ActionSprite
from actions.interval import Bezier, JumpBy, JumpTo


class DummyTexture:
    width = 1
    height = 1


def create_sprite(x=0, y=0):
    # Create a 1x1 transparent image
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sprite = ActionSprite(filename=None)
    sprite.texture = arcade.Texture(name="test_texture", image=img)
    sprite.center_x = x
    sprite.center_y = y
    return sprite


def test_jumpby_velocity_waveform():
    sprite = create_sprite()
    jump = JumpBy((100, 0), height=40, jumps=2, duration=1.0)
    jump.start(sprite)

    # Check velocity wave shape
    t_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = []
    for t in t_values:
        jump._elapsed = t * jump.duration
        jump.update(t)
        results.append(sprite.change_y)

    # Should peak in the middle of the jump
    assert results[0] == pytest.approx(results[-1])
    assert results[2] > results[1] > results[0]
    assert results[2] > results[3] > results[4]


def test_jumpto_relative_motion():
    sprite = create_sprite(x=10, y=10)
    jump = JumpTo((110, 60), height=30, jumps=1, duration=1.0)
    jump.start(sprite)
    assert jump.delta == (100, 50)
    assert sprite.change_x == pytest.approx(100.0)


def test_bezier_sets_change_xy():
    # Simple linear Bezier curve
    def linear_bezier(t):
        return (t * 100, t * 100)

    sprite = create_sprite()
    curve = Bezier(linear_bezier, duration=1.0)
    curve.start(sprite)

    # Step through multiple t values
    t_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    last = (0, 0)
    for t in t_values:
        curve._elapsed = t * curve.duration
        curve.last_position = last
        curve.update(t)
        assert abs(sprite.change_x - (100 * t - last[0])) < 2.0
        assert abs(sprite.change_y - (100 * t - last[1])) < 2.0
        last = (100 * t, 100 * t)
