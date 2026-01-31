"""Collector helpers for ACE visualizer attach."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from arcadeactions.base import Action
from arcadeactions._action_targets import TargetAdapter, adapt_target

SpritePositionsProvider = Callable[[], dict[int, tuple[float, float]]]
TargetNamesProvider = Callable[[], dict[int, str]]

class PositionSprite(Protocol):
    center_x: float
    center_y: float


class SizeSprite(Protocol):
    width: float
    height: float


class _SpriteLikeAdapter:
    def __init__(self, sprite: PositionSprite):
        self.target = sprite

    def iter_sprites(self) -> Iterable[PositionSprite]:
        return (self.target,)


# Cache for sprite positions to avoid expensive recalculation every frame
_position_cache: dict[int, tuple[float, float]] = {}
_cached_action_count = 0
_cached_action_ids: set[int] = set()
_cached_targets: dict[int, object] = {}  # target_id -> target object
_cached_action_targets: dict[int, int] = {}  # action_id -> target_id


def _collect_sprite_positions() -> dict[int, tuple[float, float]]:
    """Attempt to collect sprite positions from active actions.

    Uses caching to avoid expensive iteration when action set hasn't changed.
    """
    global _position_cache, _cached_action_count, _cached_action_ids, _cached_targets, _cached_action_targets

    current_actions = list(Action._active_actions)  # type: ignore[attr-defined]
    current_count = len(current_actions)
    current_ids = {id(action) for action in current_actions}
    current_action_targets, current_targets = _collect_current_targets(current_actions)

    # If action set hasn't changed, use cached targets and update positions.
    if (
        current_count == _cached_action_count
        and current_ids == _cached_action_ids
        and current_action_targets == _cached_action_targets
    ):
        positions = _collect_positions_from_targets(_cached_targets)
        _position_cache = positions
        return positions

    # Slow path: rebuild cache from scratch.
    positions = _collect_positions_from_targets(current_targets)
    _cached_targets = dict(current_targets)
    _position_cache = positions
    _cached_action_count = current_count
    _cached_action_ids = current_ids
    _cached_action_targets = current_action_targets
    return positions


def _collect_sprite_sizes_and_ids() -> tuple[dict[int, tuple[float, float]], dict[int, list[int]]]:
    """Collect sprite sizes and sprite IDs that belong to each target.

    Returns:
        Tuple of (sprite_sizes, sprite_ids_in_target)
        - sprite_sizes: Dict mapping sprite ID to (width, height)
        - sprite_ids_in_target: Dict mapping target ID to list of sprite IDs it contains
    """
    sprite_sizes: dict[int, tuple[float, float]] = {}
    sprite_ids_in_target: dict[int, list[int]] = {}

    # Use cached targets from position collection
    for target_id, target in _cached_targets.items():
        adapter = _try_adapt_target(target)
        if adapter is None:
            continue

        sprite_ids = _collect_sizes_for_adapter(adapter, sprite_sizes)
        if sprite_ids:
            sprite_ids_in_target[target_id] = sprite_ids

    return sprite_sizes, sprite_ids_in_target


def _collect_target_names_from_view() -> dict[int, str]:
    """Attempt to collect target names from the current game view.

    Inspects the current view's attributes to find SpriteLists and Sprites,
    mapping their IDs to their attribute names (e.g., "self.enemy_list").
    Also inspects active actions to map their targets.
    """
    import arcade  # Import at function level to avoid circular imports

    names: dict[int, str] = {}
    membership_names: dict[int, str] = {}

    try:
        window = arcade.get_window()
    except RuntimeError:
        return names

    view = window.current_view
    if view is not None:
        names, membership_names = _collect_view_names(view)
        names.update(membership_names)

    for action in list(Action._active_actions):  # type: ignore[attr-defined]
        target = action.target
        if target is None:
            continue
        target_id = id(target)
        if target_id in names:
            continue
        if target_id in membership_names:
            names[target_id] = membership_names[target_id]

    return names


def _collect_current_targets(
    actions: Iterable[Action],
) -> tuple[dict[int, int], dict[int, object]]:
    current_action_targets: dict[int, int] = {}
    current_targets: dict[int, object] = {}
    for action in actions:
        target = _get_action_target(action)
        if target is None:
            continue
        adapter = _try_adapt_target(target)
        if adapter is None:
            continue
        target_id = id(target)
        current_action_targets[id(action)] = target_id
        current_targets[target_id] = adapter.target
    return current_action_targets, current_targets


def _collect_positions_from_targets(targets: dict[int, object]) -> dict[int, tuple[float, float]]:
    positions: dict[int, tuple[float, float]] = {}
    for target_id, target in targets.items():
        adapter = _try_adapt_target(target)
        if adapter is None:
            continue
        positions.update(_collect_positions_for_adapter(target_id, adapter))
    return positions


def _collect_positions_for_adapter(target_id: int, adapter: TargetAdapter) -> dict[int, tuple[float, float]]:
    positions: dict[int, tuple[float, float]] = {}
    total_x = 0.0
    total_y = 0.0
    count = 0
    for sprite in adapter.iter_sprites():
        position = _maybe_sprite_position(sprite)
        if position is None:
            continue
        sprite_id = id(sprite)
        positions[sprite_id] = position
        total_x += position[0]
        total_y += position[1]
        count += 1
    if count:
        positions[target_id] = (total_x / count, total_y / count)
    return positions


def _collect_sizes_for_adapter(adapter: TargetAdapter, sprite_sizes: dict[int, tuple[float, float]]) -> list[int]:
    sprite_ids: list[int] = []
    for sprite in adapter.iter_sprites():
        size = _maybe_sprite_size(sprite)
        if size is None:
            continue
        sprite_id = id(sprite)
        sprite_sizes[sprite_id] = size
        if sprite_id != id(adapter.target):
            sprite_ids.append(sprite_id)
    return sprite_ids


def _collect_view_names(view: object) -> tuple[dict[int, str], dict[int, str]]:
    names: dict[int, str] = {}
    membership_names: dict[int, str] = {}
    for attr_name, attr_value in _iter_view_attributes(view):
        adapter = _try_adapt_target(attr_value)
        if adapter is None:
            continue
        target_id = id(adapter.target)
        names[target_id] = f"self.{attr_name}"
        for sprite in adapter.iter_sprites():
            if _maybe_sprite_position(sprite) is None:
                continue
            sprite_id = id(sprite)
            if sprite_id == target_id:
                continue
            hex_id = hex(sprite_id)[-4:]
            membership_names[sprite_id] = f"Sprite#{hex_id} in self.{attr_name}"
    return names, membership_names


def _iter_view_attributes(view: object) -> Iterable[tuple[str, object]]:
    try:
        items = vars(view).items()
    except TypeError:
        return ()
    return ((name, value) for name, value in items if not name.startswith("_"))


def _try_adapt_target(target: object) -> TargetAdapter | None:
    try:
        return adapt_target(target)
    except TypeError:
        if _maybe_sprite_position(target) is not None:
            return _SpriteLikeAdapter(target)  # type: ignore[arg-type]
        return None


def _get_action_target(action: Action) -> object | None:
    try:
        return action.target
    except AttributeError:
        return None


def _maybe_sprite_position(sprite: object) -> tuple[float, float] | None:
    try:
        position_sprite: PositionSprite = sprite  # type: ignore[assignment]
        return (position_sprite.center_x, position_sprite.center_y)
    except AttributeError:
        return None


def _maybe_sprite_size(sprite: object) -> tuple[float, float] | None:
    try:
        size_sprite: SizeSprite = sprite  # type: ignore[assignment]
        return (size_sprite.width, size_sprite.height)
    except AttributeError:
        return None
