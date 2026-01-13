"""Integration tests for DevVisualizer override inspector functionality."""

from __future__ import annotations

import arcade
import pytest

from actions.dev.visualizer import DevVisualizer, SpriteWithSourceMarkers


@pytest.fixture
def dev_visualizer(window):
    """Create a DevVisualizer instance for testing."""
    scene_sprites = arcade.SpriteList()
    dev_viz = DevVisualizer(scene_sprites=scene_sprites, window=window)
    return dev_viz


@pytest.fixture
def sprite_with_arrange_marker(test_sprite):
    """Create a sprite with arrange marker."""
    test_sprite._source_markers = [
        {"file": "test.py", "lineno": 10, "type": "arrange", "kwargs": {"rows": "2", "cols": "3"}}
    ]
    return test_sprite


class TestOverrideInspector:
    """Test override inspector methods."""

    def test_get_override_inspector_for_sprite_with_arrange_marker(self, dev_visualizer, sprite_with_arrange_marker):
        """Test inspector retrieval."""
        inspector = dev_visualizer.get_override_inspector_for_sprite(sprite_with_arrange_marker)

        assert inspector is not None
        # Inspector should be an ArrangeOverrideInspector instance
        assert hasattr(inspector, "__class__")

    def test_get_override_inspector_for_sprite_no_markers(self, dev_visualizer, test_sprite):
        """Test None return for sprites without markers."""
        # Sprite has no _source_markers
        assert not isinstance(test_sprite, SpriteWithSourceMarkers)

        inspector = dev_visualizer.get_override_inspector_for_sprite(test_sprite)

        assert inspector is None

    def test_get_override_inspector_for_sprite_no_arrange_marker(self, dev_visualizer, test_sprite):
        """Test None return for sprites without arrange markers."""
        # Sprite has markers but no arrange type
        test_sprite._source_markers = [
            {"file": "test.py", "lineno": 10, "attr": "center_x", "status": "yellow"}
        ]

        inspector = dev_visualizer.get_override_inspector_for_sprite(test_sprite)

        assert inspector is None

    def test_open_overrides_panel_for_sprite(self, dev_visualizer, sprite_with_arrange_marker, mocker):
        """Test opening overrides panel."""
        mock_open = mocker.patch.object(dev_visualizer.overrides_panel, "open")
        mock_open.return_value = True

        result = dev_visualizer.open_overrides_panel_for_sprite(sprite_with_arrange_marker)

        assert result is True
        mock_open.assert_called_once_with(sprite_with_arrange_marker)

    def test_toggle_overrides_panel_for_sprite(self, dev_visualizer, sprite_with_arrange_marker, mocker):
        """Test toggling overrides panel."""
        mock_toggle = mocker.patch.object(dev_visualizer.overrides_panel, "toggle")
        mock_toggle.return_value = True

        result = dev_visualizer.toggle_overrides_panel_for_sprite(sprite_with_arrange_marker)

        assert result is True
        mock_toggle.assert_called_once_with(sprite_with_arrange_marker)

    def test_toggle_overrides_panel_for_sprite_none(self, dev_visualizer, mocker):
        """Test toggling overrides panel with None sprite."""
        mock_toggle = mocker.patch.object(dev_visualizer.overrides_panel, "toggle")
        mock_toggle.return_value = False

        result = dev_visualizer.toggle_overrides_panel_for_sprite(None)

        mock_toggle.assert_called_once_with(None)
