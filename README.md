# ArcadeActions extension library for Arcade 3.x

## 🚀 Quick Appeal

So much of building an arcade game is a cluttered way of saying "animate this sprite until something happens", like colliding with another sprite, reaching a boundary, or an event response. Most of us manage this complexity in the game loop, using low-level movement of game objects and complex chains of `if`-statements. But what if you could write a command like "keep moving this sprite, wrap it the other side of the window if it hits a boundary, and raise an event when it collides with another sprite" ... and have it be clear and concise? 

```python 
import arcade
from actions import infinite, move_until, parallel

# assume player and asteroid are arcade.Sprites, and other_asteroids is a arcade.SpriteList
move_until(asteroid, velocity=(5, 4), condition=infinite, bounds=(-64, -64, 864, 664), boundary_behavior="wrap")

def asteroid_collision_check():
    player_hit = arcade.check_for_collision(player, asteroid)
    asteroid_hits = arcade.check_for_collision_with_list(asteroid, other_asteroids)

    if player_hit or asteroid_hits:
        return {
            "player_hit": player_hit,
            "asteroid_hits": asteroid_hits,
        }
    return None  # Continue moving

# The callback receives the collision data from the condition function
def handle_asteroid_collision(collision_data):
    if collision_data["player_hit"]:
        print("Player destroyed!")
    for asteroid in collision_data["asteroid_hits"]:
        print("Asteroid collisions!")
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
2. **Study the Slime Invaders example** [(remade for ArcadeActions)](examples/invaders.py) or the [Stars example](examples/stars.py) to understand the power of Actions
3. **Start with simple conditional actions** and build up to complex compositions
4. **Use formation functions** for organizing sprite positions and layouts

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


## 🎮 Example: Space Invaders Pattern

```python
import arcade
from actions import Action, arrange_grid, duration, move_until, infinite


class SpaceInvadersGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Space Invaders")

        # Create 5×10 grid of enemies with a single call
        enemies = arrange_grid(
            rows=5,
            cols=10,
            start_x=100,
            start_y=500,
            spacing_x=60,
            spacing_y=40,
            sprite_factory=lambda: arcade.Sprite(":resources:images/enemy.png"),
        )

        # Store enemies for movement management
        self.enemies = enemies
        self._setup_movement_pattern()

    def _setup_movement_pattern(self):
        # Create formation movement with boundary bouncing
        def on_boundary_hit(sprite, axis):
            if axis == "x":
                # Move entire formation down and change direction
                move_until(self.enemies, velocity=(0, -30), condition=duration(0.3))

        # Create continuous horizontal movement with boundary detection
        bounds = (50, 0, 750, 600)  # left, bottom, right, top
        move_until(
            self.enemies,
            velocity=(50, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary=on_boundary_hit
        )

    def on_update(self, delta_time):
        # Single line handles all action updates
        Action.update_all(delta_time)
```
