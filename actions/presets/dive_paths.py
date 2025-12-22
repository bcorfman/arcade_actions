"""Bezier dive path presets for breakaway behaviors.

These functions return control point lists suitable for FollowPathUntil actions,
creating common dive patterns like straight dives, curves, loops, and zigzags.
"""

from typing import Any


def dive_straight(
    start_x: float = 400,
    start_y: float = 500,
    end_x: float = 400,
    end_y: float = 100,
) -> list[tuple[float, float]]:
    """Create a straight vertical dive path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate (top)
        end_x: Ending X coordinate
        end_y: Ending Y coordinate (bottom)

    Returns:
        List of control points for FollowPathUntil

    Example:
        path = dive_straight(start_x=400, start_y=500, end_x=400, end_y=100)
        action = FollowPathUntil(path, velocity=150, condition=after_frames(60))
    """
    return [(start_x, start_y), (end_x, end_y)]


def dive_curve(
    start_x: float = 400,
    start_y: float = 500,
    end_x: float = 200,
    end_y: float = 100,
    curve_strength: float = 200.0,
) -> list[tuple[float, float]]:
    """Create a curved dive path with a control point.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        curve_strength: How much the curve bends (positive = right, negative = left)

    Returns:
        List of control points for FollowPathUntil (quadratic Bezier)
    """
    # Control point creates the curve
    mid_x = (start_x + end_x) / 2 + curve_strength
    mid_y = (start_y + end_y) / 2
    return [(start_x, start_y), (mid_x, mid_y), (end_x, end_y)]


def dive_zigzag(
    start_x: float = 400,
    start_y: float = 500,
    end_x: float = 400,
    end_y: float = 100,
    zigzag_width: float = 150.0,
    segments: int = 3,
) -> list[tuple[float, float]]:
    """Create a zigzag dive path with multiple direction changes.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        zigzag_width: Horizontal width of each zigzag segment
        segments: Number of zigzag segments (must be >= 2)

    Returns:
        List of control points for FollowPathUntil
    """
    if segments < 2:
        segments = 2

    points = [(start_x, start_y)]
    total_dy = end_y - start_y
    dy_per_segment = total_dy / segments

    for i in range(1, segments):
        y = start_y + i * dy_per_segment
        # Alternate left/right
        direction = 1 if i % 2 == 1 else -1
        x = start_x + direction * zigzag_width
        points.append((x, y))

    points.append((end_x, end_y))
    return points


def dive_loop(
    start_x: float = 400,
    start_y: float = 500,
    end_x: float = 400,
    end_y: float = 300,
    loop_radius: float = 100.0,
) -> list[tuple[float, float]]:
    """Create a loop-the-loop dive path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate (typically same as start)
        end_y: Ending Y coordinate (below loop)
        loop_radius: Radius of the loop

    Returns:
        List of control points for FollowPathUntil (creates a loop)
    """
    # Create a loop using multiple control points
    # Top of loop
    top_x = start_x
    top_y = start_y - loop_radius

    # Left side of loop
    left_x = start_x - loop_radius
    left_y = start_y

    # Right side of loop
    right_x = start_x + loop_radius
    right_y = start_y

    # Return to center and dive down
    return [
        (start_x, start_y),
        (top_x, top_y),
        (left_x, left_y),
        (right_x, right_y),
        (end_x, end_y),
    ]


def dive_corkscrew(
    start_x: float = 400,
    start_y: float = 500,
    end_x: float = 400,
    end_y: float = 100,
    spiral_radius: float = 80.0,
    turns: float = 1.5,
) -> list[tuple[float, float]]:
    """Create a corkscrew/spiral dive path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        spiral_radius: Radius of the spiral
        turns: Number of full turns in the spiral

    Returns:
        List of control points for FollowPathUntil
    """
    import math

    points = [(start_x, start_y)]
    total_dy = end_y - start_y
    num_points = int(turns * 4) + 1  # 4 points per turn

    for i in range(1, num_points):
        progress = i / num_points
        y = start_y + progress * total_dy
        angle = turns * 2 * math.pi * progress
        x = start_x + math.cos(angle) * spiral_radius
        points.append((x, y))

    points.append((end_x, end_y))
    return points
