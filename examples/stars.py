"""
Starfield demo showcasing ArcadeActions MoveUntil with wrapping boundaries.

This was intentionally built to resemble the starfield in Galaga.

Press ESC at any time to exit the application.

This example intentionally keeps the implementation minimal while still
following the project design guidelines (see docs/api_usage_guide.md).
"""

from __future__ import annotations

import random

import arcade

from actions import (
    Action,
    BlinkUntil,
    DelayUntil,
    MoveUntil,
    TweenUntil,
    duration,
    infinite,
    repeat,
    sequence,
)

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
        self._setup_stars()

        # A solid black background keeps the focus on the starfield.
        self.background_color = arcade.color.BLACK

    # ---------------------------------------------------------------------
    # Setup helpers
    # ---------------------------------------------------------------------
    def on_stars_wrap(self, sprite, axis):
        # When a star hits a vertical boundary, wrap it to the opposite side.
        # We check the direction of movement to decide which edge to wrap to.
        if sprite.change_y < 0:
            # Moving down, wrap to top
            sprite.position = (random.uniform(0, WINDOW_WIDTH), WINDOW_HEIGHT + VERTICAL_MARGIN)
        else:
            # Moving up, wrap to bottom
            sprite.position = (random.uniform(0, WINDOW_WIDTH), -VERTICAL_MARGIN)

    def _setup_stars(self) -> None:
        """Populate sprite list with stars, and start actions."""
        bounds = (0, -VERTICAL_MARGIN, WINDOW_WIDTH, WINDOW_HEIGHT + VERTICAL_MARGIN)

        for _ in range(MAX_STARS):
            color = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
            star = _create_star_sprite(color, size=3)
            self.star_list.append(star)

            blink_action = BlinkUntil(random.randint(200, 400) / 1000.0, lambda: False)
            blink_action.apply(star)

        # Action 1: A permanent action that handles boundary checking and wrapping.
        # It has zero velocity so it only enforces the rules, it doesn't cause movement.
        wrapping_action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="wrap",
            on_boundary=self.on_stars_wrap,
        )
        wrapping_action.apply(self.star_list)

        # Action 2: The main animation loop using repeat action.
        # The sequence of actions that control the starfield's velocity.
        # Uses TweenUntil to directly set velocity values (change_y property)
        # This is correct because we need precise velocity transitions, not smooth
        # acceleration into continuous movement (which would use Ease wrapper)
        control_sequence = repeat(
            sequence(
                # 1. Start at 0 speed for 1 second.
                DelayUntil(duration(1.0)),
                # 2. Accelerate to forward speed (-4) over 2 seconds.
                TweenUntil(
                    start_value=0,
                    end_value=-4,
                    property_name="change_y",
                    condition=duration(2.0),
                    ease_function=arcade.easing.ease_in,
                ),
                # 3. Hold forward speed for 5 seconds.
                DelayUntil(duration(5.0)),
                # 4. Accelerate to reverse speed (14, which is 3.5x forward) over 0.5s.
                TweenUntil(
                    start_value=-4,
                    end_value=14,
                    property_name="change_y",
                    condition=duration(0.5),
                    ease_function=arcade.easing.ease_out,
                ),
                # 5. Hold reverse speed for 1.5 seconds.
                DelayUntil(duration(1.5)),
                # 6. Decelerate from reverse speed back to 0 over 2 seconds.
                #    When this action completes, it will trigger the callback to loop.
                TweenUntil(
                    start_value=14,
                    end_value=0,
                    property_name="change_y",
                    condition=duration(2.0),
                    ease_function=arcade.easing.ease_out,
                ),
            )
        )
        control_sequence.apply(self.star_list)

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
