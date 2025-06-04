# Arcade Actions: Boundary Event Enum

For movement actions that interact with screen boundaries, the system uses a `Boundary` enum to represent which edge(s) were crossed. This applies to both `BoundedMove` and `WrappedMove` in [arcade/actions/move.py](mdc:arcade/actions/move.py).

**Enum Definition:**
```python
from enum import Enum, auto

class Boundary(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()
```

**Callback Usage:**
- Both `BoundedMove` and `WrappedMove` accept an `on_boundary_hit` callback parameter.
- The callback is called as `on_boundary_hit(sprite, boundaries, *args, **kwargs)`, where `boundaries` is a list of `Boundary` enum values (e.g., `[Boundary.TOP, Boundary.LEFT]` for a corner).

**Example:**
```python
def boundary_event(sprite, boundaries):
    if Boundary.TOP in boundaries:
        print(\"Sprite hit the top!\")
    print(f\"Boundaries crossed: {boundaries}\")

move = BoundedMove(800, 600, on_boundary_hit=boundary_event)
```
**Reference:**
- [arcade/actions/move.py](mdc:arcade/actions/move.py)
