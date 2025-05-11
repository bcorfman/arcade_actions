"""Test suite for instant.py - Instant action implementations."""

import arcade
import pytest
from arcade.texture import Texture

from actions.instant import CallFunc, CallFuncS, Hide, Place, Show, ToggleVisibility


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with a 1x1 transparent texture for testing."""
    texture = Texture.create_empty("test", (1, 1))
    sprite = arcade.Sprite()
    sprite.texture = texture
    return sprite


class TestPlace:
    """Test suite for Place action."""

    @pytest.fixture
    def sprite(self):
        return create_test_sprite()

    def test_place_initialization(self):
        """Test Place action initialization."""
        position = (100, 200)
        action = Place(position)
        assert action.position == position

    def test_place_requires_position(self):
        """Test Place action requires position parameter."""
        with pytest.raises(ValueError):
            Place()

    def test_place_execution(self, sprite):
        """Test Place action execution."""
        position = (100, 200)
        action = Place(position)
        action.target = sprite
        action.start()
        assert sprite.position == position


class TestHide:
    """Test suite for Hide action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.visible = True
        return sprite

    def test_hide_execution(self, sprite):
        """Test Hide action execution."""
        action = Hide()
        action.target = sprite
        action.start()
        assert not sprite.visible

    def test_hide_reverse(self):
        """Test Hide action reversal."""
        action = Hide()
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, Show)


class TestShow:
    """Test suite for Show action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.visible = False
        return sprite

    def test_show_execution(self, sprite):
        """Test Show action execution."""
        action = Show()
        action.target = sprite
        action.start()
        assert sprite.visible

    def test_show_reverse(self):
        """Test Show action reversal."""
        action = Show()
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, Hide)


class TestToggleVisibility:
    """Test suite for ToggleVisibility action."""

    @pytest.fixture
    def sprite(self):
        return create_test_sprite()

    def test_toggle_visibility_true_to_false(self, sprite):
        """Test ToggleVisibility from visible to hidden."""
        sprite.visible = True
        action = ToggleVisibility()
        action.target = sprite
        action.start()
        assert not sprite.visible

    def test_toggle_visibility_false_to_true(self, sprite):
        """Test ToggleVisibility from hidden to visible."""
        sprite.visible = False
        action = ToggleVisibility()
        action.target = sprite
        action.start()
        assert sprite.visible

    def test_toggle_visibility_reverse(self):
        """Test ToggleVisibility reversal."""
        action = ToggleVisibility()
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, ToggleVisibility)


class TestCallFunc:
    """Test suite for CallFunc action."""

    def test_call_func_initialization(self):
        """Test CallFunc initialization."""

        def test_func():
            pass

        action = CallFunc(test_func)
        assert action.func == test_func

    def test_call_func_requires_func(self):
        """Test CallFunc requires func parameter."""
        with pytest.raises(ValueError):
            CallFunc()

    def test_call_func_execution(self):
        """Test CallFunc execution."""
        called = False

        def test_func():
            nonlocal called
            called = True

        action = CallFunc(test_func)
        action.start()
        assert called

    def test_call_func_with_args(self):
        """Test CallFunc with arguments."""
        result = None

        def test_func(arg1, arg2):
            nonlocal result
            result = arg1 + arg2

        action = CallFunc(test_func, 1, 2)
        action.start()
        assert result == 3

    def test_call_func_with_kwargs(self):
        """Test CallFunc with keyword arguments."""
        result = None

        def test_func(x, y):
            nonlocal result
            result = x + y

        action = CallFunc(test_func, x=1, y=2)
        action.start()
        assert result == 3

    def test_call_func_reverse(self):
        """Test CallFunc reversal."""

        def test_func():
            pass

        action = CallFunc(test_func)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, CallFunc)


class TestCallFuncS:
    """Test suite for CallFuncS action."""

    @pytest.fixture
    def sprite(self):
        return create_test_sprite()

    def test_call_func_s_execution(self, sprite):
        """Test CallFuncS execution with sprite."""
        result = None

        def test_func(sprite, x, y):
            nonlocal result
            result = (sprite, x, y)

        action = CallFuncS(test_func, 1, 2)
        action.target = sprite
        action.start()
        assert result == (sprite, 1, 2)

    def test_call_func_s_requires_func(self):
        """Test CallFuncS requires func parameter."""
        with pytest.raises(ValueError):
            CallFuncS()
