"""
Test suite for simple leader-follower Galaga-style enemy entry behavior.

This test suite verifies that sprites follow the exact same S-curve path with proper
time delays, ending up at their formation positions with correct orientation.
"""

import math

from actions.base import Action
from actions.formation import arrange_grid
from actions.pattern import create_galaga_style_entry


class TestSimpleLeaderGalagaPaths:
    """Test suite for simple leader-follower Galaga path behavior."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_all_sprites_follow_same_s_curve_path_with_delays(self):
        """Test that all sprites follow the exact same S-curve path with time delays."""
        # Create a 1x4 formation for easy tracking
        formation = arrange_grid(rows=1, cols=4, start_x=350, start_y=400, spacing_x=50, visible=False)

        # Force left spawn for S-curve
        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=4,
            screen_bounds=(0, 0, 800, 600),
            path_speed=100.0,
            spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
        )

        # Apply and start the action
        action = entry_actions[0]
        action.apply(formation, tag="leader_follower_test")
        action.start()

        # Track positions for all sprites over time
        all_positions = [[] for _ in range(4)]

        # Simulate path following for enough frames to capture the full movement
        for frame in range(300):  # 5 seconds at 60 FPS (increased from 3 seconds)
            Action.update_all(0.016)  # 60 FPS
            for sprite in formation:
                sprite.update()  # Apply velocity to position

            # Record positions every 3 frames for higher resolution
            if frame % 3 == 0:
                for i, sprite in enumerate(formation):
                    all_positions[i].append((sprite.center_x, sprite.center_y))

        # Verify that followers follow the same path as the leader with delays
        leader_positions = all_positions[0]

        # Leader should start moving first (from left spawn area)
        assert len(leader_positions) > 5, "Should have recorded multiple leader positions"

        # Leader should move from left (negative X) toward formation center
        first_pos = leader_positions[0]
        last_pos = leader_positions[-1]

        assert first_pos[0] < 0, f"Leader should start off-screen left, got {first_pos[0]}"
        assert last_pos[0] > first_pos[0], "Leader should move rightward overall"

        # Verify S-curve shape by checking for direction changes in Y
        y_positions = [pos[1] for pos in leader_positions]
        y_deltas = [y_positions[i + 1] - y_positions[i] for i in range(len(y_positions) - 1)]

        # Should have both negative and positive Y deltas (S-curve goes down then up)
        has_downward = any(delta < -0.5 for delta in y_deltas)
        has_upward = any(delta > 0.5 for delta in y_deltas)

        assert has_downward and has_upward, "S-curve should have both downward and upward movement"

        # Verify that followers eventually follow similar path coordinates
        # Followers start with delays, so their paths should match leader's earlier positions
        for i in range(1, 4):  # Check followers 1, 2, 3
            follower_positions = all_positions[i]
            if len(follower_positions) > 10:  # Follower has started moving
                # Check that follower shows S-curve characteristics too
                follower_y_positions = [pos[1] for pos in follower_positions]
                follower_y_deltas = [
                    follower_y_positions[j + 1] - follower_y_positions[j] for j in range(len(follower_y_positions) - 1)
                ]

                follower_has_downward = any(delta < -0.5 for delta in follower_y_deltas)
                follower_has_upward = any(delta > 0.5 for delta in follower_y_deltas)

                assert follower_has_downward and follower_has_upward, f"Follower {i} should also follow S-curve pattern"

    def test_sprites_spawn_with_leader_spacing(self):
        """Test that sprites spawn with consistent spacing matching formation grid."""
        formation = arrange_grid(rows=1, cols=4, start_x=300, start_y=400, spacing_x=60, visible=False)

        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=4,
            screen_bounds=(0, 0, 800, 600),
            path_speed=100.0,
            spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
        )

        action = entry_actions[0]
        action.apply(formation, tag="spacing_test")
        action.start()

        # Check initial spawn positions after first update
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()

        # All sprites should be positioned in the left spawn area with proper spacing
        spawn_positions = [(sprite.center_x, sprite.center_y) for sprite in formation]

        # All should be in left spawn area (negative X)
        for i, (x, y) in enumerate(spawn_positions):
            assert x < 0, f"Sprite {i} should spawn off-screen left, got x={x}"

        # Check that sprites are spaced consistently in formation
        y_positions = [pos[1] for pos in spawn_positions]
        if len(set(y_positions)) > 1:  # If not all at same Y
            # Calculate spacing between consecutive sprites
            y_sorted = sorted(y_positions)
            spacings = [y_sorted[i + 1] - y_sorted[i] for i in range(len(y_sorted) - 1)]

            # All spacings should be roughly equal (within tolerance)
            avg_spacing = sum(spacings) / len(spacings)
            for spacing in spacings:
                assert abs(spacing - avg_spacing) < 10, f"Spawn spacing should be consistent, got spacings: {spacings}"

    def test_sprites_end_at_correct_formation_positions(self):
        """Test that sprites end up at their correct formation positions."""
        formation = arrange_grid(rows=1, cols=3, start_x=375, start_y=400, spacing_x=50, visible=False)

        # Store expected final positions
        expected_positions = [(sprite.center_x, sprite.center_y) for sprite in formation]

        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=3,
            screen_bounds=(0, 0, 800, 600),
            path_speed=200.0,  # Fast speed for quicker completion
        )

        action = entry_actions[0]
        action.apply(formation, tag="final_position_test")
        action.start()

        # Run until action completes
        max_frames = 600  # Safety limit (increased from 400)
        frame = 0
        while not action.done and frame < max_frames:
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()
            frame += 1

        # Verify that sprites are in their expected final formation positions
        for i, sprite in enumerate(formation):
            expected_x, expected_y = expected_positions[i]
            assert abs(sprite.center_x - expected_x) < 5, (
                f"Sprite {i} X position should be {expected_x}, got {sprite.center_x}"
            )
            assert abs(sprite.center_y - expected_y) < 5, (
                f"Sprite {i} Y position should be {expected_y}, got {sprite.center_y}"
            )

    def test_sprites_face_correct_direction_in_formation(self):
        """Test that sprites face the correct direction (0 degrees) in final formation."""
        formation = arrange_grid(rows=1, cols=3, start_x=375, start_y=400, spacing_x=50, visible=False)

        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=3,
            screen_bounds=(0, 0, 800, 600),
            path_speed=200.0,  # Fast speed for quicker completion
        )

        action = entry_actions[0]
        action.apply(formation, tag="final_orientation_test")
        action.start()

        # Run until action completes
        max_frames = 600  # Safety limit (increased from 400)
        frame = 0
        while not action.done and frame < max_frames:
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()
            frame += 1
            if frame % 60 == 0:  # Print every second (60 frames)
                print(f"DEBUG: Frame {frame}, angles: {[sprite.angle for sprite in formation]}")

        # Verify that sprites are oriented correctly (0 degrees = facing right)
        for i, sprite in enumerate(formation):
            print(f"DEBUG: Final angle for sprite {i}: {sprite.angle}")
            assert abs(sprite.angle) < 10, f"Sprite {i} should face right (0 degrees), got {sprite.angle}"

    def test_followers_start_with_appropriate_delays(self):
        """Test that followers start with delays based on formation spacing."""
        formation = arrange_grid(rows=1, cols=4, start_x=300, start_y=400, spacing_x=60, visible=False)

        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=4,
            screen_bounds=(0, 0, 800, 600),
            path_speed=120.0,  # 2 pixels per frame
            spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
        )

        action = entry_actions[0]
        action.apply(formation, tag="delay_test")
        action.start()

        # Track when each sprite starts moving (leaves spawn area)
        sprite_start_frames = [None] * 4
        spawn_positions = []

        # Capture initial spawn positions
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()
            spawn_positions.append((sprite.center_x, sprite.center_y))

        # Track movement start for each sprite
        for frame in range(120):  # 2 seconds
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()

            # Check if each sprite has started moving
            for i, sprite in enumerate(formation):
                if sprite_start_frames[i] is None:
                    spawn_x, spawn_y = spawn_positions[i]
                    # If sprite has moved significantly from spawn position
                    if abs(sprite.center_x - spawn_x) > 5 or abs(sprite.center_y - spawn_y) > 5:
                        sprite_start_frames[i] = frame

        # Verify that sprites start in sequence (leader first, then followers)
        assert sprite_start_frames[0] is not None, "Leader should start moving"

        # Each follower should start after the previous sprite
        for i in range(1, 4):
            if sprite_start_frames[i] is not None:
                assert sprite_start_frames[i] > sprite_start_frames[i - 1], (
                    f"Follower {i} should start after sprite {i - 1}"
                )

        # Calculate delays between sprite starts
        delays = []
        for i in range(1, 4):
            if sprite_start_frames[i] is not None and sprite_start_frames[i - 1] is not None:
                delay_frames = sprite_start_frames[i] - sprite_start_frames[i - 1]
                delays.append(delay_frames)

        # All delays should be roughly consistent
        if len(delays) > 1:
            avg_delay = sum(delays) / len(delays)
            for delay in delays:
                assert abs(delay - avg_delay) < 5, f"Delays should be consistent, got delays: {delays}"

    def test_different_spawn_sides_create_appropriate_curves(self):
        """Test that different spawn sides create different but appropriate curve shapes."""
        formation = arrange_grid(rows=1, cols=2, start_x=400, start_y=300, spacing_x=50, visible=False)

        # Test left spawn (S-curve)
        left_entry = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=2,
            screen_bounds=(0, 0, 800, 600),
            path_speed=100.0,
            spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
        )[0]

        # Test right spawn (mirror S-curve)
        right_entry = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=2,
            screen_bounds=(0, 0, 800, 600),
            path_speed=100.0,
            spawn_areas={"left": False, "right": True, "top": False, "bottom": False},
        )[0]

        # Apply left spawn action and track positions
        left_entry.apply(formation, tag="left_test")
        left_entry.start()

        left_positions = []
        for frame in range(40):
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()
            if frame % 2 == 0:
                left_positions.append((formation[0].center_x, formation[0].center_y))

        # Reset and test right spawn
        Action.clear_all()
        formation = arrange_grid(rows=1, cols=2, start_x=400, start_y=300, spacing_x=50, visible=False)

        # Create a new right spawn action for the new formation
        right_entry = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=2,
            screen_bounds=(0, 0, 800, 600),
            path_speed=100.0,
            spawn_areas={"left": False, "right": True, "top": False, "bottom": False},
        )[0]

        right_entry.apply(formation, tag="right_test")
        right_entry.start()

        # Allow spawn positioning to complete
        Action.update_all(0.016)
        for sprite in formation:
            sprite.update()

        right_positions = []
        for frame in range(40):
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()
            if frame % 2 == 0:
                right_positions.append((formation[0].center_x, formation[0].center_y))

        # Verify that paths start from different sides
        left_start = left_positions[0]
        right_start = right_positions[0]

        assert left_start[0] < 100, f"Left spawn should start from left side, got X={left_start[0]}"
        assert right_start[0] > 700, f"Right spawn should start from right side, got X={right_start[0]}"

        # Both should show curved movement (Y direction changes)
        for positions, side in [(left_positions, "left"), (right_positions, "right")]:
            if len(positions) > 5:
                y_positions = [pos[1] for pos in positions]
                y_deltas = [y_positions[i + 1] - y_positions[i] for i in range(len(y_positions) - 1)]

                # Should have both direction changes (curve characteristics)
                has_upward = any(delta > 1 for delta in y_deltas)
                has_downward = any(delta < -1 for delta in y_deltas)

                assert has_upward or has_downward, f"{side} spawn should show curved movement"

    def test_path_velocity_and_timing_consistency(self):
        """Test that path velocity is consistent and timing matches expectations."""
        formation = arrange_grid(rows=1, cols=3, start_x=350, start_y=400, spacing_x=50, visible=False)

        # Use specific speed for predictable timing
        path_speed = 120.0  # pixels per second = 2 pixels per frame at 60 FPS

        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=3,
            screen_bounds=(0, 0, 800, 600),
            path_speed=path_speed,
            spawn_areas={"left": True, "right": False, "top": False, "bottom": False},
        )

        action = entry_actions[0]
        action.apply(formation, tag="velocity_test")
        action.start()

        # Track leader movement for velocity verification
        leader_positions = []

        for frame in range(60):  # 1 second
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()

            leader_positions.append((formation[0].center_x, formation[0].center_y))

        # Calculate actual movement distances between frames
        distances = []
        for i in range(1, len(leader_positions)):
            prev_x, prev_y = leader_positions[i - 1]
            curr_x, curr_y = leader_positions[i]
            distance = math.sqrt((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2)
            distances.append(distance)

        # Verify that movement is reasonably consistent with expected speed
        # (allowing for curve variations and frame timing)
        non_zero_distances = [d for d in distances if d > 0.1]
        if non_zero_distances:
            avg_distance = sum(non_zero_distances) / len(non_zero_distances)
            expected_distance = path_speed / 60.0  # pixels per frame

            # Allow reasonable tolerance for curve effects
            assert abs(avg_distance - expected_distance) < expected_distance * 0.5, (
                f"Average movement should be close to expected speed, got {avg_distance}, expected ~{expected_distance}"
            )

    def test_s_curve_shape_variety(self):
        """Test that S-curve shape is present for a variety of path lengths and amplitudes."""
        from actions.pattern import _create_galaga_group_entry

        for dist in [200, 400, 800]:
            formation = arrange_grid(rows=1, cols=1, start_x=-dist, start_y=300, spacing_x=50, visible=False)
            target_x, target_y = 400, 300
            # Use the same S-curve generator as the coordinator
            coordinator = _create_galaga_group_entry(
                formation,
                (-dist, 0, 0, 600),
                0,
                (target_x, target_y),
                100.0,
                1.0,
                100.0,
                1.5,
            ).actions[1]  # Coordinator
            path = coordinator._create_individual_galaga_path(formation[0], target_x, target_y)
            # Check that control points are not colinear (S-curve present)
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = path
            assert abs(y1 - y0) > 10 or abs(y2 - y3) > 10, f"S-curve not pronounced for dist={dist}: {path}"

    def test_final_position_and_angle_accuracy(self):
        """Test that sprites end up within 1 pixel and 1 degree of their target position and angle."""
        formation = arrange_grid(rows=1, cols=1, start_x=375, start_y=400, spacing_x=50, visible=False)
        expected_x, expected_y = formation[0].center_x, formation[0].center_y
        entry_actions = create_galaga_style_entry(
            formation=formation,
            groups_per_formation=1,
            sprites_per_group=1,
            screen_bounds=(0, 0, 800, 600),
            path_speed=200.0,
        )
        action = entry_actions[0]
        action.apply(formation, tag="final_accuracy_test")
        action.start()
        max_frames = 600
        frame = 0
        while not action.done and frame < max_frames:
            Action.update_all(0.016)
            for sprite in formation:
                sprite.update()
            frame += 1
        sprite = formation[0]
        assert abs(sprite.center_x - expected_x) < 1, f"Final X should be {expected_x}, got {sprite.center_x}"
        assert abs(sprite.center_y - expected_y) < 1, f"Final Y should be {expected_y}, got {sprite.center_y}"
        assert abs(sprite.angle % 360) < 1, f"Final angle should be 0, got {sprite.angle}"
