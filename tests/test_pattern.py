"""Test suite for pattern.py - Formation arrangement functions."""

import arcade

from actions.base import Action
from actions.pattern import (
    arrange_circle,
    arrange_grid,
    arrange_line,
    arrange_v_formation,
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


class TestArrangeLineFunctions:
    """Test suite for arrange_line function."""

    def test_arrange_line_basic(self):
        """Test basic line arrangement."""
        sprite_list = create_test_sprite_list(3)

        arrange_line(sprite_list, start_x=100, start_y=200, spacing=60.0)

        # Check sprite positions
        assert sprite_list[0].center_x == 100
        assert sprite_list[0].center_y == 200
        assert sprite_list[1].center_x == 160
        assert sprite_list[1].center_y == 200
        assert sprite_list[2].center_x == 220
        assert sprite_list[2].center_y == 200

    def test_arrange_line_default_position(self):
        """Test line arrangement with default position."""
        sprite_list = create_test_sprite_list(2)

        arrange_line(sprite_list)

        # Check default positions
        assert sprite_list[0].center_x == 0
        assert sprite_list[0].center_y == 0
        assert sprite_list[1].center_x == 50
        assert sprite_list[1].center_y == 0

    def test_arrange_line_python_list(self):
        """Test line arrangement with Python list instead of SpriteList."""
        sprites = [create_test_sprite() for _ in range(3)]

        arrange_line(sprites, start_x=200, start_y=300, spacing=40)

        assert sprites[0].center_x == 200
        assert sprites[1].center_x == 240
        assert sprites[2].center_x == 280
        for sprite in sprites:
            assert sprite.center_y == 300


class TestArrangeGridFunctions:
    """Test suite for arrange_grid function."""

    def test_arrange_grid_basic(self):
        """Test basic grid arrangement."""
        sprite_list = create_test_sprite_list(6)  # 2x3 grid

        arrange_grid(sprite_list, rows=2, cols=3, start_x=200, start_y=400, spacing_x=80, spacing_y=60)

        # Check sprite positions for 2x3 grid
        # Row 0
        assert sprite_list[0].center_x == 200  # Col 0
        assert sprite_list[0].center_y == 400
        assert sprite_list[1].center_x == 280  # Col 1
        assert sprite_list[1].center_y == 400
        assert sprite_list[2].center_x == 360  # Col 2
        assert sprite_list[2].center_y == 400

        # Row 1
        assert sprite_list[3].center_x == 200  # Col 0
        assert sprite_list[3].center_y == 340  # Y decreased by spacing_y
        assert sprite_list[4].center_x == 280  # Col 1
        assert sprite_list[4].center_y == 340
        assert sprite_list[5].center_x == 360  # Col 2
        assert sprite_list[5].center_y == 340

    def test_arrange_grid_default_position(self):
        """Test grid arrangement with default position."""
        sprite_list = create_test_sprite_list(3)

        arrange_grid(sprite_list, cols=3)

        # Check default positions
        assert sprite_list[0].center_x == 100
        assert sprite_list[0].center_y == 500

    def test_arrange_grid_single_row(self):
        """Test grid arrangement with single row."""
        sprite_list = create_test_sprite_list(4)

        arrange_grid(sprite_list, rows=1, cols=4, start_x=0, start_y=100, spacing_x=50)

        for i, sprite in enumerate(sprite_list):
            assert sprite.center_x == i * 50
            assert sprite.center_y == 100


class TestArrangeCircleFunctions:
    """Test suite for arrange_circle function."""

    def test_arrange_circle_basic(self):
        """Test basic circle arrangement."""
        sprite_list = create_test_sprite_list(4)  # 4 sprites for easier math

        arrange_circle(sprite_list, center_x=400, center_y=300, radius=100.0)

        # Check that sprites are positioned around the circle
        # With 4 sprites, they should be at 90-degree intervals
        import math

        for i, sprite in enumerate(sprite_list):
            angle = i * 2 * math.pi / 4
            expected_x = 400 + math.cos(angle) * 100
            expected_y = 300 + math.sin(angle) * 100

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1

    def test_arrange_circle_empty_list(self):
        """Test circle arrangement with empty list."""
        sprite_list = arcade.SpriteList()

        # Should not raise error
        arrange_circle(sprite_list, center_x=400, center_y=300)

    def test_arrange_circle_default_position(self):
        """Test circle arrangement with default position."""
        sprite_list = create_test_sprite_list(2)

        arrange_circle(sprite_list)

        # Check default center position is used
        import math

        for i, sprite in enumerate(sprite_list):
            angle = i * 2 * math.pi / 2
            expected_x = 400 + math.cos(angle) * 100
            expected_y = 300 + math.sin(angle) * 100

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1


class TestArrangeVFormationFunctions:
    """Test suite for arrange_v_formation function."""

    def test_arrange_v_formation_basic(self):
        """Test basic V formation arrangement."""
        sprite_list = create_test_sprite_list(5)

        arrange_v_formation(sprite_list, apex_x=400, apex_y=500, angle=45.0, spacing=50.0)

        # Check apex sprite
        assert sprite_list[0].center_x == 400
        assert sprite_list[0].center_y == 500

        # Check that other sprites are arranged alternately
        import math

        angle_rad = math.radians(45.0)

        # Second sprite (i=1, side=1, distance=50)
        expected_x = 400 + 1 * math.cos(angle_rad) * 50
        expected_y = 500 - math.sin(angle_rad) * 50
        assert abs(sprite_list[1].center_x - expected_x) < 0.1
        assert abs(sprite_list[1].center_y - expected_y) < 0.1

    def test_arrange_v_formation_empty_list(self):
        """Test V formation with empty list."""
        sprite_list = arcade.SpriteList()

        # Should not raise error
        arrange_v_formation(sprite_list, apex_x=400, apex_y=500)

    def test_arrange_v_formation_single_sprite(self):
        """Test V formation with single sprite."""
        sprite_list = create_test_sprite_list(1)

        arrange_v_formation(sprite_list, apex_x=300, apex_y=400)

        # Single sprite should be at apex
        assert sprite_list[0].center_x == 300
        assert sprite_list[0].center_y == 400

    def test_arrange_v_formation_custom_angle(self):
        """Test V formation with custom angle."""
        sprite_list = create_test_sprite_list(3)

        arrange_v_formation(sprite_list, apex_x=200, apex_y=300, angle=30.0, spacing=40.0)

        # Apex should be at specified position
        assert sprite_list[0].center_x == 200
        assert sprite_list[0].center_y == 300

        # Other sprites should be arranged according to 30-degree angle
        import math

        angle_rad = math.radians(30.0)

        # Check second sprite positioning
        expected_x = 200 + 1 * math.cos(angle_rad) * 40
        expected_y = 300 - math.sin(angle_rad) * 40
        assert abs(sprite_list[1].center_x - expected_x) < 0.1
        assert abs(sprite_list[1].center_y - expected_y) < 0.1


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


class TestFormationIntegration:
    """Test suite for integration between formations and actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_formation_with_actions_workflow(self):
        """Test typical workflow of arranging sprites and applying actions."""
        from actions.conditional import MoveUntil

        # Create sprites and arrange them
        sprite_list = create_test_sprite_list(6)
        arrange_grid(sprite_list, rows=2, cols=3, start_x=200, start_y=400, spacing_x=80, spacing_y=60)

        # Apply actions directly to the sprite list
        move_action = MoveUntil((50, -25), time_elapsed(2.0))
        move_action.apply(sprite_list, tag="formation_movement")

        # Verify action was applied
        assert move_action in Action._active_actions
        assert move_action.target == sprite_list
        assert move_action.tag == "formation_movement"

        # Update and verify movement
        Action.update_all(0.1)
        for sprite in sprite_list:
            assert sprite.change_x == 50
            assert sprite.change_y == -25

    def test_multiple_formations_same_sprites(self):
        """Test applying different formation patterns to same sprite list."""
        sprite_list = create_test_sprite_list(4)

        # Start with line formation
        arrange_line(sprite_list, start_x=0, start_y=100, spacing=50)
        line_positions = [(s.center_x, s.center_y) for s in sprite_list]

        # Change to circle formation
        arrange_circle(sprite_list, center_x=200, center_y=200, radius=80)
        circle_positions = [(s.center_x, s.center_y) for s in sprite_list]

        # Positions should be different
        assert line_positions != circle_positions

        # Change to grid formation
        arrange_grid(sprite_list, rows=2, cols=2, start_x=300, start_y=300)
        grid_positions = [(s.center_x, s.center_y) for s in sprite_list]

        # All formations should be different
        assert len(set([tuple(line_positions), tuple(circle_positions), tuple(grid_positions)])) == 3

    def test_formation_with_conditional_actions(self):
        """Test formations with conditional actions and condition helpers."""
        from actions.composite import parallel, sequence
        from actions.conditional import FadeUntil, MoveUntil

        sprite_list = create_test_sprite_list(8)
        arrange_grid(sprite_list, rows=2, cols=4, start_x=100, start_y=400)

        # Create conditional actions using helpers
        move_action = MoveUntil((30, -20), time_elapsed(1.5))
        fade_action = FadeUntil(-20, sprite_count(sprite_list, 4, "<="))

        # Use explicit composition
        seq = sequence(move_action, fade_action)
        par = parallel(move_action, fade_action)

        # Apply to sprite list
        seq.apply(sprite_list, tag="sequential")
        par.apply(sprite_list, tag="parallel")  # This will conflict but tests the API

        # Verify actions were registered
        seq_actions = Action.get_actions_for_target(sprite_list, "sequential")
        par_actions = Action.get_actions_for_target(sprite_list, "parallel")

        assert len(seq_actions) == 1
        assert len(par_actions) == 1
