"""
ArcadeActions development tools - hot-reload, visualization, and editing utilities.

This module provides development-focused tools that extend ArcadeActions with
instant feedback, visual editing, and hot-reload capabilities.

Usage:
    from actions.dev import enable_dev_mode

    # Enable development mode (hot-reload + dev tools)
    enable_dev_mode(
        watch_paths=["src/my_game/waves/", "src/my_game/scenes/"],
        auto_reload=True,
        preserve_state=True,
        reload_key="R"
    )

    # In game loop:
    manager = enable_dev_mode(...)
    manager.process_reloads()  # Process queued reloads
    manager.indicator.update(delta_time)
    manager.indicator.draw()

    # Or use environment variable:
    # ARCADEACTIONS_DEV=1 uv run python game.py
"""

import os
from collections.abc import Callable
from pathlib import Path

from .reload import ReloadIndicator, ReloadManager
from .watch import FileWatcher

__all__ = [
    "FileWatcher",
    "ReloadManager",
    "ReloadIndicator",
    "enable_dev_mode",
    "auto_enable_from_env",
]


def enable_dev_mode(
    watch_paths: list[Path | str] | None = None,
    auto_reload: bool = True,
    preserve_state: bool = True,
    reload_key: str | None = "R",
    state_provider: Callable[[], dict] | None = None,
    on_reload: Callable[[list[Path], dict], None] | None = None,
    root_path: Path | str | None = None,
    patterns: list[str] | None = None,
    debounce_seconds: float = 0.3,
) -> ReloadManager:
    """
    Enable development mode with hot-reload functionality.

    Creates and starts a ReloadManager that monitors Python files for changes
    and automatically reloads them, preserving game state across reloads.

    Args:
        watch_paths: Directories to watch for changes (default: current directory)
        auto_reload: Automatically reload on file change (default: True)
        preserve_state: Preserve game state across reloads (default: True)
            Note: Currently always True - state is always preserved
        reload_key: Keyboard key for manual reload (default: "R")
            Use None to disable manual reload key
        state_provider: Optional callback to capture custom game state
            Should return a dictionary with game-specific state
        on_reload: Optional callback called after reload completes
            Receives (changed_files: list[Path], preserved_state: dict)
        root_path: Root path for module name resolution (default: current directory)
        patterns: File patterns to watch (default: ["*.py"])
        debounce_seconds: Debounce time for file changes (default: 0.3)

    Returns:
        ReloadManager instance - call .process_reloads() in game loop

    Example:
        def on_game_reload(files, state):
            # Reconstruct game objects after reload
            reconstruct_waves(state)

        manager = enable_dev_mode(
            watch_paths=["src/game/waves/"],
            on_reload=on_game_reload,
            state_provider=lambda: {"score": player.score, "level": current_level}
        )

        # In game loop:
        manager.process_reloads()
        manager.indicator.update(delta_time)
        manager.indicator.draw()
    """
    if watch_paths is None:
        watch_paths = [Path.cwd()]

    if root_path is None:
        # Try to infer root_path from watch_paths
        if watch_paths:
            # Use first watch path's parent as root, or the watch path itself
            first_path = Path(watch_paths[0])
            if first_path.is_file():
                root_path = first_path.parent
            elif first_path.is_dir():
                root_path = first_path
            else:
                root_path = Path.cwd()
        else:
            root_path = Path.cwd()

    manager = ReloadManager(
        watch_paths=watch_paths,
        root_path=root_path,
        auto_reload=auto_reload,
        state_provider=state_provider,
        on_reload=on_reload,
        patterns=patterns,
        debounce_seconds=debounce_seconds,
    )

    manager.start()

    # TODO: Integrate keyboard handler for reload_key when arcade.View integration is added
    # For now, manual reload can be done via manager.force_reload()

    return manager


def auto_enable_from_env() -> ReloadManager | None:
    """
    Auto-enable dev mode if ARCADEACTIONS_DEV environment variable is set.

    Checks for ARCADEACTIONS_DEV=1 and automatically enables hot-reload
    with default settings.

    Returns:
        ReloadManager instance if enabled, None otherwise

    Example:
        # In game.py:
        manager = auto_enable_from_env()
        if manager:
            # Dev mode enabled - call process_reloads() in loop
            pass
    """
    if os.environ.get("ARCADEACTIONS_DEV") == "1":
        return enable_dev_mode()
    return None
