import arcade

from actions import Action, infinite, move_until

HILL_WIDTH = 512
HILL_HEIGHT = 57
WINDOW_WIDTH = HILL_WIDTH * 2
WINDOW_HEIGHT = 432
HILL_TOP = "./res/hill_top.png"
HILL_BOTTOM = "./res/hill_bottom.png"
HILL_VELOCITY = -5
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
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Laser Gates")
        self.center_on_current_screen()
        self.show_view(Tunnel())

    def center_on_current_screen(self):
        """Center the window on its current monitor without jumping to a different one."""
        try:
            # Get the window's current location
            current_x, current_y = self.get_location()

            # Try to get display information using modern pyglet API
            try:
                # Prefer pyglet.display on Windows/pyglet 2.x, fallback to canvas if needed
                try:
                    from pyglet.display import Display
                except Exception:
                    from pyglet.canvas import Display

                display = Display()
                screens = display.get_screens()

                # Find which screen the window center point is currently on
                current_screen = None
                win_center_x = current_x + self.width // 2
                win_center_y = current_y + self.height // 2
                for screen in screens:
                    if (
                        screen.x <= win_center_x < screen.x + screen.width
                        and screen.y <= win_center_y < screen.y + screen.height
                    ):
                        current_screen = screen
                        break

                # If we found the current screen, center on it
                if current_screen:
                    # Use logical window size to match screen/set_location coordinate space
                    win_w, win_h = self.width, self.height

                    # Center relative to the screen's origin
                    center_x = current_screen.x + (current_screen.width - win_w) // 2
                    center_y = current_screen.y + (current_screen.height - win_h) // 2
                    self.set_location(center_x, center_y)
                    return

            except (ImportError, AttributeError):
                pass

            # If pyglet reports only one large screen (common with X11 + Xinerama),
            # try to detect actual monitors via xrandr and center in the monitor
            # that contains the window's center point.
            try:
                import re
                import subprocess

                # Window center point
                win_center_x = current_x + self.width // 2
                win_center_y = current_y + self.height // 2

                result = subprocess.run(
                    ["xrandr", "--listmonitors"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                monitors = []
                if result.stdout:
                    for line in result.stdout.splitlines():
                        # Lines look like: " 0: +*DP-1 3840/600x2160/340+0+0  DP-1"
                        m = re.search(r"(\d+)/(?:\d+)?x(\d+)/(?:\d+)?\+(-?\d+)\+(-?\d+)", line)
                        if not m:
                            m = re.search(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", line)
                        if m:
                            w, h, x, y = map(int, m.groups())
                            monitors.append({"x": x, "y": y, "w": w, "h": h})

                # Choose the monitor containing the window center
                current_monitor = None
                for mon in monitors:
                    if (
                        mon["x"] <= win_center_x < mon["x"] + mon["w"]
                        and mon["y"] <= win_center_y < mon["y"] + mon["h"]
                    ):
                        current_monitor = mon
                        break

                if current_monitor is not None:
                    center_x = current_monitor["x"] + (current_monitor["w"] - self.width) // 2
                    center_y = current_monitor["y"] + (current_monitor["h"] - self.height) // 2
                    self.set_location(center_x, center_y)
                    return
            except Exception:
                # Ignore and proceed to other fallbacks
                pass

            # Fallback: try to get monitor info using alternative methods
            try:
                # Try using pyglet's window system to get display info
                window_display = self._window._display
                if hasattr(window_display, "get_screens"):
                    screens = window_display.get_screens()

                    # Find which screen the window center point is currently on
                    current_screen = None
                    win_center_x = current_x + self.width // 2
                    win_center_y = current_y + self.height // 2
                    for screen in screens:
                        if (
                            screen.x <= win_center_x < screen.x + screen.width
                            and screen.y <= win_center_y < screen.y + screen.height
                        ):
                            current_screen = screen
                            break

                    # If we found the current screen, center on it
                    if current_screen:
                        # Use logical window size to match screen/set_location coordinate space
                        win_w, win_h = self.width, self.height

                        # Center relative to the screen's origin
                        center_x = current_screen.x + (current_screen.width - win_w) // 2
                        center_y = current_screen.y + (current_screen.height - win_h) // 2
                        self.set_location(center_x, center_y)
                        return

            except Exception:
                pass

            # Final fallback: don't move the window at all
            # This prevents jumping to wrong monitors or incorrect positioning
            pass

        except Exception:
            # If anything goes wrong, just leave the window where it is
            # This ensures the example still runs
            pass


def main():
    """Main function."""
    window = LaserGates()
    arcade.run()


if __name__ == "__main__":
    main()
