"""Test suite for pattern.py - Movement patterns and condition helpers."""

import math

import arcade

from actions.base import Action
from actions.composite import sequence
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
        """Test basic orbit pattern creation."""
        pattern = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=True)

        # The new orbit pattern returns an InfiniteOrbitAction, not a path-based action
        assert hasattr(pattern, "center_x")
        assert hasattr(pattern, "center_y")
        assert hasattr(pattern, "radius")
        assert pattern.center_x == 400
        assert pattern.center_y == 300
        assert pattern.radius == 120

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

        # Apply infinite orbit with rotation enabled
        orbit = create_orbit_pattern(center=center, radius=radius, speed=120.0, clockwise=True)
        orbit.apply(sprite)

        dt = 1 / 60  # 60 FPS simulation step
        angles = []

        # Capture data for multiple revolutions
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

        # A sudden rotation discontinuity would show as a large angle change
        # For a smooth orbit, the maximum change should be small (< 1 degree)
        assert max_angle_change < 1.0, (
            f"Rotation discontinuity detected: max angle change {max_angle_change:.4f}° > 1.0°"
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

        # Apply infinite orbit
        orbit = create_orbit_pattern(center=center, radius=radius, speed=120.0, clockwise=True)
        orbit.apply(sprite)

        dt = 1 / 60  # 60 FPS simulation step
        step_sizes = []
        prev_pos = (sprite.center_x, sprite.center_y)

        # Capture movement data for multiple revolutions
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
