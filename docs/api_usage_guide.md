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

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### High-Level Management (actions/pattern.py)
- **Formation functions** - Grid, line, circle, and V-formation positioning patterns

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

### Pattern 3: Formation Management
For complex game scenarios with formation positioning:

```python
from actions.pattern import arrange_grid, arrange_circle
from actions.conditional import DelayUntil, MoveUntil, FadeUntil, RotateUntil

# Create a 3×5 enemy grid in one call using sprite_factory
from functools import partial

# Define how each enemy sprite should be built
enemy_factory = partial(arcade.Sprite, ":resources:images/enemy.png")

enemies = arrange_grid(
    rows=3,
    cols=5,
    start_x=200,
    start_y=400,
    spacing_x=80,
    spacing_y=60,
    sprite_factory=enemy_factory,
)

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

### Pattern 4: Boundary Interactions
For arcade-style movement with boundary detection:

```python
from actions.conditional import MoveUntil

# Individual sprite bouncing
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

### 3. Use Formation Functions for Positioning
```python
# Good: Formation positioning
from actions.pattern import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)

# Avoid: Manual sprite positioning
# Manual calculation of sprite positions
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
| Formation positioning | Pattern functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Boundary detection | MoveUntil with bounds | `MoveUntil(vel, cond, bounds=bounds, boundary_behavior="bounce")` |
| Delayed execution | DelayUntil | `DelayUntil(condition) + action` |

The ArcadeActions framework provides a clean, declarative way to create complex game behaviors while leveraging Arcade's native sprite system!

## Runtime-checking-free patterns


Key conventions:

4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 
