# Arcade Actions: Boundary Event Callbacks

For movement actions that interact with screen boundaries, the system provides callback mechanisms to handle boundary events. This applies to both `BoundedMove` and `WrappedMove` in [actions/move.py](../actions/move.py).

## BoundedMove Callbacks

`BoundedMove` provides an `on_bounce` callback that is triggered when a sprite bounces off a boundary. When used with `SpriteList`, only edge sprites trigger the callback, making it perfect for coordinated group behaviors like Space Invaders.

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


## WrappedMove Callbacks

`WrappedMove` provides an `on_wrap` callback that is triggered when a sprite wraps around screen boundaries.


### Individual Sprite Example


## Action Controller Pattern

Both `BoundedMove` and `WrappedMove` work as **action controllers** that modify the behavior of other movement actions:

1. **Create a movement action** (e.g., `MoveUntil` or `MoveWhile`)
2. **Create a boundary action** (`BoundedMove` or `WrappedMove`) that contains the movement action
...

The boundary actions monitor sprite positions and automatically:
- **BoundedMove**: Reverses movement direction and adjusts position when boundaries are hit
- **WrappedMove**: Teleports sprites to opposite edges when they move off-screen

**Reference:**
- [actions/move.py](../actions/move.py)
- [actions/conditional.py](../actions/conditional.py)
