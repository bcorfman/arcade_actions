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


def create_formation_entry_pattern(
    formation_sprites: arcade.SpriteList,
    spawn_area: tuple[float, float, float, float],
    cruise_duration: float,
    rally_point: tuple[float, float],
    slot_duration: float,
    avoid_sprites: arcade.SpriteList | None = None,
    max_cruise_speed: float = 4.0,
    visible: bool = True,
    spawn_spacing: float = 40.0,
):
    """Create a complete formation entry pattern: cruise -> rally -> slot-in.

    This creates a 3-phase sequence:
    1. Boid cruise phase: Flock behavior while staying away from player
    2. Rally phase: Move toward rally point near formation
    3. Slot-in phase: Individual sprites move to their formation positions

    Args:
        formation_sprites: SpriteList with sprites that will move through the pattern
        spawn_area: (left, bottom, right, top) area to spawn from
        cruise_duration: Duration of boid cruise phase in seconds
        rally_point: (x, y) intermediate rally point before formation
        slot_duration: Duration for slotting into formation in seconds
        avoid_sprites: SpriteList of sprites to avoid during cruise (e.g., player, obstacles)
        max_cruise_speed: Maximum speed during cruise phase
        visible: Whether sprites should be made visible when spawning (default: True)
        spawn_spacing: Minimum distance between sprites when spawning (default: 40.0)

    Returns:
        Sequence action with cruise, rally, and slot-in phases

    Example:
        formation = arrange_grid(rows=2, cols=5, start_x=200, start_y=400, visible=False)
        entry = create_formation_entry_pattern(
            formation_sprites=formation,
            spawn_area=(0, 0, 100, 600),
            cruise_duration=3.0,
            rally_point=(150, 350),
            slot_duration=2.0,
            avoid_sprites=player_sprites,
            visible=True
        )
        entry.apply(formation, tag="formation_entry")
    """
    from actions.composite import sequence

    # Store original positions (where sprites should end up)
    target_positions = [(s.center_x, s.center_y) for s in formation_sprites]

    # Create a custom action that positions sprites in spawn area before starting phases
    class SpawnPositioner:
        """Custom action to position sprites in spawn area at the start."""

        def __init__(self, spawn_area, visible, spawn_spacing):
            self.spawn_area = spawn_area
            self.visible = visible
            self.spawn_spacing = spawn_spacing
            self.target = None
            self.tag = None
            self.done = False
            self._is_active = False

        def apply(self, target, tag=None):
            self.target = target
            self.tag = tag
            self._is_active = True
            return self

        def start(self):
            """Start the action by positioning sprites immediately."""
            self._is_active = True
            # Position sprites immediately with adaptive spacing
            if isinstance(self.target, arcade.SpriteList):
                num_sprites = len(self.target)
                if num_sprites > 0:
                    # Calculate adaptive spacing based on sprite sizes
                    adaptive_spacing = _calculate_adaptive_spacing(self.target, self.spawn_spacing)
                    spawn_points = _generate_spaced_spawn_points(
                        self.spawn_area, num_sprites, min_spacing=adaptive_spacing
                    )
                    for i, sprite in enumerate(self.target):
                        if i < len(spawn_points):
                            x, y = spawn_points[i]
                            sprite.center_x = x
                            sprite.center_y = y
                            sprite.visible = self.visible  # Set visibility when spawning
                        else:
                            # Fallback to random positioning if we don't have enough spawn points
                            x, y = _generate_random_spawn_point(self.spawn_area)
                            sprite.center_x = x
                            sprite.center_y = y
                            sprite.visible = self.visible
            elif isinstance(self.target, list):
                # Handle case where target is a list of sprites
                num_sprites = len(self.target)
                if num_sprites > 0:
                    # Convert list to SpriteList for adaptive spacing calculation
                    temp_sprite_list = arcade.SpriteList()
                    for sprite in self.target:
                        temp_sprite_list.append(sprite)
                    adaptive_spacing = _calculate_adaptive_spacing(temp_sprite_list, self.spawn_spacing)
                    spawn_points = _generate_spaced_spawn_points(
                        self.spawn_area, num_sprites, min_spacing=adaptive_spacing
                    )
                    for i, sprite in enumerate(self.target):
                        if i < len(spawn_points):
                            x, y = spawn_points[i]
                            sprite.center_x = x
                            sprite.center_y = y
                            sprite.visible = self.visible  # Set visibility when spawning
                        else:
                            # Fallback to random positioning if we don't have enough spawn points
                            x, y = _generate_random_spawn_point(self.spawn_area)
                            sprite.center_x = x
                            sprite.center_y = y
                            sprite.visible = self.visible
            else:
                # Handle single sprite case
                x, y = _generate_random_spawn_point(self.spawn_area)
                self.target.center_x = x
                self.target.center_y = y
                self.target.visible = self.visible
            self.done = True

        def stop(self):
            self.done = True
            self._is_active = False

        def update(self, delta_time):
            pass  # No update needed, positioning is immediate

    # Create a custom action for slotting into formation positions
    class SlotIntoFormation:
        """Custom action to move sprites to their formation positions."""

        def __init__(self, target_positions, slot_duration, rally_point):
            self.target_positions = target_positions
            self.slot_duration = slot_duration
            self.rally_point = rally_point
            self.target = None
            self.tag = None
            self.done = False
            self._is_active = False
            self.start_time = None

        def apply(self, target, tag=None):
            self.target = target
            self.tag = tag
            self._is_active = True
            return self

        def start(self):
            """Start the slot-in action."""
            import time

            self.start_time = time.time()

        def stop(self):
            self.done = True
            self._is_active = False

        def update(self, delta_time):
            if not self._is_active or self.done or not self.target:
                return

            import time

            elapsed = time.time() - self.start_time
            progress = min(elapsed / self.slot_duration, 1.0)

            # Move each sprite to its target position
            if isinstance(self.target, arcade.SpriteList):
                for i, sprite in enumerate(self.target):
                    if i < len(self.target_positions):
                        target_x, target_y = self.target_positions[i]

                        # Calculate current position (from rally point to target)
                        current_x = self.rally_point[0] + (target_x - self.rally_point[0]) * progress
                        current_y = self.rally_point[1] + (target_y - self.rally_point[1]) * progress

                        sprite.center_x = current_x
                        sprite.center_y = current_y
            elif isinstance(self.target, list):
                # Handle case where target is a list of sprites
                for i, sprite in enumerate(self.target):
                    if i < len(self.target_positions):
                        target_x, target_y = self.target_positions[i]

                        # Calculate current position (from rally point to target)
                        current_x = self.rally_point[0] + (target_x - self.rally_point[0]) * progress
                        current_y = self.rally_point[1] + (target_y - self.rally_point[1]) * progress

                        sprite.center_x = current_x
                        sprite.center_y = current_y
            else:
                # Handle single sprite case
                if len(self.target_positions) > 0:
                    target_x, target_y = self.target_positions[0]

                    # Calculate current position (from rally point to target)
                    current_x = self.rally_point[0] + (target_x - self.rally_point[0]) * progress
                    current_y = self.rally_point[1] + (target_y - self.rally_point[1]) * progress

                    self.target.center_x = current_x
                    self.target.center_y = current_y

            if progress >= 1.0:
                self.done = True

    # Phase 0: Position sprites in spawn area
    spawn_positioner = SpawnPositioner(spawn_area, visible, spawn_spacing)

    # Phase 1: Boid cruise with adaptive separation for better spacing
    # Calculate adaptive separation distance based on sprite sizes
    adaptive_separation = _calculate_adaptive_spacing(formation_sprites, 50.0)
    cruise_action = create_boid_flock_pattern(
        max_speed=max_cruise_speed,
        duration_seconds=cruise_duration,
        avoid_sprites=avoid_sprites,
        separation_weight=0.08,  # Increased separation weight
        separation_distance=adaptive_separation,  # Adaptive separation distance
        cohesion_weight=0.003,  # Reduced cohesion for more spread
    )

    # Phase 2: Rally toward formation area
    rally_action = MoveUntilTowardsTarget(
        target_position=rally_point,
        speed=max_cruise_speed * 0.8,  # Slightly slower for rally
        stop_distance=30.0,
    )

    # Phase 3: Slot into formation positions
    slot_action = SlotIntoFormation(target_positions, slot_duration, rally_point)

    # Combine all phases
    phases = [spawn_positioner, cruise_action, rally_action, slot_action]

    return sequence(*phases)


def create_formation_entry_with_boid_cruise(
    formation: arcade.SpriteList,
    groups_per_formation: int = 4,
    sprites_per_group: int = 10,
    player_sprite: arcade.Sprite | None = None,
    screen_bounds: tuple[float, float, float, float] = (0, 0, 800, 600),
    cruise_duration: float = 3.0,
    slot_duration: float = 2.0,
    max_cruise_speed: float = 12.0,
    spawn_areas: dict[str, bool] | None = None,
):
    """Create multiple formation entry patterns with boid cruise behavior.

    This creates multiple groups that enter from different sides of the screen,
    each following the cruise -> rally -> slot-in pattern using boid flocking.

    Args:
        formation: Target formation with all positions arranged
        groups_per_formation: Number of groups to create (default: 4)
        sprites_per_group: Sprites per group (default: 10)
        player_sprite: Player sprite to avoid during cruise
        screen_bounds: (left, bottom, right, top) screen boundaries
        cruise_duration: Duration of cruise phase per group
        slot_duration: Duration of slot-in phase per group
        max_cruise_speed: Maximum speed during cruise phase in pixels per frame
        spawn_areas: Dict to enable/disable spawn areas. Keys: "left", "right", "top", "bottom".
                    Values: True to enable, False to disable. Default: all areas enabled.

    Returns:
        List of sequence actions, one per group

    Example:
        formation = arrange_grid(count=40, rows=4, cols=10)
        entry_actions = create_formation_entry_with_boid_cruise(
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
    margin = 200  # Distance outside screen bounds

    # Define all possible spawn areas for different sides
    all_spawn_areas = [
        (left - margin, bottom, left, top),  # Left side
        (right, bottom, right + margin, top),  # Right side
        (left, top, right, top + margin),  # Top side
        (left, bottom - margin, right, bottom),  # Bottom side (less common)
    ]

    # Filter spawn areas based on spawn_areas parameter
    if spawn_areas is not None:
        area_names = ["left", "right", "top", "bottom"]
        filtered_spawn_areas = []
        for i, (area_name, area_coords) in enumerate(zip(area_names, all_spawn_areas, strict=False)):
            if spawn_areas.get(area_name, True):  # Default to True if not specified
                filtered_spawn_areas.append(area_coords)
        spawn_areas = filtered_spawn_areas
    else:
        spawn_areas = all_spawn_areas

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

        # Determine which spawn side this corresponds to for rally point calculation
        spawn_side_index = group_index % len(spawn_areas)

        # Calculate rally point based on spawn side
        if spawn_side_index == 0:  # Left spawn
            rally_point = (form_center_x - 100, form_center_y + 50)
        elif spawn_side_index == 1:  # Right spawn
            rally_point = (form_center_x + 100, form_center_y + 50)
        elif spawn_side_index == 2:  # Top spawn
            rally_point = (form_center_x, form_center_y + 100)
        else:  # Bottom spawn (or any remaining spawn)
            rally_point = (form_center_x, form_center_y - 100)

        # Calculate which part of formation this group will fill
        start_index = group_index * sprites_per_group
        end_index = min(start_index + sprites_per_group, len(formation))
        group_formation = arcade.SpriteList()

        for i in range(start_index, end_index):
            if i < len(formation):
                group_formation.append(formation[i])

        # Create formation entry pattern for this group
        # Always create an entry action, even if the group is empty
        entry_pattern = create_formation_entry_pattern(
            formation_sprites=group_formation,
            spawn_area=spawn_area,
            cruise_duration=cruise_duration,
            rally_point=rally_point,
            slot_duration=slot_duration,
            avoid_sprites=player_sprite,
            max_cruise_speed=max_cruise_speed + random.uniform(-1.0, 1.0),  # Slight speed variation
            visible=True,
        )
        entry_actions.append(entry_pattern)

    return entry_actions


def create_galaga_style_entry(
    formation: arcade.SpriteList,
    groups_per_formation: int = 4,
    sprites_per_group: int = 10,
    player_sprite: arcade.Sprite | None = None,
    screen_bounds: tuple[float, float, float, float] = (0, 0, 800, 600),
    path_speed: float = 150.0,
    slot_duration: float = 2.0,
    spawn_areas: dict[str, bool] | None = None,
    path_amplitude: float = 100.0,
    path_frequency: float = 1.5,
):
    """Create authentic Galaga-style enemy entry patterns.

    This creates multiple groups that fly in curved spline paths in formation,
    following a leader, then slot into grid positions. This matches the actual
    Galaga enemy behavior where enemies fly in curved paths before forming up.

    Args:
        formation: Target formation with all positions arranged
        groups_per_formation: Number of groups to create (default: 4)
        sprites_per_group: Sprites per group (default: 10)
        player_sprite: Player sprite to avoid during flight
        screen_bounds: (left, bottom, right, top) screen boundaries
        path_speed: Speed along the spline path in pixels per second
        slot_duration: Duration of slot-in phase per group
        spawn_areas: Dict to enable/disable spawn areas. Keys: "left", "right", "top", "bottom".
                    Values: True to enable, False to disable. Default: all areas enabled.
        path_amplitude: Amplitude of the wave pattern in the spline (default: 100.0)
        path_frequency: Frequency of wave cycles in the spline (default: 1.5)

    Returns:
        List of sequence actions, one per group

    Example:
        formation = arrange_grid(count=40, rows=4, cols=10)
        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=4,
            sprites_per_group=10,
            player_sprite=player,
            path_speed=200.0
        )

        # Apply each group with a delay
        for i, action in enumerate(entry_actions):
            delay = DelayUntil(duration(i * 2.0))  # Stagger entries
            sequence(delay, action).apply(group_sprites[i], tag=f"group_{i}")
    """
    left, bottom, right, top = screen_bounds
    margin = 200  # Distance outside screen bounds

    # Define all possible spawn areas for different sides
    all_spawn_areas = [
        (left - margin, bottom, left, top),  # Left side
        (right, bottom, right + margin, top),  # Right side
        (left, top, right, top + margin),  # Top side
        (left, bottom - margin, right, bottom),  # Bottom side (less common)
    ]

    # Filter spawn areas based on spawn_areas parameter
    if spawn_areas is not None:
        area_names = ["left", "right", "top", "bottom"]
        filtered_spawn_areas = []
        for i, (area_name, area_coords) in enumerate(zip(area_names, all_spawn_areas, strict=False)):
            if spawn_areas.get(area_name, True):  # Default to True if not specified
                filtered_spawn_areas.append(area_coords)
        spawn_areas = filtered_spawn_areas
    else:
        spawn_areas = all_spawn_areas

    # Calculate formation center for path endpoints
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
        spawn_side_index = group_index % len(spawn_areas)

        # Calculate which part of formation this group will fill
        start_index = group_index * sprites_per_group
        end_index = min(start_index + sprites_per_group, len(formation))
        group_formation = arcade.SpriteList()

        for i in range(start_index, end_index):
            if i < len(formation):
                group_formation.append(formation[i])

        # Create Galaga-style entry pattern for this group
        entry_pattern = _create_galaga_group_entry(
            formation_sprites=group_formation,
            spawn_area=spawn_area,
            spawn_side_index=spawn_side_index,
            formation_center=(form_center_x, form_center_y),
            path_speed=path_speed,
            slot_duration=slot_duration,
            path_amplitude=path_amplitude,
            path_frequency=path_frequency,
        )
        entry_actions.append(entry_pattern)

    return entry_actions


def _create_galaga_group_entry(
    formation_sprites: arcade.SpriteList,
    spawn_area: tuple[float, float, float, float],
    spawn_side_index: int,
    formation_center: tuple[float, float],
    path_speed: float,
    slot_duration: float,
    path_amplitude: float,
    path_frequency: float,  # Kept for API compatibility but not used
):
    """Create simple leader-follower Galaga-style group entry using established ArcadeActions patterns.

    All sprites follow the exact same S-curve path with time delays.
    Leader starts immediately, followers start with delays based on formation spacing.
    Each sprite ends up at its final formation position.

    This is the SIMPLE implementation using a single shared path.
    """
    from actions.composite import sequence
    from actions.conditional import FollowPathUntil, duration

    # Store original target positions (where sprites should end up)
    target_positions = [(s.center_x, s.center_y) for s in formation_sprites]

    # Calculate follower spacing from formation grid
    def calculate_grid_spacing(target_positions):
        if len(target_positions) < 2:
            return 50.0

        # Find minimum non-zero X spacing
        x_positions = [pos[0] for pos in target_positions]
        min_spacing = float("inf")

        for i in range(len(x_positions)):
            for j in range(i + 1, len(x_positions)):
                spacing = abs(x_positions[i] - x_positions[j])
                if spacing > 0:
                    min_spacing = min(min_spacing, spacing)

        return min_spacing if min_spacing != float("inf") else 50.0

    follower_spacing = calculate_grid_spacing(target_positions)
    # Much tighter spacing - reduce delay to 1/10th of the calculated value
    delay_between_sprites = (follower_spacing / path_speed) * 0.1

    # Helper function to create spline paths (using proven working Bezier control points)
    def _create_galaga_spline_path(spawn_side_index, formation_center, path_amplitude):
        """Create a Galaga-style spline path from spawn to formation center."""
        center_x, center_y = formation_center

        # Get spawn area bounds
        left, bottom, right, top = spawn_area

        # Generate control points for authentic Galaga S-curve path
        if spawn_side_index == 0:  # Left spawn
            start_x = left
            start_y = (bottom + top) / 2

            # Create dramatic S-curve using more pronounced control points
            control_points = [
                (start_x, start_y),  # Start off-screen left
                (start_x + 200, start_y - 150),  # Pull down-right (creates dramatic first curve)
                (start_x + 400, start_y + 150),  # Pull up-right (creates dramatic S-shape)
                (center_x, center_y),  # End at formation center
            ]
        elif spawn_side_index == 1:  # Right spawn
            start_x = right
            start_y = (bottom + top) / 2

            # Mirror the dramatic S-curve for right spawn
            control_points = [
                (start_x, start_y),  # Start off-screen right
                (start_x - 200, start_y - 150),  # Pull down-left (creates dramatic first curve)
                (start_x - 400, start_y + 150),  # Pull up-left (creates dramatic S-shape)
                (center_x, center_y),  # End at formation center
            ]
        elif spawn_side_index == 2:  # Top spawn
            start_x = (left + right) / 2
            start_y = top

            # Curly-Q from top
            control_points = [
                (start_x, start_y),  # Start off-screen top
                (start_x + path_amplitude * 0.7, start_y - path_amplitude * 0.5),  # Curve right
                (start_x - path_amplitude * 0.5, start_y - path_amplitude * 1.2),  # Loop back left
                (center_x, center_y),  # End at formation center
            ]
        else:  # Bottom spawn
            start_x = (left + right) / 2
            start_y = bottom

            # Simple curve from bottom
            control_points = [
                (start_x, start_y),  # Start off-screen bottom
                (start_x + path_amplitude * 0.6, start_y + path_amplitude * 0.8),  # Curve right
                (start_x - path_amplitude * 0.4, start_y + path_amplitude * 1.5),  # Curve left
                (center_x, center_y),  # End at formation center
            ]

        return control_points

    # Helper function to create individual spline paths for each sprite
    def _create_individual_galaga_path(spawn_side_index, target_position, path_amplitude):
        """Create a Galaga-style spline path from spawn to individual target position."""
        target_x, target_y = target_position

        # Get spawn area bounds
        left, bottom, right, top = spawn_area

        # Generate control points for authentic Galaga S-curve path
        if spawn_side_index == 0:  # Left spawn
            start_x = left
            start_y = (bottom + top) / 2

            # Create S-curve using proven working Bezier control points
            control_points = [
                (start_x, start_y),  # Start off-screen left
                (start_x + 200, start_y - 150),  # Pull down-right (creates dramatic first curve)
                (start_x + 400, start_y + 150),  # Pull up-right (creates dramatic S-shape)
                (target_x, target_y),  # End at individual target position
            ]
        elif spawn_side_index == 1:  # Right spawn
            start_x = right
            start_y = (bottom + top) / 2

            # Mirror the dramatic S-curve for right spawn
            control_points = [
                (start_x, start_y),  # Start off-screen right
                (start_x - 200, start_y - 150),  # Pull down-left (creates dramatic first curve)
                (start_x - 400, start_y + 150),  # Pull up-left (creates dramatic S-shape)
                (target_x, target_y),  # End at individual target position
            ]
        elif spawn_side_index == 2:  # Top spawn
            start_x = (left + right) / 2
            start_y = top

            # Curly-Q from top
            control_points = [
                (start_x, start_y),  # Start off-screen top
                (start_x + path_amplitude * 0.7, start_y - path_amplitude * 0.5),  # Curve right
                (start_x - path_amplitude * 0.5, start_y - path_amplitude * 1.2),  # Loop back left
                (target_x, target_y),  # End at individual target position
            ]
        else:  # Bottom spawn
            start_x = (left + right) / 2
            start_y = bottom

            # Simple curve from bottom
            control_points = [
                (start_x, start_y),  # Start off-screen bottom
                (start_x + path_amplitude * 0.6, start_y + path_amplitude * 0.8),  # Curve right
                (start_x - path_amplitude * 0.4, start_y + path_amplitude * 1.5),  # Curve left
                (target_x, target_y),  # End at individual target position
            ]

        return control_points

    # Simple spawn positioner
    class SimpleSpawnPositioner:
        """Position sprites in spawn area with formation spacing."""

        def __init__(self, spawn_area, formation_sprites, spawn_side_index, grid_spacing, shared_spline_path):
            self.spawn_area = spawn_area
            self.formation_sprites = formation_sprites
            self.spawn_side_index = spawn_side_index
            self.grid_spacing = grid_spacing
            self.shared_spline_path = shared_spline_path
            self.target = None
            self.tag = None
            self.done = False
            self._is_active = False

        def apply(self, target, tag=None):
            self.target = target
            self.tag = tag
            self._is_active = True
            return self

        def start(self):
            """Position sprites at the start of the shared path with proper grid spacing."""
            self._is_active = True

            if not self.formation_sprites:
                self.done = True
                return

            # Get the start point of the shared path (first control point)
            start_x, start_y = self.shared_spline_path[0] if hasattr(self, "shared_spline_path") else (0, 0)

            # Position sprites in a line at the start of the shared path
            # Calculate spacing based on number of sprites
            total_spacing = (len(self.formation_sprites) - 1) * self.grid_spacing
            start_offset = -total_spacing / 2

            for i, sprite in enumerate(self.formation_sprites):
                # Position exactly at the path start point
                sprite.center_x = start_x
                sprite.center_y = start_y + start_offset + i * self.grid_spacing
                sprite.visible = True

                # Ensure sprites start with no velocity
                sprite.change_x = 0
                sprite.change_y = 0
                sprite.change_angle = 0

            self.done = True

        def stop(self):
            self.done = True
            self._is_active = False

        def update(self, delta_time):
            pass

    # Simple coordinator using shared path for true leader-follower behavior
    class SimpleGalagaCoordinator:
        """Coordinates sprites following the same shared S-curve path with delays, then moving to final positions."""

        def __init__(
            self,
            formation_sprites,
            target_positions,
            path_speed,
            delay_between_sprites,
            shared_spline_path,
            formation_center,
        ):
            self.formation_sprites = formation_sprites
            self.target_positions = target_positions
            self.path_speed = path_speed
            self.delay_between_sprites = delay_between_sprites
            self.shared_spline_path = shared_spline_path
            self.formation_center = formation_center
            self.target = None
            self.tag = None
            self.done = False
            self._is_active = False
            self.sprite_sequences = []

        def apply(self, target, tag=None):
            self.target = target
            self.tag = tag
            self._is_active = True
            return self

        def start(self):
            """Create and start sprite sequences: delay -> shared path -> individual positioning -> rotation."""
            self._is_active = True
            self._target_positions = list(self.target_positions)
            self._rotated = [False] * len(self.formation_sprites)

            for i, sprite in enumerate(self.formation_sprites):
                sprite_delay = i * self.delay_between_sprites
                target_x, target_y = self.target_positions[i]
                from actions.conditional import DelayUntil, MoveUntil, RotateUntil

                def make_individual_path_action(sprite=sprite, target_x=target_x, target_y=target_y):
                    """Each sprite follows its own S-curve path to its final position."""

                    def on_path_stop(*_):
                        # Position sprite at its final position when path completes
                        sprite.center_x = target_x
                        sprite.center_y = target_y
                        sprite.change_angle = 0

                    # Create individual path for this sprite
                    individual_path = _create_individual_galaga_path(
                        spawn_side_index, (target_x, target_y), path_amplitude
                    )

                    return FollowPathUntil(
                        control_points=individual_path,
                        velocity=self.path_speed,
                        condition=lambda: abs(sprite.center_x - target_x) < 30 and abs(sprite.center_y - target_y) < 30,
                        rotate_with_path=True,
                        rotation_offset=0.0,
                        on_stop=on_path_stop,
                    )

                def make_final_positioning_action(sprite=sprite, target_x=target_x, target_y=target_y):
                    """Move from formation center to individual final grid position."""

                    def on_final_stop(*_):
                        sprite.center_x = target_x
                        sprite.center_y = target_y
                        sprite.change_angle = 0

                    # Calculate direction and distance from formation center to final position
                    dx = target_x - self.formation_center[0]
                    dy = target_y - self.formation_center[1]
                    distance = (dx**2 + dy**2) ** 0.5

                    if distance > 0:
                        # Normalize direction and apply moderate speed
                        speed = 2.0  # Much slower speed to prevent offscreen movement
                        velocity = (dx / distance * speed, dy / distance * speed)
                    else:
                        # Already at target
                        velocity = (0, 0)

                    return MoveUntil(
                        velocity=velocity,
                        condition=lambda: abs(sprite.center_x - target_x) < 10 and abs(sprite.center_y - target_y) < 10,
                        on_stop=on_final_stop,
                    )

                def make_rotate_action(sprite=sprite, idx=i):
                    # Simple approach: always rotate towards 0 degrees using the shortest path

                    def get_shortest_rotation_to_zero():
                        """Calculate the angular velocity needed for shortest rotation to 0 degrees."""
                        # Normalize current angle to [0, 360) range
                        current_angle = sprite.angle % 360

                        # Calculate shortest path to 0 degrees with smaller velocity to prevent overshoot
                        if current_angle <= 180:
                            # Rotate counter-clockwise (negative) to reach 0
                            return -30.0  # Much smaller velocity
                        else:
                            # Rotate clockwise (positive) to reach 0
                            return 30.0  # Much smaller velocity

                    def angle_distance_to_zero():
                        """Calculate the angular distance to 0 degrees."""
                        normalized = sprite.angle % 360
                        distance = min(normalized, 360 - normalized)
                        return distance

                    def on_stop(*_):
                        sprite.angle = 0
                        sprite.change_angle = 0
                        self._rotated[idx] = True

                    # Create a wrapper that recalculates direction on each condition check
                    class AdaptiveRotateUntil(RotateUntil):
                        def __init__(self):
                            super().__init__(
                                angular_velocity=30.0,  # Will be updated dynamically
                                condition=lambda: angle_distance_to_zero() < 15,  # Larger tolerance
                                on_stop=on_stop,
                            )

                        def apply_effect(self):
                            # Update angular velocity to always go the shortest way
                            optimal_velocity = get_shortest_rotation_to_zero()
                            self.target_angular_velocity = optimal_velocity
                            self.current_angular_velocity = optimal_velocity
                            super().apply_effect()

                    return AdaptiveRotateUntil()

                # Create sequence: delay -> individual path -> rotation
                if sprite_delay > 0:
                    delay_action = DelayUntil(condition=duration(sprite_delay))
                    individual_path_action = make_individual_path_action()
                    rotate_action = make_rotate_action()
                    sprite_sequence = sequence(delay_action, individual_path_action, rotate_action)
                else:
                    individual_path_action = make_individual_path_action()
                    rotate_action = make_rotate_action()
                    sprite_sequence = sequence(individual_path_action, rotate_action)

                sprite_sequence.apply(sprite, tag=f"galaga_leader_follower_{i}")
                sprite_sequence.start()
                self.sprite_sequences.append(sprite_sequence)

        def stop(self):
            self.done = True
            self._is_active = False
            # Stop all sprite sequences
            for sequence_action in self.sprite_sequences:
                sequence_action.stop()

        def update(self, delta_time):
            if not self._is_active:
                return
            all_done = True
            for sequence_action in self.sprite_sequences:
                if not sequence_action.done:
                    all_done = False
                    break
            if all_done:
                # Only zero change_angle when all actions are done
                for sprite in self.formation_sprites:
                    sprite.change_angle = 0
                self.done = True

    # Create simple components
    grid_spacing = calculate_grid_spacing(target_positions)

    # Create the shared spline path that all sprites in this row will follow
    # Each sprite's path ends at its individual final position
    shared_spline_path = _create_galaga_spline_path(spawn_side_index, formation_center, path_amplitude)

    spawn_positioner = SimpleSpawnPositioner(
        spawn_area, formation_sprites, spawn_side_index, grid_spacing, shared_spline_path
    )

    coordinator = SimpleGalagaCoordinator(
        formation_sprites,
        target_positions,
        path_speed * 3.0,  # Increase speed to make S-curve more visible
        delay_between_sprites,
        shared_spline_path,  # Pass the shared path
        formation_center,  # Pass formation center for positioning
    )

    # Combine spawn positioning and coordination
    phases = [spawn_positioner, coordinator]
    return sequence(*phases)


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
