"""Unit tests for overlay components."""

from __future__ import annotations

import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay, ActionCard, TargetGroup


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


@pytest.fixture
def snapshot(debug_store):
    debug_store.update_snapshot(
        action_id=1,
        action_type="MoveUntil",
        target_id=100,
        target_type="Sprite",
        tag="test",
        is_active=True,
        is_paused=False,
        factor=1.0,
        elapsed=0.0,
        progress=0.5,
    )
    return debug_store.get_all_snapshots()[0]


class TestActionCard:
    def test_init(self, snapshot):
        card = ActionCard(snapshot)
        assert card.snapshot is snapshot
        assert card.width == 300
        assert card.action_id == 1
        assert card.action_type == "MoveUntil"

    def test_init_with_width(self, snapshot):
        card = ActionCard(snapshot, width=400)
        assert card.width == 400

    def test_get_display_text_with_tag(self, snapshot):
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "MoveUntil" in text
        assert "test" in text

    def test_get_display_text_without_tag(self, debug_store):
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=0.5,
        )
        snapshot = debug_store.get_all_snapshots()[0]
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "MoveUntil" in text
        assert "tag:" not in text

    def test_get_display_text_with_progress(self, snapshot):
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "progress" in text
        assert "50%" in text

    def test_get_display_text_without_progress(self, debug_store):
        debug_store.update_snapshot(
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
        snapshot = debug_store.get_all_snapshots()[0]
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "progress" not in text

    def test_get_display_text_with_paused(self, debug_store):
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=True,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        snapshot = debug_store.get_all_snapshots()[0]
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "PAUSED" in text

    def test_get_display_text_with_factor(self, debug_store):
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=2.0,
            elapsed=0.0,
            progress=None,
        )
        snapshot = debug_store.get_all_snapshots()[0]
        card = ActionCard(snapshot)
        text = card.get_display_text()
        assert "factor" in text
        assert "2.0" in text

    def test_get_progress_bar_width_with_progress(self, snapshot):
        card = ActionCard(snapshot, width=300)
        width = card.get_progress_bar_width()
        assert width == 150  # 50% of 300

    def test_get_progress_bar_width_without_progress(self, debug_store):
        debug_store.update_snapshot(
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
        snapshot = debug_store.get_all_snapshots()[0]
        card = ActionCard(snapshot)
        width = card.get_progress_bar_width()
        assert width == 0


class TestTargetGroup:
    def test_init(self):
        group = TargetGroup(target_id=100, target_type="Sprite")
        assert group.target_id == 100
        assert group.target_type == "Sprite"
        assert group.cards == []

    def test_add_card(self, snapshot):
        group = TargetGroup(target_id=100, target_type="Sprite")
        card = ActionCard(snapshot)
        group.add_card(card)
        assert len(group.cards) == 1
        assert group.cards[0] is card

    def test_get_header_text(self, snapshot):
        group = TargetGroup(target_id=100, target_type="Sprite")
        card1 = ActionCard(snapshot)
        card2 = ActionCard(snapshot)
        group.add_card(card1)
        group.add_card(card2)
        header = group.get_header_text()
        assert "Sprite" in header
        assert "100" in header
        assert "2 action(s)" in header


class TestInspectorOverlay:
    def test_init(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        assert overlay.debug_store is debug_store
        assert overlay.x == 10
        assert overlay.y == 10
        assert overlay.width == 400
        assert overlay.visible is True
        assert overlay.filter_tag is None
        assert overlay.position == "upper_left"
        assert overlay.highlighted_target_id is None

    def test_init_with_filter(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store, filter_tag="movement")
        assert overlay.filter_tag == "movement"

    def test_toggle(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        assert overlay.visible is True
        overlay.toggle()
        assert overlay.visible is False
        overlay.toggle()
        assert overlay.visible is True

    def test_cycle_position(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        assert overlay.position == "upper_left"
        assert overlay.visible is True

        overlay.cycle_position()
        assert overlay.position == "upper_right"

        overlay.cycle_position()
        assert overlay.position == "lower_right"

        overlay.cycle_position()
        assert overlay.position == "lower_left"

        overlay.cycle_position()
        assert overlay.visible is False

        overlay.cycle_position()
        assert overlay.visible is True
        assert overlay.position == "upper_left"

    def test_update_collects_target_ids(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
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
        overlay.update()
        target_ids = overlay.get_target_ids()
        assert 100 in target_ids
        assert 200 in target_ids

    def test_update_filters_by_tag(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store, filter_tag="movement")
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag="rotation",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        overlay.update()
        target_ids = overlay.get_target_ids()
        assert 100 in target_ids
        assert 200 not in target_ids

    def test_get_total_action_count(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
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
        count = overlay.get_total_action_count()
        assert count == 2

    def test_get_total_action_count_with_filter(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store, filter_tag="movement")
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
            action_id=2,
            action_type="RotateUntil",
            target_id=200,
            target_type="Sprite",
            tag="rotation",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        count = overlay.get_total_action_count()
        assert count == 1

    def test_clear_highlight(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        overlay.highlighted_target_id = 100
        overlay._highlight_index = 0
        overlay.clear_highlight()
        assert overlay.highlighted_target_id is None
        assert overlay._highlight_index == -1

    def test_highlight_next(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
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
        overlay.update()
        overlay.highlight_next()
        assert overlay.highlighted_target_id in [100, 200]

    def test_highlight_previous(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        debug_store.update_snapshot(
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
        debug_store.update_snapshot(
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
        overlay.update()
        overlay.highlight_previous()
        assert overlay.highlighted_target_id in [100, 200]

    def test_highlight_cycles_when_no_targets(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        overlay.update()
        overlay.highlight_next()
        assert overlay.highlighted_target_id is None

    def test_update_clears_highlight_when_target_removed(self, debug_store):
        overlay = InspectorOverlay(debug_store=debug_store)
        debug_store.update_snapshot(
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
        overlay.highlight_next()
        assert overlay.highlighted_target_id == 100

        # Remove the action
        debug_store.record_event("removed", 1, "MoveUntil", 100, "Sprite")
        overlay.update()
        assert overlay.highlighted_target_id is None
