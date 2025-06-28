# ArcadeActions API Usage Guide

## Overview

ArcadeActions provides a conditional action system that works directly with Arcade's native sprites and sprite lists. The framework uses **condition-based actions** rather than duration-based ones, enabling more flexible and declarative game behaviors.

## Core Design Principles

### 1. Global Action Management
All actions are managed globally - no manual action tracking needed:

```python
from actions.base import Action
from actions.conditional import MoveUntil, duration

# Apply actions directly to any arcade.Sprite or arcade.SpriteList
action = MoveUntil((100, 0), duration(2.0))
action.apply(sprite, tag="movement")

# Global update handles everything
def update(self, delta_time):
    Action.update_all(delta_time)  # Updates all active actions
```

### 2. Condition-Based Actions
Actions run until conditions are met, not for fixed durations:

```python
# Velocity-based movement until condition is met
move_action = MoveUntil((50, -30), lambda: sprite.center_y < 100)
rotate_action = RotateUntil(90, lambda: sprite.angle >= 45)
fade_action = FadeUntil(-50, lambda: sprite.alpha <= 50)

# Apply directly to sprites
move_action.apply(sprite, tag="movement")
```

### 3. Operator-Based Composition
Use `+` for sequences and `|` for parallel actions:

```python
# Sequential actions
sequence = delay_action + move_action + fade_action

# Parallel actions  
parallel = move_action | rotate_action | fade_action

# Nested composition
complex = delay_action + (move_action | fade_action) + final_action
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

#### Boundary Actions (actions/move.py)
- **BoundedMove** - Bounce off boundaries with callbacks
- **WrappedMove** - Wrap around screen edges

#### High-Level Management (actions/pattern.py)
- **AttackGroup** - Game-oriented sprite group management
- **GridPattern** - Formation positioning patterns

## Usage Patterns

### Pattern 1: Individual Sprite Control
For player characters, single enemies, individual UI elements:

```python
import arcade
from actions.conditional import MoveUntil, RotateUntil, duration

# Create any arcade.Sprite
player = arcade.Sprite(":resources:images/player.png")

# Apply actions directly
move_action = MoveUntil((100, 0), duration(2.0))
move_action.apply(player, tag="movement")

# Combine with operators
dodge_sequence = move_action + RotateUntil(180, duration(0.5))
dodge_sequence.apply(player, tag="dodge")
```

### Pattern 2: Group Coordination
For enemy formations, bullet patterns, coordinated behaviors:

```python
# Create standard arcade.SpriteList
enemies = arcade.SpriteList()
for i in range(10):
    enemy = arcade.Sprite(":resources:images/enemy.png")
    enemies.append(enemy)

# Apply actions to entire group
formation_move = MoveUntil((0, -50), duration(3.0))
formation_move.apply(enemies, tag="formation")

# All sprites in the list move together
```

### Pattern 3: AttackGroup for Game Logic
For complex game scenarios with lifecycle management:

```python
from actions.pattern import AttackGroup, GridPattern
from actions.conditional import DelayUntil, MoveUntil, FadeUntil, RotateUntil

# Create AttackGroup for high-level management
enemies = arcade.SpriteList([enemy1, enemy2, enemy3])
formation = AttackGroup(enemies, name="wave_1", auto_destroy_when_empty=True)

# Apply formation patterns
grid_pattern = GridPattern(rows=2, cols=3, spacing_x=80, spacing_y=60)
grid_pattern.apply(formation, start_x=200, start_y=400)

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
formation.apply(sequential, tag="sequential")
formation.apply(parallel, tag="parallel") 
formation.apply(mixed, tag="mixed")
formation.apply(complex_nested, tag="complex")

# Action management and queries
all_active = formation.get_active_actions()
movement_active = formation.get_active_actions(tag="movement")

# Stop specific tagged actions
formation.stop_all_actions(tag="effects")  # Stop just effects
formation.stop_all_actions()               # Stop all actions

# Properties and state
print(f"Formation has {formation.sprite_count} sprites")
print(f"Formation is empty: {formation.is_empty}")
print(f"Formation destroyed: {formation.is_destroyed}")
```

### Pattern 4: Boundary Interactions
For arcade-style movement with boundary detection:

```python
from actions.move import BoundedMove

# Individual sprite bouncing
def on_bounce(sprite, axis):
    print(f"Sprite bounced on {axis} axis")

bounds = lambda: (0, 0, 800, 600)
bouncer = BoundedMove(bounds, on_bounce=on_bounce)
movement = MoveUntil((100, 50), lambda: False)  # Move indefinitely
bouncer.wrap_action(movement)
bouncer.apply(sprite, tag="bounce")

# Group bouncing (like Space Invaders)
formation = AttackGroup(enemies)
def formation_bounce(sprite, axis):
    if axis == 'x':
        # Move entire formation down
        down_action = MoveUntil((0, -30), duration(0.2))
        formation.apply(down_action, tag="drop")

group_bouncer = BoundedMove(bounds, on_bounce=formation_bounce)
group_movement = MoveUntil((100, 0), lambda: False)
group_bouncer.wrap_action(group_movement)
group_bouncer.apply(formation.sprites, tag="formation_bounce")
```

## Action Management

### Tags and Organization
Use tags to organize and control different types of actions:

```python
# Apply different tagged actions
movement_action.apply(sprite, tag="movement")
effect_action.apply(sprite, tag="effects")
combat_action.apply(sprite, tag="combat")

# Stop specific tagged actions
Action.stop(sprite, tag="effects")  # Stop just effects
Action.stop(sprite)  # Stop all actions on sprite
```

### Global Control
The global Action system provides centralized management:

```python
# Update all actions globally
Action.update_all(delta_time)

# Global action queries
active_count = Action.get_active_count()
movement_actions = Action.get_tag_actions("movement")

# Global cleanup
Action.clear_all()
```

## Complete Game Example

```python
import arcade
from actions.base import Action
from actions.conditional import MoveUntil, DelayUntil, duration
from actions.pattern import AttackGroup

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
        
        # Use AttackGroup for high-level management
        self.formation = AttackGroup(enemies, "invaders")
        
        # Set up formation movement pattern
        self._setup_formation_movement()
    
    def _setup_formation_movement(self):
        # Wait 2 seconds, then start moving
        delay = DelayUntil(duration(2.0))
        move_right = MoveUntil((50, 0), duration(4.0))
        
        # Use operators for clean composition
        sequence = delay + move_right
        self.formation.apply(sequence, tag="movement")
        
        # Set up boundary bouncing
        def on_formation_bounce(sprite, axis):
            # Move formation down and reverse direction
            if axis == 'x':
                drop = MoveUntil((0, -30), duration(0.3))
                self.formation.apply(drop, tag="drop")
        
        bounds = lambda: (50, 0, 750, 600)
        bouncer = BoundedMove(bounds, on_bounce=on_formation_bounce)
        formation_move = MoveUntil((50, 0), lambda: False)
        bouncer.wrap_action(formation_move)
        bouncer.apply(self.formation.sprites, tag="bounce")
    
    def on_update(self, delta_time):
        # Single global update handles all actions
        Action.update_all(delta_time)
```

## Best Practices

### 1. Prefer Conditions Over Durations
```python
# Good: Condition-based
move_until_edge = MoveUntil((100, 0), lambda: sprite.center_x > 700)

# Avoid: Duration-based thinking
# move_for_time = MoveBy((500, 0), 5.0)  # Old paradigm
```

### 2. Use Operators for Composition
```python
# Good: Clean operator syntax
complex_action = delay + (move | fade) + final_move

# Avoid: Verbose constructors
# complex_action = Sequence(delay, Spawn(move, fade), final_move)
```

### 3. Use AttackGroup for Game Logic
```python
# Good: High-level game management
formation = AttackGroup(enemies, auto_destroy_when_empty=True)
formation.apply(pattern, tag="attack")

# Avoid: Manual sprite list management
# Manual tracking of sprite lifecycles and cleanup
```

### 4. Tag Your Actions
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
| Game management | AttackGroup | `formation.apply(pattern, tag="attack")` |
| Boundary detection | BoundedMove wrapper | `bouncer.wrap_action(movement)` |
| Delayed execution | DelayUntil | `DelayUntil(condition) + action` |

The ArcadeActions framework provides a clean, declarative way to create complex game behaviors while leveraging Arcade's native sprite system!

## Runtime-checking-free patterns


Key conventions:

4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 
