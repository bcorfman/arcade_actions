"""Test the corrected firing rate"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

import random
import arcade
from examples.invaders import GameView, WINDOW_WIDTH, WINDOW_HEIGHT

random.seed(42)
window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Test", visible=False)
game = GameView()
game.reset()

print(f"Initial enemy count: {len(game.enemy_list)}")
print(f"Expected firing rate: ~{35 / (4 + 35 * 4):.3f} bullets per call")
print(f"With 60-frame interval: ~{35 / (4 + 35 * 4):.3f} bullets per second\n")

# Run for 60 frames (1 second)
initial_bullets = len(game.enemy_bullet_list)
for i in range(60):
    game.on_update(1 / 60)

bullets_after_1_second = len(game.enemy_bullet_list) - initial_bullets
print(f"Bullets fired in 1 second: {bullets_after_1_second}")

# Run for another 60 frames
for i in range(60):
    game.on_update(1 / 60)

bullets_after_2_seconds = len(game.enemy_bullet_list) - initial_bullets
print(f"Bullets fired in 2 seconds: {bullets_after_2_seconds}")

# Now simulate destroying some enemies
print(f"\nDestroying 20 enemies...")
for i in range(20):
    if len(game.enemy_list) > 0:
        game.enemy_list[0].remove_from_sprite_lists()

print(f"Remaining enemies: {len(game.enemy_list)}")
print(f"Expected firing rate now: ~{len(game.enemy_list) / (4 + len(game.enemy_list) * 4):.3f} bullets per call")

# Run for another 60 frames
bullets_before = len(game.enemy_bullet_list)
for i in range(60):
    game.on_update(1 / 60)

bullets_after_destroyed = len(game.enemy_bullet_list) - bullets_before
print(f"Bullets fired after destroying enemies: {bullets_after_destroyed}")

window.close()
