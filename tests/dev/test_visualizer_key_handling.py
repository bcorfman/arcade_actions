"""Tests for DevVisualizer key handling.

Tests handle_key_press method which handles keyboard input for DevVisualizer.
This is a complex function (F complexity) with many branches.
"""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.integration


class TestHandleKeyPressBasic(ActionTestBase):
    """Test suite for basic key handling in handle_key_press."""

    def test_f11_toggles_palette(self, window, mocker):
        """Test that F11 toggles palette window."""
        dev_viz = DevVisualizer()

        # Mock toggle_palette method
        mock_toggle = mocker.patch.object(dev_viz, "toggle_palette")

        result = dev_viz.handle_key_press(arcade.key.F11, 0)

        assert result is True
        mock_toggle.assert_called_once()

    def test_f8_toggles_command_palette(self, window, test_sprite, mocker):
        """Test that F8 toggles command palette window."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)

        mock_toggle = mocker.patch.object(dev_viz, "toggle_command_palette")

        result = dev_viz.handle_key_press(arcade.key.F8, 0)

        assert result is True
        mock_toggle.assert_called_once_with()

    def test_f8_handles_empty_scene(self, window, mocker):
        """Test that F8 still toggles command palette when scene is empty."""
        dev_viz = DevVisualizer()
        mock_toggle = mocker.patch.object(dev_viz, "toggle_command_palette")

        result = dev_viz.handle_key_press(arcade.key.F8, 0)

        assert result is True
        mock_toggle.assert_called_once_with()

    def test_e_key_exports_to_yaml(self, window, test_sprite_list, mocker, tmp_path):
        """Test that E key exports scene to YAML."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)

        # Mock export_template (imported inside the function, so patch the module)
        mock_export = mocker.patch("arcadeactions.dev.templates.export_template")

        result = dev_viz.handle_key_press(arcade.key.E, 0)

        assert result is True
        mock_export.assert_called_once()

    def test_i_key_imports_from_yaml(self, window, test_sprite_list, mocker, tmp_path):
        """Test that I key imports scene from YAML."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)

        # Mock load_scene_template (imported inside the function, so patch the module)
        mock_load = mocker.patch("arcadeactions.dev.templates.load_scene_template")

        result = dev_viz.handle_key_press(arcade.key.I, 0)

        assert result is True
        # Should try to load from files (even if they don't exist, returns True)
        # The actual import logic would be called if files exist

    def test_delete_key_removes_selected_sprites(self, window, test_sprite_list, mocker):
        """Test that Delete key removes selected sprites."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)

        # Select all sprites
        for sprite in test_sprite_list:
            dev_viz.selection_manager._selected.add(sprite)

        result = dev_viz.handle_key_press(arcade.key.DELETE, 0)

        assert result is True
        # Sprites should be removed from scene
        assert len(dev_viz.scene_sprites) == 0
        # Selection should be cleared
        assert len(dev_viz.selection_manager.get_selected()) == 0

    def test_backspace_key_removes_selected_sprites(self, window, test_sprite_list, mocker):
        """Test that Backspace key removes selected sprites (same as Delete)."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)

        # Select all sprites
        for sprite in test_sprite_list:
            dev_viz.selection_manager._selected.add(sprite)

        result = dev_viz.handle_key_press(arcade.key.BACKSPACE, 0)

        assert result is True
        # Sprites should be removed from scene
        assert len(dev_viz.scene_sprites) == 0

    def test_delete_key_returns_false_with_no_selection(self, window, test_sprite_list):
        """Test that Delete key returns False when no sprites are selected."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)

        # No sprites selected
        assert len(dev_viz.selection_manager.get_selected()) == 0

        initial_count = len(dev_viz.scene_sprites)

        result = dev_viz.handle_key_press(arcade.key.DELETE, 0)

        # Should return False (key not handled) when no selection
        assert result is False
        assert len(dev_viz.scene_sprites) == initial_count

    def test_unhandled_key_returns_false(self, window):
        """Test that unhandled keys return False."""
        dev_viz = DevVisualizer()

        result = dev_viz.handle_key_press(arcade.key.A, 0)

        assert result is False

    def test_o_key_toggles_overrides_panel_for_selected_sprite(self, window, test_sprite, mocker):
        """O key should attempt to toggle overrides panel for current selection."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        mock_toggle = mocker.patch.object(dev_viz, "toggle_overrides_panel_for_sprite", return_value=True)

        result = dev_viz.handle_key_press(arcade.key.O, 0)

        assert result is True
        mock_toggle.assert_called_once_with(test_sprite)

    def test_o_key_reports_when_no_arrange_marker_available(self, window, capsys):
        """O key should report when no arrange-grid marker is available."""
        dev_viz = DevVisualizer()

        result = dev_viz.handle_key_press(arcade.key.O, 0)

        assert result is True
        assert "Overrides panel unavailable" in capsys.readouterr().out


class TestHandleKeyPressOverridesPanel(ActionTestBase):
    """Test suite for overrides panel key handling in handle_key_press."""

    def test_ctrl_z_undo_when_panel_open(self, window, mocker):
        """Test that Ctrl+Z triggers undo when overrides panel is open."""
        dev_viz = DevVisualizer()

        # Mock overrides panel
        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.Z, arcade.key.MOD_CTRL)

        assert result is True
        mock_panel.handle_key.assert_called_once_with("CTRL+Z")

    def test_ctrl_z_handles_exception(self, window, mocker):
        """Test that Ctrl+Z handles exceptions from panel.handle_key."""
        dev_viz = DevVisualizer()

        # Mock overrides panel that raises exception
        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.handle_key.side_effect = Exception("Panel error")
        dev_viz.overrides_panel = mock_panel

        # Should not raise, just return True
        result = dev_viz.handle_key_press(arcade.key.Z, arcade.key.MOD_CTRL)

        assert result is True

    def test_enter_starts_edit_when_not_editing(self, window, mocker):
        """Test that Enter starts edit when panel is open but not editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = False
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.ENTER, 0)

        assert result is True
        mock_panel.start_edit.assert_called_once()

    def test_enter_commits_edit_when_editing(self, window, mocker):
        """Test that Enter commits edit when panel is open and editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.ENTER, 0)

        assert result is True
        mock_panel.commit_edit.assert_called_once()
        mock_panel.start_edit.assert_not_called()

    def test_escape_cancels_edit_when_editing(self, window, mocker):
        """Test that Escape cancels edit when panel is open and editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.ESCAPE, 0)

        assert result is True
        mock_panel.cancel_edit.assert_called_once()

    def test_escape_returns_false_when_not_editing(self, window, mocker):
        """Test that Escape returns False when panel is open but not editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = False
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.ESCAPE, 0)

        # Escape only returns True when editing, otherwise falls through
        assert result is False
        mock_panel.cancel_edit.assert_not_called()

    def test_x_key_starts_edit_x_field(self, window, mocker):
        """Test that X key starts editing x field."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.X, 0)

        assert result is True
        mock_panel.start_edit.assert_called_once_with("x")

    def test_y_key_starts_edit_y_field(self, window, mocker):
        """Test that Y key starts editing y field."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.Y, 0)

        assert result is True
        mock_panel.start_edit.assert_called_once_with("y")

    def test_tab_switches_field_when_editing(self, window, mocker):
        """Test that Tab switches editing field when editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = True
        mock_panel._editing_field = "x"
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.TAB, 0)

        assert result is True
        assert mock_panel._editing_field == "y"

    def test_tab_switches_from_y_to_x(self, window, mocker):
        """Test that Tab switches from y to x field."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = True
        mock_panel._editing_field = "y"
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.TAB, 0)

        assert result is True
        assert mock_panel._editing_field == "x"

    def test_backspace_handles_input_when_editing(self, window, mocker):
        """Test that Backspace sends backspace char when editing."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.editing = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.BACKSPACE, 0)

        assert result is True
        mock_panel.handle_input_char.assert_called_once_with("\b")

    def test_up_key_not_handled_when_panel_open(self, window, mocker):
        """Test that Up key is not handled (dead code in implementation)."""
        # Document current behavior: UP key handler exists but is unreachable (dead code)
        # Lines 1186-1187 in visualizer.py are after a return statement, so they never execute
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.UP, 0)

        # UP key is not actually handled (dead code), returns False
        assert result is False
        mock_panel.select_prev.assert_not_called()

    def test_down_key_selects_next_when_panel_open(self, window, mocker):
        """Test that Down key selects next item when panel is open."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.DOWN, 0)

        assert result is True
        mock_panel.select_next.assert_called_once()

    def test_left_key_increments_x(self, window, mocker):
        """Test that Left key decrements x coordinate."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.LEFT, 0)

        assert result is True
        mock_panel.increment_selected.assert_called_once_with(-1, 0)

    def test_right_key_increments_x(self, window, mocker):
        """Test that Right key increments x coordinate."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.RIGHT, 0)

        assert result is True
        mock_panel.increment_selected.assert_called_once_with(1, 0)

    def test_pageup_key_increments_y(self, window, mocker):
        """Test that PageUp key increments y coordinate."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.PAGEUP, 0)

        assert result is True
        mock_panel.increment_selected.assert_called_once_with(0, 1)

    def test_pagedown_key_decrements_y(self, window, mocker):
        """Test that PageDown key decrements y coordinate."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.PAGEDOWN, 0)

        assert result is True
        mock_panel.increment_selected.assert_called_once_with(0, -1)

    def test_delete_removes_override_when_panel_open(self, window, mocker):
        """Test that Delete key removes selected override when panel is open."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.get_selected.return_value = {"row": 0, "col": 1}
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.DELETE, 0)

        assert result is True
        mock_panel.remove_override.assert_called_once_with(0, 1)

    def test_delete_does_nothing_when_no_selection(self, window, mocker):
        """Test that Delete does nothing when panel is open but no override selected."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = True
        mock_panel.get_selected.return_value = None
        dev_viz.overrides_panel = mock_panel

        result = dev_viz.handle_key_press(arcade.key.DELETE, 0)

        assert result is True
        mock_panel.remove_override.assert_not_called()

    def test_keys_ignored_when_panel_closed(self, window, mocker):
        """Test that overrides panel keys are ignored when panel is closed."""
        dev_viz = DevVisualizer()

        mock_panel = mocker.MagicMock()
        mock_panel.is_open.return_value = False
        dev_viz.overrides_panel = mock_panel

        # These keys should not trigger panel actions when panel is closed
        result1 = dev_viz.handle_key_press(arcade.key.X, 0)
        result2 = dev_viz.handle_key_press(arcade.key.ENTER, 0)

        # Should return False (not handled) or handled by other logic
        mock_panel.start_edit.assert_not_called()
        mock_panel.commit_edit.assert_not_called()

    def test_keys_ignored_when_panel_is_none(self, window):
        """Test that overrides panel keys are ignored when panel is None."""
        dev_viz = DevVisualizer()

        # overrides_panel should exist, but test the None check path
        # Actually, overrides_panel is always created in __init__, so this tests the is_open() check
        dev_viz.overrides_panel.is_open = lambda: False

        result = dev_viz.handle_key_press(arcade.key.X, 0)

        # X key without panel open should not be handled
        assert result is False
