import arcade

from actions import Action, center_window, infinite, move_until

HILL_WIDTH = 512
HILL_HEIGHT = 57
WINDOW_WIDTH = HILL_WIDTH * 2
WINDOW_HEIGHT = 432
HILL_TOP = "./res/hill_top.png"
HILL_BOTTOM = "./res/hill_bottom.png"
SHIP = "./res/dart.png"
PLAYER_SHOT = ":resources:/images/space_shooter/laserRed01.png"
PLAYER_SHIP_VERT = 5
PLAYER_SHIP_HORIZ = 8
PLAYER_SHIP_FIRE_SPEED = 20
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


def _create_sprite_at_location(filepath, **kwargs):
    sprite = arcade.Sprite(filepath)
    if kwargs.get("left") is not None and kwargs.get("top") is not None:
        sprite.left = kwargs.get("left")
        sprite.top = kwargs.get("top")
    elif kwargs.get("center_x") is not None and kwargs.get("center_y") is not None:
        sprite.center_x = kwargs.get("center_x")
        sprite.center_y = kwargs.get("center_y")
    return sprite


class PlayerShip(arcade.Sprite):
    LEFT = -1
    RIGHT = 1

    def __init__(
        self,
        shot_list,
        velocity_func,
    ):
        super().__init__(SHIP, center_x=HILL_WIDTH // 4, center_y=WINDOW_HEIGHT // 2)
        self.shot_list = shot_list
        self.right_texture = arcade.load_texture(SHIP)
        self.left_texture = self.right_texture.flip_left_right()
        self.texture_red_laser = arcade.load_texture(":resources:images/space_shooter/laserRed01.png").rotate_90()
        self.speed_factor = 1
        self.set_tunnel_velocity = velocity_func
        self.direction = self.RIGHT

    def move(self, left_pressed, right_pressed, up_pressed, down_pressed):
        horizontal = 0
        vertical = 0
        if left_pressed and not right_pressed:
            horizontal = -PLAYER_SHIP_HORIZ
            self.direction = self.LEFT
            self.texture = self.left_texture
        if right_pressed and not left_pressed:
            horizontal = PLAYER_SHIP_HORIZ
            self.direction = self.RIGHT
            self.texture = self.right_texture
        if up_pressed and not down_pressed:
            vertical = PLAYER_SHIP_VERT
        if down_pressed and not up_pressed:
            vertical = -PLAYER_SHIP_VERT
        if horizontal != 0 or vertical != 0:
            Action.stop_actions_for_target(self, tag="player_move")
            move_until(
                self,
                velocity=(horizontal, vertical),
                condition=self.bounds_check,
                bounds=(
                    SHIP_LEFT_BOUND,
                    TUNNEL_WALL_HEIGHT,
                    SHIP_RIGHT_BOUND,
                    WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT,
                ),
                boundary_behavior="limit",
                on_boundary=self.on_boundary_hit,
                tag="player_move",
            )
            if self.speed_factor > 1 and horizontal <= 0:
                self.speed_factor = 1
                Action.stop_actions_for_target(self, tag="tunnel_velocity")
                self.set_tunnel_velocity(TUNNEL_VELOCITY)
        else:
            Action.stop_actions_for_target(self, tag="player_move")
            self.speed_factor = 1
            Action.stop_actions_for_target(self, tag="tunnel_velocity")
            self.set_tunnel_velocity(TUNNEL_VELOCITY)

    def fire_when_ready(self):
        can_fire = len(self.shot_list) == 0
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
            condition=lambda: shot.right < 0 or shot.left > WINDOW_WIDTH,
            on_stop=lambda: shot.remove_from_sprite_lists(),
        )
        self.shot_list.append(shot)

    def update(self, delta_time):
        super().update(delta_time)

    def bounds_check(self):
        return self.center_x >= SHIP_RIGHT_BOUND + 1

    def on_boundary_hit(self, sprite, axis):
        if axis == "x" and self.right >= SHIP_RIGHT_BOUND:
            self.speed_factor = 2
        Action.stop_actions_for_target(self, tag="tunnel_velocity")
        self.set_tunnel_velocity(TUNNEL_VELOCITY * self.speed_factor)


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

        self.setup_walls()
        self.setup_hills()
        self.setup_ship()

        self.set_tunnel_velocity(self.speed)

    def set_tunnel_velocity(self, speed):
        move_until(
            self.hill_tops,
            velocity=(speed, 0),
            condition=infinite,
            bounds=TOP_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_top_wrap,
            tag="tunnel_velocity",
        )

        move_until(
            self.hill_bottoms,
            velocity=(speed, 0),
            condition=infinite,
            bounds=BOTTOM_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_bottom_wrap,
            tag="tunnel_velocity",
        )

    def on_hill_top_wrap(self, sprite, axis):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def on_hill_bottom_wrap(self, sprite, axis):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def setup_ship(self):
        self.ship = PlayerShip(self.shot_list, self.set_tunnel_velocity)
        self.player_list.append(self.ship)

    def setup_walls(self):
        top_wall = _create_tunnel_wall(0, WINDOW_HEIGHT)
        bottom_wall = _create_tunnel_wall(0, TUNNEL_WALL_HEIGHT)
        self.tunnel_walls.append(top_wall)
        self.tunnel_walls.append(bottom_wall)

    def setup_hills(self):
        for x in [0, HILL_WIDTH * 2]:
            self.hill_tops.append(_create_sprite_at_location(HILL_TOP, left=x, top=WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT))
            self.hill_bottoms.append(
                _create_sprite_at_location(HILL_BOTTOM, left=x + HILL_WIDTH, top=TUNNEL_WALL_HEIGHT + HILL_HEIGHT)
            )

    def on_update(self, delta_time: float):
        Action.update_all(delta_time)
        self.tunnel_walls.update()
        self.hill_tops.update()
        self.hill_bottoms.update()
        self.player_list.update()
        self.shot_list.update()
        self.ship.move(self.left_pressed, self.right_pressed, self.up_pressed, self.down_pressed)
        if self.fire_pressed:
            self.ship.fire_when_ready()

    def on_draw(self):
        # Clear screen (preferred over arcade.start_render() inside a View).
        self.clear()
        self.tunnel_walls.draw()
        self.hill_tops.draw()
        self.hill_bottoms.draw()
        self.player_list.draw()
        self.shot_list.draw()

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
    window = LaserGates()
    arcade.run()


if __name__ == "__main__":
    main()
