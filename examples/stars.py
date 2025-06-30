"""
Starfield demo showcasing ArcadeActions MoveUntil with wrapping boundaries.

Five layers of stars scroll downward at different speeds to create a simple
parallax effect:
    • Darkest (farthest) stars scroll the slowest.
    • Brightest (nearest) stars scroll the fastest.

Press ESC at any time to exit the application.

This example intentionally keeps the implementation minimal while still
following the project design guidelines (see docs/api_usage_guide.md).
"""

from __future__ import annotations

import random

import arcade

from actions.base import Action
from actions.conditional import BlinkUntil, MoveUntil

# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 1280
WINDOW_TITLE = "ArcadeActions Starfield"

# ---------------------------------------------------------------------------
# Starfield configuration
# ---------------------------------------------------------------------------
# Number of stars per layer. Feel free to tweak for denser / sparser fields.
MAX_STARS: int = 400
# A small margin lets us spawn stars just outside the visible area so they
# don't wrap immediately when the demo starts.
VERTICAL_MARGIN: int = 5

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _random_star_position() -> tuple[float, float]:
    """Return a random (x, y) position slightly above the top of the screen."""
    x = random.uniform(0, WINDOW_WIDTH)
    y = random.uniform(0, WINDOW_HEIGHT) + 5
    return x, y


def _create_star_sprite(color: arcade.Color, size: int = 2) -> arcade.Sprite:
    """Create a tiny square sprite representing a single star."""
    sprite = arcade.SpriteSolidColor(size, size, color=color)
    sprite.center_x, sprite.center_y = _random_star_position()
    return sprite


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------
class StarfieldView(arcade.View):
    """Simple starfield rendered using five independent sprite lists."""

    def __init__(self):
        super().__init__()

        self.star_list = arcade.SpriteList()
        self._setup_star_layers()

        # A solid black background keeps the focus on the starfield.
        self.background_color = arcade.color.BLACK

    # ---------------------------------------------------------------------
    # Setup helpers
    # ---------------------------------------------------------------------
    def on_wrap(self, sprite, axis):
        sprite.position = (random.uniform(0, WINDOW_WIDTH), WINDOW_HEIGHT + 5)

    def _setup_star_layers(self) -> None:
        """Create sprite lists, populate them with stars, and start actions."""
        bounds = (0, -VERTICAL_MARGIN, WINDOW_WIDTH, WINDOW_HEIGHT + VERTICAL_MARGIN)

        for _ in range(MAX_STARS):
            color = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
            star = _create_star_sprite(color, size=3)
            self.star_list.append(star)

            blink_action = BlinkUntil(random.randint(200, 400) / 1000.0, lambda: False)
            blink_action.apply(star)
        # Move downward indefinitely; wrap from bottom back to the top.
        move_action = MoveUntil(
            (0, -4),
            lambda: False,  # Run forever
            bounds=bounds,
            boundary_behavior="wrap",
            on_boundary=self.on_wrap,
        )
        move_action.apply(self.star_list)

    # ---------------------------------------------------------------------
    # Arcade callbacks
    # ---------------------------------------------------------------------
    def on_update(self, delta_time: float):
        # Update all active actions first (updates velocities & wrapping).
        Action.update_all(delta_time)

        # Apply velocities to sprites.
        self.star_list.update()

    def on_draw(self):
        # Clear screen (preferred over arcade.start_render() inside a View).
        self.clear()

        self.star_list.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ESCAPE:
            # Close the whole application immediately.
            self.window.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.show_view(StarfieldView())
    arcade.run()


if __name__ == "__main__":
    main()
