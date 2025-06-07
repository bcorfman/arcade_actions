"""
Slime Invaders refactored with the Actions API.

This example shows how to:

* Use the `Game` class as a base for a full game.
* Use `SpriteGroup` to manage collections of sprites.
* Use `BoundedMove` with a callback to create classic invader movement.
* Demonstrate compatibility between `ActionSprite`s and `arcade.Sprite`s.
"""

import random

import arcade

from actions.base import ActionSprite
from actions.game import Game
from actions.group import SpriteGroup
from actions.move import BoundedMove

SPRITE_SCALING_PLAYER = 0.75
SPRITE_SCALING_enemy = 0.75
SPRITE_SCALING_LASER = 1.0

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Slime Invaders (Actions)"

BULLET_SPEED = 250
ENEMY_SPEED = 200  # Increased speed for action-based movement

MAX_PLAYER_BULLETS = 3

ENEMY_VERTICAL_MARGIN = 15
RIGHT_ENEMY_BORDER = WINDOW_WIDTH - ENEMY_VERTICAL_MARGIN
LEFT_ENEMY_BORDER = ENEMY_VERTICAL_MARGIN

ENEMY_MOVE_DOWN_AMOUNT = 30

GAME_OVER = 1
PLAY_GAME = 0


class InvadersGame(Game):
    """Main application class."""

    def __init__(self):
        """Initializer"""
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

        # Game state
        self.game_state = PLAY_GAME

        # Sprite management (player is a standard arcade.Sprite)
        self.shields = SpriteGroup()
        self.player_bullets = SpriteGroup()
        self.enemy_bullets = SpriteGroup()

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
            x=self.width / 2,
            y=self.height / 2,
            color=arcade.color.WHITE,
            font_size=60,
            anchor_x="center",
        )

        # Flag to ensure enemy bounce logic runs once per frame
        self.enemy_logic_executed_this_frame = False
        self.setup()

    def setup(self):
        """Reset the game so it can be played again."""
        self.game_state = PLAY_GAME
        self.score = 0

        # Clear sprite groups
        self.enemies.clear()
        self.shields.clear()
        self.player_bullets.clear()
        self.enemy_bullets.clear()

        # Set up player
        self.player = arcade.Sprite(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            scale=SPRITE_SCALING_PLAYER,
            center_x=50,
            center_y=70,
        )

        # Make shields
        step = self.width // 4 - 50
        for x in [step, step * 2, step * 3]:
            self.make_shield(x)

        self.background_color = arcade.color.AMAZON
        self.setup_level_one()
        self.window.set_mouse_visible(False)

    def setup_level_one(self):
        # Create rows and columns of enemies
        x_count = 7
        x_start = 380
        x_spacing = 80
        y_count = 5
        y_start = 470
        y_spacing = 60
        for x in range(x_start, x_spacing * x_count + x_start, x_spacing):
            for y in range(y_start, y_spacing * y_count + y_start, y_spacing):
                enemy = ActionSprite(self.texture_enemy_right, scale=SPRITE_SCALING_enemy, center_x=x, center_y=y)
                enemy.change_x = -ENEMY_SPEED
                self.enemies.append(enemy)

        # Use BoundedMove to handle enemy movement and bouncing
        bounds = (LEFT_ENEMY_BORDER, 0, RIGHT_ENEMY_BORDER, WINDOW_HEIGHT)
        bounded_move = BoundedMove(lambda: bounds, on_bounce=self.on_enemy_bounce)
        self.enemies.do(bounded_move)

    def on_enemy_bounce(self, bouncing_enemy: ActionSprite, axis: str):
        """Callback for when an enemy hits a boundary."""
        if axis == "x" and not self.enemy_logic_executed_this_frame:
            self.enemy_logic_executed_this_frame = True
            new_dx = bouncing_enemy.change_x

            for enemy in self.enemies:
                enemy.change_x = new_dx
                enemy.center_y -= ENEMY_MOVE_DOWN_AMOUNT
                # Flip texture based on new direction
                if new_dx > 0:
                    enemy.texture = self.texture_enemy_left
                else:
                    enemy.texture = self.texture_enemy_right

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

    def draw(self):
        """Render the screen."""
        self.clear()
        self.enemies.draw()
        self.player_bullets.draw()
        self.enemy_bullets.draw()
        self.shields.draw(pixelated=True)
        if self.player:
            self.player.draw()

        self.score_text.text = f"Score: {self.score}"
        self.score_text.draw()

        if self.game_state == GAME_OVER:
            self.game_over_text.draw()
            self.window.set_mouse_visible(True)

    def _update_game_logic(self, delta_time: float):
        """Movement and game logic that runs every frame."""
        if self.game_state == GAME_OVER:
            return

        self.enemy_logic_executed_this_frame = False

        self.allow_enemies_to_fire()
        self.process_player_bullets()
        self.process_enemy_bullets()

        # Player is updated manually, not by actions
        if self.player:
            self.player.update()

        if len(self.enemies) == 0:
            self.setup_level_one()

    def on_key_press(self, key, modifiers):
        super().on_key_press(key, modifiers)
        if key == arcade.key.ESCAPE:
            self.window.close()

    def on_mouse_motion(self, x, y, dx, dy):
        """Move the player sprite with the mouse."""
        if self.game_state == PLAY_GAME and self.player:
            self.player.center_x = x

    def on_mouse_press(self, x, y, button, modifiers):
        """Fire a bullet when the mouse is clicked."""
        if len(self.player_bullets) < MAX_PLAYER_BULLETS:
            arcade.play_sound(self.gun_sound)
            bullet = ActionSprite(self.texture_blue_laser, scale=SPRITE_SCALING_LASER)
            bullet.change_y = BULLET_SPEED
            bullet.center_x = self.player.center_x
            bullet.bottom = self.player.top
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
                bullet.change_y = -BULLET_SPEED
                bullet.center_x = enemy.center_x
                bullet.top = enemy.bottom
                self.enemy_bullets.append(bullet)
                x_spawn.append(enemy.center_x)

    def process_player_bullets(self):
        """Handle collisions and movement for player bullets."""
        for bullet in self.player_bullets:
            # Shield collisions
            shield_hits = arcade.check_for_collision_with_list(bullet, self.shields)
            if shield_hits:
                bullet.remove_from_sprite_lists()
                for shield in shield_hits:
                    shield.remove_from_sprite_lists()
                continue

            # Enemy collisions
            enemy_hits = arcade.check_for_collision_with_list(bullet, self.enemies)
            if enemy_hits:
                bullet.remove_from_sprite_lists()
                for enemy in enemy_hits:
                    enemy.remove_from_sprite_lists()
                    self.score += 1
                    arcade.play_sound(self.hit_sound)

            if bullet.bottom > WINDOW_HEIGHT:
                bullet.remove_from_sprite_lists()

    def process_enemy_bullets(self):
        """Handle collisions and movement for enemy bullets."""
        for bullet in self.enemy_bullets:
            # Shield collisions
            shield_hits = arcade.check_for_collision_with_list(bullet, self.shields)
            if shield_hits:
                bullet.remove_from_sprite_lists()
                for shield in shield_hits:
                    shield.remove_from_sprite_lists()
                continue

            # Player collision
            if self.player and arcade.check_for_collision(bullet, self.player):
                self.game_state = GAME_OVER
                bullet.remove_from_sprite_lists()

            if bullet.top < 0:
                bullet.remove_from_sprite_lists()


def main():
    """Main function"""
    game = InvadersGame()
    arcade.run()


if __name__ == "__main__":
    main()
