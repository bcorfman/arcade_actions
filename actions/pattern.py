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

from actions import Ease, FollowPathUntil, MoveUntil, duration, sequence

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


class MoveUntilTowardsTarget:
    """Move sprites toward a target point until reaching it or condition is met.

    Args:
        target: (x, y) target position
        speed: Movement speed in pixels per frame
        stop_distance: Distance at which to stop (default: 10.0)
        condition: Optional additional stop condition
    """

    def __init__(
        self,
        target_position: tuple[float, float],
        speed: float,
        stop_distance: float = 10.0,
        condition: Callable[[], bool] | None = None,
    ):
        self.target_point = target_position
        self.speed = speed
        self.stop_distance = stop_distance
        self.additional_condition = condition

        # Action state
        self.target = None
        self.tag = None
        self.done = False
        self._is_active = False

    def apply(self, target: arcade.Sprite | arcade.SpriteList, tag: str | None = None):
        """Apply this action to a sprite or sprite list."""
        self.target = target
        self.tag = tag
        self._is_active = True
        # Add to global action manager
        from actions.base import Action

        Action._active_actions.append(self)
        return self

    def start(self):
        """Start the action."""
        self._is_active = True

    def stop(self) -> None:
        """Stop the action and clean up."""
        self.done = True
        self._is_active = False
        if self.target:
            # Stop all sprites
            if isinstance(self.target, arcade.SpriteList):
                for sprite in self.target:
                    sprite.change_x = 0
                    sprite.change_y = 0
            else:
                self.target.change_x = 0
                self.target.change_y = 0
        # Remove from global action manager
        from actions.base import Action

        if self in Action._active_actions:
            Action._active_actions.remove(self)

    def update(self, delta_time: float) -> None:
        """Update movement toward target."""
        if not self._is_active or self.done or not self.target:
            return

        # Check additional condition
        if self.additional_condition and self.additional_condition():
            self.stop()
            return

        def update_sprite(sprite):
            # Calculate distance to target
            dx = self.target_point[0] - sprite.center_x
            dy = self.target_point[1] - sprite.center_y
            distance = math.sqrt(dx * dx + dy * dy)

            # Check if close enough to stop
            if distance <= self.stop_distance:
                sprite.change_x = 0
                sprite.change_y = 0
                return True  # Signal that this sprite has reached target

            # Calculate velocity toward target
            if distance > 0:
                sprite.change_x = (dx / distance) * self.speed
                sprite.change_y = (dy / distance) * self.speed

            return False

        # Apply to all sprites and check if all have reached target
        all_reached = True
        if isinstance(self.target, arcade.SpriteList):
            for sprite in self.target:
                if not update_sprite(sprite):
                    all_reached = False
        else:
            all_reached = update_sprite(self.target)

        if all_reached:
            self.stop()


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


# Usage examples and notes:
#
# # Create Galaga-style formation entry:
# from actions.formation import arrange_grid
# formation = arrange_grid(rows=4, cols=10, start_x=200, start_y=400)
# entry_actions = create_galaga_style_entry(
#     formation=formation,
#     groups_per_formation=4,
#     sprites_per_group=10,
#     player_sprite=player
# )
#
# # Apply each group with staggered timing:
# for i, action in enumerate(entry_actions):
#     delay = DelayUntil(duration(i * 1.5))
#     sequence(delay, action).apply(group_sprites[i], tag=f"group_{i}_entry")
#
# # Custom formation entry for specific scenarios:
# custom_entry = create_formation_entry_pattern(
#     target_formation=circular_formation,
#     spawn_area=(0, 0, 100, 600),  # Left side spawn
#     cruise_duration=3.0,
#     rally_point=(150, 350),
#     slot_duration=2.0,
#     avoid_sprite=player
# )
# custom_entry.apply(new_enemy_group, tag="custom_formation_entry")
#
# # Individual boid flocking:
# flock_behavior = create_boid_flock_pattern(
#     max_speed=4.0,
#     duration_seconds=5.0,
#     avoid_sprite=player,
#     cohesion_weight=0.01,
#     separation_weight=0.08
# )
# flock_behavior.apply(wandering_enemies, tag="free_roam")


def create_formation_entry_pattern(
    target_positions: list[tuple[float, float]],
    *,
    spawn_radius: float = 800.0,
    spawn_center: tuple[float, float] = (400, 300),
    spawn_angle_range: tuple[float, float] = (0, math.pi),  # Semicircle
    speed: float = 200.0,
    stagger_delay: float = 0.2,
    min_spacing: float = 30.0,
    window_bounds: tuple[float, float, float, float] | None = None,
) -> list[tuple[arcade.Sprite, arcade.SpriteList]]:
    """Create a formation entry pattern that moves sprites from spawn to target positions.

    This function creates a sequence of MoveUntil actions that move sprites from
    semicircle spawn positions outside the window to their target formation positions.
    Sprites are moved in waves to avoid overlaps, with innermost sprites moving first.

    Args:
        target_positions: List of (x, y) target positions for each sprite
        spawn_radius: Distance from spawn center to place sprites (default: 800.0)
        spawn_center: (x, y) center point for spawn semicircle (default: (400, 300))
        spawn_angle_range: (start_angle, end_angle) in radians for spawn arc (default: (0, π))
        speed: Movement speed in pixels per frame (Arcade velocity semantics)
        stagger_delay: Delay between sprite movement waves in seconds (default: 0.2)
        min_spacing: Minimum spacing between sprites during movement (default: 30.0)
        window_bounds: (left, bottom, right, top) window bounds for spawn positioning

    Returns:
        List of (sprite, action) tuples for each sprite's movement

    Example:
        # Create a circle formation
        circle_formation = arrange_circle(count=8, center_x=400, center_y=300, radius=100)
        target_positions = [(sprite.center_x, sprite.center_y) for sprite in circle_formation]

        # Create entry pattern
        entry_actions = create_formation_entry_pattern(
            target_positions=target_positions,
            speed=150.0,
            stagger_delay=0.3
        )

        # Apply to sprites
        for sprite, action in entry_actions:
            action.apply(sprite, tag="formation_entry")
    """
    if not target_positions:
        return []

    # Calculate spawn positions along semicircle
    spawn_positions = _generate_semicircle_spawn_positions(
        target_positions,
        spawn_radius=spawn_radius,
        spawn_center=spawn_center,
        spawn_angle_range=spawn_angle_range,
        window_bounds=window_bounds,
    )

    # Group sprites by distance from formation center for wave entry (innermost first)
    formation_center = _calculate_formation_center(target_positions)
    wave_groups = _group_sprites_by_distance_waves(target_positions, formation_center, spawn_radius)

    speed = kwargs.get("speed", 10.0)
    base_stagger_delay = kwargs.get("stagger_delay", 0.3)

    final_actions = []
    current_delay = 0.0

    print(f"Formation entry: {len(wave_groups)} waves, center at {formation_center}")

    # Process each wave (innermost to outermost)
    for wave_index, sprite_indices in enumerate(wave_groups):
        print(f"Wave {wave_index}: {len(sprite_indices)} sprites, delay={current_delay:.1f}s")

        for sprite_idx in sprite_indices:
            if sprite_idx >= len(sprites) or sprite_idx >= len(spawn_positions):
                continue

            sprite = sprites[sprite_idx]
            target_pos = target_positions[sprite_idx]
            spawn_pos = spawn_positions[sprite_idx]

            # Position sprite at spawn location
            sprite.center_x, sprite.center_y = spawn_pos

            # Create precision movement action that stops exactly at target
            def create_precision_condition_and_callback(target_position, sprite_ref):
                def precision_condition():
                    # Calculate distance to target
                    dx = target_position[0] - sprite_ref.center_x
                    dy = target_position[1] - sprite_ref.center_y
                    distance = math.sqrt(dx * dx + dy * dy)

                    # If very close, position exactly and stop
                    if distance <= 2.0:  # Within 2 pixels
                        sprite_ref.center_x = target_position[0]
                        sprite_ref.center_y = target_position[1]
                        sprite_ref.change_x = 0
                        sprite_ref.change_y = 0
                        return True

                    # If close, slow down proportionally to prevent overshoot
                    elif distance <= 20.0:  # Within 20 pixels, start slowing
                        current_speed = math.sqrt(sprite_ref.change_x**2 + sprite_ref.change_y**2)
                        if current_speed > 0:
                            # Scale velocity by distance ratio (closer = slower)
                            scale_factor = max(0.1, distance / 20.0)  # Minimum 10% speed
                            direction_x = dx / distance
                            direction_y = dy / distance
                            # Set new velocity directly
                            sprite_ref.change_x = direction_x * current_speed * scale_factor
                            sprite_ref.change_y = direction_y * current_speed * scale_factor

                    return False  # Continue moving

                return precision_condition

            # Create movement action with wave-based delay
            velocity = _calculate_velocity_to_target(spawn_pos, target_pos, speed)

            if current_delay > 0.01:  # Add delay for waves after the first
                from actions.composite import sequence
                from actions.conditional import DelayUntil

                delay_action = DelayUntil(duration(current_delay))
                movement_action = MoveUntil(velocity, create_precision_condition_and_callback(target_pos, sprite))
                combined_action = sequence(delay_action, movement_action)
            else:
                movement_action = MoveUntil(velocity, create_precision_condition_and_callback(target_pos, sprite))
                combined_action = movement_action

            final_actions.append((sprite, combined_action))

        # Add stagger delay for next wave (ensure previous wave has time to clear paths)
        # Longer delay for waves that are likely to intersect with the next wave
        wave_delay = base_stagger_delay * (2.0 if len(sprite_indices) > 4 else 1.5)
        current_delay += wave_delay

    return final_actions


def _generate_semicircle_spawn_positions(
    target_positions: list[tuple[float, float]],
    spawn_radius: float,
    spawn_center: tuple[float, float],
    spawn_angle_range: tuple[float, float],
    window_bounds: tuple[float, float, float, float] | None = None,
) -> list[tuple[float, float]]:
    """Generate spawn positions along a semicircle outside the window.

    Args:
        target_positions: List of target positions
        spawn_radius: Distance from spawn center
        spawn_center: (x, y) center of spawn semicircle (will be overridden by formation center)
        spawn_angle_range: (start_angle, end_angle) in radians
        window_bounds: Optional window bounds for positioning

    Returns:
        List of (x, y) spawn positions
    """
    num_sprites = len(target_positions)
    if num_sprites == 0:
        return []

    # Always use the formation center as the spawn center
    formation_center = _calculate_formation_center(target_positions)

    # Adjust spawn radius if window bounds are provided
    if window_bounds:
        left, bottom, right, top = window_bounds
        # Ensure spawn radius is outside window
        window_diagonal = math.sqrt((right - left) ** 2 + (top - bottom) ** 2)
        spawn_radius = max(spawn_radius, window_diagonal * 0.6)

    # Use shared helper function to calculate spawn points
    return _calculate_spawn_points_from_formation(target_positions, formation_center, spawn_radius)


def _calculate_spawn_points_from_formation(
    target_positions: list[tuple[float, float]],
    formation_center: tuple[float, float],
    spawn_radius: float,
) -> list[tuple[float, float]]:
    """Calculate spawn points by projecting from formation center through target positions to spawn radius.

    Args:
        target_positions: List of (x, y) formation positions
        formation_center: (x, y) center of formation and semicircle
        spawn_radius: Radius from formation center to semicircle for spawn points

    Returns:
        List of (x, y) spawn positions
    """
    import math

    center_x, center_y = formation_center
    spawn_points = []

    for x, y in target_positions:
        dx = x - center_x
        dy = y - center_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            # If sprite is at the center, spawn directly to the right
            spawn_x = center_x + spawn_radius
            spawn_y = center_y
        else:
            scale = spawn_radius / dist
            spawn_x = center_x + dx * scale
            spawn_y = center_y + dy * scale
        spawn_points.append((spawn_x, spawn_y))

    return spawn_points


def _calculate_formation_center(positions: list[tuple[float, float]]) -> tuple[float, float]:
    """Calculate the center point of a formation.

    Args:
        positions: List of (x, y) positions

    Returns:
        (x, y) center point
    """
    if not positions:
        return (0, 0)

    total_x = sum(x for x, y in positions)
    total_y = sum(y for x, y in positions)
    count = len(positions)

    return (total_x / count, total_y / count)


def _group_sprites_by_distance_waves(
    target_positions: list[tuple[float, float]],
    formation_center: tuple[float, float],
    spawn_radius: float,
) -> list[list[int]]:
    """Group sprite indices into waves for collision-free entry from outermost to innermost.

    Each wave contains all sprites whose straight-line path from formation position to spawn point
    (on a semicircle of given radius from the formation center) does not intersect any other remaining sprite's path.
    Remove assigned sprites and repeat until all are assigned. Any intersection is a collision.

    Args:
        target_positions: List of (x, y) formation positions
        formation_center: (x, y) center of formation and semicircle
        spawn_radius: Radius from formation center to semicircle for spawn points

    Returns:
        List of sprite index groups, outermost wave first
    """

    num_sprites = len(target_positions)
    if num_sprites == 0:
        return []

    # Use shared helper function to compute spawn points
    spawn_points = _calculate_spawn_points_from_formation(target_positions, formation_center, spawn_radius)

    # Helper: check if two line segments intersect
    def lines_intersect(p1, q1, p2, q2):
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        return ccw(p1, p2, q2) != ccw(q1, p2, q2) and ccw(p1, q1, p2) != ccw(p1, q1, q2)

    remaining = set(range(num_sprites))
    waves = []

    while remaining:
        current_wave = []
        for idx in list(remaining):
            p1 = target_positions[idx]
            q1 = spawn_points[idx]
            collision = False
            for other_idx in remaining:
                if other_idx == idx:
                    continue
                p2 = target_positions[other_idx]
                q2 = spawn_points[other_idx]
                if lines_intersect(p1, q1, p2, q2):
                    collision = True
                    break
            if not collision:
                current_wave.append(idx)
        if not current_wave:
            # If all remaining paths collide, assign one per wave to break deadlock
            current_wave.append(next(iter(remaining)))
        for idx in current_wave:
            remaining.remove(idx)
        waves.append(current_wave)

    return waves


def _calculate_velocity_to_target(
    start_pos: tuple[float, float],
    target_pos: tuple[float, float],
    speed: float,
) -> tuple[float, float]:
    """Calculate velocity vector from start to target position.

    Args:
        start_pos: (x, y) starting position
        target_pos: (x, y) target position
        speed: Movement speed in pixels per frame

    Returns:
        (dx, dy) velocity vector
    """
    dx = target_pos[0] - start_pos[0]
    dy = target_pos[1] - start_pos[1]
    distance = math.sqrt(dx * dx + dy * dy)

    if distance == 0:
        return (0, 0)

    # Normalize and scale to speed
    dx = (dx / distance) * speed
    dy = (dy / distance) * speed

    return (dx, dy)


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

    This is a convenience function that creates sprites positioned at spawn locations
    and creates movement actions to move them to the target formation positions.

    Args:
        target_formation: SpriteList with sprites positioned at target formation locations
        **kwargs: Additional arguments for create_formation_entry_pattern

    Returns:
        List of (sprite, action) tuples

    Example:
        # Create target formation (e.g., circle formation)
        target_formation = arrange_circle(count=8, center_x=400, center_y=300, radius=100, visible=False)

        # Create entry pattern
        entry_actions = create_formation_entry_from_sprites(
            target_formation, speed=150.0, stagger_delay=0.3
        )

        # Apply actions
        for sprite, action in entry_actions:
            action.apply(sprite, tag="formation_entry")
    """
    # Extract target positions from the formation
    target_positions = [(sprite.center_x, sprite.center_y) for sprite in target_formation]

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

    # Position sprites at spawn locations and create final actions
    spawn_positions = _generate_semicircle_spawn_positions(
        target_positions,
        spawn_radius=kwargs.get("spawn_radius", 800.0),
        spawn_center=kwargs.get("spawn_center", (400, 300)),
        spawn_angle_range=kwargs.get("spawn_angle_range", (0, math.pi)),
        window_bounds=kwargs.get("window_bounds"),
    )

    speed = kwargs.get("speed", 10.0)
    stagger_delay = kwargs.get("stagger_delay", 0.3)
    min_spacing = kwargs.get("min_spacing", 30.0)

    # Calculate movement paths and detect potential collisions using line intersection
    movement_paths = []
    for i in range(len(sprites)):
        if i < len(spawn_positions):
            spawn_pos = spawn_positions[i]
            target_pos = target_positions[i]
            velocity = _calculate_velocity_to_target(spawn_pos, target_pos, speed)
            movement_paths.append((i, spawn_pos, target_pos, velocity))

    # Group sprites to avoid collisions during movement
    collision_groups = _group_sprites_to_avoid_collisions(movement_paths, min_spacing)

    final_actions = []
    current_delay = 0.0

    print(f"Formation entry: {len(collision_groups)} groups to avoid path collisions")

    # Process each collision-avoidance group
    for group_index, sprite_indices in enumerate(collision_groups):
        print(f"Group {group_index}: {len(sprite_indices)} sprites, delay={current_delay:.1f}s")

        for sprite_idx in sprite_indices:
            if sprite_idx >= len(sprites) or sprite_idx >= len(spawn_positions):
                continue

            sprite = sprites[sprite_idx]
            target_pos = target_positions[sprite_idx]
            spawn_pos = spawn_positions[sprite_idx]

            # Position sprite at spawn location
            sprite.center_x, sprite.center_y = spawn_pos

            # Create precision movement action that stops exactly at target
            def create_precision_condition_and_callback(target_position, sprite_ref):
                def precision_condition():
                    # Calculate distance to target
                    dx = target_position[0] - sprite_ref.center_x
                    dy = target_position[1] - sprite_ref.center_y
                    distance = math.sqrt(dx * dx + dy * dy)

                    # If very close, position exactly and stop
                    if distance <= 2.0:  # Within 2 pixels
                        sprite_ref.center_x = target_position[0]
                        sprite_ref.center_y = target_position[1]
                        sprite_ref.change_x = 0
                        sprite_ref.change_y = 0
                        return True

                    # If close, slow down proportionally to prevent overshoot
                    elif distance <= 20.0:  # Within 20 pixels, start slowing
                        current_speed = math.sqrt(sprite_ref.change_x**2 + sprite_ref.change_y**2)
                        if current_speed > 0:
                            # Scale velocity by distance ratio (closer = slower)
                            scale_factor = max(0.1, distance / 20.0)  # Minimum 10% speed
                            direction_x = dx / distance
                            direction_y = dy / distance
                            # Set new velocity directly
                            sprite_ref.change_x = direction_x * current_speed * scale_factor
                            sprite_ref.change_y = direction_y * current_speed * scale_factor

                    return False  # Continue moving

                return precision_condition

            # Create movement action with wave-based delay
            velocity = _calculate_velocity_to_target(spawn_pos, target_pos, speed)

            if current_delay > 0.01:  # Add delay for waves after the first
                from actions.composite import sequence
                from actions.conditional import DelayUntil

                delay_action = DelayUntil(duration(current_delay))
                movement_action = MoveUntil(velocity, create_precision_condition_and_callback(target_pos, sprite))
                combined_action = sequence(delay_action, movement_action)
            else:
                movement_action = MoveUntil(velocity, create_precision_condition_and_callback(target_pos, sprite))
                combined_action = movement_action

            final_actions.append((sprite, combined_action))

        # Add delay only if this group would collide with the next group
        if group_index < len(collision_groups) - 1:
            current_delay += stagger_delay

    return final_actions


def _group_sprites_to_avoid_collisions(
    movement_paths: list[tuple[int, tuple[float, float], tuple[float, float], tuple[float, float]]],
    min_spacing: float,
) -> list[list[int]]:
    """Group sprite indices to avoid collisions during movement.

    This function analyzes movement paths and groups sprites so that sprites in the same
    group can move simultaneously without colliding. Only adds delays when necessary.

    Args:
        movement_paths: List of (sprite_idx, spawn_pos, target_pos, velocity) tuples
        min_spacing: Minimum spacing to maintain between sprites during movement

    Returns:
        List of sprite index groups that can move simultaneously
    """
    if not movement_paths:
        return []

    # For simple formations like circles where all sprites move radially outward from spawn,
    # they typically won't collide with each other, so they can all move at once

    # Check if any movement paths would intersect
    groups = []
    remaining_sprites = list(range(len(movement_paths)))

    while remaining_sprites:
        current_group = [remaining_sprites[0]]
        remaining_sprites.remove(remaining_sprites[0])

        # Try to add more sprites to the current group
        sprites_to_remove = []
        for sprite_idx in remaining_sprites:
            can_add_to_group = True

            # Check if this sprite would collide with any sprite already in the group
            for group_sprite_idx in current_group:
                if _would_paths_collide(movement_paths[sprite_idx], movement_paths[group_sprite_idx], min_spacing):
                    can_add_to_group = False
                    break

            if can_add_to_group:
                current_group.append(sprite_idx)
                sprites_to_remove.append(sprite_idx)

        # Remove sprites that were added to the group
        for sprite_idx in sprites_to_remove:
            remaining_sprites.remove(sprite_idx)

        groups.append(current_group)

    return groups


def _would_paths_collide(
    path1: tuple[int, tuple[float, float], tuple[float, float], tuple[float, float]],
    path2: tuple[int, tuple[float, float], tuple[float, float], tuple[float, float]],
    min_spacing: float,
) -> bool:
    """Check if two movement paths would result in sprites getting too close.

    Uses line intersection to detect if movement paths cross, which would cause collisions.

    Args:
        path1: (sprite_idx, spawn_pos, target_pos, velocity) for first sprite
        path2: (sprite_idx, spawn_pos, target_pos, velocity) for second sprite
        min_spacing: Minimum spacing to maintain between sprites

    Returns:
        True if paths would result in collision, False otherwise
    """
    _, spawn1, target1, _ = path1
    _, spawn2, target2, _ = path2

    # Check if the straight-line paths from spawn to target intersect
    return _do_line_segments_intersect(spawn1, target1, spawn2, target2, min_spacing)


def _do_line_segments_intersect(
    p1: tuple[float, float],
    q1: tuple[float, float],
    p2: tuple[float, float],
    q2: tuple[float, float],
    min_spacing: float,
) -> bool:
    """Check if two line segments intersect or come within min_spacing of each other.

    Args:
        p1, q1: Start and end points of first line segment (spawn to target)
        p2, q2: Start and end points of second line segment (spawn to target)
        min_spacing: Minimum distance to maintain between paths

    Returns:
        True if line segments intersect or come too close
    """

    # First check if the actual lines intersect
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    if intersect(p1, q1, p2, q2):
        return True

    # Check if any point on one line segment is too close to the other line segment
    def point_to_line_distance(point, line_start, line_end):
        """Calculate shortest distance from point to line segment."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        # Vector from line_start to line_end
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # Line segment is actually a point
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        # Parameter t represents position along line segment (0 to 1)
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)))

        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.sqrt((x0 - closest_x) ** 2 + (y0 - closest_y) ** 2)

    # Sample points along each path and check distances
    num_samples = 20  # More samples for better collision detection
    for i in range(num_samples + 1):
        t = i / num_samples

        # Point on first path
        sample1 = (p1[0] + t * (q1[0] - p1[0]), p1[1] + t * (q1[1] - p1[1]))

        # Check distance to second path
        if point_to_line_distance(sample1, p2, q2) < min_spacing:
            return True

        # Point on second path
        sample2 = (p2[0] + t * (q2[0] - p2[0]), p2[1] + t * (q2[1] - p2[1]))

        # Check distance to first path
        if point_to_line_distance(sample2, p1, q1) < min_spacing:
            return True

    return False
