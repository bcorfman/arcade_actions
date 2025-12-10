"""
Hot-reload demonstration for ArcadeActions.

This example shows how to use the ReloadManager to enable hot-reload
functionality during game development. When you modify wave files,
the game automatically reloads them without restarting.

Usage:
    # Run the game
    uv run python examples/hot_reload_demo.py

    # Edit examples/waves/demo_wave.py while the game is running
    # Changes will be automatically reloaded!
"""

from __future__ import annotations

import arcade
from pathlib import Path

from actions import Action, center_window
from actions.dev import enable_dev_mode


class HotReloadDemo(arcade.Window):
    """Demonstration window with hot-reload enabled."""

    def __init__(self):
        # Create hidden window so we can center before showing.
        super().__init__(800, 600, "Hot-Reload Demo - Edit waves/demo_wave.py", visible=False)
        center_window(self)
        self.set_visible(True)

        self.enemies = arcade.SpriteList()
        self.wave = None
        self.reload_manager = None
        self.instructions_text: arcade.Text | None = None
        self.count_text: arcade.Text | None = None

    def setup(self) -> None:
        """Set up the game."""
        # Enable dev mode with hot-reload
        # Watch the waves directory for changes
        waves_dir = Path(__file__).parent / "waves"
        waves_dir.mkdir(exist_ok=True)

        # Write initial wave file if it doesn't exist
        wave_file = waves_dir / "demo_wave.py"
        if not wave_file.exists():
            wave_file.write_text(
                '''"""
Demo wave - modify this file to see hot-reload in action!

Try changing:
- enemy_count
- enemy_color (e.g., arcade.color.BLUE, arcade.color.GREEN)
- spawn_y
"""

import arcade

class DemoWave:
    """Simple wave class that can be modified and reloaded."""

    def __init__(self):
        self.enemy_count = 5
        self.enemy_color = arcade.color.RED
        self.spawn_y = 500

    def create_enemies(self):
        """Create enemies for this wave."""
        from arcade import SpriteList, SpriteSolidColor
        from actions.conditional import MoveUntil, infinite

        enemies = SpriteList()
        for i in range(self.enemy_count):
            enemy = SpriteSolidColor(40, 40, color=self.enemy_color)
            enemy.center_x = 100 + i * 100
            enemy.center_y = self.spawn_y

            # Make enemies move down
            MoveUntil((0, -2), infinite()).apply(enemy, tag="move_down")
            enemies.append(enemy)

        return enemies
'''
            )

        def on_reload(files, state):
            """Handle reload - reconstruct enemies from new wave definition."""
            print(f"Reloading: {files}")

            # Clear old enemies
            for enemy in list(self.enemies):
                Action.stop_actions_for_target(enemy, tag="move_down")
            self.enemies.clear()

            # Reimport and recreate wave
            import importlib
            import sys

            if "examples.waves.demo_wave" in sys.modules:
                importlib.reload(sys.modules["examples.waves.demo_wave"])
                from examples.waves import demo_wave

                self.wave = demo_wave.DemoWave()
                self.enemies = self.wave.create_enemies()

        def state_provider():
            """Provide game state for preservation."""
            return {
                "enemy_count": len(self.enemies),
            }

        def sprite_provider():
            """Provide sprites for state preservation."""
            return list(self.enemies)

        self.reload_manager = enable_dev_mode(
            watch_paths=[waves_dir],
            root_path=Path(__file__).parent.parent,
            on_reload=on_reload,
            state_provider=state_provider,
            sprite_provider=sprite_provider,
        )

        # Load initial wave
        import sys

        waves_path = Path(__file__).parent / "waves"
        if str(waves_path) not in sys.path:
            sys.path.insert(0, str(waves_path.parent))

        try:
            from examples.waves import demo_wave

            self.wave = demo_wave.DemoWave()
            self.enemies = self.wave.create_enemies()
        except ImportError as e:
            print(f"Error: Could not import wave module: {e}")
            print("Make sure examples/waves/demo_wave.py exists and is valid.")
            self.enemies = arcade.SpriteList()

        # Pre-create text objects to avoid per-frame draw_text calls
        self.instructions_text = arcade.Text(
            "Edit examples/waves/demo_wave.py to see hot-reload!",
            10,
            10,
            arcade.color.WHITE,
            14,
        )
        self.count_text = arcade.Text(
            f"Enemies: {len(self.enemies)}",
            10,
            30,
            arcade.color.YELLOW,
            14,
        )

    def on_update(self, delta_time: float) -> None:
        """Update game logic."""
        # Process reload requests from background thread
        if self.reload_manager:
            self.reload_manager.process_reloads()
            self.reload_manager.indicator.update(delta_time)

        # Update actions
        Action.update_all(delta_time)

        # Update sprites to apply velocities set by actions
        self.enemies.update()

        # Remove enemies that moved off screen
        for enemy in list(self.enemies):
            if enemy.center_y < -50:
                enemy.remove_from_sprite_lists()

    def on_draw(self) -> None:
        """Draw everything."""
        self.clear()

        # Draw enemies
        self.enemies.draw()

        # Draw reload indicator
        if self.reload_manager:
            self.reload_manager.indicator.draw()

        # Draw instructions
        if self.instructions_text:
            self.instructions_text.draw()
        if self.count_text:
            self.count_text.text = f"Enemies: {len(self.enemies)}"
            self.count_text.draw()

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Handle key presses."""
        # Let reload manager handle keyboard shortcuts (R key for reload)
        if self.reload_manager:
            self.reload_manager.on_key_press(key, modifiers)

    def on_close(self) -> None:
        """Clean up on window close."""
        if self.reload_manager:
            self.reload_manager.stop()
        Action.stop_all()
        super().on_close()


def main():
    """Main entry point."""
    window = HotReloadDemo()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
