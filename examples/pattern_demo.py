"""
ArcadeActions Pattern Demo - Showcases all movement patterns simultaneously.

This demo displays all seven movement patterns from the pattern.py module,
running in parallel in a 800x600 window with appropriate labels.
"""

import arcade
import arcade.gui

from actions import (
    Action,
    MoveBy,
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_orbit_pattern,
    create_patrol_pattern,
    create_spiral_pattern,
    create_wave_pattern,
    create_zigzag_pattern,
    repeat,
    sequence,
)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "ArcadeActions Pattern Demo"

# Pattern display positions - 4 on top row, 3 on bottom row
TOP_ROW_Y = 450
BOTTOM_ROW_Y = 200
TOP_ROW_POSITIONS = [150, 300, 500, 650]  # X positions for top row
BOTTOM_ROW_POSITIONS = [200, 400, 600]  # X positions for bottom row


class PatternDemo(arcade.Window):
    """Demo window showing all movement patterns."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.MIDNIGHT_BLUE)

        # Sprite lists
        self.pattern_sprites = arcade.SpriteList()
        self.text_labels = []

        # UI Manager for text
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

    def setup(self):
        """Set up the pattern demonstrations."""
        # Create sprites and patterns for top row
        patterns_top = [
            ("Wave", self._create_wave_demo),
            ("Zigzag", self._create_zigzag_demo),
            ("Figure-8", self._create_figure8_demo),
            ("Orbit", self._create_orbit_demo),
        ]

        for i, (label, create_func) in enumerate(patterns_top):
            x = TOP_ROW_POSITIONS[i]
            y = TOP_ROW_Y
            sprite = self._create_sprite(x, y)
            self.pattern_sprites.append(sprite)
            create_func(sprite)

            # Create Text object for label
            text_label = arcade.Text(
                label, x, y + 80, arcade.color.WHITE, 14, anchor_x="center", font_name="Kenney Future"
            )
            self.text_labels.append(text_label)

        # Create sprites and patterns for bottom row
        patterns_bottom = [
            ("Spiral", self._create_spiral_demo),
            ("Bounce", self._create_bounce_demo),
            ("Patrol", self._create_patrol_demo),
        ]

        for i, (label, create_func) in enumerate(patterns_bottom):
            x = BOTTOM_ROW_POSITIONS[i]
            y = BOTTOM_ROW_Y
            sprite = self._create_sprite(x, y)
            self.pattern_sprites.append(sprite)
            create_func(sprite)

            # Create Text object for label
            text_label = arcade.Text(
                label, x, y + 80, arcade.color.WHITE, 14, anchor_x="center", font_name="Kenney Future"
            )
            self.text_labels.append(text_label)

    def _create_sprite(self, x: float, y: float) -> arcade.Sprite:
        """Create a sprite at the given position."""
        sprite = arcade.Sprite(":resources:images/space_shooter/playerShip1_orange.png", scale=0.5)
        sprite.center_x = x
        sprite.center_y = y
        return sprite

    def _create_wave_demo(self, sprite: arcade.Sprite):
        """Create repeating wave pattern."""
        quarter_wave = create_wave_pattern(amplitude=30, length=80, speed=80, start_progress=0.75, end_progress=1.0)
        full_wave = create_wave_pattern(amplitude=30, length=80, speed=80)
        sequence(quarter_wave, repeat(full_wave)).apply(sprite)

    def _create_zigzag_demo(self, sprite: arcade.Sprite):
        """Create zigzag pattern that reverses to return to start."""
        # Create a zigzag that moves right and up
        forward = create_zigzag_pattern(dimensions=(30, 15), speed=100, segments=5)

        # Create a zigzag that moves left and down to return to start
        # We need to reverse both X and Y directions
        backward = create_zigzag_pattern(dimensions=(-30, -15), speed=100, segments=5)

        # Combine forward and backward into a sequence, then repeat
        zigzag_cycle = sequence(forward, backward)
        sequence(MoveBy(-15, -30), repeat(zigzag_cycle)).apply(sprite)

    def _create_figure8_demo(self, sprite: arcade.Sprite):
        """Create repeating figure-8 pattern."""
        figure8 = create_figure_eight_pattern(center=(sprite.center_x, sprite.center_y), width=80, height=60, speed=100)
        repeat(figure8).apply(sprite)

    def _create_orbit_demo(self, sprite: arcade.Sprite):
        """Create repeating circular orbit pattern."""
        # The sprite should start at a point on the orbit path, not at the center
        # Calculate the starting position on the orbit (right side of the circle)
        orbit_center = (sprite.center_x, sprite.center_y)
        start_x = orbit_center[0] + 50  # Start at right edge of orbit
        start_y = orbit_center[1]  # Same Y as center

        # Move sprite to starting position on orbit path
        sprite.center_x = start_x
        sprite.center_y = start_y

        # Create orbit around the center point
        orbit = create_orbit_pattern(center=orbit_center, radius=50, speed=100, clockwise=True)
        repeat(orbit).apply(sprite)

    def _create_spiral_demo(self, sprite: arcade.Sprite):
        """Create spiral pattern that alternates between outward and inward."""
        # Create outward spiral
        outward = create_spiral_pattern(
            center=(sprite.center_x, sprite.center_y), max_radius=60, revolutions=2, speed=80, direction="outward"
        )
        # Create inward spiral
        inward = create_spiral_pattern(
            center=(sprite.center_x, sprite.center_y), max_radius=60, revolutions=2, speed=80, direction="inward"
        )

        # Combine into a sequence and repeat
        spiral_cycle = sequence(outward, inward)
        repeat(spiral_cycle).apply(sprite)

    def _create_bounce_demo(self, sprite: arcade.Sprite):
        """Create bouncing pattern within a boundary box."""
        # Define bounce bounds around the sprite's starting position
        bounds = (
            sprite.center_x - 60,  # left
            sprite.center_y - 40,  # bottom
            sprite.center_x + 60,  # right
            sprite.center_y + 40,  # top
        )

        bounce = create_bounce_pattern(velocity=(2, 1), bounds=bounds)
        bounce.apply(sprite)

    def _create_patrol_demo(self, sprite: arcade.Sprite):
        """Create repeating patrol pattern."""
        start_pos = (sprite.center_x - 40, sprite.center_y)
        end_pos = (sprite.center_x + 40, sprite.center_y)
        quarter_patrol = create_patrol_pattern(start_pos, end_pos, speed=2, start_progress=0.75, end_progress=1.0)
        full_patrol = create_patrol_pattern(start_pos, end_pos, speed=2)
        sequence(quarter_patrol, repeat(full_patrol)).apply(sprite)

    def on_draw(self):
        """Draw everything."""
        self.clear()

        # Draw pattern sprites
        self.pattern_sprites.draw()

        # Draw text labels using Text objects
        for text_label in self.text_labels:
            text_label.draw()

        # Draw UI elements
        self.ui_manager.draw()

    def on_update(self, delta_time):
        """Update all actions."""
        # Update actions
        Action.update_all(delta_time)

        # Update sprites
        self.pattern_sprites.update()


def main():
    """Main function."""
    demo = PatternDemo()
    demo.setup()
    arcade.run()


if __name__ == "__main__":
    main()
