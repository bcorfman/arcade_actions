"""
Movement patterns and condition helpers.

This module provides functions for creating complex movement patterns like zigzag,
wave, spiral, and orbit movements, as well as condition helper functions for
use with conditional actions.
"""

import math
import random
import time
from collections.abc import Callable

import arcade

from actions import DelayUntil, FollowPathUntil, MoveUntil, duration, sequence


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

    # Calculate parametric zig-zag using a single relative curve
    # -----------------------------------------------------------
    width, height = dimensions

    # Guard against invalid inputs
    if segments <= 0:
        raise ValueError("segments must be > 0")
    if speed <= 0:
        raise ValueError("speed must be > 0")

    # Total travel distance and corresponding duration (pixels / (pixels per second) = seconds)
    segment_distance = math.sqrt(width**2 + height**2)
    total_distance = segment_distance * segments
    total_time = total_distance / speed  # seconds

    # Pre-compute constants for efficiency
    half_width = width  # alias – clearer below

    def _offset_fn(t: float) -> tuple[float, float]:
        """Piece-wise linear zig-zag offset (relative).

        `t` in 0 → 1 is mapped across *segments* straight-line sections that
        alternate left/right movement while always moving *up* (positive Y).
        """

        # Clamp for numerical safety
        t = max(0.0, min(1.0, t))

        # Determine which segment we're in and the local progress within it
        seg_f = t * segments  # floating-segment index
        seg_idx = int(math.floor(seg_f))
        if seg_idx >= segments:
            seg_idx = segments - 1
            seg_t = 1.0
        else:
            seg_t = seg_f - seg_idx  # 0→1 progress within segment

        # Accumulate completed segments
        dx = 0.0
        dy = 0.0
        for i in range(seg_idx):
            direction = 1 if i % 2 == 0 else -1
            dx += half_width * direction
            dy += height

        # Current segment partial
        direction = 1 if seg_idx % 2 == 0 else -1
        dx += half_width * direction * seg_t
        dy += height * seg_t

        return dx, dy

    from actions.conditional import ParametricMotionUntil  # local import to avoid cycles

    return ParametricMotionUntil(_offset_fn, duration(total_time))


def create_wave_pattern(
    amplitude: float,
    length: float,
    speed: float,
    *,
    start_progress: float = 0.0,
    end_progress: float = 1.0,
    debug: bool = False,
    debug_threshold: float | None = None,
):
    """Galaga-style sway with *formation slots in the middle of the dip*.

    The Action returned is a ParametricMotionUntil instance implemented with
    relative parametric offsets. The function keeps the zero-drift guarantee:
    after every complete cycle the sprite returns to its original X/Y.

    Args:
        amplitude: Height of the wave (Y-axis movement)
        length: Half-width of the wave (X-axis movement)
        speed: Movement speed in pixels per frame
        start_progress: Starting position along the wave cycle [0.0, 1.0], default 0.0
        end_progress: Ending position along the wave cycle [0.0, 1.0], default 1.0

    The wave cycle progresses as:
        0.0: Left crest
        0.25: Trough (dip)
        0.5: Right crest
        0.75: Trough (dip)
        1.0: Back to left crest

    Example:
        # Full wave (default behavior)
        create_wave_pattern(20, 80, 4)

        # From trough to left crest only
        create_wave_pattern(20, 80, 4, start_progress=0.75, end_progress=1.0)
    """

    from actions.conditional import ParametricMotionUntil, duration  # local import to avoid cycles

    # Validate progress parameters
    if not (0.0 <= start_progress <= 1.0 and 0.0 <= end_progress <= 1.0):
        raise ValueError("start_progress and end_progress must be within [0.0, 1.0]")
    if end_progress < start_progress:
        raise ValueError("end_progress must be >= start_progress (no wrap or reverse supported)")

    # ----------------- helper for building parametric actions -----------------
    def _param(offset_fn, dur):
        return ParametricMotionUntil(
            offset_fn,
            duration(dur),
            debug=debug,
            debug_threshold=debug_threshold if debug_threshold is not None else length * 1.2,
        )

    # ------------------------------------------------------------
    # Full wave: left crest → trough → right crest → back
    # ------------------------------------------------------------
    # Per tests/docs, a full wave duration is 2.5 * length / speed seconds
    full_time = (2.5 * length / speed) if speed != 0 else 0.0

    def _full_offset(t: float) -> tuple[float, float]:
        # Triangular time-base 0→1→0 to make sure we return to origin in X
        tri = 1 - abs(1 - 2 * t)
        dx = length * tri  # right then back left
        dy = -amplitude * math.sin(math.pi * tri)  # dip (trough at centre)
        return dx, dy

    # Calculate the sub-range parameters (span maps linearly to time)
    span = end_progress - start_progress
    sub_time = full_time * span

    # Compute base offset at the start so subrange is relative (no initial snap)
    _base_dx, _base_dy = _full_offset(start_progress)

    # For sequence continuity, we need to ensure the end position matches the next pattern's start
    # If this is a partial pattern that doesn't end at the natural cycle end, adjust accordingly
    _end_dx, _end_dy = _full_offset(end_progress)

    def _remapped_offset(t: float) -> tuple[float, float]:
        # Remap t from [0, 1] to [start_progress, end_progress]
        p = start_progress + span * t
        dx, dy = _full_offset(p)

        # For sequence continuity: if end_progress is 1.0 (full cycle end),
        # ensure we end at (0,0) regardless of the pattern's natural end position
        if end_progress >= 1.0 and t >= 1.0:
            # Force end position to (0, 0) for seamless sequence transitions
            return 0.0 - _base_dx, 0.0 - _base_dy

        return dx - _base_dx, dy - _base_dy

    # If start and end are the same, return a no-op action
    if span == 0.0:
        return _param(lambda t: (0.0, 0.0), 0.0)

    return _param(_remapped_offset, sub_time)


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

    # Always generate the outward spiral path first
    outward_points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        radius = t * max_radius
        angle = t * revolutions * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        outward_points.append((x, y))

    # For inward spiral, reverse the outward path to ensure perfect reversal
    if direction == "outward":
        control_points = outward_points
        rotation_offset = 0.0  # Default rotation
    else:  # inward
        control_points = list(reversed(outward_points))
        rotation_offset = 180.0  # Compensate for reversed movement direction

    # Estimate total path length
    total_length = revolutions * math.pi * max_radius  # Approximate
    duration_time = total_length / speed

    return FollowPathUntil(
        control_points, speed, duration(duration_time), rotate_with_path=True, rotation_offset=rotation_offset
    )


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
    if speed <= 0:
        raise ValueError("speed must be > 0")

    # Approximate path length for timing (perimeter of both lobes)
    path_length = 2 * math.pi * max(width, height) / 2.0
    total_time = path_length / speed  # seconds

    # Pre-generate control points for test symmetry checks (17 items inc. loop closure)
    control_points: list[tuple[float, float]] = []
    num_points = 16
    for i in range(num_points + 1):
        theta = (i / num_points) * 2 * math.pi
        px = (width / 2.0) * math.sin(theta)
        py = (height / 2.0) * math.sin(2 * theta)
        control_points.append((center_x + px, center_y + py))

    def _offset_fn(t: float) -> tuple[float, float]:
        """Relative figure-8 offset using classic lemniscate equations."""
        t = max(0.0, min(1.0, t))
        theta = t * 2.0 * math.pi
        dx = (width / 2.0) * math.sin(theta)
        dy = (height / 2.0) * math.sin(2.0 * theta)
        return dx, dy

    from actions.conditional import ParametricMotionUntil  # local import to avoid cycles

    action = ParametricMotionUntil(_offset_fn, duration(total_time))
    # Retain control_points attribute for existing unit-tests
    action.control_points = control_points  # type: ignore[attr-defined]
    return action


def create_orbit_pattern(center: tuple[float, float], radius: float, speed: float, clockwise: bool = True):
    """Create a single circular orbit pattern (one full revolution).

    Args:
        center: (x, y) coordinates of orbit center
        radius: Radius of the orbit
        speed: Movement speed along the path (pixels per second)
        clockwise: True for clockwise orbit, False for counter-clockwise

    Returns:
        An Action that completes exactly one orbit. Wrap with repeat() for infinite orbits.

    The returned action starts from the sprite's current angular position relative
    to the given center, ensuring seamless repetition when wrapped with repeat().
    """

    from actions.base import Action as _Action

    center_x, center_y = center

    # Calculate angular velocity (radians per second) from path speed
    circumference = 2 * math.pi * radius
    if circumference <= 0:
        raise ValueError("radius must be > 0")
    angular_velocity = (2 * math.pi * speed) / circumference  # radians per second

    class SingleOrbitAction(_Action):
        def __init__(self):
            # Use a non-terminating condition; completion handled internally
            from actions.conditional import infinite as _infinite

            super().__init__(_infinite)
            self.center_x = center_x
            self.center_y = center_y
            self.radius = radius
            self.angular_velocity = angular_velocity
            self.clockwise = clockwise
            # Per-sprite state: angle, start_angle, accumulated, prev_pos, prev_sprite_angle
            self._states: dict[int, dict[str, float | tuple[float, float] | None]] = {}

        def apply_effect(self):
            # Initialize per-sprite state from current positions for seamless start
            def init_state(sprite):
                dx0 = sprite.center_x - self.center_x
                dy0 = sprite.center_y - self.center_y
                # Compute starting angle; if at center, place at rightmost point
                if abs(dx0) < 1e-9 and abs(dy0) < 1e-9:
                    start_angle = 0.0
                    sprite.center_x = self.center_x + self.radius
                    sprite.center_y = self.center_y
                else:
                    start_angle = math.atan2(dy0, dx0)

                sid = id(sprite)
                self._states[sid] = {
                    "angle": float(start_angle),
                    "start_angle": float(start_angle),
                    "accumulated": 0.0,
                    "prev_pos": (sprite.center_x, sprite.center_y),
                    "prev_sprite_angle": None,
                }

            self.for_each_sprite(init_state)

        def update_effect(self, delta_time: float):
            # Update each sprite along its orbit and track completion
            direction_sign = 1.0 if self.clockwise else -1.0
            per_sprite_done: list[bool] = []

            def step(sprite):
                sid = id(sprite)
                st = self._states.get(sid)
                if st is None:
                    return

                delta_angle = self.angular_velocity * delta_time * direction_sign
                st["angle"] = float(st["angle"]) + delta_angle  # type: ignore[assignment]
                st["accumulated"] = float(st["accumulated"]) + abs(delta_angle)  # type: ignore[assignment]

                # Compute new position on circle
                angle_now = float(st["angle"])  # type: ignore[arg-type]
                orbit_x = self.center_x + self.radius * math.cos(angle_now)
                orbit_y = self.center_y + self.radius * math.sin(angle_now)

                # Movement vector for rotation continuity
                prev_pos = st["prev_pos"]  # type: ignore[assignment]
                sprite_angle: float | None = None
                if isinstance(prev_pos, tuple):
                    move_dx = orbit_x - prev_pos[0]
                    move_dy = orbit_y - prev_pos[1]
                    if abs(move_dx) > 1e-6 or abs(move_dy) > 1e-6:
                        sprite_angle = math.degrees(math.atan2(move_dy, move_dx))
                        st["prev_sprite_angle"] = sprite_angle
                    else:
                        prev_ang = st["prev_sprite_angle"]
                        if isinstance(prev_ang, float):
                            sprite_angle = prev_ang

                # Apply transform
                sprite.center_x = orbit_x
                sprite.center_y = orbit_y
                if sprite_angle is not None:
                    sprite.angle = sprite_angle

                # Store prev position
                st["prev_pos"] = (orbit_x, orbit_y)

                # Check completion for this sprite
                done = float(st["accumulated"]) >= math.tau * 0.999  # tolerate small numeric error
                per_sprite_done.append(done)

                # If done, snap to exact start point for seamless repeat
                if done:
                    start_angle = float(st["start_angle"])  # type: ignore[arg-type]
                    sprite.center_x = self.center_x + self.radius * math.cos(start_angle)
                    sprite.center_y = self.center_y + self.radius * math.sin(start_angle)

            self.for_each_sprite(step)

            # Mark action complete when all sprites have completed one orbit
            if per_sprite_done and all(per_sprite_done):
                self._condition_met = True
                self.done = True

        def reset(self):
            """Reset the action to its initial state."""
            self._states.clear()

        def clone(self):
            return create_orbit_pattern((self.center_x, self.center_y), self.radius, speed, self.clockwise)

    return SingleOrbitAction()


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
    # Local import to avoid potential circular dependency with main actions module
    from .conditional import infinite

    return MoveUntil(
        velocity,
        infinite,  # Continue indefinitely
        bounds=bounds,
        boundary_behavior="bounce",
    )


def create_patrol_pattern(
    start_pos: tuple[float, float],
    end_pos: tuple[float, float],
    speed: float,
    *,
    start_progress: float = 0.0,
    end_progress: float = 1.0,
):
    """Create a back-and-forth patrol pattern between two points.

    The sprite starts from its current position and executes the specified
    portion of the patrol cycle using boundary bouncing.

    Args:
        start_pos: (x, y) left boundary position
        end_pos: (x, y) right boundary position
        speed: Movement speed in pixels per frame (Arcade semantics)
        start_progress: Starting progress along the patrol cycle [0.0, 1.0], default 0.0
        end_progress: Ending progress along the patrol cycle [0.0, 1.0], default 1.0

    The patrol cycle progresses as:
        0.0: Start position (left boundary)
        0.5: End position (right boundary)
        1.0: Back to start position (left boundary)

    Returns:
        MoveUntil action with boundary bouncing

    Example:
        # Sprite at center, move to left boundary then do full patrol
        quarter = create_patrol_pattern(left_pos, right_pos, 2, start_progress=0.75, end_progress=1.0)
        full = create_patrol_pattern(left_pos, right_pos, 2, start_progress=0.0, end_progress=1.0)
        sequence(quarter, repeat(full)).apply(sprite)
    """
    # Validate progress parameters
    if not (0.0 <= start_progress <= 1.0 and 0.0 <= end_progress <= 1.0):
        raise ValueError("start_progress and end_progress must be within [0.0, 1.0]")
    if end_progress < start_progress:
        raise ValueError("end_progress must be >= start_progress (no wrap or reverse supported)")

    # Handle edge cases
    if start_progress == end_progress:
        return sequence()

    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.hypot(dx, dy)

    if distance == 0:
        return sequence()

    # Local imports to avoid circular dependencies
    from .conditional import MoveUntil, duration

    # Set boundaries at the patrol endpoints
    left = min(start_pos[0], end_pos[0])
    right = max(start_pos[0], end_pos[0])
    bottom = min(start_pos[1], end_pos[1])
    top = max(start_pos[1], end_pos[1])
    bounds = (left, bottom, right, top)

    # Determine initial direction based on start_progress
    # start_progress < 0.5 means we're on the forward leg (toward end_pos)
    # start_progress >= 0.5 means we're on the return leg (toward start_pos)
    dir_x, dir_y = dx / distance, dy / distance
    if start_progress < 0.5:
        # Moving toward end_pos (right boundary)
        velocity = (dir_x * speed, dir_y * speed)
    else:
        # Moving toward start_pos (left boundary)
        velocity = (-dir_x * speed, -dir_y * speed)

    # Calculate duration for the progress range
    total_distance = distance * 2  # full round trip distance
    progress_distance = total_distance * (end_progress - start_progress)
    duration_seconds = progress_distance / speed / 60.0

    # Create MoveUntil with boundary bouncing (like create_bounce_pattern)
    return MoveUntil(velocity, duration(duration_seconds), bounds=bounds, boundary_behavior="bounce")


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


# Create precision movement action that stops exactly at target
def _create_precision_condition_and_callback(target_position, sprite_ref):
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


def _validate_entry_kwargs(kwargs: dict) -> dict:
    """Validate and normalize kwargs for create_formation_entry_from_sprites."""
    if "window_bounds" not in kwargs:
        raise ValueError("window_bounds is required for create_formation_entry_from_sprites")

    # Defaults
    validated = {
        "window_bounds": kwargs["window_bounds"],
        "speed": kwargs.get("speed", 5.0),
        "stagger_delay": kwargs.get("stagger_delay", 0.5),
    }
    return validated


def _determine_min_spacing(target_formation):
    """Compute a reasonable minimum spacing based on largest sprite dimension."""
    max_sprite_dimension = 64  # Default fallback
    # Get the maximum dimension from the first sprite as a reference
    first_sprite = target_formation[0]
    if hasattr(first_sprite, "width") and hasattr(first_sprite, "height"):
        max_sprite_dimension = max(first_sprite.width, first_sprite.height)
    elif hasattr(first_sprite, "texture") and first_sprite.texture:
        max_sprite_dimension = max(first_sprite.texture.width, first_sprite.texture.height)

    # Minimum spacing is 1.5x the maximum sprite dimension
    min_spacing = max_sprite_dimension * 1.5
    return min_spacing


def _clone_formation_sprites(target_formation) -> arcade.SpriteList:
    """Create invisible clones that will perform the entry animation."""
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
    return sprites


def create_formation_entry_from_sprites(
    target_formation: arcade.SpriteList, **kwargs
) -> list[tuple[arcade.Sprite, arcade.SpriteList, int]]:
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
        List of (sprite, action, target_formation_index) tuples

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
        for sprite, action, target_index in entry_actions:
            action.apply(sprite, tag="formation_entry")
    """
    if len(target_formation) == 0:
        return []

    params = _validate_entry_kwargs(kwargs)
    window_bounds = params["window_bounds"]
    speed = params["speed"]
    stagger_delay = params["stagger_delay"]

    # Create new sprites for the entry pattern (same number as target formation)
    sprites = _clone_formation_sprites(target_formation)

    # Calculate minimum spacing based on sprite dimensions
    min_spacing = _determine_min_spacing(target_formation)
    # Generate spawn positions distributed equally around an off-screen arc
    # Extract target positions from the formation
    spawn_positions = _generate_arc_spawn_positions(target_formation, window_bounds, min_spacing)
    target_positions = [(sprite.center_x, sprite.center_y) for sprite in target_formation]

    # Pick the nearest spawn position for each target position
    sprite_distances = _find_nearest(spawn_positions, target_positions)
    center_x = sum(pos[0] for pos in target_positions) / len(target_positions)
    center_y = sum(pos[1] for pos in target_positions) / len(target_positions)

    # Sort by distance from center (closest first for center-outward)
    def distance_from_center(item):
        _, tgt_idx, _ = item
        tgt_pos = target_positions[tgt_idx]
        return math.hypot(tgt_pos[0] - center_x, tgt_pos[1] - center_y)

    sprite_distances.sort(key=distance_from_center)

    # Use min-conflicts algorithm for optimal sprite-to-spawn assignment
    optimal_assignments = _min_conflicts_sprite_assignment(
        target_formation, spawn_positions, max_iterations=1000, time_limit=0.1
    )

    # Convert single assignment to wave format for compatibility
    enemy_waves_with_assignments = [optimal_assignments] if optimal_assignments else []

    entry_actions = []

    # Calculate movement time to determine proper delays
    max_movement_time = 0.0
    for wave_assignments in enemy_waves_with_assignments:
        for sprite_idx, spawn_idx in wave_assignments.items():
            distance = math.hypot(
                target_positions[sprite_idx][0] - spawn_positions[spawn_idx][0],
                target_positions[sprite_idx][1] - spawn_positions[spawn_idx][1],
            )
            movement_time = distance / speed if speed > 0 else 0
            max_movement_time = max(max_movement_time, movement_time)

    # Calculate safe wave separation time based on sprite velocity and size
    # Rule 3: Calculate enough time between waves to avoid collisions
    estimated_sprite_size = 64  # Conservative estimate for sprite width/height
    safe_clearance_time = (estimated_sprite_size * 2) / speed  # Time for 2 sprite widths at current speed
    # Cap the safe clearance time to prevent excessive delays
    safe_clearance_time = min(safe_clearance_time, 2.0)  # Maximum 2 seconds
    wave_separation_time = max(stagger_delay, safe_clearance_time)

    for wave_idx, wave_assignments in enumerate(enemy_waves_with_assignments):
        wave_delay = wave_idx * wave_separation_time

        # Calculate the longest distance in this wave to determine target arrival time
        max_distance_in_wave = 0.0
        for sprite_idx, spawn_idx in wave_assignments.items():
            distance = math.hypot(
                target_positions[sprite_idx][0] - spawn_positions[spawn_idx][0],
                target_positions[sprite_idx][1] - spawn_positions[spawn_idx][1],
            )
            max_distance_in_wave = max(max_distance_in_wave, distance)

        # Calculate target arrival time based on the longest distance and base speed
        target_arrival_time = max_distance_in_wave / speed if speed > 0 else 1.0

        for sprite_idx in wave_assignments:
            sprite = sprites[sprite_idx]
            si = wave_assignments[sprite_idx]  # Get spawn index directly from wave assignments
            sprite.center_x, sprite.center_y = spawn_positions[si]
            sprite.visible = True
            sprite.alpha = 255

            # Calculate individual speed so this sprite arrives at the same time as the slowest sprite
            distance = math.hypot(
                target_positions[sprite_idx][0] - spawn_positions[si][0],
                target_positions[sprite_idx][1] - spawn_positions[si][1],
            )
            individual_speed = distance / target_arrival_time if target_arrival_time > 0 else speed

            velocity = _calculate_velocity_to_target(
                spawn_positions[si], target_positions[sprite_idx], individual_speed
            )

            movement_action = MoveUntil(
                velocity, _create_precision_condition_and_callback(target_positions[sprite_idx], sprite)
            )

            if wave_delay > 0.01:  # Add delay for waves after the first
                delay_action = DelayUntil(duration(wave_delay))
                combined_action = sequence(delay_action, movement_action)
            else:
                combined_action = movement_action

            entry_actions.append((sprite, combined_action, sprite_idx))

    return entry_actions


def _generate_arc_spawn_positions(target_formation, window_bounds, min_spacing):
    num_sprites = len(target_formation)
    left, bottom, right, top = window_bounds
    arc_center_x = (left + right) / 2  # Center horizontally
    arc_center_y = (bottom + top) / 2  # Halfway down window (as requested)
    arc_radius = (right - left) * 1.2  # Arc radius based on window width

    # Calculate how many spawn points can fit on the arc with proper spacing
    arc_length = math.pi * arc_radius  # Half circle (180°)
    max_spawn_points = int(arc_length / min_spacing)

    # If we have more sprites than spawn points, reduce the number of spawn points
    # and increase spacing to ensure no starting collisions
    if num_sprites > max_spawn_points:
        # Recalculate spacing to fit all sprites
        min_spacing = arc_length / num_sprites

    # Distribute sprites equally along the arc from left (180°) to right (0°)
    spawn_positions = []
    for i in range(num_sprites):
        if num_sprites == 1:
            angle = math.pi / 2  # Single sprite at top of arc
        else:
            # Evenly distribute from 180° (left) to 0° (right)
            angle = math.pi - (i * math.pi / (num_sprites - 1))

            # Calculate position on the arc
        x = arc_center_x + arc_radius * math.cos(angle)
        y = arc_center_y + arc_radius * math.sin(angle)
        spawn_positions.append((x, y))
    return spawn_positions


def _find_nearest(spawn_positions, target_positions):
    """Find the optimal assignment of spawn positions to target positions.

    Uses a greedy approach to assign each target position to its nearest
    available spawn position, ensuring no spawn position is used twice.
    """
    # Simple optimization: if we have the same number of spawn positions as targets,
    # we can use a direct assignment without expensive sorting
    if len(spawn_positions) == len(target_positions):
        # Direct assignment - each target gets its nearest spawn
        sprite_distances = []
        used_spawn_positions = set()

        for i, target_pos in enumerate(target_positions):
            min_dist = float("inf")
            best_spawn_idx = 0

            for j, spawn_pos in enumerate(spawn_positions):
                if j not in used_spawn_positions:
                    dist = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        best_spawn_idx = j

            sprite_distances.append((min_dist, i, best_spawn_idx))
            used_spawn_positions.add(best_spawn_idx)

        return sprite_distances

    # Fallback to original algorithm for cases where spawn positions != targets
    sprite_distances = []
    used_spawn_positions = set()

    # Create list of (distance, target_idx, spawn_idx) for all combinations
    all_combinations = []
    for i, target_pos in enumerate(target_positions):
        for j, spawn_pos in enumerate(spawn_positions):
            dist = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
            all_combinations.append((dist, i, j))

    # Sort by distance (shortest first)
    all_combinations.sort()
    assigned_targets = set()

    # Assign targets to nearest available spawn positions
    for dist, target_idx, spawn_idx in all_combinations:
        if target_idx not in assigned_targets and spawn_idx not in used_spawn_positions:
            sprite_distances.append((dist, target_idx, spawn_idx))
            assigned_targets.add(target_idx)
            used_spawn_positions.add(spawn_idx)

    # Handle any remaining unassigned targets (shouldn't happen if enough spawn positions)
    for i, target_pos in enumerate(target_positions):
        if i not in assigned_targets:
            # Find nearest spawn position even if already used
            min_dist = float("inf")
            best_spawn_idx = 0
            for j, spawn_pos in enumerate(spawn_positions):
                dist = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
                if dist < min_dist:
                    min_dist = dist
                    best_spawn_idx = j
            sprite_distances.append((min_dist, i, best_spawn_idx))
    return sprite_distances


def _do_line_segments_intersect(
    line1: tuple[float, float, float, float], line2: tuple[float, float, float, float]
) -> bool:
    """
    Check if two line segments intersect.

    Args:
        line1: (x1, y1, x2, y2) - first line segment from (x1,y1) to (x2,y2)
        line2: (x3, y3, x4, y4) - second line segment from (x3,y3) to (x4,y4)

    Returns:
        True if the line segments intersect, False otherwise
    """
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    # First check if any endpoints are the same (touching at endpoints)
    tolerance = 1e-10
    if (
        (abs(x1 - x3) < tolerance and abs(y1 - y3) < tolerance)
        or (abs(x1 - x4) < tolerance and abs(y1 - y4) < tolerance)
        or (abs(x2 - x3) < tolerance and abs(y2 - y3) < tolerance)
        or (abs(x2 - x4) < tolerance and abs(y2 - y4) < tolerance)
    ):
        return True

    # Calculate the denominator for the parametric equations
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    # If denominator is 0, lines are parallel
    if abs(denom) < tolerance:
        return False

    # Calculate the parameters t and u
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    # Check if intersection point is on both line segments
    return -tolerance <= t <= 1 + tolerance and -tolerance <= u <= 1 + tolerance


def _min_conflicts_sprite_assignment(
    target_formation: arcade.SpriteList,
    spawn_positions: list[tuple[float, float]],
    max_iterations: int = 1000,
    time_limit: float = 0.1,
) -> dict[int, int]:
    """Assign sprites to spawn positions using min-conflicts algorithm.

    This function implements a min-conflicts approach:
    1. Start with a nearest-neighbor assignment of sprites to spawn positions
    2. Detect all path conflicts between sprites
    3. Iteratively swap conflicting sprite assignments to reduce conflicts
    4. Continue until no conflicts remain or time/iteration limits reached

    Args:
        target_formation: SpriteList with sprites positioned at target formation locations
        spawn_positions: List of (x, y) spawn positions
        max_iterations: Maximum number of iterations to perform
        time_limit: Maximum time in seconds to spend on optimization

    Returns:
        Dictionary mapping sprite_idx to spawn_idx with minimal conflicts
    """
    if len(target_formation) == 0 or len(spawn_positions) == 0:
        return {}

    num_sprites = len(target_formation)
    num_spawns = len(spawn_positions)

    # Ensure we have enough spawn positions
    if num_sprites > num_spawns:
        # Use only the first num_spawns sprites
        num_sprites = num_spawns

    start_time = time.time()

    # Step 1: Create initial assignment (greedy nearest-neighbor)
    assignments = {}  # sprite_idx -> spawn_idx
    used_spawns = set()

    # Sort sprites by distance from formation center for better initial assignment
    center_x = sum(sprite.center_x for sprite in target_formation) / len(target_formation)
    center_y = sum(sprite.center_y for sprite in target_formation) / len(target_formation)

    sprite_order = list(range(num_sprites))
    sprite_order.sort(
        key=lambda idx: math.sqrt(
            (target_formation[idx].center_x - center_x) ** 2 + (target_formation[idx].center_y - center_y) ** 2
        )
    )

    # Assign each sprite to its nearest available spawn
    for sprite_idx in sprite_order:
        target_pos = (target_formation[sprite_idx].center_x, target_formation[sprite_idx].center_y)
        best_spawn = None
        best_distance = float("inf")

        for spawn_idx, spawn_pos in enumerate(spawn_positions):
            if spawn_idx in used_spawns:
                continue
            distance = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
            if distance < best_distance:
                best_distance = distance
                best_spawn = spawn_idx

        if best_spawn is not None:
            assignments[sprite_idx] = best_spawn
            used_spawns.add(best_spawn)

    def count_conflicts(assignments_dict: dict[int, int]) -> int:
        """Count the number of path conflicts in the current assignment."""
        conflicts = 0
        sprite_indices = list(assignments_dict.keys())

        for i in range(len(sprite_indices)):
            for j in range(i + 1, len(sprite_indices)):
                sprite1_idx = sprite_indices[i]
                sprite2_idx = sprite_indices[j]

                if _sprites_would_collide_during_movement_with_assignments(
                    sprite1_idx, sprite2_idx, target_formation, spawn_positions, assignments_dict
                ):
                    conflicts += 1

        return conflicts

    def get_conflicting_pairs(assignments_dict: dict[int, int]) -> list[tuple[int, int]]:
        """Get all pairs of sprites that have path conflicts."""
        conflicts = []
        sprite_indices = list(assignments_dict.keys())

        for i in range(len(sprite_indices)):
            for j in range(i + 1, len(sprite_indices)):
                sprite1_idx = sprite_indices[i]
                sprite2_idx = sprite_indices[j]

                if _sprites_would_collide_during_movement_with_assignments(
                    sprite1_idx, sprite2_idx, target_formation, spawn_positions, assignments_dict
                ):
                    conflicts.append((sprite1_idx, sprite2_idx))

        return conflicts

    # Step 2: Iteratively resolve conflicts
    current_conflicts = count_conflicts(assignments)
    iteration = 0

    while current_conflicts > 0 and iteration < max_iterations:
        if time.time() - start_time > time_limit:
            break

        # Get all conflicting pairs
        conflicting_pairs = get_conflicting_pairs(assignments)
        if not conflicting_pairs:
            break

        # Try to resolve conflicts by swapping assignments
        improved = False

        for sprite1_idx, sprite2_idx in conflicting_pairs:
            if time.time() - start_time > time_limit:
                break

            # Try swapping the spawn assignments
            spawn1 = assignments[sprite1_idx]
            spawn2 = assignments[sprite2_idx]

            # Create temporary assignment with swap
            temp_assignments = assignments.copy()
            temp_assignments[sprite1_idx] = spawn2
            temp_assignments[sprite2_idx] = spawn1

            # Check if this reduces conflicts
            new_conflicts = count_conflicts(temp_assignments)

            if new_conflicts < current_conflicts:
                assignments = temp_assignments
                current_conflicts = new_conflicts
                improved = True
                break

        if not improved:
            # If no single swap helps, try random swaps to escape local optima
            for _ in range(min(10, len(conflicting_pairs))):
                if time.time() - start_time > time_limit:
                    break

                # Pick a random conflicting pair
                sprite1_idx, sprite2_idx = random.choice(conflicting_pairs)

                # Try swapping
                spawn1 = assignments[sprite1_idx]
                spawn2 = assignments[sprite2_idx]

                temp_assignments = assignments.copy()
                temp_assignments[sprite1_idx] = spawn2
                temp_assignments[sprite2_idx] = spawn1

                new_conflicts = count_conflicts(temp_assignments)

                # Accept swap if it doesn't increase conflicts too much (allows some exploration)
                if new_conflicts <= current_conflicts + 1:
                    assignments = temp_assignments
                    current_conflicts = new_conflicts
                    improved = True
                    break

        if not improved:
            break

        iteration += 1

    elapsed_time = time.time() - start_time
    return assignments


def _sprites_would_collide_during_movement_with_assignments(
    sprite1_idx: int,
    sprite2_idx: int,
    target_formation: arcade.SpriteList,
    spawn_positions: list[tuple[float, float]],
    assignments: dict[int, int],
) -> bool:
    """Check if two sprites would collide during movement using explicit assignments.

    This is a simplified version of _sprites_would_collide_during_movement
    that works with explicit assignment dictionaries.
    """
    # Get the sprites
    sprite1 = target_formation[sprite1_idx]
    sprite2 = target_formation[sprite2_idx]

    # Get spawn assignments
    spawn1_idx = assignments.get(sprite1_idx)
    spawn2_idx = assignments.get(sprite2_idx)

    if spawn1_idx is None or spawn2_idx is None:
        return False

    # Get spawn positions
    spawn1 = spawn_positions[spawn1_idx]
    spawn2 = spawn_positions[spawn2_idx]

    # Get target positions
    target1 = (sprite1.center_x, sprite1.center_y)
    target2 = (sprite2.center_x, sprite2.center_y)

    # Calculate sprite dimensions
    sprite1_width = getattr(sprite1, "width", 64)
    sprite1_height = getattr(sprite1, "height", 64)
    sprite2_width = getattr(sprite2, "width", 64)
    sprite2_height = getattr(sprite2, "height", 64)

    # Calculate minimum safe distance - use a more reasonable value
    # For movement collision detection, we only care about actual sprite overlap
    # The final formation positions are handled separately
    min_safe_distance = max(sprite1_width, sprite1_height, sprite2_width, sprite2_height) * 0.8

    # Check start positions
    start_distance = math.hypot(spawn1[0] - spawn2[0], spawn1[1] - spawn2[1])
    if start_distance < min_safe_distance:
        return True

    # Check end positions
    end_distance = math.hypot(target1[0] - target2[0], target1[1] - target2[1])
    if end_distance < min_safe_distance:
        return True

    # Check if movement paths intersect
    path1 = (spawn1[0], spawn1[1], target1[0], target1[1])
    path2 = (spawn2[0], spawn2[1], target2[0], target2[1])

    if _do_line_segments_intersect(path1, path2):
        return True

    # Check multiple points along the movement paths
    for t in [0.25, 0.5, 0.75]:
        # Calculate position at time t for sprite 1
        pos1_x = spawn1[0] + t * (target1[0] - spawn1[0])
        pos1_y = spawn1[1] + t * (target1[1] - spawn1[1])

        # Calculate position at time t for sprite 2
        pos2_x = spawn2[0] + t * (target2[0] - spawn2[0])
        pos2_y = spawn2[1] + t * (target2[1] - spawn2[1])

        # Check distance at this point
        distance = math.hypot(pos2_x - pos1_x, pos2_y - pos1_y)
        if distance < min_safe_distance:
            return True

    return False
