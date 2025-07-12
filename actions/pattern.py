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

# Boid-based formation entry patterns


class BoidMoveUntil:
    """Move sprites using boid algorithm until a condition is satisfied.

    This action applies classic boid flocking behavior (cohesion, separation, alignment)
    to a sprite list, with optional player avoidance and velocity clamping.

    Args:
        max_speed: Maximum speed in pixels per frame (Arcade velocity semantics)
        duration_condition: Function that returns True when movement should stop
        avoid_sprite: Optional sprite to avoid (e.g., player)
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
        avoid_sprite: arcade.Sprite | None = None,
        cohesion_weight: float = 0.005,
        separation_weight: float = 0.05,
        alignment_weight: float = 0.05,
        avoid_weight: float = 0.02,
        avoid_distance: float = 200.0,
        separation_distance: float = 30.0,
    ):
        self.max_speed = max_speed
        self.condition = duration_condition
        self.avoid_sprite = avoid_sprite
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

            # Avoidance: steer away from avoid_sprite
            if self.avoid_sprite:
                dx = self.avoid_sprite.center_x - sprite.center_x
                dy = self.avoid_sprite.center_y - sprite.center_y
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
        target: tuple[float, float],
        speed: float,
        stop_distance: float = 10.0,
        condition: Callable[[], bool] | None = None,
    ):
        self.target_point = target
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


def create_boid_flock_pattern(
    max_speed: float, duration_seconds: float, avoid_sprite: arcade.Sprite | None = None, **boid_kwargs
) -> BoidMoveUntil:
    """Create a boid flocking pattern for a specified duration.

    Args:
        max_speed: Maximum speed in pixels per frame
        duration_seconds: How long to run the boid behavior
        avoid_sprite: Optional sprite to avoid (e.g., player)
        **boid_kwargs: Additional boid parameters (cohesion_weight, etc.)

    Returns:
        BoidMoveUntil action

    Example:
        flock_pattern = create_boid_flock_pattern(4.0, 3.0, avoid_sprite=player)
        flock_pattern.apply(enemy_sprites, tag="flock_cruise")
    """
    from actions.conditional import duration

    return BoidMoveUntil(
        max_speed=max_speed, duration_condition=duration(duration_seconds), avoid_sprite=avoid_sprite, **boid_kwargs
    )


def create_formation_entry_pattern(
    flock_size: int,
    target_formation: arcade.SpriteList,
    spawn_area: tuple[float, float, float, float],
    cruise_duration: float,
    rally_point: tuple[float, float],
    slot_duration: float,
    avoid_sprite: arcade.Sprite | None = None,
    max_cruise_speed: float = 4.0,
):
    """Create a complete formation entry pattern: cruise -> rally -> slot-in.

    This creates a 3-phase sequence:
    1. Boid cruise phase: Flock behavior while staying away from player
    2. Rally phase: Move toward rally point near formation
    3. Slot-in phase: Individual sprites move to their formation positions

    Args:
        flock_size: Number of sprites in the flock
        target_formation: SpriteList with pre-arranged formation positions
        spawn_area: (left, bottom, right, top) area to spawn from
        cruise_duration: Duration of boid cruise phase in seconds
        rally_point: (x, y) intermediate rally point before formation
        slot_duration: Duration for slotting into formation in seconds
        avoid_sprite: Optional sprite to avoid during cruise (e.g., player)
        max_cruise_speed: Maximum speed during cruise phase

    Returns:
        Sequence action with cruise, rally, and slot-in phases

    Example:
        formation = arrange_grid(count=10, rows=2, cols=5)
        entry = create_formation_entry_pattern(
            flock_size=10,
            target_formation=formation,
            spawn_area=(0, 0, 100, 600),
            cruise_duration=3.0,
            rally_point=(150, 350),
            slot_duration=2.0,
            avoid_sprite=player
        )
        entry.apply(new_sprites, tag="formation_entry")
    """
    from actions.composite import parallel, sequence

    # Phase 1: Boid cruise
    cruise_action = create_boid_flock_pattern(
        max_speed=max_cruise_speed, duration_seconds=cruise_duration, avoid_sprite=avoid_sprite
    )

    # Phase 2: Rally toward formation area
    rally_action = MoveUntilTowardsTarget(
        target=rally_point,
        speed=max_cruise_speed * 0.8,  # Slightly slower for rally
        stop_distance=30.0,
    )

    # Phase 3: Slot into formation positions
    # Note: This creates a parallel action where each sprite moves to its slot
    # The actual sprite-to-slot assignment happens when the action is applied
    slot_actions = []
    formation_positions = [(s.center_x, s.center_y) for s in target_formation[:flock_size]]

    for i, pos in enumerate(formation_positions):
        slot_action = MoveUntilTowardsTarget(
            target=pos,
            speed=3.0,  # Moderate speed for precise positioning
            stop_distance=5.0,
        )
        slot_actions.append(slot_action)

    # If we have more formation slots than flock size, just use what we need
    if len(slot_actions) > flock_size:
        slot_actions = slot_actions[:flock_size]

    slot_in_action = parallel(*slot_actions) if slot_actions else None

    # Combine all phases
    phases = [cruise_action, rally_action]
    if slot_in_action:
        phases.append(slot_in_action)

    return sequence(*phases)


def create_galaga_style_entry(
    formation: arcade.SpriteList,
    groups_per_formation: int = 4,
    sprites_per_group: int = 10,
    player_sprite: arcade.Sprite | None = None,
    screen_bounds: tuple[float, float, float, float] = (0, 0, 800, 600),
    cruise_duration: float = 3.0,
    slot_duration: float = 2.0,
):
    """Create multiple formation entry patterns for Galaga-style enemy arrival.

    This creates multiple groups that enter from different sides of the screen,
    each following the cruise -> rally -> slot-in pattern.

    Args:
        formation: Target formation with all positions arranged
        groups_per_formation: Number of groups to create (default: 4)
        sprites_per_group: Sprites per group (default: 10)
        player_sprite: Player sprite to avoid during cruise
        screen_bounds: (left, bottom, right, top) screen boundaries
        cruise_duration: Duration of cruise phase per group
        slot_duration: Duration of slot-in phase per group

    Returns:
        List of sequence actions, one per group

    Example:
        formation = arrange_grid(count=40, rows=4, cols=10)
        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=4,
            sprites_per_group=10,
            player_sprite=player
        )

        # Apply each group with a delay
        for i, action in enumerate(entry_actions):
            delay = DelayUntil(duration(i * 1.5))  # Stagger entries
            sequence(delay, action).apply(group_sprites[i], tag=f"group_{i}")
    """
    left, bottom, right, top = screen_bounds
    margin = 50  # Distance outside screen bounds

    # Define spawn areas for different sides
    spawn_areas = [
        (left - margin, bottom, left, top),  # Left side
        (right, bottom, right + margin, top),  # Right side
        (left, top, right, top + margin),  # Top side
        (left, bottom - margin, right, bottom),  # Bottom side (less common)
    ]

    # Calculate formation center for rally points
    if formation:
        form_center_x = sum(s.center_x for s in formation) / len(formation)
        form_center_y = sum(s.center_y for s in formation) / len(formation)
    else:
        form_center_x = (left + right) / 2
        form_center_y = (bottom + top) / 2

    entry_actions = []

    for group_index in range(groups_per_formation):
        # Select spawn area (cycle through available sides)
        spawn_area = spawn_areas[group_index % len(spawn_areas)]

        # Calculate rally point based on spawn side
        if group_index % 4 == 0:  # Left spawn
            rally_point = (form_center_x - 100, form_center_y + 50)
        elif group_index % 4 == 1:  # Right spawn
            rally_point = (form_center_x + 100, form_center_y + 50)
        elif group_index % 4 == 2:  # Top spawn
            rally_point = (form_center_x, form_center_y + 100)
        else:  # Bottom spawn
            rally_point = (form_center_x, form_center_y - 100)

        # Calculate which part of formation this group will fill
        start_index = group_index * sprites_per_group
        end_index = min(start_index + sprites_per_group, len(formation))
        group_formation = arcade.SpriteList()

        for i in range(start_index, end_index):
            if i < len(formation):
                group_formation.append(formation[i])

        # Create formation entry pattern for this group
        if group_formation:
            entry_pattern = create_formation_entry_pattern(
                flock_size=len(group_formation),
                target_formation=group_formation,
                spawn_area=spawn_area,
                cruise_duration=cruise_duration,
                rally_point=rally_point,
                slot_duration=slot_duration,
                avoid_sprite=player_sprite,
                max_cruise_speed=4.0 + random.uniform(-1.0, 1.0),  # Slight speed variation
            )
            entry_actions.append(entry_pattern)

    return entry_actions


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
    return Ease(zigzag, duration=ease_duration, ease_function=easing.ease_in_out)


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
#     flock_size=8,
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
