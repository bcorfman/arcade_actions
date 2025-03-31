"""
Move Sprite With Keyboard

Simple program to show moving a sprite with the keyboard.
The sprite_move_keyboard_better.py example is slightly better
in how it works, but also slightly more complex.

Artwork from https://kenney.nl

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.sprite_move_keyboard
"""

import arcade

from actions.base import ActionSprite

SPRITE_SCALING = 1.0

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Move Sprite with Keyboard Example"

DURATION = WINDOW_WIDTH / 5


class Player(ActionSprite):
    def update(self, delta_time: float = 1 / 60):
        # Move player.
        # Remove these lines if physics engine is moving player.
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Check for out-of-bounds
        if self.left < 0:
            self.left = 0
        elif self.right > WINDOW_WIDTH - 1:
            self.right = WINDOW_WIDTH - 1

        if self.bottom < 0:
            self.bottom = 0
        elif self.top > WINDOW_HEIGHT - 1:
            self.top = WINDOW_HEIGHT - 1


class Enemy(ActionSprite):
    def update(self, delta_time: float = 1 / 60):
        pass


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__()

        # Variables that will hold sprite lists
        self.player_list = None

        # Set up the player info
        self.player_sprite = None

        # Set the background color
        self.background_color = arcade.color.AMAZON
        self.active_actions = []

    def setup(self):
        """Set up the game and initialize the variables."""
        # Set up the player
        self.player_list = arcade.SpriteList()
        self.player_sprite = Player(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            scale=SPRITE_SCALING,
        )
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.player_list.append(self.player_sprite)

        self.enemy_list = arcade.SpriteList()
        self.enemy_sprite = Enemy(
            ":resources:images/animated_characters/male_person/malePerson_idle.png",
            scale=SPRITE_SCALING,
        )
        self.enemy_sprite.center_x = WINDOW_WIDTH / 2
        self.enemy_sprite.center_y = WINDOW_HEIGHT - self.enemy_sprite.height
        self.enemy_list.append(self.enemy_sprite)

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        self.clear()

        # Draw all the sprites.
        self.player_list.draw()
        self.enemy_list.draw()

    def on_update(self, delta_time):
        """Movement and game logic"""
        for action in self.active_actions[:]:  # Copy list since we'll modify it
            action.step(delta_time)
            if action.done():
                action.stop()
                self.active_actions.remove(action)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        # If the player presses a key, update the speed
        if key == arcade.key.UP:
            self.player_sprite.change_y = WINDOW_HEIGHT
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -WINDOW_HEIGHT
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -WINDOW_WIDTH
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = WINDOW_WIDTH

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        # If a player releases a key, zero out the speed.
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0


def main():
    """Main function"""
    # Create a window class. This is what actually shows up on screen
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

    # Create and setup the GameView
    game = GameView()
    game.setup()

    # Show GameView on screen
    window.show_view(game)

    # Start the arcade game loop
    arcade.run()


if __name__ == "__main__":
    main()
