"""Debug script to test wrapping behavior."""

import arcade
from actions import Action, ease, infinite, move_until
from arcade import easing

# Create window and sprite
window = arcade.Window(1280, 720, "Wrap Test", visible=False)
missile = arcade.SpriteCircle(8, arcade.color.RED)
missile.position = (250, 100)

print(f"Missile dimensions: {missile.width}x{missile.height}")
print(f"Initial position: {missile.position}")
print(f"Initial edges: left={missile.left}, right={missile.right}")

# Create movement with wrap
bounds = (0, 0, 1280, 720)
print(f"\nBounds: {bounds}")


def on_boundary_hit(sprite, axis, side):
    print(f"Boundary hit! axis={axis}, side={side}, position={sprite.position}")
    if side == "right":
        sprite.trail_points = []


continuous_flight = move_until(
    missile,
    velocity=(5, 0),
    condition=infinite,
    bounds=bounds,
    boundary_behavior="wrap",
    on_boundary_enter=on_boundary_hit,
)

# Wrap with ease
ease(missile, continuous_flight, duration=2.0, ease_function=easing.linear)

print(f"\nAfter setup:")
print(f"  Position: {missile.position}")
print(f"  Velocity: ({missile.change_x}, {missile.change_y})")

# Simulate frames
for frame in range(300):
    Action.update_all(1 / 60)
    missile.update()

    if frame % 50 == 0:
        print(f"\nFrame {frame}:")
        print(f"  Position: {missile.position}")
        print(f"  Edges: left={missile.left}, right={missile.right}")
        print(f"  Velocity: ({missile.change_x}, {missile.change_y})")

    # Stop if missile gets stuck
    if frame > 150 and missile.center_x > 1270:
        print(f"\n*** STUCK AT RIGHT EDGE ***")
        print(f"  Position: {missile.position}")
        print(f"  Edges: left={missile.left}, right={missile.right}")
        print(f"  Velocity: ({missile.change_x}, {missile.change_y})")
        break

window.close()
