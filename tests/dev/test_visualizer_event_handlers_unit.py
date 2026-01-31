"""Unit tests for DevVisualizer event handler wrapping."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import DevVisualizer


@pytest.mark.integration
class TestWindowKeyHandling:
    """Tests for wrapped window key handling."""

    def test_f12_toggles_dev_visualizer(self, window, mocker):
        """F12 should toggle DevVisualizer without calling the original handler."""
        dev_viz = DevVisualizer(window=window)
        original_handler = mocker.MagicMock()
        window.on_key_press = original_handler

        dev_viz.attach_to_window(window)
        toggle = mocker.patch.object(dev_viz, "toggle")

        window.on_key_press(arcade.key.F12, 0)

        toggle.assert_called_once()
        original_handler.assert_not_called()

    def test_escape_closes_palette_in_edit_mode(self, window, mocker):
        """ESC should close palette window when edit mode is active."""
        dev_viz = DevVisualizer(window=window)
        original_handler = mocker.MagicMock()
        window.on_key_press = original_handler

        dev_viz.attach_to_window(window)
        dev_viz.visible = True
        mock_palette = mocker.MagicMock()
        mock_palette.closed = False
        dev_viz.palette_window = mock_palette

        window.on_key_press(arcade.key.ESCAPE, 0)

        mock_palette.close.assert_called_once()
        original_handler.assert_not_called()

    def test_escape_calls_original_when_not_visible(self, window, mocker):
        """ESC should fall back to original handler when not in edit mode."""
        dev_viz = DevVisualizer(window=window)
        original_handler = mocker.MagicMock()
        window.on_key_press = original_handler

        dev_viz.attach_to_window(window)
        dev_viz.visible = False

        window.on_key_press(arcade.key.ESCAPE, 0)

        original_handler.assert_called_once_with(arcade.key.ESCAPE, 0)
