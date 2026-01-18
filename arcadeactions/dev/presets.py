"""Preset action library for DevVisualizer.

Provides decorator-based registration of composable Action presets with
parameter editing support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from arcadeactions.base import Action


class ActionPresetRegistry:
    """
    Registry of action preset factories.

    Presets are registered via decorator and can be instantiated with
    customizable parameters for bulk application to sprites.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._presets: dict[str, dict[str, Any]] = {}  # id -> {factory, category, default_params}

    def register(
        self,
        preset_id: str,
        category: str = "General",
        params: dict[str, Any] | None = None,
    ) -> Callable[[Callable], Callable]:
        """
        Decorator to register an action preset factory.

        Args:
            preset_id: Unique identifier for this preset
            category: Category name for organization (e.g., "Movement", "Effects")
            params: Default parameter values

        Returns:
            Decorator function

        Example:
            @registry.register("scroll_left_cleanup", category="Movement", params={"speed": 4})
            def preset_scroll_left_cleanup(ctx, speed):
                return move_until(
                    None,
                    velocity=(-speed, 0),
                    condition=infinite,
                    bounds=(OFFSCREEN_LEFT, 0, SCREEN_RIGHT, SCREEN_HEIGHT),
                    boundary_behavior="limit",
                )
        """

        def decorator(factory: Callable[..., Action]) -> Callable:
            if preset_id in self._presets:
                # Overwrite existing preset registration to support tests and reloads
                # Later registrations intentionally replace earlier ones.
                pass
            self._presets[preset_id] = {
                "factory": factory,
                "category": category,
                "default_params": params or {},
            }
            return factory

        return decorator

    def create(self, preset_id: str, ctx: Any, **params) -> Action:
        """
        Create an action instance from a registered preset.

        Args:
            preset_id: ID of preset to instantiate
            ctx: DevContext or similar context object
            **params: Parameter overrides (merged with defaults)

        Returns:
            New action instance (unbound, not applied to target)

        Raises:
            KeyError: If preset_id is not registered
        """
        if preset_id not in self._presets:
            raise KeyError(f"Preset '{preset_id}' not found")

        preset_info = self._presets[preset_id]
        factory = preset_info["factory"]
        default_params = preset_info["default_params"].copy()

        # Merge provided params with defaults
        merged_params = {**default_params, **params}

        # Call factory with context and merged params
        return factory(ctx, **merged_params)

    def all(self) -> dict[str, dict[str, Any]]:
        """
        Get all registered presets.

        Returns:
            Dictionary mapping preset_id -> preset info (factory, category, default_params)
        """
        return {
            preset_id: {
                "category": info["category"],
                "default_params": info["default_params"].copy(),
            }
            for preset_id, info in self._presets.items()
        }

    def has(self, preset_id: str) -> bool:
        """
        Check if a preset is registered.

        Args:
            preset_id: ID to check

        Returns:
            True if registered, False otherwise
        """
        return preset_id in self._presets

    def get_categories(self) -> list[str]:
        """
        Get list of all preset categories.

        Returns:
            List of unique category names
        """
        categories = set()
        for info in self._presets.values():
            categories.add(info["category"])
        return sorted(list(categories))


# Global registry instance
_global_preset_registry = ActionPresetRegistry()


def register_preset(
    preset_id: str,
    category: str = "General",
    params: dict[str, Any] | None = None,
):
    """
    Decorator to register an action preset with the global registry.

    Args:
        preset_id: Unique identifier for this preset
        category: Category name for organization
        params: Default parameter values

    Example:
        @register_preset("scroll_left", category="Movement", params={"speed": 4})
        def preset_scroll_left(ctx, speed):
            from arcadeactions.helpers import move_until
            from arcadeactions.conditional import infinite
            return move_until(None, velocity=(-speed, 0), condition=infinite)
    """
    return _global_preset_registry.register(preset_id, category, params)


def get_preset_registry() -> ActionPresetRegistry:
    """
    Get the global preset registry.

    Returns:
        Global ActionPresetRegistry instance
    """
    return _global_preset_registry
