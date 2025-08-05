import math

import arcade


def _paths_would_intersect(
    spawn1: tuple[float, float],
    target1: tuple[float, float],
    width1: float,
    height1: float,
    spawn2: tuple[float, float],
    target2: tuple[float, float],
    width2: float,
    height2: float,
) -> bool:
    """Check if two sprite movement paths would intersect."""

    # Check if paths are too close or intersect
    # Simple line intersection check for center paths
    def line_intersects(p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects with line segment p3-p4."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:  # Lines are parallel
            return False

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        return 0 <= t <= 1 and 0 <= u <= 1

    # Check for overlapping spawn positions first (fix starting collisions)

    spawn_separation = max(width1, height1, width2, height2) * 1.2  # Increased buffer
    spawn_distance = math.hypot(spawn2[0] - spawn1[0], spawn2[1] - spawn1[1])
    if spawn_distance < spawn_separation:
        return True

    # Check for overlapping target positions
    target_separation = max(width1, height1, width2, height2) * 1.2
    target_distance = math.hypot(target2[0] - target1[0], target2[1] - target1[1])
    if target_distance < target_separation:
        return True

    # Check center line intersection
    if line_intersects(spawn1, target1, spawn2, target2):
        return True

    # Check if paths are too close throughout movement (parallel paths)
    # This handles cases where lines don't intersect but sprites would still collide
    min_separation = max(width1, height1, width2, height2) * 0.8

    # Sample multiple points along each path to check minimum distance
    for t in [0.25, 0.5, 0.75]:  # Check at 25%, 50%, 75% of movement
        point1 = (spawn1[0] + t * (target1[0] - spawn1[0]), spawn1[1] + t * (target1[1] - spawn1[1]))
        point2 = (spawn2[0] + t * (target2[0] - spawn2[0]), spawn2[1] + t * (target2[1] - spawn2[1]))
        distance = math.hypot(point2[0] - point1[0], point2[1] - point1[1])
        if distance < min_separation:
            return True

    return False


def assign_sprites_to_waves_simple(
    target_formation: arcade.SpriteList,
    spawn_positions: list[tuple[float, float]],
) -> list[dict[int, int]]:
    """Simple implementation of user's rules without complex collision detection."""

    if len(target_formation) == 0:
        return []

    # Calculate center of formation for center-outward ordering
    center_x = sum(sprite.center_x for sprite in target_formation) / len(target_formation)
    center_y = sum(sprite.center_y for sprite in target_formation) / len(target_formation)

    # Initialize all sprites as candidates, sorted by distance from center
    candidates = list(range(len(target_formation)))
    candidates.sort(
        key=lambda sprite_idx: math.sqrt(
            (target_formation[sprite_idx].center_x - center_x) ** 2
            + (target_formation[sprite_idx].center_y - center_y) ** 2
        )
    )

    wave_assignments = []  # List of dicts, each dict maps sprite_idx to spawn_idx

    while candidates:
        current_wave_assignments = {}  # sprite_idx -> spawn_idx for current wave
        remaining_candidates = []
        used_spawns = set()

        # Try to assign each candidate to the current wave
        for sprite_idx in candidates:
            target_pos = (target_formation[sprite_idx].center_x, target_formation[sprite_idx].center_y)

            # Calculate distances to all spawn positions and sort by distance
            spawn_distances = []
            for spawn_idx, spawn_pos in enumerate(spawn_positions):
                distance = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
                spawn_distances.append((distance, spawn_idx))

            # Sort by distance (closest first)
            spawn_distances.sort(key=lambda x: x[0])

            # Try each spawn position in order of preference (closest first)
            assigned = False

            # Group spawn positions by distance to handle ties randomly
            distance_groups = {}
            for distance, spawn_idx in spawn_distances:
                if distance not in distance_groups:
                    distance_groups[distance] = []
                distance_groups[distance].append(spawn_idx)

            # Try each distance group, shuffling within each group for random tie-breaking
            for distance in sorted(distance_groups.keys()):
                spawn_indices = distance_groups[distance]
                import random

                random.shuffle(spawn_indices)  # Random tie-breaking (Rule 4)

                for spawn_idx in spawn_indices:
                    # Skip if this spawn position is already used in current wave
                    if spawn_idx in used_spawns:
                        continue

                    # Check for path intersections during movement (Rule 5)
                    would_collide = False
                    sprite = target_formation[sprite_idx]
                    sprite_width = sprite.width if hasattr(sprite, "width") else 64
                    sprite_height = sprite.height if hasattr(sprite, "height") else 64

                    current_spawn = spawn_positions[spawn_idx]
                    current_target = (sprite.center_x, sprite.center_y)

                    for other_sprite_idx, other_spawn_idx in current_wave_assignments.items():
                        other_sprite = target_formation[other_sprite_idx]
                        other_width = other_sprite.width if hasattr(other_sprite, "width") else 64
                        other_height = other_sprite.height if hasattr(other_sprite, "height") else 64

                        other_spawn = spawn_positions[other_spawn_idx]
                        other_target = (other_sprite.center_x, other_sprite.center_y)

                        # Check if movement paths would intersect
                        if _paths_would_intersect(
                            current_spawn,
                            current_target,
                            sprite_width,
                            sprite_height,
                            other_spawn,
                            other_target,
                            other_width,
                            other_height,
                        ):
                            would_collide = True
                            break

                    # If no collisions found, assign this spawn position
                    if not would_collide:
                        current_wave_assignments[sprite_idx] = spawn_idx
                        used_spawns.add(spawn_idx)
                        assigned = True
                        break

                # If we found a valid assignment, don't try further distance groups
                if assigned:
                    break

            # If we couldn't assign any spawn position without collisions, move to next wave
            if not assigned:
                remaining_candidates.append(sprite_idx)

        # Add the current wave assignments to the list
        if current_wave_assignments:
            wave_assignments.append(current_wave_assignments)

        # Put remaining candidates back for the next iteration
        candidates = remaining_candidates

        # If no assignments were made in this wave, we need to handle remaining candidates
        if not current_wave_assignments and remaining_candidates:
            # Add remaining candidates as separate single-sprite waves to avoid infinite loop
            for sprite_idx in remaining_candidates:
                # Find the closest available spawn position for each sprite
                target_pos = (target_formation[sprite_idx].center_x, target_formation[sprite_idx].center_y)
                closest_spawn = 0
                min_distance = float("inf")
                for spawn_idx, spawn_pos in enumerate(spawn_positions):
                    distance = math.hypot(target_pos[0] - spawn_pos[0], target_pos[1] - spawn_pos[1])
                    if distance < min_distance:
                        min_distance = distance
                        closest_spawn = spawn_idx
                wave_assignments.append({sprite_idx: closest_spawn})
            break

    return wave_assignments
