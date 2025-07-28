"""
Movement patterns and condition helpers.

This module provides functions for creating complex movement patterns like zigzag,
wave, spiral, and orbit movements, as well as condition helper functions for
use with conditional actions.
"""

import math
import random
from collections.abc import Callable

import arcade
from arcade import easing

from actions import DelayUntil, Ease, FollowPathUntil, MoveUntil, duration, sequence

# Boid-based formation entry patterns


class BoidMoveUntil:
    """Move sprites using boid algorithm until a condition is satisfied.

    This action applies classic boid flocking behavior (cohesion, separation, alignment)
    to a sprite list, with optional player avoidance and velocity clamping.

    Args:
        max_speed: Maximum speed in pixels per frame (Arcade velocity semantics)
        duration_condition: Function that returns True when movement should stop
        avoid_sprites: Optional SpriteList of sprites to avoid (e.g., player, obstacles)
        cohesion_weight: Strength of cohesion force (default: 0.005)
        separation_weight: Strength of separation force (default: 0.05)
        alignment_weight: Strength of alignment force (default: 0.05)
        avoid_weight: Strength of avoidance force (default: 0.02)
        avoid_distance: Distance at which avoidance kicks in (default: 200)
        separation_distance: Distance for separation behavior (default: 30)
    """

    def __init__(
        self,
        *,
        max_speed: float,
        duration_condition: Callable[[], bool],
        avoid_sprites: arcade.SpriteList | None = None,
        cohesion_weight: float = 0.005,
        separation_weight: float = 0.05,
        alignment_weight: float = 0.05,
        avoid_weight: float = 0.02,
        avoid_distance: float = 200.0,
        separation_distance: float = 30.0,
    ):
        self.max_speed = max_speed
        self.condition = duration_condition
        self.avoid_sprites = avoid_sprites
        self.cohesion_weight = cohesion_weight
        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.avoid_weight = avoid_weight
        self.avoid_distance = avoid_distance
        self.separation_distance = separation_distance

        # Action state
        self.target = None
        self.tag = None
        self.done = False
        self._is_active = False

    def apply(self, target: arcade.SpriteList, tag: str | None = None):
        """Apply this action to a sprite list."""
        self.target = target
        self.tag = tag
        self._is_active = True
        # Add to global action manager
        from actions.base import Action

        Action._active_actions.append(self)
        return self

    def start(self):
        """Start the boid action."""
        self._is_active = True

    def stop(self) -> None:
        """Stop the action and clean up."""
        self.done = True
        self._is_active = False
        if self.target:
            # Stop all sprites
            for sprite in self.target:
                sprite.change_x = 0
                sprite.change_y = 0
        # Remove from global action manager
        from actions.base import Action

        if self in Action._active_actions:
            Action._active_actions.remove(self)

    def update(self, delta_time: float) -> None:
        """Update boid movement."""
        if not self._is_active or self.done or not self.target:
            return

        # Check condition
        if self.condition():
            self.stop()
            return

        if len(self.target) == 0:
            return

        # Calculate flock center and average velocity for cohesion/alignment
        center_x = sum(s.center_x for s in self.target) / len(self.target)
        center_y = sum(s.center_y for s in self.target) / len(self.target)
        avg_vx = sum(s.change_x for s in self.target) / len(self.target)
        avg_vy = sum(s.change_y for s in self.target) / len(self.target)

        for sprite in self.target:
            # Initialize steering forces
            steer_x = steer_y = 0.0

            # Cohesion: steer toward flock center
            steer_x += (center_x - sprite.center_x) * self.cohesion_weight
            steer_y += (center_y - sprite.center_y) * self.cohesion_weight

            # Separation: avoid nearby flockmates
            for other in self.target:
                if other is sprite:
                    continue
                dx = other.center_x - sprite.center_x
                dy = other.center_y - sprite.center_y
                dist_sq = dx * dx + dy * dy
                if dist_sq < self.separation_distance * self.separation_distance and dist_sq > 0:
                    # Steer away from other sprite
                    steer_x -= dx * self.separation_weight
                    steer_y -= dy * self.separation_weight

            # Alignment: match average flock velocity
            steer_x += (avg_vx - sprite.change_x) * self.alignment_weight
            steer_y += (avg_vy - sprite.change_y) * self.alignment_weight

            # Avoidance: steer away from all avoid_sprites
            if self.avoid_sprites:
                for avoid_sprite in self.avoid_sprites:
                    dx = avoid_sprite.center_x - sprite.center_x
                    dy = avoid_sprite.center_y - sprite.center_y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < self.avoid_distance * self.avoid_distance and dist_sq > 0:
                        steer_x -= dx * self.avoid_weight
                        steer_y -= dy * self.avoid_weight

            # Apply steering to current velocity
            new_vx = sprite.change_x + steer_x
            new_vy = sprite.change_y + steer_y

            # Clamp to max speed
            speed = math.sqrt(new_vx * new_vx + new_vy * new_vy)
            if speed > self.max_speed:
                scale = self.max_speed / speed
                new_vx *= scale
                new_vy *= scale

            sprite.change_x = new_vx
            sprite.change_y = new_vy


def _generate_random_spawn_point(spawn_area: tuple[float, float, float, float]) -> tuple[float, float]:
    """Generate a random point within the spawn area.

    Args:
        spawn_area: (left, bottom, right, top) boundary rectangle

    Returns:
        (x, y) random point within the area
    """
    left, bottom, right, top = spawn_area
    x = random.uniform(left, right) if left != right else left
    y = random.uniform(bottom, top) if bottom != top else bottom
    return (x, y)


def _generate_spaced_spawn_points(
    spawn_area: tuple[float, float, float, float], num_sprites: int, min_spacing: float = 30.0
) -> list[tuple[float, float]]:
    """Generate spawn points with minimum spacing between sprites.

    Args:
        spawn_area: (left, bottom, right, top) boundary rectangle
        num_sprites: Number of sprites to position
        min_spacing: Minimum distance between sprites

    Returns:
        List of (x, y) positions with minimum spacing
    """
    left, bottom, right, top = spawn_area
    positions = []

    for _ in range(num_sprites):
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            # Generate random position
            x = random.uniform(left, right) if left != right else left
            y = random.uniform(bottom, top) if bottom != top else bottom

            # Check distance from all existing positions
            too_close = False
            for existing_x, existing_y in positions:
                distance = math.sqrt((x - existing_x) ** 2 + (y - existing_y) ** 2)
                if distance < min_spacing:
                    too_close = True
                    break

            if not too_close:
                positions.append((x, y))
                break

            attempts += 1

        # If we couldn't find a good position, just use the random one
        if attempts >= max_attempts:
            positions.append((x, y))

    return positions


def _calculate_adaptive_spacing(sprites: arcade.SpriteList, base_spacing: float = 40.0) -> float:
    """Calculate adaptive spacing based on sprite sizes.

    Args:
        sprites: SpriteList to calculate spacing for
        base_spacing: Base spacing in pixels (default: 40.0)

    Returns:
        Adaptive spacing value that considers sprite sizes
    """
    if not sprites:
        return base_spacing

    # Calculate average sprite size
    total_width = 0
    total_height = 0
    count = 0

    for sprite in sprites:
        # Get sprite dimensions
        if hasattr(sprite, "width") and hasattr(sprite, "height"):
            total_width += sprite.width
            total_height += sprite.height
            count += 1
        elif hasattr(sprite, "texture") and sprite.texture:
            # Fallback to texture size
            total_width += sprite.texture.width
            total_height += sprite.texture.height
            count += 1

    if count == 0:
        return base_spacing

    # Calculate average sprite size
    avg_width = total_width / count
    avg_height = total_height / count
    avg_size = max(avg_width, avg_height)

    # Adaptive spacing: base spacing + 50% of average sprite size
    # This ensures sprites don't overlap even if they're large
    adaptive_spacing = base_spacing + (avg_size * 0.5)

    # Clamp to reasonable bounds (20-200 pixels)
    return max(20.0, min(200.0, adaptive_spacing))


def create_boid_flock_pattern(
    max_speed: float, duration_seconds: float, avoid_sprites: arcade.SpriteList | None = None, **boid_kwargs
) -> BoidMoveUntil:
    """Create a boid flocking pattern for a specified duration.

    Args:
        max_speed: Maximum speed in pixels per frame
        duration_seconds: How long to run the boid behavior
        avoid_sprites: Optional SpriteList of sprites to avoid (e.g., player, obstacles)
        **boid_kwargs: Additional boid parameters (cohesion_weight, etc.)

    Returns:
        BoidMoveUntil action

    Example:
        flock_pattern = create_boid_flock_pattern(4.0, 3.0, avoid_sprites=player_sprites)
        flock_pattern.apply(enemy_sprites, tag="flock_cruise")
    """
    from actions.conditional import duration

    return BoidMoveUntil(
        max_speed=max_speed, duration_condition=duration(duration_seconds), avoid_sprites=avoid_sprites, **boid_kwargs
    )


def create_zigzag_pattern(dimensions: tuple[float, float], speed: float, segments: int = 4):
    """Create a zigzag movement pattern using sequences of MoveUntil actions.

    Args:
        width: Horizontal distance for each zigzag segment
        height: Vertical distance for each zigzag segment
        speed: Movement speed in pixels per second
        segments: Number of zigzag segments to create

    Returns:
        Sequence action that creates zigzag movement

    Example:
        zigzag = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=6)
        zigzag.apply(sprite, tag="zigzag_movement")
    """

    # Calculate time for each segment
    width, height = dimensions
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


def create_smooth_zigzag_pattern(dimensions: tuple[float, float], speed: float, ease_duration: float = 0.5):
    """Create a zigzag pattern with smooth easing transitions.

    Args:
        width: Horizontal distance for each zigzag segment
        height: Vertical distance for each zigzag segment
        speed: Movement speed in pixels per second
        ease_duration: Duration of easing effect in seconds

    Returns:
        Ease action wrapping zigzag movement

    Example:
        smooth_zigzag = create_smooth_zigzag_pattern(dimensions=(100, 50), speed=150, ease_duration=1.0)
        smooth_zigzag.apply(sprite, tag="smooth_zigzag")
    """

    # Create the base zigzag
    zigzag = create_zigzag_pattern(dimensions, speed)

    # Wrap with easing for smooth acceleration
    return Ease(zigzag, duration=ease_duration, ease_function=easing.ease_in_out)


def create_spiral_pattern(
    center: tuple[float, float], max_radius: float, revolutions: float, speed: float, direction: str = "outward"
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
    center_x, center_y = center
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


def create_figure_eight_pattern(center: tuple[float, float], width: float, height: float, speed: float):
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
    center_x, center_y = center
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


def create_orbit_pattern(center: tuple[float, float], radius: float, speed: float, clockwise: bool = True):
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
    center_x, center_y = center

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
    from .conditional import infinite

    return MoveUntil(
        velocity,
        infinite,  # Continue indefinitely
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


def _calculate_movement_duration(
    start_pos: tuple[float, float],
    target_pos: tuple[float, float],
    speed: float,
) -> float:
    """Calculate movement duration from start to target position.

    Args:
        start_pos: (x, y) starting position
        target_pos: (x, y) target position
        speed: Movement speed in pixels per frame

    Returns:
        Duration in seconds
    """
    dx = target_pos[0] - start_pos[0]
    dy = target_pos[1] - start_pos[1]
    distance = math.sqrt(dx * dx + dy * dy)

    if speed <= 0:
        return 0

    # Convert from pixels per frame to seconds (assuming 60 FPS)
    return distance / speed / 60.0


def create_formation_entry_from_sprites(
    target_formation: arcade.SpriteList, **kwargs
) -> list[tuple[arcade.Sprite, arcade.SpriteList]]:
    """Create formation entry pattern from a target formation SpriteList.

    This function creates sprites positioned around the upper half of the window boundary
    (left side, top, right side) and creates a three-phase movement:
    1. Invisible movement to target positions
    2. Return to origin positions
    3. Visible entry with staggered waves to avoid collisions

    Args:
        target_formation: SpriteList with sprites positioned at target formation locations
        **kwargs: Additional arguments including:
            - window_bounds: (left, bottom, right, top) window boundaries
            - speed: Movement speed in pixels per frame
            - stagger_delay: Delay between waves in seconds
            - min_spacing: Minimum spacing between sprites during movement

    Returns:
        List of (sprite, action) tuples

    Example:
        # Create target formation (e.g., circle formation)
        target_formation = arrange_circle(count=8, center_x=400, center_y=300, radius=100, visible=False)

        # Create entry pattern
        entry_actions = create_formation_entry_from_sprites(
            target_formation,
            window_bounds=(0, 0, 800, 600),
            speed=5.0,
            stagger_delay=1.0
        )

        # Apply actions
        for sprite, action in entry_actions:
            action.apply(sprite, tag="formation_entry")
    """
    # Get window bounds (required for this implementation)
    window_bounds = kwargs.get("window_bounds")
    if not window_bounds:
        raise ValueError("window_bounds is required for create_formation_entry_from_sprites")

    # Create new sprites for the entry pattern (same number as target formation)
    sprites = arcade.SpriteList()
    for i in range(len(target_formation)):
        # Create a new sprite with the same texture as the target formation sprite
        target_sprite = target_formation[i]
        if hasattr(target_sprite, "texture") and target_sprite.texture:
            new_sprite = arcade.Sprite(target_sprite.texture, scale=getattr(target_sprite, "scale", 1.0))
        else:
            # Fallback to default star texture
            new_sprite = arcade.Sprite(":resources:images/items/star.png", scale=1.0)
        sprites.append(new_sprite)

    # Generate spawn positions around the upper half of the window boundary
    # Extract target positions from the formation
    spawn_positions = _generate_equally_spaced_spawn_positions(target_formation, window_bounds)
    target_positions = [(sprite.center_x, sprite.center_y) for sprite in target_formation]

    # Pick the nearest spawn position for each target position
    sprite_distances = find_nearest(spawn_positions, target_positions)
    sprite_distances.sort()

    # Get parameters
    speed = kwargs.get("speed", 5.0)
    stagger_delay = kwargs.get("stagger_delay", 1.0)

    # Calculate movement paths for collision detection
    entry_lines = _calculate_sprite_entry_lines(target_formation, spawn_positions, sprite_distances)

    # Group sprites to avoid collisions during movement
    tgt_index = [tgt_index for _, tgt_index, _ in sprite_distances]
    enemy_waves = _group_sprites_to_avoid_collisions(entry_lines, tgt_index)

    entry_actions = []
    max_idx = len(enemy_waves) - 1
    for idx, wave in enumerate(enemy_waves):
        for sprite_idx in wave:
            sprite = target_formation[sprite_idx]
            sprite.center_x, sprite.center_y = spawn_positions[sprite_idx]
            sprite.visible = True
            sprite.alpha = 0
            actions = sequence(
                DelayUntil(duration(stagger_delay * (max_idx - idx))),
                MoveUntil(
                    sprite,
                    _calculate_movement_duration(spawn_positions[sprite_idx], target_positions[sprite_idx], speed),
                ),
            )
            entry_actions.append(sprite, actions)
    return entry_actions


def find_nearest(spawn_positions, target_positions):
    sprite_distances = []
    for i, target_pos in enumerate(target_positions):
        min_dist = 999
        for j, spawn_pos in enumerate(spawn_positions):
            dist = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
            if dist < min_dist:
                min_dist = dist
                tgt_index = i
                spawn_index = j
        sprite_distances.append((min_dist, tgt_index, spawn_index))
    return sprite_distances


def _generate_equally_spaced_spawn_positions(
    target_formation: arcade.SpriteList,
    window_bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    """Generate spawn positions around the upper half of the window boundary.

    Creates spawn positions along:
    - Upper half of left side
    - Top side
    - Upper half of right side

    Args:
        target_positions: List of target formation positions
        window_bounds: (left, bottom, right, top) window boundaries

    Returns:
        List of (x, y) spawn positions
    """
    left, bottom, right, top = window_bounds
    num_sprites = len(target_formation)
    if num_sprites == 0:
        return []

    # Calculate boundary positions
    # Upper half of left side (from center to top)
    left_side_y_start = (bottom + top) / 2
    left_side_y_end = top
    left_side_x = left - 50  # 50 pixels outside window

    # Top side (full width)
    top_side_y = top + 50  # 50 pixels above window
    top_side_x_start = left - 50
    top_side_x_end = right + 50

    # Upper half of right side (from center to top)
    right_side_y_start = (bottom + top) / 2
    right_side_y_end = top
    right_side_x = right + 50  # 50 pixels outside window

    # Calculate how many sprites to place on each boundary section
    # Distribute evenly across the three sections
    sprites_per_section = num_sprites // 3
    spawn_positions = []

    for i in range(sprites_per_section):
        if sprites_per_section > 1:
            t = i / (sprites_per_section - 1)
        else:
            t = 0.5
        left_side_y = left_side_y_start + t * (left_side_y_end - left_side_y_start)
        spawn_positions.append((left_side_x, left_side_y))
        top_side_x = top_side_x_start + t * (top_side_x_end - top_side_x_start)
        spawn_positions.append((top_side_x, top_side_y))
        right_side_y = right_side_y_start + t * (right_side_y_end - right_side_y_start)
        spawn_positions.append((right_side_x, right_side_y))

    return spawn_positions


def _calculate_sprite_entry_lines(
    target_formation: arcade.SpriteList,
    spawn_positions: list[tuple[float, float]],
    sprite_distances: list[float, int, int],
) -> list[
    tuple[
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
        tuple[float, float, float, float],
    ]
]:
    entry_lines = []
    for _, tgt_index, spawn_index in sorted(sprite_distances):
        tgt_width, tgt_height = target_formation[tgt_index].width, target_formation[tgt_index].height
        tgt_cx, tgt_cy = target_formation[tgt_index].center_x, target_formation[tgt_index].center_y
        spawn_cx, spawn_cy = spawn_positions[spawn_index]
        half_width, half_height = tgt_width / 2, tgt_height / 2
        line1 = (tgt_cx - half_width, tgt_cy - half_height, spawn_cx - half_width, spawn_cy - half_height)
        line2 = (tgt_cx - half_width, tgt_cy + half_height, spawn_cx - half_width, spawn_cy + half_height)
        line3 = (tgt_cx + half_width, tgt_cy - half_height, spawn_cx + half_width, spawn_cy - half_height)
        line4 = (tgt_cx + half_width, tgt_cy + half_height, spawn_cx + half_width, spawn_cy + half_height)
        entry_lines.append((line1, line2, line3, line4))
    return entry_lines


def _group_sprites_to_avoid_collisions(
    line_groups: list[
        tuple[
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
        ]
    ],
    tgt_index: tuple[int],
) -> list[list[int]]:
    """Group sprite indices to avoid collisions during movement.

    This function analyzes entry lines and groups sprites so that sprites in the same
    group can move simultaneously without colliding. Only adds delays when necessary.

    Args:
        entry_lines: List of lines for each sprite going from spawn point to target position
        sprite_distances: List of (distance, target_index, spawn_index) tuples

    Returns:
        List of sprite index groups that can move simultaneously
    """
    if not tgt_index:
        return []
    # Check if any entry lines would intersect
    groups = []
    sprites_not_grouped = list(reversed(tgt_index))
    while sprites_not_grouped:
        remaining_sprites = sprites_not_grouped[:]
        sprites_not_grouped = []
        group = []
        line_groups_to_check = []
        while remaining_sprites:
            idx = remaining_sprites.pop()
            for line in line_groups[idx]:
                if _would_lines_collide(line, line_groups_to_check):
                    sprites_not_grouped.append(idx)
                    break
            else:
                # only add the sprite to the group if it doesn't collide with any other sprites
                group.append(idx)
                line_groups_to_check.extend(line_groups[idx])
        groups.append(group)
    return groups


def _would_lines_collide(
    line1: tuple[float, float, float, float],
    lines: list[tuple[float, float, float, float]],
) -> bool:
    """Check if two movement paths would result in sprites getting too close.

    Uses line intersection to detect if movement paths cross, which would cause collisions.

    Args:
        line1: (pt11, pt12, pt13, pt14) for first sprite
        lines: list of (pt21, pt22, pt23, pt24) for other sprites
    Returns:
        True if paths would result in collision, False otherwise
    """
    for line2 in lines:
        if _do_line_segments_intersect(line1, line2):
            return True
    return False


def _do_line_segments_intersect(
    line1: tuple[float, float, float, float],
    line2: tuple[float, float, float, float],
) -> bool:
    """Check if two line segments intersect or come within min_spacing of each other.

    Args:
        line1: (x11, y11, x12, y12)
        line2: (x21, y21, x22, y22)

    Returns:
        True if line segments intersect or come too close
    """

    # First check if the actual lines intersect
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2
    return intersect((x11, y11), (x12, y12), (x21, y21), (x22, y22))
