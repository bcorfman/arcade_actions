import random

import arcade

from actions.base import ActionSprite, IntervalAction, Repeat
from actions.interval import MoveBy

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Alien Invaders"

# Sprite scaling
SPRITE_SCALING = 1.0
SPRITE_SIZE = 64

# Movement speeds
PLAYER_MOVEMENT_SPEED = 5
LASER_SPEED = 5

# Game states
ATTRACT_MODE = 0
GAME_RUNNING = 1
GAME_OVER = 2


class ExplosionSprite(arcade.Sprite):
    def __init__(self):
        super().__init__()

        # Start at 0 duration
        self.current_texture = 0
        self.time_counter = 0

        # Load explosion textures
        self.textures = []
        columns = 16
        count = 60
        sprite_width = 256
        sprite_height = 256
        file_name = ":resources:images/spritesheets/explosion.png"

        sprite_sheet = arcade.load_spritesheet(file_name, sprite_width, sprite_height, columns, count)
        for texture in sprite_sheet:
            self.textures.append(texture)

    def update(self):
        # Update to the next texture every frame
        self.current_texture += 1
        if self.current_texture < len(self.textures):
            self.texture = self.textures[self.current_texture]
        else:
            self.remove_from_sprite_lists()


class LaserSprite(ActionSprite):
    def __init__(self, filename: str, scale: float, speed: float, is_player: bool):
        super().__init__(filename, scale)
        self.speed = speed
        self.is_player = is_player

    def setup(self):
        # Set up vertical movement
        direction = 1 if self.is_player else -1
        move_action = MoveBy((0, direction * SCREEN_HEIGHT), SCREEN_HEIGHT / self.speed)
        self.do(move_action)


class AlienSprite(ActionSprite):
    def __init__(self, filename: str, scale: float):
        super().__init__(filename, scale)
        self.angle = 180  # Rotate sprite 180 degrees


class PlayerSprite(ActionSprite):
    def __init__(self, filename: str, scale: float):
        super().__init__(filename, scale)
        self.lives = 3


class FormationMove(IntervalAction):
    def __init__(self, speed: float, drop_amount: float, formation: arcade.SpriteList):
        super().__init__(float("inf"))
        self.speed = speed
        self.drop_amount = drop_amount
        self.prev_width = None
        self.formation = formation

    def start(self):
        # Get initial formation width
        active_enemies = [e for e in self.formation if not e.sprite_lists]
        if not active_enemies:
            return

        self.prev_width = max(e.center_x for e in active_enemies) - min(e.center_x for e in active_enemies)

        # Initial movement sequence
        self.move_right = MoveBy((self.prev_width, 0), self.speed)
        self.drop = MoveBy((0, -self.drop_amount), 0.5)
        self.move_left = MoveBy((-self.prev_width, 0), self.speed)

        sequence = self.move_right + self.drop + self.move_left + self.drop
        self.movement = Repeat(sequence)

        # Combine movements
        self.movement.start()

    def update(self, t: float):
        # Get current formation bounds
        active_enemies = [e for e in self.formation if not e.sprite_lists]
        if not active_enemies:
            return

        # Check if formation width has changed
        current_width = max(e.center_x for e in active_enemies) - min(e.center_x for e in active_enemies)

        if current_width != self.prev_width:
            # Update the movement distances
            self.move_right.update_delta(current_width, 0)
            self.move_left.update_delta(-current_width, 0)
            self.prev_width = current_width


class AlienInvaders(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Initialize sprite lists
        self.player_list = None
        self.alien_list = None
        self.player_laser_list = None
        self.alien_laser_list = None
        self.explosion_list = None
        self.base_list = None
        self.life_icon_list = None
        self.text_list = None

        # Game state
        self.state = ATTRACT_MODE
        self.score = 0
        self.game_over_timer = 0

        # Load sounds
        self.alien_laser_sound = arcade.load_sound(":resources:/sounds/hit2.wav")
        self.alien_explosion_sound = arcade.load_sound(":resources:/sounds/explosion2.wav")
        self.player_laser_sound = arcade.load_sound(":resources:/sounds/hurt2.wav")
        self.player_explosion_sound = arcade.load_sound(":resources:/sounds/explosion1.wav")

        # Load custom font
        arcade.load_font("res/AlienRavager-0WYod.ttf")

        # Player sprite
        self.player_sprite = None

        # Keyboard state
        self.left_pressed = False
        self.right_pressed = False

    def setup(self):
        """Set up the game and initialize variables."""
        # Create sprite lists
        self.player_list = arcade.SpriteList()
        self.alien_list = arcade.SpriteList()
        self.player_laser_list = arcade.SpriteList()
        self.alien_laser_list = arcade.SpriteList()
        self.explosion_list = arcade.SpriteList()
        self.base_list = arcade.SpriteList()
        self.life_icon_list = arcade.SpriteList()

        # Set up player
        self.player_sprite = PlayerSprite("res/ship_L.png", SPRITE_SCALING)
        self.player_sprite.center_x = SCREEN_WIDTH // 2
        self.player_sprite.center_y = 50
        self.player_list.append(self.player_sprite)

        self.setup_aliens()
        self.setup_bases()
        self.setup_life_icons()
        self.setup_text()

        # Reset score
        self.score = 0

    def setup_aliens(self):
        # Create grid of enemies in the formation
        enemies = []
        for row in range(5):
            for col in range(10):
                enemy = ActionSprite("res/enemy_B.png")
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 50
                self.alien_list.append(enemy)

        formation_move = FormationMove(2.0, 30, self.alien_list)
        for alien in self.alien_list:
            alien.do(formation_move)

    def setup_bases(self):
        """Create the defensive bases."""
        base_positions = [200, 333, 466, 600]
        for x in base_positions:
            base = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", 0.5)
            base.center_x = x
            base.center_y = 150
            self.base_list.append(base)

    def setup_life_icons(self):
        for i in range(self.player_sprite.lives):
            icon = arcade.Sprite("res/ship_L.png", 0.25)
            icon.center_x = 120 + i * 25
            icon.center_y = SCREEN_HEIGHT - 20
            self.life_icon_list.append(icon)

    def setup_text(self):
        self.score_text = arcade.Text(
            text="Score: 0",
            x=10,
            y=SCREEN_HEIGHT - 30,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="AlienRavager-0WYod",
        )

        self.title_text = arcade.Text(
            text="Alien Invaders",
            x=SCREEN_WIDTH // 2,
            y=SCREEN_HEIGHT // 2 + 25,
            color=arcade.color.WHITE,
            font_size=48,
            font_name="AlienRavager-0WYod",
            anchor_x="center",
        )

        self.start_text = arcade.Text(
            text="Press ENTER to begin",
            x=SCREEN_WIDTH // 2,
            y=SCREEN_HEIGHT // 2 - 25,
            color=arcade.color.WHITE,
            font_size=36,
            font_name="AlienRavager-0WYod",
            anchor_x="center",
        )

        self.game_over_text = arcade.Text(
            text="Game Over",
            x=SCREEN_WIDTH // 2,
            y=SCREEN_HEIGHT // 2,
            color=arcade.color.WHITE,
            font_size=48,
            font_name="AlienRavager-0WYod",
            anchor_x="center",
        )

        # Set initial visibility
        self.title_text.visible = False
        self.start_text.visible = False
        self.game_over_text.visible = False

    def on_draw(self):
        """Render the screen."""
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)

        # Draw all sprite lists
        self.base_list.draw()
        self.player_list.draw()
        self.alien_list.draw()
        self.player_laser_list.draw()
        self.alien_laser_list.draw()
        self.explosion_list.draw()
        self.life_icon_list.draw()

        # Update and draw score
        self.score_text.text = f"Score: {self.score}"
        self.score_text.draw()

        # Draw attract mode text
        if self.state == ATTRACT_MODE:
            self.title_text.draw()
            self.start_text.draw()

        # Draw game over text
        elif self.state == GAME_OVER:
            self.game_over_text.draw()

    def update(self, delta_time):
        """Movement and game logic."""
        # Update all sprites
        self.player_list.update()
        self.alien_list.update()
        self.player_laser_list.update()
        self.alien_laser_list.update()
        self.explosion_list.update()

        # Handle player movement
        if self.state == GAME_RUNNING:
            if self.left_pressed and not self.right_pressed:
                self.player_sprite.center_x -= PLAYER_MOVEMENT_SPEED
            elif self.right_pressed and not self.left_pressed:
                self.player_sprite.center_x += PLAYER_MOVEMENT_SPEED

            # Keep player in bounds
            self.player_sprite.center_x = max(
                self.player_sprite.width // 2,
                min(self.player_sprite.center_x, SCREEN_WIDTH - self.player_sprite.width // 2),
            )

            # Random alien shooting
            if random.random() < 0.02:
                bottom_aliens = self.get_bottom_row_aliens()
                if bottom_aliens:
                    shooting_alien = random.choice(bottom_aliens)
                    self.fire_alien_laser(shooting_alien)

            # Check for collisions
            self.check_collisions()

        # Handle game over timer
        if self.state == GAME_OVER:
            self.game_over_timer += delta_time
            if self.game_over_timer >= 3.0:
                self.state = ATTRACT_MODE
                self.setup()

    def get_bottom_row_aliens(self) -> list[AlienSprite]:
        """Get list of aliens at the bottom of each column."""
        if not self.alien_list:
            return []

        columns = {}
        for alien in self.alien_list:
            x = alien.center_x
            if x not in columns or alien.center_y < columns[x].center_y:
                columns[x] = alien

        return list(columns.values())

    def fire_player_laser(self):
        """Create a laser fired by the player."""
        if self.state != GAME_RUNNING:
            return

        laser = LaserSprite(":resources:/images/space_shooter/laserBlue01.png", SPRITE_SCALING, LASER_SPEED, True)
        laser.center_x = self.player_sprite.center_x
        laser.center_y = self.player_sprite.center_y
        laser.setup()

        self.player_laser_list.append(laser)
        arcade.play_sound(self.player_laser_sound)

    def fire_alien_laser(self, alien: AlienSprite):
        """Create a laser fired by an alien."""
        laser = LaserSprite(":resources:/images/space_shooter/laserRed01.png", SPRITE_SCALING, LASER_SPEED, False)
        laser.center_x = alien.center_x
        laser.center_y = alien.center_y
        laser.setup()

        self.alien_laser_list.append(laser)
        arcade.play_sound(self.alien_laser_sound)

    def create_explosion(self, x: float, y: float, is_player: bool):
        """Create an explosion sprite at the given location."""
        explosion = ExplosionSprite()
        explosion.center_x = x
        explosion.center_y = y
        self.explosion_list.append(explosion)

        sound = self.player_explosion_sound if is_player else self.alien_explosion_sound
        arcade.play_sound(sound)

    def check_collisions(self):
        """Check for collisions between sprites."""
        # Player lasers hitting aliens
        for laser in self.player_laser_list:
            hit_list = arcade.check_for_collision_with_list(laser, self.alien_list)

            if hit_list:
                laser.remove_from_sprite_lists()
                for alien in hit_list:
                    self.score += 10
                    self.create_explosion(alien.center_x, alien.center_y, False)
                    alien.remove_from_sprite_lists()

        # Alien lasers hitting player
        for laser in self.alien_laser_list:
            if arcade.check_for_collision(laser, self.player_sprite):
                self.handle_player_hit()
                laser.remove_from_sprite_lists()

        # Lasers hitting bases
        for laser in self.player_laser_list + self.alien_laser_list:
            hit_list = arcade.check_for_collision_with_list(laser, self.base_list)
            if hit_list:
                laser.remove_from_sprite_lists()
                for base in hit_list:
                    # Create damage effect on base
                    self.damage_base(base, laser)

    def handle_player_hit(self):
        """Handle the player being hit by a laser."""
        self.create_explosion(self.player_sprite.center_x, self.player_sprite.center_y, True)

        # Remove a life icon
        if self.life_icon_list:
            self.life_icon_list[-1].remove_from_sprite_lists()

        self.player_sprite.lives -= 1

        if self.player_sprite.lives <= 0:
            self.state = GAME_OVER
            self.game_over_timer = 0
        else:
            # Reset player position after delay
            self.player_sprite.center_x = SCREEN_WIDTH // 2

    def damage_base(self, base: arcade.Sprite, laser: LaserSprite):
        """Create damage effect on a base where hit by a laser."""
        # Simple implementation - just reduce the base's scale
        base.scale *= 0.9
        if base.scale < 0.2:
            base.remove_from_sprite_lists()

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.ENTER and self.state == ATTRACT_MODE:
            self.state = GAME_RUNNING
            self.setup()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif self.state == GAME_RUNNING:
            if key == arcade.key.LEFT:
                self.left_pressed = True
            elif key == arcade.key.RIGHT:
                self.right_pressed = True
            elif key == arcade.key.LCTRL:
                self.fire_player_laser()

    def on_key_release(self, key, modifiers):
        """Handle key releases."""
        if self.state == GAME_RUNNING:
            if key == arcade.key.LEFT:
                self.left_pressed = False
            elif key == arcade.key.RIGHT:
                self.right_pressed = False


def main():
    """Main function to start the game."""
    window = AlienInvaders()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
