#!/usr/bin/env python3
"""
Real collision detection test using arcade.check_for_collision_with_list
to see what's actually happening during wave formation entry.
"""

import sys

sys.path.append(".")

import arcade

from actions import Action, arrange_grid, create_formation_entry_from_sprites


def test_real_collisions_during_formation_entry():
    """Test actual sprite collisions during formation entry using arcade collision detection."""
    print("Testing real collision detection during formation entry...")

    # Create a test formation
    target_formation = arrange_grid(
        sprites=[arcade.Sprite(":resources:images/items/star.png", scale=0.5) for _ in range(9)],
        rows=3,
        cols=3,
        start_x=300,
        start_y=200,
        spacing_x=80,
        spacing_y=80,
        visible=False,
    )

    window_bounds = (0, 0, 800, 600)

    # Create formation entry actions
    entry_actions = create_formation_entry_from_sprites(
        target_formation,
        window_bounds=window_bounds,
        speed=3.0,
        stagger_delay=1.0,
    )

    print(f"Created {len(entry_actions)} sprite entry actions")

    # Apply all actions
    all_sprites = arcade.SpriteList()
    for sprite, action in entry_actions:
        action.apply(sprite, tag="formation_entry")
        all_sprites.append(sprite)

    print("All sprites added to list. Starting collision monitoring...")

    # Monitor collisions during movement
    collision_log = []
    frame_count = 0
    max_frames = 600  # 10 seconds at 60 FPS

    while frame_count < max_frames:
        # Update all actions
        Action.update_all(1 / 60)  # 60 FPS simulation

        # Check for collisions between all sprites
        collisions_this_frame = []
        for i, sprite1 in enumerate(all_sprites):
            if sprite1.visible:
                # Check if this sprite collides with any other visible sprites
                colliding_sprites = arcade.check_for_collision_with_list(sprite1, all_sprites)
                # Remove self from collision list
                colliding_sprites = [s for s in colliding_sprites if s != sprite1 and s.visible]

                if colliding_sprites:
                    for sprite2 in colliding_sprites:
                        j = all_sprites.index(sprite2)
                        if i < j:  # Avoid duplicate collision reports
                            collision_info = {
                                "frame": frame_count,
                                "time": frame_count / 60.0,
                                "sprite1_idx": i,
                                "sprite2_idx": j,
                                "sprite1_pos": (sprite1.center_x, sprite1.center_y),
                                "sprite2_pos": (sprite2.center_x, sprite2.center_y),
                                "distance": (
                                    (sprite1.center_x - sprite2.center_x) ** 2
                                    + (sprite1.center_y - sprite2.center_y) ** 2
                                )
                                ** 0.5,
                            }
                            collisions_this_frame.append(collision_info)

        if collisions_this_frame:
            collision_log.extend(collisions_this_frame)
            print(f"Frame {frame_count}: {len(collisions_this_frame)} collisions detected!")
            for collision in collisions_this_frame:
                print(
                    f"  Sprites {collision['sprite1_idx']} and {collision['sprite2_idx']} colliding at distance {collision['distance']:.1f}"
                )

        frame_count += 1

        # Check if all sprites have reached their targets (no more actions running)
        active_actions = len([action for action in Action._active_actions if not getattr(action, "_completed", False)])
        if active_actions == 0:
            print(f"All sprites reached targets at frame {frame_count}")
            break

    # Report collision summary
    print("\n=== COLLISION SUMMARY ===")
    print(f"Total simulation frames: {frame_count}")
    print(f"Total collisions detected: {len(collision_log)}")

    if collision_log:
        print(f"\nFirst collision at frame {collision_log[0]['frame']} ({collision_log[0]['time']:.1f}s)")
        print(f"Last collision at frame {collision_log[-1]['frame']} ({collision_log[-1]['time']:.1f}s)")

        # Group by sprite pairs
        sprite_pairs = {}
        for collision in collision_log:
            pair = tuple(sorted([collision["sprite1_idx"], collision["sprite2_idx"]]))
            if pair not in sprite_pairs:
                sprite_pairs[pair] = []
            sprite_pairs[pair].append(collision)

        print("\nColliding sprite pairs:")
        for pair, collisions in sprite_pairs.items():
            print(f"  Sprites {pair[0]} and {pair[1]}: {len(collisions)} collision frames")

        return False  # Collisions detected
    else:
        print("✅ No collisions detected during formation entry!")
        return True  # No collisions


def test_wave_timing_analysis():
    """Analyze wave timing to understand collision patterns."""
    print("\n=== WAVE TIMING ANALYSIS ===")

    target_formation = arrange_grid(
        sprites=[arcade.Sprite(":resources:images/items/star.png", scale=0.5) for _ in range(6)],
        rows=2,
        cols=3,
        start_x=300,
        start_y=200,
        spacing_x=80,
        spacing_y=80,
        visible=False,
    )

    window_bounds = (0, 0, 800, 600)

    # Test different stagger delays
    for stagger_delay in [0.5, 1.0, 2.0]:
        print(f"\nTesting stagger delay: {stagger_delay}s")

        entry_actions = create_formation_entry_from_sprites(
            target_formation,
            window_bounds=window_bounds,
            speed=2.0,
            stagger_delay=stagger_delay,
        )

        # Apply actions and record start times
        all_sprites = arcade.SpriteList()
        start_times = {}

        for i, (sprite, action) in enumerate(entry_actions):
            # Try to determine wave delay by inspecting action structure
            # This is a bit hacky but helps understand timing
            action.apply(sprite, tag=f"test_timing_{i}")
            all_sprites.append(sprite)
            start_times[i] = 0  # Default immediate start

        # Quick collision test
        collision_detected = False
        for frame in range(300):  # 5 seconds
            Action.update_all(1 / 60)

            # Quick collision check
            for sprite in all_sprites:
                if sprite.visible:
                    collisions = arcade.check_for_collision_with_list(sprite, all_sprites)
                    if len(collisions) > 1:  # More than just self
                        collision_detected = True
                        break

            if collision_detected:
                print(f"  Collision detected at frame {frame} ({frame / 60.0:.1f}s)")
                break

        if not collision_detected:
            print(f"  ✅ No collisions with {stagger_delay}s delay")

        # Clean up actions (Action doesn't have stop_all_actions, use stop_actions_for_target)
        for sprite in all_sprites:
            Action.stop_actions_for_target(sprite)


if __name__ == "__main__":
    print("Starting real collision detection tests...\n")

    # Test 1: Real collision detection
    no_collisions = test_real_collisions_during_formation_entry()

    # Test 2: Wave timing analysis
    test_wave_timing_analysis()

    print("\n=== FINAL RESULT ===")
    if no_collisions:
        print("✅ Formation entry collision avoidance is working correctly!")
    else:
        print("❌ Collisions detected - collision avoidance needs improvement!")
