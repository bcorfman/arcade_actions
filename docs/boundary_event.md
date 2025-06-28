# Arcade Actions: Boundary Event Callbacks

For movement actions that interact with screen boundaries, the system provides callback mechanisms to handle boundary events. This applies to both `BoundedMove` and `WrappedMove` in [actions/move.py](../actions/move.py).

## BoundedMove Callbacks

`BoundedMove` provides an `on_bounce` callback that is triggered when a sprite bounces off a boundary. When used with `arcade.SpriteList`, only edge sprites trigger the callback, making it perfect for coordinated group behaviors like Space Invaders.

**Callback Signature:**
```python
def on_bounce(sprite: arcade.Sprite, axis: str) -> None:
    """Handle bounce events.
    
    Args:
        sprite: The sprite that bounced (edge sprite when used with groups)
        axis: 'x' for horizontal bounce, 'y' for vertical bounce
    """
    pass
```

### Individual Sprite Example

```python
import arcade
from actions.move import BoundedMove
from actions.conditional import MoveUntil

# Create sprite and movement action
player = arcade.Sprite(":resources:images/player.png")
player.center_x = 400
player.center_y = 300

# Define bounce callback
def on_player_bounce(sprite, axis):
    print(f"Player bounced on {axis} axis at ({sprite.center_x}, {sprite.center_y})")

# Create boundary bouncer
bounds = lambda: (50, 50, 750, 550)  # left, bottom, right, top
bouncer = BoundedMove(bounds, on_bounce=on_player_bounce)

# Create movement and wrap it with boundary detection
movement = MoveUntil((100, 50), lambda: False)  # Move indefinitely
bouncer.wrap_action(movement)

# Apply to sprite
bouncer.apply(player, tag="bounded_movement")
```

### Group Formation Example (Space Invaders Pattern)

```python
import arcade
from actions.move import BoundedMove
from actions.conditional import MoveUntil, duration
from actions.pattern import AttackGroup

# Create enemy formation
enemies = arcade.SpriteList()
for row in range(3):
    for col in range(8):
        enemy = arcade.Sprite(":resources:images/enemy.png")
        enemy.center_x = 100 + col * 60
        enemy.center_y = 500 - row * 50
        enemies.append(enemy)

formation = AttackGroup(enemies, name="invaders")

# Formation bounce callback
def on_formation_bounce(edge_sprite, axis):
    if axis == 'x':
        # Only horizontal bounces matter for formation
        print(f"Formation hit {axis} boundary, moving down")
        
        # Move entire formation down
        drop_action = MoveUntil((0, -40), duration(0.5))
        formation.apply(drop_action, tag="drop")
        
        # Reverse direction by stopping and restarting movement
        formation.stop_all_actions(tag="horizontal_movement")
        # New movement will start automatically

# Set up boundary detection
bounds = lambda: (100, 50, 700, 600)
bouncer = BoundedMove(bounds, on_bounce=on_formation_bounce)

# Create horizontal movement
horizontal_move = MoveUntil((50, 0), lambda: False)  # Move right indefinitely
bouncer.wrap_action(horizontal_move)

# Apply to formation
bouncer.apply(formation.sprites, tag="horizontal_movement")
```

## WrappedMove Callbacks

`WrappedMove` provides an `on_wrap` callback that is triggered when a sprite wraps around screen boundaries.

**Callback Signature:**
```python
def on_wrap(sprite: arcade.Sprite, axis: str) -> None:
    """Handle wrap events.
    
    Args:
        sprite: The sprite that wrapped around
        axis: 'x' for horizontal wrap, 'y' for vertical wrap
    """
    pass
```

### Individual Sprite Example

```python
import arcade
from actions.move import WrappedMove
from actions.conditional import MoveUntil

# Create asteroid sprite
asteroid = arcade.Sprite(":resources:images/asteroid.png")
asteroid.center_x = 0
asteroid.center_y = 300

# Define wrap callback
def on_asteroid_wrap(sprite, axis):
    print(f"Asteroid wrapped around {axis} axis")
    
    # Could trigger effects, spawn particles, etc.
    if axis == 'x':
        # Asteroid crossed screen horizontally
        spawn_trail_effect(sprite)

# Create screen wrapper
bounds = lambda: (0, 0, 800, 600)
wrapper = WrappedMove(bounds, on_wrap=on_asteroid_wrap)

# Create continuous movement
movement = MoveUntil((80, -20), lambda: False)  # Diagonal movement
wrapper.wrap_action(movement)

# Apply to sprite
wrapper.apply(asteroid, tag="wrapped_movement")
```

### Group Wrapping Example

```python
import arcade
from actions.move import WrappedMove
from actions.conditional import MoveUntil

# Create particle system
particles = arcade.SpriteList()
for i in range(10):
    particle = arcade.Sprite(":resources:images/particle.png")
    particle.center_x = random.randint(0, 800)
    particle.center_y = random.randint(0, 600)
    particles.append(particle)

# Group wrap callback
def on_particle_wrap(sprite, axis):
    # Reset particle properties when it wraps
    sprite.alpha = 255
    sprite.scale = random.uniform(0.5, 1.5)

# Set up wrapping
bounds = lambda: (0, 0, 800, 600)
wrapper = WrappedMove(bounds, on_wrap=on_particle_wrap)

# Create random movement for each particle
for particle in particles:
    velocity = (random.randint(-50, 50), random.randint(-50, 50))
    movement = MoveUntil(velocity, lambda: False)
    
    # Create individual wrapper for each particle
    particle_wrapper = WrappedMove(bounds, on_wrap=on_particle_wrap)
    particle_wrapper.wrap_action(movement)
    particle_wrapper.apply(particle, tag="particle_movement")
```

## Action Controller Pattern

Both `BoundedMove` and `WrappedMove` work as **action controllers** that modify the behavior of other movement actions:

1. **Create a movement action** (e.g., `MoveUntil`)
2. **Create a boundary action** (`BoundedMove` or `WrappedMove`)
3. **Wrap the movement** using `wrap_action(movement)`
4. **Apply the boundary action** to sprites using `apply()`

```python
# Pattern: Boundary Action Controller
movement_action = MoveUntil((velocity_x, velocity_y), condition)
boundary_action = BoundedMove(bounds, on_bounce=callback)
boundary_action.wrap_action(movement_action)
boundary_action.apply(sprite, tag="controlled_movement")
```

The boundary actions monitor sprite positions and automatically:
- **BoundedMove**: Reverses movement direction and adjusts position when boundaries are hit
- **WrappedMove**: Teleports sprites to opposite edges when they move off-screen

Both trigger their respective callbacks when boundary interactions occur, enabling game logic to respond to these events.

**Reference:**
- [actions/move.py](../actions/move.py)
- [actions/conditional.py](../actions/conditional.py)
- [API Usage Guide](api_usage_guide.md) - Complete patterns and examples