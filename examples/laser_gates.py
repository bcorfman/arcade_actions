import arcade

from actions import Action, center_window, infinite, move_until

HILL_WIDTH = 512
HILL_HEIGHT = 57
WINDOW_WIDTH = HILL_WIDTH * 2
WINDOW_HEIGHT = 432
HILL_TOP = "./res/hill_top.png"
HILL_BOTTOM = "./res/hill_bottom.png"
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


def create_tunnel_wall(left, top):
    wall = arcade.SpriteSolidColor(WINDOW_WIDTH, TUNNEL_WALL_HEIGHT, color=TUNNEL_WALL_COLOR)
    wall.left = left
    wall.top = top
    return wall


def create_hill(filepath, left, top):
    hill = arcade.Sprite(filepath)
    hill.left = left
    hill.top = top
    return hill


class Tunnel(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.BLACK
        self.tunnel_walls = arcade.SpriteList()
        top_wall = create_tunnel_wall(0, WINDOW_HEIGHT)
        bottom_wall = create_tunnel_wall(0, TUNNEL_WALL_HEIGHT)
        self.tunnel_walls.append(top_wall)
        self.tunnel_walls.append(bottom_wall)

        self.hill_tops = arcade.SpriteList()
        self.hill_bottoms = arcade.SpriteList()
        for x in [0, HILL_WIDTH * 2]:
            self.hill_tops.append(create_hill(HILL_TOP, x, WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT))
            self.hill_bottoms.append(create_hill(HILL_BOTTOM, x + HILL_WIDTH, TUNNEL_WALL_HEIGHT + HILL_HEIGHT))

        move_until(
            self.hill_tops,
            velocity=(TUNNEL_VELOCITY, 0),
            condition=infinite,
            bounds=TOP_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_top_wrap,
        )

        move_until(
            self.hill_bottoms,
            velocity=(TUNNEL_VELOCITY, 0),
            condition=infinite,
            bounds=BOTTOM_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_bottom_wrap,
        )

    def on_hill_top_wrap(self, sprite, axis):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def on_hill_bottom_wrap(self, sprite, axis):
        sprite.position = (HILL_WIDTH * 3, sprite.position[1])

    def on_update(self, delta_time: float):
        Action.update_all(delta_time)
        self.tunnel_walls.update()
        self.hill_tops.update()
        self.hill_bottoms.update()

    def on_draw(self):
        # Clear screen (preferred over arcade.start_render() inside a View).
        self.clear()
        self.tunnel_walls.draw()
        self.hill_tops.draw()
        self.hill_bottoms.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ESCAPE:
            self.window.close()


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
