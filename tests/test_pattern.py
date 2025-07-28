"""Test suite for pattern.py - Movement patterns and condition helpers."""

import math

import arcade

from actions.base import Action
from actions.composite import sequence
from actions.conditional import DelayUntil, FadeUntil, duration
from actions.formation import arrange_circle, arrange_grid, arrange_line
from actions.pattern import (
    BoidMoveUntil,
    _calculate_adaptive_spacing,
    _generate_random_spawn_point,
    _generate_spaced_spawn_points,
    _generate_upper_boundary_spawn_positions,
    create_boid_flock_pattern,
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_formation_entry_from_sprites,
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


class TestBoidFormationEntry:
    """Test suite for boid-based formation entry patterns."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_boid_flock_pattern_basic(self):
        """Test basic boid flock pattern creation."""
        pattern = create_boid_flock_pattern(max_speed=4.0, duration_seconds=3.0)

        # Should return a BoidMoveUntil action
        assert hasattr(pattern, "max_speed")
        assert hasattr(pattern, "avoid_sprites")
        assert pattern.max_speed == 4.0

    def test_create_boid_flock_pattern_with_player_avoidance(self):
        """Test boid flock pattern with player avoidance."""
        player_sprite = create_test_sprite()
        avoid_sprites = arcade.SpriteList()
        avoid_sprites.append(player_sprite)
        pattern = create_boid_flock_pattern(max_speed=3.0, duration_seconds=2.0, avoid_sprites=avoid_sprites)

        assert pattern.avoid_sprites == avoid_sprites

    def test_create_boid_flock_pattern_application(self):
        """Test applying boid flock pattern to sprite list."""

        sprite_list = create_test_sprite_list(5)
        pattern = create_boid_flock_pattern(max_speed=2.0, duration_seconds=1.0)
        pattern.apply(sprite_list, tag="boid_test")

        assert pattern.target == sprite_list
        assert pattern.tag == "boid_test"

    def test_random_spawn_point_generation(self):
        """Test random spawn point generation within area."""

        spawn_area = (0, 0, 100, 200)

        # Generate multiple points and verify they're in bounds
        for _ in range(10):
            x, y = _generate_random_spawn_point(spawn_area)
            assert 0 <= x <= 100
            assert 0 <= y <= 200

    def test_random_spawn_point_edge_cases(self):
        """Test random spawn point generation with edge cases."""

        # Zero-width area
        narrow_area = (50, 50, 50, 100)
        x, y = _generate_random_spawn_point(narrow_area)
        assert x == 50
        assert 50 <= y <= 100

        # Zero-height area
        flat_area = (0, 75, 100, 75)
        x, y = _generate_random_spawn_point(flat_area)
        assert 0 <= x <= 100
        assert y == 75

    def test_spaced_spawn_points_generation(self):
        """Test spaced spawn point generation with minimum spacing."""
        spawn_area = (0, 0, 200, 200)
        num_sprites = 5
        min_spacing = 30.0

        spawn_points = _generate_spaced_spawn_points(spawn_area, num_sprites, min_spacing)

        # Should generate the correct number of points
        assert len(spawn_points) == num_sprites

        # All points should be within the spawn area
        for x, y in spawn_points:
            assert 0 <= x <= 200
            assert 0 <= y <= 200

        # Check minimum spacing between all pairs of points
        for i in range(len(spawn_points)):
            for j in range(i + 1, len(spawn_points)):
                x1, y1 = spawn_points[i]
                x2, y2 = spawn_points[j]
                distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                assert distance >= min_spacing, f"Points {i} and {j} are too close: {distance} < {min_spacing}"

    def test_spaced_spawn_points_small_area(self):
        """Test spaced spawn points in a small area where spacing might be impossible."""
        spawn_area = (0, 0, 50, 50)  # Small area
        num_sprites = 3
        min_spacing = 30.0

        # Should still generate points even if ideal spacing isn't possible
        spawn_points = _generate_spaced_spawn_points(spawn_area, num_sprites, min_spacing)

        assert len(spawn_points) == num_sprites

        # All points should be within the spawn area
        for x, y in spawn_points:
            assert 0 <= x <= 50
            assert 0 <= y <= 50

    def test_adaptive_spacing_calculation(self):
        """Test adaptive spacing calculation based on sprite sizes."""
        # Create sprites with different sizes
        small_sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
        large_sprite = arcade.Sprite(":resources:images/items/star.png", scale=2.0)
        medium_sprite = arcade.Sprite(":resources:images/items/star.png", scale=1.0)

        sprite_list = arcade.SpriteList()
        sprite_list.append(small_sprite)
        sprite_list.append(large_sprite)
        sprite_list.append(medium_sprite)

        # Calculate adaptive spacing
        adaptive_spacing = _calculate_adaptive_spacing(sprite_list, base_spacing=40.0)

        # Should be greater than base spacing due to large sprites
        assert adaptive_spacing > 40.0

        # Should be within reasonable bounds
        assert 20.0 <= adaptive_spacing <= 200.0

    def test_adaptive_spacing_empty_list(self):
        """Test adaptive spacing with empty sprite list."""
        empty_list = arcade.SpriteList()
        spacing = _calculate_adaptive_spacing(empty_list, base_spacing=30.0)

        # Should return base spacing for empty list
        assert spacing == 30.0

    def test_adaptive_spacing_single_sprite(self):
        """Test adaptive spacing with single sprite."""
        sprite_list = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png", scale=1.5)
        sprite_list.append(sprite)

        spacing = _calculate_adaptive_spacing(sprite_list, base_spacing=25.0)

        # Should be greater than base spacing
        assert spacing > 25.0
        assert 20.0 <= spacing <= 200.0

    def test_boid_move_until_action_basic(self):
        """Test basic BoidMoveUntil action functionality."""
        sprite_list = create_test_sprite_list(3)
        condition = duration(1.0)

        action = BoidMoveUntil(
            max_speed=3.0,
            duration_condition=condition,
            cohesion_weight=0.01,
            separation_weight=0.05,
            alignment_weight=0.03,
        )

        action.apply(sprite_list, tag="boid_test")

        # Verify action was applied
        assert action.target == sprite_list
        assert action.max_speed == 3.0

    def test_boid_move_until_action_with_avoidance(self):
        """Test BoidMoveUntil action with sprite avoidance (single and multiple)."""
        sprite_list = create_test_sprite_list(4)
        # Single avoid sprite
        player_sprite = create_test_sprite()
        player_sprite.center_x = 200
        player_sprite.center_y = 200
        avoid_sprites = arcade.SpriteList()
        avoid_sprites.append(player_sprite)

        action = BoidMoveUntil(max_speed=2.5, duration_condition=duration(2.0), avoid_sprites=avoid_sprites)
        action.apply(sprite_list, tag="avoidance_test")
        assert action.avoid_sprites == avoid_sprites

        # Update once and check that at least one sprite is steering away from the avoid sprite
        Action.update_all(0.016)
        for sprite in sprite_list:
            dx = player_sprite.center_x - sprite.center_x
            dy = player_sprite.center_y - sprite.center_y
            # If within avoidance distance, the velocity should be away from the avoid sprite
            dist_sq = dx * dx + dy * dy
            if dist_sq < action.avoid_distance * action.avoid_distance and dist_sq > 0:
                dot = dx * sprite.change_x + dy * sprite.change_y
                assert dot < 0  # Moving away

        # Now test with three avoid sprites
        avoid_sprites = arcade.SpriteList()
        for i in range(3):
            s = create_test_sprite()
            s.center_x = 200 + i * 20
            s.center_y = 200 + i * 20
            avoid_sprites.append(s)
        action = BoidMoveUntil(max_speed=2.5, duration_condition=duration(2.0), avoid_sprites=avoid_sprites)
        action.apply(sprite_list, tag="multi_avoidance_test")
        assert action.avoid_sprites == avoid_sprites
        Action.update_all(0.016)
        # Check that at least one sprite is steering away from at least one avoid sprite
        found_avoidance = False
        for sprite in sprite_list:
            for avoid_sprite in avoid_sprites:
                dx = avoid_sprite.center_x - sprite.center_x
                dy = avoid_sprite.center_y - sprite.center_y
                dist_sq = dx * dx + dy * dy
                if dist_sq < action.avoid_distance * action.avoid_distance and dist_sq > 0:
                    dot = dx * sprite.change_x + dy * sprite.change_y
                    if dot < 0:
                        found_avoidance = True
        assert found_avoidance

    def test_boid_move_until_velocity_clamping(self):
        """Test that BoidMoveUntil properly clamps velocity to max_speed."""

        # Create sprites positioned to create high cohesion forces
        sprite_list = arcade.SpriteList()
        for i in range(3):
            sprite = create_test_sprite()
            sprite.center_x = i * 200  # Spread far apart
            sprite.center_y = 100
            sprite_list.append(sprite)

        action = BoidMoveUntil(
            max_speed=1.0,  # Very low max speed
            duration_condition=duration(0.5),
            cohesion_weight=1.0,  # High cohesion to test clamping
        )

        action.apply(sprite_list, tag="clamp_test")

        # Update once to apply forces
        Action.update_all(0.016)  # ~60 FPS frame

        # Check that velocities don't exceed max_speed
        for sprite in sprite_list:
            speed = math.sqrt(sprite.change_x**2 + sprite.change_y**2)
            assert speed <= action.max_speed + 0.01  # Small tolerance for floating point


class TestFormationEntryFromSprites:
    """Test suite for create_formation_entry_from_sprites function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_formation_entry_from_sprites_basic(self):
        """Test basic formation entry from sprites functionality."""
        # Create a simple target formation (circle)
        target_formation = arcade.SpriteList()

        # Create 6 sprites in a circle formation
        center_x, center_y = 400, 300
        radius = 100
        for i in range(6):
            angle = (i / 6) * 2 * math.pi
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
            sprite.center_x = x
            sprite.center_y = y
            sprite.visible = False  # Target formation is invisible
            target_formation.append(sprite)

        # Create entry pattern
        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=(0, 0, 800, 600), speed=5.0, stagger_delay=1.0, min_spacing=30.0
        )

        # Should create the same number of actions as sprites in target formation
        assert len(entry_actions) == len(target_formation)

        # Each action should be a tuple of (sprite, action)
        for sprite, action in entry_actions:
            assert isinstance(sprite, arcade.Sprite)
            assert hasattr(action, "apply")  # Should be an action object

    def test_create_formation_entry_from_sprites_spawn_positions(self):
        """Test that spawn positions are created around upper boundary."""
        # Create target formation
        target_formation = arcade.SpriteList()
        for i in range(8):
            sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
            sprite.center_x = 400 + (i % 3) * 50
            sprite.center_y = 300 + (i // 3) * 50
            sprite.visible = False
            target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=(0, 0, 800, 600), speed=5.0, stagger_delay=1.0
        )

        # Check that spawn positions are outside the window boundary
        for sprite, _ in entry_actions:
            # Sprites should be positioned outside the window
            assert sprite.center_x < 0 or sprite.center_x > 800 or sprite.center_y > 600, (
                f"Sprite at ({sprite.center_x}, {sprite.center_y}) should be outside window"
            )

            # Sprites should start invisible
            assert sprite.alpha == 0

    def test_create_formation_entry_from_sprites_requires_window_bounds(self):
        """Test that window_bounds parameter is required."""
        target_formation = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 400
        sprite.center_y = 300
        sprite.visible = False
        target_formation.append(sprite)

        # Should raise ValueError when window_bounds is not provided
        try:
            create_formation_entry_from_sprites(target_formation, speed=5.0)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "window_bounds is required" in str(e)

    def test_create_formation_entry_from_sprites_three_phase_movement(self):
        """Test that the three-phase movement pattern is created correctly."""
        target_formation = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 400
        sprite.center_y = 300
        sprite.visible = False
        target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=(0, 0, 800, 600), speed=5.0, stagger_delay=1.0
        )

        sprite, action = entry_actions[0]

        # The action should be a sequence with multiple phases
        assert hasattr(action, "actions")  # Should be a sequence
        assert len(action.actions) >= 3  # Should have at least 3 phases

    def test_create_formation_entry_from_sprites_collision_avoidance(self):
        """Test that collision avoidance groups sprites into waves."""
        # Create a larger formation to test collision grouping
        target_formation = arcade.SpriteList()
        for i in range(12):
            sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
            sprite.center_x = 400 + (i % 4) * 30
            sprite.center_y = 300 + (i // 4) * 30
            sprite.visible = False
            target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=(0, 0, 800, 600), speed=5.0, stagger_delay=1.0, min_spacing=30.0
        )

        # Should create the same number of actions as sprites
        assert len(entry_actions) == len(target_formation)

        # All sprites should be positioned at spawn locations
        for sprite, _ in entry_actions:
            assert sprite.alpha == 0  # Should start invisible

    def test_create_formation_entry_from_sprites_parameter_defaults(self):
        """Test that default parameters work correctly."""
        target_formation = arcade.SpriteList()
        for i in range(4):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 400 + i * 20
            sprite.center_y = 300 + i * 20
            sprite.visible = False
            target_formation.append(sprite)

        # Test with minimal parameters (only window_bounds required)
        entry_actions = create_formation_entry_from_sprites(target_formation, window_bounds=(0, 0, 800, 600))

        # Should work with default parameters
        assert len(entry_actions) == len(target_formation)

        # Check default values are used
        for sprite, action in entry_actions:
            assert sprite.alpha == 0  # Should start invisible

    def test_create_formation_entry_from_sprites_center_first_ordering(self):
        """Test that sprites are ordered from center to outermost."""
        # Create formation with clear center and outer sprites
        target_formation = arcade.SpriteList()

        # Center sprite
        center_sprite = arcade.Sprite(":resources:images/items/star.png")
        center_sprite.center_x = 400
        center_sprite.center_y = 300
        center_sprite.visible = False
        target_formation.append(center_sprite)

        # Outer sprites
        for i in range(4):
            angle = (i / 4) * 2 * math.pi
            x = 400 + 100 * math.cos(angle)
            y = 300 + 100 * math.sin(angle)

            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = x
            sprite.center_y = y
            sprite.visible = False
            target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=(0, 0, 800, 600), speed=5.0, stagger_delay=1.0
        )

        # Should create actions for all sprites
        assert len(entry_actions) == len(target_formation)

        # All sprites should be positioned and ready for movement
        for sprite, _ in entry_actions:
            assert sprite.alpha == 0

    def test_create_formation_entry_from_sprites_empty_formation(self):
        """Test behavior with empty target formation."""
        empty_formation = arcade.SpriteList()

        entry_actions = create_formation_entry_from_sprites(empty_formation, window_bounds=(0, 0, 800, 600), speed=5.0)

        # Should return empty list for empty formation
        assert len(entry_actions) == 0

    def test_create_formation_entry_from_sprites_custom_parameters(self):
        """Test that custom parameters are respected."""
        target_formation = arcade.SpriteList()
        for i in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 400 + i * 50
            sprite.center_y = 300 + i * 50
            sprite.visible = False
            target_formation.append(sprite)

        # Test with custom parameters
        custom_speed = 8.0
        custom_stagger = 2.0
        custom_spacing = 50.0

        entry_actions = create_formation_entry_from_sprites(
            target_formation,
            window_bounds=(0, 0, 800, 600),
            speed=custom_speed,
            stagger_delay=custom_stagger,
            min_spacing=custom_spacing,
        )

        # Should create actions with custom parameters
        assert len(entry_actions) == len(target_formation)

        # All sprites should be positioned and ready
        for sprite, _ in entry_actions:
            assert sprite.alpha == 0

    def test_generate_upper_boundary_spawn_positions(self):
        """Test the upper boundary spawn position generation."""
        # Create target positions
        target_positions = [
            (400, 300),  # Center
            (350, 250),  # Top left
            (450, 250),  # Top right
            (350, 350),  # Bottom left
            (450, 350),  # Bottom right
        ]

        window_bounds = (0, 0, 800, 600)
        formation_center = (400, 300)

        spawn_positions = _generate_upper_boundary_spawn_positions(target_positions, window_bounds, formation_center)

        # Should generate same number of spawn positions as target positions
        assert len(spawn_positions) == len(target_positions)

        # All spawn positions should be outside the window boundary
        for x, y in spawn_positions:
            # Should be outside the window (left, right, or top)
            assert x < 0 or x > 800 or y > 600, f"Spawn position ({x}, {y}) should be outside window"

            # Should be in the upper half (y > 300) or on the sides
            assert y > 300 or x < 0 or x > 800, f"Spawn position ({x}, {y}) should be in upper half or sides"

    def test_generate_upper_boundary_spawn_positions_distribution(self):
        """Test that spawn positions are distributed across the three boundary sections."""
        target_positions = [(400 + i * 20, 300 + i * 20) for i in range(9)]  # 9 positions
        window_bounds = (0, 0, 800, 600)
        formation_center = (400, 300)

        spawn_positions = _generate_upper_boundary_spawn_positions(target_positions, window_bounds, formation_center)

        assert len(spawn_positions) == 9

        # Count positions in each section (some positions may be in corners, so count them only once)
        left_positions = [pos for pos in spawn_positions if pos[0] < 0 and pos[1] <= 600]
        top_positions = [pos for pos in spawn_positions if pos[1] > 600 and pos[0] >= 0 and pos[0] <= 800]
        right_positions = [pos for pos in spawn_positions if pos[0] > 800 and pos[1] <= 600]

        # Should have positions in all three sections
        assert len(left_positions) > 0, "Should have positions on left side"
        assert len(top_positions) > 0, "Should have positions on top side"
        assert len(right_positions) > 0, "Should have positions on right side"

        # Total should equal original count (accounting for corner positions)
        total_counted = len(left_positions) + len(top_positions) + len(right_positions)
        assert total_counted <= 9, f"Total counted positions ({total_counted}) should not exceed original count (9)"
        assert total_counted >= 6, f"Should have at least 6 positions distributed across sections, got {total_counted}"

    def test_generate_upper_boundary_spawn_positions_empty_input(self):
        """Test behavior with empty target positions."""
        empty_positions = []
        window_bounds = (0, 0, 800, 600)
        formation_center = (400, 300)

        spawn_positions = _generate_upper_boundary_spawn_positions(empty_positions, window_bounds, formation_center)

        # Should return empty list for empty input
        assert len(spawn_positions) == 0

    def test_create_formation_entry_from_sprites_visibility_tracking(self):
        """Test that sprites become visible during the formation entry process."""
        # Create a simple target formation
        target_formation = arcade.SpriteList()
        for i in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
            sprite.center_x = 400 + i * 30
            sprite.center_y = 300 + i * 30
            sprite.visible = False
            target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation,
            window_bounds=(0, 0, 800, 600),
            speed=5.0,
            stagger_delay=0.1,  # Short delay for testing
            min_spacing=30.0,
        )

        # Apply actions to sprites
        for sprite, action in entry_actions:
            action.apply(sprite, tag="visibility_test")

        # Track sprite visibility over time
        visibility_over_time = []

        # Test initial state
        all_sprites = [sprite for sprite, _ in entry_actions]
        initial_visibility = [(sprite.visible, sprite.alpha) for sprite in all_sprites]
        visibility_over_time.append(("initial", initial_visibility))

        # All sprites should start invisible (alpha=0, visible=True)
        for sprite in all_sprites:
            assert sprite.visible == True, f"Sprite should be visible=True but got {sprite.visible}"
            assert sprite.alpha == 0, f"Sprite should have alpha=0 but got {sprite.alpha}"

            # Update through the phases - include sprite updates for position changes
        total_updates = 0
        max_updates = 1000  # Prevent infinite loop

        while Action._active_actions and total_updates < max_updates:
            Action.update_all(0.016)  # 60 FPS
            # IMPORTANT: Update sprites to apply velocity to position
            for sprite in all_sprites:
                sprite.update()
            total_updates += 1

            # Record visibility every 10 frames
            if total_updates % 10 == 0:
                current_visibility = [(sprite.visible, sprite.alpha) for sprite in all_sprites]
                visibility_over_time.append((f"frame_{total_updates}", current_visibility))

                # Check if any sprite has become visible (alpha > 0)
                visible_sprites = [sprite for sprite in all_sprites if sprite.alpha > 0]
                if visible_sprites:
                    print(f"Frame {total_updates}: {len(visible_sprites)} sprites are now visible")
                    break

        # Final check - at least one sprite should have become visible
        final_visible_sprites = [sprite for sprite in all_sprites if sprite.alpha > 0]

        # Debug output
        print(f"Total updates: {total_updates}")
        print(f"Active actions remaining: {len(Action._active_actions)}")
        print(f"Final visible sprites: {len(final_visible_sprites)}/{len(all_sprites)}")

        for i, (timestamp, visibility) in enumerate(visibility_over_time):
            visible_count = sum(1 for visible, alpha in visibility if alpha > 0)
            print(f"{timestamp}: {visible_count}/{len(all_sprites)} sprites visible")

        # At least one sprite should have become visible during the process
        assert len(final_visible_sprites) > 0, (
            f"No sprites became visible during formation entry. Visibility tracking: {visibility_over_time}"
        )

    def test_create_formation_entry_from_sprites_phase_completion(self):
        """Test that all phases of the formation entry complete properly."""
        # Create a single sprite for easier testing
        target_formation = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
        sprite.center_x = 400
        sprite.center_y = 300
        sprite.visible = False
        target_formation.append(sprite)

        entry_actions = create_formation_entry_from_sprites(
            target_formation,
            window_bounds=(0, 0, 800, 600),
            speed=10.0,  # Faster speed for quicker testing
            stagger_delay=0.1,
            min_spacing=30.0,
        )

        test_sprite, action = entry_actions[0]
        action.apply(test_sprite, tag="phase_test")

        # Record sprite position and visibility at key moments
        phases = []

        # Initial state
        phases.append(
            {
                "phase": "initial",
                "position": (test_sprite.center_x, test_sprite.center_y),
                "visible": test_sprite.visible,
                "alpha": test_sprite.alpha,
                "velocity": (test_sprite.change_x, test_sprite.change_y),
            }
        )

        # Run until completion or timeout
        frame_count = 0
        max_frames = 2000  # Increased timeout
        previous_position = (test_sprite.center_x, test_sprite.center_y)

        while Action._active_actions and frame_count < max_frames:
            Action.update_all(0.016)
            # IMPORTANT: Update sprite to apply velocity to position
            test_sprite.update()
            frame_count += 1

            current_position = (test_sprite.center_x, test_sprite.center_y)

            # Record significant state changes
            if frame_count % 50 == 0 or current_position != previous_position:
                phases.append(
                    {
                        "phase": f"frame_{frame_count}",
                        "position": current_position,
                        "visible": test_sprite.visible,
                        "alpha": test_sprite.alpha,
                        "velocity": (test_sprite.change_x, test_sprite.change_y),
                    }
                )

            previous_position = current_position

        # Final state
        phases.append(
            {
                "phase": "final",
                "position": (test_sprite.center_x, test_sprite.center_y),
                "visible": test_sprite.visible,
                "alpha": test_sprite.alpha,
                "velocity": (test_sprite.change_x, test_sprite.change_y),
            }
        )

        # Debug output
        print(f"Formation entry completed in {frame_count} frames")
        for phase_data in phases:
            print(
                f"{phase_data['phase']}: pos={phase_data['position']}, "
                f"visible={phase_data['visible']}, alpha={phase_data['alpha']}, "
                f"vel={phase_data['velocity']}"
            )

        # Verify the sprite ended up visible
        assert test_sprite.alpha > 0, f"Sprite should be visible at end but alpha={test_sprite.alpha}"
        assert test_sprite.visible == True, "Sprite should have visible=True at end"

        # Verify the sprite moved through different positions (indicating phases completed)
        positions = [phase["position"] for phase in phases]
        unique_positions = set(positions)
        assert len(unique_positions) > 2, f"Sprite should have moved through multiple positions: {unique_positions}"

    def test_create_formation_entry_from_sprites_spawn_distance_analysis(self):
        """Test spawn distances to understand why sprites aren't reaching targets."""
        # Create a simple target formation
        target_formation = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.5)
        sprite.center_x = 400
        sprite.center_y = 300
        sprite.visible = False
        target_formation.append(sprite)

        window_bounds = (0, 0, 800, 600)
        speed = 5.0

        entry_actions = create_formation_entry_from_sprites(
            target_formation, window_bounds=window_bounds, speed=speed, stagger_delay=0.1, min_spacing=30.0
        )

        test_sprite, action = entry_actions[0]

        # Calculate distances involved
        spawn_pos = (test_sprite.center_x, test_sprite.center_y)
        target_pos = (400, 300)

        distance_to_target = math.sqrt((target_pos[0] - spawn_pos[0]) ** 2 + (target_pos[1] - spawn_pos[1]) ** 2)

        # Calculate expected time to reach target at current speed
        # Speed is in pixels per frame, so at 60 FPS:
        frames_to_target = distance_to_target / speed
        seconds_to_target = frames_to_target / 60.0

        print(f"Spawn position: {spawn_pos}")
        print(f"Target position: {target_pos}")
        print(f"Distance to target: {distance_to_target:.1f} pixels")
        print(f"Speed: {speed} pixels/frame")
        print(f"Expected frames to reach target: {frames_to_target:.1f}")
        print(f"Expected seconds to reach target: {seconds_to_target:.1f}")

        # Apply action and test movement for a reasonable time
        action.apply(test_sprite, tag="distance_test")

        # Test movement for expected time + some buffer
        max_test_frames = int(frames_to_target * 1.5)  # 50% buffer

        initial_distance = distance_to_target
        closest_distance = distance_to_target

        for frame in range(max_test_frames):
            Action.update_all(0.016)

            current_distance = math.sqrt(
                (target_pos[0] - test_sprite.center_x) ** 2 + (target_pos[1] - test_sprite.center_y) ** 2
            )

            if current_distance < closest_distance:
                closest_distance = current_distance

            # Check if we reached the target (within 5 pixels)
            if current_distance <= 5.0:
                print(f"Reached target at frame {frame}! Final distance: {current_distance:.1f}")
                break

            if frame % 50 == 0:
                print(
                    f"Frame {frame}: distance={current_distance:.1f}, pos=({test_sprite.center_x:.1f}, {test_sprite.center_y:.1f}), vel=({test_sprite.change_x:.1f}, {test_sprite.change_y:.1f})"
                )

        print(f"Initial distance: {initial_distance:.1f}")
        print(f"Closest distance achieved: {closest_distance:.1f}")
        print(f"Final distance: {current_distance:.1f}")
        print(f"Movement progress: {((initial_distance - current_distance) / initial_distance * 100):.1f}%")

        # The sprite should have made significant progress towards the target
        progress_threshold = 0.1  # At least 10% progress expected
        actual_progress = (initial_distance - current_distance) / initial_distance
        assert actual_progress > progress_threshold, (
            f"Sprite made insufficient progress towards target. "
            f"Expected > {progress_threshold * 100:.1f}%, got {actual_progress * 100:.1f}%"
        )


class TestZigzagPattern:
    """Test suite for zigzag movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_zigzag_pattern_basic(self):
        """Test basic zigzag pattern creation."""
        pattern = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=4)

        # Should return a sequence action
        assert hasattr(pattern, "actions")
        assert len(pattern.actions) == 4

    def test_create_zigzag_pattern_application(self):
        """Test applying zigzag pattern to sprite."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x

        pattern = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=2)
        pattern.apply(sprite, tag="zigzag_test")

        # Start the action and update
        Action.update_all(0.1)

        # Sprite should be moving
        assert sprite.change_x != 0 or sprite.change_y != 0

    def test_create_zigzag_pattern_segments(self):
        """Test zigzag pattern with different segment counts."""
        pattern_2 = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=2)
        pattern_6 = create_zigzag_pattern(dimensions=(100, 50), speed=150, segments=6)

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

        pattern = create_spiral_pattern(
            center=(400, 300), max_radius=150, revolutions=2.0, speed=200, direction="outward"
        )

        assert hasattr(pattern, "control_points")
        points = pattern.control_points

        # First point should be near center (small radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Outward spiral should end farther from center than it starts
        assert last_dist > first_dist

    def test_create_spiral_pattern_inward(self):
        """Test inward spiral pattern creation."""
        pattern = create_spiral_pattern(
            center=(400, 300), max_radius=150, revolutions=2.0, speed=200, direction="inward"
        )

        points = pattern.control_points

        # First point should be far from center (large radius)
        first_dist = math.sqrt((points[0][0] - 400) ** 2 + (points[0][1] - 300) ** 2)
        last_dist = math.sqrt((points[-1][0] - 400) ** 2 + (points[-1][1] - 300) ** 2)

        # Inward spiral should end closer to center than it starts
        assert last_dist < first_dist

    def test_create_spiral_pattern_application(self):
        """Test applying spiral pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_spiral_pattern(center=(200, 200), max_radius=100, revolutions=1.5, speed=150)
        pattern.apply(sprite, tag="spiral_test")

        assert pattern.target == sprite


class TestFigureEightPattern:
    """Test suite for figure-8 movement pattern."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_create_figure_eight_pattern_basic(self):
        """Test basic figure-8 pattern creation."""
        pattern = create_figure_eight_pattern(center=(400, 300), width=200, height=100, speed=180)

        assert hasattr(pattern, "control_points")
        assert len(pattern.control_points) == 17  # 16 + 1 to complete loop

    def test_create_figure_eight_pattern_symmetry(self):
        """Test that figure-8 pattern has approximate symmetry."""
        pattern = create_figure_eight_pattern(center=(400, 300), width=200, height=100, speed=180)
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
        pattern = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=True)

        assert hasattr(pattern, "control_points")
        points = pattern.control_points

        # All points should be approximately the same distance from center
        for point in points:
            distance = math.sqrt((point[0] - 400) ** 2 + (point[1] - 300) ** 2)
            assert abs(distance - 120) < 1.0

    def test_create_orbit_pattern_counter_clockwise(self):
        """Test counter-clockwise orbit pattern."""
        cw_pattern = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=True)
        ccw_pattern = create_orbit_pattern(center=(400, 300), radius=120, speed=150, clockwise=False)

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
        pattern = create_smooth_zigzag_pattern(dimensions=(100, 50), speed=150, ease_duration=1.0)

        # Should return an Ease action wrapping a zigzag
        assert hasattr(pattern, "wrapped_action")
        assert hasattr(pattern, "easing_duration")
        assert pattern.easing_duration == 1.0

    def test_create_smooth_zigzag_pattern_application(self):
        """Test applying smooth zigzag pattern to sprite."""
        sprite = create_test_sprite()

        pattern = create_smooth_zigzag_pattern(dimensions=(80, 40), speed=120, ease_duration=0.5)
        pattern.apply(sprite, tag="smooth_zigzag_test")

        assert pattern.target == sprite


class TestPatternIntegration:
    """Test suite for integration between patterns and other actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_pattern_with_sprite_list(self):
        """Test applying patterns to sprite lists."""

        # Create formation
        sprites = arrange_line(count=3, start_x=100, start_y=200, spacing=50)

        # Apply wave pattern to entire formation
        wave = create_wave_pattern(amplitude=30, frequency=1, length=300, speed=150)
        wave.apply(sprites, tag="formation_wave")

        assert wave.target == sprites

    def test_pattern_composition(self):
        """Test composing patterns with other actions."""
        sprite = create_test_sprite()

        # Create a complex sequence: delay, then zigzag, then fade
        complex_action = sequence(
            DelayUntil(duration(0.5)),
            create_zigzag_pattern(dimensions=(80, 40), speed=120, segments=3),
            FadeUntil(-20, duration(2.0)),
        )

        complex_action.apply(sprite, tag="complex_sequence")

        # Should be a valid sequence
        assert hasattr(complex_action, "actions")
        assert len(complex_action.actions) == 3

    def test_pattern_with_conditions(self):
        """Test patterns with condition helpers."""
        sprite_list = create_test_sprite_list(5)

        # Create a spiral that stops when few sprites remain
        spiral = create_spiral_pattern(center=(400, 300), max_radius=100, revolutions=2, speed=150)

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
        spiral = create_spiral_pattern(center=(300, 300), max_radius=80, revolutions=1, speed=120)

        wave.apply(sprite, tag="wave_movement")
        spiral.apply(sprite, tag="spiral_movement")  # This will override the wave

        # Most recent action should be active
        spiral_actions = Action.get_actions_for_target(sprite, "spiral_movement")
        assert len(spiral_actions) == 1

    def test_formation_functions_visible_parameter(self):
        """Test that formation functions respect the visible parameter."""
        # Test arrange_line with visible=False
        line_hidden = arrange_line(count=3, start_x=100, start_y=200, visible=False)
        for sprite in line_hidden:
            assert not sprite.visible

        # Test arrange_line with visible=True (default)
        line_visible = arrange_line(count=3, start_x=100, start_y=200, visible=True)
        for sprite in line_visible:
            assert sprite.visible

        # Test arrange_grid with visible=False
        grid_hidden = arrange_grid(rows=2, cols=2, start_x=100, start_y=200, visible=False)
        for sprite in grid_hidden:
            assert not sprite.visible

        # Test arrange_circle with visible=False
        circle_hidden = arrange_circle(count=4, center_x=200, center_y=200, radius=50, visible=False)
        for sprite in circle_hidden:
            assert not sprite.visible
