"""Hot-reload manager for ArcadeActions games.

Provides automatic reloading of Python modules when files change,
with state preservation and integration with the Action system.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from queue import Empty, Queue

import arcade

from actions import Action
from actions.dev.watch import FileWatcher


class ReloadIndicator:
    """
    Visual feedback indicator for hot-reload events.

    Shows a brief flash overlay when a reload completes,
    providing visual confirmation that the reload happened.
    """

    def __init__(self, flash_duration: float = 0.2):
        """
        Initialize reload indicator.

        Args:
            flash_duration: Duration of flash effect in seconds (default: 0.2)
        """
        self._flash_alpha = 0.0
        self._flash_duration = flash_duration

    def trigger(self) -> None:
        """Start the flash effect."""
        self._flash_alpha = 1.0

    def update(self, delta_time: float) -> None:
        """
        Update flash animation.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - delta_time / self._flash_duration)

    def draw(self) -> None:
        """Draw flash overlay on screen."""
        if self._flash_alpha <= 0:
            return

        # Draw semi-transparent overlay
        # Get window dimensions if available
        try:
            window = arcade.get_window()
            if window:
                width = window.width
                height = window.height
                arcade.draw_lrtb_rectangle_filled(0, width, height, 0, (255, 255, 0, int(64 * self._flash_alpha)))
        except Exception:
            # Window not available (headless test environment) - skip drawing
            pass

    @property
    def is_flashing(self) -> bool:
        """Check if flash is currently active."""
        return self._flash_alpha > 0


class ReloadManager:
    """
    Manages hot-reload functionality for ArcadeActions games.

    Monitors Python files for changes, reloads modules, and preserves
    game state across reloads. Integrates with the Action system to
    pause/resume during reload operations.

    Example:
        manager = ReloadManager(
            watch_paths=["src/game/"],
            root_path=Path("src/"),
            on_reload=reconstruct_game_objects
        )
        manager.start()

        # In game loop:
        manager.process_reloads()  # Process queued reloads
        manager.indicator.update(delta_time)
        manager.indicator.draw()
    """

    def __init__(
        self,
        watch_paths: list[Path | str] | None = None,
        root_path: Path | str | None = None,
        auto_reload: bool = True,
        preserve_state: bool = True,
        state_provider: Callable[[], dict] | None = None,
        sprite_provider: Callable[[], list] | None = None,
        on_reload: Callable[[list[Path], dict], None] | None = None,
        patterns: list[str] | None = None,
        debounce_seconds: float = 0.3,
    ):
        """
        Initialize reload manager.

        Args:
            watch_paths: Directories to watch for changes (default: current directory)
            root_path: Root path for module name resolution (default: current directory)
            auto_reload: Automatically reload on file change (default: True)
            preserve_state: Preserve game state across reloads (default: True)
            state_provider: Optional callback to capture custom game state
            sprite_provider: Optional callback to provide sprites for state preservation
            on_reload: Optional callback called after reload with (files, state)
            patterns: File patterns to watch (default: ["*.py"])
            debounce_seconds: Debounce time for file changes (default: 0.3)
        """
        self.watch_paths = [Path(p) for p in (watch_paths or [Path.cwd()])]
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.auto_reload = auto_reload
        self.preserve_state = preserve_state
        self.state_provider = state_provider
        self.sprite_provider = sprite_provider
        self.on_reload = on_reload
        self.patterns = patterns or ["*.py"]
        self.debounce_seconds = debounce_seconds

        self._reload_queue: Queue[list[Path]] = Queue()
        self._file_watcher: FileWatcher | None = None
        self.indicator = ReloadIndicator()
        self.reload_key: str | None = None

    def start(self) -> None:
        """Start watching files and enable hot-reload."""
        if self._file_watcher is not None:
            return

        if self.auto_reload:
            self._file_watcher = FileWatcher(
                paths=self.watch_paths,
                callback=self._on_files_changed,
                patterns=self.patterns,
                debounce_seconds=self.debounce_seconds,
            )
            self._file_watcher.start()

    def stop(self) -> None:
        """Stop watching files."""
        if self._file_watcher is not None:
            self._file_watcher.stop()
            self._file_watcher = None

    def is_watching(self) -> bool:
        """Check if file watching is active."""
        return self._file_watcher is not None and self._file_watcher.is_running()

    def _on_files_changed(self, changed_files: list[Path]) -> None:
        """
        Handle file change notification from FileWatcher.

        Called from background thread - queues reload request for main thread.

        Args:
            changed_files: List of changed file paths
        """
        if self.auto_reload:
            self._reload_queue.put(changed_files)

    def process_reloads(self) -> None:
        """
        Process queued reload requests from main thread.

        Call this once per frame in your game loop to handle
        file changes detected by the background watcher thread.
        """
        while not self._reload_queue.empty():
            try:
                changed_files = self._reload_queue.get_nowait()
                self._perform_reload(changed_files)
            except Empty:
                break

    def _perform_reload(self, changed_files: list[Path]) -> None:
        """
        Execute reload operation in main thread.

        Args:
            changed_files: List of file paths that changed
        """
        # 1. Preserve state if enabled
        saved_state = {}
        if self.preserve_state:
            sprites_to_preserve = []
            if self.sprite_provider:
                try:
                    sprites_to_preserve = self.sprite_provider()
                except Exception:
                    # Ignore errors in sprite provider
                    sprites_to_preserve = []
            saved_state = self._preserve_state(sprites_to_preserve)

        # 2. Reload modules
        reloaded = []
        for file_path in changed_files:
            if self._reload_module(file_path, self.root_path):
                reloaded.append(file_path)

        # 3. Trigger reload callback (call even if no files reloaded to notify of attempt)
        if self.on_reload:
            self.on_reload(reloaded, saved_state)

        # 4. Visual feedback
        self.indicator.trigger()

    def _preserve_state(self, sprite_list: list) -> dict:
        """
        Capture current game state before reload.

        Args:
            sprite_list: List of sprites to preserve (optional - can be empty)

        Returns:
            Dictionary containing preserved state
        """
        state = {
            "sprites": {},
            "actions": {},
            "custom": {},
        }

        # Preserve sprite state
        for sprite in sprite_list:
            sprite_id = id(sprite)
            # Handle scale - Arcade sprites can have scale as float or tuple (scale_x, scale_y)
            scale = sprite.scale
            scale_x: float
            scale_y: float
            if isinstance(scale, tuple):
                if len(scale) >= 2:
                    scale_x = float(scale[0])
                    scale_y = float(scale[1])
                elif len(scale) == 1:
                    scale_x = float(scale[0])
                    scale_y = float(scale[0])
                else:
                    scale_x = 1.0
                    scale_y = 1.0
            elif isinstance(scale, (int, float)):
                scale_x = float(scale)
                scale_y = float(scale)
            else:
                scale_x = 1.0
                scale_y = 1.0
            state["sprites"][sprite_id] = {
                "position": (sprite.center_x, sprite.center_y),
                "angle": sprite.angle,
                "scale": (scale_x, scale_y),
            }

        # Preserve action state
        for action in Action._active_actions:
            action_id = id(action)
            state["actions"][action_id] = {
                "tag": action.tag,
                "elapsed": action._elapsed,
                "paused": action._paused,
            }

        # Preserve custom state
        if self.state_provider:
            try:
                state["custom"] = self.state_provider()
            except Exception:
                # Ignore errors in state provider
                pass

        return state

    def _reload_module(self, file_path: Path, root_path: Path) -> bool:
        """
        Reload a Python module from file path.

        Args:
            file_path: Path to Python file
            root_path: Root path for module resolution

        Returns:
            True if module was reloaded, False otherwise
        """
        module_name = self._path_to_module_name(file_path, root_path)
        if module_name is None:
            return False

        if module_name not in sys.modules:
            return False

        try:
            module = sys.modules[module_name]

            # Clear __pycache__ to ensure fresh reload from source
            if hasattr(module, "__file__") and module.__file__:
                import shutil

                module_dir = Path(module.__file__).parent
                cache_dir = module_dir / "__pycache__"
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)

            # Invalidate import caches
            importlib.invalidate_caches()

            # Reload the module
            importlib.reload(module)
            return True
        except Exception as e:
            # Log error but don't crash
            print(f"Error reloading {module_name}: {e}")
            return False

    def _path_to_module_name(self, file_path: Path, root_path: Path) -> str | None:
        """
        Convert file path to Python module name.

        Args:
            file_path: Path to Python file (may be relative or absolute)
            root_path: Root path for relative resolution (may be relative or absolute)

        Returns:
            Module name (e.g., "game.waves") or None if path is outside root
        """
        try:
            # Resolve both paths to absolute to ensure relative_to() works correctly
            # FileWatcher provides absolute paths, but root_path might be relative
            file_path = file_path.resolve()
            root_path = root_path.resolve()

            relative = file_path.relative_to(root_path)
            parts = relative.with_suffix("").parts
            if not parts:
                return None
            if parts[-1] == "__init__":
                parts = parts[:-1]
            return ".".join(parts) if parts else None
        except ValueError:
            # Path is outside root
            return None

    def force_reload(self, files: list[Path] | None = None) -> None:
        """
        Force reload of specified files or all watched modules.

        Args:
            files: List of file paths to reload, or None to reload all watched modules
        """
        if files is None:
            # Collect all Python files from watch paths
            files = []
            for watch_path in self.watch_paths:
                if watch_path.is_dir():
                    files.extend(watch_path.rglob("*.py"))
                elif watch_path.is_file() and watch_path.suffix == ".py":
                    files.append(watch_path)

        self._perform_reload(files)

    def on_key_press(self, key: int, modifiers: int) -> bool:
        """
        Handle keyboard shortcut for manual reload.

        Call this from your arcade.Window's on_key_press method to enable
        keyboard shortcuts for reloading.

        Args:
            key: Arcade key code
            modifiers: Keyboard modifiers

        Returns:
            True if reload was triggered, False otherwise

        Example:
            def on_key_press(self, key, modifiers):
                if self.reload_manager:
                    self.reload_manager.on_key_press(key, modifiers)
        """
        if self.reload_key is None:
            return False

        # Import arcade here to avoid dependency issues
        import arcade

        # Map reload_key string to arcade key code
        key_map = {
            "R": arcade.key.R,
            "F5": arcade.key.F5,
            "F6": arcade.key.F6,
        }

        reload_key_code = key_map.get(self.reload_key.upper())
        if reload_key_code is not None and key == reload_key_code:
            self.force_reload()
            return True

        return False
