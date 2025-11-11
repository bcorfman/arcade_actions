"""Shared test fixtures and utilities for the ArcadeActions test suite."""

import arcade
import pytest

from actions import Action


@pytest.fixture(scope="function", autouse=True)
def window():
    """Create a headless window for tests that need Arcade context.

    This fixture ensures that all tests have access to a window context,
    which is required for creating sprites and sprite lists in CI environments.
    The window is created lazily - only when needed and not already present.
    """
    # Check if window already exists (don't create if tests mock get_window)
    existing_window = None
    try:
        existing_window = arcade.get_window()
    except RuntimeError:
        pass

    if existing_window is not None:
        yield existing_window
        return

    # Create a new headless window only if none exists
    # This is needed for CI environments where sprites/sprite lists require a context
    test_window = None
    try:
        test_window = arcade.Window(800, 600, visible=False)
        arcade.set_window(test_window)
        yield test_window
    finally:
        # Cleanup: close the window if we created it
        if test_window is not None:
            try:
                if not test_window.has_exit:
                    test_window.close()
            except Exception:
                pass
            # Clear the window reference
            try:
                arcade.set_window(None)
            except Exception:
                pass


@pytest.fixture
def test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    sprite.angle = 0
    sprite.scale = 1.0
    sprite.alpha = 255
    return sprite


@pytest.fixture
def test_sprite_list() -> arcade.SpriteList:
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
