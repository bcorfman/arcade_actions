# ArcadeActions API Usage Guide

## Overview

This guide provides clear guidance on when and how to use the different components of the ArcadeActions framework. Understanding these patterns is crucial for building effective games and demos.

## Core Components

### 1. ActionSprite
**When to use:** For any sprite that needs to perform actions.
**Key principle:** Only `ActionSprite` instances can use the Actions system.

```python
from actions.base import ActionSprite
from actions.interval import MoveBy

# Create an ActionSprite
player = ActionSprite(":resources:images/player.png")
player.center_x = 100
player.center_y = 100

# Apply an action
move_action = MoveBy((200, 0), 2.0)  # Move 200 pixels right over 2 seconds
player.do(move_action)

# Update in game loop
player.update(delta_time)
```

### 2. Individual Actions
**When to use:** For single sprite behaviors, simple movements, or when you need precise control.

```python
# Basic movement
move_action = MoveBy((100, 50), 1.0)
sprite.do(move_action)

# Rotation
rotate_action = RotateBy(360, 2.0)
sprite.do(rotate_action)

# Composite actions for complex behavior
complex_action = MoveBy((100, 0), 1.0) + RotateBy(180, 0.5) + FadeTo(0, 1.0)
sprite.do(complex_action)
```

### 3. SpriteGroup
**When to use:** For managing collections of sprites that need coordinated behavior.
**Key features:** Automatic GroupAction management, collision detection, group operations.

```python
from actions.group import SpriteGroup
from actions.interval import MoveBy

# Create a SpriteGroup
enemies = SpriteGroup()

# Add sprites to the group
for i in range(5):
    enemy = ActionSprite(":resources:images/enemy.png")
    enemy.center_x = 100 + i * 80
    enemy.center_y = 400
    enemies.append(enemy)

# Apply action to entire group (creates GroupAction automatically)
move_action = MoveBy((200, 0), 3.0)
enemies.do(move_action)  # All enemies move together

# Update in game loop (automatically updates GroupActions)
enemies.update(delta_time)
```

### 4. GroupAction
**When to use:** Automatically created by `SpriteGroup.do()`. You rarely create these directly.
**Key principle:** Coordinates the same action across multiple sprites.

```python
# GroupAction is created automatically
group_action = enemies.do(move_action)

# GroupAction manages individual actions for each sprite
assert len(group_action.actions) == len(enemies)

# Automatic cleanup when actions complete
# No manual tracking needed!
```

## Usage Patterns

### Pattern 1: Individual Sprite Control
**Use case:** Player character, single enemies, UI elements.

```python
class Player:
    def __init__(self):
        self.sprite = ActionSprite(":resources:images/player.png")
        self.sprite.center_x = 400
        self.sprite.center_y = 100
    
    def move_to(self, x, y):
        move_action = MoveTo((x, y), 1.0)
        self.sprite.do(move_action)
    
    def update(self, delta_time):
        self.sprite.update(delta_time)
```

### Pattern 2: Group Coordination
**Use case:** Enemy formations, bullet patterns, particle effects.

```python
class EnemyFormation:
    def __init__(self):
        self.enemies = SpriteGroup()
        self._setup_formation()
    
    def _setup_formation(self):
        # Create 3x5 grid of enemies
        for row in range(3):
            for col in range(5):
                enemy = ActionSprite(":resources:images/enemy.png")
                enemy.center_x = 200 + col * 80
                enemy.center_y = 500 - row * 60
                self.enemies.append(enemy)
    
    def move_formation(self, dx, dy, duration):
        move_action = MoveBy((dx, dy), duration)
        self.enemies.do(move_action)  # All enemies move together
    
    def update(self, delta_time):
        self.enemies.update(delta_time)  # Automatically updates GroupActions
```

### Pattern 3: Boundary Interactions with Groups
**Use case:** Space Invaders-style movement, bouncing formations.

```python
from actions.move import BoundedMove

class SpaceInvaders:
    def __init__(self):
        self.enemies = SpriteGroup()
        self._setup_enemies()
        self._setup_movement()
    
    def _setup_movement(self):
        # Define movement boundaries
        def get_bounds():
            return (50, 0, 750, 600)  # left, bottom, right, top
        
        # Callback for when edge enemies hit boundaries
        def on_bounce(sprite, axis):
            if axis == "x":
                # Move all enemies down using GroupAction
                move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
                self.enemies.do(move_down)
                
                # Clear current actions and start new movement
                self.enemies.clear_actions()
                self._start_new_movement()
        
        # Set up boundary detection (only edge sprites trigger callbacks)
        self.boundary_action = BoundedMove(get_bounds, on_bounce=on_bounce)
        self.boundary_action.target = self.enemies
        self.boundary_action.start()
        
        # Start initial movement
        self._start_new_movement()
    
    def _start_new_movement(self):
        # Move horizontally across screen
        move_action = MoveBy((400, 0), 4.0)
        self.enemies.do(move_action)
    
    def update(self, delta_time):
        self.enemies.update(delta_time)
        self.boundary_action.update(delta_time)
```

### Pattern 4: Collision Detection with Groups
**Use case:** Bullet vs enemy collisions, player vs powerup collisions.

```python
class CollisionSystem:
    def __init__(self):
        self.player_bullets = SpriteGroup()
        self.enemies = SpriteGroup()
        self.shields = SpriteGroup()
        
        # Set up collision handlers with method chaining
        self.player_bullets.on_collision_with(
            self.enemies, self._bullet_enemy_collision
        ).on_collision_with(
            self.shields, self._bullet_shield_collision
        )
    
    def _bullet_enemy_collision(self, bullet, hit_enemies):
        bullet.remove_from_sprite_lists()
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()
            # Add explosion effect, score, etc.
    
    def _bullet_shield_collision(self, bullet, hit_shields):
        bullet.remove_from_sprite_lists()
        for shield in hit_shields:
            shield.remove_from_sprite_lists()
    
    def update(self, delta_time):
        self.player_bullets.update(delta_time)
        self.enemies.update(delta_time)
        self.shields.update(delta_time)
        
        # Check collisions
        self.player_bullets.update_collisions()
```

## Decision Matrix

| Scenario | Use | Reason |
|----------|-----|--------|
| Single sprite needs to move | `ActionSprite.do(action)` | Simple, direct control |
| Multiple sprites move together | `SpriteGroup.do(action)` | Automatic coordination |
| Sprites need different actions | Individual `ActionSprite.do()` calls | Different behaviors |
| Boundary detection for groups | `BoundedMove` + `SpriteGroup` | Edge detection + callbacks |
| Screen wrapping for groups | `WrappedMove` + `SpriteGroup` | Edge detection + callbacks |
| Collision detection | `SpriteGroup.on_collision_with()` | Efficient group collisions |
| Complex sequences | Composite actions (`+`, `|`, `*`) | Declarative behavior |

## Common Mistakes to Avoid

### ❌ Don't: Use regular arcade.Sprite with Actions
```python
# WRONG - arcade.Sprite doesn't support actions
sprite = arcade.Sprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # This will fail!
```

### ✅ Do: Use ActionSprite for all action-based sprites
```python
# CORRECT - ActionSprite supports actions
sprite = ActionSprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # This works!
```

### ❌ Don't: Manually track GroupActions
```python
# WRONG - Manual tracking is error-prone
group_action = sprite_group.do(move_action)
# ... later in game loop ...
group_action.update(delta_time)  # Easy to forget!
```

### ✅ Do: Let SpriteGroup handle GroupActions automatically
```python
# CORRECT - Automatic management
sprite_group.do(move_action)
# ... later in game loop ...
sprite_group.update(delta_time)  # Automatically updates GroupActions
```

### ❌ Don't: Apply BoundedMove to individual sprites in a group
```python
# WRONG - Causes spacing issues
for sprite in sprite_group:
    bounce_action = BoundedMove(get_bounds)
    sprite.do(move_action | bounce_action)
```

### ✅ Do: Apply BoundedMove to the entire SpriteGroup
```python
# CORRECT - Proper edge detection and coordination
bounce_action = BoundedMove(get_bounds, on_bounce=handle_bounce)
bounce_action.target = sprite_group
bounce_action.start()
sprite_group.do(move_action)
```

### ❌ Don't: Apply WrappedMove to individual sprites in a group
```python
# WRONG - All sprites wrap individually, no coordination
for sprite in sprite_group:
    wrap_action = WrappedMove(get_bounds)
    sprite.do(move_action | wrap_action)
```

### ✅ Do: Apply WrappedMove to the entire SpriteGroup
```python
# CORRECT - Only edge sprites trigger wraps, enables coordination
wrap_action = WrappedMove(get_bounds, on_wrap=handle_wrap)
wrap_action.target = sprite_group
wrap_action.start()
sprite_group.do(move_action)
```

### ❌ Don't: Directly manipulate sprite positions in groups
```python
# WRONG - Direct position manipulation bypasses the action system
def on_bounce(sprite, axis):
    for enemy in enemies:
        enemy.center_y -= 30  # Direct manipulation!
```

### ✅ Do: Use GroupActions for coordinated positioning
```python
# CORRECT - Use MoveBy GroupAction for coordinated movement
def on_bounce(sprite, axis):
    move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
    enemies.do(move_down)  # GroupAction coordinates all sprites
```

## Testing Patterns

### Testing Individual Actions
```python
def test_individual_action(self):
    sprite = ActionSprite(":resources:images/test.png")
    sprite.center_x = 0
    sprite.center_y = 0
    
    move_action = MoveBy((100, 0), 1.0)
    sprite.do(move_action)
    
    sprite.update(0.5)  # Half duration
    assert sprite.center_x == 50  # Halfway there
    
    sprite.update(0.5)  # Complete
    assert sprite.center_x == 100
    assert not sprite.is_busy()
```

### Testing Group Actions
```python
def test_group_action(self):
    sprite_group = SpriteGroup()
    for i in range(3):
        sprite = ActionSprite(":resources:images/test.png")
        sprite.center_x = i * 100
        sprite_group.append(sprite)
    
    move_action = MoveBy((50, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)  # Complete action
    
    # All sprites should have moved
    for i, sprite in enumerate(sprite_group):
        assert sprite.center_x == i * 100 + 50
```

### Testing Boundary Interactions
```python
def test_boundary_with_group(self):
    sprite_group = SpriteGroup()
    # ... setup sprites near boundary ...
    
    bounce_called = False
    def on_bounce(sprite, axis):
        nonlocal bounce_called
        bounce_called = True
    
    bounds = lambda: (0, 0, 800, 600)
    bounce_action = BoundedMove(bounds, on_bounce=on_bounce)
    bounce_action.target = sprite_group
    bounce_action.start()
    
    move_action = MoveBy((200, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)
    bounce_action.update(1.0)
    
    assert bounce_called
```

### Testing Wrapping Interactions
```python
def test_wrapping_with_group(self):
    sprite_group = SpriteGroup()
    # ... setup sprites near screen edge ...
    
    wrap_called = False
    def on_wrap(sprite, axis):
        nonlocal wrap_called
        wrap_called = True
    
    bounds = lambda: (800, 600)  # width, height
    wrap_action = WrappedMove(bounds, on_wrap=on_wrap)
    wrap_action.target = sprite_group
    wrap_action.start()
    
    move_action = MoveBy((200, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)
    wrap_action.update(1.0)
    
    assert wrap_called
```

## Performance Considerations

1. **SpriteGroup vs SpriteList**: `SpriteGroup` extends `arcade.SpriteList`, so it has the same performance characteristics plus action management.

2. **GroupAction overhead**: Minimal - just coordinates individual actions.

3. **Boundary detection**: Only edge sprites are checked, making it efficient for large groups.

4. **Collision detection**: Uses Arcade's optimized collision detection under the hood.

## Summary

- **ActionSprite**: The foundation - only sprites that can use actions
- **SpriteGroup**: For coordinated group behavior with automatic management
- **GroupAction**: Created automatically, handles action coordination
- **BoundedMove + SpriteGroup**: Perfect for Space Invaders-style movement
- **WrappedMove + SpriteGroup**: Perfect for asteroid field-style movement
- **Collision detection**: Built into SpriteGroup with method chaining

Follow these patterns and your ArcadeActions code will be clean, efficient, and maintainable!

## Runtime-checking-free patterns

A common temptation is to write:

```python
# ❌ old – forbidden
if isinstance(action, MovementAction):
    dx, dy = action.delta
```

Now you **call the capability method directly**:

```python
# ✅ new – always available
if action.get_movement_delta() != (0, 0):
    dx, dy = action.get_movement_delta()
```

Key conventions:

1. **Capability hooks on `Action`.**
   – `get_movement_delta()` returns `(dx, dy)` or `(0, 0)`.
   – `adjust_for_position_delta(delta)` lets decorators (e.g. `WrappedMove`) tell inner actions about teleports.
2. **Iteration helpers.**  Instead of `isinstance(target, arcade.SpriteList)`, call `for sprite in self._iter_target():` in custom actions.
3. **Group detection.**  Check for the structural attribute `_group_actions` instead of type-checking `SpriteGroup`.
4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 