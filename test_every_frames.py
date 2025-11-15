"""Test every_frames helper"""

import sys

sys.path.insert(0, "/home/bcorfman/dev/arcade_actions")

from actions.frame_timing import every_frames

call_count = 0


def test_callback():
    global call_count
    call_count += 1
    print(f"Callback called! Count: {call_count}")


# Create ticker that calls callback every 10 frames
ticker = every_frames(10, test_callback)

# Call ticker 30 times (should fire 3 times: at 0, 10, 20)
print("Calling ticker 30 times (should fire 3 times)...")
for i in range(30):
    ticker()

print(f"\nTotal callback calls: {call_count} (expected: 3)")
