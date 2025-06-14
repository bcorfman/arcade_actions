"""
Slime Invaders refactored with the Actions API.

This example shows how to:

* Use the `Game` class as a base for a full game.
* Use `SpriteGroup` to manage collections of sprites.
* Use `BoundedMove` with a callback to create classic invader movement.
* Demonstrate compatibility between `ActionSprite`s and `arcade.Sprite`s.
* Support both direct game implementation and view-based architecture.
"""

import random

import arcade

from actions.base import ActionSprite
from actions.game import Game
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import BoundedMove

SPRITE_SCALING_PLAYER = 0.75
SPRITE_SCALING_enemy = 0.75
SPRITE_SCALING_LASER = 1.0

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Slime Invaders (Actions)"

# Convert time-based velocities (pixels/second) to frame-based velocities (pixels/frame)
BULLET_SPEED = 250
ENEMY_SPEED = 200

MAX_PLAYER_BULLETS = 3

ENEMY_VERTICAL_MARGIN = 15
RIGHT_ENEMY_BORDER = WINDOW_WIDTH - ENEMY_VERTICAL_MARGIN
LEFT_ENEMY_BORDER = ENEMY_VERTICAL_MARGIN

ENEMY_MOVE_DOWN_AMOUNT = 30

GAME_OVER = 1
PLAY_GAME = 0


class InvadersView(arcade.View):
    """View class for the main game screen."""

    def __init__(self, game: "InvadersGame"):
        super().__init__()
        self.game = game

        # Game state
        self.game_state = PLAY_GAME

        # Sprite management
        self.player_list = arcade.SpriteList()  # Regular arcade.SpriteList for player
        self.enemies = SpriteGroup()  # ActionSprite group for enemies
        self.shields = arcade.SpriteList()
        self.player_bullets = SpriteGroup()  # ActionSprite group for player bullets
        self.enemy_bullets = SpriteGroup()  # ActionSprite group for enemy bullets

        # Enemy movement state
        self.enemy_move_direction = 1  # 1 for right, -1 for left
        self.enemy_move_speed = ENEMY_SPEED
        self.boundary_action = None  # Will hold the BoundedMove action

        # Load sounds and textures
        self.gun_sound = arcade.load_sound(":resources:sounds/hurt5.wav")
        self.hit_sound = arcade.load_sound(":resources:sounds/hit5.wav")
        self.texture_enemy_left = arcade.load_texture(
            ":resources:images/enemies/slimeBlue.png",
        )
        self.texture_enemy_right = self.texture_enemy_left.flip_left_right()
        self.texture_blue_laser = arcade.load_texture(
            ":resources:images/space_shooter/laserBlue01.png",
        ).rotate_270()

        # UI
        self.score_text = arcade.Text("Score: 0", 10, 20, arcade.color.WHITE, 14)
        self.game_over_text = arcade.Text(
            "GAME OVER",
            x=WINDOW_WIDTH / 2,
            y=WINDOW_HEIGHT / 2,
            color=arcade.color.WHITE,
            font_size=60,
            anchor_x="center",
        )

        self.setup()

    def setup(self):
        """Reset the game so it can be played again."""
        self.game_state = PLAY_GAME
        self.game.score = 0

        # Clear sprite groups
        self.enemies.clear()
        self.shields.clear()
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.player_list.clear()

        # Set up player (regular arcade.Sprite)
        self.player_sprite = arcade.Sprite(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            scale=SPRITE_SCALING_PLAYER,
            center_x=WINDOW_WIDTH // 2,
            center_y=70,
        )
        self.player_list.append(self.player_sprite)

        # Make shields
        step = WINDOW_WIDTH // 4 - 50
        for x in [step, step * 2, step * 3]:
            self.make_shield(x)

        self.setup_level_one()
        self.window.set_mouse_visible(False)

        # Setup collision handlers
        self._setup_collision_handlers()

    def setup_level_one(self):
        # Create rows and columns of enemies
        x_count = 7
        x_start = 380
        x_spacing = 80
        y_count = 5
        y_start = 470
        y_spacing = 60

        # Reset enemy movement state
        self.enemy_move_direction = 1  # 1 for right, -1 for left
        self.enemy_move_speed = ENEMY_SPEED

        for x in range(x_start, x_spacing * x_count + x_start, x_spacing):
            for y in range(y_start, y_spacing * y_count + y_start, y_spacing):
                enemy = ActionSprite(self.texture_enemy_right, scale=SPRITE_SCALING_enemy, center_x=x, center_y=y)
                self.enemies.append(enemy)

        # Set up the enemy movement system with BoundedMove
        self._setup_enemy_bounded_movement()

    def _setup_enemy_bounded_movement(self):
        """Set up BoundedMove action for the entire enemy group, using callback for Space Invaders behavior."""
        if not self.enemies:
            return

        # Create the bounds function that returns the movement boundaries
        def get_enemy_bounds():
            return (LEFT_ENEMY_BORDER, 0, RIGHT_ENEMY_BORDER, WINDOW_HEIGHT)

        # Create the bounce callback that handles boundary hits
        def on_enemy_bounce(sprite, axis):
            """Handle when edge enemies hit boundaries - coordinate entire grid behavior."""
            if axis != "x" or not self.enemies:  # Only handle horizontal bounces
                return

            # BoundedMove now automatically handles edge detection, so any callback means an edge sprite bounced
            # Move ALL enemies down using GroupAction (Space Invaders grid behavior)
            move_down_action = MoveBy((0, -ENEMY_MOVE_DOWN_AMOUNT), 0.1)  # Quick downward movement
            self.enemies.do(move_down_action)

            # Reverse direction and update textures for ALL enemies
            self.enemy_move_direction *= -1
            for enemy in self.enemies:
                enemy.texture = self.texture_enemy_left if self.enemy_move_direction > 0 else self.texture_enemy_right

            # Clear horizontal movement actions and start new movement after downward movement completes
            # Note: We don't clear the move_down_action since it's already started
            self._start_enemy_grid_movement()

        # Create BoundedMove action for the entire enemy group
        self.boundary_action = BoundedMove(
            get_enemy_bounds, bounce_horizontal=True, bounce_vertical=False, on_bounce=on_enemy_bounce
        )

        # Apply boundary action to the entire enemy group
        self.boundary_action.target = self.enemies
        self.boundary_action.start()

        # Set up initial movement for ALL sprites
        self._start_enemy_grid_movement()

    def _start_enemy_grid_movement(self):
        """Start continuous movement for ALL enemies."""
        if not self.enemies:
            return

        # Calculate movement parameters
        move_distance = abs(RIGHT_ENEMY_BORDER - LEFT_ENEMY_BORDER)
        move_duration = move_distance / self.enemy_move_speed

        # Apply movement action to ALL enemies using GroupAction
        dx = move_distance * self.enemy_move_direction
        move_action = MoveBy((dx, 0), move_duration)
        self.enemies.do(move_action)

    def make_shield(self, x_start):
        """Make a shield from a grid of solid color sprites."""
        shield_block_width = 10
        shield_block_height = 20
        shield_width_count = 20
        shield_height_count = 5
        y_start = 150
        for x in range(x_start, x_start + shield_width_count * shield_block_width, shield_block_width):
            for y in range(y_start, y_start + shield_height_count * shield_block_height, shield_block_height):
                shield_sprite = arcade.SpriteSolidColor(
                    shield_block_width, shield_block_height, color=arcade.color.WHITE
                )
                shield_sprite.center_x = x
                shield_sprite.center_y = y
                self.shields.append(shield_sprite)

    def _setup_collision_handlers(self):
        """Configure collision detection for all sprite groups."""
        # Player bullets collision handlers
        self.player_bullets.on_collision_with(self.shields, self._handle_bullet_shield_collision).on_collision_with(
            self.enemies, self._handle_bullet_enemy_collision
        )

        # Enemy bullets collision handlers
        self.enemy_bullets.on_collision_with(self.shields, self._handle_bullet_shield_collision).on_collision_with(
            [self.player_sprite], self._handle_enemy_bullet_player_collision
        )

    def _handle_bullet_shield_collision(self, bullet, shields):
        """Handle collision between any bullet and shields."""
        bullet.remove_from_sprite_lists()
        for shield in shields:
            shield.remove_from_sprite_lists()

    def _handle_bullet_enemy_collision(self, bullet, enemies):
        """Handle collision between player bullet and enemies."""
        bullet.remove_from_sprite_lists()
        for enemy in enemies:
            enemy.remove_from_sprite_lists()
            self.game.score += 1
            arcade.play_sound(self.hit_sound)

    def _handle_enemy_bullet_player_collision(self, bullet, targets):
        """Handle collision between enemy bullet and player."""
        self.game_state = GAME_OVER
        bullet.remove_from_sprite_lists()

    def on_draw(self):
        """Render the screen."""
        self.clear()

        # Draw all sprite groups
        self.enemies.draw()
        self.player_bullets.draw()
        self.enemy_bullets.draw()
        self.shields.draw(pixelated=True)
        self.player_list.draw()

        # Draw UI elements
        self.score_text.text = f"Score: {self.game.score}"
        self.score_text.draw()

        if self.game_state == GAME_OVER:
            self.game_over_text.draw()
            self.window.set_mouse_visible(True)

    def on_update(self, delta_time: float):
        """Movement and game logic."""
        if self.game_state == GAME_OVER:
            return

        # Update sprite groups
        self.enemies.update(delta_time)
        self.player_bullets.update(delta_time)
        self.enemy_bullets.update(delta_time)
        self.shields.update(delta_time)

        # Update boundary action for enemy bouncing
        if self.boundary_action:
            self.boundary_action.update(delta_time)

        self.allow_enemies_to_fire()

        # Handle all collisions declaratively
        self.player_bullets.update_collisions()
        self.enemy_bullets.update_collisions()

        # Clean up off-screen bullets
        self._cleanup_offscreen_bullets()

        if len(self.enemies) == 0:
            self.setup_level_one()

    def _cleanup_offscreen_bullets(self):
        """Remove bullets that have left the screen."""
        for bullet in list(self.player_bullets):
            if bullet.bottom > WINDOW_HEIGHT:
                bullet.remove_from_sprite_lists()

        for bullet in list(self.enemy_bullets):
            if bullet.top < 0:
                bullet.remove_from_sprite_lists()

    def on_mouse_motion(self, x, y, dx, dy):
        """Move the player sprite with the mouse."""
        if self.game_state == PLAY_GAME and self.player_sprite:
            self.player_sprite.center_x = x

    def on_mouse_press(self, x, y, button, modifiers):
        """Fire a bullet when the mouse is clicked."""
        if len(self.player_bullets) < MAX_PLAYER_BULLETS:
            arcade.play_sound(self.gun_sound)
            bullet = ActionSprite(self.texture_blue_laser, scale=SPRITE_SCALING_LASER)
            bullet.center_x = self.player_sprite.center_x
            bullet.bottom = self.player_sprite.top
            # Use MoveBy action for continuous upward movement
            bullet.do(MoveBy((0, WINDOW_HEIGHT), duration=WINDOW_HEIGHT / BULLET_SPEED))
            self.player_bullets.append(bullet)

    def allow_enemies_to_fire(self):
        """Randomly select enemies to fire."""
        x_spawn = []
        for enemy in self.enemies.sprite_list:
            chance = 4 + len(self.enemies) * 4
            if random.randrange(chance) == 0 and enemy.center_x not in x_spawn:
                bullet = ActionSprite(
                    ":resources:images/space_shooter/laserRed01.png",
                    scale=SPRITE_SCALING_LASER,
                    angle=180,
                )
                bullet.center_x = enemy.center_x
                bullet.top = enemy.bottom
                # Use MoveBy action for continuous downward movement
                bullet.do(MoveBy((0, -WINDOW_HEIGHT), duration=WINDOW_HEIGHT / BULLET_SPEED))
                self.enemy_bullets.append(bullet)
            x_spawn.append(enemy.center_x)


class InvadersGame(Game):
    """Main game window class."""

    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_color = arcade.color.AMAZON
        self.game_view = InvadersView(self)
        self.show_view(self.game_view)


def main():
    """Main function"""

    game = InvadersGame()
    arcade.run()


if __name__ == "__main__":
    main()
