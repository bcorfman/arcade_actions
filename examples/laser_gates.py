import arcade

from actions import Action, center_window, infinite, move_until

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
def handle_hill_collision(sprite, collision_lists, parent_view):
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
    if hasattr(parent_view, "damage_flash"):
        parent_view.damage_flash = min(parent_view.damage_flash + 0.3, 1.0)
    else:
        parent_view.damage_flash = 0.3

    return True


class PlayerShip(arcade.Sprite):
    LEFT = -1
    RIGHT = 1

    def __init__(self, parent):
        super().__init__(SHIP, center_x=HILL_WIDTH // 4, center_y=WINDOW_HEIGHT // 2)
        self.parent = parent
        self.right_texture = arcade.load_texture(SHIP)
        self.left_texture = self.right_texture.flip_left_right()
        self.texture_red_laser = arcade.load_texture(":resources:images/space_shooter/laserRed01.png").rotate_90()
        self.speed_factor = 1
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
                self.parent.set_tunnel_velocity(TUNNEL_VELOCITY)
        else:
            Action.stop_actions_for_target(self, tag="player_move")
            self.speed_factor = 1
            Action.stop_actions_for_target(self, tag="tunnel_velocity")
            self.parent.set_tunnel_velocity(TUNNEL_VELOCITY)

        # Always check for hill or wall collisions after movement (whether moving or stationary)
        hill_collision_lists = [self.parent.hill_tops, self.parent.hill_bottoms, self.parent.tunnel_walls]
        if handle_hill_collision(self, hill_collision_lists, self.parent):
            # Stop current movement if we hit hills
            Action.stop_actions_for_target(self, tag="player_move")

    def fire_when_ready(self):
        can_fire = len(self.parent.shot_list) == 0
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
            on_stop=lambda result: shot.remove_from_sprite_lists(),
        )
        self.parent.shot_list.append(shot)

    def shot_collision_check(self):
        shot = self.parent.shot_list[0]
        off_screen = shot.right < 0 or shot.left > WINDOW_WIDTH
        hills_hit = arcade.check_for_collision_with_lists(shot, [self.parent.hill_tops, self.parent.hill_bottoms])
        return {"off_screen": off_screen, "hills_hit": hills_hit} if off_screen or hills_hit else None

    def update(self, delta_time):
        super().update(delta_time)

    def bounds_check(self):
        return self.center_x >= SHIP_RIGHT_BOUND + 1

    def on_boundary_hit(self, sprite, axis):
        # Handle tunnel boundary limits (existing behavior)
        if axis == "x" and self.right >= SHIP_RIGHT_BOUND:
            self.speed_factor = 2
            Action.stop_actions_for_target(self, tag="tunnel_velocity")
            self.parent.set_tunnel_velocity(TUNNEL_VELOCITY * self.speed_factor)


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
        self.ship = PlayerShip(self)
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
        self.ship.move(self.left_pressed, self.right_pressed, self.up_pressed, self.down_pressed)
        if self.fire_pressed:
            self.ship.fire_when_ready()

        # Decay damage flash effect
        if self.damage_flash > 0:
            self.damage_flash = max(0, self.damage_flash - delta_time * 5.0)

    def on_draw(self):
        # Always clear with black background
        self.background_color = arcade.color.BLACK
        self.clear()
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
    window = LaserGates()
    arcade.run()


if __name__ == "__main__":
    main()
