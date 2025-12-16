"""YAML template export/import for DevVisualizer.

Provides functions to export sprite scenes to YAML and import them back,
with support for symbolic bound expressions.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade
    from actions.dev.prototype_registry import DevContext


# Symbolic token mappings for bounds
# These can be replaced during load/export for readability
SYMBOLIC = {
    "OFFSCREEN_LEFT": -100,  # Default - should be configurable
    "OFFSCREEN_RIGHT": 900,  # Default - should be configurable
    "SCREEN_LEFT": 0,
    "SCREEN_RIGHT": 800,  # Default - should be configurable
    "SCREEN_BOTTOM": 0,
    "SCREEN_TOP": 600,  # Default - should be configurable
    "SCREEN_HEIGHT": 600,  # Default - should be configurable
    "SCREEN_WIDTH": 800,  # Default - should be configurable
    "WALL_WIDTH": 50,  # Default - should be configurable
}

# Preferred tokens for ambiguous values, grouped by context
# Used when multiple tokens map to the same value
_SYMBOLIC_PREFERENCES = {
    # X-axis tokens (left/right bounds)
    "x": {
        0: "SCREEN_LEFT",
        800: "SCREEN_RIGHT",
    },
    # Y-axis tokens (bottom/top bounds)
    "y": {
        0: "SCREEN_BOTTOM",
        600: "SCREEN_TOP",
    },
}

# Reverse mapping for export (value -> token)
# Only used for unambiguous values; ambiguous ones use preferences
_SYMBOLIC_REVERSE: dict[float, str] = {v: k for k, v in SYMBOLIC.items()}


def _resolve_symbolic(value: Any) -> Any:
    """
    Resolve symbolic tokens in YAML values.

    Args:
        value: Value that might be a string token or number

    Returns:
        Resolved numeric value or original value
    """
    if isinstance(value, str) and value in SYMBOLIC:
        return SYMBOLIC[value]
    return value


def _symbolize_value(value: float, axis: str | None = None) -> str | float:
    """
    Convert numeric value to symbolic token if it matches a known constant.

    Args:
        value: Numeric value to check
        axis: Optional axis context ("x" or "y") for ambiguous values.
              Used for bounds: x-axis for left/right, y-axis for bottom/top.

    Returns:
        Symbolic token string if match found, original value otherwise
    """
    # If axis context is provided and value has a preference, use it
    if axis is not None and axis in _SYMBOLIC_PREFERENCES:
        preferences = _SYMBOLIC_PREFERENCES[axis]
        if value in preferences:
            return preferences[value]

    # Otherwise, use reverse mapping (may be ambiguous but still valid)
    if value in _SYMBOLIC_REVERSE:
        return _SYMBOLIC_REVERSE[value]
    return value


def _resolve_bounds(bounds: Any) -> tuple[float, float, float, float] | None:
    """
    Resolve bounds tuple, replacing symbolic tokens.

    Args:
        bounds: Bounds value (tuple, list, or dict)

    Returns:
        Resolved bounds tuple or None
    """
    if bounds is None:
        return None

    if isinstance(bounds, (tuple, list)) and len(bounds) == 4:
        return tuple(_resolve_symbolic(v) for v in bounds)

    if isinstance(bounds, dict):
        # Handle dict format if needed
        return None

    return None


def export_template(
    sprites: arcade.SpriteList,
    path: str | Path,
    prompt_user: bool = True,
) -> None:
    """
    Export sprite scene to YAML template.

    Args:
        sprites: SpriteList containing sprites to export
        path: File path to write YAML to
        prompt_user: If True, prompt before overwriting (not implemented in MVP)
    """
    path = Path(path)

    scene_data = []

    for sprite in sprites:
        sprite_def: dict[str, Any] = {
            "prototype": getattr(sprite, "_prototype_id", "unknown"),
            "x": sprite.center_x,
            "y": sprite.center_y,
            "group": getattr(sprite, "_group", ""),
            "actions": [],
        }

        # Export action configs (metadata, not running actions)
        if hasattr(sprite, "_action_configs"):
            for action_config in sprite._action_configs:
                action_def: dict[str, Any] = {
                    "preset": action_config.get("preset", "unknown"),
                    "params": {},
                }

                # Export params, converting bounds to symbolic if possible
                params = action_config.get("params", {})
                for key, value in params.items():
                    if key == "bounds" and isinstance(value, (tuple, list)) and len(value) == 4:
                        # Try to symbolize bounds tuple (left, bottom, right, top)
                        # Use axis context to choose correct tokens for ambiguous values
                        symbolized_bounds = [
                            _symbolize_value(value[0], axis="x"),  # left -> x-axis
                            _symbolize_value(value[1], axis="y"),  # bottom -> y-axis
                            _symbolize_value(value[2], axis="x"),  # right -> x-axis
                            _symbolize_value(value[3], axis="y"),  # top -> y-axis
                        ]
                        action_def["params"]["bounds"] = symbolized_bounds
                    else:
                        action_def["params"][key] = value

                sprite_def["actions"].append(action_def)

        scene_data.append(sprite_def)

    # Write YAML
    with open(path, "w") as f:
        yaml.dump(scene_data, f, default_flow_style=False, sort_keys=False)


def load_scene_template(path: str | Path, ctx: DevContext) -> arcade.SpriteList:
    """
    Load sprite scene from YAML template.

    Clears ctx.scene_sprites and rebuilds from YAML. Actions are stored
    as metadata (_action_configs), not applied (edit mode).

    Args:
        path: File path to read YAML from
        ctx: DevContext with scene_sprites and registry access

    Returns:
        SpriteList with loaded sprites
    """
    from actions.dev.prototype_registry import get_registry

    path = Path(path)
    registry = get_registry()

    # Clear existing scene
    if ctx.scene_sprites is not None:
        ctx.scene_sprites.clear()
    else:
        import arcade

        ctx.scene_sprites = arcade.SpriteList()

    # Load YAML
    with open(path, "r") as f:
        scene_data = yaml.safe_load(f)

    if not isinstance(scene_data, list):
        raise ValueError("YAML must contain a list of sprite definitions")

    # Create sprites from definitions
    for sprite_def in scene_data:
        prototype_id = sprite_def.get("prototype")
        if not prototype_id:
            continue

        # Create sprite from prototype
        sprite = registry.create(prototype_id, ctx)

        # Set position
        sprite.center_x = float(sprite_def.get("x", 0))
        sprite.center_y = float(sprite_def.get("y", 0))

        # Set group metadata
        sprite._group = sprite_def.get("group", "")

        # Store action configs (not applying - edit mode)
        sprite._action_configs = []
        for action_def in sprite_def.get("actions", []):
            preset_id = action_def.get("preset")
            if not preset_id:
                continue

            params = action_def.get("params", {})
            # Resolve symbolic tokens in params
            resolved_params = {}
            for key, value in params.items():
                if key == "bounds":
                    resolved_params[key] = _resolve_bounds(value)
                else:
                    resolved_params[key] = _resolve_symbolic(value)

            sprite._action_configs.append({"preset": preset_id, "params": resolved_params})

        ctx.scene_sprites.append(sprite)

    return ctx.scene_sprites


