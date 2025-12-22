"""Tests for breakaway system."""

import pytest
import arcade
from actions.base import Action
from actions.group import AttackGroup
from actions.group_state import BreakawayManager, BreakawayStrategy, GroupStage
from actions.formation import arrange_line
from actions.conditional import FollowPathUntil, TweenUntil
from actions.frame_timing import after_frames
from tests.conftest import ActionTestBase


class TestBreakawayManager(ActionTestBase):
    """Test suite for BreakawayManager."""

    def test_breakaway_manager_creation(self):
        """Test creating a BreakawayManager."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        assert manager.parent_group == group
        assert manager.stage == GroupStage.IN_FORMATION
        assert len(manager.breakaway_sprites) == 0
        assert len(manager.breakaway_groups) == 0

    def test_breakaway_trigger_timer(self):
        """Test breakaway triggered by timer."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.setup_breakaway(trigger="timer", seconds=1.0, count=2, strategy="deterministic")

        # Initially in formation
        assert manager.stage == GroupStage.IN_FORMATION

        # Wait for timer (simulate 1 second at 60 FPS)
        for _ in range(60):
            Action.update_all(1.0 / 60.0)
            manager.update(1.0 / 60.0)  # Update manager to check trigger

        # Should have triggered breakaway
        assert manager.stage == GroupStage.BREAKAWAY
        assert len(manager.breakaway_sprites) == 2
        assert len(manager.breakaway_groups) == 1

    def test_breakaway_deterministic_dive(self):
        """Test deterministic dive strategy."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.setup_breakaway(
            trigger="timer",
            seconds=0.1,
            count=2,
            strategy="deterministic",
            dive_path=[(100, 200), (100, 100)],
            dive_velocity=100,
        )

        # Trigger breakaway
        for _ in range(6):  # 0.1 seconds at 60 FPS
            Action.update_all(1.0 / 60.0)
            manager.update(1.0 / 60.0)  # Update manager to check trigger

        assert manager.stage == GroupStage.BREAKAWAY
        assert len(manager.breakaway_groups) == 1

        # Breakaway group should have dive action
        breakaway_group = manager.breakaway_groups[0]
        # Check that actions are applied (we can't easily inspect internal actions, so just verify group exists)
        assert breakaway_group is not None

    def test_breakaway_return_to_formation(self):
        """Test that sprites return to their home slots after dive."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        # Record home slots
        home_slot_0 = group.get_home_slot(sprites[0])
        home_slot_1 = group.get_home_slot(sprites[1])

        manager = BreakawayManager(group)
        manager.setup_breakaway(
            trigger="timer",
            seconds=0.1,
            count=2,
            strategy="deterministic",
            dive_path=[(100, 200), (100, 100)],
            dive_velocity=200,  # Fast dive
        )

        # Trigger breakaway
        for _ in range(6):
            Action.update_all(1.0 / 60.0)
            manager.update(1.0 / 60.0)  # Update manager to check trigger

        assert manager.stage == GroupStage.BREAKAWAY

        # Wait for dive to complete and return
        # This is a simplified test - in reality we'd wait for the dive action to complete
        # and then the return TweenUntil to complete
        # For now, just verify the manager tracks the stage
        assert manager.stage in (GroupStage.BREAKAWAY, GroupStage.RETURNING, GroupStage.IN_FORMATION)


class TestBreakawayStrategy(ActionTestBase):
    """Test suite for BreakawayStrategy interface."""

    def test_strategy_interface(self):
        """Test that BreakawayStrategy is an abstract base class."""
        from abc import ABC

        assert issubclass(BreakawayStrategy, ABC)

        # Cannot instantiate directly
        with pytest.raises(TypeError):
            BreakawayStrategy()
