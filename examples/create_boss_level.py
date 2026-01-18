"""
Create a Boss Level Scene - Truly Zero Boilerplate

This demonstrates creating a new scene from scratch with ABSOLUTELY NO API calls needed.
DevVisualizer works completely transparently - just register prototypes and run!

Usage:
    ARCADEACTIONS_DEVVIZ=1 uv run python examples/create_boss_level.py

Workflow:
    1. Run the script - DevVisualizer auto-appears
    2. Press F12 to toggle DevVisualizer (if not visible)
    3. Drag sprites from the palette on the left
    4. Click sprites to select them
    5. Press E to export scene to boss_level.yaml
    6. Load the YAML in your game (see invaders.py example)

No get_dev_visualizer(), no scene_sprites.draw(), no enable_dev_visualizer() - NOTHING!
DevVisualizer automatically draws scene sprites - completely transparent to the developer.
"""

import arcade

from arcadeactions import center_window
from arcadeactions.dev import register_prototype

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Boss Level Editor"

# Register prototypes - these appear in the palette automatically
# No other code needed! DevVisualizer auto-enables when ARCADEACTIONS_DEVVIZ=1


@register_prototype("boss")
def make_boss(ctx):
    """Create a boss enemy sprite."""
    texture = arcade.load_texture(":resources:images/enemies/slimeBlue.png")
    boss = arcade.Sprite(texture, scale=2.0)  # Boss is bigger
    boss._prototype_id = "boss"
    return boss


@register_prototype("boss_minion")
def make_boss_minion(ctx):
    """Create a smaller enemy that follows the boss."""
    texture = arcade.load_texture(":resources:images/enemies/slimeBlue.png")
    minion = arcade.Sprite(texture, scale=0.75)
    minion._prototype_id = "boss_minion"
    return minion


@register_prototype("power_up")
def make_power_up(ctx):
    """Create a power-up sprite."""
    power = arcade.Sprite(":resources:images/items/star.png", scale=0.8)
    power._prototype_id = "power_up"
    return power


class SceneEditorView(arcade.View):
    """Simple view - DevVisualizer handles EVERYTHING automatically!

    DevVisualizer auto-attaches when ARCADEACTIONS_DEVVIZ=1 is set.
    Scene sprites are drawn automatically - zero API calls needed!
    Just register prototypes and create a basic View. That's it!
    """

    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.BLACK

    def on_draw(self):
        """Draw the scene - DevVisualizer draws sprites automatically."""
        self.clear()
        # That's it! DevVisualizer automatically draws scene_sprites
        # No get_dev_visualizer(), no scene_sprites.draw(), nothing!
        # Completely transparent - beginner-friendly!

    def on_key_press(self, key, modifiers):
        """Handle keyboard shortcuts."""
        if key == arcade.key.ESCAPE:
            self.window.close()


def main():
    """Run the scene editor."""
    window = arcade.Window(
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        WINDOW_TITLE,
        visible=False,
        vsync=True,
    )
    center_window(window)
    window.set_visible(True)

    view = SceneEditorView()
    window.show_view(view)

    print("=" * 60)
    print("Boss Level Editor")
    print("=" * 60)
    print("DevVisualizer auto-enabled! (ARCADEACTIONS_DEVVIZ=1)")
    print("Press F12 to toggle DevVisualizer")
    print("Drag sprites from the palette on the left")
    print("Click sprites to select them")
    print("Press E to export scene to boss_level.yaml")
    print("Press ESC to exit")
    print("=" * 60)

    arcade.run()


if __name__ == "__main__":
    main()
