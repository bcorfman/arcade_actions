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

        assert guide.enabled is True
        assert guide.color == arcade.color.GREEN

    def test_guide_can_be_toggled(self):
        """Test that guide can be enabled/disabled."""
        guide = VelocityGuide()

        initial = guide.enabled
        guide.toggle()

        assert guide.enabled != initial

    def test_guide_builds_arrows_from_snapshots(self):
        """Test that guide creates arrow shapes for velocity vectors."""
        guide = VelocityGuide()

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

        assert guide.enabled is True
        assert guide.color == arcade.color.RED

    def test_guide_builds_rectangles_from_snapshots(self):
        """Test that guide creates rectangles for bounds."""
        guide = BoundsGuide()

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

        assert guide.enabled is True
        assert guide.color == arcade.color.BLUE

    def test_guide_stores_path_data(self):
        """Test that guide stores path information."""
        guide = PathGuide()

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
        sprite_positions = {100: (100, 200)}

        manager.velocity_guide.enabled = True
        manager.bounds_guide.enabled = True
        manager.path_guide.enabled = True
        manager.update([snapshot], sprite_positions)

        # All enabled guides should have updated
        assert len(manager.velocity_guide.arrows) > 0
        assert len(manager.bounds_guide.rectangles) > 0


class TestHighlightGuide:
    """Test highlight bounding box guide."""

    def test_highlight_guide_initialization(self):
        """Test that highlight guide initializes with always enabled."""
        from actions.visualizer.guides import HighlightGuide
        
        guide = HighlightGuide()
        assert guide.enabled is True
        assert guide.color == arcade.color.LIME_GREEN

    def test_highlight_guide_draws_box_for_highlighted_target(self):
        """Test that highlight guide draws box around highlighted sprite."""
        from actions.visualizer.guides import HighlightGuide
        
        guide = HighlightGuide()
        
        # Sprite positions
        sprite_positions = {
            100: (150, 250),
            200: (300, 400),
        }
        
        # Sprite sizes (width, height) - would come from actual sprites
        sprite_sizes = {
            100: (50, 50),
            200: (60, 60),
        }
        
        # Highlight sprite 100
        guide.update(
            highlighted_target_id=100,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes
        )
        
        assert len(guide.rectangles) == 1
        # Rectangle format: (left, bottom, right, top)
        rect = guide.rectangles[0]
        # Center is at (150, 250), size is 50x50
        # So: left=125, bottom=225, right=175, top=275
        assert rect == (125.0, 225.0, 175.0, 275.0)
    
    def test_highlight_guide_draws_boxes_for_sprite_list(self):
        """Test that highlight guide draws boxes around all sprites in a highlighted list."""
        from actions.visualizer.guides import HighlightGuide
        
        guide = HighlightGuide()
        
        # Sprite list contains multiple sprites
        sprite_positions = {
            100: (150, 250),  # The sprite list itself (average position)
            101: (100, 200),  # First sprite in list
            102: (200, 300),  # Second sprite in list
        }
        
        sprite_sizes = {
            101: (40, 40),
            102: (40, 40),
        }
        
        # Sprite IDs that belong to target 100 (the sprite list)
        sprite_ids_in_target = {
            100: [101, 102]
        }
        
        # Highlight sprite list 100
        guide.update(
            highlighted_target_id=100,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes,
            sprite_ids_in_target=sprite_ids_in_target
        )
        
        # Should draw boxes for both sprites in the list
        assert len(guide.rectangles) == 2
    
    def test_highlight_guide_clears_when_no_highlight(self):
        """Test that highlight guide clears rectangles when nothing is highlighted."""
        from actions.visualizer.guides import HighlightGuide
        
        guide = HighlightGuide()
        
        sprite_positions = {100: (150, 250)}
        sprite_sizes = {100: (50, 50)}
        
        # First highlight something
        guide.update(
            highlighted_target_id=100,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes
        )
        assert len(guide.rectangles) == 1
        
        # Then clear highlight
        guide.update(
            highlighted_target_id=None,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes
        )
        assert len(guide.rectangles) == 0
    
    def test_highlight_guide_disabled_produces_no_rectangles(self):
        """Test that disabled highlight guide doesn't draw anything."""
        from actions.visualizer.guides import HighlightGuide
        
        guide = HighlightGuide(enabled=False)
        
        sprite_positions = {100: (150, 250)}
        sprite_sizes = {100: (50, 50)}
        
        guide.update(
            highlighted_target_id=100,
            sprite_positions=sprite_positions,
            sprite_sizes=sprite_sizes
        )
        
        # Should not draw anything when disabled
        assert len(guide.rectangles) == 0
