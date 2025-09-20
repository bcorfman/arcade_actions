"""
Experimental sprite pooling for zero-allocation gameplay.

This module provides SpritePool for managing sprite lifecycle without
allocating new sprites during gameplay, supporting patterns like:

    # Boot-time setup
    pool = SpritePool(make_block, max_size=300)
    blocks = pool.acquire(150)
    arrange_grid(rows=30, cols=5, sprites=blocks, start_x=0, start_y=0)
    pool.assign(blocks)  # Return to pool invisible & neutral

    # In-wave usage
    shield = pool.acquire(width*30)
    arrange_grid(rows=30, cols=width, sprites=shield, start_x=WINDOW+..., start_y=TUNNEL_H)
    # ... gameplay ...
    pool.release(shield)  # Return for next wave
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import arcade


class SpritePool:
    """Experimental sprite pool for zero-allocation gameplay.

    Pre-allocates sprites via a factory callable and provides acquire/release
    semantics to avoid sprite allocation during gameplay. Sprites are always
    hidden and detached when in the pool.

    Args:
        sprite_factory: Callable that creates new sprites when needed
        max_size: Maximum number of sprites the pool can manage

    Example:
        def make_enemy():
            return arcade.Sprite(":resources:images/enemies/bee.png", scale=0.5)

        pool = SpritePool(make_enemy, max_size=100)

        # Acquire sprites for a wave
        enemies = pool.acquire(20)
        arrange_grid(sprites=enemies, rows=4, cols=5, start_x=100, start_y=400)

        # Return sprites when wave ends
        pool.release(enemies)
    """

    def __init__(self, sprite_factory: Callable[[], arcade.Sprite], *, max_size: int = 100):
        """Initialize the sprite pool.

        Args:
            sprite_factory: Function that creates new sprites
            max_size: Maximum sprites the pool can manage (prevents runaway growth)
        """
        if max_size <= 0:
            raise ValueError("max_size must be positive")

        self._sprite_factory = sprite_factory
        self.max_size = max_size
        self._inactive_sprites: list[arcade.Sprite] = []
        self._active_sprites: set[arcade.Sprite] = set()

    def acquire(self, n: int) -> list[arcade.Sprite]:
        """Acquire n sprites from the pool.

        Returns invisible, un-positioned sprites ready for arrangement.
        Creates new sprites via the factory if needed.

        Args:
            n: Number of sprites to acquire

        Returns:
            List of available sprites

        Raises:
            ValueError: If acquiring would exceed max_size
        """
        if n <= 0:
            raise ValueError("Cannot acquire non-positive number of sprites")

        if len(self._active_sprites) + n > self.max_size:
            raise ValueError(
                f"Cannot acquire {n} sprites: would exceed max_size {self.max_size} "
                f"({len(self._active_sprites)} already active)"
            )

        sprites = []

        # First, reuse inactive sprites
        while len(sprites) < n and self._inactive_sprites:
            sprite = self._inactive_sprites.pop()
            self._prepare_sprite_for_use(sprite)
            sprites.append(sprite)

        # Create new sprites if needed
        while len(sprites) < n:
            sprite = self._sprite_factory()
            self._prepare_sprite_for_use(sprite)
            sprites.append(sprite)

        # Track as active
        for sprite in sprites:
            self._active_sprites.add(sprite)

        return sprites

    def release(self, sprites: Iterable[arcade.Sprite]) -> None:
        """Return sprites to the inactive pool.

        Sprites are made invisible, detached from sprite lists, and reset
        to neutral positions.

        Args:
            sprites: Sprites to return to the pool
        """
        sprites_list = list(sprites)  # Convert to list for multiple iteration

        for sprite in sprites_list:
            if sprite in self._active_sprites:
                self._prepare_sprite_for_storage(sprite)
                self._active_sprites.remove(sprite)
                self._inactive_sprites.append(sprite)

    def assign(self, sprites: Iterable[arcade.Sprite]) -> None:
        """Load externally-created sprites into the pool.

        This is a one-off operation to load sprites created outside the pool.
        Sprites are made invisible and stored as inactive. If any sprites are
        currently active in the pool, they are moved to inactive status.

        Args:
            sprites: External sprites to add to the pool

        Raises:
            ValueError: If assigning would exceed max_size
        """
        sprites_list = list(sprites)

        # Count how many new sprites we would need to add
        new_sprites_count = 0
        for sprite in sprites_list:
            if sprite not in self._active_sprites and sprite not in self._inactive_sprites:
                new_sprites_count += 1

        if len(self._inactive_sprites) + len(self._active_sprites) + new_sprites_count > self.max_size:
            raise ValueError(
                f"Cannot assign {len(sprites_list)} sprites: would exceed max_size {self.max_size} "
                f"(currently have {len(self._inactive_sprites)} inactive + {len(self._active_sprites)} active)"
            )

        for sprite in sprites_list:
            if sprite in self._active_sprites:
                # Move from active to inactive
                self._active_sprites.remove(sprite)
                self._prepare_sprite_for_storage(sprite)
                self._inactive_sprites.append(sprite)
            elif sprite not in self._inactive_sprites:
                # Add new sprite to inactive
                self._prepare_sprite_for_storage(sprite)
                self._inactive_sprites.append(sprite)

    def _prepare_sprite_for_use(self, sprite: arcade.Sprite) -> None:
        """Prepare a sprite for use (acquired from pool).

        Makes sprite invisible and unpositioned, ready for arrangement.
        """
        sprite.visible = False
        sprite.center_x = 0
        sprite.center_y = 0
        sprite.alpha = 255  # Full alpha

        # Remove from any existing sprite lists
        sprite.remove_from_sprite_lists()

    def _prepare_sprite_for_storage(self, sprite: arcade.Sprite) -> None:
        """Prepare a sprite for storage in the pool.

        Makes sprite invisible, detached, and positioned at origin.
        """
        sprite.visible = False
        sprite.center_x = 0
        sprite.center_y = 0
        sprite.alpha = 255  # Reset alpha

        # Remove from all sprite lists
        sprite.remove_from_sprite_lists()

    @property
    def active_count(self) -> int:
        """Number of sprites currently acquired from the pool."""
        return len(self._active_sprites)

    @property
    def inactive_count(self) -> int:
        """Number of sprites available in the pool."""
        return len(self._inactive_sprites)

    @property
    def total_count(self) -> int:
        """Total number of sprites managed by the pool."""
        return len(self._active_sprites) + len(self._inactive_sprites)
