"""Undo/redo history for sprite property edits."""

from __future__ import annotations

from collections import deque

import arcade


class PropertyChange:
    """Single property mutation for one sprite."""

    def __init__(self, sprite: arcade.Sprite, property_name: str, old_value: object, new_value: object) -> None:
        self.sprite = sprite
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value


class PropertyHistory:
    """Per-sprite bounded undo/redo stacks."""

    def __init__(self, max_changes_per_sprite: int = 20) -> None:
        self._max_changes_per_sprite = max_changes_per_sprite
        self._undo: dict[arcade.Sprite, deque[PropertyChange]] = {}
        self._redo: dict[arcade.Sprite, deque[PropertyChange]] = {}

    def _ensure_sprite(self, sprite: arcade.Sprite) -> None:
        if sprite not in self._undo:
            self._undo[sprite] = deque(maxlen=self._max_changes_per_sprite)
        if sprite not in self._redo:
            self._redo[sprite] = deque(maxlen=self._max_changes_per_sprite)

    def record_change(self, sprite: arcade.Sprite, property_name: str, old_value: object, new_value: object) -> None:
        """Record a new property change and clear redo stack."""
        self._ensure_sprite(sprite)
        self._undo[sprite].append(PropertyChange(sprite, property_name, old_value, new_value))
        self._redo[sprite].clear()

    def undo(self, sprite: arcade.Sprite) -> PropertyChange | None:
        """Undo the most recent change for a sprite and return it."""
        self._ensure_sprite(sprite)
        if not self._undo[sprite]:
            return None

        change = self._undo[sprite].pop()
        setattr(change.sprite, change.property_name, change.old_value)
        self._redo[sprite].append(change)
        return change

    def redo(self, sprite: arcade.Sprite) -> PropertyChange | None:
        """Redo the most recently undone change for a sprite and return it."""
        self._ensure_sprite(sprite)
        if not self._redo[sprite]:
            return None

        change = self._redo[sprite].pop()
        setattr(change.sprite, change.property_name, change.new_value)
        self._undo[sprite].append(change)
        return change
