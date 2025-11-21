"""
Visual debug guides for ACE visualizer.

Provides visual overlays for velocity vectors, boundary rectangles,
and path splines to help visualize action behavior in real-time.
"""

from __future__ import annotations

import arcade
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import ActionSnapshot


class VelocityGuide:
    """
    Renders velocity vectors as arrows.

    Shows the direction and magnitude of movement for MoveUntil actions.
    """

    def __init__(self, enabled: bool = True, color: tuple[int, int, int] = arcade.color.GREEN):
        """
        Initialize velocity guide.

        Args:
            enabled: Whether guide is initially enabled
            color: Color for velocity arrows
        """
        self.enabled = enabled
        self.color = color
        self.arrows: list[tuple[float, float, float, float]] = []  # (x1, y1, x2, y2)

    def toggle(self) -> None:
        """Toggle guide enabled state."""
        self.enabled = not self.enabled

    def update(
        self,
        snapshots: list[ActionSnapshot],
        sprite_positions: dict[int, tuple[float, float]],
    ) -> None:
        """
        Update arrow data from snapshots.

        Args:
            snapshots: List of action snapshots
            sprite_positions: Dict mapping target_id to (x, y) position
        """
        self.arrows = []

        if not self.enabled:
            return

        for snapshot in snapshots:
            if snapshot.velocity is None:
                continue

            # Get sprite position
            target_id = snapshot.target_id
            vx, vy = snapshot.velocity

            metadata = snapshot.metadata or {}
            sprite_ids = metadata.get("sprite_ids")

            def add_arrow(position: tuple[float, float]) -> None:
                x, y = position
                end_x = x + vx * 10
                end_y = y + vy * 10
                self.arrows.append((x, y, end_x, end_y))

            if sprite_ids:
                for sprite_id in sprite_ids:
                    position = sprite_positions.get(sprite_id)
                    if position is not None:
                        add_arrow(position)
                continue

            position = sprite_positions.get(target_id)
            if position is not None:
                add_arrow(position)


class BoundsGuide:
    """
    Renders boundary rectangles.

    Shows the bounds for MoveUntil actions with boundary checking enabled.
    """

    def __init__(self, enabled: bool = True, color: tuple[int, int, int] = arcade.color.RED):
        """
        Initialize bounds guide.

        Args:
            enabled: Whether guide is initially enabled
            color: Color for boundary rectangles
        """
        self.enabled = enabled
        self.color = color
        self.rectangles: list[tuple[float, float, float, float]] = []  # (left, bottom, right, top)

    def toggle(self) -> None:
        """Toggle guide enabled state."""
        self.enabled = not self.enabled

    def update(self, snapshots: list[ActionSnapshot]) -> None:
        """
        Update rectangle data from snapshots.

        Args:
            snapshots: List of action snapshots
        """
        self.rectangles = []

        if not self.enabled:
            return

        # Collect unique bounds (deduplicate)
        unique_bounds = set()

        for snapshot in snapshots:
            if snapshot.bounds is not None:
                unique_bounds.add(snapshot.bounds)

        self.rectangles = list(unique_bounds)


class PathGuide:
    """
    Renders path splines.

    Shows the path for FollowPathUntil actions.
    """

    def __init__(self, enabled: bool = True, color: tuple[int, int, int] = arcade.color.BLUE):
        """
        Initialize path guide.

        Args:
            enabled: Whether guide is initially enabled
            color: Color for path splines
        """
        self.enabled = enabled
        self.color = color
        self.paths: list[list[tuple[float, float]]] = []  # List of point lists

    def toggle(self) -> None:
        """Toggle guide enabled state."""
        self.enabled = not self.enabled

    def update(self, snapshots: list[ActionSnapshot]) -> None:
        """
        Update path data from snapshots.

        Args:
            snapshots: List of action snapshots
        """
        self.paths = []

        if not self.enabled:
            return

        for snapshot in snapshots:
            if snapshot.action_type == "FollowPathUntil" and snapshot.metadata:
                path_points = snapshot.metadata.get("path_points")
                if path_points:
                    self.paths.append(path_points)


class GuideManager:
    """
    Manages all visual debug guides.

    Coordinates velocity, bounds, and path guides and provides
    unified toggle/update interface.
    """

    def __init__(self, initial_enabled: bool = False):
        """
        Initialize guide manager with all guides.
        
        Args:
            initial_enabled: Whether guides should be enabled initially (default: False)
        """
        self.velocity_guide = VelocityGuide(enabled=initial_enabled)
        self.bounds_guide = BoundsGuide(enabled=initial_enabled)
        self.path_guide = PathGuide(enabled=initial_enabled)

    def toggle_all(self) -> None:
        """Toggle all guides on/off."""
        self.velocity_guide.toggle()
        self.bounds_guide.toggle()
        self.path_guide.toggle()

    def toggle_velocity(self) -> None:
        """Toggle velocity guide."""
        self.velocity_guide.toggle()

    def toggle_bounds(self) -> None:
        """Toggle bounds guide."""
        self.bounds_guide.toggle()

    def toggle_path(self) -> None:
        """Toggle path guide."""
        self.path_guide.toggle()

    def update(
        self,
        snapshots: list[ActionSnapshot],
        sprite_positions: dict[int, tuple[float, float]],
    ) -> None:
        """
        Update all guides from snapshot data.

        Args:
            snapshots: List of action snapshots
            sprite_positions: Dict mapping target_id to (x, y) position
        """
        self.velocity_guide.update(snapshots, sprite_positions)
        self.bounds_guide.update(snapshots)
        self.path_guide.update(snapshots)

    def any_enabled(self) -> bool:
        """Return True if any guide is enabled."""
        return self.velocity_guide.enabled or self.bounds_guide.enabled or self.path_guide.enabled
