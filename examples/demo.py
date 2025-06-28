"""
Demo that pauses the game and drives timed callbacks
using pyglet's ClockGroup directly (no custom clock class).

Key bindings
------------
P          Toggle pause/resume
SPACE      Restart the action sequence
ESC        Quit
"""

from __future__ import annotations

import math

import arcade
from arcade import easing
from pyglet import clock as pyglet_clock  # ← lightweight scheduler

from actions.base import ActionSprite
from actions.interval import (
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
from actions.interval import (
    Easing as Ease,
)

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TEXT_MARGIN = 60
SPRITE_IMG = ":resources:images/animated_characters/female_person/femalePerson_idle.png"


class DemoSprite(ActionSprite):
    """Action-aware sprite with clamped movement."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.initial = dict(center_x=SCREEN_WIDTH // 2, center_y=SCREEN_HEIGHT // 2, angle=0, alpha=255, scale=0.5)
        self.reset_state()

    # ---------------------------------------------------------
    def update(self, dt: float):
        super().update(dt)
        self.center_x = max(self.width / 2, min(self.center_x, SCREEN_WIDTH - self.width / 2))
        self.center_y = max(self.height / 2 + TEXT_MARGIN, min(self.center_y, SCREEN_HEIGHT - self.height / 2))

    def reset_state(self):
        for k, v in self.initial.items():
            setattr(self, k, v)


class ActionDemo(arcade.Window):
    """Window that shows the action system plus a custom scheduler."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Minimal-Clock Demo")
        arcade.set_background_color(arcade.color.WHITE)

        # --- Core state ----------------------------------------------------
        self.paused: bool = False
        self.engine_clock = pyglet_clock.Clock()  # ← our scheduler
        self.sprite = DemoSprite(SPRITE_IMG, 0.5)
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        # --- UI text
        self.text = arcade.Text(
            "",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - TEXT_MARGIN // 2,
            arcade.color.BLACK,
            16,
            anchor_x="center",
            anchor_y="center",
        )

        # --- Action sequence
        self.actions = [
            ("MoveTo", lambda: MoveTo((600, 300), 2.0)),
            ("MoveBy", lambda: MoveBy((-200, 125), 2.0)),
            ("RotateBy", lambda: RotateBy(360, 2.0)),
            ("FadeOut", lambda: FadeOut(2.0)),
            ("FadeIn", lambda: FadeIn(2.0)),
            ("ScaleTo", lambda: ScaleTo(1.5, 2.0)),
            ("ScaleBy", lambda: ScaleBy(0.5, 2.0)),
            ("Blink", lambda: Blink(5, 2.0)),
            ("Ease In", lambda: Ease(MoveTo((600, 300), 2.0), easing.ease_in)),
            ("Ease In/Out", lambda: Ease(MoveTo((200, 300), 2.0), easing.ease_in_out)),
            ("Bezier", lambda: Bezier([(0, 0), (200, 200), (400, -200), (600, 0)], 3.0)),
            ("JumpTo", lambda: JumpTo((400, 300), 100, 3, 2.0)),
            ("Spawn with Bezier", self._create_spawn_bezier_action),
        ]
        self.index = 0
        self.demo_active = False
        self._setup_scheduler()
        self._start_demo()

    def _create_spawn_bezier_action(self):
        """Fan-out 32 sprites along looping Bézier paths."""
        num = 32
        radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.7 - TEXT_MARGIN
        spawn_x, spawn_y = self.sprite.center_x, self.sprite.center_y

        # Build 32 symmetrical paths
        paths: list[list[tuple[float, float]]] = []
        for i in range(num):
            ang = 2 * math.pi * i / num
            end_x, end_y = radius * math.cos(ang), radius * math.sin(ang)

            c1 = (end_y * 0.5, -end_x * 0.5)  # perpendicular kick
            c2 = (end_x + end_y * 0.5, end_y - end_x * 0.5)
            paths.append([(0, 0), c1, c2, (0, 0)])

        # Replace the single sprite with many
        self.sprite_list.remove(self.sprite)
        sprites = [DemoSprite(SPRITE_IMG, 2.0) for _ in range(num)]
        for s in sprites:
            s.center_x, s.center_y = spawn_x, spawn_y
            self.sprite_list.append(s)
        return [Bezier(p, 4.0) for p in paths]

    # ------------------------------------------------------------------ #
    #  Scheduler helpers
    # ------------------------------------------------------------------ #
    def _setup_scheduler(self):
        # Flash the banner text while the demo is running
        self.engine_clock.schedule_interval(self._flash_banner, 0.4)

    def _flash_banner(self, dt: float):
        if self.demo_active:  # Only flash during the demo
            color = arcade.color.RED if self.text.color == arcade.color.BLACK else arcade.color.BLACK
            self.text.color = color

    # ------------------------------------------------------------------ #
    #  Demo helpers
    # ------------------------------------------------------------------ #
    def _start_demo(self):
        self.demo_active, self.index = True, 0
        self.sprite = DemoSprite(SPRITE_IMG, 0.5)
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)
        self._play_next_action()

    def _play_next_action(self):
        if self.index >= len(self.actions):
            self.demo_active = False
            self.text.text = "Demo complete – Press SPACE to restart"
            for sprite in self.sprite_list[1:]:
                self.sprite_list.remove(sprite)
            return

        name, factory = self.actions[self.index]
        self.text.text = f"Current Action: {name}"
        if name == "Spawn with Bezier":
            actions = factory()
            for spr, act in zip(self.sprite_list, actions, strict=False):
                spr.do(act)
        else:
            self.sprite_list[0].do(factory())
        self.index += 1

    # ------------------------------------------------------------------ #
    #  Arcade callbacks
    # ------------------------------------------------------------------ #
    def on_draw(self):
        self.clear()
        self.sprite_list.draw()
        self.text.draw()

    def on_update(self, dt: float):
        # advance scheduler regardless – but freeze it if paused
        if not self.paused:
            self.engine_clock.tick()

        if not self.paused:
            self.sprite_list.update(dt)

        if self.demo_active and not any(s.has_active_actions() for s in self.sprite_list):
            self._play_next_action()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.P:
            self.paused = not self.paused
        elif key == arcade.key.SPACE and not self.demo_active:
            self._start_demo()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()


if __name__ == "__main__":
    ActionDemo()
    arcade.run()
