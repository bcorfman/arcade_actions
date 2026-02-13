"""Unit tests for sprite property history undo/redo."""

from __future__ import annotations

from arcadeactions.dev.property_history import PropertyHistory


def test_property_history_undo_and_redo_single_sprite(test_sprite):
    """Undo/redo should restore old/new values for a sprite property."""
    history = PropertyHistory(max_changes_per_sprite=20)

    old_x = float(test_sprite.center_x)
    new_x = old_x + 50
    test_sprite.center_x = new_x
    history.record_change(test_sprite, "center_x", old_x, new_x)

    undone = history.undo(test_sprite)
    assert undone is not None
    assert undone.property_name == "center_x"
    assert test_sprite.center_x == old_x

    redone = history.redo(test_sprite)
    assert redone is not None
    assert redone.property_name == "center_x"
    assert test_sprite.center_x == new_x


def test_property_history_limits_to_max_changes(test_sprite):
    """History should keep only the most recent N changes per sprite."""
    history = PropertyHistory(max_changes_per_sprite=20)

    current = float(test_sprite.center_x)
    for _ in range(25):
        nxt = current + 1
        test_sprite.center_x = nxt
        history.record_change(test_sprite, "center_x", current, nxt)
        current = nxt

    undo_count = 0
    while history.undo(test_sprite) is not None:
        undo_count += 1

    assert undo_count == 20
