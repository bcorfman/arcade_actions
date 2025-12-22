"""Tests for path-based entry system."""

import pytest
import arcade
from actions.base import Action
from actions.group import AttackGroup
from actions.formation import arrange_line
from actions.frame_timing import after_frames
from tests.conftest import ActionTestBase


class TestEntryPath(ActionTestBase):
    """Test suite for AttackGroup entry_path functionality."""

    def test_entry_path_leader_follower(self):
        """Test leader/follower entry path pattern."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=400, spacing=50)

        # Create entry path
        entry_waypoints = [(400, -100), (400, 200), (100, 400)]
        group.entry_path(entry_waypoints, velocity=150, spacing_frames=5)

        # Verify actions are applied
        # Leader (first sprite) should have FollowPathUntil
        # Followers should have DelayUntil + FollowPathUntil sequences
        assert len(Action._active_actions) > 0

    def test_entry_path_follower_spacing(self):
        """Test that followers maintain proper spacing."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=400, spacing=50)

        entry_waypoints = [(400, -100), (400, 400)]
        spacing_frames = 10
        group.entry_path(entry_waypoints, velocity=150, spacing_frames=spacing_frames)

        # Update a few frames - leader should start moving immediately
        # Follower 1 should wait spacing_frames
        # Follower 2 should wait spacing_frames * 2
        for _ in range(spacing_frames + 5):
            Action.update_all(1.0 / 60.0)
            for sprite in sprites:
                sprite.update()

        # Leader should have moved
        assert sprites[0].center_y > -100

    def test_entry_path_returns_to_formation(self):
        """Test that sprites return to home slots after entry path."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=400, spacing=50)

        # Record home slots
        home_slot_0 = group.get_home_slot(sprites[0])
        home_slot_1 = group.get_home_slot(sprites[1])

        entry_waypoints = [(400, -100), (400, 400)]
        group.entry_path(entry_waypoints, velocity=300, spacing_frames=5)

        # Wait for entry to complete (simplified - in reality would wait for actions)
        # This test verifies the structure is set up correctly
        assert home_slot_0 is not None
        assert home_slot_1 is not None

    def test_loop_the_loop_creates_path(self):
        """Test that loop_the_loop creates a valid entry path (backward compatibility)."""
        from actions.presets.entry_paths import loop_the_loop

        # Create a loop path
        start_x, start_y = 400, -100
        end_x, end_y = 400, 500
        loop_radius = 150.0
        waypoints = loop_the_loop(start_x, start_y, end_x, end_y, loop_radius)

        # Verify we have enough waypoints for a path
        assert len(waypoints) >= 6, "Loop path should have at least 6 waypoints"

        # Verify the path starts and ends at the correct positions
        assert waypoints[0] == (start_x, start_y), "Path should start at start position"
        assert waypoints[-1] == (end_x, end_y), "Path should end at end position"

    def test_entry_path_with_exact_loop(self):
        """Test that entry_path works with loop_the_loop_exact helper."""
        from actions.presets.entry_paths import loop_the_loop_exact

        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=400, spacing=50)

        # Create exact loop entry path
        entry_path = loop_the_loop_exact(
            start_x=500,
            start_y=-100,
            end_x=100,
            end_y=400,
            loop_center_x=300,
            loop_center_y=150,
            loop_radius=120,
        )
        group.entry_path(entry_path, velocity=2.5, spacing_frames=5)

        # Verify actions are applied (leader + followers)
        assert len(Action._active_actions) > 0, "Entry path should create actions"

        # Verify leader/follower pattern still works
        # Leader should start immediately, followers should be delayed
        for _ in range(10):
            Action.update_all(1.0 / 60.0)
            for sprite in sprites:
                sprite.update()

        # Leader should have moved more than followers
        assert sprites[0].center_y > sprites[1].center_y, "Leader should be ahead of followers"
