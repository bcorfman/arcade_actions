from unittest.mock import Mock

from actions.base import Action, ActionSprite


def test_action_sprite_initialization():
    # Initialize an ActionSprite and check its properties
    sprite = ActionSprite()
    assert isinstance(sprite.actions, list)  # Ensure actions is a list
    assert sprite.actions == []  # Should start with no active actions


def test_do_action():
    sprite = ActionSprite()
    action = Mock(spec=Action)

    # Perform an action and verify it starts on the sprite
    sprite.do(action)
    assert len(sprite.actions) == 1
    action.start.assert_called_once_with(sprite)


def test_update_actions():
    sprite = ActionSprite()
    action = Mock(spec=Action)
    sprite.do(action)

    # Update the sprite, advancing any active actions
    sprite.update(0.1)
    action.step.assert_called_once_with(0.1)


def test_remove_action():
    sprite = ActionSprite()
    action = Mock(spec=Action)
    sprite.do(action)
    sprite.remove_action(action)

    # Verify that the action was removed
    assert action not in sprite.actions
    action.stop.assert_called_once()


def test_clear_actions():
    sprite = ActionSprite()
    action1 = Mock(spec=Action)
    action2 = Mock(spec=Action)
    sprite.do(action1)
    sprite.do(action2)

    # Clear all actions and verify they are removed
    sprite.clear_actions()
    assert sprite.actions == []
    action1.stop.assert_called_once()
    action2.stop.assert_called_once()
