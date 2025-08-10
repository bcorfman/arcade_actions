"""
Example demonstrating the repeat() function with wave patterns.

This example shows how to create a repeating wave pattern that goes forward,
then backward, then repeats endlessly - perfect for Galaga-style swaying movement.
"""

import arcade

from actions import Action, repeat
from actions.formation import arrange_grid


class RepeatingWaveExample(arcade.Window):
    """Example window showing repeating wave patterns."""

    def __init__(self):
        super().__init__(800, 600, "Repeating Wave Pattern Example")

        # Create a grid of enemy sprites that fills most of the screen width
        # Leave margins for wave movement
        margin = 60  # Space at edges for wave movement
        screen_width = 800 - (2 * margin)  # Usable width
        cols = 5
        rows = 4
        spacing_x = screen_width / cols if cols > 1 else 0

        self.enemies = arrange_grid(
            rows=rows,
            cols=cols,
            start_x=margin,
            start_y=400,
            spacing_x=spacing_x,
            spacing_y=50,
            sprite_factory=lambda: arcade.Sprite(":resources:images/enemies/slimeBlue.png"),
        )

        # Prepare instructional text objects (avoid slow draw_text on every frame)
        self.header_text = arcade.Text(
            "Repeating Movement Pattern Example",
            10,
            self.height - 30,
            arcade.color.WHITE,
            16,
        )
        self.caption_text = arcade.Text(
            "Enemies move back and forth: right, then left, then repeat (no Y drift)",
            10,
            self.height - 50,
            arcade.color.WHITE,
            12,
        )

        # Create the repeating wave pattern using new create_wave_pattern
        from actions import sequence
        from actions.pattern import create_wave_pattern

        forward_wave = create_wave_pattern(
            amplitude=30,
            length=120,
            speed=60,
        )

        backward_wave = create_wave_pattern(
            amplitude=30,
            length=120,
            speed=60,
        )

        wave_sequence = sequence(forward_wave, backward_wave)
        self.repeating_wave = repeat(wave_sequence)

        # Apply the repeating wave action to all enemies
        self.repeating_wave.apply(self.enemies, tag="repeating_wave")

    def on_draw(self):
        self.clear()
        self.enemies.draw()
        self.header_text.draw()
        self.caption_text.draw()

    def on_update(self, delta_time):
        # Update all actions (including the repeating wave pattern)
        Action.update_all(delta_time)
        self.enemies.update()


def main():
    """Run the example."""
    window = RepeatingWaveExample()
    window.run()


if __name__ == "__main__":
    main()
