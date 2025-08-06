"""Shared test fixtures and utilities for the ArcadeActions test suite."""

import arcade
import pytest

from actions import Action


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
