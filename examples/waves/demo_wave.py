"""
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
            enemy = SpriteSolidColor(40, 40, self.enemy_color)
            enemy.center_x = 100 + i * 100
            enemy.center_y = self.spawn_y

            # Make enemies move down
            MoveUntil((0, -2), infinite()).apply(enemy, tag="move_down")
            enemies.append(enemy)

        return enemies
