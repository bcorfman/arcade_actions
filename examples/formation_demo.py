"""
ArcadeActions Formation Demo - Showcases all formation patterns.

This demo displays all twelve formation functions from the formation.py module,
cycling through them one at a time using the spacebar. The demo uses a 640x480
window and spaceship sprites for all formations.
"""

import arcade
import arcade.gui

from actions.formation import (
    arrange_arc,
    arrange_circle,
    arrange_concentric_rings,
    arrange_cross,
    arrange_diamond,
    arrange_grid,
    arrange_hexagonal_grid,
    arrange_line,
    arrange_triangle,
    arrange_v_formation,
)

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "ArcadeActions Formation Demo"

# Formation display area
FORMATION_CENTER_X = SCREEN_WIDTH // 2
FORMATION_CENTER_Y = SCREEN_HEIGHT // 2
FORMATION_SPACING = 60  # Increased from 40 to ensure sprite width separation
SPRITE_COUNT = 20  # Number of sprites to use for all formations

# Text positioning constants for reference
TOP_TEXT_Y = SCREEN_HEIGHT - 50
BOTTOM_TEXT_Y = 30
AVAILABLE_HEIGHT = TOP_TEXT_Y - BOTTOM_TEXT_Y - 100  # Leave 50px margin on each side
FORMATION_AREA_CENTER_Y = BOTTOM_TEXT_Y + 60 + (AVAILABLE_HEIGHT // 2)

# Formation definitions with their display names, optimal sprite counts, and arrangement functions
FORMATIONS = [
    (
        "Line",
        10,  # 10 sprites work well in a horizontal line without going offscreen
        lambda sprites, count: arrange_line(
            sprites[:count],
            start_x=FORMATION_CENTER_X - ((count - 1) * FORMATION_SPACING) / 2,
            start_y=FORMATION_AREA_CENTER_Y,
            spacing=FORMATION_SPACING,
        ),
    ),
    (
        "Grid",
        20,  # 4x5 grid = 20 sprites
        lambda sprites, count: arrange_grid(
            sprites[:count],
            rows=4,
            cols=5,
            start_x=FORMATION_CENTER_X - (5 // 2) * FORMATION_SPACING,
            start_y=FORMATION_AREA_CENTER_Y - FORMATION_SPACING,
            spacing_x=FORMATION_SPACING,
            spacing_y=FORMATION_SPACING,
        ),
    ),
    (
        "Circle",
        16,  # 16 sprites fit well in a circle without overcrowding
        lambda sprites, count: arrange_circle(
            sprites[:count], center_x=FORMATION_CENTER_X, center_y=FORMATION_AREA_CENTER_Y, radius=120
        ),
    ),
    (
        "V Formation",
        9,  # 9 sprites fit comfortably in V formation without going offscreen
        lambda sprites, count: arrange_v_formation(
            sprites[:count],
            count=count,
            apex_x=FORMATION_CENTER_X,
            apex_y=FORMATION_AREA_CENTER_Y - 100,
            spacing=FORMATION_SPACING,
            direction="up",
        ),
    ),
    (
        "Diamond",
        13,  # 13 sprites (1 + 4 + 8) fit well in diamond layers
        lambda sprites, count: arrange_diamond(
            sprites[:count],
            center_x=FORMATION_CENTER_X,
            center_y=FORMATION_AREA_CENTER_Y,
            spacing=FORMATION_SPACING,
            include_center=True,
        ),
    ),
    (
        "Triangle",
        15,  # 10 sprites (1+2+3+4) fit well in triangle without overcrowding
        lambda sprites, count: arrange_triangle(
            sprites[:count],
            apex_x=FORMATION_CENTER_X,
            apex_y=FORMATION_AREA_CENTER_Y - 105,  # Position apex higher to center the group
            row_spacing=FORMATION_SPACING,
            lateral_spacing=FORMATION_SPACING,
            invert=True,  # Grow upward instead of downward to avoid bottom text
        ),
    ),
    (
        "Hexagonal Grid",
        20,  # 4x5 hex grid = 20 sprites
        lambda sprites, count: arrange_hexagonal_grid(
            sprites[:count],
            rows=4,
            cols=5,
            start_x=FORMATION_CENTER_X - (5 // 2) * FORMATION_SPACING,
            start_y=FORMATION_AREA_CENTER_Y - FORMATION_SPACING,
            spacing=FORMATION_SPACING,
        ),
    ),
    (
        "Arc",
        8,  # 8 sprites fit well in a semicircle arc
        lambda sprites, count: arrange_arc(
            sprites[:count],
            center_x=FORMATION_CENTER_X,
            center_y=FORMATION_AREA_CENTER_Y,
            radius=120,
            start_angle=20,
            end_angle=160,
        ),
    ),
    (
        "Concentric Rings",
        18,  # 18 sprites (6+12) fit well in two rings
        lambda sprites, count: arrange_concentric_rings(
            sprites[:count],
            radii=[80, 120],
            sprites_per_ring=[6, 12],
            center_x=FORMATION_CENTER_X,
            center_y=FORMATION_AREA_CENTER_Y,
        ),
    ),
    (
        "Cross",
        9,  # 9 sprites (1 center + 2 per arm) fit well in cross
        lambda sprites, count: arrange_cross(
            sprites[:count],
            center_x=FORMATION_CENTER_X,
            center_y=FORMATION_AREA_CENTER_Y,
            arm_length=120,
            spacing=FORMATION_SPACING,
            include_center=True,
        ),
    ),
]


class FormationDemo(arcade.Window):
    """Demo window showing all formation patterns."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.MIDNIGHT_BLUE)

        # Sprite lists
        self.formation_sprites = arcade.SpriteList()
        self.text_labels = []

        # UI Manager for text
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        # Formation state
        self.current_formation_index = 0
        self.formation_name = ""
        self.formation_function = None

    def setup(self):
        """Set up the formation demonstrations."""
        # Create all sprites once at the beginning
        self._create_sprites()

        # Create text objects for better performance
        self._create_text_objects()

        # Set up the first formation
        self._show_formation(0)

    def _create_sprites(self):
        """Create all sprites once for reuse across formations."""
        for i in range(SPRITE_COUNT):
            sprite = arcade.Sprite(":resources:images/space_shooter/playerShip1_orange.png", scale=0.5)
            # Start sprites off-screen until first formation is applied
            sprite.center_x = -1000
            sprite.center_y = -1000
            self.formation_sprites.append(sprite)

    def _create_text_objects(self):
        """Create text objects for better performance."""
        # Formation name text (will be updated for each formation)
        self.formation_name_text = arcade.Text(
            "",
            SCREEN_WIDTH // 2,
            TOP_TEXT_Y,
            arcade.color.WHITE,
            24,
            anchor_x="center",
            font_name="Kenney Future",
        )

        # Instructions text
        self.instructions_text = arcade.Text(
            "Press SPACE to cycle formations, ESC to quit",
            SCREEN_WIDTH // 2,
            BOTTOM_TEXT_Y,
            arcade.color.LIGHT_GRAY,
            16,
            anchor_x="center",
            font_name="Kenney Future",
        )

        # Formation counter text (will be updated for each formation)
        self.counter_text = arcade.Text(
            "",
            SCREEN_WIDTH // 2,
            BOTTOM_TEXT_Y + 30,
            arcade.color.LIGHT_GRAY,
            14,
            anchor_x="center",
            font_name="Kenney Future",
        )

    def _show_formation(self, formation_index: int):
        """Display the formation at the given index."""
        if 0 <= formation_index < len(FORMATIONS):
            self.current_formation_index = formation_index
            self.formation_name, self.formation_count, self.formation_function = FORMATIONS[formation_index]

            # Update text objects
            self.formation_name_text.text = self.formation_name
            self.counter_text.text = f"Formation {self.current_formation_index + 1} of {len(FORMATIONS)}"

            # Hide and move offscreen all sprites first
            for sprite in self.formation_sprites:
                sprite.visible = False
                sprite.center_x = -1000
                sprite.center_y = -1000

            # Apply the formation function to the needed sprites with the optimal count
            self.formation_function(self.formation_sprites, self.formation_count)

            # Ensure all used sprites are visible
            for i in range(self.formation_count):
                self.formation_sprites[i].visible = True

    def _next_formation(self):
        """Move to the next formation, cycling back to the beginning."""
        next_index = (self.current_formation_index + 1) % len(FORMATIONS)
        self._show_formation(next_index)

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.SPACE:
            self._next_formation()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_draw(self):
        """Draw everything."""
        self.clear()

        # Draw formation sprites
        self.formation_sprites.draw()

        # Draw text objects (much better performance than draw_text)
        self.formation_name_text.draw()
        self.instructions_text.draw()
        self.counter_text.draw()

        # Draw UI elements
        self.ui_manager.draw()

    def on_update(self, delta_time):
        """Update the demo."""
        # Update sprites
        self.formation_sprites.update()


def main():
    """Main function."""
    demo = FormationDemo()
    demo.setup()
    arcade.run()


if __name__ == "__main__":
    main()
