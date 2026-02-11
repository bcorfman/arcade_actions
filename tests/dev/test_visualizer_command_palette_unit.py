"""Unit tests for DevVisualizer command-palette integration paths."""

from __future__ import annotations

import arcade

from arcadeactions.dev.command_registry import CommandExecutionContext
from arcadeactions.dev.visualizer import DevVisualizer


def test_build_command_context_uses_current_selection(window, test_sprite_list):
    """Context should include selected sprites and active window."""
    dev_viz = DevVisualizer(scene_sprites=test_sprite_list, window=window)
    selected_sprite = test_sprite_list[0]
    dev_viz.selection_manager._selected.add(selected_sprite)

    context = dev_viz._build_command_context()

    assert context.window is window
    assert context.scene_sprites is test_sprite_list
    assert context.selection == [selected_sprite]


def test_toggle_command_palette_creates_and_toggles(window, mocker):
    """toggle_command_palette should create window, refresh context, and toggle visibility."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_palette = mocker.MagicMock()
    mocker.patch.object(dev_viz, "_create_command_palette_window", side_effect=lambda: setattr(dev_viz, "command_palette_window", mock_palette))
    mock_context = mocker.patch.object(dev_viz, "_build_command_context", return_value=mocker.MagicMock())

    dev_viz.toggle_command_palette()

    mock_context.assert_called_once()
    mock_palette.set_context.assert_called_once()
    mock_palette.toggle_window.assert_called_once()


def test_toggle_command_palette_returns_when_creation_fails(window, mocker):
    """toggle_command_palette should return quietly when creation fails."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mocker.patch.object(dev_viz, "_create_command_palette_window")
    dev_viz.command_palette_window = None

    dev_viz.toggle_command_palette()

    assert dev_viz.command_palette_window is None


def test_hide_hides_command_palette(window, mocker):
    """hide should hide command palette when present."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    dev_viz.command_palette_window = mocker.MagicMock()
    mock_resume = mocker.patch("arcadeactions.dev.visualizer.Action.resume_all")

    dev_viz.hide()

    dev_viz.command_palette_window.hide_window.assert_called_once()
    mock_resume.assert_called_once()


def test_detach_closes_command_palette(window, mocker):
    """detach_from_window should close and clear command palette window."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    dev_viz._attached = True
    command_palette = mocker.MagicMock()
    dev_viz.command_palette_window = command_palette

    # Seed required originals used during detach.
    dev_viz._original_on_draw = window.on_draw
    dev_viz._original_on_key_press = window.on_key_press
    dev_viz._original_on_mouse_press = window.on_mouse_press
    dev_viz._original_on_mouse_drag = window.on_mouse_drag
    dev_viz._original_on_mouse_release = window.on_mouse_release
    dev_viz._original_on_close = window.on_close

    dev_viz.detach_from_window()

    command_palette.close.assert_called_once()
    assert dev_viz.command_palette_window is None


def test_default_command_registry_contains_expected_keys(window):
    """Built-in command set should include enabled and disabled command keys."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    context = CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[])
    enabled = dev_viz.command_registry.get_enabled_commands(context)
    enabled_keys = {command.key for command in enabled}

    assert arcade.key.E in enabled_keys
    assert arcade.key.I in enabled_keys
    assert arcade.key.H in enabled_keys
    assert arcade.key.G not in enabled_keys


def test_create_command_palette_positions_next_to_main_window(window, mocker):
    """Creation should position command palette relative to main window when location is valid."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_palette = mocker.MagicMock()
    mocker.patch("arcadeactions.dev.visualizer.CommandPaletteWindow", return_value=mock_palette)
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
    mocker.patch.object(window, "get_location", return_value=(100, 200))

    dev_viz._create_command_palette_window()

    mock_palette.set_location.assert_called_once_with(120, 220)


def test_create_command_palette_ignores_position_errors(window, mocker):
    """Creation should swallow set_location errors."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_palette = mocker.MagicMock()
    mock_palette.set_location.side_effect = RuntimeError("boom")
    mocker.patch("arcadeactions.dev.visualizer.CommandPaletteWindow", return_value=mock_palette)
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
    mocker.patch.object(window, "get_location", return_value=(1, 2))

    dev_viz._create_command_palette_window()


def test_create_command_palette_noop_when_already_present(window, mocker):
    """Creation should return early when palette already exists."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    existing = mocker.MagicMock()
    dev_viz.command_palette_window = existing
    ctor = mocker.patch("arcadeactions.dev.visualizer.CommandPaletteWindow")

    dev_viz._create_command_palette_window()

    ctor.assert_not_called()
    assert dev_viz.command_palette_window is existing


def test_command_export_scene_prefers_examples_path(window, mocker):
    """Export command should select examples path when examples directory exists."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_export = mocker.patch("arcadeactions.dev.templates.export_template")
    mocker.patch("arcadeactions.dev.visualizer.os.path.exists", side_effect=lambda path: path == "examples")

    result = dev_viz._command_export_scene(CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[]))

    assert result is True
    mock_export.assert_called_once()
    assert mock_export.call_args.args[1] == "examples/boss_level.yaml"


def test_command_export_scene_uses_scenes_fallback(window, mocker):
    """Export command should use scenes path when examples path is unavailable."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_export = mocker.patch("arcadeactions.dev.templates.export_template")
    mocker.patch(
        "arcadeactions.dev.visualizer.os.path.exists",
        side_effect=lambda path: path == "scenes",
    )

    result = dev_viz._command_export_scene(CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[]))

    assert result is True
    assert mock_export.call_args.args[1] == "scenes/new_scene.yaml"


def test_command_import_scene_loads_first_existing(window, mocker):
    """Import command should load first existing candidate scene file."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_load = mocker.patch("arcadeactions.dev.templates.load_scene_template")
    mocker.patch("arcadeactions.dev.visualizer.os.path.exists", side_effect=lambda path: path == "scene.yaml")

    result = dev_viz._command_import_scene(CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[]))

    assert result is True
    mock_load.assert_called_once()
    assert mock_load.call_args.args[0] == "scene.yaml"


def test_command_import_scene_when_missing_files(window, mocker):
    """Import command should still return True when no candidate files exist."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    mock_load = mocker.patch("arcadeactions.dev.templates.load_scene_template")
    mocker.patch("arcadeactions.dev.visualizer.os.path.exists", return_value=False)

    result = dev_viz._command_import_scene(CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[]))

    assert result is True
    mock_load.assert_not_called()


def test_command_show_help_prints_message(window, capsys):
    """Help command should print available command summary and succeed."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)

    result = dev_viz._command_show_help(CommandExecutionContext(window=window, scene_sprites=dev_viz.scene_sprites, selection=[]))

    assert result is True
    assert "Dev Commands" in capsys.readouterr().out


def test_command_placeholder_helpers_return_false(window):
    """Disabled and placeholder command handlers should return False."""
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])
    assert DevVisualizer._command_disabled(context) is False
    assert DevVisualizer._command_not_implemented(context) is False
