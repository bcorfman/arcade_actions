"""Tests for exact circular loop path generation."""

import pytest
import math
import arcade
from actions.base import Action
from actions.group import AttackGroup
from actions.formation import arrange_line
from actions.conditional import FollowPathUntil, infinite
from actions.presets.entry_paths import circle_arc_waypoints, loop_the_loop_exact
from tests.conftest import ActionTestBase


class TestCircleArcWaypoints(ActionTestBase):
    """Test suite for circle_arc_waypoints function."""

    def test_circle_arc_waypoints_creates_complete_loop(self):
        """Test that circle_arc_waypoints creates a complete 360° loop."""
        cx, cy = 400, 300
        radius = 150.0

        waypoints = circle_arc_waypoints(cx, cy, radius)

        # Should have 13 points (12 control points + closing point)
        assert len(waypoints) == 13, "Circle should have 13 waypoints"

        # First and last points should be the same (complete loop)
        assert waypoints[0] == waypoints[-1], "Loop should start and end at same point"

        # First point should be at bottom (270°)
        first_x, first_y = waypoints[0]
        assert abs(first_x - cx) < 0.1, "First point should be at center X"
        assert abs(first_y - (cy - radius)) < 0.1, "First point should be at bottom"

    def test_circle_arc_waypoints_has_cardinal_points(self):
        """Test that circle waypoints include all four cardinal directions."""
        cx, cy = 400, 300
        radius = 150.0

        waypoints = circle_arc_waypoints(cx, cy, radius)

        # Check for right (0°), top (90°), left (180°), bottom (270°)
        has_right = any(abs(wp[0] - (cx + radius)) < 0.1 and abs(wp[1] - cy) < 0.1 for wp in waypoints)
        has_top = any(abs(wp[0] - cx) < 0.1 and abs(wp[1] - (cy + radius)) < 0.1 for wp in waypoints)
        has_left = any(abs(wp[0] - (cx - radius)) < 0.1 and abs(wp[1] - cy) < 0.1 for wp in waypoints)
        has_bottom = any(abs(wp[0] - cx) < 0.1 and abs(wp[1] - (cy - radius)) < 0.1 for wp in waypoints)

        assert has_right, "Circle should have a waypoint on the right"
        assert has_top, "Circle should have a waypoint at the top"
        assert has_left, "Circle should have a waypoint on the left"
        assert has_bottom, "Circle should have a waypoint at the bottom"


class TestLoopTheLoopExact(ActionTestBase):
    """Test suite for loop_the_loop_exact function."""

    def test_loop_the_loop_exact_creates_complete_path(self):
        """Test that loop_the_loop_exact creates a complete entry path."""
        start_x, start_y = 600, -100
        end_x, end_y = 200, 400
        loop_cx, loop_cy = 400, 200
        loop_radius = 150.0

        waypoints = loop_the_loop_exact(start_x, start_y, end_x, end_y, loop_cx, loop_cy, loop_radius)

        # Should have: start + approach + 13 loop points + exit + end = 17 points
        assert len(waypoints) >= 15, "Path should have at least 15 waypoints"

        # Verify start and end positions
        assert waypoints[0] == (start_x, start_y), "Path should start at start position"
        assert waypoints[-1] == (end_x, end_y), "Path should end at end position"

    def test_loop_path_actually_loops(self):
        """Test that the Bezier curve path actually forms a circular loop."""
        start_x, start_y = 400, -100
        end_x, end_y = 400, 500
        loop_cx, loop_cy = 400, 200
        loop_radius = 150.0

        waypoints = loop_the_loop_exact(start_x, start_y, end_x, end_y, loop_cx, loop_cy, loop_radius)

        # Create a FollowPathUntil action to sample the actual path
        action = FollowPathUntil(waypoints, velocity=100, condition=infinite)

        # Sample points along the path
        samples = 50
        path_points = []
        for i in range(samples + 1):
            t = i / samples
            point = action._bezier_point(t)
            path_points.append(point)

        # Check that the path forms a loop by verifying it passes through all four quadrants
        # and maintains a reasonable distance from center in the loop section
        # Loop section is roughly t=0.2 to t=0.8 (middle 60% of path, avoiding approach/exit)
        loop_section_start = 0.2
        loop_section_end = 0.8
        loop_section_indices = range(int(loop_section_start * samples), int(loop_section_end * samples))
        loop_section_points = [path_points[i] for i in loop_section_indices]

        # Calculate distances from center for points in the loop section
        distances = [math.sqrt((p[0] - loop_cx) ** 2 + (p[1] - loop_cy) ** 2) for p in loop_section_points]

        # Verify the path maintains a reasonable distance from center (at least 60% of target radius)
        # This accounts for Bezier curve approximation and approach/exit influence
        min_acceptable_radius = loop_radius * 0.6
        points_with_reasonable_radius = [d for d in distances if d >= min_acceptable_radius]

        assert len(points_with_reasonable_radius) >= len(distances) * 0.5, (
            f"At least 50% of loop points should be at least {min_acceptable_radius:.1f}px from center. Got {len(points_with_reasonable_radius)}/{len(distances)}"
        )

        # Verify the path passes through all four quadrants (proves it forms a loop)
        right_quadrant = [p for p in loop_section_points if p[0] > loop_cx and abs(p[1] - loop_cy) < loop_radius * 1.5]
        top_quadrant = [p for p in loop_section_points if p[1] > loop_cy and abs(p[0] - loop_cx) < loop_radius * 1.5]
        left_quadrant = [p for p in loop_section_points if p[0] < loop_cx and abs(p[1] - loop_cy) < loop_radius * 1.5]
        bottom_quadrant = [p for p in loop_section_points if p[1] < loop_cy and abs(p[0] - loop_cx) < loop_radius * 1.5]

        assert len(right_quadrant) > 0, "Path should pass through right quadrant"
        assert len(top_quadrant) > 0, "Path should pass through top quadrant"
        assert len(left_quadrant) > 0, "Path should pass through left quadrant"
        assert len(bottom_quadrant) > 0, "Path should pass through bottom quadrant"

    def test_loop_path_with_entry_path(self):
        """Test that loop_the_loop_exact works with AttackGroup.entry_path."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=400, spacing=50)

        # Create exact loop path
        waypoints = loop_the_loop_exact(
            start_x=400,
            start_y=-100,
            end_x=100,
            end_y=400,
            loop_center_x=250,
            loop_center_y=150,
            loop_radius=100,
        )

        group.entry_path(waypoints, velocity=2.5, spacing_frames=5)

        # Verify actions are applied
        assert len(Action._active_actions) > 0, "Entry path should create actions"

        # Update a few frames to verify it works
        for _ in range(10):
            Action.update_all(1.0 / 60.0)
            for sprite in sprites:
                sprite.update()

        # Leader should have moved
        assert sprites[0].center_y > -100, "Leader sprite should have moved"
