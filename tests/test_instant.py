from unittest.mock import Mock

from actions.instant import CallFunc, CallFuncS, Hide, Place, Show, ToggleVisibility


def test_place_action():
    sprite = Mock()
    action = Place(position=(100, 200))  # Provide position as a tuple
    action.target = sprite
    action.update(1)  # Complete the action
    assert sprite.center_x == 100
    assert sprite.center_y == 200


def test_hide_action():
    sprite = Mock()
    sprite.alpha = 255
    action = Hide()
    action.target = sprite
    action.update(1)  # Set alpha to 0 to hide
    assert sprite.alpha == 0


def test_show_action():
    sprite = Mock()
    sprite.alpha = 0
    action = Show()
    action.target = sprite
    action.update(1)  # Set alpha to 255 to show
    assert sprite.alpha == 255


def test_toggle_visibility_action():
    sprite = Mock()
    sprite.alpha = 255  # Initially visible
    action = ToggleVisibility()
    action.target = sprite
    action.update(1)  # First toggle should hide
    assert sprite.alpha == 0
    action.update(1)  # Second toggle should show
    assert sprite.alpha == 255


def test_call_func_action():
    mock_func = Mock()
    action = CallFunc(func=mock_func)
    action.update(1)  # Directly call the function
    mock_func.assert_called_once()


def test_call_func_s_action():
    mock_func = Mock()
    sprite = Mock()
    action = CallFuncS(func=mock_func)
    action.target = sprite
    action.update(1)  # Pass the sprite to the function
    mock_func.assert_called_once_with(sprite)
