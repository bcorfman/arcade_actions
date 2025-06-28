"""
Attack patterns and group management.
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


def time_elapsed(seconds: float) -> Callable:
    """Create a condition function that returns True after the specified time.

    Args:
        seconds: Number of seconds to wait

    Returns:
        Condition function for use with conditional actions

    Example:
        move_action = MoveUntil((100, 0), time_elapsed(3.0))
    """
    start_time = None

    def condition():
        nonlocal start_time
        import time

        current_time = time.time()
        if start_time is None:
            start_time = current_time
        return (current_time - start_time) >= seconds

    return condition


def sprite_count(sprite_list: arcade.SpriteList, target_count: int, comparison: str = "<=") -> Callable:
    """Create a condition function that checks sprite list count.

    Args:
        sprite_list: The sprite list to monitor
        target_count: The count to compare against
        comparison: Comparison operator ("<=", ">=", "<", ">", "==", "!=")

    Returns:
        Condition function for use with conditional actions

    Example:
        fade_action = FadeUntil(-30, sprite_count(enemies, 2, "<="))
    """

    def condition():
        current_count = len(sprite_list)
        if comparison == "<=":
            return current_count <= target_count
        elif comparison == ">=":
            return current_count >= target_count
        elif comparison == "<":
            return current_count < target_count
        elif comparison == ">":
            return current_count > target_count
        elif comparison == "==":
            return current_count == target_count
        elif comparison == "!=":
            return current_count != target_count
        else:
            raise ValueError(f"Invalid comparison operator: {comparison}")

    return condition


# AttackGroup has been removed - use arcade.SpriteList directly with actions
#
# Example usage that replaces AttackGroup:
#
# # Instead of AttackGroup, use arcade.SpriteList directly:
# enemies = arcade.SpriteList()
#
# # Apply formation patterns:
# arrange_grid(enemies, rows=3, cols=5, start_x=200, start_y=400)
#
# # Apply actions directly to sprite list:
# move_action = MoveUntil((50, -25), time_elapsed(2.0))
# move_action.apply(enemies, tag="movement")
#
# # Use explicit composition functions (see composite.py):
# delay = DelayUntil(time_elapsed(1.0))
# fade = FadeUntil(-30, sprite_count(enemies, 2, "<="))
# move_sequence = sequence(delay, move_action)  # Instead of delay + move_action
# move_parallel = parallel(move_action, fade)   # Instead of move_action | fade
