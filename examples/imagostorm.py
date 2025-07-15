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
    blink_until,
    infinite,
    move_until,
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
# Ship configuration
# ---------------------------------------------------------------------------
PLAYER_SHIP_SPEED = 5
PLAYER_SHIP_FIRE_SPEED = 20
PLAYER_SHIP_LEFT_BOUND = 50
PLAYER_SHIP_RIGHT_BOUND = WINDOW_WIDTH - 50
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

        self.shot_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.star_list = arcade.SpriteList()
        self.cooldown_max = 30
        self.player_fire_cooldown = self.cooldown_max
        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False
        self._setup_stars()
        self._setup_ship()

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
            blink_until(star, random.randint(200, 400) / 1000.0, condition=infinite)
            self.star_list.append(star)

        move_until(
            self.star_list,
            velocity=(0, -4),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="wrap",
            on_boundary=self.on_stars_wrap,
        )

    def _setup_ship(self) -> None:
        """Create and position the ship sprite."""
        self.ship = arcade.Sprite(":resources:/images/space_shooter/playerShip1_green.png")
        self.ship.center_x = WINDOW_WIDTH / 2
        self.ship.center_y = 100
        self.player_list.append(self.ship)

    def _fire_bullet_if_ready(self) -> None:
        if self.player_fire_cooldown == 0 and self.fire_pressed:
            shot = arcade.Sprite(":resources:/images/space_shooter/laserRed01.png")
            shot.center_x = self.ship.center_x
            shot.center_y = self.ship.center_y + 10

            move_until(
                shot,
                velocity=(0, PLAYER_SHIP_FIRE_SPEED),
                condition=lambda: shot.top > WINDOW_HEIGHT,
                on_stop=lambda: shot.remove_from_sprite_lists(),
            )
            self.shot_list.append(shot)
            self.player_fire_cooldown = self.cooldown_max

    # ---------------------------------------------------------------------
    # Arcade callbacks
    # ---------------------------------------------------------------------
    def on_update(self, delta_time: float):
        # Update all active actions first (updates velocities & wrapping).
        Action.update_all(delta_time)

        # Apply velocities to sprites.
        self.star_list.update()
        self.player_list.update()
        self.shot_list.update()

        if self.player_fire_cooldown > 0:
            self.player_fire_cooldown -= 1
        self.update_player_speed()
        self._fire_bullet_if_ready()

    def on_draw(self):
        # Clear screen (preferred over arcade.start_render() inside a View).
        self.clear()
        self.star_list.draw()
        self.player_list.draw()
        self.shot_list.draw()

    def update_player_speed(self):
        direction = 0
        if self.left_pressed and not self.right_pressed:
            direction = -PLAYER_SHIP_SPEED
        if self.right_pressed and not self.left_pressed:
            direction = PLAYER_SHIP_SPEED
        if direction != 0:
            Action.stop_actions_for_target(self.ship, tag="player_move")
            move_until(
                self.ship,
                velocity=(direction, 0),
                condition=lambda: self.ship.left < PLAYER_SHIP_LEFT_BOUND or self.ship.right > PLAYER_SHIP_RIGHT_BOUND,
                tag="player_move",
            )
        else:
            Action.stop_actions_for_target(self.ship, tag="player_move")

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.LEFT:
            print("left pressed")
            self.left_pressed = True
            self.right_pressed = False
        elif key == arcade.key.RIGHT:
            print("right pressed")
            self.right_pressed = True
            self.left_pressed = False
        if key == arcade.key.LCTRL or modifiers == arcade.key.MOD_CTRL:
            self.fire_pressed = True
        if key == arcade.key.ESCAPE:
            self.window.close()

    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        if key == arcade.key.LCTRL:
            self.fire_pressed = False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.show_view(StarfieldView())
    arcade.run()


if __name__ == "__main__":
    main()
