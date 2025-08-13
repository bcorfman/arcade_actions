"""
Starfield demo showcasing ArcadeActions MoveUntil with wrapping boundaries.

This was intentionally built to resemble the starfield in Galaga.

Press ESC at any time to exit the application.

This example intentionally keeps the implementation minimal while still
following the project design guidelines (see docs/api_usage_guide.md).
"""

from __future__ import annotations

import math
import random

import arcade

from actions import (
    Action,
    DelayUntil,
    MoveBy,
    arrange_grid,
    blink_until,
    create_formation_entry_from_sprites,
    create_wave_pattern,
    infinite,
    move_until,
    repeat,
    sequence,
)

# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 720
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
DOUBLE_FIRE = 0
THREE_WAY = 1
SHIELD = 2
BOMB = 3

# Grid configuration
ENEMY_GRID_MARGIN = 80.0  # Desired left and right margin for enemy grid

# Powerup constants
POWERUP_SPAWN_INTERVAL = 10.0
POWERUP_SPAWN_VARIANCE = 5.0

# Sprite constants
PLAYER_SHIP = ":resources:/images/space_shooter/playerShip1_green.png"
PLAYER_SHOT = ":resources:/images/space_shooter/laserRed01.png"
BEE = ":resources:/images/enemies/bee.png"
FISH_PINK = ":resources:/images/enemies/fishPink.png"
FISH_GREEN = ":resources:/images/enemies/fishGreen.png"
FLY = ":resources:/images/enemies/fly.png"
SAW = ":resources:/images/enemies/saw.png"
SLIME_BLOCK = ":resources:/images/enemies/slimeBlock.png"
GEM_GREEN = ":resources:/images/items/gemGreen.png"
GEM_RED = ":resources:/images/items/gemRed.png"
GEM_YELLOW = ":resources:/images/items/gemYellow.png"
GEM_BLUE = ":resources:/images/items/gemBlue.png"
EXPLOSION_TEXTURE_COUNT = 60


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
            blink_until(star, seconds_until_change=random.randint(200, 400) / 1000.0, condition=infinite)
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
            arcade.load_texture(GEM_BLUE),
            arcade.load_texture(GEM_GREEN),
            arcade.load_texture(GEM_RED),
            arcade.load_texture(GEM_YELLOW),
        ]
        self.texture_index = random.randint(0, 3)
        super().__init__(self.gem_textures[self.texture_index])
        self.textures = self.gem_textures
        self.center_x = random.uniform(LEFT_BOUND + self.width / 2, RIGHT_BOUND - self.width / 2)
        self.center_y = WINDOW_HEIGHT + 30
        # update the powerup animation/type every second
        arcade.schedule(self.update_animation, 1)

    def update_animation(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.texture_index = (self.texture_index + 1) % len(self.textures)
        self.texture = self.textures[self.texture_index]


class Explosion(arcade.Sprite):
    """This class creates an explosion animation"""

    # Class variable to store shared textures
    _texture_list = None

    @classmethod
    def _load_textures(cls):
        """Load the explosion textures from spritesheet (done only once)"""
        if cls._texture_list is None:
            # Load the explosion from a sprite sheet
            columns = 16
            count = 60
            sprite_width = 256
            sprite_height = 256
            file_name = ":resources:images/spritesheets/explosion.png"

            # Load the explosions from a sprite sheet
            spritesheet = arcade.load_spritesheet(file_name)
            cls._texture_list = spritesheet.get_texture_grid(
                size=(sprite_width, sprite_height),
                columns=columns,
                count=count,
            )

    def __init__(self):
        # Ensure textures are loaded
        self._load_textures()

        # Initialize with first texture
        super().__init__(self._texture_list[0])

        # How long the explosion has been around
        self.time_elapsed = 0

        # Start at the first frame
        self.current_texture = 0
        self.textures = self._texture_list

    def update(self, delta_time=1 / 60):
        self.time_elapsed += delta_time
        # Update to the next frame of the animation. If we are at the end
        # of our frames, then delete this sprite.
        self.current_texture = int(self.time_elapsed * 60)
        if self.current_texture < len(self.textures):
            self.set_texture(self.current_texture)
        else:
            self.remove_from_sprite_lists()


class PlayerShip(arcade.Sprite):
    def __init__(self, shot_list):
        super().__init__(PLAYER_SHIP)
        self.center_x = WINDOW_WIDTH / 2
        self.center_y = 100
        self.current_powerup = None
        self.cooldown_normal = 30
        self.cooldown_max = COOLDOWN_NORMAL
        self.fire_cooldown = self.cooldown_max
        self.shot_list = shot_list

    def fire_when_ready(self):
        can_fire = self.fire_cooldown == 0
        if can_fire:
            self.setup_shot()
            if self.current_powerup == THREE_WAY:
                self.setup_shot(-10)
                self.setup_shot(10)
            self.fire_cooldown = self.cooldown_max
        return can_fire

    def setup_shot(self, angle=0):
        shot = arcade.Sprite(PLAYER_SHOT)
        shot.center_x = self.center_x
        shot.center_y = self.center_y + 10
        if angle == 0:
            shot_vel_x = 0
            shot_vel_y = PLAYER_SHIP_FIRE_SPEED
        else:
            shot.angle = angle
            angle_rad = math.radians(angle)
            shot_vel_x = PLAYER_SHIP_FIRE_SPEED * math.sin(angle_rad)
            shot_vel_y = PLAYER_SHIP_FIRE_SPEED * math.cos(angle_rad)

        move_until(
            shot,
            velocity=(shot_vel_x, shot_vel_y),
            condition=lambda: shot.top > WINDOW_HEIGHT,
            on_stop=lambda: shot.remove_from_sprite_lists(),
        )
        self.shot_list.append(shot)

    def reset_cooldown(self, delta_time):
        self.current_powerup = None
        self.cooldown_max = COOLDOWN_NORMAL
        self.player_fire_cooldown = self.cooldown_max

    def powerup_hit(self):
        self.cooldown_max = COOLDOWN_POWERUP
        self.player_fire_cooldown = self.cooldown_max
        arcade.unschedule(self.reset_cooldown)
        arcade.schedule_once(self.reset_cooldown, COOLDOWN_POWERUP)

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
        self._setup_enemies(0)
        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False
        self.background_color = arcade.color.BLACK
        arcade.schedule_once(self._spawn_powerup, random.gauss(POWERUP_SPAWN_INTERVAL, POWERUP_SPAWN_VARIANCE))

    # ---------------------------------------------------------------------
    # Setup helpers
    # ---------------------------------------------------------------------

    def _setup_ship(self) -> None:
        """Create and position the ship sprite."""
        self.ship = PlayerShip(self.shot_list)
        self.ship_list.append(self.ship)

    def _setup_enemies(self, delta_time) -> None:
        # Clear existing enemies
        self.enemy_list.clear()
        enemy_list = [BEE, FISH_PINK, FLY, SAW, SLIME_BLOCK, FISH_GREEN]

        # Calculate centered grid layout using the new function
        start_x, spacing_x = get_centered_grid_spacing(ENEMY_GRID_MARGIN)

        # Create the target formation sprites (these define the final positions)
        target_sprites = [arcade.Sprite(random.choice(enemy_list), scale=0.5) for i in range(16)]
        self.enemy_formation: arcade.SpriteList = arrange_grid(
            sprites=target_sprites,
            rows=4,
            cols=4,
            start_x=start_x,  # Use calculated centered position
            start_y=WINDOW_HEIGHT - 400,
            spacing_x=spacing_x,  # Use calculated spacing
            spacing_y=ENEMY_HEIGHT * 1.5,
            visible=False,
        )

        # Create the entry pattern - this returns new sprites with actions
        entry_actions = create_formation_entry_from_sprites(
            self.enemy_formation,
            speed=5.0,
            stagger_delay=0.5,
            window_bounds=(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
        )

        # Apply actions to the new sprites and add them to the enemy list
        for sprite, action, _ in entry_actions:
            action.apply(sprite, tag="enemy_formation_entry")
            self.enemy_list.append(sprite)

        # Create a DelayUntil action that waits for all formation entry actions to complete,
        # then starts a wave pattern motion for the entire enemy formation
        def all_enemies_arrived() -> bool:
            """Return True after the entire grid has been motionless for ~0.5 s."""

            # Thresholds
            vel_eps = 0.05  # pixels / frame considered stationary
            stable_frames_required = 30  # ≈0.5 s at 60 FPS

            moving = any(abs(s.change_x) > vel_eps or abs(s.change_y) > vel_eps for s in self.enemy_list)

            if moving:
                all_enemies_arrived._stable = 0  # reset counter
                return False

            # All sprites stationary this frame → increment stability counter
            all_enemies_arrived._stable = getattr(all_enemies_arrived, "_stable", 0) + 1
            return all_enemies_arrived._stable >= stable_frames_required

        def start_wave_motion():
            """Start repeating wave motion for the entire enemy formation."""
            AMP = 30  # desired half-wave dip depth

            move_by = MoveBy(-AMP, AMP)
            single_wave = create_wave_pattern(
                amplitude=AMP,
                length=100,
                speed=150.0,
            )

            # Repeat the wave forever so enemies keep swaying
            repeating_wave = sequence(move_by, repeat(single_wave))

            # Apply to the whole enemy list (grid moves as one unit)
            repeating_wave.apply(self.enemy_list, tag="enemy_wave")

        # Create and apply the DelayUntil action
        delay_action = DelayUntil(condition=all_enemies_arrived, on_stop=start_wave_motion)

        # Apply the delay action to any sprite (it just waits, doesn't move anything)
        # We'll use the first enemy sprite as the target, but it could be any sprite
        if self.enemy_list:
            delay_action.apply(self.enemy_list[0], tag="formation_completion_watcher")

    def _spawn_powerup(self, delta_time):
        if len(self.powerup_list) == 0:
            powerup = Powerup()

            def powerup_condition():
                shots_colliding = arcade.check_for_collision_with_list(powerup, self.shot_list)
                offscreen = powerup.top < -30
                if shots_colliding or offscreen:
                    return {
                        "powerup_hit": shots_colliding,
                        "offscreen": offscreen,
                    }
                return None

            def handle_powerup(collision_data):
                if collision_data["powerup_hit"]:
                    self.ship.current_powerup = powerup.texture_index
                    powerup.remove_from_sprite_lists()
                    shots_colliding = collision_data["powerup_hit"]
                    if shots_colliding:
                        for shot in shots_colliding:
                            shot.remove_from_sprite_lists()
                        self.ship.powerup_hit()
                if collision_data["offscreen"]:
                    powerup.remove_from_sprite_lists()
                arcade.schedule_once(self._spawn_powerup, random.gauss(POWERUP_SPAWN_INTERVAL, POWERUP_SPAWN_VARIANCE))

            self.powerup_list.append(powerup)
            move_until(
                self.powerup_list,
                velocity=(0, -5),
                condition=powerup_condition,
                on_stop=handle_powerup,
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


def calculate_centered_grid_layout(
    window_width: float, cols: int, sprite_width: float, desired_margin: float = 0.0
) -> tuple[float, float]:
    """Calculate start_x and spacing_x to center a grid with specified margins.
    Args:
        window_width: Total window width
        cols: Number of columns in the grid
        sprite_width: Width of each sprite
        desired_margin: Desired left and right margin (default: 0.0 for auto-centering)
    Returns:
        Tuple of (start_x, spacing_x) for centered grid
    """
    if desired_margin > 0:
        # Calculate spacing needed to achieve equal margins
        # The grid spans from left_margin to (window_width - right_margin)
        # where left_margin = right_margin = desired_margin

        # The leftmost sprite center is at: desired_margin + sprite_width/2
        # The rightmost sprite center is at: window_width - desired_margin - sprite_width/2

        # Total distance between centers = rightmost_center - leftmost_center
        leftmost_center = desired_margin + sprite_width / 2
        rightmost_center = window_width - desired_margin - sprite_width / 2
        total_center_distance = rightmost_center - leftmost_center

        # Divide this distance into (cols - 1) equal gaps
        spacing_x = total_center_distance / (cols - 1)

        # Ensure spacing is not negative
        if spacing_x < 0:
            # Grid too wide for specified margin, reduce spacing to fit
            spacing_x = (window_width - sprite_width) / (cols - 1)
            print(f"[WARNING] Grid too wide for margin {desired_margin}, using minimum spacing {spacing_x}")

        start_x = leftmost_center

        return start_x, spacing_x
    else:
        # Equal margins on both sides (original behavior)
        # Use a reasonable default spacing and calculate margins
        default_spacing = 80.0
        total_sprite_width = sprite_width * cols
        total_spacing_width = default_spacing * (cols - 1)
        total_grid_width = total_sprite_width + total_spacing_width
        total_margin = window_width - total_grid_width
        left_margin = total_margin / 2
        start_x = left_margin + sprite_width / 2
        return start_x, default_spacing


def get_centered_grid_spacing(desired_margin: float = 0.0):
    """Calculate centered spacing for the enemy grid with configurable margins.
    Args:
        desired_margin: Desired left and right margin (default: 0.0 for full-width grid)
    Returns:
        Tuple of (start_x, spacing_x) for centered grid
    """
    if desired_margin == 0.0:
        # Full-width grid (current behavior)
        # The sprites are positioned by their centers
        # Leftmost sprite center: ENEMY_WIDTH/2
        # Rightmost sprite center: WINDOW_WIDTH - ENEMY_WIDTH/2
        # Total distance between centers: (WINDOW_WIDTH - ENEMY_WIDTH/2) - ENEMY_WIDTH/2 = WINDOW_WIDTH - ENEMY_WIDTH

        total_center_distance = WINDOW_WIDTH - ENEMY_WIDTH
        spacing_x = total_center_distance / 3  # 3 gaps for 4 columns
        start_x = ENEMY_WIDTH / 2  # Center of the first sprite

        return start_x, spacing_x
    else:
        # Use configurable margin
        return calculate_centered_grid_layout(
            window_width=WINDOW_WIDTH,
            cols=4,
            sprite_width=ENEMY_WIDTH,
            desired_margin=desired_margin,
        )


def main() -> None:
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.show_view(StarfieldView())
    arcade.run()


if __name__ == "__main__":
    main()
