import pytest

from actions.instant import CallFunc, CallFuncS, Hide, Place, Show, ToggleVisibility


class MockSprite:
    """Mock sprite class for testing"""

    def __init__(self):
        self.center_x = 0
        self.center_y = 0
        self.visible = True

    @property
    def center(self):
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, value):
        self.center_x, self.center_y = value


@pytest.fixture
def mock_sprite():
    return MockSprite()


@pytest.fixture
def callback_tracker():
    class CallbackTracker:
        def __init__(self):
            self.called = False
            self.args = None
            self.kwargs = None

        def __call__(self, *args, **kwargs):
            self.called = True
            self.args = args
            self.kwargs = kwargs

    return CallbackTracker()


class TestPlace:
    def test_place_action(self, mock_sprite):
        """Test Place action"""
        action = Place((100, 200))
        action.target = mock_sprite
        action.start()

        assert mock_sprite.center == (100, 200)
        assert action.done()

    @pytest.mark.parametrize("invalid_position", [None, (1,), ("invalid", 100), [1, 2, 3], "not_a_position"])
    def test_invalid_positions(self, invalid_position):
        """Test Place action with various invalid positions"""
        with pytest.raises(ValueError):
            Place(invalid_position)


class TestVisibilityActions:
    def test_hide_action(self, mock_sprite):
        """Test Hide action"""
        action = Hide()
        action.target = mock_sprite
        action.start()

        assert not mock_sprite.visible
        assert action.done()

    def test_show_action(self, mock_sprite):
        """Test Show action"""
        mock_sprite.visible = False
        action = Show()
        action.target = mock_sprite
        action.start()

        assert mock_sprite.visible
        assert action.done()

    @pytest.mark.parametrize("initial_visibility,expected_visibility", [(True, False), (False, True)])
    def test_toggle_visibility_action(self, mock_sprite, initial_visibility, expected_visibility):
        """Test ToggleVisibility action with different initial states"""
        mock_sprite.visible = initial_visibility
        action = ToggleVisibility()
        action.target = mock_sprite
        action.start()

        assert mock_sprite.visible == expected_visibility
        assert action.done()

    def test_visibility_reversals(self):
        """Test reversing visibility actions"""
        hide = Hide()
        show = Show()
        toggle = ToggleVisibility()

        assert isinstance(hide.__reversed__(), Show)
        assert isinstance(show.__reversed__(), Hide)
        assert isinstance(toggle.__reversed__(), ToggleVisibility)


class TestCallbackActions:
    def test_callfunc_action(self, callback_tracker):
        """Test CallFunc action"""
        action = CallFunc(callback_tracker, 1, 2, key="value")
        action.start()

        assert callback_tracker.called
        assert callback_tracker.args == (1, 2)
        assert callback_tracker.kwargs == {"key": "value"}
        assert action.done()

    def test_callfuncs_action(self, mock_sprite, callback_tracker):
        """Test CallFuncS action (with sprite)"""
        action = CallFuncS(callback_tracker, 1, key="value")
        action.target = mock_sprite
        action.start()

        assert callback_tracker.called
        assert callback_tracker.args[0] == mock_sprite  # First arg should be sprite
        assert callback_tracker.args[1:] == (1,)
        assert callback_tracker.kwargs == {"key": "value"}
        assert action.done()

    @pytest.mark.parametrize(
        "invalid_callback",
        [
            None,
            "not_callable",
            123,
            [],
        ],
    )
    def test_invalid_callbacks(self, invalid_callback):
        """Test various invalid callbacks"""
        with pytest.raises(ValueError):
            CallFunc(invalid_callback)

    def test_callfuncs_no_target(self, callback_tracker):
        """Test CallFuncS without a target"""
        action = CallFuncS(callback_tracker)
        with pytest.raises(AttributeError):
            action.start()

    @pytest.mark.parametrize(
        "args,kwargs,expected_args,expected_kwargs",
        [
            ((), {}, (), {}),
            ((1, 2), {}, (1, 2), {}),
            ((), {"x": 1}, (), {"x": 1}),
            ((1, 2), {"x": 1, "y": 2}, (1, 2), {"x": 1, "y": 2}),
        ],
    )
    def test_callback_parameters(self, callback_tracker, args, kwargs, expected_args, expected_kwargs):
        """Test different parameter combinations for callbacks"""
        action = CallFunc(callback_tracker, *args, **kwargs)
        action.start()

        assert callback_tracker.args == expected_args
        assert callback_tracker.kwargs == expected_kwargs
