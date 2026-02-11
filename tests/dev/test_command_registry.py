"""Tests for dev command registry behavior."""

from __future__ import annotations

import arcade

from arcadeactions.dev.command_registry import CommandExecutionContext, CommandRegistry


def test_register_and_resolve_enabled_command(window):
    """Registered enabled commands are discoverable and executable."""
    calls: list[str] = []
    registry = CommandRegistry()
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])

    def handler(ctx: CommandExecutionContext) -> bool:
        calls.append(f"handled:{len(ctx.selection)}")
        return True

    registry.register_command(
        key=arcade.key.E,
        name="Export Scene",
        category="Export/Import",
        handler=handler,
    )

    command = registry.find_enabled_command_for_key(arcade.key.E, context)
    assert command is not None
    assert command.name == "Export Scene"
    assert registry.execute_key(arcade.key.E, context) is True
    assert calls == ["handled:0"]


def test_disabled_command_is_not_resolved(window):
    """Commands with failing enabled checks are not returned for key execution."""
    registry = CommandRegistry()
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])

    registry.register_command(
        key=arcade.key.G,
        name="Toggle Grid",
        category="Visualization",
        handler=lambda _ctx: True,
        enabled_check=lambda _ctx: False,
    )

    assert registry.find_enabled_command_for_key(arcade.key.G, context) is None
    assert registry.execute_key(arcade.key.G, context) is False


def test_enabled_commands_sorted_by_category_then_name(window):
    """Enabled command listing should be stable for UI rendering."""
    registry = CommandRegistry()
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])

    registry.register_command(
        key=arcade.key.I,
        name="Import Scene",
        category="Export/Import",
        handler=lambda _ctx: True,
    )
    registry.register_command(
        key=arcade.key.H,
        name="Show Help",
        category="Other",
        handler=lambda _ctx: True,
    )
    registry.register_command(
        key=arcade.key.E,
        name="Export Scene",
        category="Export/Import",
        handler=lambda _ctx: True,
    )

    commands = registry.get_enabled_commands(context)
    assert [c.name for c in commands] == ["Export Scene", "Import Scene", "Show Help"]


def test_enabled_check_exception_disables_command(window):
    """enabled_check exceptions should safely disable commands."""
    registry = CommandRegistry()
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])

    registry.register_command(
        key=arcade.key.H,
        name="Help",
        category="Other",
        handler=lambda _ctx: True,
        enabled_check=lambda _ctx: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert registry.get_enabled_commands(context) == []


def test_execute_key_returns_false_when_handler_raises(window):
    """Handler exceptions should be swallowed and report not executed."""
    registry = CommandRegistry()
    context = CommandExecutionContext(window=window, scene_sprites=arcade.SpriteList(), selection=[])

    registry.register_command(
        key=arcade.key.E,
        name="Export",
        category="Export/Import",
        handler=lambda _ctx: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert registry.execute_key(arcade.key.E, context) is False
