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
# Edge-based bounds: add half-width to allow center to reach full window
bounds = (-8, -8, 1280 + 8, 720 + 8)
print(f"\nBounds: {bounds}")


def on_boundary_hit(sprite, axis, side):
    print(f"Boundary hit! axis={axis}, side={side}, position={sprite.position}")
    if side == "right":
        sprite.trail_points = []


# Create the action but don't apply it yet (Ease will apply it)
from actions.conditional import MoveUntil

continuous_flight = MoveUntil(
    velocity=(5, 0),
    condition=infinite,
    bounds=bounds,
    boundary_behavior="wrap",
    on_boundary_enter=on_boundary_hit,
)

# Wrap with ease (this will apply the action)
ease(missile, continuous_flight, duration=2.0, ease_function=easing.linear)

print(f"\nAfter setup:")
print(f"  Position: {missile.position}")
print(f"  Velocity: ({missile.change_x}, {missile.change_y})")

# Simulate frames
for frame in range(300):
    old_x = missile.center_x
    Action.update_all(1 / 60)
    missile.update()
    new_x = missile.center_x

    if frame % 50 == 0:
        print(f"\nFrame {frame}:")
        print(f"  Position: {missile.position}")
        print(f"  Edges: left={missile.left}, right={missile.right}")
        print(f"  Velocity: ({missile.change_x}, {missile.change_y})")

    # Stop if missile gets stuck or stops moving
    if frame > 150 and missile.center_x > 1270:
        if abs(new_x - old_x) < 0.01:  # Not moving
            print(f"\n*** STOPPED MOVING AT FRAME {frame} ***")
            print(f"  Position: {missile.position}")
            print(f"  Edges: left={missile.left}, right={missile.right}")
            print(f"  Velocity: ({missile.change_x}, {missile.change_y})")
            print(f"  Moved: {new_x - old_x}")
            print(f"  Active actions: {len(Action._active_actions)}")
            for action in Action._active_actions:
                print(f"    - {type(action).__name__}: done={action.done}")
            break

window.close()
