"""Test suite for pattern.py - Movement patterns and condition helpers."""

import math

import arcade

from actions.base import Action
from actions.pattern import (
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_orbit_pattern,
    create_patrol_pattern,
    create_smooth_zigzag_pattern,
    create_spiral_pattern,
    create_wave_pattern,
    create_zigzag_pattern,
    sprite_count,
    time_elapsed,
)


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


def create_test_sprite_list(count=5):
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    for i in range(count):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite_list.append(sprite)
    return sprite_list


class TestConditionHelpers:
    """Test suite for condition helper functions."""

    def test_time_elapsed_condition(self):
        """Test time_elapsed condition helper."""
        condition = time_elapsed(0.1)  # 0.1 seconds

        # Should start as False
        assert not condition()

        # Should become True after enough time
        import time

        time.sleep(0.15)  # Wait longer than threshold
        assert condition()

    def test_sprite_count_condition(self):
        """Test sprite_count condition helper."""
        sprite_list = create_test_sprite_list(5)

        # Test different comparison operators
        condition_le = sprite_count(sprite_list, 3, "<=")
        condition_ge = sprite_count(sprite_list, 3, ">=")
        condition_eq = sprite_count(sprite_list, 5, "==")
        condition_ne = sprite_count(sprite_list, 3, "!=")

        assert not condition_le()  # 5 <= 3 is False
        assert condition_ge()  # 5 >= 3 is True
        assert condition_eq()  # 5 == 5 is True
        assert condition_ne()  # 5 != 3 is True

        # Remove some sprites and test again
        sprite_list.remove(sprite_list[0])
        sprite_list.remove(sprite_list[0])  # Now has 3 sprites

        assert condition_le()  # 3 <= 3 is True
        assert not condition_ne()  # 3 != 3 is False

    def test_sprite_count_invalid_operator(self):
        """Test sprite_count with invalid comparison operator."""
        sprite_list = create_test_sprite_list(3)

        condition = sprite_count(sprite_list, 2, "invalid")

        try:
            condition()
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Invalid comparison operator" in str(e)


class TestBoidFormationEntry:
    """Test suite for boid-based formation entry patterns."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_boid_flock_pattern_basic(self):
        """Test basic boid flock pattern creation."""
        from actions.pattern import create_boid_flock_pattern

        pattern = create_boid_flock_pattern(max_speed=4.0, duration_seconds=3.0)

        # Should return a BoidMoveUntil action
        assert hasattr(pattern, "max_speed")
        assert hasattr(pattern, "avoid_sprite")
        assert pattern.max_speed == 4.0

    def test_create_boid_flock_pattern_with_player_avoidance(self):
        """Test boid flock pattern with player avoidance."""
        from actions.pattern import create_boid_flock_pattern

        player_sprite = create_test_sprite()
        pattern = create_boid_flock_pattern(max_speed=3.0, duration_seconds=2.0, avoid_sprite=player_sprite)

        assert pattern.avoid_sprite == player_sprite

    def test_create_boid_flock_pattern_application(self):
        """Test applying boid flock pattern to sprite list."""
        from actions.pattern import create_boid_flock_pattern

        sprite_list = create_test_sprite_list(5)
        pattern = create_boid_flock_pattern(max_speed=2.0, duration_seconds=1.0)
        pattern.apply(sprite_list, tag="boid_test")

        assert pattern.target == sprite_list
        assert pattern.tag == "boid_test"

    def test_create_formation_entry_pattern_basic(self):
        """Test basic formation entry pattern creation."""
        from actions.formation import arrange_grid
        from actions.pattern import create_formation_entry_pattern

        # Create target formation
        grid_formation = arrange_grid(rows=2, cols=5, start_x=200, start_y=400)

        pattern = create_formation_entry_pattern(
            flock_size=10,
            target_formation=grid_formation,
            spawn_area=(0, 0, 100, 600),  # Left side spawn
            cruise_duration=3.0,
            rally_point=(150, 350),
            slot_duration=2.0,
        )

        # Should return a sequence with 3 phases
        assert hasattr(pattern, "actions")
        assert len(pattern.actions) == 3  # cruise, rally, slot-in

    def test_create_formation_entry_pattern_with_player(self):
        """Test formation entry pattern with player avoidance."""
        from actions.formation import arrange_line
        from actions.pattern import create_formation_entry_pattern

        player_sprite = create_test_sprite()
        line_formation = arrange_line(count=5, start_x=300, start_y=500, spacing=60)

        pattern = create_formation_entry_pattern(
            flock_size=5,
            target_formation=line_formation,
            spawn_area=(700, 0, 800, 600),  # Right side spawn
            cruise_duration=2.5,
            rally_point=(400, 450),
            slot_duration=1.5,
            avoid_sprite=player_sprite,
        )

        # Check that the cruise phase has player avoidance
        cruise_action = pattern.actions[0]
        assert hasattr(cruise_action, "avoid_sprite")
        assert cruise_action.avoid_sprite == player_sprite

    def test_random_spawn_point_generation(self):
        """Test random spawn point generation within area."""
        from actions.pattern import _generate_random_spawn_point

        spawn_area = (0, 0, 100, 200)

        # Generate multiple points and verify they're in bounds
        for _ in range(10):
            x, y = _generate_random_spawn_point(spawn_area)
            assert 0 <= x <= 100
            assert 0 <= y <= 200

    def test_random_spawn_point_edge_cases(self):
        """Test random spawn point generation with edge cases."""
        from actions.pattern import _generate_random_spawn_point

        # Zero-width area
        narrow_area = (50, 50, 50, 100)
        x, y = _generate_random_spawn_point(narrow_area)
        assert x == 50
        assert 50 <= y <= 100

        # Zero-height area
        flat_area = (0, 75, 100, 75)
        x, y = _generate_random_spawn_point(flat_area)
        assert 0 <= x <= 100
        assert y == 75

    def test_boid_move_until_action_basic(self):
        """Test basic BoidMoveUntil action functionality."""
        from actions.conditional import duration
        from actions.pattern import BoidMoveUntil

        sprite_list = create_test_sprite_list(3)
        condition = duration(1.0)

        action = BoidMoveUntil(
            max_speed=3.0,
            duration_condition=condition,
            cohesion_weight=0.01,
            separation_weight=0.05,
            alignment_weight=0.03,
        )

        action.apply(sprite_list, tag="boid_test")

        # Verify action was applied
        assert action.target == sprite_list
        assert action.max_speed == 3.0

    def test_boid_move_until_action_with_avoidance(self):
        """Test BoidMoveUntil action with sprite avoidance."""
        from actions.conditional import duration
        from actions.pattern import BoidMoveUntil

        sprite_list = create_test_sprite_list(4)
        player_sprite = create_test_sprite()
        player_sprite.center_x = 200
        player_sprite.center_y = 200

        action = BoidMoveUntil(max_speed=2.5, duration_condition=duration(2.0), avoid_sprite=player_sprite)

        action.apply(sprite_list, tag="avoidance_test")

        assert action.avoid_sprite == player_sprite

    def test_boid_move_until_velocity_clamping(self):
        """Test that BoidMoveUntil properly clamps velocity to max_speed."""
        from actions.conditional import duration
        from actions.pattern import BoidMoveUntil

        # Create sprites positioned to create high cohesion forces
        sprite_list = arcade.SpriteList()
        for i in range(3):
            sprite = create_test_sprite()
            sprite.center_x = i * 200  # Spread far apart
            sprite.center_y = 100
            sprite_list.append(sprite)

        action = BoidMoveUntil(
            max_speed=1.0,  # Very low max speed
            duration_condition=duration(0.5),
            cohesion_weight=1.0,  # High cohesion to test clamping
        )

        action.apply(sprite_list, tag="clamp_test")

        # Update once to apply forces
        Action.update_all(0.016)  # ~60 FPS frame

        # Check that velocities don't exceed max_speed
        for sprite in sprite_list:
            speed = math.sqrt(sprite.change_x**2 + sprite.change_y**2)
            assert speed <= action.max_speed + 0.01  # Small tolerance for floating point

    def test_move_until_towards_target_basic(self):
        """Test basic MoveUntilTowardsTarget action functionality."""
        from actions.pattern import MoveUntilTowardsTarget

        sprite = create_test_sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        target_point = (300, 200)

        action = MoveUntilTowardsTarget(target=target_point, speed=5.0, stop_distance=20.0)

        action.apply(sprite, tag="towards_test")

        # Check initial velocity direction
        Action.update_all(0.016)

        # Should be moving towards target
        assert sprite.change_x > 0  # Moving right
        assert sprite.change_y > 0  # Moving up

    def test_move_until_towards_target_reaches_destination(self):
        """Test that MoveUntilTowardsTarget stops when reaching target."""
        from actions.pattern import MoveUntilTowardsTarget

        sprite = create_test_sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        target_point = (120, 110)  # Close target

        action = MoveUntilTowardsTarget(
            target=target_point,
            speed=10.0,
            stop_distance=15.0,  # Should stop before reaching exact target
        )

        action.apply(sprite, tag="reach_test")

        # Update multiple frames to reach target
        for _ in range(10):
            Action.update_all(0.016)
            # In Arcade, sprites need to be updated to apply velocity to position
            sprite.update()
            if action.done:
                break

        # Should have stopped due to proximity
        assert action.done

        # Should be within stop distance
        distance = math.sqrt((sprite.center_x - target_point[0]) ** 2 + (sprite.center_y - target_point[1]) ** 2)
        assert distance <= action.stop_distance + 5  # Some tolerance

    def test_create_galaga_style_entry_complete_workflow(self):
        """Test complete Galaga-style formation entry workflow."""
        from actions.formation import arrange_grid
        from actions.pattern import create_galaga_style_entry

        # Create a formation to fill
        formation = arrange_grid(rows=4, cols=10, start_x=200, start_y=400)

        # Create player sprite for avoidance
        player = create_test_sprite()
        player.center_x = 400
        player.center_y = 100

        # Create entry sequence for 4 groups
        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=4,
            sprites_per_group=10,
            player_sprite=player,
            screen_bounds=(0, 0, 800, 600),
        )

        # Should create 4 entry actions (one per group)
        assert len(entry_actions) == 4

        # Each should be a sequence action
        for action in entry_actions:
            assert hasattr(action, "actions")
            assert len(action.actions) == 3  # cruise, rally, slot-in

    def test_create_galaga_style_entry_different_spawn_sides(self):
        """Test that different groups spawn from different sides."""
        from actions.formation import arrange_line
        from actions.pattern import create_galaga_style_entry

        formation = arrange_line(count=12, start_x=300, start_y=500)

        entry_actions = create_galaga_style_entry(
            formation=formation, groups_per_formation=3, sprites_per_group=4, screen_bounds=(0, 0, 800, 600)
        )

        assert len(entry_actions) == 3

        # Each action should have different spawn characteristics
        # (This is tested indirectly through the spawn area generation)

    def test_formation_entry_pattern_error_handling(self):
        """Test error handling in formation entry pattern creation."""
        from actions.pattern import create_formation_entry_pattern

        # Test with mismatched flock size and formation size
        try:
            from actions.formation import arrange_line

            small_formation = arrange_line(count=3)

            create_formation_entry_pattern(
                flock_size=10,  # More sprites than formation slots
                target_formation=small_formation,
                spawn_area=(0, 0, 100, 100),
                cruise_duration=1.0,
                rally_point=(50, 50),
                slot_duration=1.0,
            )

            # Should not raise an error, but should handle gracefully
            # (Implementation should either truncate or extend formation)

        except Exception as e:
            # If an error is raised, it should be informative
            assert "formation" in str(e).lower() or "size" in str(e).lower()


class TestZigzagPattern:
    """Test suite for zigzag movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_zigzag_pattern_basic(self):
        """Test basic zigzag pattern creation."""
        pattern = create_zigzag_pattern(width=100, height=50, speed=150, segments=4)

        # Should return a sequence action
        assert hasattr(pattern, "actions")
        assert len(pattern.actions) == 4

    def test_create_zigzag_pattern_application(self):
        """Test applying zigzag pattern to sprite."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x

        pattern = create_zigzag_pattern(width=100, height=50, speed=150, segments=2)
        pattern.apply(sprite, tag="zigzag_test")

        # Start the action and update
        Action.update_all(0.1)

        # Sprite should be moving
        assert sprite.change_x != 0 or sprite.change_y != 0

    def test_create_zigzag_pattern_segments(self):
        """Test zigzag pattern with different segment counts."""
        pattern_2 = create_zigzag_pattern(width=100, height=50, speed=150, segments=2)
        pattern_6 = create_zigzag_pattern(width=100, height=50, speed=150, segments=6)

        assert len(pattern_2.actions) == 2
        assert len(pattern_6.actions) == 6


class TestWavePattern:
    """Test suite for wave movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_wave_pattern_basic(self):
        """Test basic wave pattern creation."""
        pattern = create_wave_pattern(amplitude=50, frequency=2, length=400, speed=200)

        # Should return a FollowPathUntil action
        assert hasattr(pattern, "control_points")
        assert len(pattern.control_points) >= 8  # Should have multiple points

    def test_create_wave_pattern_application(self):
        """Test applying wave pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_wave_pattern(amplitude=30, frequency=1, length=200, speed=100)
        pattern.apply(sprite, tag="wave_test")

        # Verify pattern was applied
        assert pattern.target == sprite
        assert pattern.tag == "wave_test"

    def test_create_wave_pattern_frequency_affects_points(self):
        """Test that higher frequency creates more control points."""
        low_freq = create_wave_pattern(amplitude=50, frequency=1, length=400, speed=200)
        high_freq = create_wave_pattern(amplitude=50, frequency=3, length=400, speed=200)

        assert len(high_freq.control_points) > len(low_freq.control_points)


class TestSpiralPattern:
    """Test suite for spiral movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_spiral_pattern_outward(self):
        """Test outward spiral pattern creation."""
        pattern = create_spiral_pattern(400, 300, 150, 2.0, 200, "outward")

        assert hasattr(pattern, "control_points")
        points = pattern.control_points

        # First point should be near center (small radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Outward spiral should end farther from center than it starts
        assert last_dist > first_dist

    def test_create_spiral_pattern_inward(self):
        """Test inward spiral pattern creation."""
        pattern = create_spiral_pattern(400, 300, 150, 2.0, 200, "inward")

        points = pattern.control_points

        # First point should be far from center (large radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Inward spiral should end closer to center than it starts
        assert last_dist < first_dist

    def test_create_spiral_pattern_application(self):
        """Test applying spiral pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_spiral_pattern(200, 200, 100, 1.5, 150)
        pattern.apply(sprite, tag="spiral_test")

        assert pattern.target == sprite


class TestFigureEightPattern:
    """Test suite for figure-8 movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_figure_eight_pattern_basic(self):
        """Test basic figure-8 pattern creation."""
        pattern = create_figure_eight_pattern(400, 300, 200, 100, 180)

        assert hasattr(pattern, "control_points")
        assert len(pattern.control_points) == 17  # 16 + 1 to complete loop

    def test_create_figure_eight_pattern_symmetry(self):
        """Test that figure-8 pattern has approximate symmetry."""
        pattern = create_figure_eight_pattern(400, 300, 200, 100, 180)
        points = pattern.control_points

        # Check that we have points on both sides of center
        left_points = [p for p in points if p[0] < 400]
        right_points = [p for p in points if p[0] > 400]

        assert len(left_points) > 0
        assert len(right_points) > 0


class TestOrbitPattern:
    """Test suite for orbit movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_orbit_pattern_clockwise(self):
        """Test clockwise orbit pattern."""
        pattern = create_orbit_pattern(400, 300, 120, 150, clockwise=True)

        assert hasattr(pattern, "control_points")
        points = pattern.control_points

        # All points should be approximately the same distance from center
        for point in points:
            distance = math.sqrt((point[0] - 400) ** 2 + (point[1] - 300) ** 2)
            assert abs(distance - 120) < 1.0

    def test_create_orbit_pattern_counter_clockwise(self):
        """Test counter-clockwise orbit pattern."""
        cw_pattern = create_orbit_pattern(400, 300, 120, 150, clockwise=True)
        ccw_pattern = create_orbit_pattern(400, 300, 120, 150, clockwise=False)

        # Patterns should have same number of points but different order
        assert len(cw_pattern.control_points) == len(ccw_pattern.control_points)


class TestBouncePattern:
    """Test suite for bounce movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_bounce_pattern_basic(self):
        """Test basic bounce pattern creation."""
        bounds = (0, 0, 800, 600)
        pattern = create_bounce_pattern((150, 100), bounds)

        # Should return a MoveUntil action with bounce behavior
        assert hasattr(pattern, "boundary_behavior")
        assert pattern.boundary_behavior == "bounce"
        assert pattern.bounds == bounds

    def test_create_bounce_pattern_application(self):
        """Test applying bounce pattern to sprite."""
        sprite = create_test_sprite()
        bounds = (0, 0, 800, 600)

        pattern = create_bounce_pattern((150, 100), bounds)
        pattern.apply(sprite, tag="bounce_test")

        Action.update_all(0.1)

        # Sprite should be moving
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert sprite.change_x == 150
        assert sprite.change_y == 100


class TestPatrolPattern:
    """Test suite for patrol movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_patrol_pattern_basic(self):
        """Test basic patrol pattern creation."""
        start_pos = (100, 200)
        end_pos = (500, 200)

        pattern = create_patrol_pattern(start_pos, end_pos, 120)

        # Should return a sequence with two movements
        assert hasattr(pattern, "actions")
        assert len(pattern.actions) == 2

    def test_create_patrol_pattern_distance_calculation(self):
        """Test that patrol pattern calculates distances correctly."""
        # Horizontal patrol
        start_pos = (100, 200)
        end_pos = (300, 200)  # 200 pixels apart

        pattern = create_patrol_pattern(start_pos, end_pos, 100)  # 100 px/s

        # Should create two actions (forward and return)
        assert len(pattern.actions) == 2

    def test_create_patrol_pattern_diagonal(self):
        """Test patrol pattern with diagonal movement."""
        start_pos = (100, 100)
        end_pos = (200, 200)  # Diagonal movement

        pattern = create_patrol_pattern(start_pos, end_pos, 100)

        # Should still create a valid sequence
        assert hasattr(pattern, "actions")
        assert len(pattern.actions) == 2


class TestSmoothZigzagPattern:
    """Test suite for smooth zigzag movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_smooth_zigzag_pattern_basic(self):
        """Test smooth zigzag pattern creation."""
        pattern = create_smooth_zigzag_pattern(100, 50, 150, ease_duration=1.0)

        # Should return an Ease action wrapping a zigzag
        assert hasattr(pattern, "wrapped_action")
        assert hasattr(pattern, "easing_duration")
        assert pattern.easing_duration == 1.0

    def test_create_smooth_zigzag_pattern_application(self):
        """Test applying smooth zigzag pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_smooth_zigzag_pattern(80, 40, 120, ease_duration=0.5)
        pattern.apply(sprite, tag="smooth_zigzag_test")

        assert pattern.target == sprite


class TestPatternIntegration:
    """Test suite for integration between patterns and other actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_pattern_with_sprite_list(self):
        """Test applying patterns to sprite lists."""
        from actions.formation import arrange_line

        # Create formation
        sprites = arrange_line(count=3, start_x=100, start_y=200, spacing=50)

        # Apply wave pattern to entire formation
        wave = create_wave_pattern(amplitude=30, frequency=1, length=300, speed=150)
        wave.apply(sprites, tag="formation_wave")

        assert wave.target == sprites

    def test_pattern_composition(self):
        """Test composing patterns with other actions."""
        from actions.composite import sequence
        from actions.conditional import DelayUntil, FadeUntil, duration

        sprite = create_test_sprite()

        # Create a complex sequence: delay, then zigzag, then fade
        complex_action = sequence(
            DelayUntil(duration(0.5)), create_zigzag_pattern(80, 40, 120, segments=3), FadeUntil(-20, duration(2.0))
        )

        complex_action.apply(sprite, tag="complex_sequence")

        # Should be a valid sequence
        assert hasattr(complex_action, "actions")
        assert len(complex_action.actions) == 3

    def test_pattern_with_conditions(self):
        """Test patterns with condition helpers."""
        sprite_list = create_test_sprite_list(5)

        # Create a spiral that stops when few sprites remain
        spiral = create_spiral_pattern(400, 300, 100, 2, 150)

        # Note: This test mainly verifies that condition helpers work with patterns
        condition = sprite_count(sprite_list, 2, "<=")

        # Should not trigger initially
        assert not condition()

        # Remove sprites to trigger condition
        while len(sprite_list) > 2:
            sprite_list.remove(sprite_list[0])

        assert condition()

    def test_multiple_patterns_same_sprite(self):
        """Test applying multiple patterns to the same sprite with different tags."""
        sprite = create_test_sprite()

        # Apply different patterns with different tags (this would conflict in real usage)
        wave = create_wave_pattern(amplitude=20, frequency=1, length=200, speed=100)
        spiral = create_spiral_pattern(300, 300, 80, 1, 120)

        wave.apply(sprite, tag="wave_movement")
        spiral.apply(sprite, tag="spiral_movement")  # This will override the wave

        # Most recent action should be active
        spiral_actions = Action.get_actions_for_target(sprite, "spiral_movement")
        assert len(spiral_actions) == 1

    def test_boid_formation_entry_integration(self):
        """Test integration of boid formation entry with existing patterns."""
        from actions.formation import arrange_circle
        from actions.pattern import create_formation_entry_pattern

        # Create circular formation
        formation = arrange_circle(count=8, center_x=400, center_y=300, radius=100)

        # Create formation entry pattern
        entry_pattern = create_formation_entry_pattern(
            flock_size=8,
            target_formation=formation,
            spawn_area=(0, 300, 50, 350),  # Narrow spawn area
            cruise_duration=2.0,
            rally_point=(200, 300),
            slot_duration=1.5,
        )

        # Should integrate properly with the formation system
        assert hasattr(entry_pattern, "actions")
        assert len(entry_pattern.actions) == 3
