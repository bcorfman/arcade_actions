"""Shared test fixtures and utilities for the ArcadeActions test suite."""

import os
import sys

import arcade
import pytest

from actions import Action


# Global window instance (created lazily, shared across all tests)
_global_test_window = None
_original_window_init = None
_original_get_window = None
_original_ctx_property_global = None




@pytest.fixture(scope="session", autouse=True)
def _ensure_window_context():
    """Ensure a window context exists for all tests.
    
    This session-scoped autouse fixture creates a window once at the start
    of the test session and cleans it up at the end. This avoids the overhead
    of creating a window for every test while ensuring sprites/sprite lists
    can be created in CI environments.
    
    On Linux with Xvfb, creates a real window. On Windows/macOS CI without
    OpenGL, monkeypatches Window.__init__ to create a mock window.
    """
    global _global_test_window, _original_window_init, _original_get_window, _original_ctx_property_global
    
    # Check if window already exists
    try:
        existing = arcade.get_window()
        if existing is not None:
            _global_test_window = existing
            yield
            return
    except RuntimeError:
        pass
    
    # Detect if we're on Windows/macOS CI (no OpenGL available)
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    is_linux = sys.platform.startswith("linux")
    needs_mock = is_ci and not is_linux
    
    # Try to create a real window first (will work on Linux with Xvfb)
    if _global_test_window is None and not needs_mock:
        try:
            _global_test_window = arcade.Window(800, 600, visible=False)
            arcade.set_window(_global_test_window)
        except Exception:
            # If window creation fails and we're in CI, fall back to mock
            if is_ci:
                needs_mock = True
    
    # On Windows/macOS CI, use a mock window instead of real OpenGL window
    if needs_mock and _global_test_window is None:
        _original_window_init = arcade.Window.__init__
        _original_get_window = arcade.get_window
        
        # Store original ctx property if it exists (for restoration)
        _original_ctx_property = getattr(arcade.Window, 'ctx', None)
        # Store it globally so we can restore it in cleanup
        _original_ctx_property_global = _original_ctx_property
        
        def mock_window_init(self, width=800, height=600, visible=False, **kwargs):
            """Mock Window.__init__ that avoids OpenGL initialization.
            
            Sets basic attributes without creating OpenGL context.
            The ctx property (set on the class) will raise RuntimeError.
            """
            # Set basic attributes without calling super().__init__()
            self._width = width
            self._height = height
            self.visible = visible
            self.has_exit = False
            self._title = kwargs.get("title", "")
        
        # Create a property that raises RuntimeError for ctx
        def ctx_getter(self):
            raise RuntimeError("No OpenGL context available (mock window for Windows/macOS CI)")
        
        # Set ctx as a property on the Window class
        arcade.Window.ctx = property(ctx_getter)
        
        # Monkeypatch Window.__init__
        arcade.Window.__init__ = mock_window_init
        
        try:
            # Create the mock window
            _global_test_window = arcade.Window(800, 600, visible=False)
            arcade.set_window(_global_test_window)
            
            # Monkeypatch get_window to return our mock
            def mock_get_window():
                return _global_test_window
            arcade.get_window = mock_get_window
        except Exception:
            # If mock creation fails, restore originals
            arcade.Window.__init__ = _original_window_init
            arcade.get_window = _original_get_window
            if _original_ctx_property is not None:
                arcade.Window.ctx = _original_ctx_property
            pass
    
    yield
    
    # Restore original Window.__init__, get_window, and ctx property if we monkeypatched them
    if _original_window_init is not None:
        arcade.Window.__init__ = _original_window_init
        _original_window_init = None
    if _original_get_window is not None:
        arcade.get_window = _original_get_window
        _original_get_window = None
    if _original_ctx_property_global is not None:
        arcade.Window.ctx = _original_ctx_property_global
        _original_ctx_property_global = None
    
    # Cleanup at end of session
    if _global_test_window is not None:
        try:
            if hasattr(_global_test_window, 'has_exit') and not _global_test_window.has_exit:
                if hasattr(_global_test_window, 'close'):
                    _global_test_window.close()
        except Exception:
            pass
        try:
            arcade.set_window(None)
        except Exception:
            pass
        _global_test_window = None


@pytest.fixture(scope="function")
def window():
    """Provide window context for tests that explicitly need it.
    
    Most tests don't need to request this - the window is created automatically.
    This fixture is for tests that need explicit access to the window object.
    """
    # Ensure window exists (should already exist from _ensure_window_context)
    try:
        win = arcade.get_window()
        if win is not None:
            yield win
            return
    except RuntimeError:
        pass
    
    # Fallback: create if somehow missing (shouldn't happen)
    global _global_test_window
    if _global_test_window is None:
        _global_test_window = arcade.Window(800, 600, visible=False)
        arcade.set_window(_global_test_window)
    yield _global_test_window


@pytest.fixture
def test_sprite(window) -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    sprite.angle = 0
    sprite.scale = 1.0
    sprite.alpha = 255
    return sprite


@pytest.fixture
def test_sprite_list(window) -> arcade.SpriteList:
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    sprite1 = arcade.Sprite(":resources:images/items/star.png")
    sprite2 = arcade.Sprite(":resources:images/items/star.png")
    sprite1.center_x = 50
    sprite2.center_x = 150
    sprite_list.append(sprite1)
    sprite_list.append(sprite2)
    return sprite_list


@pytest.fixture(autouse=True)
def cleanup_actions():
    """Clean up actions after each test."""
    yield
    Action.stop_all()


class ActionTestBase:
    """Base class for action tests with common setup and teardown."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
