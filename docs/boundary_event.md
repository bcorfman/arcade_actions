# Arcade Actions: Boundary Event Callbacks

For movement actions that interact with screen boundaries, the system provides callback mechanisms to handle boundary events. This applies to both `BoundedMove` and `WrappedMove` in [actions/move.py](../actions/move.py).

## BoundedMove Callbacks

`BoundedMove` provides an `on_bounce` callback that is triggered when a sprite bounces off a boundary. When used with `SpriteGroup`, only edge sprites trigger the callback, making it perfect for coordinated group behaviors like Space Invaders.

**Callback Signature:**
```python
def on_bounce(sprite: ActionSprite, axis: str) -> None:
    """Handle bounce events.
    
    Args:
        sprite: The sprite that bounced (edge sprite when used with SpriteGroup)
        axis: 'x' for horizontal bounce, 'y' for vertical bounce
    """
    pass
```

### Individual Sprite Example
```python
from actions.interval import MoveBy
from actions.move import BoundedMove

def handle_bounce(sprite, axis):
    if axis == 'x':
        print(f"Sprite {sprite} bounced horizontally!")
    else:
        print(f"Sprite {sprite} bounced vertically!")

# Create movement and boundary actions
move_action = MoveBy((200, 0), 2.0)  # Move right over 2 seconds
bounce_action = BoundedMove(
    lambda: (0, 0, 800, 600),  # left, bottom, right, top
    on_bounce=handle_bounce
)

# Combine actions and apply to sprite
sprite.do(move_action | bounce_action)
```

### SpriteGroup Example (Space Invaders Pattern)
```python
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import BoundedMove

def setup_space_invaders_movement():
    # Create enemy formation
    enemies = SpriteGroup()
    for row in range(5):
        for col in range(10):
            enemy = ActionSprite(":resources:images/enemy.png")
            enemy.center_x = 100 + col * 60
            enemy.center_y = 500 - row * 50
            enemies.append(enemy)
    
    # Define movement boundaries
    def get_bounds():
        return (50, 0, 750, 600)  # left, bottom, right, top
    
    # Callback for coordinated group behavior
    def on_edge_bounce(sprite, axis):
        if axis == 'x':
            # Only edge sprites trigger this callback
            # Move ALL enemies down using GroupAction
            move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
            enemies.do(move_down)
            
            # Clear current actions and start new movement
            enemies.clear_actions()
            start_horizontal_movement()
    
    def start_horizontal_movement():
        # Move across screen
        move_action = MoveBy((400, 0), 4.0)
        enemies.do(move_action)  # GroupAction coordinates all sprites
    
    # Set up boundary detection for the entire group
    boundary_action = BoundedMove(get_bounds, on_bounce=on_edge_bounce)
    boundary_action.target = enemies  # Apply to entire SpriteGroup
    boundary_action.start()
    
    # Start initial movement
    start_horizontal_movement()
    
    return enemies, boundary_action

# In game loop
enemies, boundary_action = setup_space_invaders_movement()

def update(delta_time):
    enemies.update(delta_time)      # Automatically updates GroupActions
    boundary_action.update(delta_time)  # Updates boundary detection
```

### Key Features with SpriteGroup

1. **Edge Detection**: Only leftmost/rightmost sprites (horizontal) or top/bottom sprites (vertical) trigger callbacks
2. **Coordinated Behavior**: Callback can affect the entire group, not just the bouncing sprite
3. **Automatic Management**: `SpriteGroup` handles GroupAction lifecycle automatically
4. **Spacing Preservation**: Enhanced algorithm prevents spacing drift during bounces

## WrappedMove Callbacks

`WrappedMove` provides an `on_wrap` callback that is triggered when a sprite wraps around screen boundaries.

**Callback Signature:**
```python
def on_wrap(sprite: ActionSprite, axis: str) -> None:
    """Handle wrap events.
    
    Args:
        sprite: The sprite that wrapped
        axis: 'x' for horizontal wrap, 'y' for vertical wrap
    """
    pass
```

### Individual Sprite Example
```python
from actions.interval import MoveBy
from actions.move import WrappedMove

def handle_wrap(sprite, axis):
    if axis == 'x':
        print(f"Sprite {sprite} wrapped horizontally!")
    else:
        print(f"Sprite {sprite} wrapped vertically!")

# Create movement and wrapping actions
move_action = MoveBy((200, 0), 2.0)  # Move right over 2 seconds
wrap_action = WrappedMove(
    lambda: (800, 600),  # width, height
    on_wrap=handle_wrap
)

# Combine actions and apply to sprite
sprite.do(move_action | wrap_action)
```

### SpriteGroup Example (Asteroid Field Pattern)
```python
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import WrappedMove

def setup_asteroid_field():
    # Create asteroid field
    asteroids = SpriteGroup()
    for i in range(8):
        asteroid = ActionSprite(":resources:images/asteroid.png")
        asteroid.center_x = 100 + i * 80
        asteroid.center_y = 300
        asteroids.append(asteroid)
    
    # Define screen bounds
    def get_bounds():
        return (800, 600)  # width, height
    
    # Callback for coordinated group behavior
    def on_edge_wrap(sprite, axis):
        if axis == 'x':
            # Only edge sprites trigger this callback
            # Coordinate new movement pattern for entire field
            asteroids.clear_actions()
            
            # Start new diagonal movement pattern
            new_move = MoveBy((-300, 50), 3.0)  # Move left and slightly up
            asteroids.do(new_move)
    
    # Set up wrapping for the entire group
    wrap_action = WrappedMove(get_bounds, on_wrap=on_edge_wrap)
    wrap_action.target = asteroids  # Apply to entire SpriteGroup
    wrap_action.start()
    
    # Start initial movement
    move_action = MoveBy((300, 0), 3.0)  # Move right
    asteroids.do(move_action)
    
    return asteroids, wrap_action

# In game loop
asteroids, wrap_action = setup_asteroid_field()

def update(delta_time):
    asteroids.update(delta_time)    # Automatically updates GroupActions
    wrap_action.update(delta_time)  # Updates wrapping detection
```

### Key Features with SpriteGroup

1. **Edge Detection**: Only leftmost/rightmost sprites (horizontal) or top/bottom sprites (vertical) trigger callbacks
2. **Coordinated Behavior**: Callback can affect the entire group, not just the wrapping sprite
3. **Automatic Management**: `SpriteGroup` handles GroupAction lifecycle automatically
4. **Position Coordination**: Enhanced algorithm allows for group-wide position management

## Action Controller Pattern

Both `BoundedMove` and `WrappedMove` work as **action controllers** that modify the behavior of other movement actions:

1. **Create a movement action** (e.g., `MoveBy`, `MoveTo`, or eased movements)
2. **Create a boundary action** (`BoundedMove` or `WrappedMove`)
3. **Combine them** using the `|` operator to run in parallel
4. **Apply to sprite** using `sprite.do(combined_action)`

The boundary actions monitor sprite positions and automatically:
- **BoundedMove**: Reverses movement direction and adjusts position when boundaries are hit
- **WrappedMove**: Teleports sprites to opposite edges when they move off-screen

**Reference:**
- [actions/move.py](../actions/move.py)
- [actions/interval.py](../actions/interval.py)
