"""Unit tests for visualizer collector helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from arcadeactions.base import Action
from arcadeactions.visualizer import _collectors
from arcadeactions.visualizer._collectors import (
    _collect_current_targets,
    _collect_positions_for_adapter,
    _collect_sprite_positions,
    _collect_sprite_sizes_and_ids,
    _collect_view_names,
    _iter_view_attributes,
)


@pytest.fixture(autouse=True)
def reset_collector_state():
    """Reset action and collector module state between tests."""
    original_actions = list(Action._active_actions)
    original_position_cache = dict(_collectors._position_cache)
    original_action_count = _collectors._cached_action_count
    original_action_ids = set(_collectors._cached_action_ids)
    original_targets = dict(_collectors._cached_targets)
    original_action_targets = dict(_collectors._cached_action_targets)
    try:
        Action._active_actions.clear()
        _collectors._position_cache = {}
        _collectors._cached_action_count = 0
        _collectors._cached_action_ids = set()
        _collectors._cached_targets = {}
        _collectors._cached_action_targets = {}
        yield
    finally:
        Action._active_actions[:] = original_actions
        _collectors._position_cache = original_position_cache
        _collectors._cached_action_count = original_action_count
        _collectors._cached_action_ids = original_action_ids
        _collectors._cached_targets = original_targets
        _collectors._cached_action_targets = original_action_targets


class TestCollectSpriteSizes:
    """Tests for size collection helpers."""

    def test_collect_sprite_sizes_and_ids_from_cached_targets(self):
        """Collect sizes after positions have populated cached targets."""

        class DummySprite:
            def __init__(self, x: float, y: float, width: float, height: float) -> None:
                self.center_x = x
                self.center_y = y
                self.width = width
                self.height = height

        class DummyAction:
            def __init__(self, target: object) -> None:
                self.target = target

        sprite1 = DummySprite(1, 2, 10, 20)
        sprite2 = DummySprite(3, 4, 30, 40)
        sprite_list = [sprite1, sprite2]
        Action._active_actions.append(DummyAction(sprite_list))

        _collect_sprite_positions()
        sprite_sizes, sprite_ids_in_target = _collect_sprite_sizes_and_ids()

        assert sprite_sizes[id(sprite1)] == (10, 20)
        assert sprite_sizes[id(sprite2)] == (30, 40)
        assert sprite_ids_in_target[id(sprite_list)] == [id(sprite1), id(sprite2)]

    def test_collect_sprite_sizes_skips_missing_sizes(self):
        """Skip sprites missing size data when collecting sizes."""

        class DummySprite:
            def __init__(self, x: float, y: float, width: float, height: float) -> None:
                self.center_x = x
                self.center_y = y
                self.width = width
                self.height = height

        class DummySpriteMissing:
            def __init__(self, x: float, y: float) -> None:
                self.center_x = x
                self.center_y = y

        class DummyAction:
            def __init__(self, target: object) -> None:
                self.target = target

        sprite_ok = DummySprite(5, 6, 12, 18)
        sprite_missing = DummySpriteMissing(7, 8)
        sprite_list = [sprite_ok, sprite_missing]
        Action._active_actions.append(DummyAction(sprite_list))

        _collect_sprite_positions()
        sprite_sizes, sprite_ids_in_target = _collect_sprite_sizes_and_ids()

        assert sprite_sizes == {id(sprite_ok): (12, 18)}
        assert sprite_ids_in_target[id(sprite_list)] == [id(sprite_ok)]


class TestCollectPositionHelpers:
    """Tests for position helper functions."""

    def test_collect_positions_for_adapter_averages_target(self):
        """Include average position for target id when sprites are present."""

        class DummySprite:
            def __init__(self, x: float, y: float) -> None:
                self.center_x = x
                self.center_y = y

        sprite1 = DummySprite(2, 4)
        sprite2 = DummySprite(4, 6)
        sprite_list = [sprite1, sprite2]
        adapter = _collectors.adapt_target(sprite_list)

        positions = _collect_positions_for_adapter(id(sprite_list), adapter)

        assert positions[id(sprite1)] == (2, 4)
        assert positions[id(sprite2)] == (4, 6)
        assert positions[id(sprite_list)] == (3, 5)


class TestCollectCurrentTargets:
    """Tests for collecting active action targets."""

    def test_collect_current_targets_includes_sprite_like_target(self):
        """Include sprite-like targets via the sprite adapter fallback."""

        class DummySprite:
            def __init__(self, x: float, y: float) -> None:
                self.center_x = x
                self.center_y = y

        class DummyAction:
            def __init__(self, target: object) -> None:
                self.target = target

        sprite = DummySprite(10, 20)
        action = DummyAction(sprite)

        action_targets, targets = _collect_current_targets([action])

        assert action_targets == {id(action): id(sprite)}
        assert targets == {id(sprite): sprite}

    def test_collect_current_targets_skips_unadaptable_target(self):
        """Skip targets that are neither adaptable nor sprite-like."""

        class DummyAction:
            def __init__(self, target: object) -> None:
                self.target = target

        action = DummyAction(object())
        action_targets, targets = _collect_current_targets([action])

        assert action_targets == {}
        assert targets == {}


class TestViewNames:
    """Tests for view name extraction helpers."""

    def test_collect_view_names_lists_and_sprites(self):
        """Collect target and membership names from view attributes."""

        class DummySprite:
            def __init__(self, x: float, y: float) -> None:
                self.center_x = x
                self.center_y = y

        class DummyView:
            def __init__(self) -> None:
                self.enemies = [DummySprite(1, 2), DummySprite(3, 4)]
                self.player = DummySprite(5, 6)

        view = DummyView()
        names, membership_names = _collect_view_names(view)

        assert names[id(view.enemies)] == "self.enemies"
        assert names[id(view.player)] == "self.player"
        assert len(membership_names) == 2
        for value in membership_names.values():
            assert value.startswith("Sprite#")
            assert value.endswith("in self.enemies")

    def test_iter_view_attributes_handles_no_dict(self):
        """Return empty attributes when view has no __dict__."""

        class DummyView:
            __slots__ = ()

        attributes = list(_iter_view_attributes(DummyView()))

        assert attributes == []
