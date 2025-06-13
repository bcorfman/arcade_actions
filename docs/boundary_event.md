# Arcade Actions: Boundary Event Callbacks

For movement actions that interact with screen boundaries, the system provides callback mechanisms to handle boundary events. This applies to both `BoundedMove` and `WrappedMove` in [actions/move.py](../actions/move.py).

## BoundedMove Callbacks

`BoundedMove` provides an `on_bounce` callback that is triggered when a sprite bounces off a boundary.

**Callback Signature:**
```python
def on_bounce(sprite: ActionSprite, axis: str) -> None:
    """Handle bounce events.
    
    Args:
        sprite: The sprite that bounced
        axis: 'x' for horizontal bounce, 'y' for vertical bounce
    """
    pass
```

**Example:**
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

**Example:**
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
