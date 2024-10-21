import pytest

from actions.base import Spawn
from actions.interval import FadeOut, MoveTo, RotateBy, ScaleTo
from demo import ActionDemo, ActionSprite, error_handler


@pytest.fixture
def action_sprite():
    return ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)


@pytest.fixture
def action_demo():
    return ActionDemo()


def test_action_sprite_initialization(action_sprite):
    assert action_sprite.scale.x == 0.5
    assert action_sprite.scale.y == 0.5
    assert action_sprite.center_x == 400  # SCREEN_WIDTH // 2
    assert action_sprite.center_y == 300  # SCREEN_HEIGHT // 2
    assert action_sprite.angle == 0
    assert action_sprite.alpha == 255


def test_action_sprite_do_method(action_sprite):
    move_action = MoveTo((100, 100), 1.0)
    action_sprite.do(move_action)
    assert len(action_sprite.actions) == 1
    assert action_sprite.actions[0] == move_action


def test_action_sprite_update(action_sprite):
    move_action = MoveTo((100, 100), 1.0)
    action_sprite.do(move_action)
    action_sprite.update(1.0)
    assert action_sprite.center_x == 100
    assert action_sprite.center_y == 100
    assert len(action_sprite.actions) == 0


def test_action_sprite_reset_state(action_sprite):
    action_sprite.center_x = 100
    action_sprite.center_y = 100
    action_sprite.angle = 45
    action_sprite.alpha = 128
    action_sprite.scale = 2.0

    action_sprite.reset_state()

    assert action_sprite.center_x == 400
    assert action_sprite.center_y == 300
    assert action_sprite.angle == 0
    assert action_sprite.alpha == 255
    assert action_sprite.scale.x == 0.5
    assert action_sprite.scale.y == 0.5


def test_action_demo_initialization(action_demo):
    assert len(action_demo.actions) == 13
    assert isinstance(action_demo.sprite, ActionSprite)
    assert len(action_demo.sprite_list) == 1


def test_action_demo_start_demo(action_demo):
    action_demo.start_demo()
    assert action_demo.demo_active == True
    assert action_demo.current_action == 1
    assert len(action_demo.sprite.actions) == 1


def test_action_demo_start_next_action(action_demo):
    action_demo.start_next_action()
    assert action_demo.current_action == 2
    assert len(action_demo.sprite.actions) == 2


def test_move_to_action():
    sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    move_action = MoveTo((100, 100), 1.0)
    sprite.do(move_action)
    sprite.update(1.0)
    assert sprite.center_x == 100
    assert sprite.center_y == 100


def test_rotate_by_action():
    sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    rotate_action = RotateBy(90, 1.0)
    sprite.do(rotate_action)
    sprite.update(1.0)
    assert sprite.angle == 90


def test_fade_out_action():
    sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    fade_action = FadeOut(1.0)
    sprite.do(fade_action)
    sprite.update(1.0)
    assert sprite.alpha == 0


def test_scale_to_action():
    sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
    scale_action = ScaleTo(2.0, 1.0)
    sprite.do(scale_action)
    sprite.update(1.0)
    assert sprite.scale.x == 2.0
    assert sprite.scale.y == 2.0


def test_error_handler_decorator():
    @error_handler
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_function()


def test_spawn_bezier_action(action_demo):
    action = action_demo.create_spawn_bezier_action()
    assert isinstance(action, Spawn)
    assert len(action.actions) == 16  # Number of sprites created


# Add more tests for other actions and edge cases as needed
