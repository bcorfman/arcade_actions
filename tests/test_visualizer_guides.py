"""
Tests for ACE visualizer visual guide layers.

Tests velocity vectors, boundary rectangles, path splines, and other
visual debug overlays that help visualize action behavior.
"""

import pytest
import arcade
from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot
from actions.visualizer.guides import (
    VelocityGuide,
    BoundsGuide,
    PathGuide,
    GuideManager,
)


class TestVelocityGuide:
    """Test velocity vector rendering guide."""

    def test_guide_initialization(self):
        """Test that velocity guide initializes."""
        guide = VelocityGuide()

        assert guide.enabled is False
        assert guide.color == arcade.color.GREEN

    def test_guide_can_be_toggled(self):
        """Test that guide can be enabled/disabled."""
        guide = VelocityGuide()
        guide.enabled = True

        initial = guide.enabled
        guide.toggle()

        assert guide.enabled != initial

    def test_guide_builds_arrows_from_snapshots(self):
        """Test that guide creates arrow shapes for velocity vectors."""
        guide = VelocityGuide()
        guide.enabled = True

        snapshots = [
            ActionSnapshot(
                action_id=1,
                action_type="MoveUntil",
                target_id=100,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
                velocity=(5.0, 3.0),
            ),
        ]

        # Mock sprite positions
        sprite_positions = {100: (100, 200)}

        guide.update(snapshots, sprite_positions)

        # Should have created shape data
        assert len(guide.arrows) == 1

    def test_guide_respects_disabled_state(self):
        """Test that disabled guide doesn't create shapes."""
        guide = VelocityGuide(enabled=False)

        snapshots = [
            ActionSnapshot(
                action_id=1,
                action_type="MoveUntil",
                target_id=100,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
                velocity=(5.0, 3.0),
            ),
        ]

        sprite_positions = {100: (100, 200)}
        guide.update(snapshots, sprite_positions)

        assert len(guide.arrows) == 0


class TestBoundsGuide:
    """Test boundary rectangle rendering guide."""

    def test_guide_initialization(self):
        """Test that bounds guide initializes."""
        guide = BoundsGuide()

        assert guide.enabled is False
        assert guide.color == arcade.color.RED

    def test_guide_builds_rectangles_from_snapshots(self):
        """Test that guide creates rectangles for bounds."""
        guide = BoundsGuide()
        guide.enabled = True

        snapshots = [
            ActionSnapshot(
                action_id=1,
                action_type="MoveUntil",
                target_id=100,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
                bounds=(0, 0, 800, 600),
            ),
        ]

        guide.update(snapshots)

        # Should have created rectangle shape
        assert len(guide.rectangles) == 1
        assert guide.rectangles[0] == (0, 0, 800, 600)

    def test_guide_deduplicates_identical_bounds(self):
        """Test that guide doesn't create duplicate rectangles."""
        guide = BoundsGuide()
        guide.enabled = True

        snapshots = [
            ActionSnapshot(
                action_id=1,
                action_type="MoveUntil",
                target_id=100,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
                bounds=(0, 0, 800, 600),
            ),
            ActionSnapshot(
                action_id=2,
                action_type="MoveUntil",
                target_id=101,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=None,
                bounds=(0, 0, 800, 600),  # Same bounds
            ),
        ]

        guide.update(snapshots)

        # Should only have one rectangle for duplicate bounds
        assert len(guide.rectangles) == 1


class TestPathGuide:
    """Test path spline rendering guide."""

    def test_guide_initialization(self):
        """Test that path guide initializes."""
        guide = PathGuide()

        assert guide.enabled is False
        assert guide.color == arcade.color.BLUE

    def test_guide_stores_path_data(self):
        """Test that guide stores path information."""
        guide = PathGuide()
        guide.enabled = True

        # Simulate FollowPathUntil snapshot with path data
        snapshots = [
            ActionSnapshot(
                action_id=1,
                action_type="FollowPathUntil",
                target_id=100,
                target_type="Sprite",
                tag=None,
                is_active=True,
                is_paused=False,
                factor=1.0,
                elapsed=0.0,
                progress=0.5,
                metadata={"path_points": [(100, 100), (200, 150), (300, 100)]},
            ),
        ]

        guide.update(snapshots)

        # Should have stored path data
        assert len(guide.paths) == 1


class TestGuideManager:
    """Test the guide manager that coordinates all visual guides."""

    def test_manager_initialization(self):
        """Test that manager initializes with guides."""
        manager = GuideManager()

        assert manager.velocity_guide is not None
        assert manager.bounds_guide is not None
        assert manager.path_guide is not None

    def test_manager_toggles_all_guides(self):
        """Test that manager can toggle all guides at once."""
        manager = GuideManager()

        initial_velocity = manager.velocity_guide.enabled
        initial_bounds = manager.bounds_guide.enabled

        manager.toggle_all()

        assert manager.velocity_guide.enabled != initial_velocity
        assert manager.bounds_guide.enabled != initial_bounds

    def test_manager_toggles_individual_guides(self):
        """Test that manager can toggle guides individually."""
        manager = GuideManager()

        initial = manager.velocity_guide.enabled
        manager.toggle_velocity()

        assert manager.velocity_guide.enabled != initial

    def test_manager_updates_all_guides(self):
        """Test that manager updates all enabled guides."""
        # Create snapshots directly instead of via update_snapshot
        snapshot = ActionSnapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            velocity=(5.0, 3.0),
            bounds=(0, 0, 800, 600),
        )

        manager = GuideManager()
        manager.toggle_all()
        sprite_positions = {100: (100, 200)}

        manager.update([snapshot], sprite_positions)

        # All enabled guides should have updated
        assert len(manager.velocity_guide.arrows) > 0
        assert len(manager.bounds_guide.rectangles) > 0
