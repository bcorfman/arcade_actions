# ArcadeActions extension library for Arcade 3.x

## 🚀 Quick Appeal

So much of building an arcade game is a cluttered way of saying "animate this sprite until something happens", like colliding with another sprite, reaching a boundary, or an event response. Most of us manage this complexity in the game loop, using low-level movement of game objects and complex chains of `if`-statements. But what if you could write a concise command like "keep moving this sprite, wrap it the other side of the window if it hits a boundary, and raise an event when it collides with another sprite"? 

```python 
import arcade
from actions import move_until

# Overview: This example shows how to set up an asteroid that moves continuously,
# wraps around screen boundaries, and stops when it collides with the player or other asteroids.
# The collision data is passed from the condition function to the callback function.

# assume player and asteroid are arcade.Sprites, and other_asteroids is a arcade.SpriteList

def asteroid_collision_check():
    player_hit = arcade.check_for_collision(player, asteroid)
    asteroid_hits = arcade.check_for_collision_with_list(asteroid, other_asteroids)

    if player_hit or asteroid_hits:
        return {
            "player_hit": player_hit,
            "asteroid_hits": asteroid_hits,
        }
    return None  # Continue moving

def handle_asteroid_collision(collision_data):
    if collision_data["player_hit"]:
        print("Player destroyed!")
    for asteroid in collision_data["asteroid_hits"]:
        print("Asteroid collisions!")

# Start the asteroid moving with collision detection
# bounds are slightly outside the viewing area, so asteroids go offscreen before wrapping
move_until(
    asteroid, 
    velocity=(5, 4), 
    condition=asteroid_collision_check, 
    on_stop=handle_asteroid_collision,
    bounds=(-64, -64, 864, 664), 
    boundary_behavior="wrap"
)
```
This example shows how animation actions can be logically separated from collision responses, making your code simple and appealing. 
If writing high-level game code appeals to you ... it's why you chose Python in the first place ... read on!

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](docs/api_usage_guide.md)** - **START HERE** - Complete guide to using the framework
2. **[Testing Guide](docs/testing_guide.md)** - **Testing patterns and best practices**
3. **[PRD](docs/prd.md)** - Project requirements and architecture decisions


## 🚀 Getting Started

1. **Read the [API Usage Guide](api_usage_guide.md)** to understand the framework
2. **Study the demos in the examples directory** to understand the power of Actions
3. **Start with simple conditional actions** and build up to complex compositions
4. **Use formation and pattern functions** for organizing sprite positions and layouts

## 📖 Documentation Structure

```
docs/
├── README.md                # This file - overview and quick start
├── api_usage_guide.md       # Complete API usage patterns (START HERE)
├── testing_guide.md         # Testing patterns and fixtures
└── prd.md                   # Requirements and architecture
```

## 🔧 Core Components

### ✅ Implementation

#### Base Action System (actions/base.py)
- **Action** - Core action class with global management
- **CompositeAction** - Base for sequential and parallel actions
- **Global management** - Automatic action tracking and updates
- **Composition helpers** - `sequence()` and `parallel()` functions

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement until condition met
- **FollowPathUntil** - Follow Bezier curve paths with optional automatic sprite rotation
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes  
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition to be met
- **TweenUntil** - Direct property animation from start to end value

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Formation Management (actions/formation.py)
- **Formation functions** - Grid, line, circle, diamond, V-formation, triangle, hexagonal grid, arc, concentric rings, cross, and arrow positioning

#### Movement Patterns (actions/pattern.py)
- **Movement pattern functions** - Zigzag, wave, spiral, figure-8, orbit, bounce, and patrol patterns
- **Condition helpers** - Time-based and sprite count conditions for conditional actions

#### Easing Effects (actions/easing.py)
- **Ease wrapper** - Apply smooth acceleration/deceleration curves to any conditional action
- **Multiple easing functions** - Built-in ease_in, ease_out, ease_in_out support
- **Custom easing** - Create specialized easing curves and nested easing effects

## 📋 Decision Matrix

| Scenario | Use | Example |
|----------|-----|---------|
| Simple sprite actions | Helper functions | `move_until(sprite, ..., tag="move")` |
| Sprite group actions | Helper functions on SpriteList | `move_until(enemies, ..., tag="formation")` |
| Complex sequences | Direct classes + `sequence()` | `sequence(DelayUntil(...), MoveUntil(...))` |
| Parallel behaviors | Direct classes + `parallel()` | `parallel(MoveUntil(...), RotateUntil(...))` |
| Formation positioning | Formation functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Triangle formations | `arrange_triangle` | `arrange_triangle(count=10, apex_x=400, apex_y=500)` |
| Hexagonal grids | `arrange_hexagonal_grid` | `arrange_hexagonal_grid(rows=4, cols=6)` |
| Arc formations | `arrange_arc` | `arrange_arc(count=8, radius=120, start_angle=0, end_angle=180)` |
| Concentric patterns | `arrange_concentric_rings` | `arrange_concentric_rings(radii=[50, 100])` |
| Cross patterns | `arrange_cross` | `arrange_cross(count=9, arm_length=100)` |
| Arrow formations | `arrange_arrow` | `arrange_arrow(count=7, rows=3)` |
| Curved path movement | `follow_path_until` helper | `follow_path_until(sprite, points, ...)` |
| Boundary detection | `move_until` with bounds | `move_until(sprite, ..., bounds=bounds, boundary_behavior="bounce")` |
| Smooth acceleration | `ease()` helper | `ease(sprite, action, ...)` |
| Complex curved movement | `ease()` + `follow_path_until` | `ease(sprite, follow_path_until(...), ...)` |
| Property animation | `tween_until` helper | `tween_until(sprite, 0, 100, "center_x", ...)` |
| Standard sprites (no actions) | arcade.Sprite + arcade.SpriteList | Regular Arcade usage |
