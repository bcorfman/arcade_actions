"""Tests for DevVisualizer protocol conformance.

Tests that protocols defined in visualizer.py work correctly with @runtime_checkable
and that sprites/windows conform to the expected protocols.
"""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import (
    SpriteWithActionConfigs,
    SpriteWithOriginal,
    SpriteWithPositionId,
    SpriteWithSourceMarkers,
    WindowWithContext,
)
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.integration


class TestSpriteWithActionConfigsProtocol(ActionTestBase):
    """Test suite for SpriteWithActionConfigs protocol conformance."""

    def test_sprite_with_action_configs_conforms(self, test_sprite):
        """Test that a sprite with _action_configs conforms to protocol."""
        test_sprite._action_configs = []

        assert isinstance(test_sprite, SpriteWithActionConfigs)

    def test_sprite_without_action_configs_does_not_conform(self, test_sprite):
        """Test that a sprite without _action_configs does not conform to protocol."""
        # Ensure sprite doesn't have the attribute
        if hasattr(test_sprite, "_action_configs"):
            delattr(test_sprite, "_action_configs")

        assert not isinstance(test_sprite, SpriteWithActionConfigs)

    def test_sprite_with_action_configs_has_correct_type(self, test_sprite):
        """Test that _action_configs is a list."""
        test_sprite._action_configs = [{"preset": "test"}]

        assert isinstance(test_sprite, SpriteWithActionConfigs)
        assert isinstance(test_sprite._action_configs, list)


class TestSpriteWithSourceMarkersProtocol(ActionTestBase):
    """Test suite for SpriteWithSourceMarkers protocol conformance."""

    def test_sprite_with_source_markers_conforms(self, test_sprite):
        """Test that a sprite with _source_markers conforms to protocol."""
        test_sprite._source_markers = []

        assert isinstance(test_sprite, SpriteWithSourceMarkers)

    def test_sprite_without_source_markers_does_not_conform(self, test_sprite):
        """Test that a sprite without _source_markers does not conform to protocol."""
        # Ensure sprite doesn't have the attribute
        if hasattr(test_sprite, "_source_markers"):
            delattr(test_sprite, "_source_markers")

        assert not isinstance(test_sprite, SpriteWithSourceMarkers)

    def test_sprite_with_source_markers_has_correct_type(self, test_sprite):
        """Test that _source_markers is a list."""
        test_sprite._source_markers = [{"lineno": 1, "file": "test.py"}]

        assert isinstance(test_sprite, SpriteWithSourceMarkers)
        assert isinstance(test_sprite._source_markers, list)


class TestSpriteWithOriginalProtocol(ActionTestBase):
    """Test suite for SpriteWithOriginal protocol conformance."""

    def test_sprite_with_original_conforms(self, test_sprite):
        """Test that a sprite with _original_sprite conforms to protocol."""
        original = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.BLUE)
        test_sprite._original_sprite = original

        assert isinstance(test_sprite, SpriteWithOriginal)

    def test_sprite_without_original_does_not_conform(self, test_sprite):
        """Test that a sprite without _original_sprite does not conform to protocol."""
        # Ensure sprite doesn't have the attribute
        if hasattr(test_sprite, "_original_sprite"):
            delattr(test_sprite, "_original_sprite")

        assert not isinstance(test_sprite, SpriteWithOriginal)


class TestSpriteWithPositionIdProtocol(ActionTestBase):
    """Test suite for SpriteWithPositionId protocol conformance."""

    def test_sprite_with_position_id_conforms(self, test_sprite):
        """Test that a sprite with _position_id conforms to protocol."""
        test_sprite._position_id = "test_id"

        assert isinstance(test_sprite, SpriteWithPositionId)

    def test_sprite_with_none_position_id_conforms(self, test_sprite):
        """Test that a sprite with _position_id=None conforms to protocol."""
        test_sprite._position_id = None

        assert isinstance(test_sprite, SpriteWithPositionId)

    def test_sprite_without_position_id_does_not_conform(self, test_sprite):
        """Test that a sprite without _position_id does not conform to protocol."""
        # Ensure sprite doesn't have the attribute
        if hasattr(test_sprite, "_position_id"):
            delattr(test_sprite, "_position_id")

        assert not isinstance(test_sprite, SpriteWithPositionId)


class TestWindowWithContextProtocol(ActionTestBase):
    """Test suite for WindowWithContext protocol conformance."""

    def test_window_with_context_conforms(self, window, mocker):
        """Test that a window with _context conforms to protocol."""
        window._context = mocker.MagicMock()
        window.height = 600

        assert isinstance(window, WindowWithContext)

    def test_window_with_none_context_conforms(self, window):
        """Test that a window with _context=None conforms to protocol."""
        window._context = None
        window.height = 600

        assert isinstance(window, WindowWithContext)

    def test_window_without_context_does_not_conform(self, window):
        """Test that a window without _context does not conform to protocol."""

        # Create a window-like object without _context
        class WindowWithoutContext:
            def __init__(self):
                self.height = 600

            def get_location(self):
                return None

        window_mock = WindowWithoutContext()
        assert not isinstance(window_mock, WindowWithContext)

    def test_window_without_height_does_not_conform(self, window, mocker):
        """Test that a window without height does not conform to protocol."""

        # Create a window-like object without height
        class WindowWithoutHeight:
            def __init__(self):
                self._context = mocker.MagicMock()

            def get_location(self):
                return None

        window_mock = WindowWithoutHeight()
        assert not isinstance(window_mock, WindowWithContext)
