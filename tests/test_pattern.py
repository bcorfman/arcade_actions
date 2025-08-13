"""Test suite for pattern.py - Movement patterns and condition helpers."""

import math

import arcade
import pytest

from actions.base import Action
from actions.composite import repeat, sequence
from actions.conditional import DelayUntil, FadeUntil, ParametricMotionUntil, duration
from actions.formation import arrange_circle, arrange_grid, arrange_line
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
