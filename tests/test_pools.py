"""Additional SpritePool coverage tests.

Covers error branches, counters, and property accessors to improve
coverage for actions/pools.py.
"""

import arcade
import pytest


def _make_sprite():
    return arcade.Sprite(":resources:images/items/star.png")


def test_sprite_pool_invalid_max_size():
    from actions.pools import SpritePool

    with pytest.raises(ValueError):
        SpritePool(_make_sprite, max_size=0)


def test_sprite_pool_acquire_invalid_n():
    from actions.pools import SpritePool

    pool = SpritePool(_make_sprite, max_size=5)
    with pytest.raises(ValueError):
        pool.acquire(0)


def test_sprite_pool_counts_properties_update():
    from actions.pools import SpritePool

    pool = SpritePool(_make_sprite, max_size=10)
    assert pool.active_count == 0
    assert pool.inactive_count == 0
    assert pool.total_count == 0

    acquired = pool.acquire(3)
    assert pool.active_count == 3
    assert pool.inactive_count == 0
    assert pool.total_count == 3

    pool.release(acquired[:2])
    assert pool.active_count == 1
    assert pool.inactive_count == 2
    assert pool.total_count == 3

    pool.release(acquired[2:])
    assert pool.active_count == 0
    assert pool.inactive_count == 3
    assert pool.total_count == 3


def test_assign_handles_active_and_new_sprites_and_enforces_max():
    from actions.pools import SpritePool

    pool = SpritePool(_make_sprite, max_size=4)

    # Acquire 2 (become active)
    acquired = pool.acquire(2)
    assert pool.active_count == 2

    # Create 2 external sprites and 1 extra to exceed max
    external = [arcade.Sprite(":resources:images/items/coinGold.png") for _ in range(3)]

    # Assigning all 3 would exceed max (2 active + 0 inactive + 3 new = 5)
    with pytest.raises(ValueError):
        pool.assign(external)

    # Assign only 2 external - should succeed
    pool.assign(external[:2])
    assert pool.active_count == 2  # Still active until released
    assert pool.inactive_count == 2

    # Now assign one of the active ones (should move to inactive)
    pool.assign([acquired[0]])
    assert pool.active_count == 1
    assert pool.inactive_count == 3
    assert pool.total_count == 4
