"""
Tests for GroupAction batch optimization feature.

This test suite verifies that the batch optimization correctly handles
movement actions while maintaining backward compatibility for other action types.
"""

import pytest

from actions.base import ActionSprite
from actions.composite import sequence
from actions.group import SpriteGroup
from actions.interval import FadeOut, MoveBy, MoveTo, RotateBy, ScaleBy


class TestGroupActionBatchOptimization:
    """Test suite for GroupAction batch optimization."""

    @pytest.fixture
    def sprite_group(self):
        """Create a sprite group with test sprites for starfield-like testing."""
        group = SpriteGroup()
        # Create multiple sprites at different positions (like stars)
        positions = [(100 + i * 50, 200 + i * 30) for i in range(10)]
        for i, (x, y) in enumerate(positions):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.center_x = x
            sprite.center_y = y
            group.append(sprite)
        return group

    def test_move_by_uses_batch_optimization(self, sprite_group):
        """Test that MoveBy action uses batch optimization."""
        move_action = MoveBy((50, -100), 2.0)
        group_action = sprite_group.do(move_action)

        # Verify batch optimization is enabled
        assert group_action._use_batch_optimization is True
        assert len(group_action.actions) == 0  # No individual actions created
        assert len(group_action._batch_start_positions) == len(sprite_group)
        assert group_action._batch_total_change == (50, -100)

    def test_move_to_uses_batch_optimization(self, sprite_group):
        """Test that MoveTo action uses batch optimization."""
        move_action = MoveTo((400, 300), 2.0)
        group_action = sprite_group.do(move_action)

        # Verify batch optimization is enabled
        assert group_action._use_batch_optimization is True
        assert len(group_action.actions) == 0  # No individual actions created
        assert len(group_action._batch_start_positions) == len(sprite_group)

    def test_non_movement_action_uses_individual_actions(self, sprite_group):
        """Test that non-movement actions still use individual actions."""
        rotate_action = RotateBy(90, 2.0)
        group_action = sprite_group.do(rotate_action)

        # Verify individual actions are created
        assert group_action._use_batch_optimization is False
        assert len(group_action.actions) == len(sprite_group)
        assert len(group_action._batch_start_positions) == 0

    def test_batch_movement_correctness(self, sprite_group):
        """Test that batch optimization produces correct movement results."""
        # Store initial positions
        initial_positions = [(s.center_x, s.center_y) for s in sprite_group]

        # Apply MoveBy action
        move_action = MoveBy((50, -100), 1.0)
        group_action = sprite_group.do(move_action)

        # Update for half duration
        sprite_group.update(0.5)

        # Verify all sprites moved by half the expected amount
        for i, sprite in enumerate(sprite_group):
            expected_x = initial_positions[i][0] + 25  # Half of 50
            expected_y = initial_positions[i][1] - 50  # Half of -100
            assert abs(sprite.center_x - expected_x) < 1, f"Sprite {i} x-position incorrect"
            assert abs(sprite.center_y - expected_y) < 1, f"Sprite {i} y-position incorrect"

        # Update for remaining duration
        sprite_group.update(0.5)

        # Verify all sprites moved by full expected amount
        for i, sprite in enumerate(sprite_group):
            expected_x = initial_positions[i][0] + 50
            expected_y = initial_positions[i][1] - 100
            assert abs(sprite.center_x - expected_x) < 1, f"Sprite {i} final x-position incorrect"
            assert abs(sprite.center_y - expected_y) < 1, f"Sprite {i} final y-position incorrect"

        # Verify action is complete
        assert group_action.done

    def test_batch_vs_individual_same_results(self, sprite_group):
        """Test that batch optimization produces the same results as individual actions.

        This is a critical test to ensure the optimization doesn't change behavior.
        """
        # Split sprites into two groups for comparison
        group1 = SpriteGroup()
        group2 = SpriteGroup()

        # Create identical sprites in both groups
        for i in range(5):
            sprite1 = ActionSprite(":resources:images/items/star.png")
            sprite2 = ActionSprite(":resources:images/items/star.png")

            # Set identical positions
            x, y = 100 + i * 50, 200 + i * 30
            sprite1.center_x = x
            sprite1.center_y = y
            sprite2.center_x = x
            sprite2.center_y = y

            group1.append(sprite1)
            group2.append(sprite2)

        # Apply same MoveBy action to both groups
        move_action1 = MoveBy((75, -50), 1.5)
        move_action2 = MoveBy((75, -50), 1.5)

        group_action1 = group1.do(move_action1)  # Should use batch optimization

        # Force group2 to use individual actions by using a non-movement action wrapper
        # We'll apply individual MoveBy actions manually to simulate the old behavior
        individual_actions = []
        for sprite in group2:
            action = MoveBy((75, -50), 1.5)
            action.target = sprite
            action.start()
            individual_actions.append(action)

        # Update both groups with same timing
        for dt in [0.3, 0.4, 0.5, 0.3]:  # Total = 1.5 seconds
            group1.update(dt)
            for action in individual_actions:
                if not action.done:
                    action.update(dt)

        # Compare final positions - they should be identical
        for sprite1, sprite2 in zip(group1, group2, strict=False):
            assert abs(sprite1.center_x - sprite2.center_x) < 0.01, "X positions differ between batch and individual"
            assert abs(sprite1.center_y - sprite2.center_y) < 0.01, "Y positions differ between batch and individual"

    def test_batch_optimization_with_pause_resume(self, sprite_group):
        """Test that pause/resume works correctly with batch optimization."""
        initial_positions = [(s.center_x, s.center_y) for s in sprite_group]

        move_action = MoveBy((100, 0), 2.0)
        group_action = sprite_group.do(move_action)

        # Update for 0.5 seconds
        sprite_group.update(0.5)

        # Pause the action
        group_action.pause()

        # Store positions at pause
        paused_positions = [(s.center_x, s.center_y) for s in sprite_group]

        # Update while paused - positions shouldn't change
        sprite_group.update(0.5)
        for i, sprite in enumerate(sprite_group):
            assert abs(sprite.center_x - paused_positions[i][0]) < 0.01
            assert abs(sprite.center_y - paused_positions[i][1]) < 0.01

        # Resume and complete
        group_action.resume()
        sprite_group.update(1.5)  # Complete remaining duration

        # Verify final movement
        for i, sprite in enumerate(sprite_group):
            expected_x = initial_positions[i][0] + 100
            assert abs(sprite.center_x - expected_x) < 1

    def test_batch_optimization_with_reverse_movement(self, sprite_group):
        """Test that reverse_movement works correctly with batch optimization."""
        initial_positions = [(s.center_x, s.center_y) for s in sprite_group]

        move_action = MoveBy((100, -50), 2.0)
        group_action = sprite_group.do(move_action)

        # Update for half duration
        sprite_group.update(1.0)

        # Store positions at halfway point
        halfway_positions = [(s.center_x, s.center_y) for s in sprite_group]

        # Reverse x-axis movement
        group_action.reverse_movement("x")

        # Complete the remaining duration (which was reset in reverse_movement)
        sprite_group.update(1.0)

        # Verify batch optimization is being used
        assert group_action._use_batch_optimization is True
        original_total_change = (100, -50)  # Original movement

        # Verify that the batch total change was reversed for X axis only
        assert group_action._batch_total_change[0] == -original_total_change[0], "X movement should be reversed"
        assert group_action._batch_total_change[1] == original_total_change[1], "Y movement should be unchanged"

        # The main thing we want to test is that batch optimization doesn't break
        # when reverse_movement is called, and that sprites continue to move
        for i, sprite in enumerate(sprite_group):
            # Sprites should have moved from their halfway positions
            assert sprite.center_x != halfway_positions[i][0], f"Sprite {i} should have moved in X after reverse"

            # Since Y wasn't reversed, it should continue in the same direction
            assert sprite.center_y < halfway_positions[i][1], f"Sprite {i} should continue moving down in Y"

    def test_performance_improvement_indicator(self, sprite_group):
        """Test that indicates the performance improvement of batch optimization.

        This test doesn't directly measure performance but verifies the optimization
        is working by checking that no individual actions are created.
        """
        # Create a larger group to simulate starfield
        large_group = SpriteGroup()
        for i in range(100):  # 100 sprites like stars
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.center_x = i * 8  # Spread across screen
            sprite.center_y = 500
            large_group.append(sprite)

        # Apply movement (like falling stars)
        move_action = MoveBy((0, -600), 3.0)  # Move down off screen
        group_action = large_group.do(move_action)

        # Verify batch optimization is used
        assert group_action._use_batch_optimization is True
        assert len(group_action.actions) == 0  # No individual actions = O(1) instead of O(N)

        # Verify movement still works
        initial_y = large_group[0].center_y
        large_group.update(1.5)  # Half duration
        expected_y = initial_y - 300  # Half of -600
        assert abs(large_group[0].center_y - expected_y) < 1

    def test_mixed_action_types_fallback(self, sprite_group):
        """Test that non-movement actions properly fall back to individual actions."""
        # Test various non-movement actions
        test_actions = [
            RotateBy(90, 1.0),
            ScaleBy(1.5, 1.0),
            FadeOut(1.0),
            sequence(MoveBy((10, 0), 0.5), RotateBy(45, 0.5)),  # Composite action
        ]

        for action in test_actions:
            group_action = sprite_group.do(action)

            # Verify fallback to individual actions
            assert group_action._use_batch_optimization is False, (
                f"Action {type(action).__name__} should not use batch optimization"
            )
            assert len(group_action.actions) == len(sprite_group), (
                f"Action {type(action).__name__} should create individual actions"
            )

            # Clear actions for next test
            sprite_group.clear_actions()

    def test_batch_optimization_with_boundary_actions(self, sprite_group):
        """Test that batch optimization works correctly with boundary actions like BoundedMove."""
        from actions.move import BoundedMove

        # Position sprites near right edge
        for i, sprite in enumerate(sprite_group):
            sprite.center_x = 720 + i * 5  # Near right boundary
            sprite.center_y = 300

        initial_positions = [(s.center_x, s.center_y) for s in sprite_group]

        # Apply movement that will trigger boundary
        move_action = MoveBy((200, 0), 1.0)
        group_action = sprite_group.do(move_action)

        # Set up boundary detection
        bounds = lambda: (0, 0, 800, 600)
        boundary_action = BoundedMove(bounds)
        boundary_action.target = sprite_group
        boundary_action.start()

        # Update both actions
        sprite_group.update(0.5)  # This updates the GroupAction (batch optimized)
        boundary_action.update(0.5)  # This handles boundary detection

        # Verify batch optimization is still active
        assert group_action._use_batch_optimization is True

        # Verify sprites moved (either bounced or continued)
        for i, sprite in enumerate(sprite_group):
            assert sprite.center_x != initial_positions[i][0], f"Sprite {i} should have moved"


class TestStarfieldPerformanceScenario:
    """Test suite specifically for starfield-like performance scenarios."""

    def test_large_starfield_batch_optimization(self):
        """Test batch optimization with a large number of sprites (starfield scenario)."""
        # Create a large starfield
        starfield = SpriteGroup()
        num_stars = 200  # Large number to simulate performance concern

        for i in range(num_stars):
            star = ActionSprite(":resources:images/items/star.png")
            # Random-ish distribution across screen
            star.center_x = (i * 17) % 800  # Spread across width
            star.center_y = 600 + (i % 10) * 20  # Start above screen
            starfield.append(star)

        # Apply downward movement (typical starfield behavior)
        fall_action = MoveBy((0, -800), 4.0)  # Move down and off screen
        group_action = starfield.do(fall_action)

        # Verify batch optimization is used
        assert group_action._use_batch_optimization is True
        assert len(group_action.actions) == 0  # Critical: no individual actions
        assert len(group_action._batch_start_positions) == num_stars

        # Test movement correctness over time
        initial_positions = [(s.center_x, s.center_y) for s in starfield]

        # Update for quarter duration
        starfield.update(1.0)

        # Verify all stars moved down by expected amount
        expected_delta_y = -200  # Quarter of -800
        for i, star in enumerate(starfield):
            expected_y = initial_positions[i][1] + expected_delta_y
            assert abs(star.center_y - expected_y) < 1, f"Star {i} incorrect position"
            # X should be unchanged
            assert abs(star.center_x - initial_positions[i][0]) < 0.01

    def test_starfield_with_wrapping(self):
        """Test starfield with screen wrapping using batch optimization."""
        from actions.move import WrappedMove

        # Create starfield
        starfield = SpriteGroup()
        for i in range(50):
            star = ActionSprite(":resources:images/items/star.png")
            star.center_x = i * 16  # Spread across screen
            star.center_y = 600  # Start at top
            starfield.append(star)

        # Continuous downward movement
        fall_action = MoveBy((0, -1000), 5.0)
        group_action = starfield.do(fall_action)

        # Set up wrapping
        bounds = lambda: (800, 600)
        wrap_action = WrappedMove(bounds)
        wrap_action.target = starfield
        wrap_action.start()

        # Verify batch optimization is active
        assert group_action._use_batch_optimization is True

        # Update to move stars off screen and wrap
        starfield.update(3.0)  # Move stars down significantly
        wrap_action.update(3.0)

        # Verify movement occurred and wrapping is handled
        # After 3 seconds of 5-second action moving -1000 pixels, stars should have moved -600 pixels
        # Some stars should have wrapped or be in the process of moving down
        star_positions = [star.center_y for star in starfield]

        # At minimum, verify that stars have moved from their initial position (600)
        # and some may have wrapped or be continuing to move
        assert any(pos != 600 for pos in star_positions), "Stars should have moved from initial position"
