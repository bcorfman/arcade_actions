"""Test CallbackUntil with every_frames ticker"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

import arcade
from actions import CallbackUntil, infinite
from actions.frame_timing import every_frames
from actions import Action

call_count = 0


def test_callback():
    global call_count
    call_count += 1
    print(f"Callback called! Count: {call_count}")


# Create ticker that calls callback every 10 frames
ticker = every_frames(10, test_callback)

# Create CallbackUntil that calls ticker every frame
sprite = arcade.SpriteSolidColor(10, 10)
action = CallbackUntil(callback=ticker, condition=infinite)
action.apply(sprite, tag="test")

print("Updating 30 frames (should fire 3 times: at 0, 10, 20)...")
for i in range(30):
    Action.update_all(1 / 60)

print(f"\nTotal callback calls: {call_count} (expected: 3)")
