# ArcadeActions Framework Documentation

## 🚀 Quick Start

**Getting started with ArcadeActions?** Start here: **[API Usage Guide](api_usage_guide.md)**

ArcadeActions is a **conditional action system** for Arcade 3.x that enables declarative game behaviors through condition-based actions rather than fixed durations.

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](api_usage_guide.md)** - **START HERE** - Complete guide to using the framework
2. **[Testing Guide](testing_guide.md)** - **Testing patterns and best practices**
3. **[PRD](prd.md)** - Project requirements and architecture decisions

## 🎯 Key Concepts

### Core Philosophy: Condition-Based Actions
Actions run until conditions are met, not for fixed time periods:

```python
from actions.conditional import MoveUntil, RotateUntil, FadeUntil

# Move until reaching a position
move = MoveUntil((100, 0), lambda: sprite.center_x > 700)

# Rotate until reaching an angle  
rotate = RotateUntil(90, lambda: sprite.angle >= 45)

# Fade until reaching transparency
fade = FadeUntil(-50, lambda: sprite.alpha <= 50)
```

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
from actions.pattern import arrange_grid


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
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes  
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition to be met

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Game Management (actions/pattern.py)
- **Formation functions** - Grid, line, circle, and V-formation positioning

## 📋 Decision Matrix

| Scenario | Use | Example |
|----------|-----|---------|
| Single sprite behavior | Direct action application | `action.apply(sprite, tag="move")` |
| Group coordination | Action on SpriteList | `action.apply(enemies, tag="formation")` |
| Sequential behavior | `sequence()` | `sequence(delay, move, fade)` |
| Parallel behavior | `parallel()` | `parallel(move, rotate, scale)` |
| Formation positioning | Pattern functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Boundary detection | MoveUntil with bounds | `MoveUntil(vel, cond, bounds=bounds, boundary_behavior="bounce")` |
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

# Compose with operators
from actions.composite import sequence, parallel

complex_action = sequence(delay, parallel(move, fade), rotate)
complex_action.apply(sprite, tag="complex")

# Formation positioning
from actions.pattern import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)

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
    from actions.pattern import arrange_grid
    
    enemies = arcade.SpriteList([enemy1, enemy2, enemy3])
    
    # Test formation positioning
    arrange_grid(enemies, rows=2, cols=2, start_x=100, start_y=400)
    
    # Test group actions
    pattern = sequence(delay, move, fade)
    pattern.apply(enemies, tag="test")
    
    # Test group state
    assert len(enemies) == 3
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