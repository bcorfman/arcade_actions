"""
Sprite prototype registry for DevVisualizer.

Provides decorator-based registration of sprite "prefabs" that can be
dragged from the palette into the scene.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade


class DevContext:
    """Context object passed to prototype factories with scene references."""

    def __init__(
        self,
        scene_sprites: arcade.SpriteList | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize dev context.

        Args:
            scene_sprites: SpriteList where spawned sprites are added
            config: Optional configuration dictionary
        """
        self.scene_sprites = scene_sprites
        self.config = config or {}


class SpritePrototypeRegistry:
    """
    Registry of sprite prototype factories.

    Prototypes are registered via decorator and can be instantiated
    by the DevVisualizer for drag-and-drop spawning.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._prototypes: dict[str, Callable[[DevContext], arcade.Sprite]] = {}

    def register(self, prototype_id: str) -> Callable[[Callable], Callable]:
        """
        Decorator to register a sprite prototype factory.

        Args:
            prototype_id: Unique identifier for this prototype

        Returns:
            Decorator function

        Example:
            @registry.register("player_ship")
            def make_player_ship(ctx):
                ship = arcade.Sprite("res/ship.png", scale=0.5)
                ship._prototype_id = "player_ship"
                return ship
        """

        def decorator(factory: Callable[[DevContext], arcade.Sprite]) -> Callable:
            if prototype_id in self._prototypes:
                raise ValueError(f"Prototype '{prototype_id}' already registered")
            self._prototypes[prototype_id] = factory
            return factory

        return decorator

    def create(self, prototype_id: str, ctx: DevContext) -> arcade.Sprite:
        """
        Create a sprite instance from a registered prototype.

        Args:
            prototype_id: ID of prototype to instantiate
            ctx: DevContext with scene references

        Returns:
            New sprite instance

        Raises:
            KeyError: If prototype_id is not registered
        """
        if prototype_id not in self._prototypes:
            raise KeyError(f"Prototype '{prototype_id}' not found")
        factory = self._prototypes[prototype_id]
        sprite = factory(ctx)
        # Ensure prototype_id is set for serialization
        sprite._prototype_id = prototype_id
        return sprite

    def all(self) -> dict[str, Callable[[DevContext], arcade.Sprite]]:
        """
        Get all registered prototypes.

        Returns:
            Dictionary mapping prototype_id -> factory function
        """
        return self._prototypes.copy()

    def has(self, prototype_id: str) -> bool:
        """
        Check if a prototype is registered.

        Args:
            prototype_id: ID to check

        Returns:
            True if registered, False otherwise
        """
        return prototype_id in self._prototypes


# Global registry instance
_global_registry = SpritePrototypeRegistry()


def register_prototype(prototype_id: str):
    """
    Decorator to register a sprite prototype with the global registry.

    Args:
        prototype_id: Unique identifier for this prototype

    Example:
        @register_prototype("player_ship")
        def make_player_ship(ctx):
            ship = arcade.Sprite("res/ship.png", scale=0.5)
            ship._prototype_id = "player_ship"
            return ship
    """
    return _global_registry.register(prototype_id)


def get_registry() -> SpritePrototypeRegistry:
    """
    Get the global prototype registry.

    Returns:
        Global SpritePrototypeRegistry instance
    """
    return _global_registry
