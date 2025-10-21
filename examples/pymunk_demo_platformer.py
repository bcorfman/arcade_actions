"""
PyMunk Platformer - State Machine Pattern (amazon-warriors style)

Demonstrates zero state flags using python-statemachine as single source of truth.
- InputState: Clean @dataclass for input (amazon-warriors pattern)
- PlayerAnimationState: State machine with guard conditions and named events
- Physics and animation cleanly separated

Prerequisites: uv add python-statemachine
Run with: uv run python examples/pymunk_demo_platformer.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import arcade
from statemachine import State, StateMachine

from actions import Action
from actions.conditional import infinite
from actions.helpers import cycle_textures_until, move_until

# Window settings
SCREEN_TITLE = "PyMunk Platformer with ArcadeActions and python-statemachine"
SPRITE_IMAGE_SIZE = 128
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_TILES = 0.5
SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 15
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

# Physics constants
GRAVITY = 1500
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6
PLAYER_MASS = 2.0
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600
PLAYER_MOVE_FORCE_ON_GROUND = 8000
PLAYER_MOVE_FORCE_IN_AIR = 900
PLAYER_JUMP_IMPULSE = 1800
BULLET_MOVE_FORCE = 4500
BULLET_MASS = 0.1
BULLET_GRAVITY = 300

# Animation constants
DEAD_ZONE = 0.1
RIGHT_FACING = 1  # Facing right (positive direction)
LEFT_FACING = -1  # Facing left (negative direction)
DISTANCE_TO_CHANGE_TEXTURE = 20  # Pixels to move before changing walk texture


@dataclass
class InputState:
    """Input state container (amazon-warriors pattern)."""

    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False
    shift: bool = False
    direction: int = RIGHT_FACING

    @property
    def moving(self) -> bool:
        """True if any horizontal movement key is pressed."""
        return self.left or self.right

    @property
    def horizontal_input(self) -> int:
        """Net horizontal input: -1 (left), 0 (none), or 1 (right)."""
        if self.left and not self.right:
            return -1
        elif self.right and not self.left:
            return 1
        return 0

    @property
    def vertical_input(self) -> int:
        """Net vertical input: -1 (down), 0 (none), or 1 (up)."""
        if self.up and not self.down:
            return 1
        elif self.down and not self.up:
            return -1
        return 0


class PlayerAnimationState(StateMachine):
    """State machine for player animation (single source of truth - no state flags)."""

    idle = State(initial=True)
    walk = State()
    jump = State()
    fall = State()
    climb = State()

    # Movement transitions (input + physics based)
    movement = (
        idle.to(walk, cond="moving and on_ground and not climbing")
        | walk.to(idle, cond="not moving and on_ground and not climbing")
        | idle.to(climb, cond="climbing")
        | walk.to(climb, cond="climbing")
        | jump.to(climb, cond="climbing")
        | fall.to(climb, cond="climbing")
        | climb.to(walk, cond="moving and on_ground and not climbing")
        | climb.to(idle, cond="not moving and on_ground and not climbing")
        | climb.to(fall, cond="not climbing and not on_ground")
    )

    # Jump transitions (triggered on key press)
    jump_action = idle.to(jump, cond="on_ground and not climbing") | walk.to(jump, cond="on_ground and not climbing")

    # Physics-driven transitions (automatic)
    physics_update = (
        jump.to(climb, cond="on_ladder and not on_ground")
        | fall.to(climb, cond="on_ladder and not on_ground")
        | jump.to(fall, cond="falling")
        | fall.to(idle, cond="on_ground and not moving")
        | fall.to(walk, cond="on_ground and moving")
    )

    def __init__(self, player: PlayerSprite, input_state: InputState, physics_engine: arcade.PymunkPhysicsEngine):
        self.player = player
        self.input = input_state
        self.physics = physics_engine
        super().__init__()
        self.allow_event_without_transition = True

    # Guards
    @property
    def moving(self) -> bool:
        return self.input.moving

    @property
    def on_ground(self) -> bool:
        try:
            return self.physics.is_on_ground(self.player)
        except (KeyError, AttributeError):
            return False

    @property
    def on_ladder(self) -> bool:
        return len(arcade.check_for_collision_with_list(self.player, self.player.ladder_list)) > 0

    @property
    def climbing(self) -> bool:
        return self.on_ladder and not self.on_ground

    @property
    def falling(self) -> bool:
        return self.player.last_dy < -DEAD_ZONE

    def _tex_idx(self) -> int:
        return 0 if self.input.direction == RIGHT_FACING else 1

    def on_enter_idle(self):
        self.player.texture = self.player.idle_texture_pair[self._tex_idx()]

    def on_enter_walk(self):
        textures = [pair[self._tex_idx()] for pair in self.player.walk_textures]
        cycle_textures_until(self.player, textures=textures, frames_per_second=10.0, tag="animation")

    def on_enter_jump(self):
        self.player.texture = self.player.jump_texture_pair[self._tex_idx()]
        # Apply jump impulse when entering jump state
        self.physics.apply_impulse(self.player, (0, PLAYER_JUMP_IMPULSE))

    def on_enter_fall(self):
        self.player.texture = self.player.fall_texture_pair[self._tex_idx()]

    def on_enter_climb(self):
        # Start idle climbing texture; animation starts automatically when vertical input is non-zero
        self.player.texture = self.player.climbing_textures[0]

    # Stop animation when leaving walk/climb so texture stays on last frame until next state sets it.
    def on_exit_walk(self):
        Action.stop_actions_for_target(self.player, tag="animation")

    def on_exit_climb(self):
        Action.stop_actions_for_target(self.player, tag="animation")

    def apply_physics_forces(self):
        """Apply movement forces based on input (called from update loop)."""
        is_on_ground = self.on_ground
        horizontal = self.input.horizontal_input
        vertical = self.input.vertical_input

        if horizontal != 0:
            force_magnitude = (
                PLAYER_MOVE_FORCE_ON_GROUND if (is_on_ground or self.player.is_on_ladder) else PLAYER_MOVE_FORCE_IN_AIR
            )
            self.physics.apply_force(self.player, (horizontal * force_magnitude, 0))
            self.physics.set_friction(self.player, 0)
        elif vertical != 0 and self.player.is_on_ladder:
            self.physics.apply_force(self.player, (0, vertical * PLAYER_MOVE_FORCE_ON_GROUND))
            self.physics.set_friction(self.player, 0)
        else:
            self.physics.set_friction(self.player, 1.0)

        # Handle climb animation start/stop based on vertical input
        if self.current_state == self.climb:
            if vertical != 0:
                if not Action.get_actions_for_target(self.player, tag="animation"):
                    cycle_textures_until(
                        self.player,
                        textures=self.player.climbing_textures,
                        frames_per_second=6.0,
                        tag="animation",
                    )
            else:
                Action.stop_actions_for_target(self.player, tag="animation")


class PlayerSprite(arcade.Sprite):
    """Player sprite with animation state machine."""

    def __init__(
        self, ladder_list: arcade.SpriteList, input_state: InputState, physics_engine: arcade.PymunkPhysicsEngine
    ):
        super().__init__(scale=SPRITE_SCALING_PLAYER)

        # Load textures
        main_path = ":resources:images/animated_characters/female_person/femalePerson"
        idle_texture = arcade.load_texture(f"{main_path}_idle.png", hit_box_algorithm=arcade.hitbox.algo_detailed)
        jump_texture = arcade.load_texture(f"{main_path}_jump.png")
        fall_texture = arcade.load_texture(f"{main_path}_fall.png")

        self.idle_texture_pair = idle_texture, idle_texture.flip_left_right()
        self.jump_texture_pair = jump_texture, jump_texture.flip_left_right()
        self.fall_texture_pair = fall_texture, fall_texture.flip_left_right()

        self.walk_textures = []
        for i in range(8):
            texture = arcade.load_texture(f"{main_path}_walk{i}.png")
            self.walk_textures.append((texture, texture.flip_left_right()))

        self.climbing_textures = [
            arcade.load_texture(f"{main_path}_climb0.png"),
            arcade.load_texture(f"{main_path}_climb1.png"),
        ]

        self.texture = self.idle_texture_pair[0]
        self.ladder_list = ladder_list

        # Animation tracking
        self.last_dy = 0.0

        # State machine (single source of truth)
        self.animation_state = PlayerAnimationState(self, input_state, physics_engine)

    @property
    def is_on_ladder(self) -> bool:
        """True if touching a ladder (used by physics for vertical movement)."""
        return len(arcade.check_for_collision_with_list(self, self.ladder_list)) > 0

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """Physics callback: update ladder physics and distance-based animations."""
        # Ladder physics: zero gravity when touching ladder
        self.last_dy = dy

        on_ladder = self.is_on_ladder
        if on_ladder:
            if self.pymunk.gravity != (0, 0):
                self.pymunk.gravity = (0, 0)
                self.pymunk.damping = 0.0001
                self.pymunk.max_vertical_velocity = PLAYER_MAX_HORIZONTAL_SPEED
        else:
            if self.pymunk.gravity == (0, 0):
                self.pymunk.damping = 1.0
                self.pymunk.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
                self.pymunk.gravity = None

        # Animation is handled by CycleTexturesUntil actions – no manual odometer logic

        # Trigger state transitions (climb first, then jump/fall)
        self.animation_state.movement()
        if not self.animation_state.climbing:
            self.animation_state.physics_update()

    def fire_bullet(
        self,
        target_x: float,
        target_y: float,
        bullet_list: arcade.SpriteList,
        physics_engine: arcade.PymunkPhysicsEngine,
    ):
        """Fire a bullet toward the target position."""
        bullet = BulletSprite(width=20, height=5, color=arcade.color.DARK_YELLOW)
        bullet_list.append(bullet)
        bullet.position = self.position

        x_diff = target_x - self.center_x
        y_diff = target_y - self.center_y
        angle = math.atan2(y_diff, x_diff)

        size = max(self.width, self.height) / 2
        bullet.center_x += size * math.cos(angle)
        bullet.center_y += size * math.sin(angle)
        bullet.angle = math.degrees(angle)

        physics_engine.add_sprite(
            bullet,
            mass=BULLET_MASS,
            damping=1.0,
            friction=0.6,
            collision_type="bullet",
            gravity=(0, -BULLET_GRAVITY),
            elasticity=0.9,
        )

        physics_engine.apply_force(bullet, (BULLET_MOVE_FORCE, 0))


class BulletSprite(arcade.SpriteSolidColor):
    """Simple bullet sprite that removes itself when off-screen."""

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        if self.center_y < -100:
            self.remove_from_sprite_lists()


class GameWindow(arcade.Window):
    """Main game window with state machine pattern."""

    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        self.player_sprite: PlayerSprite | None = None
        self.player_list: arcade.SpriteList | None = None
        self.wall_list: arcade.SpriteList | None = None
        self.bullet_list: arcade.SpriteList | None = None
        self.item_list: arcade.SpriteList | None = None
        self.moving_sprites_list: arcade.SpriteList | None = None
        self.ladder_list: arcade.SpriteList | None = None

        self.input_state = InputState()
        self.physics_engine: arcade.PymunkPhysicsEngine | None = None
        self.background_color = arcade.color.AMAZON

    def setup(self):
        """Initialize the game with physics and sprites."""
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        map_name = ":resources:/tiled_maps/pymunk_test_map.json"
        tile_map = arcade.load_tilemap(map_name, SPRITE_SCALING_TILES)

        self.wall_list = tile_map.sprite_lists["Platforms"]
        self.item_list = tile_map.sprite_lists["Dynamic Items"]
        self.ladder_list = tile_map.sprite_lists["Ladders"]
        self.moving_sprites_list = tile_map.sprite_lists["Moving Platforms"]

        self.physics_engine = arcade.PymunkPhysicsEngine(damping=DEFAULT_DAMPING, gravity=(0, -GRAVITY))

        self.player_sprite = PlayerSprite(self.ladder_list, self.input_state, self.physics_engine)
        self.player_sprite.center_x = SPRITE_SIZE * 1.5
        self.player_sprite.center_y = SPRITE_SIZE * 1.5
        self.player_list.append(self.player_sprite)

        # Collision handlers
        def wall_hit_handler(bullet_sprite, _wall_sprite, _arbiter, _space, _data):
            bullet_sprite.remove_from_sprite_lists()

        def item_hit_handler(bullet_sprite, item_sprite, _arbiter, _space, _data):
            bullet_sprite.remove_from_sprite_lists()
            item_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("bullet", "wall", post_handler=wall_hit_handler)
        self.physics_engine.add_collision_handler("bullet", "item", post_handler=item_hit_handler)

        # Add player to physics
        self.physics_engine.add_sprite(
            self.player_sprite,
            friction=PLAYER_FRICTION,
            mass=PLAYER_MASS,
            moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
            collision_type="player",
            max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
            max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED,
        )

        # Add walls (static)
        self.physics_engine.add_sprite_list(
            self.wall_list, friction=WALL_FRICTION, collision_type="wall", body_type=arcade.PymunkPhysicsEngine.STATIC
        )

        # Add dynamic items
        self.physics_engine.add_sprite_list(self.item_list, friction=DYNAMIC_ITEM_FRICTION, collision_type="item")

        # Add moving platforms (kinematic)
        self.physics_engine.add_sprite_list(self.moving_sprites_list, body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

        # Apply MoveUntil actions to moving platforms with bounce
        for sprite in self.moving_sprites_list:
            # Use sprite's initial change_x/change_y as velocity and boundaries from map
            velocity = (sprite.change_x, sprite.change_y)
            # bounds format: (left, bottom, right, top)
            bounds = (
                sprite.boundary_left if sprite.boundary_left is not None else float("-inf"),
                sprite.boundary_bottom if sprite.boundary_bottom is not None else float("-inf"),
                sprite.boundary_right if sprite.boundary_right is not None else float("inf"),
                sprite.boundary_top if sprite.boundary_top is not None else float("inf"),
            )

            move_until(sprite, velocity=velocity, condition=infinite, boundary_behavior="bounce", bounds=bounds)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.input_state.left = True
            self.input_state.direction = LEFT_FACING
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.input_state.right = True
            self.input_state.direction = RIGHT_FACING
        elif key in (arcade.key.UP, arcade.key.W):
            self.input_state.up = True
            self.player_sprite.animation_state.jump_action()
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.input_state.down = True
        elif key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.input_state.shift = True
        self.player_sprite.animation_state.movement()

    def on_key_release(self, key, modifiers):
        """Handle key releases (amazon-warriors pattern: update state, trigger events)."""
        if key in (arcade.key.LEFT, arcade.key.A):
            self.input_state.left = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.input_state.right = False
        elif key in (arcade.key.UP, arcade.key.W):
            self.input_state.up = False
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.input_state.down = False
        elif key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.input_state.shift = False
        self.player_sprite.animation_state.movement()

    def on_mouse_press(self, x, y, button, modifiers):
        """Fire bullet (delegate to player sprite)."""
        self.player_sprite.fire_bullet(x, y, self.bullet_list, self.physics_engine)

    def on_update(self, delta_time):
        """Update game logic and physics."""
        # State machine handles all movement forces
        self.player_sprite.animation_state.apply_physics_forces()

        # Action.update_all automatically syncs kinematic sprites to physics engine
        Action.update_all(delta_time, physics_engine=self.physics_engine)
        self.physics_engine.step()

    def on_draw(self):
        """Render the game."""
        self.clear()
        self.wall_list.draw()
        self.ladder_list.draw()
        self.moving_sprites_list.draw()
        self.bullet_list.draw()
        self.item_list.draw()
        self.player_list.draw()


def main():
    """Run the demo."""
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
