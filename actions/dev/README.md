# ArcadeActions Development Tools

Development-focused tools for ArcadeActions that enable hot-reload, visual editing, and rapid iteration workflows.

## FileWatcher

Monitors file system paths for changes and triggers callbacks when files are modified, with intelligent debouncing to prevent excessive reloads during rapid edits.

### Features

- **Multi-path monitoring**: Watch multiple directories simultaneously
- **Pattern filtering**: Only watch specific file types (e.g., `*.py`)
- **Debouncing**: Automatically batches rapid changes to prevent callback spam
- **Recursive watching**: Monitors subdirectories automatically
- **Context manager support**: Clean resource management with `with` statement
- **Thread-safe**: Uses background threads for efficient file monitoring

### Basic Usage

```python
from pathlib import Path
from actions.dev import FileWatcher

def on_files_changed(changed_files: list[Path]) -> None:
    print(f"Files changed: {[f.name for f in changed_files]}")
    # Trigger reload logic here

# Create and start watcher
watcher = FileWatcher(
    paths=["src/game/"],
    callback=on_files_changed,
    patterns=["*.py"],
    debounce_seconds=0.3
)
watcher.start()

# ... do work ...

watcher.stop()
```

### Context Manager

```python
from actions.dev import FileWatcher

with FileWatcher(paths=["src/"], callback=on_reload) as watcher:
    # Watcher automatically starts
    # ... do work ...
    pass
# Watcher automatically stops
```

### Parameters

- **paths** (`list[Path | str]`): Directories or files to watch
- **callback** (`Callable[[list[Path]], None]`): Function called with list of changed file paths
- **patterns** (`list[str] | None`): File patterns to watch (default: `["*.py"]`)
- **debounce_seconds** (`float`): Minimum quiet time before triggering callback (default: `0.3`)

### How Debouncing Works

When files change rapidly (e.g., saving multiple times in quick succession), the watcher:

1. Collects all changed file paths
2. Waits for a quiet period (no changes for `debounce_seconds`)
3. Calls the callback once with the accumulated list of changes

This prevents overwhelming your reload logic with redundant callbacks during active editing.

### Example: Hot-Reload Workflow

```python
import importlib
from pathlib import Path
from actions.dev import FileWatcher

# Modules to watch and reload
watched_modules = {
    Path("src/game/waves.py"): "game.waves",
    Path("src/game/enemies.py"): "game.enemies",
}

def reload_modules(changed_files: list[Path]) -> None:
    """Reload changed modules."""
    for file_path in changed_files:
        module_name = watched_modules.get(file_path.resolve())
        if module_name:
            try:
                module = __import__(module_name, fromlist=[''])
                importlib.reload(module)
                print(f"✓ Reloaded {module_name}")
            except Exception as e:
                print(f"✗ Error reloading {module_name}: {e}")

# Start watching
watcher = FileWatcher(
    paths=["src/game/"],
    callback=reload_modules,
    patterns=["*.py"],
    debounce_seconds=0.5
)
watcher.start()
```

### Threading Considerations

The FileWatcher uses background threads for efficient monitoring:

- File system events are handled in a watchdog observer thread
- Debouncing happens in a separate debounce worker thread
- Your callback is called from the debounce thread

**Important**: If your callback modifies game state, ensure proper synchronization. Consider using a queue to defer actual reload until the main game loop.

### Error Handling

Callbacks that raise exceptions won't crash the watcher:

```python
def safe_callback(changed_files: list[Path]) -> None:
    try:
        # Your reload logic here
        pass
    except Exception as e:
        print(f"Reload error: {e}")
        # Watcher continues running
```

### Performance

The FileWatcher is lightweight:

- Negligible CPU usage when files aren't changing
- Efficient event batching via debouncing
- Non-blocking (uses background threads)

For large codebases, consider narrowing the watch paths to only directories that contain hot-reloadable code.

## ReloadManager

High-level hot-reload orchestration that uses FileWatcher to automatically reload Python modules when files change, with state preservation and integration with the Action system.

### Features

- **Automatic module reloading**: Detects file changes and reloads Python modules using `importlib.reload()`
- **State preservation**: Captures sprite positions, action states, and custom game state before reload
- **Thread-safe queue**: Safely handles file change notifications from background thread
- **Visual feedback**: Optional flash indicator when reload completes
- **Error handling**: Gracefully handles reload failures without crashing
- **Action system integration**: Coordinates with ArcadeActions during reload

### Basic Usage

```python
from pathlib import Path
from actions.dev import enable_dev_mode

# Enable dev mode with hot-reload
manager = enable_dev_mode(
    watch_paths=["src/game/waves/"],
    root_path=Path("src/"),
    on_reload=lambda files, state: reconstruct_game(files, state)
)

# In game loop:
manager.process_reloads()  # Process queued reloads
manager.indicator.update(delta_time)
manager.indicator.draw()
```

### Advanced Usage

```python
from pathlib import Path
from actions.dev import enable_dev_mode

def on_reload(changed_files: list[Path], preserved_state: dict) -> None:
    """Called after modules are reloaded."""
    # Reconstruct game objects from new module definitions
    reconstruct_waves(preserved_state)

def state_provider() -> dict:
    """Capture custom game state before reload."""
    return {
        "player_score": player.score,
        "current_level": current_level,
        "enemy_count": len(enemies),
    }

def sprite_provider() -> list:
    """Provide sprites for state preservation."""
    # Return list of sprites to preserve positions/angles/scales
    return [player_sprite] + list(enemy_sprites)

manager = enable_dev_mode(
    watch_paths=["src/game/waves/", "src/game/enemies/"],
    root_path=Path("src/"),
    auto_reload=True,
    on_reload=on_reload,
    state_provider=state_provider,
    sprite_provider=sprite_provider,
    debounce_seconds=0.3,
)

# Start watching
manager.start()

# In game loop:
def on_update(delta_time: float) -> None:
    manager.process_reloads()
    manager.indicator.update(delta_time)
    Action.update_all(delta_time)

def on_draw() -> None:
    arcade.start_render()
    # ... draw game ...
    manager.indicator.draw()  # Draw reload flash
```

### Environment Variable

Enable dev mode automatically via environment variable:

```bash
ARCADEACTIONS_DEV=1 uv run python game.py
```

```python
from actions.dev import auto_enable_from_env

# Auto-enable if ARCADEACTIONS_DEV=1
manager = auto_enable_from_env()
if manager:
    # Dev mode enabled
    pass
```

### Manual Reload

Force reload specific files:

```python
# Reload specific files
manager.force_reload([Path("src/game/waves.py")])

# Reload all watched modules
manager.force_reload()
```

### State Preservation

ReloadManager automatically preserves:

- **Sprite state**: Position, angle, scale (for sprites provided by `sprite_provider`)
- **Action state**: Tags, elapsed time, pause status (for all active actions)
- **Custom state**: Provided by `state_provider` callback

State is captured before reload and passed to `on_reload` callback for reconstruction.

**Note**: To enable sprite state preservation, provide a `sprite_provider` callback that returns a list of sprites. Without this, only action and custom state will be preserved.

### Module Reload Strategy

ReloadManager:

1. Converts file paths to module names (e.g., `src/game/waves.py` → `game.waves`)
2. Clears `__pycache__` to ensure fresh reload from source
3. Invalidates import caches
4. Reloads modules using `importlib.reload()`
5. Handles errors gracefully

**Note**: Only modules that are already imported will be reloaded. Modules not yet imported are skipped.

### Thread Safety

- FileWatcher callbacks run in background thread
- Reload requests are queued thread-safely
- `process_reloads()` must be called from main thread (game loop)

### Visual Feedback

The `ReloadIndicator` provides a brief yellow flash overlay when reload completes:

```python
# Indicator is automatically created
manager.indicator.trigger()  # Manually trigger flash
manager.indicator.update(delta_time)  # Update animation
manager.indicator.draw()  # Draw overlay
```

### Error Handling

ReloadManager handles errors gracefully:

- Failed module reloads are logged but don't crash
- Exceptions in `state_provider` are caught and ignored
- Exceptions in `on_reload` callback are not caught (your responsibility)

### Keyboard Shortcut for Manual Reload

Enable keyboard shortcut for manual reload by calling `manager.on_key_press()` in your window's key handler:

```python
class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "My Game")
        self.manager = enable_dev_mode(
            watch_paths=["src/game/"],
            reload_key="R"  # Enable R key for manual reload
        )
    
    def on_key_press(self, key, modifiers):
        # Let reload manager handle keyboard shortcuts
        if self.manager:
            self.manager.on_key_press(key, modifiers)
```

Supported reload keys:
- `"R"` - R key (default)
- `"F5"` - F5 key
- `"F6"` - F6 key
- `None` - Disable keyboard shortcut

### State Preservation Control

Control whether state is preserved during reload:

```python
# Preserve state (default) - slower but maintains game state
manager = enable_dev_mode(
    watch_paths=["src/game/"],
    preserve_state=True,  # Default
    state_provider=lambda: {"score": player.score},
    sprite_provider=lambda: [player_sprite]
)

# Skip state preservation - faster but loses game state
manager = enable_dev_mode(
    watch_paths=["src/game/"],
    preserve_state=False  # Skip state preservation
)
```

When `preserve_state=False`:
- Reloads are faster (no state capture overhead)
- Sprite positions, action states, and custom state are NOT preserved
- Useful for quick iteration when state doesn't matter

When `preserve_state=True` (default):
- Sprite positions, angles, scales are preserved
- Action states (tags, elapsed time) are preserved
- Custom state from `state_provider` is preserved
- Slower but maintains game continuity

### Parameters

**enable_dev_mode()**:

- **watch_paths** (`list[Path | str] | None`): Directories to watch (default: current directory)
- **root_path** (`Path | str | None`): Root path for module resolution (default: inferred from watch_paths)
- **auto_reload** (`bool`): Automatically reload on file change (default: `True`)
- **preserve_state** (`bool`): Preserve game state across reloads (default: `True`)
- **reload_key** (`str | None`): Keyboard key for manual reload (default: `"R"`)
- **on_reload** (`Callable[[list[Path], dict], None] | None`): Callback after reload
- **state_provider** (`Callable[[], dict] | None`): Callback to capture custom state
- **sprite_provider** (`Callable[[], list] | None`): Callback to provide sprites for state preservation
- **patterns** (`list[str] | None`): File patterns to watch (default: `["*.py"]`)
- **debounce_seconds** (`float`): Debounce time for file changes (default: `0.3`)

### Example

See [examples/hot_reload_demo.py](../../examples/hot_reload_demo.py) for a complete working example.

## Coming Soon

- **DevVisualizer**: Visual editor for sprite positioning and animation tuning
- **SceneTemplates**: Save/load scene configurations

## See Also

- [Plan: 10× Developer Speed Boost](../../.cursor/plans/) - Full roadmap for development tools
- [Example: file_watcher_demo.py](../../examples/file_watcher_demo.py) - Live demonstration
- [Tests: test_file_watcher.py](../../tests/test_file_watcher.py) - Usage examples in tests

