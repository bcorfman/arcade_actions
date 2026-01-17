"""Runtime helpers for tagging sprites with a stable position id.

Use as a decorator on factory functions, or call `tag_sprite(sprite, id)` at
runtime to associate a stable identifier for code↔visual mapping.
"""

from __future__ import annotations

from typing import Dict, List


# Runtime registry mapping position_id -> list of sprites
_REGISTRY: Dict[str, List[object]] = {}
_SPRITE_TO_POSITION_ID: Dict[int, str] = {}


def tag_sprite(sprite: object, position_id: str) -> None:
    """Attach a stable position id to a sprite instance and register it.

    Args:
        sprite: sprite-like object (any object) to tag
        position_id: stable identifier used in code and visualizer to map
    """
    setattr(sprite, "_position_id", position_id)
    _REGISTRY.setdefault(position_id, []).append(sprite)
    _SPRITE_TO_POSITION_ID[id(sprite)] = position_id


def remove_sprite_from_registry(sprite: object) -> None:
    pid = _SPRITE_TO_POSITION_ID.pop(id(sprite), None)
    if not pid:
        return
    lst = _REGISTRY.get(pid)
    if not lst:
        return
    try:
        lst.remove(sprite)
    except ValueError:
        pass
    if not lst:
        _REGISTRY.pop(pid, None)


def get_sprites_for(position_id: str) -> List[object]:
    return list(_REGISTRY.get(position_id, []))


def positioned(position_id: str):
    """Decorator for factory functions that tags created sprites with `position_id`.

    Example:
        @positioned("forcefield")
        def make_forcefield(...):
            s = Sprite(...)
            return s

    The returned sprite will have attribute `_position_id == "forcefield"` and
    will be added to the runtime registry.
    """

    def decorator(factory):
        def wrapper(*args, **kwargs):
            sprite = factory(*args, **kwargs)
            tag_sprite(sprite, position_id)
            return sprite

        # Preserve introspection-friendly attributes
        wrapper.__name__ = getattr(factory, "__name__", "wrapper")
        wrapper.__doc__ = getattr(factory, "__doc__", None)
        wrapper.__wrapped__ = factory
        wrapper._positioned_id = position_id
        return wrapper

    return decorator


__all__ = ["tag_sprite", "remove_sprite_from_registry", "get_sprites_for", "positioned"]
