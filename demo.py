import logging
import math
import traceback
from functools import wraps

import arcade

from actions.base import Action, Spawn
from actions.interval import (
    AccelDecel,
    Accelerate,
    Bezier,
    Blink,
    FadeIn,
    FadeOut,
    JumpTo,
    MoveBy,
    MoveTo,
    RotateBy,
    ScaleBy,
    ScaleTo,
)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Action System Demo"
TEXT_MARGIN = 60  # Margin for text at the top of the screen
SPRITE_IMAGE_PATH = ":resources:images/animated_characters/female_person/femalePerson_idle.png"

# Setup basic configuration for logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="demo.log",  # Log to a file
    filemode="a",
)  # Append mode

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Set console to show only warnings and above
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Get the root logger and add the console handler
logger = logging.getLogger()
logger.addHandler(console_handler)


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.debug(traceback.format_exc())

            # For methods that are part of the game loop (update, draw, etc.),
            # we want to continue execution to prevent the game from freezing
            if func.__name__ in ["on_update", "on_draw", "update"]:
                return

            # For other functions, we might want to re-raise the exception
            # to allow the caller to handle it
            raise

    return wrapper


class ActionSprite(arcade.Sprite):
    @error_handler
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions: list[Action] = []
        self.initial_state = {
            "center_x": SCREEN_WIDTH // 2,
            "center_y": SCREEN_HEIGHT // 2,
            "angle": 0,
            "alpha": 255,
            "scale": 0.5,
        }
        self.reset_state()

    @error_handler
    def do(self, action: Action):
        action.target = self
        action.start()
        self.actions.append(action)

    @error_handler
    def update(self, delta_time: float = 1 / 60):
        super().update()
        for action in self.actions[:]:
            try:
                action.step(delta_time)
                if action.done():
                    action.stop()
                    self.actions.remove(action)
            except Exception as e:
                print(f"Error updating action: {e}")
                self.actions.remove(action)

        # Ensure sprite stays within screen bounds and below text
        self.center_x = max(self.width / 2, min(self.center_x, SCREEN_WIDTH - self.width / 2))
        self.center_y = max(self.height / 2 + TEXT_MARGIN, min(self.center_y, SCREEN_HEIGHT - self.height / 2))

    @error_handler
    def reset_state(self):
        for attr, value in self.initial_state.items():
            setattr(self, attr, value)


class ActionDemo(arcade.Window):
    @error_handler
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.WHITE)

        self.sprite = ActionSprite(SPRITE_IMAGE_PATH, 0.5)
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        self.current_action = 0
        self.actions = [
            ("MoveTo", lambda: MoveTo((600, 300), 2.0)),
            ("MoveBy", lambda: MoveBy((-200, 125), 2.0)),
            ("RotateBy", lambda: RotateBy(360, 2.0)),
            ("FadeOut", lambda: FadeOut(2.0)),
            ("FadeIn", lambda: FadeIn(2.0)),
            ("ScaleTo", lambda: ScaleTo(1.5, 2.0)),
            ("ScaleBy", lambda: ScaleBy(0.5, 2.0)),
            ("Blink", lambda: Blink(5, 2.0)),
            ("Accelerate", lambda: Accelerate(MoveTo((600, 300), 2.0), 2.0)),
            ("AccelDecel", lambda: AccelDecel(MoveTo((200, 300), 2.0))),
            ("Bezier", lambda: Bezier([(0, 0), (200, 200), (400, -200), (600, 0)], 3.0)),
            ("JumpTo", lambda: JumpTo((400, 300), 100, 3, 2.0)),
            ("Spawn with Bezier", self.create_spawn_bezier_action),
        ]

        self.message = ""
        self.text_sprite = arcade.Text(
            self.message,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - TEXT_MARGIN // 2,
            arcade.color.BLACK,
            16,
            anchor_x="center",
            anchor_y="center",
        )

        self.demo_active = False
        self.start_demo()

    @error_handler
    def create_spawn_bezier_action(self):
        num_sprites = 16
        radius = (
            min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.6 - TEXT_MARGIN
        )  # Adjust radius to fit within screen and below text
        spawn_x, spawn_y = self.sprite.center_x, self.sprite.center_y  # Use the current sprite's position

        bezier_paths = []
        for i in range(num_sprites):
            angle = 2 * math.pi * i / num_sprites
            end_x = radius * math.cos(angle)
            end_y = radius * math.sin(angle)

            # Create a curved path that goes out from the center, circles around, and comes back
            control1_x = end_y * 0.5  # Perpendicular to the radius
            control1_y = -end_x * 0.5
            control2_x = end_x + end_y * 0.5
            control2_y = end_y - end_x * 0.5

            path = [
                (0, 0),  # Start at center
                (control1_x, control1_y),  # First control point
                (control2_x, control2_y),  # Second control point
                (0, 0),  # End back at center
            ]
            bezier_paths.append(path)

        self.sprite_list.remove(self.sprite)

        sprites = [ActionSprite(SPRITE_IMAGE_PATH, 2.0) for _ in range(num_sprites)]
        for sprite in sprites:
            sprite.center_x = spawn_x
            sprite.center_y = spawn_y
            self.sprite_list.append(sprite)

        actions = [Bezier(path, 4.0) for path in bezier_paths]
        return Spawn(actions)

    @error_handler
    def start_demo(self):
        self.demo_active = True
        self.current_action = 0
        # Reset to only one sprite with original scale
        self.sprite_list = arcade.SpriteList()
        self.sprite = ActionSprite(SPRITE_IMAGE_PATH, 0.5)
        self.sprite_list.append(self.sprite)
        self.sprite.reset_state()
        self.start_next_action()

    @error_handler
    def start_next_action(self):
        if self.current_action < len(self.actions):
            action_name, action_creator = self.actions[self.current_action]
            self.message = f"Current Action: {action_name}"
            self.text_sprite.text = self.message
            if action_name == "Spawn with Bezier":
                action = action_creator()
                if action:
                    for sprite, subaction in zip(self.sprite_list, action.actions, strict=False):
                        sprite.do(subaction)
            else:
                self.sprite.do(action_creator())
            self.current_action += 1
        else:
            self.demo_active = False
            self.message = "Demo completed. Press SPACE to restart or ESC to exit."
            self.text_sprite.text = self.message

    @error_handler
    def on_draw(self):
        self.clear()
        self.sprite_list.draw()
        self.text_sprite.draw()

    @error_handler
    def on_update(self, delta_time):
        self.sprite_list.update(delta_time)
        if self.demo_active and all(not sprite.actions for sprite in self.sprite_list):
            self.start_next_action()

    @error_handler
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and not self.demo_active:
            self.start_demo()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()


@error_handler
def main():
    ActionDemo()
    arcade.run()


if __name__ == "__main__":
    main()
