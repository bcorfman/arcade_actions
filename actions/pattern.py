"""
Movement patterns and condition helpers.

This module provides functions for creating complex movement patterns like zigzag,
wave, spiral, and orbit movements, as well as condition helper functions for
use with conditional actions.
"""

import math
from collections.abc import Callable

import arcade


def create_zigzag_pattern(width: float, height: float, speed: float, segments: int = 4):
    """Create a zigzag movement pattern using sequences of MoveUntil actions.

    Args:
        width: Horizontal distance for each zigzag segment
        height: Vertical distance for each zigzag segment
        speed: Movement speed in pixels per second
        segments: Number of zigzag segments to create

    Returns:
        Sequence action that creates zigzag movement

    Example:
        zigzag = create_zigzag_pattern(width=100, height=50, speed=150, segments=6)
        zigzag.apply(sprite, tag="zigzag_movement")
    """
    from actions.composite import sequence
    from actions.conditional import MoveUntil, duration

    # Calculate time for each segment
    distance = math.sqrt(width**2 + height**2)
    segment_time = distance / speed

    actions = []
    for i in range(segments):
        # Alternate direction for zigzag effect
        direction = 1 if i % 2 == 0 else -1
        velocity = (width * direction / segment_time, height / segment_time)

        actions.append(MoveUntil(velocity, duration(segment_time)))

    return sequence(*actions)


def create_wave_pattern(amplitude: float, frequency: float, length: float, speed: float):
    """Create a smooth wave movement pattern using Bezier path following.

    Args:
        amplitude: Height of the wave peaks/troughs
        frequency: Number of complete wave cycles
        length: Total horizontal distance of the wave
        speed: Movement speed in pixels per second

    Returns:
        FollowPathUntil action that creates wave movement

    Example:
        wave = create_wave_pattern(amplitude=50, frequency=2, length=400, speed=200)
        wave.apply(sprite, tag="wave_movement")
    """
    from actions.conditional import FollowPathUntil, duration

    # Generate control points for wave using sine function
    num_points = max(8, int(frequency * 4))  # More points for higher frequency
    control_points = []

    for i in range(num_points):
        t = i / (num_points - 1)
        x = t * length
        y = amplitude * math.sin(2 * math.pi * frequency * t)
        control_points.append((x, y))

    # Calculate expected duration based on curve length and speed
    expected_duration = length / speed

    return FollowPathUntil(
        control_points,
        speed,
        duration(expected_duration),
        rotate_with_path=True,  # Optional: sprite rotates to follow wave direction
    )


def create_smooth_zigzag_pattern(width: float, height: float, speed: float, ease_duration: float = 0.5):
    """Create a zigzag pattern with smooth easing transitions.

    Args:
        width: Horizontal distance for each zigzag segment
        height: Vertical distance for each zigzag segment
        speed: Movement speed in pixels per second
        ease_duration: Duration of easing effect in seconds

    Returns:
        Ease action wrapping zigzag movement

    Example:
        smooth_zigzag = create_smooth_zigzag_pattern(100, 50, 150, ease_duration=1.0)
        smooth_zigzag.apply(sprite, tag="smooth_zigzag")
    """
    from arcade import easing

    from actions.easing import Ease

    # Create the base zigzag
    zigzag = create_zigzag_pattern(width, height, speed)

    # Wrap with easing for smooth acceleration
    return Ease(zigzag, seconds=ease_duration, ease_function=easing.ease_in_out)


def create_spiral_pattern(
    center_x: float, center_y: float, max_radius: float, revolutions: float, speed: float, direction: str = "outward"
):
    """Create an outward or inward spiral pattern.

    Args:
        center_x: X coordinate of spiral center
        center_y: Y coordinate of spiral center
        max_radius: Maximum radius of the spiral
        revolutions: Number of complete revolutions
        speed: Movement speed in pixels per second
        direction: "outward" for expanding spiral, "inward" for contracting

    Returns:
        FollowPathUntil action that creates spiral movement

    Example:
        spiral = create_spiral_pattern(400, 300, 150, 3.0, 200, "outward")
        spiral.apply(sprite, tag="spiral_movement")
    """
    from actions.conditional import FollowPathUntil, duration

    num_points = max(20, int(revolutions * 8))
    control_points = []

    for i in range(num_points):
        t = i / (num_points - 1)
        if direction == "outward":
            radius = t * max_radius
        else:  # inward
            radius = (1 - t) * max_radius

        angle = t * revolutions * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        control_points.append((x, y))

    # Estimate total path length
    total_length = revolutions * math.pi * max_radius  # Approximate
    duration_time = total_length / speed

    return FollowPathUntil(control_points, speed, duration(duration_time), rotate_with_path=True)


def create_figure_eight_pattern(center_x: float, center_y: float, width: float, height: float, speed: float):
    """Create a figure-8 (infinity) movement pattern.

    Args:
        center_x: X coordinate of pattern center
        center_y: Y coordinate of pattern center
        width: Width of the figure-8
        height: Height of the figure-8
        speed: Movement speed in pixels per second

    Returns:
        FollowPathUntil action that creates figure-8 movement

    Example:
        figure_eight = create_figure_eight_pattern(400, 300, 200, 100, 180)
        figure_eight.apply(sprite, tag="figure_eight")
    """
    from actions.conditional import FollowPathUntil, duration

    # Generate figure-8 using parametric equations
    num_points = 16
    control_points = []

    for i in range(num_points + 1):  # +1 to complete the loop
        t = (i / num_points) * 2 * math.pi
        # Parametric equations for figure-8
        x = center_x + (width / 2) * math.sin(t)
        y = center_y + (height / 2) * math.sin(2 * t)
        control_points.append((x, y))

    # Estimate path length (approximate)
    path_length = 2 * math.pi * max(width, height) / 2
    duration_time = path_length / speed

    return FollowPathUntil(control_points, speed, duration(duration_time), rotate_with_path=True)


def create_orbit_pattern(center_x: float, center_y: float, radius: float, speed: float, clockwise: bool = True):
    """Create a circular orbit pattern.

    Args:
        center_x: X coordinate of orbit center
        center_y: Y coordinate of orbit center
        radius: Radius of the orbit
        speed: Movement speed in pixels per second
        clockwise: True for clockwise orbit, False for counter-clockwise

    Returns:
        FollowPathUntil action that creates orbital movement

    Example:
        orbit = create_orbit_pattern(400, 300, 120, 150, clockwise=True)
        orbit.apply(sprite, tag="orbit")
    """
    from actions.conditional import FollowPathUntil, duration

    # Generate circular path
    num_points = 12
    control_points = []

    for i in range(num_points + 1):  # +1 to complete the circle
        angle_step = 2 * math.pi / num_points
        angle = i * angle_step
        if not clockwise:
            angle = -angle

        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        control_points.append((x, y))

    # Calculate duration for one complete orbit
    circumference = 2 * math.pi * radius
    duration_time = circumference / speed

    return FollowPathUntil(control_points, speed, duration(duration_time), rotate_with_path=True)


def create_bounce_pattern(velocity: tuple[float, float], bounds: tuple[float, float, float, float]):
    """Create a bouncing movement pattern within boundaries.

    Args:
        velocity: (dx, dy) initial velocity vector
        bounds: (left, bottom, right, top) boundary box

    Returns:
        MoveUntil action with bouncing behavior

    Example:
        bounce = create_bounce_pattern((150, 100), bounds=(0, 0, 800, 600))
        bounce.apply(sprite, tag="bouncing")
    """
    from actions.conditional import MoveUntil

    return MoveUntil(
        velocity,
        lambda: False,  # Continue indefinitely
        bounds=bounds,
        boundary_behavior="bounce",
    )


def create_patrol_pattern(start_pos: tuple[float, float], end_pos: tuple[float, float], speed: float):
    """Create a back-and-forth patrol pattern between two points.

    Args:
        start_pos: (x, y) starting position
        end_pos: (x, y) ending position
        speed: Movement speed in pixels per second

    Returns:
        Sequence action that creates patrol movement

    Example:
        patrol = create_patrol_pattern((100, 200), (500, 200), 120)
        patrol.apply(sprite, tag="patrol")
    """
    from actions.composite import sequence
    from actions.conditional import MoveUntil, duration

    # Calculate distance and time for each leg
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    travel_time = distance / speed

    # Create forward and return movements
    forward_velocity = (dx / travel_time, dy / travel_time)
    return_velocity = (-dx / travel_time, -dy / travel_time)

    return sequence(
        MoveUntil(forward_velocity, duration(travel_time)), MoveUntil(return_velocity, duration(travel_time))
    )


# Condition helper functions
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


# Usage examples and notes:
#
# # Create enemy formation using formation functions:
# from actions.formation import arrange_grid
# enemies = arrange_grid(rows=3, cols=5, start_x=200, start_y=400)
#
# # Apply movement patterns:
# wave_movement = create_wave_pattern(amplitude=30, frequency=1, length=600, speed=100)
# wave_movement.apply(enemies, tag="formation_wave")
#
# # Individual patterns for each sprite:
# for i, enemy in enumerate(enemies):
#     # Stagger the wave timing for a "rolling wave" effect
#     delay_time = i * 0.1
#     from actions.composite import sequence
#     from actions.conditional import DelayUntil, duration
#     delayed_wave = sequence(
#         DelayUntil(duration(delay_time)),
#         create_wave_pattern(amplitude=20, frequency=2, length=400, speed=120)
#     )
#     delayed_wave.apply(enemy, tag=f"individual_wave_{i}")
#
# # Combine patterns with other actions:
# from actions.composite import parallel
# from actions.conditional import FadeUntil
# combined = parallel(
#     create_spiral_pattern(400, 300, 100, 2, 150),
#     FadeUntil(-10, sprite_count(enemies, 1, "<="))
# )
# combined.apply(sprite, tag="spiral_fade")
