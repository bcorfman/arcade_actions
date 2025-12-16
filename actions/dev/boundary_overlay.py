"""Boundary gizmos for DevVisualizer.

Provides draggable handles to edit bounds of MoveUntil actions visually.
"""

from __future__ import annotations

import arcade
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.conditional import MoveUntil


class BoundaryHandle:
    """A draggable handle for editing boundary bounds."""

    def __init__(self, x: float, y: float, handle_type: str):
        """
        Initialize boundary handle.

        Args:
            x: Handle X position
            y: Handle Y position
            handle_type: "left", "right", "bottom", or "top"
        """
        self.x = x
        self.y = y
        self.handle_type = handle_type
        self.handle_size = 8  # Size of handle square

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if point is within handle bounds.

        Args:
            x: Point X coordinate
            y: Point Y coordinate

        Returns:
            True if point is within handle
        """
        half_size = self.handle_size / 2
        return self.x - half_size <= x <= self.x + half_size and self.y - half_size <= y <= self.y + half_size


class BoundaryGizmo:
    """
    Gizmo for editing bounds of MoveUntil actions.

    Displays a semi-transparent rectangle showing bounds and four
    draggable corner handles for editing.
    """

    def __init__(self, sprite: arcade.Sprite):
        """
        Initialize boundary gizmo for a sprite.

        Args:
            sprite: Sprite to check for bounded actions
        """
        self.sprite = sprite
        self._handles: list[BoundaryHandle] = []
        self._bounded_action: MoveUntil | None = None
        self._update_handles()

    def _update_handles(self) -> None:
        """Update handle positions based on current bounds."""
        from actions.base import Action

        # Find MoveUntil action with bounds on this sprite
        self._bounded_action = None
        self._handles.clear()

        MoveUntil = self._get_move_until_class()

        # Check all actions on this sprite
        for action in Action.get_actions_for_target(self.sprite):
            if isinstance(action, MoveUntil):
                if hasattr(action, "bounds") and action.bounds is not None:
                    self._bounded_action = action
                    break

        if self._bounded_action is None:
            return

        bounds = self._bounded_action.bounds
        left, bottom, right, top = bounds

        # Create four corner handles
        self._handles = [
            BoundaryHandle(left, bottom, "bottom_left"),
            BoundaryHandle(right, bottom, "bottom_right"),
            BoundaryHandle(left, top, "top_left"),
            BoundaryHandle(right, top, "top_right"),
        ]

    def _get_move_until_class(self):
        """Get MoveUntil class (avoid circular import)."""
        from actions.conditional import MoveUntil

        return MoveUntil

    def has_bounded_action(self) -> bool:
        """
        Check if sprite has a MoveUntil action with bounds.

        Returns:
            True if bounded action exists
        """
        return self._bounded_action is not None

    def get_handles(self) -> list[BoundaryHandle]:
        """
        Get list of boundary handles.

        Returns:
            List of BoundaryHandle objects
        """
        return self._handles.copy()

    def get_handle_at_point(self, x: float, y: float) -> BoundaryHandle | None:
        """
        Find handle at given point.

        Args:
            x: Point X coordinate
            y: Point Y coordinate

        Returns:
            BoundaryHandle if found, None otherwise
        """
        for handle in self._handles:
            if handle.contains_point(x, y):
                return handle
        return None

    def handle_drag(self, handle: BoundaryHandle, dx: float, dy: float) -> None:
        """
        Handle dragging a boundary handle.

        Args:
            handle: Handle being dragged
            dx: X delta
            dy: Y delta
        """
        if self._bounded_action is None:
            return

        # Update handle position
        handle.x += dx
        handle.y += dy

        # Update all handles that share the same edge
        # Corner handles affect two edges
        for h in self._handles:
            if h == handle:
                continue
            # If handle shares the same edge, update it too
            if "left" in handle.handle_type and "left" in h.handle_type:
                h.x = handle.x
            if "right" in handle.handle_type and "right" in h.handle_type:
                h.x = handle.x
            if "bottom" in handle.handle_type and "bottom" in h.handle_type:
                h.y = handle.y
            if "top" in handle.handle_type and "top" in h.handle_type:
                h.y = handle.y

        # Recalculate bounds from handle positions
        if len(self._handles) == 4:
            left_handles = [h for h in self._handles if "left" in h.handle_type]
            right_handles = [h for h in self._handles if "right" in h.handle_type]
            bottom_handles = [h for h in self._handles if "bottom" in h.handle_type]
            top_handles = [h for h in self._handles if "top" in h.handle_type]

            left = min(h.x for h in left_handles)
            right = max(h.x for h in right_handles)
            bottom = min(h.y for h in bottom_handles)
            top = max(h.y for h in top_handles)

            # Validate bounds: ensure left <= right and bottom <= top
            # If handles are dragged past each other, swap them to maintain valid bounds
            if left > right:
                left, right = right, left
            if bottom > top:
                bottom, top = top, bottom

            # Update action bounds
            self._bounded_action.set_bounds((left, bottom, right, top))

    def draw(self) -> None:
        """Draw the boundary gizmo (rectangle and handles)."""
        if self._bounded_action is None:
            return

        bounds = self._bounded_action.bounds
        if bounds is None:
            return

        left, bottom, right, top = bounds
        width = right - left
        height = top - bottom
        center_x = left + width / 2
        center_y = bottom + height / 2

        # Draw semi-transparent rectangle
        arcade.draw_rectangle_outline(
            center_x,
            center_y,
            width,
            height,
            arcade.color.CYAN,
            2,
        )
        arcade.draw_rectangle_filled(
            center_x,
            center_y,
            width,
            height,
            (*arcade.color.CYAN[:3], 32),  # Very transparent
        )

        # Draw handles
        for handle in self._handles:
            arcade.draw_rectangle_filled(
                handle.x,
                handle.y,
                handle.handle_size,
                handle.handle_size,
                arcade.color.YELLOW,
            )
            arcade.draw_rectangle_outline(
                handle.x,
                handle.y,
                handle.handle_size,
                handle.handle_size,
                arcade.color.BLACK,
                1,
            )


