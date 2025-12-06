"""
Tests for ACE visualizer overlay UI components.

Tests the inspector overlay panels, action cards, and UI rendering
following test-driven development and dependency injection principles.
"""

import pytest
import arcade
from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot
from actions.visualizer.overlay import (
    InspectorOverlay,
    ActionCard,
    TargetGroup,
)


class TestActionCard:
    """Test action card component."""

    def test_card_initialization(self):
        """Test that card initializes with snapshot data."""
        snapshot = ActionSnapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.25,
        )

        card = ActionCard(snapshot)

        assert card.snapshot == snapshot
        assert card.action_id == 1
        assert card.action_type == "MoveUntil"

    def test_card_formatting(self):
        """Test that card produces formatted display text."""
        snapshot = ActionSnapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.75,
        )

        card = ActionCard(snapshot)
        text = card.get_display_text()

        assert "MoveUntil" in text
        assert "75%" in text or "0.75" in text  # Progress display
        assert "movement" in text  # Tag

    def test_card_progress_bar_calculation(self):
        """Test progress bar width calculation."""
        snapshot = ActionSnapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.6,
        )

        card = ActionCard(snapshot, width=200)
        progress_width = card.get_progress_bar_width()

        assert progress_width == 120  # 60% of 200


class TestTargetGroup:
    """Test target group container."""

    def test_group_initialization(self):
        """Test that group initializes with target info."""
        group = TargetGroup(target_id=100, target_type="Sprite")

        assert group.target_id == 100
        assert group.target_type == "Sprite"
        assert len(group.cards) == 0

    def test_add_action_card(self):
        """Test adding action cards to group."""
        group = TargetGroup(target_id=100, target_type="Sprite")

        snapshot = ActionSnapshot(
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

        group.add_card(ActionCard(snapshot))

        assert len(group.cards) == 1
        assert group.cards[0].action_id == 1

    def test_group_header_text(self):
        """Test group header formatting."""
        group = TargetGroup(target_id=100, target_type="Sprite")
        header = group.get_header_text()

        assert "Sprite" in header
        assert str(100) in header or "100" in header


class TestInspectorOverlay:
    """Test the main inspector overlay."""

    def test_overlay_initialization(self):
        """Test that overlay initializes with debug store dependency."""
        store = DebugDataStore()
        overlay = InspectorOverlay(debug_store=store)

        assert overlay.debug_store == store
        assert overlay.visible is True  # Default to visible
        assert overlay.x >= 0
        assert overlay.y >= 0

    def test_overlay_builds_groups_from_store(self):
        """Test that overlay collects target IDs from debug store data."""
        store = DebugDataStore()

        # Add some snapshots
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=0.5,
        )
        store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=100,
            target_type="Sprite",
            tag="rotation",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=0.3,
        )

        overlay = InspectorOverlay(debug_store=store)
        overlay.update()

        # Should collect one unique target ID (100) from 2 actions
        assert overlay.get_target_ids() == [100]
        assert overlay.get_total_action_count() == 2

    def test_overlay_can_be_toggled(self):
        """Test that overlay visibility can be toggled."""
        store = DebugDataStore()
        overlay = InspectorOverlay(debug_store=store)

        initial_state = overlay.visible
        overlay.toggle()

        assert overlay.visible != initial_state

    def test_overlay_respects_disabled_state(self):
        """Test that overlay collects data even when not visible (for F8)."""
        store = DebugDataStore()
        overlay = InspectorOverlay(debug_store=store, visible=False)

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

        overlay.update()

        # Simplified overlay still tracks target IDs for F8 even when not visible
        assert overlay.get_target_ids() == [100]
        assert overlay.get_total_action_count() == 1

    def test_overlay_highlight_next_target(self):
        """Test cycling highlight across target groups."""
        store = DebugDataStore()
        # Create two targets
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

        assert overlay.highlighted_target_id is None

        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

        overlay.highlight_next()
        assert overlay.highlighted_target_id == 200

        # Wrap around
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

    def test_overlay_highlight_previous_target(self):
        """Test cycling highlight backwards across target groups."""
        store = DebugDataStore()
        for idx, target_id in enumerate((100, 200, 300)):
            store.update_snapshot(
                action_id=idx,
                action_type="MoveUntil",
                target_id=target_id,
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
        overlay.highlight_next()
        overlay.highlight_previous()
        assert overlay.highlighted_target_id == 300
        overlay.highlight_previous()
        assert overlay.highlighted_target_id == 200

    def test_overlay_clear_highlight_when_no_groups(self):
        """Removing all groups should clear highlight state."""
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

        overlay = InspectorOverlay(debug_store=store)
        overlay.update()
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

        store.clear()
        overlay.update()
        assert overlay.highlighted_target_id is None

    def test_overlay_supports_filtering_by_tag(self):
        """Test that overlay can filter actions by tag."""
        store = DebugDataStore()

        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            action_id=2,
            action_type="FadeUntil",
            target_id=100,
            target_type="Sprite",
            tag="visual",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        overlay = InspectorOverlay(debug_store=store, filter_tag="movement")
        overlay.update()

        # Should only count movement-tagged action
        assert overlay.get_total_action_count() == 1
