"""Test suite for DevVisualizer boundary gizmos.

Tests draggable handles that edit bounds of MoveUntil actions.
"""

import arcade
import pytest

from actions.conditional import MoveUntil, infinite
from actions.dev.boundary_overlay import BoundaryGizmo
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
