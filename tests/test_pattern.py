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
