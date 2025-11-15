"""Debug invaders firing"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

import random
import arcade
from examples.invaders import GameView, WINDOW_WIDTH, WINDOW_HEIGHT

# Monkey patch to add debug output
original_allow = GameView.allow_enemies_to_fire

call_count = 0


def debug_allow(self):
    global call_count
    call_count += 1
    print(f"allow_enemies_to_fire called! (call #{call_count})")
    before = len(self.enemy_bullet_list)
    original_allow(self)
    after = len(self.enemy_bullet_list)
    if after > before:
        print(f"  -> Fired {after - before} bullets")


GameView.allow_enemies_to_fire = debug_allow

random.seed(42)
window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Test", visible=False)
game = GameView()
game.reset()

print(f"Initial enemy count: {len(game.enemy_list)}")
print("Running 120 frames (2 seconds)...\n")

for i in range(120):
    game.on_update(1 / 60)

print(f"\nTotal calls to allow_enemies_to_fire: {call_count}")
print(f"Total bullets: {len(game.enemy_bullet_list)}")

window.close()
