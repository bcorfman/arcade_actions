"""Amazon State-Machine Demo (1-on-1)

This minimal example shows how to drive both a player sprite and an AI-controlled
enemy sprite using the `StateMachine` helper from ArcadeActions.  Each sprite
shares the same six high-level states (Idle, Run, Jump, Attack, Hurt, Dead) but
transitions are triggered differently:

• AmazonFighter (player) - keyboard input & collisions
• AmazonEnemy            - internal timers & distance checks

"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import arcade
from statemachine import State, StateMachine

from actions import Action, CycleTexturesUntil, DelayUntil, StateMachine, center_window, duration

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
        (128, 128),
        1,
        info.frame_count,
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
        super().__init__(self.state_info["Idle"].frames[0], scale=scale, hit_box_algorithm="None")

        # StateMachine
        self.machine = self._setup_states()

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


class AmazonStateMachine(StateMachine):
    idle = State(initial=True)
    idle_2 = State()

    cycle = idle.to(idle_2) | idle_2.to(idle)

    def __init__(self, sprite: AmazonFighter):
        super().__init__()
        self.sprite = sprite

    def on_enter_idle(self):
        self.sprite.play_animation("Idle")

    def on_enter_idle_2(self):
        self.sprite.play_animation("Idle_2")


class AmazonFighter(BaseAmazon):
    """Player-controlled Amazon."""

    PLAYER_ANIM_INFO = {
        "Attack_1": AnimInfo(fps=10, frame_count=6),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=3),
        "Idle": AnimInfo(fps=3, frame_count=6),
        "Idle_2": AnimInfo(fps=3, frame_count=6),
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

    def _setup_states(self):
        states = [
            ("Attack_1", lambda: DelayUntil(duration(1.0))),
            ("Attack_2", lambda: DelayUntil(duration(1.0))),
            ("Dead", lambda: DelayUntil(duration(1.0))),
            ("Hurt", lambda: DelayUntil(duration(1.0))),
            (
                "Idle",
                lambda: CycleTexturesUntil(
                    textures=self.PLAYER_ANIM_INFO["Idle"].frames, frames_per_second=self.PLAYER_ANIM_INFO["Idle"].fps
                ),
            ),
            (
                "Idle_2",
                lambda: CycleTexturesUntil(
                    textures=self.PLAYER_ANIM_INFO["Idle_2"].frames,
                    frames_per_second=self.PLAYER_ANIM_INFO["Idle_2"].fps,
                ),
            ),
            ("Jump", lambda: DelayUntil(duration(1.0))),
            ("Run", lambda: DelayUntil(duration(1.0))),
            ("Special", lambda: DelayUntil(duration(1.0))),
            ("Walk", lambda: DelayUntil(duration(1.0))),
        ]
        self.machine = StateMachine(states)

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
        m = self.machine
        if key == arcade.key.LEFT:
            if pressed and m.state == "Idle":
                m.change_state("Run")
            elif not pressed and m.state == "Run":
                m.change_state("Idle")
        elif key == arcade.key.RIGHT:
            self.change_x = self.SPEED if pressed else 0
            if pressed and m.state == "Idle":
                m.change_state("Run")
            elif not pressed and m.state == "Run":
                m.change_state("Idle")
        elif key == arcade.key.SPACE and pressed and self.grounded:
            m.change_state("Jump")
        elif key == arcade.key.LCTRL and pressed:
            m.change_state("Attack")

    def update(self, delta_time: float):
        super().update(delta_time)


class AmazonEnemy(BaseAmazon):
    """Simple AI that cycles through the same states."""

    ENEMY_ANIM_INFO = {
        "Attack_1": AnimInfo(fps=10, frame_count=5),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=4),
        "Idle": AnimInfo(fps=10, frame_count=6),
        "Idle_2": AnimInfo(fps=10, frame_count=5),
        "Jump": AnimInfo(fps=10, frame_count=11),
        "Run": AnimInfo(fps=10, frame_count=10),
        "Special": AnimInfo(fps=10, frame_count=5),
        "Walk": AnimInfo(fps=10, frame_count=10),
    }

    def __init__(self, scale: float = 1.0):
        super().__init__(self.ENEMY_ANIM_INFO, ENEMY_ASSETS_ROOT, scale, flip_vertical=True)

    def _setup_states(self):
        states = [
            ("Attack_1", DelayUntil(duration(1.0))),
            ("Attack_2", DelayUntil(duration(1.0))),
            ("Dead", DelayUntil(duration(1.0))),
            ("Hurt", DelayUntil(duration(1.0))),
            (
                "Idle",
                CycleTexturesUntil(
                    textures=self.ENEMY_ANIM_INFO["Idle"].frames,
                    frames_per_second=self.ENEMY_ANIM_INFO["Idle"].fps,
                ),
            ),
            (
                "Idle_2",
                CycleTexturesUntil(
                    textures=self.ENEMY_ANIM_INFO["Idle_2"].frames,
                    frames_per_second=self.ENEMY_ANIM_INFO["Idle_2"].fps,
                ),
            ),
            ("Jump", DelayUntil(duration(1.0))),
            ("Run", DelayUntil(duration(1.0))),
            ("Special", DelayUntil(duration(1.0))),
            ("Walk", DelayUntil(duration(1.0))),
        ]
        return StateMachine(states)

    def update(self, delta_time: float):
        super().update(delta_time)


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
        if len(self.player_list):
            self.player_list[0].on_input(key, True)

    def on_key_release(self, key, modifiers):
        if len(self.player_list):
            self.player_list[0].on_input(key, False)

    # ------------------------------------------------------------------
    # Update / Draw
    # ------------------------------------------------------------------
    def on_update(self, dt):
        Action.update_all(dt)
        if self.player_list:
            self.player_list.update(dt)
        if self.enemy_list:
            self.enemy_list.update(dt)

    def on_draw(self):
        self.clear()
        if self.player_list:
            self.player_list.draw()
        if self.enemy_list:
            self.enemy_list.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, visible=False)
    center_window(window)
    window.set_visible(True)
    window.show_view(DuelView())
    arcade.run()


if __name__ == "__main__":
    main()
