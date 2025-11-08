"""Debug script to test patrol pattern behavior."""

import arcade
from actions import Action, create_patrol_pattern

# Create window and sprite
window = arcade.Window(800, 600, "Patrol Test", visible=False)
sprite = arcade.Sprite(":resources:images/space_shooter/playerShip1_orange.png", scale=0.5)
sprite.center_x = 400
sprite.center_y = 200

print(f"Sprite dimensions: {sprite.width}x{sprite.height}")
print(f"Half-width: {sprite.width / 2}, Half-height: {sprite.height / 2}")
print(f"Initial position: center=({sprite.center_x}, {sprite.center_y})")
print(f"Initial edges: left={sprite.left}, right={sprite.right}")

# Edge-based coordinates (matching pattern_demo.py)
left_edge = sprite.center_x - 64.75
right_edge = sprite.center_x + 64.75
bottom_edge = sprite.center_y - sprite.height / 2
top_edge = sprite.center_y + sprite.height / 2
bounds = (left_edge, bottom_edge, right_edge, top_edge)

print(f"\nPatrol bounds:")
print(f"  Left edge: {left_edge}")
print(f"  Right edge: {right_edge}")
print(f"  Bottom edge: {bottom_edge}")
print(f"  Top edge: {top_edge}")
print(f"  Horizontal span: {right_edge - left_edge}px")

patrol = create_patrol_pattern(
    velocity=(2, 0),  # 2 pixels per frame horizontally
    bounds=bounds,
    axis="x",
)
patrol.apply(sprite)

print(f"\nAfter setup:")
print(f"  Position: center=({sprite.center_x}, {sprite.center_y})")
print(f"  Edges: left={sprite.left}, right={sprite.right}")
print(f"  Velocity: ({sprite.change_x}, {sprite.change_y})")

# Track boundary hits
boundary_hits = []
last_direction = None

# Simulate frames
for frame in range(600):
    old_x = sprite.center_x
    old_left = sprite.left
    old_right = sprite.right

    Action.update_all(1 / 60)
    sprite.update()

    # Detect direction changes
    if sprite.change_x != 0:
        current_direction = "right" if sprite.change_x > 0 else "left"
        if last_direction and current_direction != last_direction:
            boundary_hits.append(
                {
                    "frame": frame,
                    "direction_change": f"{last_direction} -> {current_direction}",
                    "center": sprite.center_x,
                    "left": sprite.left,
                    "right": sprite.right,
                    "old_center": old_x,
                    "old_left": old_left,
                    "old_right": old_right,
                }
            )
        last_direction = current_direction

    # Print every 100 frames
    if frame % 100 == 0:
        print(f"\nFrame {frame}:")
        print(f"  Center: {sprite.center_x:.2f}, Left: {sprite.left:.2f}, Right: {sprite.right:.2f}")
        print(f"  Velocity: {sprite.change_x:.2f}")

print(f"\n=== Boundary Hits (Direction Changes) ===")
print(f"Total hits: {len(boundary_hits)}")
for i, hit in enumerate(boundary_hits[:20]):  # Show first 20
    print(f"\n{i + 1}. Frame {hit['frame']}: {hit['direction_change']}")
    print(f"   Before: center={hit['old_center']:.2f}, left={hit['old_left']:.2f}, right={hit['old_right']:.2f}")
    print(f"   After:  center={hit['center']:.2f}, left={hit['left']:.2f}, right={hit['right']:.2f}")
    print(f"   Expected bounds: left={bounds[0]:.2f}, right={bounds[2]:.2f}")

# Check for stutters (quick direction reversals)
print(f"\n=== Checking for Stutters ===")
for i in range(len(boundary_hits) - 1):
    frame_gap = boundary_hits[i + 1]["frame"] - boundary_hits[i]["frame"]
    if frame_gap < 10:  # Less than 10 frames between direction changes
        print(f"STUTTER DETECTED!")
        print(f"  Frames {boundary_hits[i]['frame']} to {boundary_hits[i + 1]['frame']} (gap: {frame_gap})")
        print(f"  {boundary_hits[i]['direction_change']} then {boundary_hits[i + 1]['direction_change']}")

window.close()
