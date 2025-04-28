import arcade
from PIL import Image

from actions.base import ActionSprite
from actions.move import BoundedMove


def make_row(x_values):
    sprites = []
    for x in x_values:
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        sprite = ActionSprite(filename=None)
        sprite.texture = arcade.Texture(name="test_texture", image=img)
        sprite.center_x = x
        sprite.center_y = 100
        sprites.append(sprite)
    return sprites


def test_bounded_move_reverses_and_triggers_callback_with_step():
    group = make_row([50, 70, 90])
    stepped_sprites = []

    def on_hit(sprite):
        sprite.center_y -= 10
        stepped_sprites.append(sprite)

    action = BoundedMove(velocity=(20, 0), bounds=(0, 100), on_hit_left=on_hit, on_hit_right=on_hit)
    action.start(group)

    for _ in range(3):
        for sprite in group:
            sprite.update(1 / 60)  # simulate sprite movement normally
        action.step(1 / 60)  # use step(), no manual update(0.0)

    assert any(s.center_x >= 100 for s in group)

    action.step(1 / 60)

    # Check that all sprites reversed
    for sprite in group:
        assert sprite.change_x == -20

    # Check that callback was triggered
    assert len(stepped_sprites) > 0
    for sprite in stepped_sprites:
        assert sprite.center_y == 90
