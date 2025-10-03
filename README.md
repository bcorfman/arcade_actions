<table style="border: none; border-collapse: collapse;">
<tr>
<td align="center" style="border: none; padding: 10px; vertical-align: bottom;">
<img src="https://github.com/bcorfman/gif_resources/blob/main/space_clutter.gif?raw=true" style="width: 400px"/>
<br/>
<em style="display: block; width: 400px; text-align: center;">Space Clutter! - A game prototype demonstrating grid formations, wave patterns, and MoveUntil actions</em>
</td>
<td align="center" style="border: none; padding: 10px; vertical-align: bottom;">
<img src="https://github.com/bcorfman/gif_resources/blob/main/laser_gates.gif?raw=true" style="width: 400px"/>
<br/>
<em style="display: block; width: 400px; text-align: center;">A <a href="https://github.com/bcorfman/laser_gates">full game</a> under development, using Actions</em>
<br/>
<img src="https://github.com/bcorfman/gif_resources/blob/main/pattern_demo.gif?raw=true" style="width: 400px"/>
<br/>
<em style="display: block; width: 400px; text-align: center;">Pattern Demo - Showcasing various movement patterns and formation arrangements</em>
</td>
</tr>
</table>

---

# ArcadeActions extension library for Arcade 3.x
[![codecov](https://codecov.io/gh/bcorfman/arcade_actions/graph/badge.svg?token=9AIZD1GLND)](https://codecov.io/gh/bcorfman/arcade_actions)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/bcorfman/arcade_actions)

## 🚀 Quick Appeal

So much of building an arcade game is a cluttered way of saying "animate this sprite until something happens", like colliding with another sprite, reaching a boundary, or an event response. Most of us manage this complexity in the game loop, using low-level movement of game objects and complex chains of `if`-statements. But what if you could write a concise command like "keep moving this sprite, wrap it the other side of the window if it hits a boundary, and raise an event when it collides with another sprite"? 

```python 
import arcade
from actions import MoveUntil, Action

class AsteroidDemoView(arcade.View):
    def __init__(self):
        super().__init__()
        # Minimal, explicit setup
        self.player = arcade.Sprite(":resources:/images/space_shooter/playerShip1_green.png")
        self.player.center_x, self.player.center_y = 400, 100

        self.asteroids = arcade.SpriteList()
        # Position asteroids in a simple pattern with different velocities
        positions = [(200, 450), (400, 400), (600, 450)]
        velocities = [(3, -2), (-2, -3), (4, -1)]
        
        for (x, y), (vx, vy) in zip(positions, velocities):
            rock = arcade.Sprite(":resources:/images/space_shooter/meteorGrey_big1.png")
            rock.center_x, rock.center_y = x, y
            self.asteroids.append(rock)
            
            # Each asteroid moves independently with its own velocity
            MoveUntil(
                velocity=(vx, vy),
                condition=self.player_asteroid_collision,
                on_stop=self.on_player_collision,
                bounds=(-64, -64, 864, 664),
                boundary_behavior="wrap",
            ).apply(rock)

    def player_asteroid_collision(self):
        """Return data when player hits any asteroid; None to keep moving."""
        hits = arcade.check_for_collision_with_list(self.player, self.asteroids)
        return {"hits": hits} if hits else None

    def on_player_collision(self, data):
        """React to collision."""
        print(f"Game over! {len(data['hits'])} asteroid(s) hit the player.")
        # ... reset player / end round / etc. ...

    def on_update(self, dt):
        Action.update_all(dt)
        self.player.update()
        self.asteroids.update()

    def on_draw(self):
        self.clear()
        self.player.draw()
        self.asteroids.draw()
```
This example shows how animation actions can be logically separated from collision responses, making your code simple and appealing. 
If writing high-level game code appeals to you ... it's why you chose Python in the first place ... read on!

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](docs/api_usage_guide.md)** - **START HERE** - Complete guide to using the framework
2. **[Testing Guide](docs/testing_guide.md)** - **Testing patterns and best practices**
3. **[PRD](docs/prd.md)** - Project requirements and architecture decisions


## 🚀 Getting Started

1. **Read the [API Usage Guide](docs/api_usage_guide.md)** to understand the framework
2. **Study the working demos in the examples directory** to understand the power of Actions
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

#### Configuration (actions/config.py)
- **Configurable debug logging**: Fine-grained, level-based diagnostics with per-Action filtering for focused output
- **Debug levels**: Level 0 (off), Level 1 (summary counts), Level 2 (lifecycle events), Level 3+ (verbose per-frame details)
- **Action filtering**: Observe specific action classes or all actions for targeted debugging
- **Environment variables**: `ARCADEACTIONS_DEBUG=2`, `ARCADEACTIONS_DEBUG_ALL=1`, `ARCADEACTIONS_DEBUG_INCLUDE=MoveUntil,CallbackUntil`
- **Programmatic API**: `set_debug_options(level=2, include=["MoveUntil"])` or `observe_actions(MoveUntil, CallbackUntil)` in your app startup

#### Instant Action System (actions/instant.py)
- **MoveBy** - Relative Sprite or SpriteList positioning
- **MoveTo** - Absolute positioning

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement until condition met
- **FollowPathUntil** - Follow Bezier curve paths with optional automatic sprite rotation
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes  
- **FadeUntil** - Alpha velocity changes
- **CycleTexturesUntil** - Cycle through a list of textures at a specific frame rate with simulation time duration support
- **BlinkUntil** - Toggle sprite visibility with optional enter/exit callbacks for collision management
- **CallbackUntil** - Execute callback functions at specified intervals or every frame until condition is met
- **DelayUntil** - Wait for condition to be met
- **TweenUntil** - Direct property animation from start to end value

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)
- **StateMachine** - Simple predicate-based state switcher for animation and behavior states

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Formation Management (actions/formation.py)
- **Formation functions** - Grid, line, circle, diamond, V-formation, triangle, hexagonal grid, arc, concentric rings, cross, and arrow positioning
  - Zero-allocation support: pass `sprites=` to arrange existing sprites without allocating
  - Contract: exactly one of `sprites` or creation inputs (`count` or `sprite_factory`) is required
  - Grid rule: when `sprites` is provided, `len(sprites)` must equal `rows * cols`

#### Movement Patterns (actions/pattern.py)
- **Movement pattern functions** - Zigzag, wave, spiral, figure-8, orbit, bounce, and patrol patterns
- **Condition helpers** - Time-based and sprite count conditions for conditional actions
### ♻️ Zero-Allocation Gameplay (experimental)

ArcadeActions now provides an optional zero-allocation workflow to eliminate per-wave sprite creation.

1) Use the new `SpritePool` (in `actions.pools`) to pre-allocate sprites once at boot:

```python
from actions.pools import SpritePool
from actions import arrange_grid
import arcade

def make_block():
    return arcade.Sprite(":resources:images/items/star.png", scale=0.8)

pool = SpritePool(make_block, max_size=300)
blocks = pool.acquire(150)                                    # borrow invisible sprites
arrange_grid(rows=30, cols=5, sprites=blocks, start_x=0, start_y=0)  # position only
pool.assign(blocks)                                           # return to pool (hidden & neutral)
```

2) During gameplay, acquire → arrange → release without allocating:

```python
shield = pool.acquire(width * 30)
arrange_grid(rows=30, cols=width, sprites=shield, start_x=WINDOW+50, start_y=TUNNEL_H)
# ... gameplay ...
pool.release(shield)
```

SpritePool API:
- `acquire(n) -> list[Sprite]` — borrow invisible, un-positioned sprites
- `release(iterable[Sprite])` — return sprites to the pool (hidden, detached, reset)
- `assign(iterable[Sprite])` — load externally-created sprites into the pool once

Arrange functions contract:
- Provide exactly one of `sprites` or creation inputs (`count`/`sprite_factory`)
- When using `sprites` with `arrange_grid`, `len(sprites) == rows * cols` is required


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
| Instant actions | Position initialization in a sequence | sequence(MoveBy(...), MoveUntil(...)) |
| Formation positioning | Formation functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Curved path movement | `follow_path_until` helper | `follow_path_until(sprite, points, ...)` |
| Visibility blinking | `blink_until` helper | `blink_until(sprite, seconds_until_change=0.25, condition=...)` |
| Boundary detection | `move_until` with bounds | `move_until(sprite, ..., bounds=bounds, boundary_behavior="bounce")` |
| Smooth acceleration | `ease()` helper | `ease(sprite, action, ...)` |
| Complex curved movement | `ease()` + `follow_path_until` | `ease(sprite, follow_path_until(...), ...)` |
| Property animation | `tween_until` helper | `tween_until(sprite, 0, 100, "center_x", ...)` |
| Standard sprites (no actions) | arcade.Sprite + arcade.SpriteList | Regular Arcade usage |
