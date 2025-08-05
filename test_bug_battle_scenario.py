#!/usr/bin/env python3
"""
Test the exact scenario from bug_battle.py to see collision behavior.
"""

import random
import sys

sys.path.append(".")

import arcade

from actions import Action, arrange_grid, create_formation_entry_from_sprites

# Match bug_battle.py constants
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 1280
ENEMY_SCALE = 0.5
ENEMY_WIDTH = 128 * ENEMY_SCALE
ENEMY_HEIGHT = 128 * ENEMY_SCALE


def test_bug_battle_formation_entry():
    """Test the exact formation entry scenario from bug_battle.py."""
    print("Testing bug_battle.py formation entry scenario...")

    # Recreate the exact enemy setup from bug_battle.py
    enemy_list = [
        ":resources:/images/enemies/bee.png",
        ":resources:/images/enemies/fishPink.png",
        ":resources:/images/enemies/fly.png",
        ":resources:/images/enemies/saw.png",
        ":resources:/images/enemies/slimeBlock.png",
        ":resources:/images/enemies/fishGreen.png",
    ]

    X_OFFSET = 120
    COLS = 4
    NUM_SPRITES = COLS - 1
    NUM_SPACES = NUM_SPRITES - 1

    # Create the target formation sprites (these define the final positions)
    target_sprites = [arcade.Sprite(random.choice(enemy_list), scale=0.5) for i in range(16)]
    enemy_formation = arrange_grid(
        sprites=target_sprites,
        rows=4,
        cols=4,
        start_x=X_OFFSET,
        start_y=WINDOW_HEIGHT - 400,
        spacing_x=(WINDOW_WIDTH - X_OFFSET * 2 - ENEMY_WIDTH * NUM_SPRITES) / NUM_SPACES,
        spacing_y=ENEMY_HEIGHT * 1.5,
        visible=False,  # Target formation is invisible, only used for positioning
    )

    print(f"Created {len(enemy_formation)} target formation sprites")
    print(f"Formation bounds: x={X_OFFSET} to {WINDOW_WIDTH - X_OFFSET}, y={WINDOW_HEIGHT - 400}")

    # Create the entry pattern with EXACT bug_battle.py parameters
    entry_actions = create_formation_entry_from_sprites(
        enemy_formation,
        speed=1.0,
        stagger_delay=5,
        window_bounds=(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
    )

    print(f"Created {len(entry_actions)} entry actions")

    # Apply actions and create sprite list exactly like bug_battle.py
    enemy_list_sprites = arcade.SpriteList()
    for sprite, action in entry_actions:
        action.apply(sprite, tag="enemy_formation_entry")
        enemy_list_sprites.append(sprite)

    print(f"Added {len(enemy_list_sprites)} sprites to enemy list")
    print("Starting collision monitoring...")

    # Monitor for collisions during the entire formation entry
    collision_log = []
    frame_count = 0
    max_frames = 1800  # 30 seconds at 60 FPS (longer than bug_battle needs)

    sprites_at_target = set()

    while frame_count < max_frames:
        # Update all actions (same as bug_battle.py)
        Action.update_all(1 / 60)

        # Update sprite list (same as bug_battle.py)
        enemy_list_sprites.update()

        # Check for collisions between all sprites
        collisions_this_frame = []
        visible_sprites_list = arcade.SpriteList()
        for s in enemy_list_sprites:
            if s.visible:
                visible_sprites_list.append(s)

        for i, sprite1 in enumerate(visible_sprites_list):
            # Check if this sprite collides with any other visible sprites
            colliding_sprites = arcade.check_for_collision_with_list(sprite1, visible_sprites_list)
            # Remove self from collision list
            colliding_sprites = [s for s in colliding_sprites if s != sprite1]

            if colliding_sprites:
                for sprite2 in colliding_sprites:
                    # Avoid duplicate collision reports
                    sprite1_idx = enemy_list_sprites.index(sprite1)
                    sprite2_idx = enemy_list_sprites.index(sprite2)
                    if sprite1_idx < sprite2_idx:
                        collision_info = {
                            "frame": frame_count,
                            "time": frame_count / 60.0,
                            "sprite1_idx": sprite1_idx,
                            "sprite2_idx": sprite2_idx,
                            "sprite1_pos": (sprite1.center_x, sprite1.center_y),
                            "sprite2_pos": (sprite2.center_x, sprite2.center_y),
                            "distance": (
                                (sprite1.center_x - sprite2.center_x) ** 2 + (sprite1.center_y - sprite2.center_y) ** 2
                            )
                            ** 0.5,
                            "sprite1_size": (sprite1.width, sprite1.height),
                            "sprite2_size": (sprite2.width, sprite2.height),
                        }
                        collisions_this_frame.append(collision_info)

        if collisions_this_frame:
            collision_log.extend(collisions_this_frame)
            print(f"Frame {frame_count} ({frame_count / 60:.1f}s): {len(collisions_this_frame)} collisions!")
            for collision in collisions_this_frame:
                print(
                    f"  Sprites {collision['sprite1_idx']} & {collision['sprite2_idx']}: "
                    f"dist={collision['distance']:.1f}, "
                    f"pos1=({collision['sprite1_pos'][0]:.0f},{collision['sprite1_pos'][1]:.0f}), "
                    f"pos2=({collision['sprite2_pos'][0]:.0f},{collision['sprite2_pos'][1]:.0f})"
                )

        # Track sprites that have reached their targets
        new_arrivals = 0
        for sprite in visible_sprites_list:
            sprite_idx = enemy_list_sprites.index(sprite)
            if sprite_idx not in sprites_at_target:
                # Check if sprite is near its target position
                target_sprite = enemy_formation[sprite_idx]
                distance_to_target = (
                    (sprite.center_x - target_sprite.center_x) ** 2 + (sprite.center_y - target_sprite.center_y) ** 2
                ) ** 0.5
                if distance_to_target < 5.0:  # Close enough to target
                    sprites_at_target.add(sprite_idx)
                    new_arrivals += 1

        if new_arrivals > 0:
            print(
                f"Frame {frame_count}: {new_arrivals} sprites reached targets. "
                f"Total at target: {len(sprites_at_target)}/{len(enemy_formation)}"
            )

        frame_count += 1

        # Stop when all sprites have reached their targets
        if len(sprites_at_target) >= len(enemy_formation):
            print(f"All sprites reached targets at frame {frame_count} ({frame_count / 60:.1f}s)")
            break

    # Report results
    print("\n=== BUG BATTLE COLLISION SUMMARY ===")
    print(f"Total simulation time: {frame_count / 60:.1f} seconds")
    print(f"Total collisions detected: {len(collision_log)}")
    print(f"Sprites that reached targets: {len(sprites_at_target)}/{len(enemy_formation)}")

    if collision_log:
        print("\n❌ COLLISIONS DETECTED!")
        print(f"First collision at {collision_log[0]['time']:.1f}s")
        print(f"Last collision at {collision_log[-1]['time']:.1f}s")

        # Analyze collision patterns
        collision_times = [c["time"] for c in collision_log]
        sprite_pairs = {}
        for collision in collision_log:
            pair = tuple(sorted([collision["sprite1_idx"], collision["sprite2_idx"]]))
            if pair not in sprite_pairs:
                sprite_pairs[pair] = []
            sprite_pairs[pair].append(collision)

        print("\nCollision timeline:")
        for i, collision in enumerate(collision_log[:10]):  # Show first 10
            print(
                f"  {collision['time']:.1f}s: Sprites {collision['sprite1_idx']} & {collision['sprite2_idx']} "
                f"(distance: {collision['distance']:.1f})"
            )
        if len(collision_log) > 10:
            print(f"  ... and {len(collision_log) - 10} more collisions")

        print("\nMost problematic sprite pairs:")
        sorted_pairs = sorted(sprite_pairs.items(), key=lambda x: len(x[1]), reverse=True)
        for pair, collisions in sorted_pairs[:5]:
            print(f"  Sprites {pair[0]} & {pair[1]}: {len(collisions)} collision frames")

        return False
    else:
        print("✅ No collisions detected in bug_battle scenario!")
        return True


if __name__ == "__main__":
    print("Testing exact bug_battle.py formation entry scenario...\n")
    success = test_bug_battle_formation_entry()

    if not success:
        print("\n❌ Collision avoidance system needs improvement for bug_battle scenario!")
    else:
        print("\n✅ Bug battle formation entry collision avoidance working correctly!")
