# ArcadeActions Framework Documentation

## 🚀 Quick Start

**Getting started with ArcadeActions?** Start here: **[API Usage Guide](api_usage_guide.md)**

This guide explains when and how to use each component of the framework, with clear examples and common patterns.

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](api_usage_guide.md)** - **START HERE** - Complete guide to using the framework correctly
2. **[Testing Index](testing_index.md)** - Comprehensive testing patterns and examples
3. **[PRD](prd.md)** - Project requirements and architecture decisions

## 🎯 Key Concepts

### Core Components
- **ActionSprite**: The only sprite class that supports actions
- **SpriteGroup**: Manages collections of sprites with automatic GroupAction coordination
- **GroupAction**: Automatically created by SpriteGroup.do() for synchronized behavior
- **BoundedMove**: Provides boundary detection with edge sprite callbacks for group coordination

### API Patterns

#### ✅ Correct Usage
```python
# Individual sprite control
sprite = ActionSprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))

# Group coordination
enemies = SpriteGroup()
enemies.do(MoveBy((200, 0), 2.0))  # All move together

# Boundary detection for groups
bounce_action = BoundedMove(get_bounds, on_bounce=callback)
bounce_action.target = enemies  # Edge detection + coordination
bounce_action.start()

# Collision detection
bullets.on_collision_with(enemies, handle_collision)
```

#### ❌ Common Mistakes
```python
# DON'T: Use arcade.Sprite with actions
sprite = arcade.Sprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # FAILS!

# DON'T: Manual GroupAction tracking
group_action = enemies.do(move_action)
group_action.update(delta_time)  # Easy to forget!

# DON'T: Individual BoundedMove in groups
for sprite in enemies:
    sprite.do(move_action | BoundedMove(bounds))  # Spacing issues!
```

## 🎮 Example: Space Invaders Pattern

```python
import arcade
from actions.base import Action
from actions.conditional import MoveUntil, DelayUntil, duration

class SpaceInvaders:
    def __init__(self):
        # Create enemy formation using SpriteGroup
        self.enemies = SpriteGroup()
        for row in range(5):
            for col in range(10):
                enemy = ActionSprite(":resources:images/enemy.png")
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 50
                self.enemies.append(enemy)
        
        # Store enemies for movement management
        self.enemies = enemies
        self._setup_movement_pattern()
    
    def _setup_movement(self):
        # Boundary detection with edge sprite callbacks
        def on_bounce(sprite, axis):
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
- **Operator overloads** - `+` for sequences, `|` for parallel

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement until condition met
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes  
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition to be met

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `+` operator)
- **Parallel actions** - Run actions in parallel (use `|` operator)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Game Management (actions/pattern.py)
- **Formation functions** - Grid, line, circle, and V-formation positioning

## 📋 Decision Matrix

| Scenario | Use | Example |
|----------|-----|---------|
| Single sprite behavior | Direct action application | `action.apply(sprite, tag="move")` |
| Group coordination | Action on SpriteList | `action.apply(enemies, tag="formation")` |
| Sequential behavior | `+` operator | `delay + move + fade` |
| Parallel behavior | `\|` operator | `move \| rotate \| scale` |
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
move_action = MoveUntil((100, 0), duration(2.0))
move_action.apply(player, tag="movement")
move_action.apply(enemies, tag="formation")

# Compose with operators
complex = delay + (move | fade) + final_action
complex.apply(sprite, tag="complex")

# Formation positioning
from actions.pattern import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)

# Global update handles everything
Action.update_all(delta_time)
```

## 🧪 Testing Patterns

### Individual Actions
```python
def test_individual_action(self):
    sprite = ActionSprite(":resources:images/test.png")
    sprite.do(MoveBy((100, 0), 1.0))
    sprite.update(1.0)
    assert sprite.center_x == 100
```

### Group Actions
```python
def test_group_action(self, sprite_group):
    move_action = MoveBy((50, 0), 1.0)
    group_action = sprite_group.do(move_action)
    
    # Verify automatic management
    assert len(sprite_group._group_actions) == 1
    sprite_group.update(1.0)
    assert len(sprite_group._group_actions) == 0  # Auto-cleanup
```

### Formation Management
```python
def test_formation_management():
    from actions.pattern import arrange_grid
    
    enemies = arcade.SpriteList([enemy1, enemy2, enemy3])
    
    # Test formation positioning
    arrange_grid(enemies, rows=2, cols=2, start_x=100, start_y=400)
    
    # Test group actions
    pattern = delay + move + fade
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