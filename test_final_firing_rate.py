"""Final test of firing rate"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

import random
import arcade
from examples.invaders import GameView, WINDOW_WIDTH, WINDOW_HEIGHT

# Test with multiple seeds to get average
print("Testing firing rate over 10 seconds (600 frames) with different seeds:\n")

for seed in [42, 123, 456, 789, 999]:
    random.seed(seed)
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Test", visible=False)
    game = GameView()
    game.reset()

    initial_bullets = len(game.enemy_bullet_list)

    # Run for 10 seconds (600 frames)
    for i in range(600):
        game.on_update(1 / 60)

    bullets_fired = len(game.enemy_bullet_list) - initial_bullets
    calls_expected = 600 // 30  # Every 30 frames
    bullets_per_second = bullets_fired / 10

    print(f"Seed {seed:3d}: {bullets_fired:2d} bullets in 10s = {bullets_per_second:.2f} bullets/sec")

    window.close()

print("\nWith 35 enemies, expected ~0.24 bullets per call")
print("With 30-frame interval (2 calls/sec), expected ~0.48 bullets/sec")
print("As enemies are destroyed, firing rate increases!")
