"""
Attack patterns and group management.
"""

import math
from collections.abc import Callable

import arcade


def arrange_line(
    sprites: arcade.SpriteList | list[arcade.Sprite], start_x: float = 0, start_y: float = 0, spacing: float = 50.0
):
    """Arrange sprites in a horizontal line.

    Positions sprites in a straight line with configurable spacing between them.
    Useful for creating horizontal formations, bullet patterns, or UI elements.

    Args:
        sprites: List of sprites to arrange
        start_x: X coordinate of the first sprite (default: 0)
        start_y: Y coordinate for all sprites (default: 0)
        spacing: Distance between sprite centers in pixels (default: 50.0)

    Example:
        arrange_line(enemies, start_x=100, start_y=300, spacing=80.0)
        # Sprites positioned at (100,300), (180,300), (260,300), etc.
    """
    for i, sprite in enumerate(sprites):
        sprite.center_x = start_x + i * spacing
        sprite.center_y = start_y


def arrange_grid(
    sprites: arcade.SpriteList | list[arcade.Sprite],
    rows: int = 5,
    cols: int = 10,
    start_x: float = 100,
    start_y: float = 500,
    spacing_x: float = 60.0,
    spacing_y: float = 50.0,
):
    """Arrange sprites in a rectangular grid formation.

    Creates rows and columns of sprites with configurable spacing.
    Perfect for Space Invaders-style enemy formations or organized layouts.

    Args:
        sprites: List of sprites to arrange
        rows: Number of rows in the grid (default: 5)
        cols: Number of columns in the grid (default: 10)
        start_x: X coordinate of the top-left sprite (default: 100)
        start_y: Y coordinate of the top row (default: 500)
        spacing_x: Horizontal spacing between sprites in pixels (default: 60.0)
        spacing_y: Vertical spacing between sprites in pixels (default: 50.0)

    Example:
        arrange_grid(enemies, rows=3, cols=5, start_x=200, start_y=400, spacing_x=80, spacing_y=60)
        # Creates 3x5 grid starting at (200,400)
    """
    for i, sprite in enumerate(sprites):
        row = i // cols
        col = i % cols
        sprite.center_x = start_x + col * spacing_x
        sprite.center_y = start_y - row * spacing_y


def arrange_circle(
    sprites: arcade.SpriteList | list[arcade.Sprite],
    center_x: float = 400,
    center_y: float = 300,
    radius: float = 100.0,
):
    """Arrange sprites in a circular formation.

    Distributes sprites evenly around a circle with configurable radius.
    Great for radial bullet patterns or defensive formations.

    Args:
        sprites: List of sprites to arrange
        center_x: X coordinate of the circle center (default: 400)
        center_y: Y coordinate of the circle center (default: 300)
        radius: Radius of the circle in pixels (default: 100.0)

    Example:
        arrange_circle(enemies, center_x=400, center_y=300, radius=150.0)
        # Sprites arranged in circle around (400,300) with radius 150
    """
    count = len(sprites)
    if count == 0:
        return

    angle_step = 2 * math.pi / count
    for i, sprite in enumerate(sprites):
        angle = i * angle_step
        sprite.center_x = center_x + math.cos(angle) * radius
        sprite.center_y = center_y + math.sin(angle) * radius


def arrange_v_formation(
    sprites: arcade.SpriteList | list[arcade.Sprite],
    apex_x: float = 400,
    apex_y: float = 500,
    angle: float = 45.0,
    spacing: float = 50.0,
):
    """Arrange sprites in a V or wedge formation.

    Creates a V-shaped formation with one sprite at the apex and others
    arranged alternately on left and right sides. Useful for flying formations
    or arrow-like attack patterns.

    Args:
        sprites: List of sprites to arrange
        apex_x: X coordinate of the apex sprite (default: 400)
        apex_y: Y coordinate of the apex sprite (default: 500)
        angle: Angle of the V formation in degrees (default: 45.0)
        spacing: Distance between sprites in the formation (default: 50.0)

    Example:
        arrange_v_formation(enemies, apex_x=400, apex_y=500, angle=30.0, spacing=60.0)
        # Creates V formation with apex at (400,500)
    """
    count = len(sprites)
    if count == 0:
        return

    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Place the first sprite at the apex
    sprites[0].center_x = apex_x
    sprites[0].center_y = apex_y

    # Place remaining sprites alternating on left and right sides
    for i in range(1, count):
        side = 1 if i % 2 == 1 else -1  # Alternate sides
        distance = (i + 1) // 2 * spacing

        offset_x = side * math.cos(angle_rad) * distance
        offset_y = -math.sin(angle_rad) * distance

        sprites[i].center_x = apex_x + offset_x
        sprites[i].center_y = apex_y + offset_y


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
