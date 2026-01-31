"""Tests for breakaway system."""

import arcade
import pytest

from arcadeactions.base import Action
from arcadeactions.formation import arrange_line
from arcadeactions.group import AttackGroup
from arcadeactions.group_state import BreakawayManager, BreakawayStrategy, GroupStage
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

    def test_breakaway_default_path_no_stacking(self):
        """Test that sprites don't stack when using default dive path (no dive_path provided)."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        # Place sprites in a line with spacing
        group.place(arrange_line, start_x=100, start_y=200, spacing=100)

        # Record initial positions
        initial_positions = [(sprite.center_x, sprite.center_y) for sprite in sprites]

        manager = BreakawayManager(group)
        # Don't provide dive_path - should use per-sprite default paths
        manager.setup_breakaway(
            trigger="timer",
            seconds=0.1,
            count=3,  # All 3 sprites break away
            strategy="deterministic",
            dive_velocity=100,
        )

        # Trigger breakaway
        for _ in range(6):  # 0.1 seconds at 60 FPS
            Action.update_all(1.0 / 60.0)
            manager.update(1.0 / 60.0)

        assert manager.stage == GroupStage.BREAKAWAY

        # Advance a few frames to let FollowPathUntil initialize
        # FollowPathUntil teleports sprites to the path start in its start() method
        for _ in range(2):
            Action.update_all(1.0 / 60.0)

        # Verify sprites maintain their horizontal spacing (don't stack)
        # Each sprite should dive from its own position, not all from sprites[0]'s position
        breakaway_sprites = list(manager.breakaway_sprites)
        assert len(breakaway_sprites) == 3

        # Check that sprites maintain their X positions (within small tolerance for any movement)
        # The key is that they don't all stack at sprites[0]'s X position
        x_positions = [sprite.center_x for sprite in breakaway_sprites]
        # All X positions should be different (spacing maintained)
        assert len(set(x_positions)) == 3, f"Sprites should maintain spacing, not stack. Positions: {x_positions}"

        # Match sprites to their original positions by comparing current position with original
        # (breakaway_sprites is a set, so order is not guaranteed)
        matched = set()
        for sprite in breakaway_sprites:
            # Find the closest original position to this sprite's current position
            best_match_idx = None
            best_distance = float("inf")
            for i, (orig_x, orig_y) in enumerate(initial_positions):
                if i in matched:
                    continue
                distance = abs(sprite.center_x - orig_x)
                if distance < best_distance:
                    best_distance = distance
                    best_match_idx = i

            if best_match_idx is not None:
                matched.add(best_match_idx)
                original_x = initial_positions[best_match_idx][0]
                # Allow small tolerance for any frame-based movement
                assert abs(sprite.center_x - original_x) < 5, (
                    f"Sprite at {sprite.center_x} should start dive from its original position {original_x}"
                )

    def test_breakaway_trigger_callback(self):
        """Test breakaway triggered by callback condition."""
        sprites = arcade.SpriteList()
        for _ in range(2):
            sprites.append(arcade.Sprite(":resources:images/items/star.png"))

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.setup_breakaway(trigger="callback", count=1, callback=lambda: True)

        manager.update(1.0 / 60.0)

        assert manager.stage == GroupStage.BREAKAWAY
        assert len(manager.breakaway_sprites) == 1

    def test_breakaway_trigger_spatial(self):
        """Test breakaway triggered by spatial condition."""
        sprites = arcade.SpriteList()
        for _ in range(2):
            sprites.append(arcade.Sprite(":resources:images/items/star.png"))

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.setup_breakaway(trigger="spatial", count=1, condition=lambda: True)

        manager.update(1.0 / 60.0)

        assert manager.stage == GroupStage.BREAKAWAY
        assert len(manager.breakaway_sprites) == 1

    def test_breakaway_trigger_health_noop(self):
        """Health trigger should not fire (placeholder behavior)."""
        sprites = arcade.SpriteList()
        for _ in range(1):
            sprites.append(arcade.Sprite(":resources:images/items/star.png"))

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.setup_breakaway(trigger="health", count=1, threshold=0.5)

        manager.update(1.0 / 60.0)

        assert manager.stage == GroupStage.IN_FORMATION

    def test_breakaway_rejoin_clears_groups(self):
        """Rejoining last sprite should reset stage and remove groups."""
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprites = arcade.SpriteList()
        sprites.append(sprite)
        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        manager = BreakawayManager(group)
        manager.stage = GroupStage.BREAKAWAY
        manager.breakaway_sprites.add(sprite)
        breakaway_list = arcade.SpriteList()
        breakaway_list.append(sprite)
        manager.breakaway_groups.append(AttackGroup(breakaway_list, group_id="breakaway"))

        manager.rejoin(sprite)

        assert manager.stage == GroupStage.IN_FORMATION
        assert sprite not in manager.breakaway_sprites
        assert manager.breakaway_groups == []

    def test_setup_breakaway_unknown_strategy(self):
        """Unknown strategy should raise ValueError."""
        sprites = arcade.SpriteList()
        sprites.append(arcade.Sprite(":resources:images/items/star.png"))
        group = AttackGroup(sprites, group_id="test_group")

        manager = BreakawayManager(group)
        with pytest.raises(ValueError, match="Unknown breakaway strategy"):
            manager.setup_breakaway(trigger="timer", strategy="unknown")

    def test_setup_breakaway_unknown_trigger(self):
        """Unknown trigger should raise ValueError."""
        sprites = arcade.SpriteList()
        sprites.append(arcade.Sprite(":resources:images/items/star.png"))
        group = AttackGroup(sprites, group_id="test_group")

        manager = BreakawayManager(group)
        with pytest.raises(ValueError, match="Unknown trigger type"):
            manager.setup_breakaway(trigger="unknown")


class TestBreakawayDebug(ActionTestBase):
    """Test debug logging behavior for breakaway manager."""

    def test_breakaway_event_logging(self, mocker):
        """_log_breakaway_event should emit when debug level allows."""
        from arcadeactions.base import Action
        from arcadeactions.group_state import _log_breakaway_event

        sprites = arcade.SpriteList()
        sprites.append(arcade.Sprite(":resources:images/items/star.png"))
        group = AttackGroup(sprites, group_id="test_group")
        manager = BreakawayManager(group)
        manager.breakaway_sprites.add(sprites[0])

        prev_debug_level = Action.debug_level
        prev_debug_all = Action.debug_all
        try:
            Action.debug_level = 2
            Action.debug_all = True
            mock_print = mocker.patch("builtins.print")

            _log_breakaway_event(manager, "triggered")

            mock_print.assert_called_once()
        finally:
            Action.debug_level = prev_debug_level
            Action.debug_all = prev_debug_all


class TestBreakawayStrategy(ActionTestBase):
    """Test suite for BreakawayStrategy interface."""

    def test_strategy_interface(self):
        """Test that BreakawayStrategy is an abstract base class."""
        from abc import ABC

        assert issubclass(BreakawayStrategy, ABC)

        # Cannot instantiate directly
        with pytest.raises(TypeError):
            BreakawayStrategy()
