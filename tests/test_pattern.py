"""Test suite for pattern.py - Movement patterns and condition helpers."""

import math

import arcade
import pytest

from actions.base import Action
from actions.composite import repeat, sequence
from actions.conditional import DelayUntil, FadeUntil, ParametricMotionUntil, duration
from actions.formation import arrange_circle, arrange_grid, arrange_line
from actions.instant import MoveBy, MoveTo
from actions.pattern import (
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_orbit_pattern,
    create_patrol_pattern,
    create_spiral_pattern,
    create_wave_pattern,
    create_zigzag_pattern,
    sprite_count,
    time_elapsed,
)


def create_test_sprite() -> arcade.Sprite:  # type: ignore
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


class TestZigzagPattern:
    """Test suite for zigzag movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_create_zigzag_pattern_basic(self):
        """Zig-zag factory should return a single ParametricMotionUntil action."""
        pattern = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=4)

        from actions.conditional import ParametricMotionUntil

        assert isinstance(pattern, ParametricMotionUntil)

    def test_create_zigzag_pattern_application(self):
        """Test applying zigzag pattern to sprite."""
        sprite = create_test_sprite()
        initial_pos = (sprite.center_x, sprite.center_y)

        pattern = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=2)
        pattern.apply(sprite, tag="zigzag_test")

        # Start the action and update a few frames
        Action.update_all(0.1)

        # Sprite position should have changed (relative motion)
        assert (sprite.center_x, sprite.center_y) != initial_pos

    def test_zigzag_segment_alignment(self):
        """Test that zigzag segments connect smoothly without jumps."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x
        initial_y = sprite.center_y

        # Create a zigzag with 3 segments to test multiple direction changes
        pattern = create_zigzag_pattern(dimensions=(80, 40), speed=200, segments=3)
        pattern.apply(sprite, tag="zigzag_alignment_test")

        # Track positions at key points to verify smooth transitions
        positions = []

        # Simulate the movement and record positions at segment boundaries
        while not pattern.done:
            Action.update_all(1 / 60)  # 60 FPS simulation

            # Record position every 0.1 seconds (roughly every 6 frames)
            if len(positions) == 0 or (sprite.center_y - positions[-1][1]) >= 4:  # ~4 pixels up
                positions.append((sprite.center_x, sprite.center_y))

        # Should have recorded positions at each segment boundary
        assert len(positions) >= 3, f"Expected at least 3 positions, got {len(positions)}"

        # Verify the pattern spans the expected width
        # The zigzag should span approximately the specified width (80 pixels)
        x_positions = [pos[0] for pos in positions]
        min_x = min(x_positions)
        max_x = max(x_positions)

        # Pattern should span approximately the expected width
        # Note: The current implementation doesn't guarantee centering around the starting position
        # It starts from the current position and moves in the specified dimensions
        expected_width = 80
        actual_width = max_x - min_x
        assert actual_width >= expected_width * 0.8, (
            f"Pattern too narrow: expected at least {expected_width * 0.8}, got {actual_width}"
        )

        # Verify Y movement is continuous (no jumps)
        y_positions = [pos[1] for pos in positions]
        for i in range(1, len(y_positions)):
            # Each step should move upward by approximately the segment height
            y_step = y_positions[i] - y_positions[i - 1]
            assert y_step > 0, f"Y movement should always be positive, got {y_step}"
            assert y_step <= 50, f"Y step too large, got {y_step}"  # Allow some tolerance

    # Segment-count specific tests are no longer required because the factory
    # now produces a single parametric action regardless of segment count.


class TestSpiralPattern:
    """Test suite for spiral movement pattern."""

    @pytest.fixture
    def sprite(self):
        """Create a test sprite."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        return sprite

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_create_spiral_pattern_outward(self):
        """Test outward spiral pattern creation."""

        pattern = create_spiral_pattern(
            center=(400, 300), max_radius=150, revolutions=2.0, speed=200, direction="outward"
        )

        assert hasattr(pattern, "control_points")
        points = pattern.control_points

        # First point should be near center (small radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Outward spiral should end farther from center than it starts
        assert last_dist > first_dist

    def test_create_spiral_pattern_inward(self):
        """Test inward spiral pattern creation."""
        pattern = create_spiral_pattern(
            center=(400, 300), max_radius=150, revolutions=2.0, speed=200, direction="inward"
        )

        points = pattern.control_points

        # First point should be far from center (large radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Inward spiral should end closer to center than it starts
        assert last_dist < first_dist

    def test_create_spiral_pattern_application(self):
        """Test applying spiral pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_spiral_pattern(center=(200, 200), max_radius=100, revolutions=1.5, speed=150)
        pattern.apply(sprite, tag="spiral_test")

        assert pattern.target == sprite

    def test_outward_spiral_endpoints(self, sprite):
        """Test that outward spiral starts at center and ends at max radius."""
        center = (100, 100)
        max_radius = 50
        revolutions = 2
        speed = 100

        # Create outward spiral
        outward = create_spiral_pattern(center, max_radius, revolutions, speed, "outward")
        outward.apply(sprite)

        # Record initial position (should be at center)
        initial_x = sprite.center_x
        initial_y = sprite.center_y

        # Simulate until spiral completes
        while not outward.done:
            Action.update_all(1 / 60)  # 60 FPS

        # Final position should be at max radius from center
        final_x = sprite.center_x
        final_y = sprite.center_y
        final_distance = math.sqrt((final_x - center[0]) ** 2 + (final_y - center[1]) ** 2)

        # Check that we started at center
        assert abs(initial_x - center[0]) < 1.0
        assert abs(initial_y - center[1]) < 1.0

        # Check that we ended near max radius
        assert abs(final_distance - max_radius) < 5.0  # Allow some tolerance

    def test_inward_spiral_endpoints(self, sprite):
        """Test that inward spiral should start at max radius and end at center."""
        center = (100, 100)
        max_radius = 50
        revolutions = 2
        speed = 100

        # Position sprite at max radius (where outward spiral would end)
        sprite.center_x = center[0] + max_radius
        sprite.center_y = center[1]

        # Create inward spiral
        inward = create_spiral_pattern(center, max_radius, revolutions, speed, "inward")
        inward.apply(sprite)

        # Record initial position (should be at max radius)
        initial_x = sprite.center_x
        initial_y = sprite.center_y
        initial_distance = math.sqrt((initial_x - center[0]) ** 2 + (initial_y - center[1]) ** 2)

        # Simulate until spiral completes
        while not inward.done:
            Action.update_all(1 / 60)  # 60 FPS

        # Final position should be at center
        final_x = sprite.center_x
        final_y = sprite.center_y

        # Check that we started at max radius
        assert abs(initial_distance - max_radius) < 1.0

        # Check that we ended at center
        assert abs(final_x - center[0]) < 1.0
        assert abs(final_y - center[1]) < 1.0

    def test_spiral_sequence_position_continuity(self, sprite):
        """Test that position is continuous between outward and inward spirals."""
        center = (100, 100)
        max_radius = 50
        revolutions = 2
        speed = 100

        # Create spiral sequence
        outward = create_spiral_pattern(center, max_radius, revolutions, speed, "outward")
        inward = create_spiral_pattern(center, max_radius, revolutions, speed, "inward")
        spiral_cycle = sequence(outward, inward)
        spiral_cycle.apply(sprite)

        positions = []
        angles = []

        # Record positions throughout the sequence
        while not spiral_cycle.done:
            positions.append((sprite.center_x, sprite.center_y))
            angles.append(sprite.angle)
            Action.update_all(1 / 60)  # 60 FPS

        # Find the transition point (where outward ends and inward begins)
        # This should be when we're at maximum distance from center
        distances = [math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) for x, y in positions]
        max_distance_idx = distances.index(max(distances))

        # Check for position continuity around the transition
        if max_distance_idx > 0 and max_distance_idx < len(positions) - 1:
            prev_pos = positions[max_distance_idx - 1]
            curr_pos = positions[max_distance_idx]
            next_pos = positions[max_distance_idx + 1]

            # Position jump between frames should be small (smooth movement)
            jump1 = math.sqrt((curr_pos[0] - prev_pos[0]) ** 2 + (curr_pos[1] - prev_pos[1]) ** 2)
            jump2 = math.sqrt((next_pos[0] - curr_pos[0]) ** 2 + (next_pos[1] - curr_pos[1]) ** 2)

            # Both jumps should be similar (no sudden position change)
            assert abs(jump1 - jump2) < 10.0, f"Position discontinuity detected: {jump1} vs {jump2}"

    def test_spiral_sequence_rotation_continuity(self, sprite):
        """Test that rotation is continuous between outward and inward spirals."""
        center = (100, 100)
        max_radius = 50
        revolutions = 2
        speed = 100

        # Create spiral sequence
        outward = create_spiral_pattern(center, max_radius, revolutions, speed, "outward")
        inward = create_spiral_pattern(center, max_radius, revolutions, speed, "inward")
        spiral_cycle = sequence(outward, inward)
        spiral_cycle.apply(sprite)

        angles = []
        positions = []

        # Record angles throughout the sequence
        while not spiral_cycle.done:
            angles.append(sprite.angle)
            positions.append((sprite.center_x, sprite.center_y))
            Action.update_all(1 / 60)  # 60 FPS

        # Find the transition point
        distances = [math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) for x, y in positions]
        max_distance_idx = distances.index(max(distances))

        # Check for rotation continuity around the transition
        if max_distance_idx > 1 and max_distance_idx < len(angles) - 2:
            # Get angles around transition point
            angle_before = angles[max_distance_idx - 1]
            angle_at = angles[max_distance_idx]
            angle_after = angles[max_distance_idx + 1]

            # Normalize angles to [0, 360)
            def normalize_angle(angle):
                return angle % 360

            angle_before = normalize_angle(angle_before)
            angle_at = normalize_angle(angle_at)
            angle_after = normalize_angle(angle_after)

            # Calculate angle changes
            def angle_diff(a1, a2):
                diff = abs(a1 - a2)
                return min(diff, 360 - diff)

            change1 = angle_diff(angle_at, angle_before)
            change2 = angle_diff(angle_after, angle_at)

            # Rotation changes should be similar (no sudden rotation jump)
            assert abs(change1 - change2) < 30.0, f"Rotation discontinuity detected: {change1} vs {change2}"

    def test_path_reversal_property(self):
        """Test that inward spiral follows the exact reverse path of outward spiral."""
        center = (100, 100)
        max_radius = 50
        revolutions = 2
        speed = 100

        # Create both spirals
        outward = create_spiral_pattern(center, max_radius, revolutions, speed, "outward")
        inward = create_spiral_pattern(center, max_radius, revolutions, speed, "inward")

        # Get control points
        outward_points = outward.control_points
        inward_points = inward.control_points

        # For true reversal, inward points should be outward points in reverse order
        expected_inward_points = list(reversed(outward_points))

        # Check if inward points match reversed outward points
        points_match = True
        for i, (expected, actual) in enumerate(zip(expected_inward_points, inward_points, strict=False)):
            distance = math.sqrt((expected[0] - actual[0]) ** 2 + (expected[1] - actual[1]) ** 2)
            if distance > 1.0:  # Allow small tolerance
                points_match = False
                break

        assert points_match, "Inward spiral should follow exact reverse path of outward spiral"


class TestFigureEightPattern:
    """Test suite for figure-8 movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_create_figure_eight_pattern_basic(self):
        """Test basic figure-8 pattern creation."""
        pattern = create_figure_eight_pattern(center=(400, 300), width=200, height=100, speed=180)

        assert hasattr(pattern, "control_points")
        assert len(pattern.control_points) == 17  # 16 + 1 to complete loop

    def test_create_figure_eight_pattern_symmetry(self):
        """Test that figure-8 pattern has approximate symmetry."""
        pattern = create_figure_eight_pattern(center=(400, 300), width=200, height=100, speed=180)
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
        Action.stop_all()

    def test_create_orbit_pattern_basic(self):
        """Test basic orbit pattern creation returns a finite action."""
        pattern = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=True)

        # Should be a finite action that can be applied and completes
        sprite = create_test_sprite()
        start_pos = (sprite.center_x, sprite.center_y)
        pattern.apply(sprite)
        # Simulate until completion (one orbit)
        _simulate_until_done(pattern, max_steps=600)
        # Should end where it started if the sprite began on the orbit circle
        # Move sprite onto circle and re-run quick check
        sprite.center_x, sprite.center_y = (400 + 120, 300)
        pat2 = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=True)
        pat2.apply(sprite)
        _simulate_until_done(pat2, max_steps=600)
        assert math.isclose(sprite.center_x, 400 + 120, abs_tol=1e-3)
        assert math.isclose(sprite.center_y, 300, abs_tol=1e-3)

    def test_orbit_pattern_rotation_continuity(self):
        """Test that orbit pattern rotation is continuous without sudden angle jumps.

        This test specifically checks for rotation discontinuities that cause visual
        stutter when rotate_with_path=True.
        """
        import statistics

        sprite = create_test_sprite()
        center = (0.0, 0.0)
        radius = 50.0

        # Start the sprite on the right-most point of the circle
        sprite.center_x = center[0] + radius
        sprite.center_y = center[1]
        sprite.angle = 0.0  # Start with known angle

        # Apply repeating single-orbit with rotation enabled to test seamless loops
        orbit_single = create_orbit_pattern(center=center, radius=radius, speed=120.0, clockwise=True)
        orbit = repeat(orbit_single)
        orbit.apply(sprite)

        dt = 1 / 60  # 60 FPS simulation step
        angles = []

        # Capture data for multiple revolutions (via repeat)
        for _ in range(300):  # ~5 seconds at 60fps
            Action.update_all(dt)
            angles.append(sprite.angle)

        # Check for sudden angle changes (discontinuities)
        angle_changes = []
        for i in range(1, len(angles)):
            # Calculate smallest angle difference (accounting for wrap-around)
            diff = angles[i] - angles[i - 1]
            # Normalize to [-180, 180] range
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360
            angle_changes.append(abs(diff))

        max_angle_change = max(angle_changes)
        median_angle_change = statistics.median(angle_changes)

        # Calculate expected angle change per frame for smooth motion
        # Angular velocity = speed / radius = 120 / 50 = 2.4 rad/s = 137.5 deg/s
        # At 60 FPS: expected change = 137.5 / 60 = 2.29 degrees per frame
        speed = 120.0  # From test parameters
        expected_change_per_frame = (speed / radius) * (180 / math.pi) / 60

        # Allow for small variations but detect large discontinuities
        # Smooth motion should be within 20% of expected
        assert max_angle_change < expected_change_per_frame * 1.2, (
            f"Rotation discontinuity detected: max change {max_angle_change:.4f}° > "
            f"expected {expected_change_per_frame:.4f}° * 1.2"
        )

        # Additional check: if we have meaningful rotation, changes should be reasonably consistent
        if median_angle_change > 0.01:  # Only check ratio if median is significant
            assert max_angle_change < median_angle_change * 5.0, (
                f"Rotation inconsistency: max change {max_angle_change:.4f}° is "
                f"{max_angle_change / median_angle_change:.1f}x the median {median_angle_change:.4f}°"
            )

    def test_orbit_pattern_position_continuity(self):
        """Test that orbit pattern position movement is continuous without stutters."""
        import statistics

        sprite = create_test_sprite()
        center = (0.0, 0.0)
        radius = 50.0

        # Start the sprite on the right-most point of the circle
        sprite.center_x = center[0] + radius
        sprite.center_y = center[1]

        # Apply repeating single-orbit to test seamless loops
        orbit_single = create_orbit_pattern(center=center, radius=radius, speed=120.0, clockwise=True)
        orbit = repeat(orbit_single)
        orbit.apply(sprite)

        dt = 1 / 60  # 60 FPS simulation step
        step_sizes = []
        prev_pos = (sprite.center_x, sprite.center_y)

        # Capture movement data for multiple revolutions (via repeat)
        for _ in range(300):  # ~5 seconds at 60fps
            Action.update_all(dt)
            cur_pos = (sprite.center_x, sprite.center_y)
            dx = cur_pos[0] - prev_pos[0]
            dy = cur_pos[1] - prev_pos[1]
            step_sizes.append(math.hypot(dx, dy))
            prev_pos = cur_pos

        # Remove first frame (initialization)
        step_sizes = step_sizes[1:]

        median_step = statistics.median(step_sizes)
        min_step = min(step_sizes)

        # Very strict continuity check - any frame with <80% of median step indicates stutter
        assert min_step > median_step * 0.8, (
            f"Position stutter detected: min step {min_step:.4f} < 80% of median {median_step:.4f}"
        )

    def test_orbit_pattern_single_orbit_completes(self):
        """Single orbit completes and returns to starting point on the circle."""
        sprite = create_test_sprite()
        center = (100.0, 100.0)
        radius = 40.0

        # Place sprite on right-most point of the circle
        sprite.center_x = center[0] + radius
        sprite.center_y = center[1]
        start_pos = (sprite.center_x, sprite.center_y)

        orbit = create_orbit_pattern(center=center, radius=radius, speed=120.0, clockwise=True)
        orbit.apply(sprite)

        _simulate_until_done(orbit, max_steps=600)

        assert math.isclose(sprite.center_x, start_pos[0], abs_tol=1e-3)
        assert math.isclose(sprite.center_y, start_pos[1], abs_tol=1e-3)


class TestBouncePattern:
    """Test suite for bounce movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

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
        Action.stop_all()

    def test_create_patrol_pattern_basic(self):
        """Test basic patrol pattern creation."""
        start_pos = (100, 200)
        end_pos = (500, 200)

        pattern = create_patrol_pattern(start_pos, end_pos, 120)

        # Should return a MoveUntil action with bounce behavior (like create_bounce_pattern)
        assert hasattr(pattern, "boundary_behavior")
        assert pattern.boundary_behavior == "bounce"
        assert hasattr(pattern, "bounds")

    def test_create_patrol_pattern_distance_calculation(self):
        """Test that patrol pattern calculates distances correctly."""
        # Horizontal patrol
        start_pos = (100, 200)
        end_pos = (300, 200)  # 200 pixels apart

        pattern = create_patrol_pattern(start_pos, end_pos, 100)  # 100 px/s

        # Should create a single MoveUntil action with boundaries
        assert hasattr(pattern, "bounds")
        left, bottom, right, top = pattern.bounds
        assert left == 100  # min of start/end x
        assert right == 300  # max of start/end x

    def test_create_patrol_pattern_diagonal(self):
        """Test patrol pattern with diagonal movement."""
        start_pos = (100, 100)
        end_pos = (200, 200)  # Diagonal movement

        pattern = create_patrol_pattern(start_pos, end_pos, 100)

        # Should create a single MoveUntil action with boundary bouncing
        assert hasattr(pattern, "boundary_behavior")
        assert pattern.boundary_behavior == "bounce"


class TestPatternIntegration:
    """Test suite for integration between patterns and other actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_pattern_with_sprite_list(self):
        """Test applying patterns to sprite lists."""

        # Create formation
        sprites = arrange_line(count=3, start_x=100, start_y=200, spacing=50)

        # Apply wave pattern to entire formation
        wave = create_wave_pattern(amplitude=30, length=300, speed=150)
        wave.apply(sprites, tag="formation_wave")

        assert wave.target == sprites

    def test_pattern_composition(self):
        """Test composing patterns with other actions."""
        sprite = create_test_sprite()

        # Create a complex sequence: delay, then zigzag, then fade
        complex_action = sequence(
            DelayUntil(duration(0.5)),
            create_zigzag_pattern(dimensions=(80, 40), speed=120, segments=3),
            FadeUntil(-20, duration(2.0)),
        )

        complex_action.apply(sprite, tag="complex_sequence")

        # Should be a valid sequence
        assert hasattr(complex_action, "actions")
        assert len(complex_action.actions) == 3

    def test_instant_move_to_and_by(self):
        sprite = create_test_sprite()

        # MoveTo absolute (tuple form)
        MoveTo((250, 260)).apply(sprite)
        assert sprite.center_x == 250
        assert sprite.center_y == 260

        # MoveBy relative (tuple form)
        MoveBy((10, -20)).apply(sprite)
        assert sprite.center_x == 260
        assert sprite.center_y == 240

        # MoveTo absolute (separate args form)
        MoveTo(300, 350).apply(sprite)
        assert sprite.center_x == 300
        assert sprite.center_y == 350

        # MoveBy relative (separate args form)
        MoveBy(-50, 25).apply(sprite)
        assert sprite.center_x == 250
        assert sprite.center_y == 375

    def test_pattern_with_conditions(self):
        """Test patterns with condition helpers."""
        sprite_list = create_test_sprite_list(5)

        # Create a spiral that stops when few sprites remain
        spiral = create_spiral_pattern(center=(400, 300), max_radius=100, revolutions=2, speed=150)

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
        wave = create_wave_pattern(amplitude=20, length=200, speed=100)
        spiral = create_spiral_pattern(center=(300, 300), max_radius=80, revolutions=1, speed=120)

        wave.apply(sprite, tag="wave_movement")
        spiral.apply(sprite, tag="spiral_movement")  # This will override the wave

        # Most recent action should be active
        spiral_actions = Action.get_actions_for_target(sprite, "spiral_movement")
        assert len(spiral_actions) == 1

    def test_formation_functions_visible_parameter(self):
        """Test that formation functions respect the visible parameter."""
        # Test arrange_line with visible=False
        line_hidden = arrange_line(count=3, start_x=100, start_y=200, visible=False)
        for sprite in line_hidden:
            assert not sprite.visible

        # Test arrange_line with visible=True (default)
        line_visible = arrange_line(count=3, start_x=100, start_y=200, visible=True)
        for sprite in line_visible:
            assert sprite.visible

        # Test arrange_grid with visible=False
        grid_hidden = arrange_grid(rows=2, cols=2, start_x=100, start_y=200, visible=False)
        for sprite in grid_hidden:
            assert not sprite.visible

        # Test arrange_circle with visible=False
        circle_hidden = arrange_circle(count=4, center_x=200, center_y=200, radius=50, visible=False)
        for sprite in circle_hidden:
            assert not sprite.visible


# ------------------ ParametricMotionUntil & Wave pattern (new API) ------------------

import pytest

try:
    import arcade
except ImportError:  # pragma: no cover
    arcade = None  # Skip tests if arcade unavailable

pytestmark = pytest.mark.skipif(arcade is None, reason="arcade library not available")


def _simulate_until_done(action, max_steps=300, dt=1 / 60):
    steps = 0
    while not action.done and steps < max_steps:
        Action.update_all(dt)
        steps += 1
    assert action.done


def test_parametric_motion_single_sprite_new():
    sprite = arcade.Sprite()
    sprite.center_x = 20
    sprite.center_y = 30
    dx, dy = 100, 50

    def offset(t):
        return dx * t, dy * t

    act = ParametricMotionUntil(offset, duration(1.0)).apply(sprite)
    _simulate_until_done(act, max_steps=65)
    assert math.isclose(sprite.center_x, 20 + dx, abs_tol=1e-3)
    assert math.isclose(sprite.center_y, 30 + dy, abs_tol=1e-3)


def test_wave_pattern_sprite_list_new():
    sprites = arcade.SpriteList()
    originals = [(0, 0), (50, 25), (-80, -30)]
    for x, y in originals:
        s = arcade.Sprite()
        s.center_x, s.center_y = x, y
        sprites.append(s)

    amplitude, length, speed = 10, 60, 60
    act = create_wave_pattern(amplitude, length, speed).apply(sprites)
    # Wave pattern timing: half wave (length/2/speed) + full wave (2*length/speed) = 2.5*length/speed
    total_time = 2.5 * length / speed
    _simulate_until_done(act, max_steps=int(total_time * 60 + 5))

    for (ox, oy), spr in zip(originals, sprites, strict=False):
        assert math.isclose(spr.center_x, ox, abs_tol=1e-3)
        assert math.isclose(spr.center_y, oy, abs_tol=1e-3)


def test_wave_sequence_returns_origin():
    sprite = arcade.Sprite()
    sprite.center_x, sprite.center_y = 100, 200
    wave = create_wave_pattern(15, 40, 40)
    from actions.composite import sequence

    seq = sequence(wave.clone(), wave.clone()).apply(sprite)
    # Two wave patterns: each takes 2.5*length/speed time
    total_time = 2 * 2.5 * 40 / 40
    _simulate_until_done(seq, max_steps=int(total_time * 60 + 5))
    assert math.isclose(sprite.center_x, 100, abs_tol=1e-3)
    assert math.isclose(sprite.center_y, 200, abs_tol=1e-3)


# ------------------ ParametricMotionUntil mid-cycle stop and _Repeat restart continuity ------------------


def _run_frames(frames: int) -> None:
    for _ in range(frames):
        Action.update_all(1 / 60)


def test_parametric_midcycle_stop_stays_at_current_position():
    # Setup
    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Full wave returns to origin at end
    full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
    full_wave.apply(sprite, tag="midcycle")

    # Advance part-way (not near end)
    _run_frames(45)  # ~0.75s
    assert not full_wave.done

    # Record position before forced stop
    pos_before_stop = (sprite.center_x, sprite.center_y)

    # Force early completion via condition override that returns True now
    # Replace condition with immediate true so base Action.update triggers remove_effect
    full_wave.condition = lambda: True
    Action.update_all(0)  # Trigger evaluation

    # After early stop, sprite should stay at its current position (no snapping)
    # This behavior was changed to prevent jumps in repeated wave patterns
    assert abs(sprite.center_x - pos_before_stop[0]) < 1e-3
    assert abs(sprite.center_y - pos_before_stop[1]) < 1e-3


def test_repeat_restart_no_offset_after_midcycle_stop():
    # Setup
    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
    rep = repeat(full_wave)
    rep.apply(sprite, tag="repeat_midcycle")

    # Let it complete a couple cycles normally
    _run_frames(400)
    pos_before = (sprite.center_x, sprite.center_y)

    # Force mid-cycle completion of current inner action
    current = rep.current_action
    assert current is not None
    # Replace its condition with immediate true to simulate premature stop
    current.condition = lambda: True
    Action.update_all(0)
    pos_after_stop = (sprite.center_x, sprite.center_y)

    # Immediately after, _Repeat should start a fresh iteration
    # Run one frame to allow restart
    _run_frames(1)
    pos_after_restart = (sprite.center_x, sprite.center_y)

    # Positions should not jump by a large amount due to offset mismatch
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    # Snap-to-end ensures no extreme discontinuity at stop moment
    assert dist(pos_before, pos_after_stop) < 90  # strictly bounded (wave span is 80)

    # Restart should not produce a huge jump; allow small movement
    assert dist(pos_after_stop, pos_after_restart) < 15


class TestDemoPatrolPattern:
    """Tests mirroring the patrol demo behavior in examples.pattern_demo._create_patrol_demo."""

    def teardown_method(self):
        Action.stop_all()

    def test_patrol_demo_quarter_then_full_positions(self):
        sprite = arcade.Sprite()
        center_x, center_y = 200.0, 150.0
        sprite.center_x = center_x
        sprite.center_y = center_y

        # As in the demo: start/end 30px left/right of center, speed=2 px/frame
        start_pos = (center_x - 30.0, center_y)
        end_pos = (center_x + 30.0, center_y)

        quarter_patrol = create_patrol_pattern(start_pos, end_pos, speed=2, start_progress=0.75, end_progress=1.0)
        full_patrol = create_patrol_pattern(start_pos, end_pos, speed=2)

        seq = sequence(quarter_patrol, full_patrol)
        seq.apply(sprite)

        dt = 1 / 60

        def advance(seconds: float):
            steps = int(round(seconds / dt))
            for _ in range(steps):
                Action.update_all(dt)
                sprite.update()  # Apply Arcade velocities

        # Durations based on create_patrol_pattern semantics
        distance = math.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])  # 60px
        speed_px_per_frame = 2.0
        travel_time = (distance / speed_px_per_frame) / 60.0  # time for one leg

        quarter_duration = travel_time * 0.5  # progress 0.75 -> 1.0 = last half of return leg
        forward_leg = travel_time

        # After quarter_patrol: center -> start_pos (allow small systematic offset)
        advance(quarter_duration)
        assert abs(sprite.center_x - start_pos[0]) < 5.0, f"Quarter patrol end: {sprite.center_x} vs {start_pos[0]}"
        assert math.isclose(sprite.center_y, start_pos[1], abs_tol=1e-3)

        # First half of full_patrol: start_pos -> end_pos
        advance(forward_leg)
        assert abs(sprite.center_x - end_pos[0]) < 5.0, f"Forward leg end: {sprite.center_x} vs {end_pos[0]}"
        assert math.isclose(sprite.center_y, end_pos[1], abs_tol=1e-3)

        # Second half of full_patrol: end_pos -> start_pos
        advance(travel_time)
        assert abs(sprite.center_x - start_pos[0]) < 5.0, f"Return leg end: {sprite.center_x} vs {start_pos[0]}"
        assert math.isclose(sprite.center_y, start_pos[1], abs_tol=1e-3)

        # Entire sequence should now be complete (full_patrol is finite)
        # Give a bit more time in case of rounding errors
        advance(travel_time * 0.1)  # Extra 10% time for completion
        assert seq.done

    def test_patrol_demo_boundaries_stable_over_repeats(self):
        """Patrol demo should bounce reliably within boundaries without going past them.

        Boundary bouncing ensures sprites never exceed boundaries, with precision
        varying naturally based on speed (faster = less precise boundary hits).
        """
        sprite = arcade.Sprite()
        center_x, center_y = 200.0, 150.0
        sprite.center_x = center_x
        sprite.center_y = center_y

        start_pos = (center_x - 40.0, center_y)  # (160, 150)
        end_pos = (center_x + 40.0, center_y)  # (240, 150)

        quarter_patrol = create_patrol_pattern(start_pos, end_pos, speed=2, start_progress=0.75, end_progress=1.0)
        full_patrol = create_patrol_pattern(start_pos, end_pos, speed=2)
        loop = sequence(quarter_patrol, repeat(full_patrol))
        loop.apply(sprite)

        dt = 1 / 60
        left_hits: list[float] = []
        right_hits: list[float] = []
        last_dx_sign: int | None = None
        min_x = float("inf")
        max_x = float("-inf")

        # Run until we collect enough boundary data
        steps = 0
        max_steps = 10000
        while len(left_hits) + len(right_hits) < 50 and steps < max_steps:  # Reduced from 200
            prev_pos = sprite.center_x
            Action.update_all(dt)
            sprite.update()
            cur_x = sprite.center_x

            # Track extreme positions to ensure sprite stays in bounds
            min_x = min(min_x, cur_x)
            max_x = max(max_x, cur_x)

            dx = cur_x - prev_pos
            if abs(dx) > 1e-9:
                sign = 1 if dx > 0 else -1
                if last_dx_sign is not None and sign != last_dx_sign:
                    # Velocity direction change detected (boundary bounce)
                    if last_dx_sign > 0:
                        right_hits.append(cur_x)
                    else:
                        left_hits.append(cur_x)
                last_dx_sign = sign

            steps += 1

        # Primary test: sprite never goes past the boundaries
        expected_left = start_pos[0]  # 160.0
        expected_right = end_pos[0]  # 240.0

        assert min_x >= expected_left - 3.0, f"Sprite went past left boundary: {min_x} < {expected_left}"
        assert max_x <= expected_right + 3.0, f"Sprite went past right boundary: {max_x} > {expected_right}"

        # Secondary test: we should see bounces on both sides
        assert len(left_hits) > 0 and len(right_hits) > 0, f"Left: {len(left_hits)}, Right: {len(right_hits)}"

        # Boundary hit positions should be reasonably close to expected boundaries
        # (precision varies with speed, but should be within reasonable range)
        if left_hits:
            left_avg = sum(left_hits) / len(left_hits)
            assert abs(left_avg - expected_left) < 10.0, f"Left boundary too far: {left_avg} vs {expected_left}"

        if right_hits:
            right_avg = sum(right_hits) / len(right_hits)
            assert abs(right_avg - expected_right) < 10.0, f"Right boundary too far: {right_avg} vs {expected_right}"


class TestWaveRepeatContinuity:
    """Test suite for wave pattern repeat continuity to prevent large jumps."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeated_wave_motion_no_large_jump(self):
        """Ensure repeated full-wave motion never produces a single-frame jump > threshold.

        This test mirrors the enemy formation sway logic in *space_clutter.py*:
            quarter_wave  = create_wave_pattern(..., start_progress=0.75, end_progress=1.0)
            full_wave     = create_wave_pattern(...)
            repeating     = sequence(quarter_wave, repeat(full_wave))

        The bug report describes an occasional *large jump* after several cycles.
        We replicate the exact pattern for a lone sprite and verify that the
        per-frame displacement never exceeds an upper bound (1.5 × wave_length).
        """

        # Build a sprite list resembling the 4×4 enemy grid (16 sprites)
        sprites = arcade.SpriteList()
        for i in range(16):
            s = arcade.Sprite()
            # Spread initial positions horizontally to better expose any per-sprite origin issues
            s.center_x = 200.0 + (i % 4) * 15.0
            s.center_y = 300.0 + (i // 4) * 10.0
            sprites.append(s)

        # Wave parameters match the demo in space_clutter.py
        amplitude = 30.0
        length = 80.0
        speed = 80.0  # pixels per *frame* (Arcade semantics)

        quarter_wave = create_wave_pattern(
            amplitude=amplitude,
            length=length,
            speed=speed,
            start_progress=0.75,
            end_progress=1.0,
        )
        full_wave = create_wave_pattern(amplitude, length, speed)
        pattern = sequence(quarter_wave, repeat(full_wave))
        pattern.apply(sprites)

        # Run for an extended duration: 120 seconds at 60 FPS ~ 7200 frames.
        dt = 1 / 60.0
        frames_to_simulate = 7200

        # Jump threshold: allow up to 12 px movement between frames
        max_allowed_jump = 12.0

        # Track previous positions of first sprite as representative (all move identically)
        prev_x, prev_y = sprites[0].center_x, sprites[0].center_y
        for frame_idx in range(frames_to_simulate):
            # Introduce occasional frame-drop spikes (~every 397 frames, prime to avoid phase sync)
            if frame_idx % 397 == 0 and frame_idx > 0:
                Action.update_all(dt * 5)  # 5-frame drop
            else:
                Action.update_all(dt)

            cur_x, cur_y = sprites[0].center_x, sprites[0].center_y
            dx = abs(cur_x - prev_x)
            dy = abs(cur_y - prev_y)
            jump = math.hypot(dx, dy)
            assert jump <= max_allowed_jump, (
                f"Detected large single-frame jump: {jump:.2f}px (> {max_allowed_jump}px) at frame {frame_idx}"
            )
            prev_x, prev_y = cur_x, cur_y

        # Repeat should still be running (infinite) – pattern itself never completes.
        assert not pattern.done
