import arcade

from actions.base import Action
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


class ActionSprite(arcade.Sprite):
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

    def do(self, action: Action):
        action.target = self
        action.start()
        self.actions.append(action)

    def update(self):
        for action in self.actions[:]:
            action.step(1 / 60)  # Assuming 60 FPS
            if action.done():
                action.stop()
                self.actions.remove(action)

        # Ensure sprite stays within screen bounds and below text
        self.center_x = max(self.width / 2, min(self.center_x, SCREEN_WIDTH - self.width / 2))
        self.center_y = max(self.height / 2 + TEXT_MARGIN, min(self.center_y, SCREEN_HEIGHT - self.height / 2))

    def reset_state(self):
        for attr, value in self.initial_state.items():
            setattr(self, attr, value)


class ActionDemo(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.WHITE)

        self.sprite = ActionSprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        self.current_action = 0
        self.actions = [
            ("MoveTo", lambda: MoveTo((600, 300), 2.0)),
            ("MoveBy", lambda: MoveBy((-200, 125), 2.0)),  # Move to upper left
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

    def start_demo(self):
        self.demo_active = True
        self.current_action = 0
        self.sprite.reset_state()
        self.start_next_action()

    def start_next_action(self):
        if self.current_action < len(self.actions):
            action_name, action_creator = self.actions[self.current_action]
            self.message = f"Current Action: {action_name}"
            self.text_sprite.text = self.message
            self.sprite.do(action_creator())
            self.current_action += 1
        else:
            self.demo_active = False
            self.message = "Demo completed. Press SPACE to restart or ESC to exit."
            self.text_sprite.text = self.message

    def on_draw(self):
        self.clear()
        self.sprite_list.draw()
        self.text_sprite.draw()

    def on_update(self, delta_time):
        self.sprite.update()
        if self.demo_active and not self.sprite.actions:
            self.start_next_action()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and not self.demo_active:
            self.start_demo()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()


def main():
    ActionDemo()
    arcade.run()


if __name__ == "__main__":
    main()
