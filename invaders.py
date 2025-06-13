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
        self.shields = SpriteGroup()  # ActionSprite group for shields
        self.player_bullets = SpriteGroup()  # ActionSprite group for player bullets
        self.enemy_bullets = SpriteGroup()  # ActionSprite group for enemy bullets

        # Enemy movement will be handled by the grid movement system

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

        self.background_color = arcade.color.AMAZON
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

        # Track if we've already handled a boundary collision this frame
        self._boundary_handled_this_frame = False

        # Track enemy movement direction and state
        self.enemy_move_direction = 1  # 1 for right, -1 for left
        self.enemy_move_speed = ENEMY_SPEED

        for x in range(x_start, x_spacing * x_count + x_start, x_spacing):
            for y in range(y_start, y_spacing * y_count + y_start, y_spacing):
                enemy = ActionSprite(self.texture_enemy_right, scale=SPRITE_SCALING_enemy, center_x=x, center_y=y)
                self.enemies.append(enemy)

        # Create a single movement action for the entire enemy grid
        self._setup_enemy_grid_movement()

    def _setup_enemy_grid_movement(self):
        """Set up movement for the entire enemy grid as one unit."""
        if not self.enemies:
            return

        # Calculate the movement distance and duration for one direction
        move_distance = RIGHT_ENEMY_BORDER - LEFT_ENEMY_BORDER
        move_duration = move_distance / self.enemy_move_speed

        # Create a continuous horizontal movement for all enemies
        for enemy in self.enemies:
            # Create movement action that moves the full distance in the current direction
            dx = move_distance * self.enemy_move_direction
            move_action = MoveBy((dx, 0), move_duration)
            enemy.do(move_action)

    def _check_enemy_boundaries(self):
        """Check if any enemy has hit a boundary and handle grid reversal."""
        if not self.enemies or self._boundary_handled_this_frame:
            return

        # Find the leftmost and rightmost enemies
        leftmost_x = min(enemy.center_x - enemy.width / 2 for enemy in self.enemies)
        rightmost_x = max(enemy.center_x + enemy.width / 2 for enemy in self.enemies)

        should_reverse = False

        # Check boundaries based on movement direction
        if self.enemy_move_direction > 0:  # Moving right
            if rightmost_x >= RIGHT_ENEMY_BORDER:
                should_reverse = True
        else:  # Moving left
            if leftmost_x <= LEFT_ENEMY_BORDER:
                should_reverse = True

        if should_reverse:
            self._reverse_enemy_grid()

    def _reverse_enemy_grid(self):
        """Reverse the entire enemy grid direction and move down."""
        if self._boundary_handled_this_frame:
            return
        self._boundary_handled_this_frame = True

        # Move all enemies down
        for enemy in self.enemies:
            enemy.center_y -= ENEMY_MOVE_DOWN_AMOUNT

        # Reverse direction
        self.enemy_move_direction *= -1

        # Update textures based on new direction
        for enemy in self.enemies:
            enemy.texture = self.texture_enemy_left if self.enemy_move_direction > 0 else self.texture_enemy_right

        # Stop current movement actions and start new ones in opposite direction
        for enemy in self.enemies:
            enemy.clear_actions()

        # Set up new movement in the opposite direction
        self._setup_enemy_grid_movement()

    def _handle_enemy_boundary(self, sprite: ActionSprite, axis: str):
        """Handle when an enemy hits the boundary."""
        # This method is no longer used but kept for compatibility
        pass

    def make_shield(self, x_start):
        """Make a shield from a grid of solid color sprites."""
        shield_block_width = 10
        shield_block_height = 20
        shield_width_count = 20
        shield_height_count = 5
        y_start = 150
        for x in range(x_start, x_start + shield_width_count * shield_block_width, shield_block_width):
            for y in range(y_start, y_start + shield_height_count * shield_block_height, shield_block_height):
                shield_sprite = ActionSprite(
                    arcade.SpriteSolidColor(shield_block_width, shield_block_height, color=arcade.color.WHITE)
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

        # Reset boundary handling flag each frame
        self._boundary_handled_this_frame = False

        # Update all sprite groups
        self.enemies.update(delta_time)
        self.player_bullets.update(delta_time)
        self.enemy_bullets.update(delta_time)
        self.shields.update(delta_time)

        # Check enemy boundaries for grid reversal
        self._check_enemy_boundaries()

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
        for enemy in self.enemies:
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
        self.game_view = InvadersView(self)
        self.show_view(self.game_view)


def main():
    """Main function"""
    game = InvadersGame()
    arcade.run()


if __name__ == "__main__":
    main()
