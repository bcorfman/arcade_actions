"""
Game class that manages the entire game state, including clock, scheduler, sprites, and input.
"""

from typing import List, Optional, Dict, Set, Callable
import arcade
from .game_clock import GameClock, Scheduler
from .base import ActionSprite
from .group import AttackGroup, SpriteGroup


class Game(arcade.Window):
    """Central game class that manages all game state and systems.

    This class owns and coordinates:
    - Game clock and scheduler
    - Player and enemy sprites
    - Attack groups and patterns
    - Input handling
    - Pause/resume functionality
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Arcade Game",
        fullscreen: bool = False,
        resizable: bool = False,
        update_rate: float = 1 / 60,
        antialiasing: bool = True,
    ):
        super().__init__(
            width, height, title, fullscreen, resizable, update_rate, antialiasing
        )
        # Core systems
        self.clock = GameClock()
        self.scheduler = Scheduler(self.clock)

        # Sprite management
        self.player: Optional[ActionSprite] = None
        self.enemies: SpriteGroup = SpriteGroup()
        self.bullets: SpriteGroup = SpriteGroup()
        self.powerups: SpriteGroup = SpriteGroup()
        self.effects: SpriteGroup = SpriteGroup()

        # Attack groups
        self.attack_groups: List[AttackGroup] = []

        # Input state
        self.keys_pressed: Set[int] = set()
        self.mouse_position: tuple[float, float] = (0, 0)
        self.mouse_buttons: Set[int] = set()

        # Game state
        self.score: int = 0
        self.lives: int = 3
        self.level: int = 1
        self.game_over: bool = False

        # Callbacks
        self.on_pause_callbacks: List[Callable[[], None]] = []
        self.on_resume_callbacks: List[Callable[[], None]] = []
        self.on_game_over_callbacks: List[Callable[[], None]] = []
        self.on_level_complete_callbacks: List[Callable[[], None]] = []

    def setup(self):
        """Initialize the game state. Override this in your game."""
        pass

    def update(self, delta_time: float):
        """Update all game systems."""
        if self.clock.paused:
            return

        # Update core systems
        self.clock.update(delta_time)
        self.scheduler.update()

        # Update sprites
        if self.player:
            self.player.update(delta_time)
        self.enemies.update(delta_time)
        self.bullets.update(delta_time)
        self.powerups.update(delta_time)
        self.effects.update(delta_time)

        # Update attack groups
        for group in self.attack_groups[:]:  # Copy list since we might modify it
            group.update(delta_time)
            if group.is_destroyed:
                self.attack_groups.remove(group)

        # Update game logic
        self._update_game_logic(delta_time)

    def _update_game_logic(self, delta_time: float):
        """Update game-specific logic. Override this in your game."""
        pass

    def draw(self):
        """Draw all game elements."""
        self.clear()

        # Draw sprites
        self.enemies.draw()
        self.bullets.draw()
        self.powerups.draw()
        if self.player:
            self.player.draw()
        self.effects.draw()

        # Draw UI
        self._draw_ui()

    def _draw_ui(self):
        """Draw game UI elements. Override this in your game."""
        pass

    def pause(self):
        """Pause the entire game."""
        self.clock.paused = True
        for callback in self.on_pause_callbacks:
            callback()

    def resume(self):
        """Resume the game."""
        self.clock.paused = False
        for callback in self.on_resume_callbacks:
            callback()

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input."""
        self.keys_pressed.add(key)

        # Handle pause
        if key == arcade.key.P:
            if self.clock.paused:
                self.resume()
            else:
                self.pause()

        # Handle game-specific input
        self._handle_key_press(key, modifiers)

    def _handle_key_press(self, key: int, modifiers: int):
        """Handle game-specific keyboard input. Override this in your game."""
        pass

    def on_key_release(self, key: int, modifiers: int):
        """Handle keyboard release."""
        self.keys_pressed.discard(key)
        self._handle_key_release(key, modifiers)

    def _handle_key_release(self, key: int, modifiers: int):
        """Handle game-specific keyboard release. Override this in your game."""
        pass

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Handle mouse movement."""
        self.mouse_position = (x, y)
        self._handle_mouse_motion(x, y, dx, dy)

    def _handle_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Handle game-specific mouse movement. Override this in your game."""
        pass

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse button press."""
        self.mouse_buttons.add(button)
        self._handle_mouse_press(x, y, button, modifiers)

    def _handle_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle game-specific mouse press. Override this in your game."""
        pass

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse button release."""
        self.mouse_buttons.discard(button)
        self._handle_mouse_release(x, y, button, modifiers)

    def _handle_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Handle game-specific mouse release. Override this in your game."""
        pass

    def add_attack_group(self, group: AttackGroup):
        """Add an attack group to the game."""
        self.attack_groups.append(group)

    def remove_attack_group(self, group: AttackGroup):
        """Remove an attack group from the game."""
        if group in self.attack_groups:
            self.attack_groups.remove(group)

    def on_pause(self, callback: Callable[[], None]):
        """Register a callback for when the game is paused."""
        self.on_pause_callbacks.append(callback)

    def on_resume(self, callback: Callable[[], None]):
        """Register a callback for when the game is resumed."""
        self.on_resume_callbacks.append(callback)

    def on_game_over(self, callback: Callable[[], None]):
        """Register a callback for when the game is over."""
        self.on_game_over_callbacks.append(callback)

    def on_level_complete(self, callback: Callable[[], None]):
        """Register a callback for when a level is completed."""
        self.on_level_complete_callbacks.append(callback)

    def game_over(self):
        """Handle game over state."""
        self.game_over = True
        for callback in self.on_game_over_callbacks:
            callback()

    def level_complete(self):
        """Handle level completion."""
        self.level += 1
        for callback in self.on_level_complete_callbacks:
            callback()

    def reset(self):
        """Reset the game to its initial state."""
        # Reset core systems
        self.clock.reset()
        self.scheduler = Scheduler(self.clock)  # Create fresh scheduler

        # Clear all sprite groups
        self.player = None
        self.enemies = SpriteGroup()
        self.bullets = SpriteGroup()
        self.powerups = SpriteGroup()
        self.effects = SpriteGroup()

        # Clear attack groups
        for group in self.attack_groups:
            group.destroy()
        self.attack_groups.clear()

        # Reset game state
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False

        # Clear input state
        self.keys_pressed.clear()
        self.mouse_buttons.clear()
        self.mouse_position = (0, 0)

        # Re-initialize game
        self.setup()

    def __repr__(self) -> str:
        return (
            f"<Game level={self.level} score={self.score} lives={self.lives} "
            f"paused={self.clock.paused} game_over={self.game_over}>"
        )
