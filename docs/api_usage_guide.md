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

# Path following with automatic rotation
path_points = [(100, 100), (200, 200), (300, 100)]
path_action = FollowPathUntil(
    path_points, 150, lambda: sprite.center_x > 400,
    rotate_with_path=True, rotation_offset=-90  # Sprite artwork points up
)

rotate_action = RotateUntil(90, lambda: sprite.angle >= 45)
fade_action = FadeUntil(-50, lambda: sprite.alpha <= 50)

# Apply directly to sprites
move_action.apply(sprite, tag="movement")
path_action.apply(sprite, tag="path_following")
```

### 3. Function-Based Composition
Use `sequence()` and `parallel()` helper functions for composition:

```python
from actions.composite import sequence, parallel

# Sequential actions
seq = sequence(delay_action, move_action, fade_action)

# Parallel actions  
par = parallel(move_action, rotate_action, fade_action)

# Nested composition
complex = sequence(delay_action, parallel(move_action, fade_action), final_action)
```

## Core Components

### Action Types

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement
- **FollowPathUntil** - Follow Bezier curve paths with optional sprite rotation to face movement direction
- **RotateUntil** - Angular velocity rotation  
- **ScaleUntil** - Scale velocity changes
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### High-Level Management (actions/pattern.py)
- **Formation functions** - Grid, line, circle, and V-formation positioning patterns

#### Easing Effects (actions/easing.py)
- **Easing wrapper** - Apply smooth acceleration/deceleration curves to any conditional action
- **Built-in easing functions** - Use Arcade's ease_in, ease_out, ease_in_out curves
- **Custom easing support** - Create custom easing curves for specialized effects
- **Nested easing** - Combine multiple easing levels for complex animations
- **Completion callbacks** - Execute code when easing transitions complete

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

# Combine with helper functions
from actions.composite import sequence

dodge_sequence = sequence(move_action, RotateUntil(180, duration(0.5)))
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

# Apply any actions using clean helper functions
from actions.composite import sequence, parallel

delay = DelayUntil(duration(2.0))
move = MoveUntil((0, -50), duration(1.5))
fade = FadeUntil(-30, lambda: formation.sprite_count <= 2)

# Compose and apply
seq = sequence(delay, move)
par = parallel(move, fade)
formation.apply(seq, tag="initial")
formation.schedule(3.0, par, tag="retreat")

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

# Advanced function compositions
move_action = MoveUntil((50, 25), duration(2.0))
rotate_action = RotateUntil(360, duration(3.0))
scale_action = ScaleUntil(0.5, duration(1.5))

# Complex nested compositions
sequential = sequence(move_action, rotate_action, scale_action)              # All sequential
par = parallel(move_action, rotate_action, scale_action)                # All parallel
mixed = sequence(move_action, parallel(rotate_action, scale_action))                 # Mixed composition
complex_nested = sequence(parallel(move_action, rotate_action), scale_action, parallel(move_action, rotate_action))

# Apply different compositions with tags
sequential.apply(enemies, tag="sequential")
par.apply(enemies, tag="parallel") 
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

### Pattern 4: Path Following with Rotation
For smooth curved movement with automatic sprite rotation:

```python
from actions.conditional import FollowPathUntil, duration

# Basic path following without rotation
path_points = [(100, 100), (200, 150), (300, 100)]
basic_path = FollowPathUntil(path_points, 200, duration(3.0))
basic_path.apply(sprite, tag="movement")

# Path following with automatic rotation (sprite artwork points right)
rotating_path = FollowPathUntil(
    path_points, 200, duration(3.0),
    rotate_with_path=True
)
rotating_path.apply(sprite, tag="rotating_movement")

# Path following with rotation offset for sprites pointing up
upward_sprite_path = FollowPathUntil(
    path_points, 200, duration(3.0),
    rotate_with_path=True,
    rotation_offset=-90.0  # Compensate for upward-pointing artwork
)
upward_sprite_path.apply(sprite, tag="calibrated_movement")

# Complex curved missile trajectory
missile_path = [(player.center_x, player.center_y),
                (target.center_x + 100, target.center_y + 50),  # Arc over target
                (target.center_x, target.center_y)]
missile_action = FollowPathUntil(
    missile_path, 300, 
    lambda: distance_to_target() < 20,  # Until close to target
    rotate_with_path=True  # Missile points toward movement direction
)
missile_action.apply(missile_sprite, tag="homing")
```

### Pattern 5: Boundary Interactions
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

## Easing Effects

### Overview
The Easing wrapper provides smooth acceleration and deceleration effects by modulating the intensity of any conditional action using easing curves. This creates natural-feeling animations that start slow, speed up, and slow down again.

### Basic Easing Usage

```python
from actions.easing import Easing
from arcade import easing

# Wrap any conditional action with easing
move = MoveUntil((200, 0), duration(3.0))
eased_move = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)
eased_move.apply(sprite, tag="smooth_movement")

# The sprite will smoothly accelerate to full speed, then decelerate
```

### Easing Functions
Use Arcade's built-in easing functions for different effects:

```python
from arcade import easing

# Slow start, fast finish
ease_in_move = Easing(move, seconds=2.0, ease_function=easing.ease_in)

# Fast start, slow finish  
ease_out_move = Easing(move, seconds=2.0, ease_function=easing.ease_out)

# Slow start, fast middle, slow finish (default)
ease_in_out_move = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)
```

### Easing with Path Following and Rotation
Create smooth curved movements with automatic sprite rotation:

```python
# Complex curved missile trajectory with easing
control_points = [(player.center_x, player.center_y),
                  (target.center_x + 100, target.center_y + 50),  # Arc over target
                  (target.center_x, target.center_y)]

missile_path = FollowPathUntil(
    control_points, 300, 
    lambda: distance_to_target() < 20,
    rotate_with_path=True,  # Missile points toward movement direction
    rotation_offset=-90     # Compensate for upward-pointing artwork
)

# Add smooth acceleration/deceleration to the path following
eased_missile = Easing(missile_path, seconds=1.5, ease_function=easing.ease_in_out)
eased_missile.apply(missile_sprite, tag="homing_missile")

# Missile will smoothly accelerate along the curved path while rotating to face direction
```

### Multiple Concurrent Eased Effects
Apply different easing to multiple effects simultaneously:

```python
# Create multiple effects with different easing curves
move = MoveUntil((200, 100), lambda: False)
rotate = RotateUntil(360, lambda: False)  # Full rotation
fade = FadeUntil(-200, lambda: False)     # Fade to transparent

# Apply different easing to each effect
eased_move = Easing(move, seconds=2.0, ease_function=easing.ease_in_out)
eased_rotate = Easing(rotate, seconds=1.5, ease_function=easing.ease_in)
eased_fade = Easing(fade, seconds=3.0, ease_function=easing.ease_out)

# Apply all effects to the same sprite
eased_move.apply(sprite, tag="movement")
eased_rotate.apply(sprite, tag="rotation")
eased_fade.apply(sprite, tag="fade")

# Sprite moves, rotates, and fades with different easing curves
```

### Nested Easing for Complex Effects
Combine multiple levels of easing for sophisticated animations:

```python
# Base movement action
move = MoveUntil((300, 0), lambda: False)

# First level of easing (slow acceleration)
inner_easing = Easing(move, seconds=1.0, ease_function=easing.ease_in)

# Second level of easing (slow overall progression)
outer_easing = Easing(inner_easing, seconds=3.0, ease_function=easing.ease_out)
outer_easing.apply(sprite, tag="complex_movement")

# Creates compound easing effect with very gradual buildup
```

### Easing with Completion Callbacks
Execute code when easing completes:

```python
def on_movement_complete():
    print("Smooth movement finished!")
    # Start next phase of animation
    next_action.apply(sprite, tag="next_phase")

eased_action = Easing(
    move, 
    seconds=2.0, 
    ease_function=easing.ease_in_out,
    on_complete=on_movement_complete
)
eased_action.apply(sprite, tag="phased_movement")
```

### Custom Easing Functions
Create your own easing curves:

```python
def bounce_ease(t):
    """Custom bouncing ease function."""
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t

custom_eased = Easing(move, seconds=2.0, ease_function=bounce_ease)
custom_eased.apply(sprite, tag="bouncy_movement")
```

### Easing Best Practices

1. **Match Easing to Context**: Use `ease_in` for dramatic reveals, `ease_out` for natural stops, `ease_in_out` for smooth general movement

2. **Layer Different Durations**: Apply easing with different durations to create complex, layered animations

3. **Combine with Formation Management**: Use easing on formation movements for cinematic effects

```python
# Smooth formation movement with easing
formation_move = MoveUntil((0, -100), duration(3.0))
eased_formation = Easing(formation_move, seconds=2.0, ease_function=easing.ease_in_out)
eased_formation.apply(enemies, tag="formation_descent")
```

4. **Test Edge Cases**: Handle extreme values gracefully:

```python
# Very fast easing for instant effects
instant_ease = Easing(action, seconds=0.001)

# Very slow easing for background ambience
ambient_ease = Easing(action, seconds=30.0)
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
        
        # Use helper functions for clean composition
        from actions.composite import sequence
        
        seq = sequence(delay, move_right)
        seq.apply(self.enemies, tag="movement")
        
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

### 2. Use Helper Functions for Composition
```python
from actions.composite import sequence, parallel

# Good: Clean helper function syntax
complex_action = sequence(delay, parallel(move, fade), final_move)

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
| Sequential behavior | `sequence()` | `sequence(action1, action2, action3)` |
| Parallel behavior | `parallel()` | `parallel(move, rotate, fade)` |
| Formation positioning | Pattern functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Path following | FollowPathUntil | `FollowPathUntil(points, 200, condition, rotate_with_path=True)` |
| Boundary detection | MoveUntil with bounds | `MoveUntil(vel, cond, bounds=bounds, boundary_behavior="bounce")` |
| Delayed execution | DelayUntil | `DelayUntil(condition) + action` |
| Smooth acceleration | Easing wrapper | `Easing(action, seconds=2.0, ease_function=easing.ease_in_out)` |
| Complex curved movement | Easing + FollowPathUntil | `Easing(FollowPathUntil(points, vel, cond, rotate_with_path=True), seconds=1.5)` |
| Multiple eased effects | Concurrent Easing | `Easing(move, 2.0, ease_in), Easing(fade, 3.0, ease_out)` |

The ArcadeActions framework provides a clean, declarative way to create complex game behaviors while leveraging Arcade's native sprite system!

## Runtime-checking-free patterns


Key conventions:

4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 

### MoveUntil with Collision Detection and Data Passing

You can use MoveUntil for much more than just position checks. The condition function can return any data when a stop condition is met, and this data will be passed to the callback for efficient, zero-duplication event handling. This is especially powerful for collision detection:

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

This pattern ensures collision checks are only performed once per frame, and all relevant data is passed directly to the handler—no need for extra state or repeated queries. This is the recommended approach for efficient, event-driven collision handling in ArcadeActions.
