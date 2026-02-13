"""Unit tests for sprite property discovery and shared-property filtering."""

from __future__ import annotations

import arcade

from arcadeactions.dev.property_registry import SpritePropertyRegistry


def test_registry_discovers_builtin_and_custom_properties(test_sprite):
    """Registry should expose built-in editable fields and custom __dict__ values."""
    test_sprite.custom_health = 150
    test_sprite._internal_note = "ignore"

    registry = SpritePropertyRegistry()
    props = registry.properties_for_selection([test_sprite])
    names = {prop.name for prop in props}

    assert "center_x" in names
    assert "angle" in names
    assert "alpha" in names
    assert "custom_health" in names
    assert "_internal_note" not in names


def test_registry_returns_common_properties_for_multi_select():
    """Multi-select should include only properties common to every selected sprite."""
    sprite_a = arcade.SpriteSolidColor(width=8, height=8, color=arcade.color.RED)
    sprite_b = arcade.SpriteSolidColor(width=8, height=8, color=arcade.color.BLUE)
    sprite_a.custom_health = 100
    sprite_b.custom_health = 200
    sprite_a.only_a = 1

    registry = SpritePropertyRegistry()
    props = registry.properties_for_selection([sprite_a, sprite_b])
    names = {prop.name for prop in props}

    assert "custom_health" in names
    assert "only_a" not in names
