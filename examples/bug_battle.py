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
    arrange_grid,
    blink_until,
    create_formation_entry_from_sprites,
    infinite,
    move_until,
)

# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 1280
WINDOW_TITLE = "Bug Battle"

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
ENEMY_SCALE = 0.5
ENEMY_WIDTH = 128 * ENEMY_SCALE
ENEMY_HEIGHT = 128 * ENEMY_SCALE
LEFT_BOUND = 40
RIGHT_BOUND = WINDOW_WIDTH - 40
COOLDOWN_NORMAL = 30
COOLDOWN_POWERUP = 15
NORMAL = 0
DOUBLE_FIRE = 1
THREE_WAY = 2
SHIELD = 3
BOMB = 4


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


class Starfield:
    def __init__(self):
        """Populate sprite list with stars, and start actions."""
        self.star_list = arcade.SpriteList()

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

    def update(self):
        self.star_list.update()

    def draw(self):
        self.star_list.draw()

    def on_stars_wrap(self, sprite, axis):
        # When a star hits a vertical boundary, wrap it to the opposite side.
        # We check the direction of movement to decide which edge to wrap to.
        if sprite.change_y < 0:
            # Moving down, wrap to top
            sprite.position = (random.uniform(0, WINDOW_WIDTH), WINDOW_HEIGHT + VERTICAL_MARGIN)
        else:
            # Moving up, wrap to bottom
            sprite.position = (random.uniform(0, WINDOW_WIDTH), -VERTICAL_MARGIN)


class Powerup(arcade.Sprite):
    def __init__(self):
        self.gem_textures = [
            arcade.load_texture(":resources:/images/items/gemBlue.png"),
            arcade.load_texture(":resources:/images/items/gemGreen.png"),
            arcade.load_texture(":resources:/images/items/gemRed.png"),
            arcade.load_texture(":resources:/images/items/gemYellow.png"),
        ]
        self.texture_index = random.randint(0, 3)
        super().__init__(self.gem_textures[self.texture_index])
        self.textures = self.gem_textures
        self.center_x = random.uniform(LEFT_BOUND + self.width / 2, RIGHT_BOUND - self.width / 2)
        self.center_y = WINDOW_HEIGHT + 30
        arcade.schedule(self.update_animation, 1)

    def update_animation(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.texture_index = (self.texture_index + 1) % len(self.textures)
        self.texture = self.textures[self.texture_index]


class PlayerShip(arcade.Sprite):
    def __init__(self, shot_list):
        super().__init__(":resources:/images/space_shooter/playerShip1_green.png")
        self.center_x = WINDOW_WIDTH / 2
        self.center_y = 100
        self.current_powerup = 0
        self.cooldown_normal = 30
        self.cooldown_max = COOLDOWN_NORMAL
        self.fire_cooldown = self.cooldown_max
        self.shot_list = shot_list

    def fire_when_ready(self):
        if self.fire_cooldown == 0:
            self.fire_cooldown = self.cooldown_max
            shot = arcade.Sprite(":resources:/images/space_shooter/laserRed01.png")
            shot.center_x = self.center_x
            shot.center_y = self.center_y + 10

            move_until(
                shot,
                velocity=(0, PLAYER_SHIP_FIRE_SPEED),
                condition=lambda: shot.top > WINDOW_HEIGHT,
                on_stop=lambda: shot.remove_from_sprite_lists(),
            )
            self.shot_list.append(shot)
            self.fire_cooldown = self.cooldown_max
            return True
        return False

    def reset_cooldown(self, delta_time):
        self.cooldown_max = COOLDOWN_NORMAL
        self.player_fire_cooldown = self.cooldown_max

    def powerup_hit(self):
        self.current_powerup |= DOUBLE_FIRE
        self.cooldown_max = COOLDOWN_POWERUP
        self.player_fire_cooldown = self.cooldown_max
        arcade.unschedule(self.reset_cooldown)
        arcade.schedule_once(self.reset_cooldown, 5)

    def move(self, left_pressed, right_pressed):
        direction = 0
        if left_pressed and not right_pressed:
            direction = -PLAYER_SHIP_SPEED
        if right_pressed and not left_pressed:
            direction = PLAYER_SHIP_SPEED
        if direction != 0:
            Action.stop_actions_for_target(self, tag="player_move")
            move_until(
                self,
                velocity=(direction, 0),
                condition=infinite,
                bounds=(LEFT_BOUND + self.width / 2, 0, RIGHT_BOUND - self.width / 2, WINDOW_HEIGHT),
                boundary_behavior="limit",
                tag="player_move",
            )
        else:
            Action.stop_actions_for_target(self, tag="player_move")

    def update(self, delta_time):
        super().update(delta_time)
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------
class StarfieldView(arcade.View):
    """Simple starfield rendered using five independent sprite lists."""

    def __init__(self):
        super().__init__()

        self.enemy_formation = None
        self.powerup_list = arcade.SpriteList()
        self.shot_list = arcade.SpriteList()
        self.ship_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.starfield = Starfield()
        self._setup_ship()
        self._setup_enemies()
        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False
        self.background_color = arcade.color.BLACK
        arcade.schedule_once(self._spawn_powerup, random.gauss(20, 5))

    # ---------------------------------------------------------------------
    # Setup helpers
    # ---------------------------------------------------------------------

    def _setup_ship(self) -> None:
        """Create and position the ship sprite."""
        self.ship = PlayerShip(self.shot_list)
        self.ship_list.append(self.ship)

    def _setup_enemies(self) -> None:
        # Clear existing enemies
        self.enemy_list.clear()
        enemy_list = [
            ":resources:/images/enemies/bee.png",
            ":resources:/images/enemies/fishPink.png",
            ":resources:/images/enemies/fly.png",
            ":resources:/images/enemies/saw.png",
            ":resources:/images/enemies/slimeBlock.png",
            ":resources:/images/enemies/fishGreen.png",
        ]

        X_OFFSET = 120
        COLS = 4
        NUM_SPRITES = COLS - 1
        NUM_SPACES = NUM_SPRITES - 1
        self.enemy_formation: arcade.SpriteList = arrange_grid(
            sprites=[arcade.Sprite(random.choice(enemy_list), scale=0.5) for i in range(16)],
            rows=4,
            cols=4,
            start_x=X_OFFSET,
            start_y=WINDOW_HEIGHT - 400,
            spacing_x=(WINDOW_WIDTH - X_OFFSET * 2 - ENEMY_WIDTH * NUM_SPRITES) / NUM_SPACES,
            spacing_y=ENEMY_HEIGHT * 1.5,
            visible=False,
        )
        entry_actions = create_formation_entry_from_sprites(
            self.enemy_formation, speed=5.0, stagger_delay=1.2, min_spacing=50.0
        )
        for sprite, action in entry_actions:
            action.apply(sprite, tag="enemy_formation_entry")
            self.enemy_list.append(sprite)

    def _spawn_powerup(self):
        if len(self.powerup_list) == 0:
            powerup = Powerup()

            def powerup_collision_check():
                shots_colliding = arcade.check_for_collision_with_list(powerup, self.shot_list)
                offscreen = powerup.top < -30
                if shots_colliding or offscreen:
                    return {
                        "powerup_hit": shots_colliding,
                        "offscreen": offscreen,
                    }
                return None

            def handle_powerup_collision(collision_data):
                if collision_data["powerup_hit"]:
                    powerup.remove_from_sprite_lists()
                    shots_colliding = collision_data["powerup_hit"]
                    if shots_colliding:
                        for shot in shots_colliding:
                            shot.remove_from_sprite_lists()
                        self.ship.powerup_hit()
                if collision_data["offscreen"]:
                    powerup.remove_from_sprite_lists()

            self.powerup_list.append(powerup)
            move_until(
                self.powerup_list,
                velocity=(0, -5),
                condition=powerup_collision_check,
                on_stop=handle_powerup_collision,
            )

    # ---------------------------------------------------------------------
    # Arcade callbacks
    # ---------------------------------------------------------------------
    def on_update(self, delta_time: float):
        # Update all active actions first (updates velocities & wrapping).
        Action.update_all(delta_time)

        # Apply velocities to sprites.
        self.starfield.update()
        self.powerup_list.update()
        self.shot_list.update()
        self.ship_list.update()
        self.enemy_list.update()

        # Handle player input
        if self.fire_pressed:
            self.ship.fire_when_ready()
        self.ship.move(self.left_pressed, self.right_pressed)

        # Handle enemy-shot collisions
        self._handle_enemy_collisions()

    def _handle_enemy_collisions(self):
        """Handle collisions between player shots and enemies."""
        # Check collisions for all enemy groups
        for shot in self.shot_list:
            enemies_hit = arcade.check_for_collision_with_list(shot, self.enemy_list)
            if enemies_hit:
                # Remove the shot
                shot.remove_from_sprite_lists()

                # Remove hit enemies
                for enemy in enemies_hit:
                    enemy.remove_from_sprite_lists()
                break  # Shot can only hit one enemy, so break after first collision

        # Check if all enemies are defeated and restart formation
        if len(self.enemy_list) == 0:
            # Wait a moment before spawning new formation
            arcade.schedule_once(self._setup_enemies, 2.0)

    def on_draw(self):
        # Clear screen (preferred over arcade.start_render() inside a View).
        self.clear()
        self.starfield.draw()
        self.powerup_list.draw()
        self.shot_list.draw()
        self.ship_list.draw()
        self.enemy_list.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.LEFT:
            self.left_pressed = True
            self.right_pressed = False
        elif key == arcade.key.RIGHT:
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
