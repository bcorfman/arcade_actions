# ACE Visualizer Overview

The ACE visualizer adds in-engine observability for ArcadeActions. It exposes runtime state through an inspector overlay, condition debugger, timeline strip, visual guides, and configurable keyboard shortcuts.

## Instrumentation

1. Create a `DebugDataStore` and inject it into `Action`:

```python
from actions import Action
from actions.visualizer import DebugDataStore

store = DebugDataStore()
Action.set_debug_store(store)
Action._enable_visualizer = True
```

2. Run `Action.update_all(delta_time)` as usual. The store collects snapshots, events, and condition evaluations automatically.

## Overlay + Renderer

```python
from actions.visualizer import InspectorOverlay, OverlayRenderer

overlay = InspectorOverlay(debug_store=store)
renderer = OverlayRenderer(overlay)

def on_update(self, delta_time):
    Action.update_all(delta_time)
    overlay.update()
    renderer.update()

def on_draw(self):
    renderer.draw()
```

- Groups are clustered by target (sprite or sprite list).
- `highlight_next()` / `highlight_previous()` cycle focus between groups.
- Filtering by tag is available during instantiation: `InspectorOverlay(..., filter_tag="movement")`.

## Visual Guides

```python
from actions.visualizer import GuideManager

guides = GuideManager()

sprite_positions = {snapshot.target_id: (snapshot.target_id * 20, 50)
                    for snapshot in store.get_all_snapshots()}

guides.update(store.get_all_snapshots(), sprite_positions)
```

- Velocity vectors (green) mark direction/magnitude using sprite positions.
- Bounds rectangles (red) are deduplicated automatically.
- Path splines (blue) render `FollowPathUntil` metadata.
- Guides can be toggled individually or all at once.

## Condition Debugger & Timeline

```python
from actions.visualizer import ConditionDebugger, TimelineStrip

condition_debugger = ConditionDebugger(store, max_entries=100)
timeline = TimelineStrip(store, max_entries=100)

condition_debugger.update()
timeline.update()
```

- Condition debugger lists the most recent evaluations, including captured variables and tags.
- Timeline strip aggregates lifecycle events (`created`, `started`, `stopped`, `removed`) to indicate active vs. finished actions.

## Debug Controls

```python
from pathlib import Path
from actions.visualizer import DebugControlManager, GuideManager

class GameView(arcade.View):
    def __init__(self):
        self.store = DebugDataStore()
        Action.set_debug_store(self.store)
        Action._enable_visualizer = True

        self.overlay = InspectorOverlay(self.store)
        self.guides = GuideManager()
        self.condition_debugger = ConditionDebugger(self.store)
        self.timeline = TimelineStrip(self.store)

        self.control_manager = DebugControlManager(
            overlay=self.overlay,
            guides=self.guides,
            condition_debugger=self.condition_debugger,
            timeline=self.timeline,
            snapshot_directory=Path("snapshots"),
            action_controller=Action,
            step_delta=1/60,
        )

    def on_key_press(self, key, modifiers):
        if self.control_manager.handle_key_press(key, modifiers):
            return
        super().on_key_press(key, modifiers)
```

### Keyboard Shortcuts

| Key | Action |
| --- | --- |
| F3 | Toggle inspector overlay |
| F4 | Toggle condition debugger visibility |
| F5 | Toggle all visual guides |
| F6 | Pause/Resume global actions |
| F7 | Step forward one frame (while paused) |
| F8 | Highlight next target group |
| F9 | Export snapshot (`snapshots/snapshot_<timestamp>.json`) |

Snapshots contain statistics, active snapshots, recorded events, and condition evaluations for offline diagnostics.

## Stress Testing

`tests/test_visualizer_performance.py` populates 250 snapshot entries and exercises overlay, renderer, guides, condition debugger, and timeline to ensure scale and stability. Run with:

```bash
uv run python -m pytest tests/test_visualizer_performance.py -v
```

## Summary

1. Inject `DebugDataStore` into `Action`.
2. Create `InspectorOverlay`, `GuideManager`, `ConditionDebugger`, and `TimelineStrip` as needed.
3. Use `DebugControlManager` to wire global shortcuts, pause/step controls, and snapshot export.
4. Optional: integrate `OverlayRenderer` inside `on_draw` for archival visuals.
```EOF

## Validation Checklist

1. Run `uv run python -m pytest tests/test_visualizer_performance.py` to ensure overlays and guides handle 250+ actions.
2. Run `uv run python -m pytest tests/test_visualizer_controls.py` to confirm keyboard shortcuts toggle the correct systems, pause/resume, and export snapshots.
3. Launch a sample Arcade view with `InspectorOverlay`, `OverlayRenderer`, and `DebugControlManager` wired as described above. Press F3–F9 to verify visual feedback and snapshot output.
4. Inspect the generated snapshot JSON in `snapshots/` to confirm statistics, snapshots, events, and evaluations are captured.
