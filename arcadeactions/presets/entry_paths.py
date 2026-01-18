"""Entry path presets for AttackGroup path-based entry sequences.

These functions return waypoint lists suitable for FollowPathUntil actions,
creating common entry patterns like loop-the-loop, corkscrew, zigzag, etc.
"""


def circle_arc_waypoints(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    """Generate waypoints for a perfect circular loop using cubic Bezier approximation.

    Uses the standard four 90-degree cubic Bezier arcs to approximate a circle.
    This creates a visually perfect circle with maximum radial error of ~0.06% of radius.

    Args:
        cx: X coordinate of circle center
        cy: Y coordinate of circle center
        radius: Radius of the circle

    Returns:
        List of 13 waypoints (12 control points + closing point) forming a complete 360° loop.
        Points start at 270° (bottom) and proceed counter-clockwise back to bottom.
    """
    # Magic constant for cubic Bezier circle approximation
    # k = (4/3) * tan(π/8) ≈ 0.5522847498
    k = radius * 0.5522847498307935

    return [
        # Start at bottom (270°)
        (cx, cy - radius),
        # Bottom → Right 90° arc (control points for first quadrant)
        (cx + k, cy - radius),  # Handle 1
        (cx + radius, cy - k),  # Handle 2
        (cx + radius, cy),  # Right (0°)
        # Right → Top 90° arc
        (cx + radius, cy + k),  # Handle 1
        (cx + k, cy + radius),  # Handle 2
        (cx, cy + radius),  # Top (90°)
        # Top → Left 90° arc
        (cx - k, cy + radius),  # Handle 1
        (cx - radius, cy + k),  # Handle 2
        (cx - radius, cy),  # Left (180°)
        # Left → Bottom 90° arc
        (cx - radius, cy - k),  # Handle 1
        (cx - k, cy - radius),  # Handle 2
        (cx, cy - radius),  # Back to bottom (270°) - completes the loop
    ]


def loop_the_loop_exact(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    loop_center_x: float,
    loop_center_y: float,
    loop_radius: float,
) -> list[tuple[float, float]]:
    """Create a precise loop-the-loop entry path with a mathematically exact circular loop.

    This function creates a complete entry path: off-screen start → approach → tight circular
    loop → exit → formation position. The loop uses cubic Bezier approximation for perfect
    circular geometry.

    Args:
        start_x: Starting X coordinate (off-screen)
        start_y: Starting Y coordinate (off-screen)
        end_x: Ending X coordinate (formation position)
        end_y: Ending Y coordinate (formation position)
        loop_center_x: X coordinate of loop center
        loop_center_y: Y coordinate of loop center
        loop_radius: Radius of the circular loop

    Returns:
        List of waypoints for FollowPathUntil forming: start → approach → loop → exit → end

    Example:
        from arcadeactions.presets.entry_paths import loop_the_loop_exact
        path = loop_the_loop_exact(
            start_x=600, start_y=-100,
            end_x=200, end_y=350,
            loop_center_x=400, loop_center_y=200,
            loop_radius=150
        )
        group.entry_path(path, velocity=2.5, spacing_frames=50)
    """
    waypoints = [
        (start_x, start_y),  # Start point (off-screen)
    ]

    # Approach point - vertical line below the loop
    approach_y = loop_center_y - loop_radius * 0.6
    waypoints.append((loop_center_x, approach_y))

    # Add the circular loop waypoints
    loop_waypoints = circle_arc_waypoints(loop_center_x, loop_center_y, loop_radius)
    waypoints.extend(loop_waypoints)

    # Exit point - vertical line below the loop (same as approach)
    waypoints.append((loop_center_x, approach_y))

    # End point (formation position)
    waypoints.append((end_x, end_y))

    return waypoints


def loop_the_loop(
    start_x: float = 400,
    start_y: float = -100,
    end_x: float = 400,
    end_y: float = 500,
    loop_radius: float = 150.0,
) -> list[tuple[float, float]]:
    """Create a loop-the-loop entry path.

    Args:
        start_x: Starting X coordinate (off-screen bottom)
        start_y: Starting Y coordinate
        end_x: Ending X coordinate (formation start)
        end_y: Ending Y coordinate
        loop_radius: Radius of the loop

    Returns:
        List of waypoints for FollowPathUntil that form a circular loop
    """
    import math

    # Calculate loop center - positioned between start and end
    loop_center_x = (start_x + end_x) / 2
    loop_center_y = (start_y + end_y) / 2

    # For Bezier curves to approximate a circle, we need to use control points
    # positioned outside the desired circle radius. Bezier curves average through
    # control points, pulling toward the center, so we compensate with a larger radius.
    # Using fewer, well-positioned points works better than many points.
    bezier_radius = loop_radius * 1.5  # Compensate for Bezier curve averaging

    waypoints = [
        (start_x, start_y),  # Start point
    ]

    # Approach the loop from below
    waypoints.append((loop_center_x, loop_center_y - loop_radius * 0.6))

    # Create waypoints around the circle using 8 key points
    # This creates a smoother loop than many points
    angles = [
        3 * math.pi / 2,  # Bottom (270°)
        0,  # Right (0°)
        math.pi / 2,  # Top (90°)
        math.pi,  # Left (180°)
        3 * math.pi / 2,  # Bottom again (270°) - completes the loop
    ]

    for angle in angles:
        x = loop_center_x + bezier_radius * math.cos(angle)
        y = loop_center_y + bezier_radius * math.sin(angle)
        waypoints.append((x, y))

    # Exit the loop
    waypoints.append((loop_center_x, loop_center_y - loop_radius * 0.6))

    # End point
    waypoints.append((end_x, end_y))

    return waypoints


def corkscrew_entry(
    start_x: float = 400,
    start_y: float = -100,
    end_x: float = 400,
    end_y: float = 500,
    spiral_radius: float = 100.0,
    turns: float = 2.0,
) -> list[tuple[float, float]]:
    """Create a corkscrew/spiral entry path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        spiral_radius: Radius of the spiral
        turns: Number of full turns in the spiral

    Returns:
        List of waypoints for FollowPathUntil
    """
    import math

    points = [(start_x, start_y)]
    total_dy = end_y - start_y
    num_points = int(turns * 6) + 1  # 6 points per turn for smooth spiral

    for i in range(1, num_points):
        progress = i / num_points
        y = start_y + progress * total_dy
        angle = turns * 2 * math.pi * progress
        x = start_x + math.cos(angle) * spiral_radius
        points.append((x, y))

    points.append((end_x, end_y))
    return points


def zigzag_entry(
    start_x: float = 400,
    start_y: float = -100,
    end_x: float = 400,
    end_y: float = 500,
    zigzag_width: float = 200.0,
    segments: int = 4,
) -> list[tuple[float, float]]:
    """Create a zigzag entry path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        zigzag_width: Horizontal width of each zigzag segment
        segments: Number of zigzag segments (must be >= 2)

    Returns:
        List of waypoints for FollowPathUntil
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


def straight_entry(
    start_x: float = 400,
    start_y: float = -100,
    end_x: float = 400,
    end_y: float = 500,
) -> list[tuple[float, float]]:
    """Create a straight vertical entry path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate

    Returns:
        List of waypoints for FollowPathUntil
    """
    return [(start_x, start_y), (end_x, end_y)]


def swoop_entry(
    start_x: float = 400,
    start_y: float = -100,
    end_x: float = 400,
    end_y: float = 500,
    swoop_strength: float = 300.0,
) -> list[tuple[float, float]]:
    """Create a swooping curve entry path.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        swoop_strength: How much the swoop curves (positive = right, negative = left)

    Returns:
        List of waypoints for FollowPathUntil (quadratic Bezier)
    """
    # Control point creates the swoop
    mid_x = (start_x + end_x) / 2 + swoop_strength
    mid_y = (start_y + end_y) / 2
    return [(start_x, start_y), (mid_x, mid_y), (end_x, end_y)]
