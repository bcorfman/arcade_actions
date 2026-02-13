"""Unit tests for sprite property inspector editing flows."""

from __future__ import annotations

import arcade

from arcadeactions.dev.property_history import PropertyHistory
from arcadeactions.dev.property_inspector import InMemoryClipboard, SpritePropertyInspector
from arcadeactions.dev.property_registry import SpritePropertyRegistry


class _WindowStub:
    def __init__(self, width: int = 800, height: int = 600) -> None:
        self.width = width
        self.height = height


def _make_inspector() -> tuple[SpritePropertyInspector, InMemoryClipboard]:
    clipboard = InMemoryClipboard()
    inspector = SpritePropertyInspector(
        property_registry=SpritePropertyRegistry(),
        history=PropertyHistory(max_changes_per_sprite=20),
        clipboard=clipboard,
        window=_WindowStub(),
    )
    return inspector, clipboard


def test_edit_center_x_updates_sprite_immediately(test_sprite):
    """Applying an edited value should immediately update the sprite property."""
    inspector, _ = _make_inspector()
    inspector.set_selection([test_sprite])

    inspector.apply_property_text("center_x", "420")

    assert test_sprite.center_x == 420


def test_multi_select_angle_edit_updates_all_sprites():
    """Batch edit should apply the same property value to all selected sprites."""
    sprite_a = arcade.SpriteSolidColor(width=8, height=8, color=arcade.color.RED)
    sprite_b = arcade.SpriteSolidColor(width=8, height=8, color=arcade.color.BLUE)

    inspector, _ = _make_inspector()
    inspector.set_selection([sprite_a, sprite_b])

    inspector.apply_property_text("angle", "45")

    assert sprite_a.angle == 45
    assert sprite_b.angle == 45


def test_expression_support_uses_screen_center_constant(test_sprite):
    """Numeric expressions should evaluate with SCREEN_CENTER constants."""
    inspector, _ = _make_inspector()
    inspector.set_selection([test_sprite])

    inspector.apply_property_text("center_x", "SCREEN_CENTER + 100")

    assert test_sprite.center_x == 500


def test_copy_as_python_generates_assignments_for_selection(test_sprite):
    """Copy helper should emit Python assignment lines and write to clipboard."""
    inspector, clipboard = _make_inspector()
    test_sprite.center_x = 410
    test_sprite.angle = 30
    inspector.set_selection([test_sprite])

    snippet = inspector.copy_selection_as_python(property_names=["center_x", "angle"])

    assert "sprite.center_x = 410" in snippet
    assert "sprite.angle = 30" in snippet
    assert clipboard.paste() == snippet


def test_undo_redo_property_edits(test_sprite):
    """Inspector undo/redo should replay recorded property edits."""
    inspector, _ = _make_inspector()
    inspector.set_selection([test_sprite])
    start_x = float(test_sprite.center_x)

    inspector.apply_property_text("center_x", "333")
    assert test_sprite.center_x == 333

    assert inspector.undo() is True
    assert test_sprite.center_x == start_x

    assert inspector.redo() is True
    assert test_sprite.center_x == 333
