# ArcadeActions

A Python library that ports the Cocos2D Actions system to Arcade 3.x, providing a powerful and intuitive way to animate sprites.

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
from actions import MoveUntil, RotateUntil, Action, duration

# Create a standard arcade sprite
player = arcade.Sprite(":resources:images/player.png")
player.center_x = 100
player.center_y = 100

# Create and apply actions
move_action = MoveUntil((100, 0), duration(2.0))  # Move 100 px/sec for 2 seconds
rotate_action = RotateUntil(180, duration(1.0))   # Rotate 180 deg/sec for 1 second

# Combine actions in sequence using operator
combo_action = move_action + rotate_action
combo_action.apply(player, tag="combo")

# In your game loop
def on_update(self, delta_time):
    Action.update_all(delta_time)  # Updates all active actions globally
```

## Documentation

- [API Usage Guide](docs/api_usage_guide.md) - Comprehensive guide to using the library
- [Game Loop Integration](docs/game_loop_updates.md) - How to integrate with your game loop

## Examples

- `examples/invaders.py` - Space Invaders-style game using the library

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

# Run Actions version of Arcade's Slime Invaders example
uv run python examples/invaders.py
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

This library was developed using [Cursor IDE](https://www.cursor.com/) and [Claude 4 Sonnet](https://claude.ai) with me acting as Project Manager. 😎