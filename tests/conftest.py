"""Shared test fixtures and utilities for the ArcadeActions test suite."""

import atexit
import re
import sys

import arcade
import pytest

from actions import Action


class StderrFilter:
    """Filter to suppress known harmless pyglet audio driver cleanup errors."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = ""
        self.suppressing = False
        # Simple patterns to detect the pyglet audio driver error
        self.error_keywords = ["_delete_audio_driver", "Source._players", "Exception ignored in atexit callback"]

    def _contains_error(self, text):
        """Check if text contains the pyglet audio driver error."""
        # Check if all key error phrases are present
        text_lower = text.lower()
        return all(keyword.lower() in text_lower for keyword in self.error_keywords)

    def write(self, text):
        """Write to stderr, filtering out known harmless errors."""
        # Buffer writes to catch multi-line error messages
        self.buffer += text

        # Check if buffer contains the complete error
        if self._contains_error(self.buffer):
            # Suppress the entire error
            self.buffer = ""
            self.suppressing = False
            return

        # If we're currently suppressing, keep buffering until we see the error end
        if self.suppressing:
            # Check if we've seen enough to determine it's the error
            if "_players" in self.buffer and "AttributeError" in self.buffer:
                # Likely the end of the error, stop suppressing
                self.buffer = ""
                self.suppressing = False
                return
            # Keep suppressing
            return

        # Check if this looks like the start of the error
        if "_delete_audio_driver" in self.buffer or "Exception ignored in atexit callback" in self.buffer:
            self.suppressing = True
            # Don't write yet, keep buffering
            return

        # Normal output - flush buffer if it's getting large or we see newlines
        if len(self.buffer) > 8192:
            self.original_stderr.write(self.buffer)
            self.buffer = ""
        elif "\n" in text:
            # Flush complete lines
            lines = self.buffer.split("\n")
            self.buffer = lines[-1]  # Keep last incomplete line
            output = "\n".join(lines[:-1])
            if output:
                self.original_stderr.write(output + "\n")

    def flush(self):
        """Flush any remaining buffer and the original stderr."""
        if self.buffer and not self.suppressing:
            self.original_stderr.write(self.buffer)
            self.buffer = ""
        elif self.suppressing:
            # Clear suppressed error
            self.buffer = ""
            self.suppressing = False
        self.original_stderr.flush()

    def __getattr__(self, name):
        """Delegate other attributes to original stderr."""
        return getattr(self.original_stderr, name)


def pytest_configure(config):
    """Install stderr filter and patch pyglet's atexit handler at pytest startup."""
    # Install the filter early, before any tests run
    # Keep it active permanently to catch atexit errors that occur after pytest finishes
    if not isinstance(sys.stderr, StderrFilter):
        sys.stderr = StderrFilter(sys.stderr)

    # Patch pyglet to prevent the AttributeError
    # This is a known issue in pyglet where _delete_audio_driver tries to access
    # Source._players which may not exist. We ensure it exists as an empty list.
    try:
        import pyglet.media.drivers

        # Source is in pyglet.media.codecs.base, but might be imported as pyglet.media.Source
        # Try both import paths to be safe
        try:
            from pyglet.media.codecs.base import Source
        except ImportError:
            from pyglet.media import Source

        # Ensure Source._players exists to prevent AttributeError
        if not hasattr(Source, "_players"):
            Source._players = []
    except Exception:
        # If patching fails, fall back to stderr filtering
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
