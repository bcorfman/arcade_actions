"""Tests for DevVisualizer palette coordination methods.

Tests toggle_palette, _position_palette_window, _poll_show_palette, and
_create_palette_window methods. This tests current behavior.
"""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.integration


class TestTogglePalette(ActionTestBase):
    """Test suite for toggle_palette method."""

    def test_toggle_palette_creates_window_if_none(self, window, test_sprite_list, mocker):
        """Test that toggle_palette creates palette window when showing."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        # Mock PaletteWindow
        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        mock_palette_window.show_window = mocker.MagicMock()

        mocker.patch("arcadeactions.dev.visualizer.PaletteWindow", return_value=mock_palette_window)
        mocker.patch.object(dev_viz, "_create_palette_window", wraps=dev_viz._create_palette_window)
        mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
        mocker.patch.object(dev_viz, "update_main_window_position", return_value=True)
        mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)

        dev_viz.toggle_palette()

        # Should create and show palette window
        assert dev_viz.palette_window is not None
        mock_palette_window.show_window.assert_called_once()

    def test_toggle_palette_toggles_visibility(self, window, test_sprite_list, mocker):
        """Test that toggle_palette hides a visible palette window."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = True

        # Create mock palette window
        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = True
        mock_palette_window.hide_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mock_cache = mocker.patch.object(dev_viz, "_cache_palette_desired_location")

        dev_viz.toggle_palette()

        # Should cache and hide
        mock_cache.assert_called_once()
        mock_palette_window.hide_window.assert_called_once()

    def test_toggle_palette_positions_before_showing(self, window, test_sprite_list, mocker):
        """Test that toggle_palette positions window before making it visible."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = False

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        mock_palette_window.show_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
        mock_update_pos = mocker.patch.object(dev_viz, "update_main_window_position", return_value=True)
        mock_position = mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)

        dev_viz.toggle_palette()

        # Should position before showing
        mock_update_pos.assert_called_once()
        mock_position.assert_called_once()
        mock_palette_window.show_window.assert_called_once()

    def test_toggle_palette_deferred_positioning_if_not_tracked(self, window, test_sprite_list, mocker):
        """Test that toggle_palette schedules a poll when main location is not ready."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = False

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        dev_viz.palette_window = mock_palette_window

        mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=False)
        mock_schedule = mocker.patch("arcade.schedule_once")
        mock_position = mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)

        dev_viz.toggle_palette()

        # Should schedule poll and skip positioning for now
        mock_position.assert_not_called()
        mock_schedule.assert_called()

    def test_toggle_palette_requests_focus_when_showing(self, window, test_sprite_list, mocker):
        """Test that toggle_palette activates main window after showing."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = False

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        mock_palette_window.show_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
        mocker.patch.object(dev_viz, "update_main_window_position", return_value=True)
        mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)
        mock_activate = mocker.patch.object(dev_viz, "_activate_main_window")

        dev_viz.toggle_palette()

        mock_activate.assert_called_once()

    def test_toggle_palette_skips_positioning_if_already_visible(self, window, test_sprite_list, mocker):
        """Test that hiding the palette does not reposition it."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = True

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = True  # Already visible
        mock_palette_window.hide_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mock_position = mocker.patch.object(dev_viz, "_position_palette_window")

        dev_viz.toggle_palette()

        # Hiding should not trigger reposition
        mock_position.assert_not_called()


class TestPositionPaletteWindow(ActionTestBase):
    """Test suite for _position_palette_window method."""

    def test_position_palette_window_returns_false_if_no_window(self, window, test_sprite_list, mocker):
        """Test that _position_palette_window returns False if no palette window."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz.palette_window = None

        result = dev_viz._position_palette_window()

        assert result is False

    def test_position_palette_window_skips_if_visible_and_not_forced(self, window, test_sprite_list, mocker):
        """Test that _position_palette_window skips if window is visible and not forced."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = True
        dev_viz.palette_window = mock_palette_window

        result = dev_viz._position_palette_window(force=False)

        assert result is False

    def test_position_palette_window_repositions_if_forced(self, window, test_sprite_list, mocker):
        """Test that _position_palette_window repositions if forced even when visible."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = True
        dev_viz.palette_window = mock_palette_window

        # Mock dependencies
        mocker.patch("arcadeactions.dev.visualizer._get_primary_monitor_rect", return_value=(0, 0, 1920, 1080))
        mocker.patch.object(dev_viz, "_get_window_location", return_value=(100, 200))
        mocker.patch.object(mock_palette_window, "set_location")

        result = dev_viz._position_palette_window(force=True)

        # Should position even if visible when forced
        assert result is True

    def test_position_palette_window_returns_false_if_no_anchor_window(self, window, test_sprite_list, mocker):
        """Test that _position_palette_window returns False if anchor window is None."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=None)

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        dev_viz.palette_window = mock_palette_window

        mocker.patch("arcadeactions.dev.visualizer._get_primary_monitor_rect", return_value=(0, 0, 1920, 1080))

        result = dev_viz._position_palette_window()

        assert result is False

    def test_position_palette_window_uses_tracked_location(self, window, test_sprite_list, mocker):
        """Test that _position_palette_window uses tracked window location."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        mock_palette_window = mocker.MagicMock()
        mock_palette_window.visible = False
        mock_palette_window.set_location = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        # Mock dependencies
        mocker.patch("arcadeactions.dev.visualizer._get_primary_monitor_rect", return_value=(0, 0, 1920, 1080))
        mocker.patch.object(dev_viz, "_get_window_location", return_value=(100, 200))

        result = dev_viz._position_palette_window()

        # Should position using tracked location
        assert result is True
        mock_palette_window.set_location.assert_called_once()


class TestPollShowPalette(ActionTestBase):
    """Test suite for _poll_show_palette method."""

    def test_poll_show_palette_returns_early_if_not_visible(self, window, test_sprite_list, mocker):
        """Test that _poll_show_palette cancels pending show when palette is not desired."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = False
        dev_viz._palette_show_pending = True

        mock_schedule = mocker.patch("arcade.schedule_once")

        dev_viz._poll_show_palette()

        # Should clear pending flag and return early
        assert dev_viz._palette_show_pending is False
        mock_schedule.assert_not_called()

    def test_poll_show_palette_schedules_retry_if_no_window(self, window, test_sprite_list, mocker):
        """Test that _poll_show_palette schedules retry if window is None."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=None)
        dev_viz._palette_desired_visible = True
        dev_viz._palette_show_pending = True

        mocker.patch("arcade.get_window", return_value=None)
        mock_schedule = mocker.patch("arcade.schedule_once")

        dev_viz._poll_show_palette()

        # Should schedule retry
        mock_schedule.assert_called_once()

    def test_poll_show_palette_schedules_retry_if_location_invalid(self, window, test_sprite_list, mocker):
        """Test that _poll_show_palette schedules retry if window location is invalid."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = True
        dev_viz._palette_show_pending = True

        # Window returns invalid location (0, 0)
        window.get_location = mocker.MagicMock(return_value=(0, 0))
        mock_schedule = mocker.patch("arcade.schedule_once")

        dev_viz._poll_show_palette()

        # Should schedule retry
        mock_schedule.assert_called_once()

    def test_poll_show_palette_positions_and_shows_when_ready(self, window, test_sprite_list, mocker):
        """Test that _poll_show_palette positions and shows palette when window is ready."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = True
        dev_viz._palette_show_pending = True

        # Window has valid location
        window.get_location = mocker.MagicMock(return_value=(100, 200))

        mock_palette_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mock_position = mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)
        mock_update_pos = mocker.patch.object(dev_viz, "update_main_window_position")
        mock_show = mocker.patch.object(mock_palette_window, "show_window")
        mocker.patch.object(dev_viz, "_activate_main_window")
        mock_schedule = mocker.patch("arcade.schedule_once")

        dev_viz._poll_show_palette()

        # Should update position and position palette
        mock_update_pos.assert_called_once()
        # Should position (called with force=True)
        assert mock_position.call_count >= 1
        # Should show window
        mock_show.assert_called_once()
        # Should not schedule retry
        mock_schedule.assert_not_called()

    def test_poll_show_palette_measures_decoration_deltas(self, window, test_sprite_list, mocker):
        """Test that _poll_show_palette measures window decoration deltas."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._palette_desired_visible = True
        dev_viz._palette_show_pending = True
        dev_viz._window_decoration_dx = None
        dev_viz._window_decoration_dy = None

        window.get_location = mocker.MagicMock(return_value=(100, 200))
        window._arcadeactions_last_set_location = (90, 190)  # Stored location

        mock_palette_window = mocker.MagicMock()
        dev_viz.palette_window = mock_palette_window

        mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)
        mocker.patch.object(mock_palette_window, "show_window")

        dev_viz._poll_show_palette()

        # Should calculate decoration deltas
        assert dev_viz._window_decoration_dx == 10  # 100 - 90
        assert dev_viz._window_decoration_dy == 10  # 200 - 190


class TestCreatePaletteWindow(ActionTestBase):
    """Test suite for _create_palette_window method."""

    def test_create_palette_window_creates_window(self, window, test_sprite_list, mocker):
        """Test that _create_palette_window creates palette window."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")

        dev_viz._create_palette_window()

        # Should create palette window
        assert dev_viz.palette_window is not None
        mock_palette_window_class.assert_called_once()

    def test_create_palette_window_sets_close_callback(self, window, test_sprite_list, mocker):
        """Test that _create_palette_window sets close callback."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._is_detaching = False

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")

        dev_viz._create_palette_window()

        # Get the on_close_callback that was passed
        call_args = mock_palette_window_class.call_args
        on_close_callback = call_args[1]["on_close_callback"]

        # Call the callback
        window.closed = False
        mock_close = mocker.patch.object(window, "close")
        on_close_callback()

        # Should close main window
        mock_close.assert_called_once()

    def test_create_palette_window_skips_close_if_detaching(self, window, test_sprite_list, mocker):
        """Test that close callback doesn't close window if detaching."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz._is_detaching = True

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")

        dev_viz._create_palette_window()

        # Get the on_close_callback
        call_args = mock_palette_window_class.call_args
        on_close_callback = call_args[1]["on_close_callback"]

        # Call the callback
        mock_close = mocker.patch.object(window, "close")
        on_close_callback()

        # Should not close main window when detaching
        mock_close.assert_not_called()

    def test_create_palette_window_sets_forward_key_handler(self, window, test_sprite_list, mocker):
        """Test that forward handler routes global palette shortcuts."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz.visible = True

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")
        mock_toggle_palette = mocker.patch.object(dev_viz, "toggle_palette")

        dev_viz._create_palette_window()

        # Get the forward_key_handler
        call_args = mock_palette_window_class.call_args
        forward_handler = call_args[1]["forward_key_handler"]

        # Call the handler
        result = forward_handler(arcade.key.F11, 0)

        # Should route to toggle_palette directly
        mock_toggle_palette.assert_called_once_with()
        assert result is True

    def test_create_palette_window_skips_forward_if_not_visible(self, window, test_sprite_list, mocker):
        """Test non-global keys return False when visualizer is hidden."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
        dev_viz.visible = False

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")

        dev_viz._create_palette_window()

        # Get the forward_key_handler
        call_args = mock_palette_window_class.call_args
        forward_handler = call_args[1]["forward_key_handler"]

        # Call with a non-global key (global shortcuts F12/F11/F8 are always handled)
        result = forward_handler(arcade.key.SPACE, 0)

        # Should return False if not visible
        assert result is False

    def test_create_palette_window_passes_main_window(self, window, test_sprite_list, mocker):
        """Test that _create_palette_window passes main window reference."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)

        mock_palette_window_class = mocker.patch("arcadeactions.dev.visualizer.PaletteWindow")
        mock_palette_instance = mocker.MagicMock()
        mock_palette_window_class.return_value = mock_palette_instance

        mocker.patch("arcadeactions.dev.visualizer.get_registry")

        dev_viz._create_palette_window()

        # Check that main_window was passed
        call_args = mock_palette_window_class.call_args
        assert call_args[1]["main_window"] == window
