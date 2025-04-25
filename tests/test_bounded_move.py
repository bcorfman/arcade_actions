import arcade
from PIL import Image

from actions.base import ActionSprite
from actions.move import BoundedMove


def make_row(x_values):
    sprites = []
    for x in x_values:
        # Create a 1x1 transparent image
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        sprite = ActionSprite(filename=None)
        sprite.texture = arcade.Texture(name="test_texture", image=img)
        sprite.center_x = x
        sprite.center_y = 100
        sprites.append(sprite)
    return sprites


def test_bounded_move_reverses_on_wall():
    group = make_row([50, 70, 90])
    action = BoundedMove(velocity=(20, 0), bounds=(0, 100), step_down=10)
    action.start(group)

    # Simulate movement forward
    for _ in range(3):
        for sprite in group:
            sprite.center_x += sprite.change_x * (1 / 60.0)
        action.update(0.0)

    # Now they should be near or over the right boundary
    assert any(s.center_x >= 100 for s in group)

    # Next update triggers reversal
    action.update(0.0)

    # All sprites should have reversed and moved down
    for sprite in group:
        assert sprite.change_x == -20
        assert sprite.center_y == 90  # Step down applied
