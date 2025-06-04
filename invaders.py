import random

import arcade

from actions.base import ActionSprite, IntervalAction, sequence
from actions.instant import CallFunc, Place
from actions.interval import Delay, MoveBy

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Alien Invaders"

# Sprite scaling
SPRITE_SCALING = 1.0
SPRITE_SIZE = 64

# Movement speeds
PLAYER_MOVEMENT_SPEED = 5  # Units per frame
LASER_SPEED = 300  # Units per second

# Game states
ATTRACT_MODE = 0
GAME_RUNNING = 1
GAME_OVER = 2


class ExplosionSprite(ActionSprite):  # Changed to use ActionSprite
    def __init__(self):
        super().__init__()

        # Load explosion textures
        self.textures = []
        columns = 16
        count = 60
        sprite_width = 256
        sprite_height = 256
        file_name = ":resources:images/spritesheets/explosion.png"

        sprite_sheet = arcade.load_spritesheet(file_name, sprite_width, sprite_height, columns, count)
        self.textures = sprite_sheet
        self.texture = self.textures[0]

        # Create explosion animation action
        self.frame_delay = 0.05  # 20 FPS animation
        self.setup_animation()

    def setup_animation(self):
        actions = []
        for i in range(len(self.textures)):
            # Create action to set texture and wait
            set_texture = CallFunc(setattr, self, "texture", self.textures[i])
            actions.append(set_texture + Delay(self.frame_delay))

        # Add final action to remove sprite
        remove_action = CallFunc(self.remove_from_sprite_lists)
        animation = sequence(*actions) + remove_action
        self.do(animation)


class LaserSprite(ActionSprite):
    def __init__(self, filename: str, scale: float, speed: float, is_player: bool):
        super().__init__(filename, scale)
        self.speed = speed
        self.is_player = is_player

    def setup(self):
        # Create vertical movement action with fixed duration
        direction = 1 if self.is_player else -1
        distance = SCREEN_HEIGHT * direction
        move_action = MoveBy((0, distance), 2.0)  # Fixed 2 second duration
        remove_action = CallFunc(self.remove_from_sprite_lists)
        self.do(move_action + remove_action)


class AlienSprite(ActionSprite):
    def __init__(self, filename: str, scale: float):
        super().__init__(filename, scale)
        self.angle = 180  # Rotate sprite 180 degrees


class MovementDebug(MoveBy):
    """Debug wrapper for MoveBy to trace execution."""

    def update(self, t: float):
        print(f"MovementDebug update: t={t}, elapsed={self._elapsed}, duration={self.duration}")
        return super().update(t)


# Use this debug class for player movement
class PlayerSprite(ActionSprite):
    def __init__(self, filename: str, scale: float):
        super().__init__(filename, scale)
        self.lives = 3
        self.movement_action = None

    def move_left(self):
        """Simple left movement using basic MoveBy action."""
        if self.movement_action:
            self.remove_action(self.movement_action)
        move = MovementDebug((-100, 0), 1.0)  # Move left 100 pixels over 1 second
        self.do(move)  # Start a single move, no repeat

    def move_right(self):
        """Simple right movement using basic MoveBy action."""
        if self.movement_action:
            self.remove_action(self.movement_action)
        move = MovementDebug((100, 0), 1.0)  # Move right 100 pixels over 1 second
        self.do(move)  # Start a single move, no repeat

    def stop_movement(self):
        """Remove any active movement actions."""
        for action in self.actions[:]:  # Copy list since we'll modify it
            self.remove_action(action)

    def constrain_position(self):
        # Keep player in bounds
        self.center_x = max(self.width // 2, min(self.center_x, SCREEN_WIDTH - self.width // 2))


class AlienFormation(IntervalAction):
    def __init__(self, speed: float, drop_amount: float):
        super().__init__(float("inf"))
        self.speed = speed
        self.drop_amount = drop_amount
        self.direction = 1
        self.move_distance = 100
        self.formation_bottom = 0

    def update(self, t: float):
        super().update(t)  # This is critical - call parent update

        if not self.target:
            return

        # Get alien list from target sprite (which should be a dummy sprite)
        alien_list = self.target.alien_list
        if not alien_list:
            return

        # Calculate formation bounds
        left = min(alien.center_x for alien in alien_list)
        right = max(alien.center_x for alien in alien_list)
        bottom = min(alien.center_y for alien in alien_list)

        # Check for edge collisions
        if (right > SCREEN_WIDTH - 20 and self.direction > 0) or (left < 20 and self.direction < 0):
            self.direction *= -1
            # Move formation down
            for alien in alien_list:
                alien.center_y -= self.drop_amount

        # Move aliens horizontally - scale by delta time
        move_amount = self.speed * self.direction * t
        for alien in alien_list:
            alien.center_x += move_amount

        # Track lowest point of formation
        self.formation_bottom = bottom


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

        # Formation controller (using a dummy sprite to hold the formation action)
        self.formation_controller = ActionSprite()

        # Game state
        self.state = ATTRACT_MODE
        self.score = 0
        self.game_over_timer = 0

        # Load sounds
        self.alien_laser_sound = arcade.load_sound(":resources:/sounds/hit2.wav")
        self.alien_explosion_sound = arcade.load_sound(":resources:/sounds/explosion2.wav")
        self.player_laser_sound = arcade.load_sound(":resources:/sounds/hurt2.wav")
        self.player_explosion_sound = arcade.load_sound(":resources:/sounds/explosion1.wav")

        # Player sprite
        self.player_sprite = None

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

        # Set up formation controller
        self.formation_controller = ActionSprite()
        self.formation_controller.alien_list = self.alien_list

        # Set up player with initial position action
        self.player_sprite = PlayerSprite("res/ship_L.png", SPRITE_SCALING)
        initial_pos = Place((SCREEN_WIDTH // 2, 50))
        self.player_sprite.do(initial_pos)
        self.player_list.append(self.player_sprite)

        self.setup_aliens()
        self.setup_bases()
        self.setup_life_icons()

        # Reset score and setup text
        self.score = 0
        self.setup_text()

    def setup_aliens(self):
        """Create the alien formation."""
        for row in range(5):
            for col in range(10):
                enemy = AlienSprite("res/enemy_B.png", SPRITE_SCALING)
                # Use Place action for initial positioning
                pos = Place((100 + col * 60, 500 - row * 50))
                enemy.do(pos)
                self.alien_list.append(enemy)

        # Start formation movement
        formation_action = AlienFormation(1.0, 30)
        self.formation_controller.do(formation_action)

    def setup_bases(self):
        """Create the defensive bases."""
        base_positions = [200, 333, 466, 600]
        for x in base_positions:
            base = ActionSprite(":resources:images/tiles/boxCrate_double.png", 0.5)
            pos = Place((x, 150))
            base.do(pos)
            self.base_list.append(base)

    def setup_life_icons(self):
        for i in range(self.player_sprite.lives):
            icon = ActionSprite("res/ship_L.png", 0.25)
            pos = Place((120 + i * 25, SCREEN_HEIGHT - 20))
            icon.do(pos)
            self.life_icon_list.append(icon)

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if self.state == GAME_RUNNING:
            if key == arcade.key.LEFT:
                self.player_sprite.move_left()
            elif key == arcade.key.RIGHT:
                self.player_sprite.move_right()
            elif key == arcade.key.LCTRL:
                self.fire_player_laser()
        elif key == arcade.key.ENTER and self.state == ATTRACT_MODE:
            self.state = GAME_RUNNING
            self.setup()

    def on_key_release(self, key, modifiers):
        """Handle key releases."""
        if self.state == GAME_RUNNING:
            if key in (arcade.key.LEFT, arcade.key.RIGHT):
                self.player_sprite.stop_movement()

    def update(self, delta_time):
        """Movement and game logic."""
        if self.state == GAME_RUNNING:
            # Update all sprite lists (which handle their actions)
            self.player_list.update(delta_time)
            self.alien_list.update(delta_time)
            self.player_laser_list.update(delta_time)
            self.alien_laser_list.update(delta_time)
            self.explosion_list.update(delta_time)
            self.formation_controller.update(delta_time)

            # Constrain player position
            self.player_sprite.constrain_position()

            # Random alien shooting
            if random.random() < 0.02:
                bottom_aliens = self.get_bottom_row_aliens()
                if bottom_aliens:
                    shooting_alien = random.choice(bottom_aliens)
                    self.fire_alien_laser(shooting_alien)

            # Check for collisions
            self.check_collisions()

    def fire_player_laser(self):
        """Create a laser fired by the player."""
        if self.state != GAME_RUNNING:
            return

        laser = LaserSprite(":resources:/images/space_shooter/laserBlue01.png", SPRITE_SCALING, LASER_SPEED, True)
        # Use Place action for initial position
        pos = Place((self.player_sprite.center_x, self.player_sprite.center_y))
        laser.do(pos)
        laser.setup()

        self.player_laser_list.append(laser)
        arcade.play_sound(self.player_laser_sound)

    def fire_alien_laser(self, alien):
        """Create a laser fired by an alien."""
        laser = LaserSprite(":resources:/images/space_shooter/laserRed01.png", SPRITE_SCALING, LASER_SPEED, False)
        # Use Place action for initial position
        pos = Place((alien.center_x, alien.center_y))
        laser.do(pos)
        laser.setup()

        self.alien_laser_list.append(laser)
        arcade.play_sound(self.alien_laser_sound)

    def create_explosion(self, x: float, y: float, is_player: bool):
        """Create an explosion sprite at the given location."""
        explosion = ExplosionSprite()
        # Use Place action for initial position
        pos = Place((x, y))
        explosion.do(pos)
        self.explosion_list.append(explosion)

        sound = self.player_explosion_sound if is_player else self.alien_explosion_sound
        arcade.play_sound(sound)

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
        for laser_list in (self.player_laser_list, self.alien_laser_list):
            for laser in laser_list:
                hit_list = arcade.check_for_collision_with_list(laser, self.base_list)
                if hit_list:
                    laser.remove_from_sprite_lists()
                    for base in hit_list:
                        self.damage_base(base)

        # Check if aliens have reached the bottom
        if self.formation_controller.formation_bottom <= 150:  # Same height as bases
            self.state = GAME_OVER
            self.game_over_timer = 0

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
            # Reset player position
            reset_pos = Place((SCREEN_WIDTH // 2, 50))
            self.player_sprite.do(reset_pos)

    def damage_base(self, base: ActionSprite):
        """Create damage effect on a base when hit by a laser."""
        # Simple implementation - use ScaleBy action
        if base.scale > 0.2:
            base.scale *= 0.9
        else:
            base.remove_from_sprite_lists()

    def setup_text(self):
        """Create game text objects."""
        self.score_text = arcade.Text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)

        self.title_text = arcade.Text(
            "ALIEN INVADERS", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, arcade.color.WHITE, 64, anchor_x="center"
        )

        self.start_text = arcade.Text(
            "Press ENTER to start",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 20,
            arcade.color.WHITE,
            32,
            anchor_x="center",
        )

        self.game_over_text = arcade.Text(
            "GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, arcade.color.WHITE, 64, anchor_x="center"
        )

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

        # Draw game state text
        if self.state == ATTRACT_MODE:
            self.title_text.draw()
            self.start_text.draw()
        elif self.state == GAME_OVER:
            self.game_over_text.draw()


def main():
    window = AlienInvaders()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
