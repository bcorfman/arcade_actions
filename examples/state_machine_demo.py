"""Amazon State-Machine Demo (1-on-1)

This minimal example shows how to drive both a player sprite and an AI-controlled
enemy sprite using the `StateMachine` helper from ArcadeActions.  Each sprite
shares the same six high-level states (Idle, Run, Jump, Attack, Hurt, Dead) but
transitions are triggered differently:

• AmazonFighter (player) - keyboard input & collisions
• AmazonEnemy            - internal timers & distance checks

"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

import arcade
from statemachine import State, StateMachine

from actions import Action, callback_until, center_window, cycle_textures_until, infinite

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "StateMachine Demo"
BACKGROUND_COLOR = arcade.color.DARK_MIDNIGHT_BLUE
PLAYER_ASSETS_ROOT = Path("res/Amazon_2")
ENEMY_ASSETS_ROOT = Path("res/Amazon_3")


@dataclass
class AnimInfo:
    fps: int
    frame_count: int
    frames: list[arcade.Texture] = field(default_factory=list)


def load_animation(state: str, info: AnimInfo, folder: Path, flip_vertical: bool) -> list[arcade.Texture]:
    """Load textures from sprite sheet."""
    sheet = arcade.SpriteSheet(folder / f"{state}.png")
    textures = sheet.get_texture_grid(
        size=(128, 128),
        columns=info.frame_count,
        count=info.frame_count,
    )
    if flip_vertical:
        textures = [texture.flip_left_right() for texture in textures]
    return textures


# ---------------------------------------------------------------------------
# Sprite classes
# ---------------------------------------------------------------------------
class BaseAmazon(arcade.Sprite):
    """Shared loading/animation logic for player & enemy."""

    def __init__(self, state_info: dict[str, AnimInfo], sprites_dir: Path, scale: float = 1.0, flip_vertical=False):
        # Start with a 1×1 transparent texture – we’ll set the correct one in on_enter
        self.state_info = state_info
        for state, info in self.state_info.items():
            self.state_info[state].frames = load_animation(state, info, sprites_dir, flip_vertical)
        super().__init__(self.state_info["Idle"].frames, scale=scale, hit_box_algorithm="None")

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------
    def _play(self, anim_name: str):
        pass

    def update_animation(self, delta_time: float = 1 / 60):
        pass

    # ------------------------------------------------------------------
    # These will be defined in subclasses
    # ------------------------------------------------------------------
    def _setup_states(self):
        raise NotImplementedError


class DuelContext:
    def __init__(self, figure: BaseAmazon):
        self.figure = figure


class PlayerStateMachine(StateMachine):
    idle = State()
    idle_2 = State(initial=True)

    cycle = idle.to(idle_2) | idle_2.to(idle)

    def __init__(self, ctx: DuelContext):
        self.ctx = ctx
        super().__init__()

    def setup_cycle(self, info: AnimInfo):
        def on_cycle_complete():
            if random.random() < 0.1:
                self.idle()

        cycle_duration = len(info.frames) / info.fps
        cycle_textures_until(self.ctx.figure, textures=info.frames, frames_per_second=info.fps, tag="enemy")
        callback_until(
            self.ctx.figure,
            callback=on_cycle_complete,
            condition=infinite,
            seconds_between_calls=cycle_duration,
            tag="enemy",
        )

    def on_enter_idle(self):
        self.setup_cycle(self.ctx.figure.state_info["Idle"])

    def on_exit_idle(self):
        Action.stop_actions_for_target(self.ctx.figure, "player")

    def on_enter_idle_2(self):
        self.setup_cycle(self.ctx.figure.state_info["Idle_2"])

    def on_exit_idle_2(self):
        Action.stop_actions_for_target(self.ctx.figure, "player")


class EnemyStateMachine(StateMachine):
    idle = State()
    idle_2 = State(initial=True)

    cycle = idle.to(idle_2) | idle_2.to(idle)

    def __init__(self, ctx: DuelContext):
        self.ctx = ctx
        super().__init__()

    def setup_cycle(self, info: AnimInfo):
        def on_cycle_complete():
            if random.random() < 0.1:
                self.idle()

        cycle_duration = len(info.frames) / info.fps
        cycle_textures_until(self.ctx.figure, textures=info.frames, frames_per_second=info.fps, tag="enemy")
        callback_until(
            self.ctx.figure,
            callback=on_cycle_complete,
            condition=infinite,
            seconds_between_calls=cycle_duration,
            tag="enemy",
        )

    def on_enter_idle(self):
        print("on_enter_idle")
        self.setup_cycle(self.ctx.figure.state_info["Idle"])

    def on_exit_idle(self):
        print("on_exit_idle")
        Action.stop_actions_for_target(self.ctx.figure, "enemy")

    def on_enter_idle_2(self):
        print("on_enter_idle2")
        self.setup_cycle(self.ctx.figure.state_info["Idle_2"])

    def on_exit_idle_2(self):
        print("on_exit_idle2")
        Action.stop_actions_for_target(self.ctx.figure, "enemy")


class AmazonFighter(BaseAmazon):
    """Player-controlled Amazon."""

    PLAYER_ANIM_INFO = {
        "Attack_1": AnimInfo(fps=10, frame_count=6),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=3),
        "Idle": AnimInfo(fps=3, frame_count=6),
        "Idle_2": AnimInfo(fps=6, frame_count=6),
        "Jump": AnimInfo(fps=10, frame_count=11),
        "Run": AnimInfo(fps=10, frame_count=10),
        "Special": AnimInfo(fps=10, frame_count=6),
        "Walk": AnimInfo(fps=10, frame_count=10),
    }

    def __init__(self, scale: float = 1.0):
        super().__init__(self.PLAYER_ANIM_INFO, PLAYER_ASSETS_ROOT, scale)
        self.left = False
        self.right = False
        self.jump = False
        self.want_jump = False
        self.want_attack = False
        self.ctx = DuelContext(self)
        self.state_machine = PlayerStateMachine(self.ctx)

    def grounded(self) -> bool:
        return abs(self.center_y - 64) < 1

    def want_jump(self) -> bool:
        return self._want_jump and self.grounded()

    def want_attack(self) -> bool:
        return self._want_attack

    def is_moving(self) -> bool:
        return self.change_x != 0

    def is_idle(self) -> bool:
        return not self.is_moving() and not self.want_jump() and not self.want_attack() and self.grounded()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def on_input(self, key: int, pressed: bool):
        sm = self.state_machine
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            if pressed and sm.idle.is_active:
                sm.run()
            elif not pressed and sm.run.is_active:
                sm.idle()
        elif key == arcade.key.SPACE and pressed and self.grounded:
            sm.jump()
        elif key == arcade.key.LCTRL and pressed:
            sm.attack()


class AmazonEnemy(BaseAmazon):
    """Simple AI that cycles through the same states."""

    ENEMY_ANIM_INFO = {
        "Attack_1": AnimInfo(fps=10, frame_count=5),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=4),
        "Idle": AnimInfo(fps=10, frame_count=6),
        "Idle_2": AnimInfo(fps=6, frame_count=5),
        "Jump": AnimInfo(fps=10, frame_count=11),
        "Run": AnimInfo(fps=10, frame_count=10),
        "Special": AnimInfo(fps=10, frame_count=5),
        "Walk": AnimInfo(fps=10, frame_count=10),
    }

    def __init__(self, scale: float = 1.0):
        super().__init__(self.ENEMY_ANIM_INFO, ENEMY_ASSETS_ROOT, scale, flip_vertical=True)
        self.ctx = DuelContext(self)
        self.state_machine = EnemyStateMachine(self.ctx)


# ---------------------------------------------------------------------------
# Main View / Application
# ---------------------------------------------------------------------------
class DuelView(arcade.View):
    def __init__(self):
        super().__init__()
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

    def on_show_view(self):
        arcade.set_background_color(BACKGROUND_COLOR)
        self.setup()

    def setup(self):
        figure_scale = 2
        player = AmazonFighter(scale=figure_scale)
        player.center_x = SCREEN_WIDTH // 4
        player.center_y = 66 * figure_scale
        self.player_list.append(player)

        enemy = AmazonEnemy(scale=figure_scale)
        enemy.center_x = 3 * SCREEN_WIDTH // 4
        enemy.center_y = 66 * figure_scale
        self.enemy_list.append(enemy)

    # ------------------------------------------------------------------
    # Input → delegate to player
    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()
        if self.player_list:
            self.player_list[0].on_input(key, True)

    def on_key_release(self, key, modifiers):
        if len(self.player_list):
            self.player_list[0].on_input(key, False)

    # ------------------------------------------------------------------
    # Update / Draw
    # ------------------------------------------------------------------
    def on_update(self, dt):
        Action.update_all(dt)
        self.player_list.update(dt)
        self.enemy_list.update(dt)

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.enemy_list.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, visible=False)
    center_window(window)
    window.set_visible(True)
    window.show_view(DuelView())
    arcade.run()


if __name__ == "__main__":
    main()
