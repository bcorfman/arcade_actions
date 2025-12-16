"""Unit tests for visual debug guides."""

from __future__ import annotations

import arcade
import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.guides import (
    GuideManager,
    VelocityGuide,
    BoundsGuide,
    PathGuide,
    HighlightGuide,
)


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


class TestVelocityGuide:
    def test_init(self):
        guide = VelocityGuide()
        assert guide.enabled is True
        assert guide.color == arcade.color.GREEN
        assert guide.arrows == []

    def test_init_with_params(self):
        guide = VelocityGuide(enabled=False, color=arcade.color.RED)
        assert guide.enabled is False
        assert guide.color == arcade.color.RED

    def test_toggle(self):
        guide = VelocityGuide(enabled=True)
        guide.toggle()
        assert guide.enabled is False
        guide.toggle()
        assert guide.enabled is True

    def test_update_disabled(self, debug_store):
        guide = VelocityGuide(enabled=False)
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
            velocity=(5.0, 0.0),
        )
        guide.update(debug_store.get_all_snapshots(), {100: (10.0, 20.0)})
        assert guide.arrows == []

    def test_update_with_velocity(self, debug_store):
        guide = VelocityGuide(enabled=True)
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
            velocity=(5.0, 0.0),
        )
        guide.update(debug_store.get_all_snapshots(), {100: (10.0, 20.0)})
        assert len(guide.arrows) == 1
        x1, y1, x2, y2 = guide.arrows[0]
        assert (x1, y1) == (10.0, 20.0)
        assert x2 > x1  # Moving right

    def test_update_with_sprite_ids(self, debug_store):
        guide = VelocityGuide(enabled=True)
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="SpriteList",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            velocity=(5.0, 0.0),
            metadata={"sprite_ids": [101, 102]},
        )
        guide.update(
            debug_store.get_all_snapshots(),
            {101: (10.0, 20.0), 102: (30.0, 40.0)},
        )
        assert len(guide.arrows) == 2

    def test_update_no_velocity(self, debug_store):
        guide = VelocityGuide(enabled=True)
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
            velocity=None,
        )
        guide.update(debug_store.get_all_snapshots(), {100: (10.0, 20.0)})
        assert guide.arrows == []

    def test_update_no_position(self, debug_store):
        guide = VelocityGuide(enabled=True)
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
            velocity=(5.0, 0.0),
        )
        guide.update(debug_store.get_all_snapshots(), {})
        assert guide.arrows == []


class TestBoundsGuide:
    def test_init(self):
        guide = BoundsGuide()
        assert guide.enabled is True
        assert guide.color == arcade.color.RED
        assert guide.rectangles == []

    def test_init_with_params(self):
        guide = BoundsGuide(enabled=False, color=arcade.color.BLUE)
        assert guide.enabled is False
        assert guide.color == arcade.color.BLUE

    def test_toggle(self):
        guide = BoundsGuide(enabled=True)
        guide.toggle()
        assert guide.enabled is False

    def test_update_disabled(self, debug_store):
        guide = BoundsGuide(enabled=False)
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
            bounds=(0.0, 0.0, 800.0, 600.0),
        )
        guide.update(debug_store.get_all_snapshots())
        assert guide.rectangles == []

    def test_update_with_bounds(self, debug_store):
        guide = BoundsGuide(enabled=True)
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
            bounds=(0.0, 0.0, 800.0, 600.0),
        )
        guide.update(debug_store.get_all_snapshots())
        assert len(guide.rectangles) == 1
        assert guide.rectangles[0] == (0.0, 0.0, 800.0, 600.0)

    def test_update_deduplicates_bounds(self, debug_store):
        guide = BoundsGuide(enabled=True)
        bounds = (0.0, 0.0, 800.0, 600.0)
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
            bounds=bounds,
        )
        debug_store.update_snapshot(
            action_id=2,
            action_type="MoveUntil",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            bounds=bounds,
        )
        guide.update(debug_store.get_all_snapshots())
        assert len(guide.rectangles) == 1

    def test_update_no_bounds(self, debug_store):
        guide = BoundsGuide(enabled=True)
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
            bounds=None,
        )
        guide.update(debug_store.get_all_snapshots())
        assert guide.rectangles == []


class TestPathGuide:
    def test_init(self):
        guide = PathGuide()
        assert guide.enabled is True
        assert guide.color == arcade.color.BLUE
        assert guide.paths == []

    def test_init_with_params(self):
        guide = PathGuide(enabled=False, color=arcade.color.GREEN)
        assert guide.enabled is False
        assert guide.color == arcade.color.GREEN

    def test_toggle(self):
        guide = PathGuide(enabled=True)
        guide.toggle()
        assert guide.enabled is False

    def test_update_disabled(self, debug_store):
        guide = PathGuide(enabled=False)
        debug_store.update_snapshot(
            action_id=1,
            action_type="FollowPathUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            metadata={"path_points": [(0, 0), (100, 100)]},
        )
        guide.update(debug_store.get_all_snapshots())
        assert guide.paths == []

    def test_update_with_path(self, debug_store):
        guide = PathGuide(enabled=True)
        path_points = [(0, 0), (100, 100), (200, 200)]
        debug_store.update_snapshot(
            action_id=1,
            action_type="FollowPathUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            metadata={"path_points": path_points},
        )
        guide.update(debug_store.get_all_snapshots())
        assert len(guide.paths) == 1
        assert guide.paths[0] == path_points

    def test_update_wrong_action_type(self, debug_store):
        guide = PathGuide(enabled=True)
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
            metadata={"path_points": [(0, 0), (100, 100)]},
        )
        guide.update(debug_store.get_all_snapshots())
        assert guide.paths == []

    def test_update_no_path_points(self, debug_store):
        guide = PathGuide(enabled=True)
        debug_store.update_snapshot(
            action_id=1,
            action_type="FollowPathUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            metadata={},
        )
        guide.update(debug_store.get_all_snapshots())
        assert guide.paths == []


class TestHighlightGuide:
    def test_init(self):
        guide = HighlightGuide()
        assert guide.enabled is True
        assert guide.color == arcade.color.LIME_GREEN
        assert guide.rectangles == []

    def test_init_with_params(self):
        guide = HighlightGuide(enabled=False, color=arcade.color.YELLOW)
        assert guide.enabled is False
        assert guide.color == arcade.color.YELLOW

    def test_toggle(self):
        guide = HighlightGuide(enabled=True)
        guide.toggle()
        assert guide.enabled is False

    def test_update_disabled(self):
        guide = HighlightGuide(enabled=False)
        guide.update(100, {100: (10.0, 20.0)}, {100: (50.0, 50.0)})
        assert guide.rectangles == []

    def test_update_no_highlight(self):
        guide = HighlightGuide(enabled=True)
        guide.update(None, {100: (10.0, 20.0)}, {100: (50.0, 50.0)})
        assert guide.rectangles == []

    def test_update_with_single_sprite(self):
        guide = HighlightGuide(enabled=True)
        guide.update(
            highlighted_target_id=100,
            sprite_positions={100: (100.0, 200.0)},
            sprite_sizes={100: (50.0, 50.0)},
        )
        assert len(guide.rectangles) == 1
        left, bottom, right, top = guide.rectangles[0]
        assert left == 75.0  # 100 - 50/2
        assert right == 125.0  # 100 + 50/2
        assert bottom == 175.0  # 200 - 50/2
        assert top == 225.0  # 200 + 50/2

    def test_update_with_sprite_list(self):
        guide = HighlightGuide(enabled=True)
        guide.update(
            highlighted_target_id=100,
            sprite_positions={101: (10.0, 20.0), 102: (30.0, 40.0)},
            sprite_sizes={101: (20.0, 20.0), 102: (20.0, 20.0)},
            sprite_ids_in_target={100: [101, 102]},
        )
        assert len(guide.rectangles) == 2

    def test_update_missing_position(self):
        guide = HighlightGuide(enabled=True)
        guide.update(
            highlighted_target_id=100,
            sprite_positions={},
            sprite_sizes={100: (50.0, 50.0)},
        )
        assert guide.rectangles == []

    def test_update_missing_size(self):
        guide = HighlightGuide(enabled=True)
        guide.update(
            highlighted_target_id=100,
            sprite_positions={100: (10.0, 20.0)},
            sprite_sizes={},
        )
        assert guide.rectangles == []


class TestGuideManager:
    def test_init(self):
        manager = GuideManager()
        assert isinstance(manager.velocity_guide, VelocityGuide)
        assert isinstance(manager.bounds_guide, BoundsGuide)
        assert isinstance(manager.path_guide, PathGuide)
        assert isinstance(manager.highlight_guide, HighlightGuide)
        assert manager.velocity_guide.enabled is False
        assert manager.bounds_guide.enabled is False
        assert manager.path_guide.enabled is False
        assert manager.highlight_guide.enabled is True  # Always enabled

    def test_init_with_enabled(self):
        manager = GuideManager(initial_enabled=True)
        assert manager.velocity_guide.enabled is True
        assert manager.bounds_guide.enabled is True
        assert manager.path_guide.enabled is True

    def test_toggle_all(self):
        manager = GuideManager(initial_enabled=False)
        manager.toggle_all()
        assert manager.velocity_guide.enabled is True
        assert manager.bounds_guide.enabled is True
        assert manager.path_guide.enabled is True
        # highlight_guide should not be toggled

    def test_toggle_velocity(self):
        manager = GuideManager(initial_enabled=False)
        manager.toggle_velocity()
        assert manager.velocity_guide.enabled is True
        manager.toggle_velocity()
        assert manager.velocity_guide.enabled is False

    def test_toggle_bounds(self):
        manager = GuideManager(initial_enabled=False)
        manager.toggle_bounds()
        assert manager.bounds_guide.enabled is True

    def test_toggle_path(self):
        manager = GuideManager(initial_enabled=False)
        manager.toggle_path()
        assert manager.path_guide.enabled is True

    def test_update(self, debug_store):
        manager = GuideManager(initial_enabled=True)
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
            velocity=(5.0, 0.0),
            bounds=(0.0, 0.0, 800.0, 600.0),
        )
        manager.update(
            debug_store.get_all_snapshots(),
            {100: (10.0, 20.0)},
            highlighted_target_id=100,
            sprite_sizes={100: (50.0, 50.0)},
        )
        assert len(manager.velocity_guide.arrows) == 1
        assert len(manager.bounds_guide.rectangles) == 1
        assert len(manager.highlight_guide.rectangles) == 1

    def test_any_enabled(self):
        manager = GuideManager(initial_enabled=False)
        assert manager.any_enabled() is True  # highlight_guide is always enabled
        manager.highlight_guide.enabled = False
        assert manager.any_enabled() is False
        manager.velocity_guide.enabled = True
        assert manager.any_enabled() is True

