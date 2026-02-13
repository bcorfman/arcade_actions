"""Property discovery and typed access for sprite inspection/editing."""

from __future__ import annotations

from collections.abc import Sequence

import arcade


class PropertyDefinition:
    """Describes an editable sprite property."""

    def __init__(self, name: str, category: str, editor_type: str) -> None:
        self.name = name
        self.category = category
        self.editor_type = editor_type


class SpritePropertyRegistry:
    """Registry that exposes built-in and custom editable sprite properties."""

    _BUILTIN: tuple[PropertyDefinition, ...] = (
        PropertyDefinition("left", "Position", "number"),
        PropertyDefinition("right", "Position", "number"),
        PropertyDefinition("center_x", "Position", "number"),
        PropertyDefinition("bottom", "Position", "number"),
        PropertyDefinition("top", "Position", "number"),
        PropertyDefinition("center_y", "Position", "number"),
        PropertyDefinition("position", "Position", "vector2"),
        PropertyDefinition("angle", "Transform", "number"),
        PropertyDefinition("scale", "Transform", "number"),
        PropertyDefinition("width", "Transform", "number"),
        PropertyDefinition("height", "Transform", "number"),
        PropertyDefinition("color", "Appearance", "color"),
        PropertyDefinition("alpha", "Appearance", "number"),
        PropertyDefinition("opacity", "Appearance", "number"),
        PropertyDefinition("collision_radius", "Collision", "number"),
        PropertyDefinition("is_collidable", "Collision", "bool"),
        PropertyDefinition("properties", "Collision", "dict"),
        PropertyDefinition("texture", "Texture", "texture"),
        PropertyDefinition("mirrored_x", "Texture", "bool"),
        PropertyDefinition("mirrored_y", "Texture", "bool"),
    )

    _BUILTIN_BY_NAME = {prop.name: prop for prop in _BUILTIN}

    @staticmethod
    def _custom_property_names(sprite: arcade.Sprite) -> set[str]:
        names: set[str] = set()
        for name in sprite.__dict__:
            if not name.startswith("_"):
                names.add(name)
        return names

    @staticmethod
    def _editor_type_for_value(value: object) -> str:
        value_type = type(value)
        if value_type is bool:
            return "bool"
        if value_type is int or value_type is float:
            return "number"
        if value_type is tuple:
            return "vector2"
        if value_type is dict:
            return "dict"
        return "text"

    def properties_for_selection(self, sprites: Sequence[arcade.Sprite]) -> list[PropertyDefinition]:
        """Return built-ins plus custom props common across all selected sprites."""
        if not sprites:
            return []

        custom_common = self._custom_property_names(sprites[0])
        for sprite in sprites[1:]:
            custom_common &= self._custom_property_names(sprite)

        properties = list(self._BUILTIN)
        for name in sorted(custom_common):
            sample_value = sprites[0].__dict__[name]
            properties.append(PropertyDefinition(name, "Custom", self._editor_type_for_value(sample_value)))

        return properties

    def get_value(self, sprite: arcade.Sprite, property_name: str) -> object:
        """Read a property by name, including custom __dict__ fields."""
        if property_name == "opacity":
            return sprite.alpha
        if property_name == "position":
            return (sprite.center_x, sprite.center_y)
        if property_name in self._BUILTIN_BY_NAME:
            return object.__getattribute__(sprite, property_name)
        if property_name in sprite.__dict__:
            return sprite.__dict__[property_name]
        raise KeyError(property_name)

    def set_value(self, sprite: arcade.Sprite, property_name: str, value: object) -> None:
        """Write a property by name, including custom __dict__ fields."""
        if property_name == "opacity":
            sprite.alpha = int(value)
            return
        if property_name == "position":
            x_value = float(value[0])
            y_value = float(value[1])
            sprite.center_x = x_value
            sprite.center_y = y_value
            return
        if property_name in self._BUILTIN_BY_NAME:
            object.__setattr__(sprite, property_name, value)
            return
        sprite.__dict__[property_name] = value
