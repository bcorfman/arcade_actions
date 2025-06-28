# ArcadeActions Framework Documentation

## 🚀 Quick Start

**New to ArcadeActions?** Start here: **[API Usage Guide](api_usage_guide.md)**

This guide explains when and how to use each component of the framework, with clear examples and common patterns.

## 📚 Documentation Overview

### Essential Reading
1. **[API Usage Guide](api_usage_guide.md)** - **START HERE** - Complete guide to using the framework correctly
2. **[Testing Index](testing_index.md)** - Comprehensive testing patterns and examples
3. **[PRD](prd.md)** - Project requirements and architecture decisions

### Specialized Guides
- **[Boundary Events](boundary_event.md)** - BoundedMove and WrappedMove callback patterns
- **[Game Loop Updates](game_loop_updates.md)** - Integration with game loops and SpriteGroup management
- **[Testing Guide](testing.md)** - Core testing patterns and best practices
- **[Movement Testing](testing_movement.md)** - Specialized movement action testing

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
from actions.base import ActionSprite
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import BoundedMove

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
        
        self._setup_movement()
    
    def _setup_movement(self):
        # Boundary detection with edge sprite callbacks
        def on_bounce(sprite, axis):
            if axis == 'x':
                # Move ALL enemies down using GroupAction (coordinated behavior)
                move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
                self.enemies.do(move_down)
                
                # Clear and restart movement
                self.enemies.clear_actions()
                self._start_movement()
        
        # Apply BoundedMove to entire group
        bounds = lambda: (50, 0, 750, 600)
        self.boundary_action = BoundedMove(bounds, on_bounce=on_bounce)
        self.boundary_action.target = self.enemies
        self.boundary_action.start()
        
        self._start_movement()
    
    def _start_movement(self):
        # GroupAction coordinates all sprites
        move_action = MoveBy((400, 0), 4.0)
        self.enemies.do(move_action)
    
    def update(self, delta_time):
        # Automatic GroupAction management
        self.enemies.update(delta_time)
        self.boundary_action.update(delta_time)
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

### Boundary Interactions
```python
def test_boundary_with_group(self, sprite_group):
    bounce_called = False
    def on_bounce(sprite, axis):
        nonlocal bounce_called
        bounce_called = True
    
    bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)
    bounce_action.target = sprite_group
    bounce_action.start()
    
    # Test edge detection and coordination
    assert bounce_called
```

## 📋 Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Single sprite needs actions | `ActionSprite.do(action)` | Only ActionSprite supports actions |
| Multiple sprites move together | `SpriteGroup.do(action)` | Automatic coordination |
| Group boundary detection | `BoundedMove` + `SpriteGroup` | Edge detection + callbacks |
| Collision detection | `SpriteGroup.on_collision_with()` | Efficient group collisions |
| No actions needed | `arcade.Sprite` + `arcade.SpriteList` | Standard Arcade |

## 🔧 Current Implementation Status

### ✅ Completed Features
- **ActionSprite**: Full action support with automatic lifecycle management
- **SpriteGroup**: Automatic GroupAction management and collision detection
- **BoundedMove**: Enhanced with edge detection for group coordination
- **GroupAction**: Automatic creation, coordination, and cleanup
- **Space Invaders Pattern**: Fully implemented with proper spacing preservation
- **Comprehensive Testing**: All patterns tested and documented
- **API Documentation**: Complete usage guide with examples

### 🎯 Key Achievements
1. **Automatic GroupAction Management**: No manual tracking required
2. **Edge Detection**: Only edge sprites trigger boundary callbacks
3. **Spacing Preservation**: Enhanced BoundedMove prevents spacing drift
4. **Method Chaining**: Collision detection supports fluent API
5. **Clean API**: Clear separation between individual and group behaviors

## 📖 Documentation Structure

```
docs/
├── README.md                 # This file - overview and quick start
├── api_usage_guide.md       # Complete API usage patterns (START HERE)
├── testing_index.md         # Comprehensive testing guide
├── testing.md               # Core testing patterns
├── testing_movement.md      # Movement-specific testing
├── boundary_event.md        # Boundary callback patterns
├── game_loop_updates.md     # Game integration patterns
└── prd.md                   # Requirements and architecture
```

## 🚀 Getting Started

1. **Read the [API Usage Guide](api_usage_guide.md)** to understand the framework
2. **Check the [Testing Index](testing_index.md)** for testing patterns
3. **Look at `invaders.py`** for a complete working example
4. **Follow the patterns** consistently in your code

## 💡 Best Practices

1. **Always use ActionSprite** for sprites that need actions
2. **Use SpriteGroup** for coordinated group behavior
3. **Let SpriteGroup manage GroupActions** automatically
4. **Apply BoundedMove to entire groups** for proper coordination
5. **Use method chaining** for collision detection
6. **Follow the documented patterns** consistently
7. **Test both individual and group behaviors**
8. **Verify automatic cleanup** in tests

The ArcadeActions framework provides a clean, powerful API for creating complex sprite behaviors with minimal code. Follow the patterns in this documentation for the best results! 