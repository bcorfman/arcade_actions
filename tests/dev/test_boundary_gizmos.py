"""Test suite for DevVisualizer boundary gizmos.

Tests draggable handles that edit bounds of MoveUntil actions.
"""

import arcade
import pytest

from arcadeactions.conditional import MoveUntil, infinite
from arcadeactions.dev.boundary_overlay import BoundaryGizmo, BoundaryHandle
from tests.conftest import ActionTestBase


class TestBoundaryGizmos(ActionTestBase):
    """Test suite for boundary gizmo functionality."""

    @pytest.mark.integration
    def test_gizmo_detects_bounded_action(self, window):
        """Test that gizmo detects sprite with MoveUntil action that has bounds."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100

        # Create action with bounds
        action = MoveUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 800, 600),
            boundary_behavior="limit",
        )
        action.apply(sprite, tag="movement")

        # Gizmo should detect this action
        gizmo = BoundaryGizmo(sprite)
        assert gizmo.has_bounded_action()

    @pytest.mark.integration
    def test_gizmo_creates_handles(self, window):
        """Test that gizmo creates four corner handles."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(50, 50, 200, 200),
            boundary_behavior="limit",
        )
        action.apply(sprite, tag="movement")

        gizmo = BoundaryGizmo(sprite)
        handles = gizmo.get_handles()
        assert len(handles) == 4  # Four corner handles

    @pytest.mark.integration
    def test_gizmo_drag_updates_bounds(self, window):
        """Test dragging a handle updates the action's bounds."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 800, 600),
            boundary_behavior="limit",
        )
        action.apply(sprite, tag="movement")

        gizmo = BoundaryGizmo(sprite)

        # Find top handle and drag it down 20 pixels
        handles = gizmo.get_handles()
        top_handle = None
        for handle in handles:
            if "top" in handle.handle_type:
                top_handle = handle
                break

        if top_handle:
            original_bounds = action.bounds
            original_top = original_bounds[3]  # top is index 3

            # Simulate drag: move handle down 20 pixels
            gizmo.handle_drag(top_handle, 0, -20)

            # Bounds should be updated
            new_bounds = action.bounds
            assert new_bounds[3] == original_top - 20  # Top decreased by 20

    def test_gizmo_detects_bounded_config(self):
        """Gizmo should detect MoveUntil configs stored in metadata (edit mode)."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100

        # Store edit-mode MoveUntil config
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (3, 0),
                "bounds": (50, 50, 200, 200),
                "boundary_behavior": "limit",
            }
        ]

        gizmo = BoundaryGizmo(sprite)
        assert gizmo.has_bounded_action()
        handles = gizmo.get_handles()
        assert len(handles) == 4

    def test_gizmo_no_bounded_action(self):
        """Gizmo should ignore sprites without bounded actions or metadata."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        gizmo = BoundaryGizmo(sprite)
        assert not gizmo.has_bounded_action()
        assert gizmo.get_handles() == []

    def test_gizmo_ignores_metadata_without_bounds(self):
        """Gizmo should not create handles when MoveUntil metadata has no bounds."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite._action_configs = [{"action_type": "MoveUntil", "velocity": (1, 0)}]
        gizmo = BoundaryGizmo(sprite)
        assert not gizmo.has_bounded_action()
        assert gizmo.get_handles() == []

    def test_handle_drag_no_bounded_action_noop(self):
        """Dragging without bounded actions should be a no-op."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        gizmo = BoundaryGizmo(sprite)
        handle = gizmo.get_handle_at_point(0, 0)
        assert handle is None
        gizmo.handle_drag(BoundaryHandle(0, 0, "top_left"), 5, 5)
        assert gizmo.get_handles() == []

    def test_gizmo_drag_updates_metadata_bounds(self):
        """Dragging gizmo handles should update bounds stored in metadata when no runtime action exists."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite.center_x = 100
        sprite.center_y = 100

        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (3, 0),
                "bounds": (50, 50, 200, 200),
                "boundary_behavior": "limit",
            }
        ]

        gizmo = BoundaryGizmo(sprite)

        # Find top handle and drag it up 30 pixels
        handles = gizmo.get_handles()
        top_handle = None
        for handle in handles:
            if "top" in handle.handle_type:
                top_handle = handle
                break

        assert top_handle is not None
        original_top = sprite._action_configs[0]["bounds"][3]

        gizmo.handle_drag(top_handle, 0, 30)

        # Metadata bounds should be updated
        new_top = sprite._action_configs[0]["bounds"][3]
        assert new_top == original_top + 30

    def test_calculate_bounds_sorts_edges(self):
        """Test handle bounds sorting when handles cross."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (3, 0),
                "bounds": (50, 50, 200, 200),
                "boundary_behavior": "limit",
            }
        ]
        gizmo = BoundaryGizmo(sprite)
        # Force left/right and bottom/top to be inverted
        gizmo._handles = [
            BoundaryHandle(300, 300, "bottom_left"),
            BoundaryHandle(100, 300, "bottom_right"),
            BoundaryHandle(300, 100, "top_left"),
            BoundaryHandle(100, 100, "top_right"),
        ]

        bounds = gizmo._calculate_bounds_from_handles()

        assert bounds == (100, 100, 300, 300)

    def test_draw_renders_bounds_and_handles(self, mocker):
        """Test draw renders rectangle and handles when bounds exist."""
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (3, 0),
                "bounds": (50, 50, 200, 200),
                "boundary_behavior": "limit",
            }
        ]
        gizmo = BoundaryGizmo(sprite)

        mock_outline = mocker.patch("arcadeactions.dev.boundary_overlay._draw_centered_rectangle_outline")
        mock_filled = mocker.patch("arcadeactions.dev.boundary_overlay._draw_centered_rectangle_filled")

        gizmo.draw()

        assert mock_outline.called
        assert mock_filled.called
