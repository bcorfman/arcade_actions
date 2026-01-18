"""Galaga-style demo showcasing AttackGroup features.

Demonstrates:
- Grid formation entry via path
- Horizontal patrol
- Breakaway dive & return
- Multiple waves with different formations
"""

import arcade

from arcadeactions.formation import arrange_grid
from arcadeactions.group import AttackGroup
from arcadeactions.presets.entry_paths import loop_the_loop_exact


class AttackGroupDemo(arcade.Window):
    """Demo window showing AttackGroup features."""

    def __init__(self):
        super().__init__(800, 600, "AttackGroup Demo - Galaga Style")
        arcade.set_background_color(arcade.color.BLACK)

        self.enemy_groups: list[AttackGroup] = []
        self.player_list = arcade.SpriteList()

        # Create text objects for better performance
        self.title_text = arcade.Text(
            "AttackGroup Demo - Galaga Style",
            10,
            580,
            arcade.color.WHITE,
            14,
        )
        self.instructions_text = arcade.Text(
            "Watch enemies enter in formation, patrol, then break away",
            10,
            560,
            arcade.color.WHITE,
            12,
        )

        self.setup()

    def setup(self):
        """Set up the demo scene."""
        # Create player sprite
        player = arcade.Sprite(":resources:/images/space_shooter/playerShip1_orange.png", scale=0.5)
        player.center_x = 400
        player.center_y = 50
        self.player_list.append(player)

        # Create first wave - grid formation
        self.create_wave_1()

        # Create second wave - line formation (after delay)
        # In a real game, this would be triggered by wave completion

    def create_wave_1(self):
        """Create first wave with grid formation and entry path."""
        import arcade

        sprites = arcade.SpriteList()
        for _ in range(15):  # 3x5 grid
            sprite = arcade.Sprite(":resources:/images/enemies/bee.png", scale=0.5)
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="wave1")
        group.place(arrange_grid, rows=3, cols=5, start_x=200, start_y=400, spacing_x=60, spacing_y=50)

        # Entry path - exact circular loop
        # Calculate loop center between start and end
        loop_center_x = (650 + 200) / 2
        loop_center_y = (-200 + 350) / 2
        entry_path = loop_the_loop_exact(
            start_x=650,
            start_y=-200,
            end_x=200,
            end_y=350,
            loop_center_x=loop_center_x,
            loop_center_y=loop_center_y,
            loop_radius=150,
        )
        group.entry_path(entry_path, velocity=300, spacing_frames=50)

        # Patrol script - horizontal movement
        # patrol = MoveUntil((2, 0), infinite(), bounds=(0, 0, 800, 600), boundary_behavior="bounce")
        # group.script(patrol, tag="patrol")

        # Breakaway setup - timer-based
        """manager = BreakawayManager(group)
        manager.setup_breakaway(
            trigger="timer",
            seconds=3.0,
            count=3,
            strategy="deterministic",
            dive_path=dive_straight(start_x=400, start_y=400, end_x=400, end_y=100),
            dive_velocity=200,
        )
        group.set_breakaway_manager(manager)"""

        self.enemy_groups.append(group)

    def on_update(self, delta_time: float):
        """Update game state."""
        from arcadeactions.base import Action

        # Update all groups
        for group in self.enemy_groups:
            group.update(delta_time)

        # Update all actions
        Action.update_all(delta_time)

        # Update sprites (apply velocities)
        for group in self.enemy_groups:
            group.sprites.update(delta_time)

        self.player_list.update(delta_time)

    def on_draw(self):
        """Render the scene."""
        self.clear()

        # Draw enemies
        for group in self.enemy_groups:
            group.sprites.draw()

        # Draw player
        self.player_list.draw()

        # Draw text objects
        self.title_text.draw()
        self.instructions_text.draw()

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.ESCAPE:
            arcade.close_window()


def main():
    """Run the demo."""
    window = AttackGroupDemo()
    arcade.run()


if __name__ == "__main__":
    main()
