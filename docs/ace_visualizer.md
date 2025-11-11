# ACE Visualizer Quick Start

The visualizer is an *attachable debugger* for ArcadeActions. Once it is on, you get:

- Inspector overlay with grouped action cards and progress bars.
- Action timeline viewer window with color-coded timeline bars (F4).
- Visual guides (velocity vectors, bounds rectangles, path splines).
- Global keyboard controls (F3–F9) for toggling panels, pausing, frame stepping, and snapshot export.

## Fastest path (recommended)

```bash
ARCADEACTIONS_VISUALIZER=1 uv run python examples/invaders.py
```

Setting `ARCADEACTIONS_VISUALIZER=1` is enough—`attach_visualizer()` is called for you as soon as `actions.visualizer` imports. Remove the environment variable to run normally.

While the debugger is active:

| Key | What happens |
| --- | --- |
| F3 | Toggle inspector overlay |
| F4 | Toggle action timeline viewer window |
| F5 | Toggle all visual guides |
| F6 | Pause / resume the action system |
| F7 | Step a single frame (only when paused) |
| F8 | Cycle the highlighted target group |
| F9 | Dump a JSON snapshot (`snapshots/snapshot_<timestamp>.json`) |

Snapshots include the current frame/time, active actions, lifecycle events, and the most recent condition evaluations.

The F4 shortcut toggles the dedicated action timeline viewer window. The window is OS-resizable and draggable, and displays action lifetime timeline bars. Timeline bars are color-coded to distinguish between SpriteList actions (cyan/teal) and Sprite actions (orange), with different brightness levels for active vs inactive states. This color scheme is designed to be distinguishable for users with color vision differences. Condition evaluations are not shown in the window but can be saved with F9 and viewed later in the snapshot JSON. Closing the window or pressing F4 again hides it without affecting the in-game overlay.

## Single-line attach (manual opt‑in)

```python
from actions.visualizer import attach_visualizer

attach_visualizer()
```

- Call once during startup (e.g. in `View.__init__`) to opt-in without using environment variables.
- Everything else—overlay, guides, condition debugger, timeline, keyboard shortcuts—is wired automatically.
- Customize as needed:
  - `snapshot_directory="debug_snapshots"`
  - `sprite_positions_provider=lambda: {id(s): s.position for s in self.enemies}`

## Attach later (runtime hot-key)

```python
from actions.visualizer import enable_visualizer_hotkey

enable_visualizer_hotkey()  # registers Shift+F3 on the active window
```

Press **Shift+F3** any time during play to attach the debugger without restarting the game.

## When you need more control

The helper manages everything for typical use. If you want to drive the components yourself (for custom UI layouts or tooling), you can still create `InspectorOverlay`, `GuideManager`, `ConditionDebugger`, `TimelineStrip`, and `DebugControlManager` manually and call their `update()` methods inside your game loop. This is entirely optional.

## Validation checklist

1. `uv run python -m pytest tests/test_visualizer_performance.py` — sanity/stress test (≈250 actions).
2. `uv run python -m pytest tests/test_visualizer_controls.py` — keyboard shortcut coverage.
3. Play an example (e.g. `examples/invaders.py`) with the debugger attached, press F3–F9, and confirm overlays behave as expected.
4. Inspect the generated snapshot JSON to verify statistics, events, and evaluations are recorded.
