"""
Visual debug guides for ACE visualizer.

Provides visual overlays for velocity vectors, boundary rectangles,
and path splines to help visualize action behavior in real-time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import arcade

if TYPE_CHECKING:
    from arcadeactions.visualizer.instrumentation import ActionSnapshot


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
            velocity = snapshot.velocity
            if velocity is None:
                continue

            sprite_ids = self._get_sprite_ids(snapshot)
            if sprite_ids:
                self._add_arrows_for_sprite_ids(velocity, sprite_ids, sprite_positions)
                continue

            self._add_arrow_for_target(snapshot.target_id, velocity, sprite_positions)

    def _get_sprite_ids(self, snapshot: ActionSnapshot) -> list[int] | None:
        metadata = snapshot.metadata or {}
        sprite_ids = metadata.get("sprite_ids")
        if sprite_ids:
            return list(sprite_ids)
        return None

    def _add_arrows_for_sprite_ids(
        self,
        velocity: tuple[float, float],
        sprite_ids: list[int],
        sprite_positions: dict[int, tuple[float, float]],
    ) -> None:
        for sprite_id in sprite_ids:
            position = sprite_positions.get(sprite_id)
            if position is not None:
                self._add_arrow(position, velocity)

    def _add_arrow_for_target(
        self,
        target_id: int,
        velocity: tuple[float, float],
        sprite_positions: dict[int, tuple[float, float]],
    ) -> None:
        position = sprite_positions.get(target_id)
        if position is not None:
            self._add_arrow(position, velocity)

    def _add_arrow(self, position: tuple[float, float], velocity: tuple[float, float]) -> None:
        x, y = position
        vx, vy = velocity
        end_x = x + vx * 10
        end_y = y + vy * 10
        self.arrows.append((x, y, end_x, end_y))


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


class HighlightGuide:
    """
    Renders bounding boxes around highlighted sprites.

    Shows which sprite(s) are currently highlighted via F8 key.
    """

    def __init__(self, enabled: bool = True, color: tuple[int, int, int] = arcade.color.LIME_GREEN):
        """
        Initialize highlight guide.

        Args:
            enabled: Whether guide is initially enabled
            color: Color for highlight boxes
        """
        self.enabled = enabled
        self.color = color
        self.rectangles: list[tuple[float, float, float, float]] = []  # (left, bottom, right, top)

    def toggle(self) -> None:
        """Toggle guide enabled state."""
        self.enabled = not self.enabled

    def update(
        self,
        highlighted_target_id: int | None,
        sprite_positions: dict[int, tuple[float, float]],
        sprite_sizes: dict[int, tuple[float, float]],
        sprite_ids_in_target: dict[int, list[int]] | None = None,
    ) -> None:
        """
        Update highlight rectangles.

        Args:
            highlighted_target_id: ID of the target to highlight (None for no highlight)
            sprite_positions: Dict mapping sprite/target ID to (x, y) center position
            sprite_sizes: Dict mapping sprite ID to (width, height)
            sprite_ids_in_target: Dict mapping target ID to list of sprite IDs it contains
        """
        self.rectangles = []

        if not self.enabled or highlighted_target_id is None:
            return

        sprite_ids = self._resolve_sprite_ids(highlighted_target_id, sprite_ids_in_target)
        for sprite_id in sprite_ids:
            rectangle = self._build_rectangle(sprite_id, sprite_positions, sprite_sizes)
            if rectangle is not None:
                self.rectangles.append(rectangle)

    def _resolve_sprite_ids(
        self,
        highlighted_target_id: int,
        sprite_ids_in_target: dict[int, list[int]] | None,
    ) -> list[int]:
        if sprite_ids_in_target and highlighted_target_id in sprite_ids_in_target:
            return list(sprite_ids_in_target[highlighted_target_id])
        return [highlighted_target_id]

    def _build_rectangle(
        self,
        sprite_id: int,
        sprite_positions: dict[int, tuple[float, float]],
        sprite_sizes: dict[int, tuple[float, float]],
    ) -> tuple[float, float, float, float] | None:
        position = sprite_positions.get(sprite_id)
        size = sprite_sizes.get(sprite_id)
        if not position or not size:
            return None
        center_x, center_y = position
        width, height = size
        half_width = width / 2
        half_height = height / 2
        left = center_x - half_width
        right = center_x + half_width
        bottom = center_y - half_height
        top = center_y + half_height
        return (left, bottom, right, top)


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
        self.highlight_guide = HighlightGuide(enabled=True)  # Always enabled for F8

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
        highlighted_target_id: int | None = None,
        sprite_sizes: dict[int, tuple[float, float]] | None = None,
        sprite_ids_in_target: dict[int, list[int]] | None = None,
    ) -> None:
        """
        Update all guides from snapshot data.

        Args:
            snapshots: List of action snapshots
            sprite_positions: Dict mapping target_id to (x, y) position
            highlighted_target_id: Optional ID of highlighted target for highlight guide
            sprite_sizes: Optional dict mapping sprite ID to (width, height)
            sprite_ids_in_target: Optional dict mapping target ID to list of sprite IDs
        """
        self.velocity_guide.update(snapshots, sprite_positions)
        self.bounds_guide.update(snapshots)
        self.path_guide.update(snapshots)

        # Update highlight guide
        if sprite_sizes is None:
            sprite_sizes = {}
        self.highlight_guide.update(
            highlighted_target_id=highlighted_target_id,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes,
            sprite_ids_in_target=sprite_ids_in_target,
        )

    def any_enabled(self) -> bool:
        """Return True if any guide is enabled."""
        return (
            self.velocity_guide.enabled
            or self.bounds_guide.enabled
            or self.path_guide.enabled
            or self.highlight_guide.enabled
        )
