import argparse
import random
from abc import ABC, abstractmethod
from collections.abc import Callable

import arcade

from actions import Action, arrange_grid, center_window, infinite, move_until, set_debug_actions

HILL_WIDTH = 512
HILL_HEIGHT = 57
WINDOW_WIDTH = HILL_WIDTH * 2
WINDOW_HEIGHT = 432
HILL_SLICES = ["./res/hill_slice1.png", "./res/hill_slice2.png", "./res/hill_slice3.png", "./res/hill_slice4.png"]
SHIP = "./res/dart.png"
PLAYER_SHOT = ":resources:/images/space_shooter/laserRed01.png"
PLAYER_SHIP_VERT = 5
PLAYER_SHIP_HORIZ = 8
PLAYER_SHIP_FIRE_SPEED = 15
WALL_WIDTH = 200
TUNNEL_VELOCITY = -3
TOP_BOUNDS = (-HILL_WIDTH, WINDOW_HEIGHT // 2, HILL_WIDTH * 5, WINDOW_HEIGHT)
BOTTOM_BOUNDS = (
    -HILL_WIDTH,
    0,
    HILL_WIDTH * 5,
    WINDOW_HEIGHT // 2,
)
TUNNEL_WALL_HEIGHT = 50
TUNNEL_WALL_COLOR = (141, 65, 8)
SHIP_LEFT_BOUND = HILL_WIDTH // 4
SHIP_RIGHT_BOUND = WINDOW_WIDTH - HILL_WIDTH / 1.5


# sprite creation functions
def _create_tunnel_wall(left, top):
    wall = arcade.SpriteSolidColor(WINDOW_WIDTH, TUNNEL_WALL_HEIGHT, color=TUNNEL_WALL_COLOR)
    wall.left = left
    wall.top = top
    return wall


def _create_sprite_at_location(file_or_texture, **kwargs):
    sprite = arcade.Sprite(file_or_texture)
    if kwargs.get("left") is not None and kwargs.get("top") is not None:
        sprite.left = kwargs.get("left")
        sprite.top = kwargs.get("top")
    elif kwargs.get("center_x") is not None and kwargs.get("center_y") is not None:
        sprite.center_x = kwargs.get("center_x")
        sprite.center_y = kwargs.get("center_y")
    return sprite


# Hill collision detection and response
def _handle_hill_collision(sprite, collision_lists, register_damage: Callable[[float], None]):
    """Handle collision with hills by adjusting position and providing visual feedback."""
    collision_hit = arcade.check_for_collision_with_lists(sprite, collision_lists)
    if not collision_hit:
        return False

    # Compute minimum translation vector to resolve all overlaps
    min_overlap = None
    mtv_axis = None  # "x" or "y"

    for collision_sprite in collision_hit:
        dx = sprite.center_x - collision_sprite.center_x
        dy = sprite.center_y - collision_sprite.center_y

        overlap_x = (sprite.width / 2 + collision_sprite.width / 2) - abs(dx)
        overlap_y = (sprite.height / 2 + collision_sprite.height / 2) - abs(dy)

        # Skip if somehow not overlapping (shouldn't happen given collision detection)
        if overlap_x <= 0 or overlap_y <= 0:
            continue

        # Choose axis with smaller overlap to resolve
        if overlap_x < overlap_y:
            if min_overlap is None or overlap_x < min_overlap:
                min_overlap = overlap_x
                mtv_axis = ("x", 1 if dx > 0 else -1)
        else:
            if min_overlap is None or overlap_y < min_overlap:
                min_overlap = overlap_y
                mtv_axis = ("y", 1 if dy > 0 else -1)

    # Always push vertically away from screen center
    # Determine direction: up (1) if in bottom half, down (-1) if in top half
    screen_mid = WINDOW_HEIGHT / 2
    vertical_dir = 1 if sprite.center_y < screen_mid else -1

    # Determine minimal vertical overlap among collisions to move the sprite out
    min_vertical_overlap = None
    for collision_sprite in collision_hit:
        dy = sprite.center_y - collision_sprite.center_y
        overlap_y = (sprite.height / 2 + collision_sprite.height / 2) - abs(dy)
        if overlap_y > 0:
            if min_vertical_overlap is None or overlap_y < min_vertical_overlap:
                min_vertical_overlap = overlap_y

    # Fallback small nudge if calculation failed (shouldn't happen)
    if min_vertical_overlap is None:
        min_vertical_overlap = sprite.height / 2

    sprite.center_y += vertical_dir * (min_vertical_overlap + 1)
    sprite.change_y = 0

    # Visual damage feedback - flash background
    register_damage(0.3)

    return True


class WaveContext:
    """
    Read-only bundle of objects a wave may need.

    Nothing here is specific to any particular wave pattern.
    """

    __slots__ = ("shot_list", "player_ship", "register_damage", "on_cleanup")

    def __init__(
        self,
        *,
        shot_list: arcade.SpriteList,
        player_ship: arcade.Sprite,
        register_damage: Callable[[float], None],
        on_cleanup: Callable[["EnemyWave"], None],
    ):
        self.shot_list = shot_list
        self.player_ship = player_ship
        self.register_damage = register_damage
        self.on_cleanup = on_cleanup


class EnemyWave(ABC):
    """
    Behaviour strategy for a wave.

    A wave owns NO sprites—it receives the SpriteList that Tunnel created.
    """

    @property
    @abstractmethod
    def actions(self) -> list[Action]:
        """Return a list of actions that are currently active for this wave."""
        pass

    @abstractmethod
    def build(self, sprites: arcade.SpriteList, ctx: WaveContext) -> None:
        """Populate *sprites* and add actions (move_until, etc.)."""
        pass

    @abstractmethod
    def update(self, sprites: arcade.SpriteList, ctx: WaveContext, dt: float) -> None:
        """Per-frame logic (collision tests, win/loss checks)."""
        pass


def _make_shield(width):
    """Create shield blocks"""

    def _make_shield_block() -> arcade.Sprite:
        """Factory that creates a single shield block sprite."""
        return arcade.SpriteSolidColor(10, 12, color=arcade.color.GRAY)

    # Build shield by creating a small grid of blocks
    shield_grid = arrange_grid(
        rows=30,
        cols=width,
        start_x=WINDOW_WIDTH + WALL_WIDTH,
        start_y=TUNNEL_WALL_HEIGHT,  # Position shields between player and enemies
        spacing_x=10,
        spacing_y=12,
        sprite_factory=_make_shield_block,
    )
    return shield_grid


class DensePackWave(EnemyWave):
    def __init__(self, wall_width: int):
        self._width = wall_width
        self._actions = []

    @property
    def actions(self) -> list[Action]:
        """Return a list of actions that are currently active for this wave."""
        return self._actions

    def build(self, sprites: arcade.SpriteList, ctx: WaveContext) -> None:
        """Populate enemy sprites and add actions (move_until, etc.)."""
        shield = _make_shield(self._width)
        sprites.extend(shield)

        # Use the player's current speed factor to set initial velocity
        current_velocity = TUNNEL_VELOCITY * ctx.player_ship.speed_factor

        action = move_until(
            sprites,
            velocity=(current_velocity, 0),
            condition=infinite,
            bounds=(
                -WALL_WIDTH,
                0,
                WINDOW_WIDTH + WALL_WIDTH + WALL_WIDTH,
                WINDOW_HEIGHT,
            ),
            boundary_behavior="limit",
            on_boundary_enter=lambda sprite, axis, side: ctx.on_cleanup(self),
            tag="shield_move",
        )
        self._actions.append(action)

    def update(self, sprites: arcade.SpriteList, ctx: WaveContext, dt: float) -> None:
        """Per-frame logic (collision tests, win/loss checks)."""
        # Handle collisions between player shots and the dense pack sprites
        if not sprites:
            return

        # Shot collisions
        for shot in tuple(ctx.shot_list):
            hits = arcade.check_for_collision_with_list(shot, sprites)
            if hits:
                shot.remove_from_sprite_lists()
                for block in hits:
                    block.remove_from_sprite_lists()

        # Player collisions
        if arcade.check_for_collision_with_list(ctx.player_ship, sprites):
            ctx.register_damage(0.3)
            ctx.on_cleanup(self)
            return

        # Wave complete?
        if len(sprites) == 0:
            ctx.on_cleanup(self)


class ThinDensePackWave(DensePackWave):
    def __init__(self):
        super().__init__(wall_width=5)


class ThickDensePackWave(DensePackWave):
    def __init__(self):
        super().__init__(wall_width=10)


class PlayerContext:
    """
    Read-only bundle of objects a PlayerShip may need.

    Nothing here is specific to any particular player behavior.
    """

    __slots__ = ("shot_list", "hill_tops", "hill_bottoms", "tunnel_walls", "set_tunnel_velocity", "register_damage")

    def __init__(
        self,
        *,
        shot_list: arcade.SpriteList,
        hill_tops: arcade.SpriteList,
        hill_bottoms: arcade.SpriteList,
        tunnel_walls: arcade.SpriteList,
        set_tunnel_velocity: Callable[[float], None],
        register_damage: Callable[[float], None],
    ):
        self.shot_list = shot_list
        self.hill_tops = hill_tops
        self.hill_bottoms = hill_bottoms
        self.tunnel_walls = tunnel_walls
        self.set_tunnel_velocity = set_tunnel_velocity
        self.register_damage = register_damage


class PlayerShip(arcade.Sprite):
    LEFT = -1
    RIGHT = 1

    def __init__(self, ctx: PlayerContext, *, behaviour: Callable[["PlayerShip", float], None] | None = None):
        super().__init__(SHIP, center_x=HILL_WIDTH // 4, center_y=WINDOW_HEIGHT // 2)
        self.ctx = ctx
        self.right_texture = arcade.load_texture(SHIP)
        self.left_texture = self.right_texture.flip_left_right()
        self.texture_red_laser = arcade.load_texture(":resources:images/space_shooter/laserRed01.png").rotate_90()
        self.speed_factor = 1
        self.direction = self.RIGHT
        self.behaviour = behaviour  # Optional AI/attract mode behaviour

        # Input state for velocity provider
        self._input = {"left": False, "right": False, "up": False, "down": False}

        def velocity_provider():
            # Manual control takes priority
            h = 0
            v = 0

            if self._input["right"] and not self._input["left"]:
                h = PLAYER_SHIP_HORIZ
            elif self._input["left"] and not self._input["right"]:
                h = -PLAYER_SHIP_HORIZ

            if self._input["up"] and not self._input["down"]:
                v = PLAYER_SHIP_VERT
            elif self._input["down"] and not self._input["up"]:
                v = -PLAYER_SHIP_VERT

            if h or v:
                # Respect left boundary: no further left when already at edge
                if h < 0 and self.left <= SHIP_LEFT_BOUND:
                    h = 0
                return (h, v)

            # Drift when idle: same as tunnel, unless at left wall
            if self.left <= SHIP_LEFT_BOUND:
                return (0, 0)
            return (TUNNEL_VELOCITY, 0)

        def on_boundary_enter(sprite, axis, side):
            if axis == "x" and side == "right":
                self.speed_factor = 2
                self.ctx.set_tunnel_velocity(TUNNEL_VELOCITY * self.speed_factor)

        def on_boundary_exit(sprite, axis, side):
            if axis == "x" and side == "right":
                self.speed_factor = 1
                self.ctx.set_tunnel_velocity(TUNNEL_VELOCITY)

        # Single long-lived action for all movement
        move_until(
            self,
            velocity=(0, 0),  # ignored when velocity_provider is present
            condition=infinite,
            bounds=(SHIP_LEFT_BOUND, TUNNEL_WALL_HEIGHT, SHIP_RIGHT_BOUND, WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT),
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
            tag="player_move",
        )

    def move(self, left_pressed, right_pressed, up_pressed, down_pressed):
        # Simply update input state - velocity_provider handles the rest
        self._input.update(left=left_pressed, right=right_pressed, up=up_pressed, down=down_pressed)

        # Update direction and texture for visual feedback
        if right_pressed and not left_pressed:
            self.direction = self.RIGHT
            self.texture = self.right_texture
        elif left_pressed and not right_pressed:
            self.direction = self.LEFT
            self.texture = self.left_texture

        # Always check for hill or wall collisions after movement (whether moving or stationary)
        hill_collision_lists = [self.ctx.hill_tops, self.ctx.hill_bottoms, self.ctx.tunnel_walls]
        if _handle_hill_collision(self, hill_collision_lists, self.ctx.register_damage):
            # Stop current movement if we hit hills
            Action.stop_actions_for_target(self, tag="player_move")

    def fire_when_ready(self):
        can_fire = len(self.ctx.shot_list) == 0
        if can_fire:
            self.setup_shot()
        return can_fire

    def setup_shot(self, angle=0):
        shot = arcade.Sprite()
        shot.texture = self.texture_red_laser
        if self.direction == self.RIGHT:
            shot.left = self.right
        else:
            shot.right = self.left
        shot.center_y = self.center_y
        shot_vel_x = PLAYER_SHIP_FIRE_SPEED * self.direction

        move_until(
            shot,
            velocity=(shot_vel_x, 0),
            condition=self.shot_collision_check,
            on_stop=lambda *_: shot.remove_from_sprite_lists(),
        )
        self.ctx.shot_list.append(shot)

    def shot_collision_check(self):
        # Safeguard: if the shot has already been removed, stop the action.
        if not self.ctx.shot_list:
            return True  # Condition met -> stop action

        shot = self.ctx.shot_list[0]
        off_screen = shot.right < 0 or shot.left > WINDOW_WIDTH
        hills_hit = arcade.check_for_collision_with_lists(shot, [self.ctx.hill_tops, self.ctx.hill_bottoms])
        return {"off_screen": off_screen, "hills_hit": hills_hit} if off_screen or hills_hit else None

    def update(self, delta_time):
        super().update(delta_time)
        # Run AI/attract mode behaviour if present
        if self.behaviour:
            self.behaviour(self, delta_time)


class Tunnel(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.BLACK
        self.player_list = arcade.SpriteList()
        self.shot_list = arcade.SpriteList()
        self.tunnel_walls = arcade.SpriteList()
        self.hill_tops = arcade.SpriteList()
        self.hill_bottoms = arcade.SpriteList()
        self.left_pressed = self.right_pressed = False
        self.up_pressed = self.down_pressed = False
        self.fire_pressed = False
        self.speed_factor = 1
        self.speed = TUNNEL_VELOCITY * self.speed_factor
        self.damage_flash = 0.0  # Visual feedback for hill collisions
        self._wave_sprites = arcade.SpriteList()
        self._wave_strategy: EnemyWave | None = None
        self._hill_top_action = None
        self._hill_bottom_action = None
        self.setup_walls()
        self.setup_hills()
        self.setup_ship()

        # Wave classes that can be instantiated
        self.wave_classes = [ThinDensePackWave, ThickDensePackWave]

        # Create context for waves
        self._ctx = WaveContext(
            shot_list=self.shot_list,
            player_ship=self.ship,
            register_damage=self._flash_damage,
            on_cleanup=self._wave_finished,
        )

        self.set_tunnel_velocity(self.speed)
        self._start_random_wave()

    def _start_random_wave(self):
        if not self.wave_classes:
            return
        self._wave_sprites.clear()
        wave_cls = random.choice(self.wave_classes)
        self._wave_strategy = wave_cls()
        self._wave_strategy.build(self._wave_sprites, self._ctx)

    def _wave_finished(self, wave):
        """Callback when a wave signals it is finished.

        Stops all actions associated with *wave* to ensure they no longer
        run once the wave has been cleaned up.
        """
        # Stop movement actions tied to the current wave's sprite list
        Action.stop_actions_for_target(self._wave_sprites, tag="shield_move")
        # Also stop any extra references kept in the wave's local list (defensive)
        for action in wave.actions:
            action.stop()
        self._wave_strategy = None
        self._start_random_wave()

    def _flash_damage(self, amount: float):
        """Register damage and trigger visual flash effect."""
        self.damage_flash = min(self.damage_flash + amount, 1.0)

    def set_tunnel_velocity(self, speed):
        # Reuse existing actions and adjust velocity instead of recreating
        if self._hill_top_action is None or self._hill_top_action.done:
            self._hill_top_action = move_until(
                self.hill_tops,
                velocity=(speed, 0),
                condition=infinite,
                bounds=TOP_BOUNDS,
                boundary_behavior="wrap",
                on_boundary_enter=self.on_hill_top_wrap,
                tag="tunnel_velocity",
            )
        else:
            self._hill_top_action.set_current_velocity((speed, 0))

        if self._hill_bottom_action is None or self._hill_bottom_action.done:
            self._hill_bottom_action = move_until(
                self.hill_bottoms,
                velocity=(speed, 0),
                condition=infinite,
                bounds=BOTTOM_BOUNDS,
                boundary_behavior="wrap",
                on_boundary_enter=self.on_hill_bottom_wrap,
                tag="tunnel_velocity",
            )
        else:
            self._hill_bottom_action.set_current_velocity((speed, 0))

        if self._wave_strategy and self._wave_strategy.actions is not None:
            for action in self._wave_strategy.actions:
                action.set_current_velocity((speed, 0))

    def on_hill_top_wrap(self, sprite, axis, side):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def on_hill_bottom_wrap(self, sprite, axis, side):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def setup_ship(self):
        player_ctx = PlayerContext(
            shot_list=self.shot_list,
            hill_tops=self.hill_tops,
            hill_bottoms=self.hill_bottoms,
            tunnel_walls=self.tunnel_walls,
            set_tunnel_velocity=self.set_tunnel_velocity,
            register_damage=self._flash_damage,
        )
        self.ship = PlayerShip(player_ctx)
        self.player_list.append(self.ship)

    def setup_walls(self):
        top_wall = _create_tunnel_wall(0, WINDOW_HEIGHT)
        bottom_wall = _create_tunnel_wall(0, TUNNEL_WALL_HEIGHT)
        self.tunnel_walls.append(top_wall)
        self.tunnel_walls.append(bottom_wall)

    def setup_hills(self):
        largest_slice_width = arcade.load_texture(HILL_SLICES[0]).width
        for x in [0, HILL_WIDTH * 2]:
            height_so_far = 0
            for i in range(4):
                hill_slice = arcade.load_texture(HILL_SLICES[i])
                hill_top_slice = _create_sprite_at_location(
                    hill_slice,
                    left=x + (largest_slice_width - hill_slice.width) / 2,
                    top=WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT - height_so_far,
                )
                trim_width = hill_top_slice.right - hill_top_slice.left
                hill_top_slice.left = x + (hill_slice.width - trim_width) / 2
                self.hill_tops.append(hill_top_slice)
                height_so_far += hill_slice.height
                hill_slice = arcade.load_texture(HILL_SLICES[i]).flip_top_bottom()
                hill_bottom_slice = _create_sprite_at_location(
                    hill_slice,
                    left=x + HILL_WIDTH + (largest_slice_width - hill_slice.width) / 2,
                    top=TUNNEL_WALL_HEIGHT + height_so_far,
                )
                hill_bottom_slice.left = x + HILL_WIDTH + (hill_slice.width - trim_width) / 2
                self.hill_bottoms.append(hill_bottom_slice)

    def on_update(self, delta_time: float):
        Action.update_all(delta_time)
        self.tunnel_walls.update()
        self.hill_tops.update()
        self.hill_bottoms.update()
        self.player_list.update()
        self.shot_list.update()
        self._wave_sprites.update()
        if self._wave_strategy:
            self._wave_strategy.update(self._wave_sprites, self._ctx, delta_time)
        self.ship.move(self.left_pressed, self.right_pressed, self.up_pressed, self.down_pressed)
        if self.fire_pressed:
            self.ship.fire_when_ready()

        # Decay damage flash effect
        if self.damage_flash > 0:
            self.damage_flash = max(0, self.damage_flash - delta_time * 5.0)

    def on_draw(self):
        self.background_color = arcade.color.BLACK
        self.clear()
        self._wave_sprites.draw()
        self.tunnel_walls.draw()
        self.hill_tops.draw()
        self.hill_bottoms.draw()
        self.player_list.draw()
        self.shot_list.draw()

        # Draw flash overlay last so it appears over everything
        if self.damage_flash > 0:
            # Create a white overlay using a solid color sprite
            overlay_alpha = int(255 * self.damage_flash)
            arcade.draw_lrbt_rectangle_filled(
                0,
                WINDOW_WIDTH,
                0,
                WINDOW_HEIGHT,
                (255, 255, 255, overlay_alpha),
            )

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.LEFT:
            self.left_pressed = True
            self.right_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            self.left_pressed = False
        if key == arcade.key.UP:
            self.up_pressed = True
            self.down_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = True
            self.up_pressed = False
        if key == arcade.key.LCTRL or modifiers == arcade.key.MOD_CTRL:
            self.fire_pressed = True
        if key == arcade.key.ESCAPE:
            self.window.close()

    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        if key == arcade.key.LCTRL:
            self.fire_pressed = False


class LaserGates(arcade.Window):
    def __init__(self):
        # Create the window hidden so we can move it before it ever appears.
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Laser Gates", visible=False)

        # Center while the window is still invisible to avoid a visible jump.
        center_window(self)

        # Now make the window visible and proceed normally.
        self.set_visible(True)
        self.show_view(Tunnel())

    # center_on_current_screen method removed; logic now in actions.display.center_window


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Laser Gates Game")
    parser.add_argument(
        "--debug-actions",
        action="store_true",
        help="Enable debug output for action creation",
    )
    args = parser.parse_args()

    # Enable debug action logging if requested.
    # Note: environment variable ARCADEACTIONS_DEBUG is applied automatically
    # at import time; this flag only enables additional logging (does not disable).
    if args.debug_actions:
        set_debug_actions(True)

    window = LaserGates()
    arcade.run()


if __name__ == "__main__":
    main()
