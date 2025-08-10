# ArcadeActions API Usage Guide

## Overview

ArcadeActions provides a conditional action system that works directly with Arcade's native sprites and sprite lists. The framework uses **condition-based actions** rather than duration-based ones, enabling more flexible and declarative game behaviors.

## Recommended Usage Patterns

### Pattern 1: Helper Functions for Simple, Immediate Actions

Helper functions like `move_until`, `rotate_until`, and `follow_path_until` are designed for simple, immediate application to sprites:

```python
from actions import move_until, rotate_until, duration

# Simple, immediate actions - this is what helper functions are for
move_until(player_sprite, velocity=(5, 0), condition=lambda: player_sprite.center_x > 800)
rotate_until(enemy_swarm, velocity=1.5, condition=duration(5.0))
```

### Pattern 2: Direct Classes with sequence() for Complex Compositions

For complex, multi-step sequences, use direct action classes with the `sequence()` and `parallel()` functions:

```python
from actions import Action, DelayUntil, FadeUntil, MoveUntil, RotateUntil, duration, sequence, parallel

# Complex sequences - use direct classes
complex_behavior = sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(100, 0), condition=duration(2.0)),
    parallel(
        RotateUntil(angular_velocity=180, condition=duration(1.0)),
        FadeUntil(fade_velocity=-50, condition=duration(1.5))
    )
)
complex_behavior.apply(sprite, tag="complex_movement")
```

### Why This Design?

**Helper functions** immediately apply actions when called, which conflicts with sequence construction. **Direct classes** create actions without applying them, allowing proper sequence composition.

```python
# ✅ CORRECT: Direct classes + sequence()
# This works perfectly because actions aren't applied until the sequence is
sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(5, 0), condition=duration(2.0))
).apply(sprite)

# ✅ ALSO CORRECT: Helper functions for immediate, simple actions
move_until(sprite, velocity=(5, 0), condition=duration(2.0))  # Applied immediately
```

## Core Design Principles

### 1. Velocity Semantics: Pixels Per Frame at 60 FPS
**CRITICAL:** ArcadeActions uses Arcade's native velocity semantics - values represent "pixels per frame at 60 FPS", NOT "pixels per second".

```python
# Correct: 5 means "5 pixels per frame" (equivalent to 300 pixels/second at 60 FPS)
move_action = MoveUntil(velocity=(5, 0), condition=cond)  # Moves 5 pixels per frame
rotate_action = RotateUntil(angular_velocity=3, condition=cond)   # Rotates 3 degrees per frame

# These values are applied directly to sprite.change_x, sprite.change_y, sprite.change_angle
# Arcade's internal update system handles the frame-rate timing
```

This maintains consistency with Arcade's native sprite system where `sprite.change_x = 5` moves the sprite 5 pixels per frame.

### 2. Global Action Management
All actions are managed globally - no manual action tracking needed:

```python
from actions import Action, duration, move_until

# Apply actions directly to any arcade.Sprite or arcade.SpriteList
move_until(sprite, velocity=(100, 0), condition=duration(2.0))

# Global update handles everything
def update(self, delta_time):
    Action.update_all(delta_time)  # Updates all active actions
```

### 3. Target Types: arcade.Sprite and arcade.SpriteList
All action functions accept either a single sprite or a sprite list as their target:

```python
# Single sprite target
player = arcade.Sprite(":resources:images/player.png")
move_until(player, velocity=(100, 0), condition=duration(2.0))

# Sprite list target (all sprites move together)
enemies = arcade.SpriteList()
for i in range(5):
    enemy = arcade.Sprite(":resources:images/enemy.png")
    enemies.append(enemy)
move_until(enemies, velocity=(0, -50), condition=duration(3.0))
```

### 4. Condition-Based Actions
Actions run until conditions are met, not for fixed durations:

```python
from actions import move_until, rotate_until, fade_until, follow_path_until

# Velocity-based movement until condition is met (pixels per frame at 60 FPS)
move_until(sprite, velocity=(5, -2), condition=lambda: sprite.center_y < 100)

# Path following with automatic rotation
path_points = [(100, 100), (200, 200), (300, 100)]
follow_path_until(
    sprite, path_points, velocity=2.5, condition=lambda: sprite.center_x > 400
)

rotate_until(sprite, angular_velocity=1.5, condition=lambda: sprite.angle >= 45)
fade_until(sprite, fade_velocity=-4, condition=lambda: sprite.alpha <= 50)
```

### 5. Clear Separation of Use Cases

| Use Case | Pattern | Example |
|----------|---------|---------|
| **Simple immediate actions** | Helper functions | `move_until(sprite, (5, 0), condition)` |
| **Complex sequences** | Direct classes + `sequence()` | `sequence(DelayUntil(...), MoveUntil(...))` |
| **Parallel effects** | Direct classes + `parallel()` | `parallel(MoveUntil(...), FadeUntil(...))` |

## Core Components

### Action Types

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement
- **FollowPathUntil** - Follow Bezier curve paths with optional sprite rotation to face movement direction
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes
- **FadeUntil** - Alpha velocity changes
- **DelayUntil** - Wait for condition
- **TweenUntil** - Direct property animation from start to end value

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Formation Management (actions/formation.py)
- **Formation functions** - Grid, line, circle, diamond, V-formation, triangle, hexagonal grid, arc, concentric rings, cross, and arrow positioning patterns

#### Movement Patterns (actions/pattern.py)
- **Movement pattern functions** - Zigzag, wave, spiral, figure-8, orbit, bounce, and patrol movement patterns
- **Condition helpers** - Time-based and sprite count conditions for use with conditional actions

#### Easing Effects (actions/easing.py)
- **Ease wrapper** - Apply smooth acceleration/deceleration curves to any conditional action
- **Built-in easing functions** - Use Arcade's ease_in, ease_out, ease_in_out curves
- **Custom easing support** - Create custom easing curves for specialized effects
- **Nested easing** - Combine multiple easing levels for complex animations
- **Completion callbacks** - Execute code when easing transitions complete

## Animation Approaches: Ease vs TweenUntil

ArcadeActions provides two distinct but complementary approaches for creating smooth animations. Understanding when to use each is crucial for effective game development.

### Ease: Smooth Transitions for Continuous Actions

**Purpose:** Ease wraps continuous actions (like `MoveUntil`, `FollowPathUntil`, `RotateUntil`) and modulates their intensity over time, creating smooth acceleration and deceleration effects.

**How it works:** The `ease()` helper function wraps an existing action and applies the eased effect to a target. After the easing duration completes, the wrapped action continues running at full intensity until its own condition is met.

**Key characteristics:**
- Wraps existing continuous actions
- Creates smooth start/stop transitions
- Wrapped action continues after easing completes
- Perfect for velocity-based animations
- Supports complex actions like curved path following

```python
from actions import ease, infinite, move_until, follow_path_until
from arcade import easing

# Example 1: Smooth missile launch
missile_movement = move_until(missile, velocity=(300, 0), condition=infinite)  # Continuous movement
ease(missile, missile_movement, duration=1.5, ease_function=easing.ease_out)

# Result: Missile smoothly accelerates to 300px/s over 1.5 seconds, then continues at that speed

# Example 2: Smooth curved path with rotation
path_points = [(100, 100), (200, 200), (400, 150), (500, 100)]
path_action = follow_path_until(
    enemy, path_points, velocity=250, condition=infinite
)
ease(enemy, path_action, duration=2.0, ease_function=easing.ease_in_out)
# Result: Enemy smoothly accelerates along curved path while rotating to face direction

# Example 3: Formation movement
formation_move = move_until(enemy_formation, velocity=(100, 0), condition=infinite)
ease(enemy_formation, formation_move, duration=1.0, ease_function=easing.ease_in)
# Result: Entire formation smoothly accelerates to marching speed
```

### TweenUntil: Direct Property Animation

**Purpose:** `tween_until` directly animates a specific sprite property from a start value to an end value over time, with optional easing curves for the interpolation itself.

**How it works:** Calculates intermediate values between start and end using linear interpolation and an optional easing function, then directly sets the property value each frame. The action completes when the end value is reached or the condition is met.

**Key characteristics:**
- Direct property manipulation (center_x, center_y, angle, scale, alpha, etc.)
- Precise A-to-B animations
- Built-in easing support for the interpolation curve
- Action completes when animation finishes
- Perfect for UI animations and precise movements

```python
from actions import duration,tween_until
from arcade import easing

# Example 1: UI panel slide-in
tween_until(ui_panel, start_value=-200, end_value=100, property_name="center_x", condition=duration(0.8), ease_function=easing.ease_out)
# Result: Panel slides from x=-200 to x=100 with smooth deceleration, then stops

# Example 2: Health bar animation
tween_until(health_bar, start_value=current_health, end_value=new_health, property_name="width", condition=duration(0.5))
# Result: Health bar width changes smoothly from current to new value

# Example 3: Button feedback animation
tween_until(button_sprite, start_value=1.0, end_value=1.2, property_name="scale", duration(0.1), ease_function=easing.ease_out)
# Result: Button scales from normal size to 120% over 0.1 seconds, then stops

# Example 4: Fade transition
tween_until(sprite, start_value=255, end_value=0, property_name="alpha", duration(1.0), ease_function=easing.ease_in)
# Result: Sprite fades from opaque to transparent over 1 second
```

### When to Use Which?

| Scenario | Choose | Reason |
|----------|--------|--------|
| **Missile/projectile launch** | `ease` | Need smooth acceleration to cruise speed, then constant velocity |
| **UI element slide-in** | `tween_until` | Need precise positioning from off-screen to final location |
| **Enemy formation movement** | `ease` | Formation should smoothly reach marching speed and continue |
| **Health/progress bar updates** | `tween_until` | Need exact value changes with smooth visual transition |
| **Curved path following** | `ease` | Complex path requires smooth acceleration along the curve |
| **Button press feedback** | `tween_until` | Need precise scale/position changes for UI responsiveness |
| **Vehicle acceleration** | `ease` | Realistic acceleration to top speed, then constant motion |
| **Fade in/out effects** | `tween_until` | Precise alpha value control with smooth transitions |
| **Camera smooth following** | `ease` | Smooth acceleration when starting to follow target |
| **Menu animations** | `tween_until` | Precise positioning and scaling for UI elements |

### Combining Both Approaches

You can use both techniques together for complex animations:

```python
# Sequential combination: precise positioning followed by smooth movement
from actions import TweenUntil, MoveUntil, duration, ease, sequence

def create_guard_behavior(guard_sprite):
    # Step 1: Precise positioning
    position_setup = TweenUntil(start_value=0, end_value=100, property_name="center_x", condition=duration(0.5))
    
    # Step 2: Smooth patrol movement  
    patrol_move = MoveUntil((50, 0), condition=infinite)
    
    # Create sequence
    behavior_sequence = sequence(position_setup, patrol_move)
    behavior_sequence.apply(guard_sprite, tag="guard_behavior")
    
    # Add easing to the patrol movement after positioning
    # Note: This requires more complex timing - simpler to use separate actions
    ease(guard_sprite, patrol_move, duration=1.0)
```

### Advanced Easing Patterns

```python
from actions import ease, fade_until, infinite, move_until, rotate_until
from arcade import easing

# Multiple concurrent eased effects
move_action = move_until(sprite, velocity=(200, 100), condition=infinite)
rotate_action = rotate_until(sprite, angular_velocity=360, condition=infinite)
fade_action = fade_until(sprite, fade_velocity=-100, condition=infinite)

# Apply different easing curves to each effect
ease(sprite, move_action, duration=2.0, ease_function=easing.ease_in_out)
ease(sprite, rotate_action, duration=1.5, ease_function=easing.ease_in)
ease(sprite, fade_action, duration=3.0, ease_function=easing.ease_out)
```

## Usage Patterns

### Pattern 1: Individual Sprite Control
For player characters, single enemies, individual UI elements:

```python
import arcade
from actions import duration, move_until, rotate_until

# Create any arcade.Sprite
player = arcade.Sprite(":resources:images/player.png")

# Apply simple actions directly using helper functions
move_until(player, velocity=(100, 0), condition=duration(2.0))
rotate_until(player, angular_velocity=180, condition=duration(0.5))
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
move_until(enemies, velocity=(0, -50), condition=duration(3.0))

# All sprites in the list move together
```

### Pattern 3: Complex Sequential Behaviors
For multi-step animations and complex game scenarios:

```python
from actions import Action, DelayUntil, MoveUntil, RotateUntil, FadeUntil, duration, sequence, parallel

# Create complex behavior using direct classes
def create_enemy_attack_sequence(enemy_sprite):
    attack_sequence = sequence(
        DelayUntil(duration(1.0)),                               # Wait 1 second
        MoveUntil(velocity=(0, -100), condition=duration(2.0)),  # Move down
        parallel(                                                # Simultaneously:
            RotateUntil(angular_velocity=360, condition=duration(1.0)),  #   Spin
            FadeUntil(fade_velocity=-50, condition=duration(1.5))  #   Fade out
        ),
        MoveUntil(velocity=(200, 0), condition=duration(1.0))  # Move sideways
    )
    attack_sequence.apply(enemy_sprite, tag="attack_sequence")

# Apply to multiple enemies
for enemy in enemy_list:
    create_enemy_attack_sequence(enemy)
```

### Pattern 4: Formation Management
For complex game scenarios with formation positioning:

```python
from actions import (
    arrange_grid, arrange_circle, arrange_diamond, arrange_triangle, 
    arrange_hexagonal_grid, arrange_arc, arrange_concentric_rings, 
    arrange_cross, arrange_arrow
)
from functools import partial

# Define how each enemy sprite should be built
enemy_factory = partial(arcade.Sprite, ":resources:images/enemy.png")

# Classic grid formation
enemies = arrange_grid(
    rows=3,
    cols=5,
    start_x=200,
    start_y=400,
    spacing_x=80,
    spacing_y=60,
    sprite_factory=enemy_factory,
)

# Triangle formation for attack patterns
attack_formation = arrange_triangle(
    count=10, apex_x=400, apex_y=500, row_spacing=50, lateral_spacing=60
)

# Hexagonal grid for defensive formations
defensive_grid = arrange_hexagonal_grid(
    rows=4, cols=6, start_x=100, start_y=400, spacing=50
)

# Arc formation for firing patterns
firing_arc = arrange_arc(
    count=8, center_x=400, center_y=300, radius=120, start_angle=45, end_angle=135
)

# Concentric rings for boss battle patterns
boss_pattern = arrange_concentric_rings(
    radii=[80, 140, 200], sprites_per_ring=[6, 12, 18], center_x=400, center_y=300
)

# Cross formation for power-ups or obstacles
power_up_cross = arrange_cross(
    count=9, center_x=400, center_y=300, arm_length=100, spacing=40
)

# Arrow formation for escort patterns
escort_arrow = arrange_arrow(
    count=7, tip_x=400, tip_y=500, rows=3, spacing_along=50, spacing_outward=40
)

# Apply simple movement to any formation
move_until(enemies, velocity=(0, -50), condition=duration(3.0), tag="formation_move")
```

### Pattern 5: Movement Patterns
For creating complex movement behaviors using pattern functions:

```python
from actions import (
    create_zigzag_pattern, create_wave_pattern, create_spiral_pattern,
    create_figure_eight_pattern, create_orbit_pattern, create_bounce_pattern,
    create_patrol_pattern, time_elapsed, sprite_count
)

# Enemy with zigzag attack pattern
zigzag_movement = create_zigzag_pattern(
    width=100, height=50, speed=150, segments=6
)
zigzag_movement.apply(enemy_sprite)

# Boss with smooth wave movement
wave_movement = create_wave_pattern(
    amplitude=75, frequency=2, length=600, speed=120
)
wave_movement.apply(boss_sprite)

# Enemy with repeating wave pattern (forward then backward)
from actions import repeat, sequence

forward_wave = create_wave_pattern(
    amplitude=15, frequency=1, length=50, speed=100, reverse=False
)
backward_wave = create_wave_pattern(
    amplitude=15, frequency=1, length=50, speed=100, reverse=True
)
repeating_wave = repeat(sequence(forward_wave, backward_wave))
repeating_wave.apply(enemy_sprite)

# Guard with patrol pattern
patrol_movement = create_patrol_pattern(
    start_pos=(100, 200), end_pos=(500, 200), speed=80
)
patrol_movement.apply(guard_sprite)
```

### Pattern 6: Path Following with Rotation
For smooth curved movement with automatic sprite rotation:

```python
from actions import duration, follow_path_until

# Basic path following without rotation
path_points = [(100, 100), (200, 150), (300, 100)]
follow_path_until(sprite, path_points, velocity=200, condition=duration(3.0))

# Path following with automatic rotation (sprite artwork points right)
follow_path_until(
    sprite, path_points, 
    velocity=200, 
    condition=duration(3.0),
    rotate_with_path=True,
)

# Path following with rotation offset for sprites pointing up
follow_path_until(
    sprite, path_points, 
    velocity=200, 
    condition=duration(3.0),
    rotate_with_path=True,
    rotation_offset=-90.0,  # Compensate for upward-pointing artwork
)

# Complex curved missile trajectory
missile_path = [(player.center_x, player.center_y),
                (target.center_x + 100, target.center_y + 50),  # Arc over target
                (target.center_x, target.center_y)]
follow_path_until(
    missile_sprite,
    missile_path, 
    velocity=300,
    condition=lambda: distance_to_target() < 20,  # Until close to target
    rotate_with_path=True,  # Missile points toward movement direction
)
```

### Pattern 7: Boundary Interactions
For arcade-style movement with boundary detection:

```python
from actions import duration, infinite, move_until

# Individual sprite bouncing
def on_bounce(sprite, axis):
    print(f"Sprite bounced on {axis} axis")

bounds = (0, 0, 800, 600)  # left, bottom, right, top
move_until(
    sprite,
    velocity=(100, 50),
    condition=infinite,  
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary=on_bounce,
)

# Group bouncing (like Space Invaders)
def formation_bounce(sprite, axis):
    if axis == 'x':
        # Move entire formation down
        move_until(enemies, (0, -30), duration(0.2))

move_until(
    enemies,
    velocity=(100, 0),
    condition=infinite,  
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary=formation_bounce,
    tag="formation_bounce"
)
```

## Easing Effects

### Overview
The `ease()` helper function provides smooth acceleration and deceleration effects by modulating the intensity of any conditional action using easing curves. This creates natural-feeling animations that start slow, speed up, and slow down again.

### Basic Easing Usage

```python
from actions import duration, ease, move_until
from arcade import easing

# Wrap any conditional action with easing
move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)

# The sprite will smoothly accelerate to full speed, then decelerate
```

### Easing Functions
Use Arcade's built-in easing functions for different effects:

```python
from arcade import easing
from actions import duration, ease, move_until

move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))

# Slow start, fast finish
ease(sprite, move, duration=2.0, ease_function=easing.ease_in)

# Fast start, slow finish  
ease(sprite, move, duration=2.0, ease_function=easing.ease_out)

# Slow start, fast middle, slow finish (default)
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)
```

### Easing with Path Following and Rotation
Create smooth curved movements with automatic sprite rotation:

```python
# Complex curved missile trajectory with easing
control_points = [(player.center_x, player.center_y),
                  (target.center_x + 100, target.center_y + 50),  # Arc over target
                  (target.center_x, target.center_y)]

missile_path = follow_path_until(
    missile_sprite,
    control_points, 
    velocity=300,
    condition=lambda: distance_to_target() < 20,
    rotate_with_path=True,  # Missile points toward movement direction
    rotation_offset=-90     # Compensate for upward-pointing artwork
)

# Add smooth acceleration/deceleration to the path following
ease(missile_sprite, missile_path, duration=1.5, ease_function=easing.ease_in_out)

# Missile will smoothly accelerate along the curved path while rotating to face direction
```

### Multiple Concurrent Eased Effects
Apply different easing to multiple effects simultaneously:

```python
from actions import ease, move_until, rotate_until, fade_until

# Create multiple effects with different easing curves
move = move_until(sprite, velocity=(200, 100), condition=infinite)
rotate = rotate_until(sprite, angular_velocity=360, condition=infinite)  # Full rotation
fade = fade_until(sprite, fade_velocity=-200, condition=infinite)     # Fade to transparent

# Apply different easing to each effect
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)
ease(sprite, rotate, duration=1.5, ease_function=easing.ease_in)
ease(sprite, fade, duration=3.0, ease_function=easing.ease_out)

# Sprite moves, rotates, and fades with different easing curves
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

move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))
ease(sprite, move, duration=2.0, ease_function=bounce_ease)
```

## Action Management

### Tags and Organization
Use tags to organize and control different types of actions:

```python
# Apply different tagged actions
move_until(sprite, velocity=(100, 0), condition=duration(2.0), tag="movement")
fade_until(sprite, velocity=-10, condition=duration(1.5), tag="effects")
rotate_until(sprite, velocity=180, condition=duration(1.0), tag="combat")

# Stop specific tagged actions
Action.stop_actions_for_target(sprite, "effects")  # Stop just effects
Action.stop_actions_for_target(sprite)  # Stop all actions on sprite
```

### Global Control
The global Action system provides centralized management:

```python
# Update all actions globally
Action.update_all(delta_time)

# Global action queries
active_count = len(Action._active_actions)
movement_actions = Action.get_actions_for_target(sprite, "movement")

# Global cleanup
Action.stop_all()
```

## Complete Game Example

```python
import arcade
from actions import Action, DelayUntil, MoveUntil, arrange_grid, duration, sequence

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
        # Create complex sequence using direct classes
        initial_sequence = sequence(
            DelayUntil(duration(2.0)),           # Wait 2 seconds
            MoveUntil(velocity=(50, 0), condition=duration(4.0))    # Move right
        )
        initial_sequence.apply(self.enemies, tag="initial_movement")
        
        # Set up boundary bouncing using helper function
        def on_formation_bounce(sprite, axis):
            # Move formation down and reverse direction
            if axis == 'x':
                move_until(self.enemies, velocity=(0, -30), condition=duration(0.3), tag="drop")
        
        bounds = (50, 0, 750, 600)  # left, bottom, right, top
        move_until(
            self.enemies,
            velocity=(50, 0), 
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary=on_formation_bounce,
        )
    
    def on_update(self, delta_time):
        # Single global update handles all actions
        Action.update_all(delta_time)
```

## Best Practices

### 1. Choose the Right Pattern for the Use Case
```python
# ✅ Good: Helper functions for simple, immediate actions
move_until(sprite, velocity=(100, 0), condition=duration(2.0))

# ✅ Good: Direct classes + sequence() for complex behaviors
complex_behavior = sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(100, 0), condition=duration(2.0)),
    RotateUntil(angular_velocity=180, condition=duration(1.0))
)
complex_behavior.apply(sprite)

# ❌ Avoid: Mixing helper functions with operators
# (delay_until(sprite, duration(1.0)) + move_until(sprite, (100, 0), duration(2.0)))
```

### 2. Prefer Conditions Over Durations
```python
# Good: Condition-based
move_until(sprite, velocity=(100, 0), condition=lambda: sprite.center_x > 700)

# Avoid: Duration-based thinking
# move_for_time = MoveBy((500, 0), 5.0)  # Old paradigm
```

### 3. Use Formation Functions for Positioning
```python
# Good: Formation positioning
from actions import arrange_grid
arrange_grid(enemies, rows=3, cols=5)

# Avoid: Manual sprite positioning
# Manual calculation of sprite positions
```

### 4. Tag Your Actions
```python
# Good: Organized with tags
move_until(sprite, velocity=(100, 0), condition=duration(2.0), tag="movement")
fade_until(sprite, velocity=-10, condition=duration(1.5), tag="effects")

# Stop specific systems
Action.stop_actions_for_target(sprite, tag="effects")
```

### 5. Choose the Right Animation Approach
```python
# Good: Use Easing for continuous actions
move_action = move_until(sprite, velocity=(200, 0), condition=infinite)
ease(sprite, move_action, duration=1.5)

# Good: Use TweenUntil for precise property changes
tween_until(sprite, start_value=0, end_value=100, property_name="center_x", condition=duration(1.0))

# Avoid: Using the wrong approach for the use case
# Don't use TweenUntil for complex path following
# Don't use Easing for simple A-to-B property changes
```

## Common Patterns Summary

| Use Case | Pattern | Example |
|----------|---------|---------|
| Simple sprite actions | Helper functions | `move_until(sprite, velociy=(5, 0), condition=cond)` |
| Sprite group actions | Helper functions on SpriteList | `move_until(sprite_list, velocity=(5, 0), condition=cond)` |
| Complex sequences | Direct classes + `sequence()` | `sequence(DelayUntil(...), MoveUntil(...))` |
| Parallel behaviors | Direct classes + `parallel()` | `parallel(MoveUntil(...), FadeUntil(...))` |
| Formation positioning | Formation functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Triangle formations | `arrange_triangle` | `arrange_triangle(count=10, apex_x=400, apex_y=500)` |
| Hexagonal grids | `arrange_hexagonal_grid` | `arrange_hexagonal_grid(rows=4, cols=6)` |
| Arc formations | `arrange_arc` | `arrange_arc(count=8, center_x=400, radius=120, start_angle=0, end_angle=180)` |
| Concentric patterns | `arrange_concentric_rings` | `arrange_concentric_rings(radii=[50, 100], sprites_per_ring=[6, 12])` |
| Cross patterns | `arrange_cross` | `arrange_cross(count=9, center_x=400, arm_length=100)` |
| Arrow formations | `arrange_arrow` | `arrange_arrow(count=7, tip_x=400, rows=3)` |
| Movement patterns | Pattern functions | `create_zigzag_pattern(100, 50, 150)` |
| Path following | `follow_path_until` helper | `follow_path_until(sprite, points, velocity=200, condition=cond)` |
| Boundary detection | `move_until` with bounds | `move_until(sprite, velocity=vel, condition=cond, bounds=b)` |
| Delayed execution | Direct classes in sequences | `sequence(DelayUntil(duration(1.0)), action)` |
| Smooth acceleration | `ease` helper | `ease(sprite, action, duration=2.0)` |
| Property animation | `tween_until` helper | `tween_until(sprite, start_val=start, end_val=end, "prop", duration(1.0))` |

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

move_until(bullet, velocity=(0, BULLET_SPEED), condition=bullet_collision_check, on_stop=handle_bullet_collision)
```

This pattern ensures collision checks are only performed once per frame, and all relevant data is passed directly to the handler—no need for extra state or repeated queries. This is the recommended approach for efficient, event-driven collision handling in ArcadeActions.

## Important Implementation Notes

### infinite() Function

**CRITICAL:** The `infinite()` function implementation in `actions/conditional.py` should never be modified. The current implementation (`return False`) is intentional and correct for the project's usage patterns. Do not suggest changing it to return `lambda: False` or any other callable. This function works correctly with the existing codebase and should not be modified.

### Velocity System Consistency

**CRITICAL:** MoveUntil ALWAYS uses `sprite.change_x` and `sprite.change_y` (Arcade's built-in velocity system). NEVER use `sprite.velocity` - that's not how MoveUntil works. Be consistent - don't switch back and forth between approaches.

### Condition Function Usage

**CRITICAL:** ALWAYS use `infinite` instead of `lambda: False` for infinite/never-ending conditions. This is the standard pattern in the codebase.
