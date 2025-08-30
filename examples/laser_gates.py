import arcade

from actions import Action, infinite, move_until

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
VERTICAL_MARGIN = 400
HILL_HEIGHT = 62
HILL_TOP = "./res/hill_top.png"
HILL_BOTTOM = "./res/hill_bottom.png"
HILL_OFFSET = 200
HILL_VELOCITY = -3
TOP_BOUNDS = (-VERTICAL_MARGIN, WINDOW_HEIGHT // 2, VERTICAL_MARGIN * 3, WINDOW_HEIGHT)
BOTTOM_BOUNDS = (
    -VERTICAL_MARGIN + HILL_OFFSET,
    0,
    VERTICAL_MARGIN * 3 + HILL_OFFSET,
    WINDOW_HEIGHT // 2,
)
TUNNEL_WALL_HEIGHT = 40
TUNNEL_WALL_COLOR = (122, 92, 44)


def create_tunnel_wall(cx, cy):
    wall = arcade.SpriteSolidColor(WINDOW_WIDTH, TUNNEL_WALL_HEIGHT, color=TUNNEL_WALL_COLOR)
    wall.center_x = cx
    wall.center_y = cy
    return wall


def create_hill(filepath, x, y):
    hill = arcade.Sprite(filepath)
    hill.center_x = x
    hill.center_y = y
    return hill


class Tunnel(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.BLACK
        self.tunnel_walls = arcade.SpriteList()
        top_wall = create_tunnel_wall(WINDOW_WIDTH // 2, WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT // 2)
        bottom_wall = create_tunnel_wall(WINDOW_WIDTH // 2, TUNNEL_WALL_HEIGHT // 2)
        self.tunnel_walls.append(top_wall)
        self.tunnel_walls.append(bottom_wall)

        self.hill_tops = arcade.SpriteList()
        self.hill_bottoms = arcade.SpriteList()
        for x in [0, 400, 800, 1200]:
            self.hill_tops.append(create_hill(HILL_TOP, x, WINDOW_HEIGHT - TUNNEL_WALL_HEIGHT - HILL_HEIGHT // 2))
            self.hill_bottoms.append(create_hill(HILL_BOTTOM, x - HILL_OFFSET, TUNNEL_WALL_HEIGHT + HILL_HEIGHT // 2))

        move_until(
            self.hill_tops,
            velocity=(HILL_VELOCITY, 0),
            condition=infinite,
            bounds=TOP_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_top_wrap,
        )

        move_until(
            self.hill_bottoms,
            velocity=(HILL_VELOCITY, 0),
            condition=infinite,
            bounds=BOTTOM_BOUNDS,
            boundary_behavior="wrap",
            on_boundary=self.on_hill_bottom_wrap,
        )

    def on_hill_top_wrap(self, sprite, axis):
        sprite.position = (WINDOW_WIDTH + HILL_OFFSET * 2, sprite.position[1])

    def on_hill_bottom_wrap(self, sprite, axis):
        sprite.position = (WINDOW_WIDTH + HILL_OFFSET * 3, sprite.position[1])

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


def main():
    """Main function."""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Laser Gates")
    window.show_view(Tunnel())
    arcade.run()


if __name__ == "__main__":
    main()
