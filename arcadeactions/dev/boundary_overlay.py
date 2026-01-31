"""Boundary gizmos for DevVisualizer.

Provides draggable handles to edit bounds of MoveUntil actions visually.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import arcade

if TYPE_CHECKING:
    from arcadeactions.base import Action


def _draw_centered_rectangle_outline(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    color: arcade.Color,
    border_width: float = 1,
) -> None:
    """Arcade 3.3 helper to keep legacy center-based drawing logic."""
    left = center_x - width / 2
    bottom = center_y - height / 2
    arcade.draw_lbwh_rectangle_outline(left, bottom, width, height, color, border_width)


def _draw_centered_rectangle_filled(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    color: arcade.Color,
) -> None:
    """Arcade 3.3 helper to keep legacy center-based drawing logic."""
    left = center_x - width / 2
    bottom = center_y - height / 2
    arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, color)


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
        self._bounded_action: Action | None = None
        self._metadata_config: dict | None = None
        self._update_handles()

    def _update_handles(self) -> None:
        """Update handle positions based on current bounds."""
        from arcadeactions.base import Action

        # Find MoveUntil action with bounds on this sprite
        self._bounded_action = None
        self._handles.clear()

        # Check all actions on this sprite for a runtime bounded action
        self._bounded_action = None
        self._metadata_config = None
        self._handles.clear()

        for action in Action.get_actions_for_target(self.sprite):
            if action.bounds is not None:
                self._bounded_action = action
                break

        # If no runtime action found, fall back to edit-mode metadata configs
        try:
            configs = self.sprite._action_configs
        except AttributeError:
            configs = None

        if self._bounded_action is None and configs is not None:
            for config in configs:
                # Look for explicit MoveUntil metadata (edit mode)
                if config.get("action_type") == "MoveUntil":
                    bounds = config.get("bounds")
                    if bounds is not None:
                        self._metadata_config = config
                        break

            if self._metadata_config is None:
                return

            # Use bounds from metadata config to create handles
            bounds = self._metadata_config.get("bounds")
            left, bottom, right, top = bounds

            # Create four corner handles from metadata bounds
            self._handles = [
                BoundaryHandle(left, bottom, "bottom_left"),
                BoundaryHandle(right, bottom, "bottom_right"),
                BoundaryHandle(left, top, "top_left"),
                BoundaryHandle(right, top, "top_right"),
            ]
            return

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

    def has_bounded_action(self) -> bool:
        """
        Check if sprite has a bounded action with bounds (runtime or metadata).

        Returns:
            True if bounded action exists (runtime) or metadata config exists (edit mode)
        """
        return self._bounded_action is not None or self._metadata_config is not None

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
        # Allow metadata-based editing when no runtime action exists
        if self._bounded_action is None and self._metadata_config is None:
            return

        handle.x += dx
        handle.y += dy
        self._sync_handle_edges(handle)

        bounds = self._calculate_bounds_from_handles()
        if bounds is None:
            return
        self._apply_bounds(bounds)

    def _sync_handle_edges(self, handle: BoundaryHandle) -> None:
        for h in self._handles:
            if h == handle:
                continue
            if "left" in handle.handle_type and "left" in h.handle_type:
                h.x = handle.x
            if "right" in handle.handle_type and "right" in h.handle_type:
                h.x = handle.x
            if "bottom" in handle.handle_type and "bottom" in h.handle_type:
                h.y = handle.y
            if "top" in handle.handle_type and "top" in h.handle_type:
                h.y = handle.y

    def _calculate_bounds_from_handles(self) -> tuple[float, float, float, float] | None:
        if len(self._handles) != 4:
            return None

        left_handles = [h for h in self._handles if "left" in h.handle_type]
        right_handles = [h for h in self._handles if "right" in h.handle_type]
        bottom_handles = [h for h in self._handles if "bottom" in h.handle_type]
        top_handles = [h for h in self._handles if "top" in h.handle_type]

        left = min(h.x for h in left_handles)
        right = max(h.x for h in right_handles)
        bottom = min(h.y for h in bottom_handles)
        top = max(h.y for h in top_handles)

        if left > right:
            left, right = right, left
        if bottom > top:
            bottom, top = top, bottom

        return (left, bottom, right, top)

    def _apply_bounds(self, bounds: tuple[float, float, float, float]) -> None:
        if self._bounded_action is not None:
            self._bounded_action.set_bounds(bounds)
            return
        if self._metadata_config is None:
            return
        try:
            self._metadata_config["bounds"] = bounds
        except Exception:
            pass

    def draw(self) -> None:
        """Draw the boundary gizmo (rectangle and handles)."""
        # Support drawing from metadata config (edit mode) when no runtime action
        bounds = None
        if self._metadata_config is not None:
            bounds = self._metadata_config.get("bounds")
        elif self._bounded_action is not None:
            bounds = self._bounded_action.bounds

        if bounds is None:
            return

        left, bottom, right, top = bounds
        width = right - left
        height = top - bottom
        center_x = left + width / 2
        center_y = bottom + height / 2

        # Draw semi-transparent rectangle
        _draw_centered_rectangle_outline(
            center_x,
            center_y,
            width,
            height,
            arcade.color.CYAN,
            2,
        )
        _draw_centered_rectangle_filled(
            center_x,
            center_y,
            width,
            height,
            (*arcade.color.CYAN[:3], 32),  # Very transparent
        )

        # Draw handles
        for handle in self._handles:
            _draw_centered_rectangle_filled(
                handle.x,
                handle.y,
                handle.handle_size,
                handle.handle_size,
                arcade.color.YELLOW,
            )
            _draw_centered_rectangle_outline(
                handle.x,
                handle.y,
                handle.handle_size,
                handle.handle_size,
                arcade.color.BLACK,
                1,
            )
