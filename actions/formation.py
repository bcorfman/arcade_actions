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
    visible: bool = True,
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
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Arrange existing sprites
        enemies = arcade.SpriteList()
        # ... add sprites to enemies ...
        arrange_line(enemies, start_x=100, start_y=200, spacing=60)

        # Create new sprites in a line
        line = arrange_line(count=5, start_x=0, start_y=300, spacing=50)

        # Create hidden sprites for formation entry
        hidden_line = arrange_line(count=5, start_x=200, start_y=400, visible=False)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")

        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    # Arrange positions
    for i, sprite in enumerate(sprites):
        sprite.center_x = start_x + i * spacing
        sprite.center_y = start_y
        sprite.visible = visible  # Ensure visibility is set

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
    visible: bool = True,
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
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create a 3x5 grid of star sprites
        stars = arrange_grid(rows=3, cols=5, start_x=200, start_y=400)

        # Arrange existing sprites in a grid
        arrange_grid(existing_sprites, rows=2, cols=4, spacing_x=80, spacing_y=60)

        # Create hidden grid for formation entry
        hidden_grid = arrange_grid(rows=4, cols=10, start_x=200, start_y=400, visible=False)
    """
    if sprites is None:
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(rows * cols):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    for i, sprite in enumerate(sprites):
        row = i // cols
        col = i % cols
        sprite.center_x = start_x + col * spacing_x
        sprite.center_y = start_y + row * spacing_y
        sprite.visible = visible  # Ensure visibility is set

    return sprites


def arrange_circle(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    center_x: float = 400,
    center_y: float = 300,
    radius: float = 100.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
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
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create sprites in a circle
        circle_formation = arrange_circle(count=8, center_x=400, center_y=300, radius=120)

        # Arrange existing sprites in a circle
        arrange_circle(existing_sprites, center_x=200, center_y=200, radius=80)

        # Create hidden circle for formation entry
        hidden_circle = arrange_circle(count=8, center_x=400, center_y=300, radius=100, visible=False)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

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
        sprite.visible = visible  # Ensure visibility is set

    return sprites


def arrange_v_formation(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    apex_x: float = 400,
    apex_y: float = 500,
    spacing: float = 50.0,
    direction: str = "up",
    rotate_with_direction: bool = False,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in a V or wedge formation.

    The formation grows from the apex in the specified direction, with sprites placed
    in alternating left-right pattern. The V can point up, down, left, or right.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        apex_x: X coordinate of the V formation apex (tip)
        apex_y: Y coordinate of the V formation apex (tip)
        spacing: Distance between adjacent sprites along the V arms
        direction: Direction the V points ("up", "down", "left", "right")
        rotate_with_direction: Whether to rotate sprites to face the direction (default: False)
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create a V formation pointing up (default)
        v_formation = arrange_v_formation(count=7, apex_x=400, apex_y=100, spacing=60)

        # Create a V formation pointing down
        down_v = arrange_v_formation(count=7, apex_x=400, apex_y=500, spacing=60, direction="down")

        # Create a V formation pointing left with sprite rotation
        left_v = arrange_v_formation(count=7, apex_x=100, apex_y=300, spacing=60, direction="left", rotate_with_direction=True)

        # Arrange existing sprites in V formation pointing right
        arrange_v_formation(flying_birds, direction="right", spacing=40)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    count = len(sprites)
    if count == 0:
        return sprites

    # Validate direction
    valid_directions = ["up", "down", "left", "right"]
    if direction not in valid_directions:
        raise ValueError(f"direction must be one of {valid_directions}, got '{direction}'")

    # Define V angle (45 degrees for a nice V shape)
    v_angle = 45.0
    angle_rad = math.radians(v_angle)

    # Place the first sprite at the apex
    sprites[0].center_x = apex_x
    sprites[0].center_y = apex_y
    sprites[0].visible = visible

    # Set rotation for apex sprite if needed
    if rotate_with_direction:
        rotation_map = {"up": 0, "down": 180, "left": 90, "right": 270}
        sprites[0].angle = rotation_map[direction]

    for i in range(1, count):
        side = 1 if i % 2 == 1 else -1
        distance = (i + 1) // 2 * spacing

        # Calculate base offsets for V shape
        base_offset_x = side * math.cos(angle_rad) * distance
        base_offset_y = math.sin(angle_rad) * distance

        # Apply direction transformation
        if direction == "up":
            offset_x = base_offset_x
            offset_y = base_offset_y
        elif direction == "down":
            offset_x = base_offset_x
            offset_y = -base_offset_y
        elif direction == "left":
            offset_x = -base_offset_y
            offset_y = base_offset_x
        else:  # direction == "right"
            offset_x = base_offset_y
            offset_y = base_offset_x

        sprites[i].center_x = apex_x + offset_x
        sprites[i].center_y = apex_y + offset_y
        sprites[i].visible = visible

        # Set rotation for wing sprites if needed
        if rotate_with_direction:
            if direction == "up":
                sprite_angle = 0
            elif direction == "down":
                sprite_angle = 180
            elif direction == "left":
                sprite_angle = 90
            else:  # direction == "right"
                sprite_angle = 270

            # Add slight angle variation for wing sprites to face outward
            if side == 1:  # Right wing
                sprite_angle += v_angle
            else:  # Left wing
                sprite_angle -= v_angle

            sprites[i].angle = sprite_angle

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
    visible: bool = True,
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
        visible: Whether sprites should be visible (default: True)

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

        # Create hidden diamond for formation entry
        hidden_diamond = arrange_diamond(count=13, center_x=400, center_y=300, spacing=60, visible=False)

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
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

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
                sprites[sprite_index].visible = visible
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
                sprites[sprite_index].visible = visible  # Ensure visibility is set
                sprite_index += 1

        layer += 1

    return sprites


def arrange_triangle(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    apex_x: float = 400,
    apex_y: float = 500,
    row_spacing: float = 50.0,
    lateral_spacing: float = 60.0,
    invert: bool = False,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in a triangular formation.

    Sprites are arranged in successive rows (1, 2, 3, ...) forming a triangle.
    The first sprite is placed at the apex, then subsequent rows spread outward.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        apex_x: X coordinate of the triangle apex (tip)
        apex_y: Y coordinate of the triangle apex (tip)
        row_spacing: Vertical distance between rows
        lateral_spacing: Horizontal distance between sprites in same row
        invert: If True, triangle grows upward; if False, grows downward
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create downward triangle with 6 sprites (1+2+3)
        triangle = arrange_triangle(count=6, apex_x=400, apex_y=500, row_spacing=50)

        # Create upward triangle
        up_triangle = arrange_triangle(count=10, apex_x=300, apex_y=200, invert=True)

        # Arrange existing sprites in triangle
        arrange_triangle(existing_sprites, apex_x=200, apex_y=300, lateral_spacing=40)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    sprite_index = 0
    row = 0
    total_sprites = len(sprites)

    while sprite_index < total_sprites:
        sprites_in_row = row + 1  # Row 0 has 1 sprite, row 1 has 2, etc.
        sprites_to_place = min(sprites_in_row, total_sprites - sprite_index)

        # Calculate Y position for this row
        if invert:
            y_pos = apex_y + row * row_spacing  # Grow upward
        else:
            y_pos = apex_y - row * row_spacing  # Grow downward

        # Calculate starting X position to center the row
        if sprites_to_place == 1:
            start_x = apex_x
        else:
            total_width = (sprites_to_place - 1) * lateral_spacing
            start_x = apex_x - total_width / 2

        # Place sprites in this row
        for i in range(sprites_to_place):
            if sprite_index >= total_sprites:
                break
            sprites[sprite_index].center_x = start_x + i * lateral_spacing
            sprites[sprite_index].center_y = y_pos
            sprites[sprite_index].visible = visible
            sprite_index += 1

        row += 1

    return sprites


def arrange_hexagonal_grid(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    rows: int = 5,
    cols: int = 10,
    start_x: float = 100,
    start_y: float = 500,
    spacing: float = 60.0,
    orientation: str = "pointy",
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in a hexagonal grid formation.

    Creates an offset grid where every other row is shifted to create
    a honeycomb-like hexagonal pattern.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        start_x: X coordinate of the top-left sprite
        start_y: Y coordinate of the top-left sprite
        spacing: Distance between adjacent sprites
        orientation: "pointy" (default) or "flat" for hexagon orientation
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create a 4x6 hexagonal grid
        hex_grid = arrange_hexagonal_grid(rows=4, cols=6, start_x=100, start_y=400)

        # Arrange existing sprites in hexagonal pattern
        arrange_hexagonal_grid(existing_sprites, rows=3, cols=5, spacing=50)
    """
    if sprites is None:
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(rows * cols):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    # Calculate offset and spacing based on orientation
    if orientation == "pointy":
        row_offset_x = spacing / 2
        row_spacing_y = spacing * math.sqrt(3) / 2
    else:  # flat
        row_offset_x = spacing * math.sqrt(3) / 2
        row_spacing_y = spacing / 2

    for i, sprite in enumerate(sprites):
        row = i // cols
        col = i % cols

        # Calculate base position
        x = start_x + col * spacing
        y = start_y + row * row_spacing_y

        # Offset every other row for hexagonal pattern
        if row % 2 == 1:
            x += row_offset_x

        sprite.center_x = x
        sprite.center_y = y
        sprite.visible = visible

    return sprites


def arrange_arc(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    center_x: float = 400,
    center_y: float = 300,
    radius: float = 100.0,
    start_angle: float = 0.0,
    end_angle: float = 180.0,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in an arc formation.

    Sprites are arranged along a circular arc between two angles.
    Angles are in degrees, with 0° pointing right and increasing counterclockwise.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        center_x: X coordinate of the arc center
        center_y: Y coordinate of the arc center
        radius: Radius of the arc
        start_angle: Starting angle in degrees (0° = right)
        end_angle: Ending angle in degrees
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create a semicircle arc
        arc = arrange_arc(count=8, center_x=400, center_y=300, radius=120,
                         start_angle=0, end_angle=180)

        # Create a fan pattern
        fan = arrange_arc(count=5, center_x=200, center_y=200, radius=80,
                         start_angle=45, end_angle=135)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    count = len(sprites)
    if count == 0:
        return sprites

    # Validate angle range
    if start_angle >= end_angle:
        raise ValueError("start_angle must be less than end_angle")

    # Convert angles to radians
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)

    # Calculate angle step
    if count == 1:
        angle_step = 0
        current_angle = (start_rad + end_rad) / 2  # Place single sprite in middle
    else:
        angle_step = (end_rad - start_rad) / (count - 1)
        current_angle = start_rad

    for sprite in sprites:
        sprite.center_x = center_x + math.cos(current_angle) * radius
        sprite.center_y = center_y + math.sin(current_angle) * radius
        sprite.visible = visible
        current_angle += angle_step

    return sprites


def arrange_concentric_rings(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    radii: list[float] | None = None,
    sprites_per_ring: list[int] | None = None,
    center_x: float = 400,
    center_y: float = 300,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in concentric rings formation.

    Creates multiple circular rings at different radii from a center point.
    Each ring can have a different number of sprites.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        radii: List of radii for each ring
        sprites_per_ring: List of sprite counts for each ring
        center_x: X coordinate of the center
        center_y: Y coordinate of the center
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create bull's-eye pattern
        rings = arrange_concentric_rings(
            radii=[50, 100, 150],
            sprites_per_ring=[6, 12, 18],
            center_x=400, center_y=300
        )

        # Arrange existing sprites in rings
        arrange_concentric_rings(
            existing_sprites,
            radii=[40, 80],
            sprites_per_ring=[4, 8],
            center_x=200, center_y=200
        )
    """
    if radii is None:
        radii = [50, 100]
    if sprites_per_ring is None:
        sprites_per_ring = [6, 12]

    # Validate parameters
    if len(radii) != len(sprites_per_ring):
        raise ValueError("radii and sprites_per_ring lists must have the same length")

    total_sprites_needed = sum(sprites_per_ring)

    if sprites is None:
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(total_sprites_needed):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    sprite_index = 0
    for ring_idx, (radius, sprite_count) in enumerate(zip(radii, sprites_per_ring, strict=False)):
        if sprite_index >= len(sprites):
            break

        # Calculate how many sprites to actually place in this ring
        sprites_to_place = min(sprite_count, len(sprites) - sprite_index)

        if sprites_to_place == 0:
            continue

        # Calculate angle step for even distribution
        angle_step = 2 * math.pi / sprites_to_place

        for i in range(sprites_to_place):
            if sprite_index >= len(sprites):
                break

            angle = i * angle_step
            sprite = sprites[sprite_index]
            sprite.center_x = center_x + math.cos(angle) * radius
            sprite.center_y = center_y + math.sin(angle) * radius
            sprite.visible = visible
            sprite_index += 1

    return sprites


def arrange_cross(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    center_x: float = 400,
    center_y: float = 300,
    arm_length: float = 100.0,
    spacing: float = 50.0,
    include_center: bool = True,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in a cross or plus formation.

    Creates a cross pattern with equal-length arms extending up, down, left, and right
    from a center point. Optionally includes a center sprite.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        center_x: X coordinate of the cross center
        center_y: Y coordinate of the cross center
        arm_length: Length of each arm from center
        spacing: Distance between sprites along arms
        include_center: Whether to place a sprite at the center (default: True)
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create cross with center sprite
        cross = arrange_cross(count=9, center_x=400, center_y=300, arm_length=100)

        # Create hollow cross (no center)
        hollow_cross = arrange_cross(count=8, center_x=200, center_y=200,
                                   arm_length=80, include_center=False)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    sprite_index = 0
    total_sprites = len(sprites)

    # Place center sprite if requested
    if include_center and sprite_index < total_sprites:
        sprites[sprite_index].center_x = center_x
        sprites[sprite_index].center_y = center_y
        sprites[sprite_index].visible = visible
        sprite_index += 1

    # Calculate sprites per arm
    remaining_sprites = total_sprites - sprite_index
    sprites_per_arm = remaining_sprites // 4
    extra_sprites = remaining_sprites % 4

    # Define arm directions: right, up, left, down
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

    for arm_idx, (dx, dy) in enumerate(directions):
        arm_sprite_count = sprites_per_arm + (1 if arm_idx < extra_sprites else 0)

        for step in range(1, arm_sprite_count + 1):
            if sprite_index >= total_sprites:
                break

            x = center_x + dx * step * spacing
            y = center_y + dy * step * spacing

            sprites[sprite_index].center_x = x
            sprites[sprite_index].center_y = y
            sprites[sprite_index].visible = visible
            sprite_index += 1

    return sprites


def arrange_arrow(
    sprites: arcade.SpriteList | list[arcade.Sprite] | None = None,
    *,
    count: int | None = None,
    tip_x: float = 400,
    tip_y: float = 500,
    rows: int = 3,
    spacing_along: float = 50.0,
    spacing_outward: float = 40.0,
    invert: bool = False,
    sprite_factory: Callable[[], arcade.Sprite] | None = None,
    visible: bool = True,
) -> arcade.SpriteList:
    """Create or arrange sprites in an arrow or spear-head formation.

    Creates an arrow pattern with a tip sprite and symmetric wings extending
    backward and outward from the tip.

    Args:
        sprites: Existing sprites to arrange, or None to create new ones
        count: Number of sprites to create (required if sprites is None)
        tip_x: X coordinate of the arrow tip
        tip_y: Y coordinate of the arrow tip
        rows: Number of rows of wings behind the tip
        spacing_along: Distance between rows along the arrow shaft
        spacing_outward: Distance outward from center for each row of wings
        invert: If True, arrow points upward; if False, points downward
        sprite_factory: Function to create new sprites (if sprites is None)
        visible: Whether sprites should be visible (default: True)

    Returns:
        The arranged sprite list

    Example:
        # Create downward-pointing arrow
        arrow = arrange_arrow(count=7, tip_x=400, tip_y=500, rows=3)

        # Create upward-pointing arrow
        up_arrow = arrange_arrow(count=9, tip_x=300, tip_y=200, rows=4, invert=True)

        # Arrange existing sprites in arrow formation
        arrange_arrow(existing_sprites, tip_x=200, tip_y=300, spacing_along=40)
    """
    if sprites is None:
        if count is None or count <= 0:
            raise ValueError("When *sprites* is None you must supply a positive *count*.")
        sprite_factory = sprite_factory or _default_factory()
        sprites = arcade.SpriteList()
        for _ in range(count):
            sprite = sprite_factory()
            sprite.visible = visible
            sprites.append(sprite)
    else:
        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

    sprite_index = 0
    total_sprites = len(sprites)

    if total_sprites == 0:
        return sprites

    # Place tip sprite
    sprites[sprite_index].center_x = tip_x
    sprites[sprite_index].center_y = tip_y
    sprites[sprite_index].visible = visible
    sprite_index += 1

    # Calculate direction multiplier
    direction = 1 if invert else -1

    # Place wing rows
    for row in range(1, rows + 1):
        if sprite_index >= total_sprites:
            break

        # Calculate Y position for this row
        y_pos = tip_y + direction * row * spacing_along

        # Calculate wing spread for this row
        wing_spread = row * spacing_outward

        # Place left wing if sprite available
        if sprite_index < total_sprites:
            sprites[sprite_index].center_x = tip_x - wing_spread
            sprites[sprite_index].center_y = y_pos
            sprites[sprite_index].visible = visible
            sprite_index += 1

        # Place right wing if sprite available
        if sprite_index < total_sprites:
            sprites[sprite_index].center_x = tip_x + wing_spread
            sprites[sprite_index].center_y = y_pos
            sprites[sprite_index].visible = visible
            sprite_index += 1

    return sprites
