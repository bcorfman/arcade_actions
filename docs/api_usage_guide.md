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
# Sequential actions
sequence = Sequence(delay_action, move_action, fade_action)

# Parallel actions  
parallel = Parallel(move_action, rotate_action, fade_action)

# Nested composition
complex = Sequence(delay_action, Parallel(move_action, fade_action), final_action)
```

## Core Components

### Action Types

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement
- **RotateUntil** - Angular velocity rotation  
- **ScaleUntil** - Scale velocity changes
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `+` operator)
- **Parallel actions** - Run actions in parallel (use `|` operator)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### High-Level Management (actions/pattern.py)
- **Formation functions** - Grid, line, circle, and V-formation positioning patterns

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

### Pattern 3: Formation Management
For complex game scenarios with formation positioning:

```python
from actions.pattern import arrange_grid, arrange_circle
from actions.conditional import DelayUntil, MoveUntil, FadeUntil, RotateUntil

# Create enemy formation using standard arcade.SpriteList
enemies = arcade.SpriteList([enemy1, enemy2, enemy3])

# Apply formation patterns
arrange_grid(enemies, rows=2, cols=3, start_x=200, start_y=400, spacing_x=80, spacing_y=60)

# Apply any actions using clean operators
delay = DelayUntil(duration(2.0))
move = MoveUntil((0, -50), duration(1.5))
fade = FadeUntil(-30, lambda: formation.sprite_count <= 2)

# Compose and apply
sequence = delay + move
parallel = move | fade
formation.apply(sequence, tag="initial")
formation.schedule(3.0, parallel, tag="retreat")

# Set up conditional breakaway behavior
def breakaway_condition():
    return any(sprite.center_y < 100 for sprite in enemies)

edge_sprites = [enemies[0], enemies[2]]  # Edge sprites break away first
formation.setup_conditional_breakaway(
    breakaway_condition, edge_sprites, tag="breakaway_monitor"
)

# Register lifecycle callbacks
def on_formation_destroyed(group):
    print(f"Formation {group.name} was destroyed!")

def on_sprites_break_away(new_group):
    print(f"Sprites broke away into {new_group.name}")
    # Apply different behavior to breakaway group
    panic_action = MoveUntil((200, -200), duration(0.5))
    new_group.apply(panic_action, tag="panic")

formation.on_destroy(on_formation_destroyed)
formation.on_breakaway(on_sprites_break_away)

# Advanced operator compositions
move_action = MoveUntil((50, 25), duration(2.0))
rotate_action = RotateUntil(360, duration(3.0))
scale_action = ScaleUntil(0.5, duration(1.5))

# Complex nested compositions
sequential = move_action + rotate_action + scale_action              # All sequential
parallel = move_action | rotate_action | scale_action                # All parallel
mixed = move_action + (rotate_action | scale_action)                 # Mixed composition
complex_nested = (move_action | rotate_action) + scale_action + (move_action | rotate_action)

# Apply different compositions with tags
sequential.apply(enemies, tag="sequential")
parallel.apply(enemies, tag="parallel") 
mixed.apply(enemies, tag="mixed")
complex_nested.apply(enemies, tag="complex")

# Action management and queries
all_active = Action.get_all_actions()
movement_active = Action.get_tag_actions("movement")

# Stop specific tagged actions
Action.stop_by_tag("effects")  # Stop just effects
Action.clear_all()             # Stop all actions

# Properties and state
print(f"Formation has {len(enemies)} sprites")
print(f"Formation is empty: {len(enemies) == 0}")
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
from actions.conditional import MoveUntil

### ❌ Don't: Directly manipulate sprite positions in groups
```python
# WRONG - Direct position manipulation bypasses the action system
def on_bounce(sprite, axis):
    print(f"Sprite bounced on {axis} axis")

bounds = (0, 0, 800, 600)  # left, bottom, right, top
movement = MoveUntil(
    (100, 50), 
    lambda: False,  # Move indefinitely
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary=on_bounce
)
movement.apply(sprite, tag="bounce")

# Group bouncing (like Space Invaders)
def formation_bounce(sprite, axis):
    if axis == 'x':
        # Move entire formation down
        down_action = MoveUntil((0, -30), duration(0.2))
        down_action.apply(enemies, tag="drop")

group_movement = MoveUntil(
    (100, 0), 
    lambda: False,
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary=formation_bounce
)
group_movement.apply(enemies, tag="formation_bounce")
```

## Action Management

### Tags and Organization
Use tags to organize and control different types of actions:

```python
from actions.group import SpriteGroup, GroupAction
from actions.interval import MoveBy

# GroupAction is created automatically
enemies = SpriteGroup([sprite1, sprite2, sprite3])
group_action = enemies.do(MoveBy((200, 0), 2.0))  # Returns GroupAction

# GroupAction implements the same interface as individual actions
assert not group_action.done  # Check completion status
group_action.pause()          # Pause all sprites in group
group_action.resume()         # Resume all sprites in group

# Batch optimization makes large groups efficient
large_group = SpriteGroup([create_sprite() for _ in range(100)])
large_group.do(MoveBy((50, 0), 1.0))  # Optimized for 100 sprites!
```

### 6. AttackGroup  
**When to use:** For complex game scenarios requiring lifecycle management, formations, and scheduled events.
**Key features:** Built on SpriteGroup with game-oriented additions.

```python
from actions.group import AttackGroup, SpriteGroup, GridPattern
from actions.interval import MoveBy

# Create an AttackGroup for complex enemy behavior
enemies = SpriteGroup([create_enemy() for _ in range(12)])
formation = AttackGroup(enemies, name="wave_1")

# Apply formation patterns
pattern = GridPattern(rows=3, cols=4, spacing_x=80, spacing_y=60)
pattern.apply(formation, start_x=200, start_y=400)

# Schedule delayed attacks
formation.schedule_attack(2.0, formation.do, MoveBy((100, -50), 1.5))
formation.schedule_attack(5.0, formation.do, MoveBy((-200, 0), 2.0))

# Handle breakaway scenarios
def create_breakaway():
    # Some sprites break away to form new attack pattern
    breakaway_sprites = list(formation.sprites)[:3]
    new_formation = formation.breakaway(breakaway_sprites)
    new_formation.do(MoveBy((0, -100), 1.0))

formation.schedule_attack(3.0, create_breakaway)

# Update in game loop (handles all scheduled events)
formation.update(delta_time)
```

### 7. Formation Patterns
**When to use:** For organizing sprites into recognizable formations.
**Key principle:** Separate positioning logic from movement logic.

```python
import arcade
from actions.base import Action
from actions.conditional import MoveUntil, DelayUntil, duration
from actions.pattern import arrange_grid

class SpaceInvadersGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Space Invaders")
        
        # Create enemy formation
        enemies = arcade.SpriteList()
        for row in range(5):
            for col in range(10):
                enemy = arcade.Sprite(":resources:images/enemy.png")
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 40
                enemies.append(enemy)
        
        # Store enemies for management
        self.enemies = enemies
        
        # Set up formation movement pattern
        self._setup_formation_movement()
    
    def _setup_formation_movement(self):
        # Wait 2 seconds, then start moving
        delay = DelayUntil(duration(2.0))
        move_right = MoveUntil((50, 0), duration(4.0))
        
        # Use operators for clean composition
        sequence = delay + move_right
        sequence.apply(self.enemies, tag="movement")
        
        # Set up boundary bouncing
        def on_formation_bounce(sprite, axis):
            # Move formation down and reverse direction
            if axis == 'x':
                drop = MoveUntil((0, -30), duration(0.3))
                drop.apply(self.enemies, tag="drop")
        
        bounds = (50, 0, 750, 600)  # left, bottom, right, top
        formation_move = MoveUntil(
            (50, 0), 
            lambda: False,
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary=on_formation_bounce
        )
        formation_move.apply(self.enemies, tag="bounce")
    
    def on_update(self, delta_time):
        # Single global update handles all actions
        Action.update_all(delta_time)
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

### 3. Use Formation Functions for Positioning
```python
# Good: Formation positioning
from actions.pattern import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)

# Avoid: Manual sprite positioning
# Manual calculation of sprite positions
```

### Testing Collision Detection
```python
# Good: Organized with tags
movement.apply(sprite, tag="movement")
effects.apply(sprite, tag="effects")

# Stop specific systems
Action.stop(sprite, tag="effects")
```

## Common Patterns Summary

| Use Case | Pattern | Example |
|----------|---------|---------|
| Single sprite | Direct action application | `action.apply(sprite, tag="move")` |
| Sprite group | Action on SpriteList | `action.apply(sprite_list, tag="formation")` |
| Sequential behavior | `+` operator | `action1 + action2 + action3` |
| Parallel behavior | `\|` operator | `move \| rotate \| fade` |
| Formation positioning | Pattern functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Boundary detection | MoveUntil with bounds | `MoveUntil(vel, cond, bounds=bounds, boundary_behavior="bounce")` |
| Delayed execution | DelayUntil | `DelayUntil(condition) + action` |

The ArcadeActions framework provides a clean, declarative way to create complex game behaviors while leveraging Arcade's native sprite system!

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