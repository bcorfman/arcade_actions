"""Shared test fixtures and utilities for the ArcadeActions test suite."""

import os
import sys
from collections.abc import Callable
from unittest.mock import MagicMock

import arcade
import pytest

try:
    import arcade.window_commands as window_commands_module
except ImportError:  # pragma: no cover - defensive
    window_commands_module = None

import arcade.sprite_list.sprite_list as sprite_list_module

from actions import Action


class HeadlessWindow:
    """Minimal window substitute used on platforms without OpenGL support."""

    def __init__(self, width: int = 800, height: int = 600, visible: bool = False, **kwargs) -> None:
        self.width = width
        self.height = height
        self.visible = visible
        self.has_exit = False
        self.location: tuple[int, int] = (0, 0)
        self._title = kwargs.get("title", "Headless Window")
        self.handlers: dict[str, Callable[..., object]] = {}
        self._view = None
        self._mock = MagicMock(name="HeadlessWindowMock")

    @property
    def ctx(self):  # pragma: no cover - behaviour verified indirectly
        raise RuntimeError("No OpenGL context available (headless CI mode)")

    def close(self) -> None:
        self.has_exit = True

    def set_location(self, x: int, y: int) -> None:
        self.location = (x, y)

    def set_caption(self, title: str) -> None:
        self._title = title

    def set_size(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def clear(self) -> None:
        """No-op clear."""

    def switch_to(self) -> None:
        """No-op context switch."""

    def show_view(self, view) -> None:
        self._view = view

    def on_draw(self, *args, **kwargs):
        return None

    def on_update(self, *args, **kwargs):
        return None

    def on_close(self) -> None:
        self.has_exit = True

    def push_handlers(self, **handlers) -> None:
        self.handlers.update(handlers)

    def dispatch_event(self, event_type: str, *args, **kwargs):
        handler = self.handlers.get(event_type)
        if handler:
            return handler(*args, **kwargs)
        return None

    def __getattr__(self, item):  # pragma: no cover - defensive
        return getattr(self._mock, item)


# Global window state
_global_test_window: HeadlessWindow | arcade.Window | None = None
_original_get_window = None
_original_get_window_module = None
_headless_mode = False
_original_sprite_list_init = None


def _register_window(window) -> None:
    """Register the given window with arcade and keep global reference."""
    global _global_test_window
    _global_test_window = window
    if window_commands_module is not None:
        window_commands_module.set_window(window)
    else:
        arcade.set_window(window)


def _create_or_get_window() -> HeadlessWindow | arcade.Window:
    """Ensure a window exists and return it."""
    global _global_test_window
    if _global_test_window is not None:
        return _global_test_window

    if _headless_mode:
        window = HeadlessWindow(800, 600, visible=False)
    else:
        window = arcade.Window(800, 600, visible=False)
    _register_window(window)
    return window


@pytest.fixture(scope="session", autouse=True)
def _ensure_window_context():
    """Ensure we have a window (real or headless) for tests."""
    global _headless_mode, _original_get_window, _original_get_window_module, _original_sprite_list_init

    existing = None
    try:
        existing = arcade.get_window()
    except RuntimeError:
        existing = None

    if existing is not None:
        _register_window(existing)
        yield
    else:
        is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
        is_linux = sys.platform.startswith("linux")
        _headless_mode = bool(is_ci and not is_linux)

        if _headless_mode:
            _original_get_window = arcade.get_window
            if window_commands_module is not None:
                _original_get_window_module = window_commands_module.get_window
            _original_sprite_list_init = sprite_list_module.SpriteList.__init__

            def _headless_get_window():
                if _global_test_window is None:
                    raise RuntimeError("Headless window not initialised")
                return _global_test_window

            arcade.get_window = _headless_get_window
            if window_commands_module is not None:
                window_commands_module.get_window = _headless_get_window

            def _headless_sprite_list_init(
                self,
                use_spatial_hash: bool = False,
                spatial_hash_cell_size: int = 128,
                atlas=None,
                capacity: int = 100,
                lazy: bool = False,
                visible: bool = True,
            ):
                return _original_sprite_list_init(
                    self,
                    use_spatial_hash,
                    spatial_hash_cell_size,
                    atlas,
                    capacity,
                    True,
                    visible,
                )

            sprite_list_module.SpriteList.__init__ = _headless_sprite_list_init

        _create_or_get_window()

        try:
            yield
        finally:
            if _headless_mode:
                if window_commands_module is not None and _original_get_window_module is not None:
                    window_commands_module.get_window = _original_get_window_module
                    _original_get_window_module = None
                if _original_get_window is not None:
                    arcade.get_window = _original_get_window
                    _original_get_window = None
                if _original_sprite_list_init is not None:
                    sprite_list_module.SpriteList.__init__ = _original_sprite_list_init
                    _original_sprite_list_init = None

            if _global_test_window is not None:
                try:
                    _global_test_window.close()
                except Exception:
                    pass
                if window_commands_module is not None:
                    window_commands_module.set_window(None)
                else:
                    try:
                        arcade.set_window(None)
                    except Exception:
                        pass
                _register_window(None)

            _headless_mode = False


@pytest.fixture(scope="function")
def window():
    """Provide the active window (real or headless) to tests."""
    win = _create_or_get_window()
    yield win


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
