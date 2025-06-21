"""
Game class that manages the entire game state, including clock, scheduler, and input.
"""

from collections.abc import Callable

import arcade


class Game(arcade.Window):
    """Central game class that manages all game state and systems.

    This class owns and coordinates:
    - Game clock and scheduler
    - Input handling
    - Pause/resume functionality
    - View management
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
        """Create a new game window."""
        super().__init__(width, height, title, fullscreen, resizable, update_rate, antialiasing)

        # Input state
        self.keys_pressed: set[int] = set()
        self.mouse_position: tuple[float, float] = (0, 0)
        self.mouse_buttons: set[int] = set()

        # Game state
        self.score: int = 0
        self.lives: int = 3
        self.level: int = 1
        self.game_over: bool = False

        # View management
        self._current_view: arcade.View | None = None
        self._views: dict[str, arcade.View] = {}

        # Callbacks
        self.on_pause_callbacks: list[Callable[[], None]] = []
        self.on_resume_callbacks: list[Callable[[], None]] = []
        self.on_game_over_callbacks: list[Callable[[], None]] = []
        self.on_level_complete_callbacks: list[Callable[[], None]] = []

    def setup(self):
        """Initialize the game state. Override this in your game."""
        pass

    def update(self, delta_time: float):
        """Update all game systems."""
        if self.clock.paused:
            return

        # Update current view if it exists
        if self._current_view:
            self._current_view.on_update(delta_time)

    def on_draw(self):
        """Draw all game elements."""
        self.clear()

        # Draw current view if it exists
        if self._current_view:
            self._current_view.on_draw()
            return True
        return False

    def show_view(self, view: arcade.View):
        """Show a view and add it to the view dictionary if it has a name."""
        super().show_view(view)
        self._current_view = view
        try:
            name: str | None = view.name  # type: ignore[attr-defined]
        except AttributeError:
            name = None  # Fallback when view lacks a ``name`` attribute

        if name:
            self._views[name] = view

    def get_view(self, name: str) -> arcade.View | None:
        """Get a view by name."""
        return self._views.get(name)

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

        # Forward to current view
        if self._current_view:
            self._current_view.on_key_press(key, modifiers)

    def on_key_release(self, key: int, modifiers: int):
        """Handle keyboard release."""
        self.keys_pressed.discard(key)
        if self._current_view:
            self._current_view.on_key_release(key, modifiers)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Handle mouse movement."""
        self.mouse_position = (x, y)
        if self._current_view:
            self._current_view.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse button press."""
        self.mouse_buttons.add(button)
        if self._current_view:
            self._current_view.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse button release."""
        self.mouse_buttons.discard(button)
        if self._current_view:
            self._current_view.on_mouse_release(x, y, button, modifiers)

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
        self.clock.paused = False

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
