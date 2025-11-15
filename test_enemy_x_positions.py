"""Check enemy X positions"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

import random
import arcade
from examples.invaders import GameView, WINDOW_WIDTH, WINDOW_HEIGHT

random.seed(42)
window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Test", visible=False)
game = GameView()
game.reset()

print(f"Enemy count: {len(game.enemy_list)}")
print("\nEnemy X positions:")
x_positions = [enemy.center_x for enemy in game.enemy_list]
unique_x = sorted(set(x_positions))
print(f"Unique X positions: {unique_x}")
print(f"Number of unique X positions: {len(unique_x)}")
print(f"Enemies per column: {len(x_positions) / len(unique_x):.1f}")

# Now simulate firing with actual positions
print("\nSimulating firing with actual positions:")
random.seed(42)
x_spawn = []
bullets = 0
for enemy in game.enemy_list:
    chance = 4 + len(game.enemy_list) * 4
    roll = random.randrange(chance)
    if roll == 0:
        if enemy.center_x not in x_spawn:
            bullets += 1
            x_spawn.append(enemy.center_x)
            print(f"Enemy at x={enemy.center_x:.1f} fired! (roll={roll})")
        else:
            print(f"Enemy at x={enemy.center_x:.1f} blocked (x already used)")

print(f"\nTotal bullets fired: {bullets}")

window.close()
