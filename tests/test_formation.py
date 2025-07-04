"""Test suite for formation.py - Formation arrangement functions."""

import math

import arcade

from actions.base import Action
from actions.formation import (
    arrange_circle,
    arrange_diamond,
    arrange_grid,
    arrange_line,
    arrange_v_formation,
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

    def test_arrange_line_sprite_creation(self):
        """Test line arrangement creating new sprites."""
        line = arrange_line(count=4, start_x=50, start_y=150, spacing=75)

        assert isinstance(line, arcade.SpriteList)
        assert len(line) == 4

        # Check positions
        expected_positions = [(50, 150), (125, 150), (200, 150), (275, 150)]
        for sprite, (expected_x, expected_y) in zip(line, expected_positions, strict=False):
            assert sprite.center_x == expected_x
            assert sprite.center_y == expected_y


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
        assert sprite_list[3].center_y == 460  # Y increased by spacing_y
        assert sprite_list[4].center_x == 280  # Col 1
        assert sprite_list[4].center_y == 460
        assert sprite_list[5].center_x == 360  # Col 2
        assert sprite_list[5].center_y == 460

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

    def test_arrange_grid_factory_creation(self):
        """Test that arrange_grid can create its own sprites via sprite_factory."""
        rows, cols = 2, 3

        def coin_sprite():
            return arcade.Sprite(":resources:images/items/coinGold.png")

        grid = arrange_grid(
            rows=rows,
            cols=cols,
            start_x=10,
            start_y=50,
            spacing_x=20,
            spacing_y=30,
            sprite_factory=coin_sprite,
        )

        # Should return a SpriteList with rows*cols sprites
        assert isinstance(grid, arcade.SpriteList)
        assert len(grid) == rows * cols

        # Check a couple of positions to ensure arrangement
        assert grid[0].center_x == 10  # Row 0, Col 0
        assert grid[0].center_y == 50
        assert grid[cols - 1].center_x == 10 + (cols - 1) * 20  # Last in first row
        assert grid[cols - 1].center_y == 50
        # First sprite of second row
        assert grid[cols].center_x == 10
        assert grid[cols].center_y == 50 + 30  # Y increased by spacing_y


class TestArrangeCircleFunctions:
    """Test suite for arrange_circle function."""

    def test_arrange_circle_basic(self):
        """Test basic circle arrangement."""
        sprite_list = create_test_sprite_list(4)  # 4 sprites for easier math

        arrange_circle(sprite_list, center_x=400, center_y=300, radius=100.0)

        # Check that sprites are positioned around the circle
        # With 4 sprites, they should be at 90-degree intervals
        # Starting at π/2 (top) and going clockwise
        for i, sprite in enumerate(sprite_list):
            angle = math.pi / 2 - i * 2 * math.pi / 4
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
        # Starting at π/2 (top) and going clockwise
        for i, sprite in enumerate(sprite_list):
            angle = math.pi / 2 - i * 2 * math.pi / 2
            expected_x = 400 + math.cos(angle) * 100
            expected_y = 300 + math.sin(angle) * 100

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1

    def test_arrange_circle_sprite_creation(self):
        """Test circle arrangement creating new sprites."""
        circle = arrange_circle(count=6, center_x=200, center_y=200, radius=80)

        assert isinstance(circle, arcade.SpriteList)
        assert len(circle) == 6

        # Verify all sprites are approximately the correct distance from center
        for sprite in circle:
            distance = math.sqrt((sprite.center_x - 200) ** 2 + (sprite.center_y - 200) ** 2)
            assert abs(distance - 80) < 0.1


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
        angle_rad = math.radians(45.0)

        # Second sprite (i=1, side=1, distance=50)
        expected_x = 400 + 1 * math.cos(angle_rad) * 50
        expected_y = 500 + math.sin(angle_rad) * 50  # Changed to add sine for upward movement
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
        angle_rad = math.radians(30.0)

        # Check second sprite positioning
        expected_x = 200 + 1 * math.cos(angle_rad) * 40
        expected_y = 300 + math.sin(angle_rad) * 40  # Changed to add sine for upward movement
        assert abs(sprite_list[1].center_x - expected_x) < 0.1
        assert abs(sprite_list[1].center_y - expected_y) < 0.1

    def test_arrange_v_formation_sprite_creation(self):
        """Test V formation creating new sprites."""
        v_formation = arrange_v_formation(count=5, apex_x=300, apex_y=200, angle=60, spacing=30)

        assert isinstance(v_formation, arcade.SpriteList)
        assert len(v_formation) == 5

        # Check apex is at expected position
        assert v_formation[0].center_x == 300
        assert v_formation[0].center_y == 200


class TestArrangeDiamondFunctions:
    """Test suite for arrange_diamond function."""

    def test_arrange_diamond_basic(self):
        """Test basic diamond arrangement."""
        sprite_list = create_test_sprite_list(5)  # 1 center + 4 in first ring

        arrange_diamond(sprite_list, center_x=400, center_y=300, spacing=50.0)

        # Check center sprite
        assert sprite_list[0].center_x == 400
        assert sprite_list[0].center_y == 300

        # Check first layer (4 sprites in diamond pattern)
        # Layer 1 has 4 sprites at Manhattan distance 50 from center
        expected_positions = [
            (450, 300),  # Right
            (400, 350),  # Top
            (350, 300),  # Left
            (400, 250),  # Bottom
        ]

        for i, (expected_x, expected_y) in enumerate(expected_positions[: len(sprite_list) - 1]):
            sprite = sprite_list[i + 1]  # Skip center sprite
            assert abs(sprite.center_x - expected_x) < 0.1, f"Sprite {i + 1} x position incorrect"
            assert abs(sprite.center_y - expected_y) < 0.1, f"Sprite {i + 1} y position incorrect"

    def test_arrange_diamond_single_sprite(self):
        """Test diamond arrangement with single sprite."""
        sprite_list = create_test_sprite_list(1)

        arrange_diamond(sprite_list, center_x=200, center_y=150, spacing=30)

        # Single sprite should be at center
        assert sprite_list[0].center_x == 200
        assert sprite_list[0].center_y == 150

    def test_arrange_diamond_large_formation(self):
        """Test diamond arrangement with larger formation (multiple layers)."""
        sprite_list = create_test_sprite_list(13)  # 1 center + 4 first layer + 8 second layer

        arrange_diamond(sprite_list, center_x=300, center_y=200, spacing=40.0)

        # Check center sprite
        assert sprite_list[0].center_x == 300
        assert sprite_list[0].center_y == 200

        # Verify sprites are arranged in layers
        # Layer 0: 1 sprite (center)
        # Layer 1: 4 sprites at distance 40
        # Layer 2: 8 sprites at distance 80

        # Check that layer 1 sprites are at correct Manhattan distance from center
        layer_1_sprites = sprite_list[1:5]
        for sprite in layer_1_sprites:
            manhattan_distance = abs(sprite.center_x - 300) + abs(sprite.center_y - 200)
            assert abs(manhattan_distance - 40) < 0.1, (
                f"Layer 1 sprite not at correct Manhattan distance: {manhattan_distance}"
            )

        # Check that layer 2 sprites are at correct Manhattan distance from center
        layer_2_sprites = sprite_list[5:13]
        for sprite in layer_2_sprites:
            manhattan_distance = abs(sprite.center_x - 300) + abs(sprite.center_y - 200)
            assert abs(manhattan_distance - 80) < 0.1, (
                f"Layer 2 sprite not at correct Manhattan distance: {manhattan_distance}"
            )

    def test_arrange_diamond_empty_list(self):
        """Test diamond arrangement with empty list."""
        sprite_list = arcade.SpriteList()

        # Should not raise error
        arrange_diamond(sprite_list, center_x=400, center_y=300)
        assert len(sprite_list) == 0

    def test_arrange_diamond_default_position(self):
        """Test diamond arrangement with default position."""
        sprite_list = create_test_sprite_list(5)

        arrange_diamond(sprite_list)

        # Check default center position is used (400, 300)
        assert sprite_list[0].center_x == 400
        assert sprite_list[0].center_y == 300

    def test_arrange_diamond_sprite_creation(self):
        """Test diamond arrangement creating new sprites."""
        diamond = arrange_diamond(count=9, center_x=150, center_y=100, spacing=25)

        assert isinstance(diamond, arcade.SpriteList)
        assert len(diamond) == 9

        # Check center sprite
        assert diamond[0].center_x == 150
        assert diamond[0].center_y == 100

        # Verify sprites form diamond pattern
        # Should have 1 center + 4 in layer 1 + 4 in layer 2
        layer_1_count = 4
        layer_2_count = 4

        # Check layer 1 Manhattan distance
        layer_1_sprites = diamond[1 : 1 + layer_1_count]
        for sprite in layer_1_sprites:
            manhattan_distance = abs(sprite.center_x - 150) + abs(sprite.center_y - 100)
            assert abs(manhattan_distance - 25) < 0.1

        # Check layer 2 Manhattan distance
        layer_2_sprites = diamond[5:9]
        for sprite in layer_2_sprites:
            manhattan_distance = abs(sprite.center_x - 150) + abs(sprite.center_y - 100)
            assert abs(manhattan_distance - 50) < 0.1

    def test_arrange_diamond_spacing_consistency(self):
        """Test that diamond formation maintains consistent spacing."""
        sprite_list = create_test_sprite_list(5)
        spacing = 60.0

        arrange_diamond(sprite_list, center_x=200, center_y=200, spacing=spacing)

        # Center sprite
        center = sprite_list[0]
        assert center.center_x == 200
        assert center.center_y == 200

        # First layer sprites should be at Manhattan distance spacing from center
        layer_1_sprites = sprite_list[1:5]
        for sprite in layer_1_sprites:
            manhattan_distance = abs(sprite.center_x - 200) + abs(sprite.center_y - 200)
            assert abs(manhattan_distance - spacing) < 0.1

    def test_arrange_diamond_layer_symmetry(self):
        """Test that diamond layers maintain symmetry."""
        sprite_list = create_test_sprite_list(9)  # 1 + 4 + 4 sprites

        arrange_diamond(sprite_list, center_x=300, center_y=300, spacing=50)

        # Check that first layer forms a proper diamond
        layer_1_sprites = sprite_list[1:5]

        # Find cardinal direction sprites (should be exactly on axes)
        top_sprite = max(layer_1_sprites, key=lambda s: s.center_y)
        bottom_sprite = min(layer_1_sprites, key=lambda s: s.center_y)
        right_sprite = max(layer_1_sprites, key=lambda s: s.center_x)
        left_sprite = min(layer_1_sprites, key=lambda s: s.center_x)

        # Verify cardinal positions
        assert abs(top_sprite.center_x - 300) < 0.1, "Top sprite should be on vertical axis"
        assert abs(bottom_sprite.center_x - 300) < 0.1, "Bottom sprite should be on vertical axis"
        assert abs(right_sprite.center_y - 300) < 0.1, "Right sprite should be on horizontal axis"
        assert abs(left_sprite.center_y - 300) < 0.1, "Left sprite should be on horizontal axis"

        # Verify distances
        assert abs(top_sprite.center_y - 350) < 0.1, "Top sprite at correct position"
        assert abs(bottom_sprite.center_y - 250) < 0.1, "Bottom sprite at correct position"
        assert abs(right_sprite.center_x - 350) < 0.1, "Right sprite at correct position"
        assert abs(left_sprite.center_x - 250) < 0.1, "Left sprite at correct position"

    def test_arrange_diamond_hollow_basic(self):
        """Test hollow diamond arrangement (no center sprite)."""
        sprite_list = create_test_sprite_list(4)  # Just the first ring

        arrange_diamond(sprite_list, center_x=400, center_y=300, spacing=50.0, include_center=False)

        # Check that all sprites are in the first layer (no center sprite)
        expected_positions = [
            (450, 300),  # Right
            (400, 350),  # Top
            (350, 300),  # Left
            (400, 250),  # Bottom
        ]

        for i, (expected_x, expected_y) in enumerate(expected_positions):
            sprite = sprite_list[i]
            assert abs(sprite.center_x - expected_x) < 0.1, f"Sprite {i} x position incorrect"
            assert abs(sprite.center_y - expected_y) < 0.1, f"Sprite {i} y position incorrect"

    def test_arrange_diamond_hollow_large_formation(self):
        """Test hollow diamond with multiple layers."""
        sprite_list = create_test_sprite_list(12)  # 4 + 8 sprites (no center)

        arrange_diamond(sprite_list, center_x=200, center_y=150, spacing=30.0, include_center=False)

        # Check that layer 1 sprites are at correct Manhattan distance from center
        layer_1_sprites = sprite_list[0:4]
        for sprite in layer_1_sprites:
            manhattan_distance = abs(sprite.center_x - 200) + abs(sprite.center_y - 150)
            assert abs(manhattan_distance - 30) < 0.1, (
                f"Layer 1 sprite not at correct Manhattan distance: {manhattan_distance}"
            )

        # Check that layer 2 sprites are at correct Manhattan distance from center
        layer_2_sprites = sprite_list[4:12]
        for sprite in layer_2_sprites:
            manhattan_distance = abs(sprite.center_x - 200) + abs(sprite.center_y - 150)
            assert abs(manhattan_distance - 60) < 0.1, (
                f"Layer 2 sprite not at correct Manhattan distance: {manhattan_distance}"
            )

    def test_arrange_diamond_hollow_sprite_creation(self):
        """Test hollow diamond arrangement creating new sprites."""
        diamond = arrange_diamond(count=8, center_x=100, center_y=50, spacing=25, include_center=False)

        assert isinstance(diamond, arcade.SpriteList)
        assert len(diamond) == 8

        # All sprites should be in layer 1 (4 sprites) and layer 2 (4 sprites)
        # Layer 1: Manhattan distance = 25
        layer_1_sprites = diamond[0:4]
        for sprite in layer_1_sprites:
            manhattan_distance = abs(sprite.center_x - 100) + abs(sprite.center_y - 50)
            assert abs(manhattan_distance - 25) < 0.1

        # Layer 2: Manhattan distance = 50
        layer_2_sprites = diamond[4:8]
        for sprite in layer_2_sprites:
            manhattan_distance = abs(sprite.center_x - 100) + abs(sprite.center_y - 50)
            assert abs(manhattan_distance - 50) < 0.1

    def test_arrange_diamond_include_center_parameter(self):
        """Test that include_center parameter works correctly."""
        # Test with center (default behavior)
        diamond_with_center = arrange_diamond(count=5, center_x=0, center_y=0, spacing=40, include_center=True)
        center_sprite = diamond_with_center[0]
        assert center_sprite.center_x == 0 and center_sprite.center_y == 0, "Center sprite should be at origin"

        # Test without center
        diamond_without_center = arrange_diamond(count=4, center_x=0, center_y=0, spacing=40, include_center=False)
        # All sprites should be at distance 40 from center (none at center)
        for sprite in diamond_without_center:
            manhattan_distance = abs(sprite.center_x) + abs(sprite.center_y)
            assert abs(manhattan_distance - 40) < 0.1, (
                f"Hollow diamond sprite not at correct distance: {manhattan_distance}"
            )

    def test_arrange_diamond_hollow_empty_list(self):
        """Test hollow diamond arrangement with empty list."""
        sprite_list = arcade.SpriteList()

        # Should not raise error
        arrange_diamond(sprite_list, center_x=400, center_y=300, include_center=False)
        assert len(sprite_list) == 0

    def test_arrange_diamond_hollow_single_sprite(self):
        """Test hollow diamond with single sprite."""
        sprite_list = create_test_sprite_list(1)

        arrange_diamond(sprite_list, center_x=150, center_y=100, spacing=35, include_center=False)

        # Single sprite should be in first layer (at distance 35 from center)
        manhattan_distance = abs(sprite_list[0].center_x - 150) + abs(sprite_list[0].center_y - 100)
        assert abs(manhattan_distance - 35) < 0.1, "Single sprite in hollow diamond should be at layer 1"


class TestFormationIntegration:
    """Test suite for integration between formations and actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_formation_with_actions_workflow(self):
        """Test typical workflow of arranging sprites and applying actions."""
        from actions.conditional import MoveUntil
        from actions.pattern import time_elapsed

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
            # MoveUntil uses pixels per frame at 60 FPS semantics
            assert abs(sprite.change_x - 50.0) < 0.01
            assert abs(sprite.change_y - (-25.0)) < 0.01

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


class TestCoordinateConsistency:
    """Test suite specifically for verifying coordinate system consistency."""

    def test_vertical_movement_consistency(self):
        """Test that all arrangement functions handle vertical movement consistently.

        Increasing Y values should always move sprites upward in all functions.
        """
        # Create test sprites
        sprites = create_test_sprite_list(4)
        base_y = 300

        # Test arrange_line
        arrange_line(sprites, start_x=100, start_y=base_y, spacing=50)
        for sprite in sprites:
            assert sprite.center_y == base_y

        arrange_line(sprites, start_x=100, start_y=base_y + 100, spacing=50)
        for sprite in sprites:
            assert sprite.center_y == base_y + 100, "arrange_line should move sprites up with higher y"

        # Test arrange_grid (2x2 grid)
        sprites = create_test_sprite_list(4)
        arrange_grid(sprites, rows=2, cols=2, start_x=100, start_y=base_y, spacing_x=50, spacing_y=50)
        assert sprites[0].center_y == base_y, "First row should be at base_y"
        assert sprites[2].center_y == base_y + 50, "Second row should be above first row"

        # Test arrange_circle
        sprites = create_test_sprite_list(4)
        radius = 100
        arrange_circle(sprites, center_x=200, center_y=base_y, radius=radius)

        # Find top and bottom sprites by y-coordinate
        top_sprite = max(sprites, key=lambda s: s.center_y)
        bottom_sprite = min(sprites, key=lambda s: s.center_y)

        assert top_sprite.center_y > base_y, "Circle top point should be above center"
        assert bottom_sprite.center_y < base_y, "Circle bottom point should be below center"

    def test_grid_row_progression(self):
        """Test that grid rows progress upward consistently."""
        rows, cols = 3, 2
        sprites = create_test_sprite_list(rows * cols)
        start_y = 300
        spacing_y = 50

        arrange_grid(sprites, rows=rows, cols=cols, start_x=100, start_y=start_y, spacing_x=50, spacing_y=spacing_y)

        # Check each row is higher than the previous
        for row in range(rows):
            row_sprites = sprites[row * cols : (row + 1) * cols]
            expected_y = start_y + row * spacing_y
            for sprite in row_sprites:
                assert sprite.center_y == expected_y, f"Row {row} should be at y={expected_y}"

    def test_v_formation_angle_consistency(self):
        """Test that V-formation angles move sprites upward consistently."""
        sprites = create_test_sprite_list(5)
        apex_y = 300
        spacing = 50

        # Test with different angles
        for angle in [30, 45, 60]:
            arrange_v_formation(sprites, apex_x=200, apex_y=apex_y, angle=angle, spacing=spacing)

            # Apex should be at base
            assert sprites[0].center_y == apex_y, "Apex should be at specified y-coordinate"

            # All other sprites should be above apex
            for sprite in sprites[1:]:
                assert sprite.center_y > apex_y, f"Wing sprites should be above apex for angle {angle}"
                # Verify the height increase is proportional to sine of angle
                expected_min_height = spacing * math.sin(math.radians(angle))
                actual_height = sprite.center_y - apex_y
                assert actual_height >= expected_min_height * 0.99, f"Height increase incorrect for angle {angle}"

    def test_circle_quadrant_consistency(self):
        """Test that circle arrangement maintains consistent quadrant positions."""
        sprites = create_test_sprite_list(4)
        center_y = 300
        radius = 100

        arrange_circle(sprites, center_x=200, center_y=center_y, radius=radius)

        # With 4 sprites, they should be at:
        # - First sprite: top (π/2)
        # - Second sprite: right (0)
        # - Third sprite: bottom (-π/2)
        # - Fourth sprite: left (π)
        top_sprite = sprites[0]
        right_sprite = sprites[1]
        bottom_sprite = sprites[2]
        left_sprite = sprites[3]

        # Verify vertical positions
        assert top_sprite.center_y > center_y, "Top sprite should be above center"
        assert bottom_sprite.center_y < center_y, "Bottom sprite should be below center"

        # Verify horizontal positions
        assert right_sprite.center_x > 200, "Right sprite should be right of center"
        assert left_sprite.center_x < 200, "Left sprite should be left of center"

        # Verify quadrant positions
        assert right_sprite.center_y == center_y, "Right sprite should be at center_y"
        assert left_sprite.center_y == center_y, "Left sprite should be at center_y"
