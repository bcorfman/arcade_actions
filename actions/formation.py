"""
Sprite formation and arrangement functions.

This module provides functions for arranging sprites in various geometric patterns
like lines, grids, circles, V-formations, and diamonds. These functions can either
arrange existing sprites or create new ones using a sprite factory.
"""

import math
from collections.abc import Callable

import arcade


def _default_factory(texture: str = ":resources:images/items/star.png", scale: float = 1.0):
    """Return a lambda that creates a sprite with the given texture and scale."""
    return lambda: arcade.Sprite(texture, scale=scale)


def arrange_line(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    start_x: float = 0,
    start_y: float = 0,
    spacing: float = 50.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
) -> arcade.SpriteList:
    """Create or arrange sprites in a horizontal line.

    If *sprites* is given, it is arranged in-place. If *sprites* is **None**, a new
    :class:`arcade.SpriteList` is created with ``count`` sprites produced by
    *sprite_factory* (defaults to a simple star sprite).

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        start_x: X coordinate of the first sprite
        start_y: Y coordinate for all sprites in the line
        spacing: Distance between adjacent sprites
        sprite_factory: Function to create new sprites (if sprites is None)

    Returns:
        The arranged sprite list

    Example:
        # Arrange existing sprites
        enemies = arcade.SpriteList()
        # ... add sprites to enemies ...
        arrange_line(enemies, start_x=100, start_y=200, spacing=60)

        # Create new sprites in a line
        line = arrange_line(count=5, start_x=0, start_y=300, spacing=50)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")

        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprites.append(sprite_factory())

    # Arrange positions
    for i, sprite in enumerate(sprites):
        sprite.center_x = start_x + i * spacing
        sprite.center_y = start_y

    return sprites


def arrange_grid(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    rows: int = 5,
    cols: int = 10,
    start_x: float = 100,
    start_y: float = 500,
    spacing_x: float = 60.0,
    spacing_y: float = 50.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
) -> arcade.SpriteList:
    """Create or arrange sprites in a rectangular grid formation.

    If *sprites* is **None**, a new :class:`arcade.SpriteList` with ``rows × cols``
    sprites is created using *sprite_factory* (defaults to a star sprite). The
    function always returns the arranged sprite list.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        start_x: X coordinate of the top-left sprite
        start_y: Y coordinate of the top-left sprite
        spacing_x: Horizontal distance between adjacent sprites
        spacing_y: Vertical distance between adjacent rows
        sprite_factory: Function to create new sprites (if sprites is None)

    Returns:
        The arranged sprite list

    Example:
        # Create a 3x5 grid of enemy sprites
        enemies = arrange_grid(rows=3, cols=5, start_x=200, start_y=400)

        # Arrange existing sprites in a grid
        arrange_grid(existing_sprites, rows=2, cols=4, spacing_x=80, spacing_y=60)
    """
    if sprites is None:
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(rows * cols):
            sprites.append(sprite_factory())

    for i, sprite in enumerate(sprites):
        row = i // cols
        col = i % cols
        sprite.center_x = start_x + col * spacing_x
        sprite.center_y = start_y + row * spacing_y

    return sprites


def arrange_circle(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    center_x: float = 400,
    center_y: float = 300,
    radius: float = 100.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
) -> arcade.SpriteList:
    """Create or arrange sprites in a circular formation.

    Sprites are arranged starting from the top (π/2) and moving clockwise.
    This ensures that increasing Y values move sprites upward, consistent
    with the coordinate system used in other arrangement functions.

    With 4 sprites, they will be placed at:
    - First sprite: top (π/2)
    - Second sprite: right (0)
    - Third sprite: bottom (-π/2)
    - Fourth sprite: left (π)

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        center_x: X coordinate of the circle center
        center_y: Y coordinate of the circle center
        radius: Radius of the circle
        sprite_factory: Function to create new sprites (if sprites is None)

    Returns:
        The arranged sprite list

    Example:
        # Create sprites in a circle
        circle_formation = arrange_circle(count=8, center_x=400, center_y=300, radius=120)

        # Arrange existing sprites in a circle
        arrange_circle(existing_sprites, center_x=200, center_y=200, radius=80)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprites.append(sprite_factory())

    count = len(sprites)
    if count == 0:
        return sprites

    angle_step = 2 * math.pi / count
    for i, sprite in enumerate(sprites):
        # Start at π/2 (top) and go clockwise (negative angle)
        # Subtract π/2 to start at the top instead of the right
        angle = math.pi / 2 - i * angle_step
        sprite.center_x = center_x + math.cos(angle) * radius
        sprite.center_y = center_y + math.sin(angle) * radius

    return sprites


def arrange_v_formation(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    apex_x: float = 400,
    apex_y: float = 500,
    angle: float = 45.0,
    spacing: float = 50.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
) -> arcade.SpriteList:
    """Create or arrange sprites in a V or wedge formation.

    The formation grows upward from the apex, with sprites placed in alternating
    left-right pattern at the specified angle.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        apex_x: X coordinate of the V formation apex (tip)
        apex_y: Y coordinate of the V formation apex (tip)
        angle: Angle of the V formation in degrees (0-90)
        spacing: Distance between adjacent sprites along the V arms
        sprite_factory: Function to create new sprites (if sprites is None)

    Returns:
        The arranged sprite list

    Example:
        # Create a V formation with 7 sprites
        v_formation = arrange_v_formation(count=7, apex_x=400, apex_y=100, angle=60)

        # Arrange existing sprites in V formation
        arrange_v_formation(flying_birds, angle=30, spacing=40)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprites.append(sprite_factory())

    count = len(sprites)
    if count == 0:
        return sprites

    angle_rad = math.radians(angle)

    # Place the first sprite at the apex
    sprites[0].center_x = apex_x
    sprites[0].center_y = apex_y

    for i in range(1, count):
        side = 1 if i % 2 == 1 else -1
        distance = (i + 1) // 2 * spacing

        offset_x = side * math.cos(angle_rad) * distance
        offset_y = math.sin(angle_rad) * distance

        sprites[i].center_x = apex_x + offset_x
        sprites[i].center_y = apex_y + offset_y

    return sprites


def arrange_diamond(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    center_x: float = 400,
    center_y: float = 300,
    spacing: float = 50.0,
    include_center: bool = True,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
) -> arcade.SpriteList:
    """Create or arrange sprites in a diamond formation.

    Sprites are arranged in concentric diamond-shaped layers around a center point.
    The formation can optionally include a center sprite, then places sprites in
    diamond-shaped rings at increasing distances. Each layer forms a diamond pattern
    with sprites positioned using Manhattan distance.

    The diamond formation grows outward in layers:
    - Layer 0: 1 sprite at center (if include_center=True)
    - Layer 1: 4 sprites forming a small diamond
    - Layer 2: 8 sprites forming a larger diamond
    - Layer 3: 12 sprites, etc.

    Total sprites for n layers:
    - With center: 1 + 4 + 8 + 12 + ... = 1 + 2*n*(n+1) for n ≥ 1
    - Without center: 4 + 8 + 12 + ... = 2*n*(n+1) for n ≥ 1

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        center_x: X coordinate of the diamond center
        center_y: Y coordinate of the diamond center
        spacing: Distance between adjacent layer rings
        include_center: Whether to place a sprite at the center (default: True)
        sprite_factory: Function to create new sprites (if sprites is None)

    Returns:
        The arranged sprite list

    Example:
        # Create a solid diamond formation with 13 sprites (1 + 4 + 8)
        diamond = arrange_diamond(count=13, center_x=400, center_y=300, spacing=60)

        # Create a hollow diamond formation with 12 sprites (4 + 8)
        hollow_diamond = arrange_diamond(
            count=12, center_x=400, center_y=300, spacing=60, include_center=False
        )

        # Arrange existing sprites in diamond formation
        arrange_diamond(existing_sprites, center_x=200, center_y=200, spacing=40)

        # Diamond formations work well for:
        # - Enemy attack patterns (solid for boss, hollow for minions)
        # - Defensive formations (hollow allows protected units inside)
        # - Crystal/gem displays (hollow showcases central item)
        # - Special effect arrangements (hollow creates visual focus)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprites.append(sprite_factory())

    count = len(sprites)
    if count == 0:
        return sprites

    # Place sprites starting from center (if included) and working outward in diamond layers
    sprite_index = 0
    layer = 0 if include_center else 1

    while sprite_index < count:
        if layer == 0 and include_center:
            # Center sprite
            if sprite_index < count:
                sprites[sprite_index].center_x = center_x
                sprites[sprite_index].center_y = center_y
                sprite_index += 1
        else:
            # Diamond layer at distance layer * spacing from center
            # Each layer has 4 * layer sprites positioned around the diamond perimeter
            layer_distance = layer * spacing
            sprites_in_layer = min(4 * layer, count - sprite_index)

            # Place sprites evenly around the diamond perimeter
            # Diamond has 4 cardinal directions, with sprites between them
            for i in range(sprites_in_layer):
                if sprite_index >= count:
                    break

                # Calculate the angle for this sprite position
                # Distribute sprites evenly around the full perimeter
                angle = i * 2 * math.pi / (4 * layer)

                # Convert angle to diamond coordinates
                # Use the "taxicab" or "Manhattan" distance approach for diamond shape
                # The diamond has vertices at (±d, 0) and (0, ±d) where d = layer_distance

                # Convert polar coordinates to diamond coordinates
                # For a diamond, we want |x| + |y| = layer_distance (Manhattan distance)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)

                # Normalize to diamond shape by scaling to Manhattan distance
                # The diamond boundary satisfies |x| + |y| = r
                # Given direction (cos_a, sin_a), find the point on diamond boundary
                if abs(cos_a) + abs(sin_a) > 0:  # Avoid division by zero
                    scale = layer_distance / (abs(cos_a) + abs(sin_a))
                    offset_x = cos_a * scale
                    offset_y = sin_a * scale
                else:
                    offset_x = layer_distance
                    offset_y = 0

                sprites[sprite_index].center_x = center_x + offset_x
                sprites[sprite_index].center_y = center_y + offset_y
                sprite_index += 1

        layer += 1

    return sprites
