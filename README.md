# ArcadeActions Framework Documentation

## 🚀 Quick Start

**Getting started with ArcadeActions?** Start here: **[API Usage Guide](api_usage_guide.md)**

ArcadeActions is a framework for Arcade 3.x that enables declarative, flexible game behaviors by running actions until any user-defined condition is met.

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](api_usage_guide.md)** - **START HERE** - Complete guide to using the framework
2. **[Testing Guide](testing_guide.md)** - **Testing patterns and best practices**
3. **[PRD](prd.md)** - Project requirements and architecture decisions

## 🎯 Key Concepts

### ⚠️ CRITICAL API Rule: Pixels Per Frame at 60 FPS
**All velocity values in ArcadeActions use Arcade's native semantics: "pixels per frame at 60 FPS", NOT "pixels per second".**

This ensures perfect consistency with Arcade's sprite system. When you set `sprite.change_x = 5`, the sprite moves 5 pixels per frame. ArcadeActions uses the same semantics:
- `MoveUntil((5, 0), condition)` → 5 pixels/frame right (= 300 pixels/second at 60 FPS)  
- `RotateUntil(3, condition)` → 3 degrees/frame (= 180 degrees/second at 60 FPS)

### Core Philosophy: Condition-Based Actions
Actions run until conditions are met, not for fixed time periods:

**IMPORTANT:** ArcadeActions uses Arcade's native velocity semantics - values represent "pixels per frame at 60 FPS", not "pixels per second".

```python
from actions.conditional import MoveUntil, RotateUntil, FadeUntil, FollowPathUntil

# Move until reaching a position (5 pixels/frame = 300 pixels/second at 60 FPS)
move = MoveUntil((5, 0), lambda: sprite.center_x > 700)

# Follow curved path with automatic rotation
path_points = [(100, 100), (200, 200), (300, 100)]
path = FollowPathUntil(path_points, 2.5, lambda: sprite.center_x > 400, rotate_with_path=True)  # 2.5 pixels/frame

# Rotate until reaching an angle  
rotate = RotateUntil(1.5, lambda: sprite.angle >= 45)  # 1.5 degrees/frame

# Fade until reaching transparency
fade = FadeUntil(-4, lambda: sprite.alpha <= 50)  # -4 alpha/frame
```

### MoveUntil with Collision Detection and Data Passing

MoveUntil can do much more than just stop at a position. The condition function can return any data when a stop condition is met, and this data is passed to the callback for efficient, zero-duplication event handling. This is especially powerful for collision detection:

```python
# Example: Move a bullet until it collides with an enemy or shield, or leaves the screen

def bullet_collision_check():
    enemy_hits = arcade.check_for_collision_with_list(bullet, enemy_list)
    shield_hits = arcade.check_for_collision_with_list(bullet, shield_list)
    off_screen = bullet.bottom > WINDOW_HEIGHT

    if enemy_hits or shield_hits or off_screen:
        return {
            "enemy_hits": enemy_hits,
            "shield_hits": shield_hits,
            "off_screen": off_screen
        }
    return None  # Continue moving

# The callback receives the collision data from the condition function

def handle_bullet_collision(collision_data):
    bullet.remove_from_sprite_lists()
    for enemy in collision_data["enemy_hits"]:
        enemy.remove_from_sprite_lists()
    for shield in collision_data["shield_hits"]:
        shield.remove_from_sprite_lists()
    if collision_data["off_screen"]:
        print("Bullet left the screen!")

bullet_action = MoveUntil((0, BULLET_SPEED), bullet_collision_check, handle_bullet_collision)
bullet_action.apply(bullet)
```

This pattern ensures collision checks are only performed once per frame, and all relevant data is passed directly to the handler — no need for extra state or repeated queries. This is the recommended approach for efficient, event-driven collision handling in ArcadeActions.

### Animation Approaches: Ease vs TweenUntil

ArcadeActions provides two distinct approaches for creating smooth animations:

#### Ease: Smooth Acceleration/Deceleration of Continuous Actions
**Use Ease when:** You want to smoothly start or stop continuous actions (movement, rotation, path following)

```python
from actions.easing import Ease
from arcade import easing

# Smooth acceleration into constant movement
move = MoveUntil((200, 0), lambda: False)  # Continuous movement
eased_move = Ease(move, seconds=2.0, ease_function=easing.ease_in_out)
eased_move.apply(sprite, tag="smooth_movement")
# Result: Sprite accelerates smoothly to 200px/s, then continues at that speed

# Smooth path following with rotation
path_points = [(100, 100), (200, 200), (300, 100)]
path_action = FollowPathUntil(path_points, 300, lambda: False, rotate_with_path=True)
eased_path = Ease(path_action, seconds=1.5, ease_function=easing.ease_in_out)
eased_path.apply(sprite, tag="smooth_path")
# Result: Sprite smoothly accelerates along curved path while rotating
```

#### TweenUntil: Direct Property Animation
**Use TweenUntil when:** You want to animate a specific property from A to B with precise control

```python
from actions.conditional import TweenUntil, duration

# Move sprite from x=0 to x=100 over 1 second with easing
tween_x = TweenUntil(0, 100, "center_x", duration(1.0), ease_function=easing.ease_out)
tween_x.apply(sprite, tag="slide_in")
# Result: Sprite's center_x goes directly from 0 to 100, then stops

# Fade sprite from invisible to visible
fade_in = TweenUntil(0, 255, "alpha", duration(0.5))
fade_in.apply(sprite, tag="appear")
# Result: Sprite fades from transparent to opaque, then stops
```

#### When to Use Which?

| Use Case | Choose | Why |
|----------|--------|-----|
| Smooth missile launch | **Ease** | Missile accelerates to cruise speed, then continues |
| UI panel slide-in | **TweenUntil** | Panel moves from off-screen to final position |
| Enemy formation movement | **Ease** | Formation smoothly reaches marching speed |
| Health bar animation | **TweenUntil** | Bar width changes from old to new value |
| Curved path following | **Ease** | Smooth acceleration along complex curves |
| Button press feedback | **TweenUntil** | Button scale bounces from 1.0 to 1.2 to 1.0 |

### Global Action Management
No manual action tracking - everything is handled globally:

```python
from actions.base import Action

# Apply actions directly to any arcade.Sprite or arcade.SpriteList
action.apply(sprite, tag="movement")
action.apply(sprite_list, tag="formation")

# Single global update in your game loop
def on_update(self, delta_time):
    Action.update_all(delta_time)  # Handles all active actions
```

### Composition Helpers: `sequence()` and `parallel()`
Build complex behaviors declaratively with helper functions:

```python
from actions.composite import sequence, parallel

# Sequential actions run one after another
seq = sequence(delay, move, fade)

# Parallel actions run independently
par = parallel(move, rotate, scale)

# Nested combinations are fully supported
complex_action = sequence(delay, parallel(move, fade), rotate)
```

## 🎮 Example: Space Invaders Pattern

```python
import arcade
from actions.base import Action
from actions.conditional import MoveUntil, DelayUntil, duration
from actions.formation import arrange_grid


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
            if axis == 'x':
                # Move entire formation down and change direction
                drop_action = MoveUntil((0, -30), duration(0.3))
                drop_action.apply(self.enemies, tag="drop")
        
        # Create continuous horizontal movement with boundary detection
        bounds = (50, 0, 750, 600)  # left, bottom, right, top
        move_action = MoveUntil(
            (50, 0), 
            lambda: False,  # Move indefinitely
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary=on_boundary_hit
        )
        
        # Apply to enemies with global management
        move_action.apply(self.enemies, tag="formation_movement")
    
    def on_update(self, delta_time):
        # Single line handles all action updates
        Action.update_all(delta_time)
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
- **Formation functions** - Grid, line, circle, diamond, and V-formation positioning

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
| Single sprite behavior | Direct action application | `action.apply(sprite, tag="move")` |
| Group coordination | Action on SpriteList | `action.apply(enemies, tag="formation")` |
| Sequential behavior | `sequence()` | `sequence(delay, move, fade)` |
| Parallel behavior | `parallel()` | `parallel(move, rotate, scale)` |
| Formation positioning | Pattern functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Curved path movement | FollowPathUntil | `FollowPathUntil(points, 200, condition, rotate_with_path=True)` |
| Boundary detection | MoveUntil with bounds | `MoveUntil(vel, cond, bounds=bounds, boundary_behavior="bounce")` |
| Smooth acceleration | Ease wrapper | `Ease(action, seconds=2.0, ease_function=easing.ease_in_out)` |
| Complex curved movement | Ease + FollowPathUntil | `Ease(FollowPathUntil(points, vel, cond, rotate_with_path=True), 1.5)` |
| Property animation | TweenUntil | `TweenUntil(0, 100, "center_x", duration(1.0))` |
| Standard sprites (no actions) | arcade.Sprite + arcade.SpriteList | Regular Arcade usage |

## 🎯 API Patterns

### ✅ Correct Usage
```python
# Works with any arcade.Sprite or arcade.SpriteList
player = arcade.Sprite("player.png")
enemies = arcade.SpriteList([enemy1, enemy2, enemy3])

# Apply actions directly
move = MoveUntil((100, 0), duration(2.0))
move.apply(player, tag="movement")
move.apply(enemies, tag="formation")

# Compose with helpers
from actions.composite import sequence, parallel

complex_action = sequence(delay, parallel(move, fade), rotate)
complex_action.apply(sprite, tag="complex")

# Formation positioning
from actions.formation import arrange_grid, arrange_diamond

# Create a new grid of enemies with sprite_factory
def enemy_factory():
    return arcade.Sprite(":resources:images/enemy.png")

enemies = arrange_grid(
    rows=3,
    cols=5,
    start_x=100,
    start_y=400,
    spacing_x=60,
    spacing_y=40,
    sprite_factory=enemy_factory,  # Creates fresh sprites for each position
)

# Create diamond formation for special attack patterns
diamond_formation = arrange_diamond(
    count=13,  # 1 center + 4 layer 1 + 8 layer 2
    center_x=400,
    center_y=300,
    spacing=50,
    sprite_factory=enemy_factory,
)

# Create hollow diamond formation (no center sprite)
hollow_diamond = arrange_diamond(
    count=12,  # 4 layer 1 + 8 layer 2 (no center)
    center_x=600,
    center_y=300,
    spacing=50,
    include_center=False,
    sprite_factory=enemy_factory,
)

# Apply movement patterns to formations
from actions.pattern import create_wave_pattern, create_zigzag_pattern

# Wave movement for the grid formation
wave_movement = create_wave_pattern(amplitude=50, frequency=2, length=400, speed=100)
wave_movement.apply(enemies, tag="wave_formation")

# Zigzag pattern for individual enemy
zigzag_attack = create_zigzag_pattern(width=80, height=40, speed=120, segments=4)
zigzag_attack.apply(special_enemy, tag="zigzag_attack")

# Global update handles everything
Action.update_all(delta_time)
```

## 🧪 Testing Patterns

### Individual Actions
```python
def test_move_until_condition():
    sprite = arcade.Sprite(":resources:images/test.png")
    sprite.center_x = 0
    
    # Apply action
    action = MoveUntil((100, 0), lambda: sprite.center_x >= 100)
    action.apply(sprite, tag="test")
    
    # Test with global update
    Action.update_all(1.0)
    assert sprite.center_x == 100
```

### Group Actions
```python
def test_group_coordination():
    enemies = arcade.SpriteList()
    for i in range(3):
        enemy = arcade.Sprite(":resources:images/enemy.png")
        enemies.append(enemy)
    
    # Apply to entire group
    action = MoveUntil((0, -50), duration(1.0))
    action.apply(enemies, tag="formation")
    
    # Test coordinated movement
    Action.update_all(1.0)
    for enemy in enemies:
        assert enemy.center_y == -50
```

### Formation Management
```python
def test_formation_management():
    from actions.formation import arrange_grid
    
    # Create a grid of enemies with sprite_factory
    def enemy_factory():
        return arcade.Sprite(":resources:images/enemy.png")
    
    enemies = arrange_grid(
        rows=2,
        cols=2,
        start_x=100,
        start_y=400,
        spacing_x=60,
        spacing_y=40,
        sprite_factory=enemy_factory,
    )
    
    # Test group actions
    pattern = sequence(delay, move, fade)
    pattern.apply(enemies, tag="test")
    
    # Test group state
    assert len(enemies) == 4  # 2x2 grid
    assert enemies[0].center_x == 100  # First sprite at start_x
    assert enemies[0].center_y == 400  # First sprite at start_y
```

## 📖 Documentation Structure

```
docs/
├── README.md                 # This file - overview and quick start
├── api_usage_guide.md       # Complete API usage patterns (START HERE)
├── testing_guide.md         # Testing patterns and fixtures
└── prd.md                   # Requirements and architecture
```

## 🚀 Getting Started

1. **Read the [API Usage Guide](api_usage_guide.md)** to understand the framework
2. **Study the Space Invaders example** above for a complete pattern
3. **Start with simple conditional actions** and build up to complex compositions
4. **Use formation functions** for organizing sprite positions and layouts

The ArcadeActions framework transforms Arcade game development with declarative, condition-based behaviors! 

# Individual sprite control
sprite = arcade.Sprite("image.png")
action = MoveUntil((100, 0), lambda: sprite.center_x > 700)
action.apply(sprite, tag="movement")

# Group management  
enemies = arcade.SpriteList()  # Use standard arcade.SpriteList
action = MoveUntil((50, 0), duration(2.0))
action.apply(enemies, tag="formation")
