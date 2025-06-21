# ArcadeActions

A Python library that ports the Cocos2D Actions system to Arcade 3.x, providing a powerful and intuitive way to animate sprites with time-based actions.

## Features

- **Time-based animations**: Consistent behavior across different frame rates
- **Rich action library**: Move, rotate, scale, fade, and composite actions
- **Group actions**: Coordinate animations across multiple sprites
- **Boundary handling**: Built-in collision detection and boundary management
- **Easy integration**: Works seamlessly with existing Arcade projects

<img src="res/demo.gif" style="width: 500px">

## Installation

Install from PyPI using uv (recommended):

```bash
uv add arcade-actions
```

Or using pip:

```bash
pip install arcade-actions
```

## Quick Start

```python
import arcade
from actions import ActionSprite, MoveBy, RotateBy, Sequence

# Create an ActionSprite
player = ActionSprite(":resources:images/player.png")
player.center_x = 100
player.center_y = 100

# Create and apply actions
move_action = MoveBy((200, 0), 2.0)  # Move 200 pixels right over 2 seconds
rotate_action = RotateBy(360, 1.0)   # Rotate 360 degrees over 1 second

# Combine actions in sequence
combo_action = Sequence([move_action, rotate_action])
player.do(combo_action)

# In your game loop
def on_update(self, delta_time):
    player.update(delta_time)
```

## Documentation

- [API Usage Guide](docs/api_usage_guide.md) - Comprehensive guide to using the library
- [Game Loop Integration](docs/game_loop_updates.md) - How to integrate with your game loop
- [Boundary Events](docs/boundary_event.md) - Working with boundaries and collisions

## Examples

- `demo.py` - Complete demonstration of all available actions
- `examples/basic_usage.py` - Simple example showing core functionality
- `invaders.py` - Space Invaders-style game using the library

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/bcorfman/arcade_actions.git
cd arcade_actions

# Quick setup (automated)
python setup_dev.py

# Or manual setup:
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run the demo
uv run python examples/demo.py

# Run Actions version of Arcade's Slime Invaders example
uv run python examples/invaders.py
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

This library was developed using [Cursor IDE](https://www.cursor.com/) and [Claude 4 Sonnet](https://claude.ai) with me acting as Project Manager. 😎
