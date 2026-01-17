"""
Tests for simplified ACE visualizer overlay.

Tests the minimal inspector overlay that only shows action count
and cycles through corner positions.
"""

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay


class TestSimplifiedOverlay:
    """Test simplified overlay with corner cycling."""

    def test_overlay_shows_action_count(self):
        """Test that overlay tracks total action count."""
        store = DebugDataStore()
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        overlay = InspectorOverlay(debug_store=store)
        overlay.update()

        assert overlay.get_total_action_count() == 2

    def test_overlay_cycles_through_corners(self):
        """Test that overlay cycles through four corners then off."""
        store = DebugDataStore()
        overlay = InspectorOverlay(debug_store=store)

        # Initial position: upper-left
        assert overlay.position == "upper_left"
        assert overlay.visible is True

        # Cycle to upper-right
        overlay.cycle_position()
        assert overlay.position == "upper_right"
        assert overlay.visible is True

        # Cycle to lower-right
        overlay.cycle_position()
        assert overlay.position == "lower_right"
        assert overlay.visible is True

        # Cycle to lower-left
        overlay.cycle_position()
        assert overlay.position == "lower_left"
        assert overlay.visible is True

        # Cycle to off
        overlay.cycle_position()
        assert overlay.visible is False

        # Cycle back to upper-left
        overlay.cycle_position()
        assert overlay.position == "upper_left"
        assert overlay.visible is True

    def test_overlay_highlight_still_cycles_targets(self):
        """Test that F8 highlighting still cycles through targets."""
        store = DebugDataStore()
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        overlay = InspectorOverlay(debug_store=store)
        overlay.update()

        # Initially no highlight
        assert overlay.highlighted_target_id is None

        # Highlight first target
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

        # Highlight second target
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 200

        # Wrap around
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

    def test_overlay_get_highlighted_target_ids(self):
        """Test that overlay can return list of unique target IDs for highlighting."""
        store = DebugDataStore()
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            action_id=2,
            action_type="MoveUntil",  # Same target, different action
            target_id=100,
            target_type="Sprite",
            tag="other",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            action_id=3,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        overlay = InspectorOverlay(debug_store=store)
        overlay.update()

        # Should have 2 unique target IDs (100 and 200)
        target_ids = overlay.get_target_ids()
        assert len(target_ids) == 2
        assert 100 in target_ids
        assert 200 in target_ids
