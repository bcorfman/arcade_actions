# ArcadeActions Visualizer Guide

The visualizer is an *attachable debugger* for ArcadeActions that provides real-time visibility into your game's action system.

## How to Enable

### Environment Variable (Recommended)

Set the environment variable before running your game:

```bash
ARCADEACTIONS_VISUALIZER=1 uv run python examples/space_clutter.py
```

Setting `ARCADEACTIONS_VISUALIZER=1` is enough—`attach_visualizer()` is called for you automatically. Remove the environment variable to run normally.

### Programmatic Attach (Manual Opt-in)

```python
from actions.visualizer import attach_visualizer

attach_visualizer()
```

Call this once during startup (e.g. in `View.__init__`) to opt-in without using environment variables. Everything else—overlay, guides, condition debugger, timeline, keyboard shortcuts—is wired automatically.

You can customize the visualizer:
```python
attach_visualizer(
    snapshot_directory="debug_snapshots",
    sprite_positions_provider=lambda: {id(s): s.position for s in self.enemies}
)
```

### Runtime Hot-Key Attachment

```python
from actions.visualizer import enable_visualizer_hotkey

enable_visualizer_hotkey()  # registers Shift+F3 on the active window
```

Press **Shift+F3** any time during play to attach the debugger without restarting the game.

## What You'll See

When the visualizer is enabled, you get:

1. **Inspector Overlay** - A panel at the top-left of your game window showing:
   - All active actions
   - Their targets (sprites/sprite lists)
   - Progress bars for actions that report progress
   - Current state information

2. **ACE Action Timeline Window** - A separate window showing:
   - Timeline bars for each action's lifetime
   - Color-coded by target type (Cyan=SpriteList, Orange=Sprite)
   - Start/end frames for completed actions
   - Active actions extend to the right edge

3. **Visual Guides** - Overlays on the game window:
   - Velocity vectors showing sprite movement direction and speed
   - Bounds rectangles for boundary detection
   - Path splines for complex movement patterns

4. **Condition Debugger** - Internal state tracking for condition evaluations, providing behavior-level visibility

## Keyboard Shortcuts

Press these keys while the game window is focused:

| Key | Function | What Happens |
|-----|----------|--------------|
| **F3** | Toggle Inspector Overlay | Shows/hides the overlay panel in the game window |
| **F4** | Toggle Timeline Window | Shows/hides the separate "ACE Action Timeline" window |
| **F5** | Toggle Visual Guides | Shows/hides velocity arrows, bounds rectangles, and path trails (F8 highlight boxes are always shown) |
| **F6** | Pause/Resume Actions | Freezes/unfreezes all action updates |
| **F7** | Step One Frame | When paused, advances actions by one frame |
| **F8** | Highlight Next Group | Cycles through target groups, highlighting each in the overlay with cyan color |
| **F9** | Export Snapshot | Saves current action state to `snapshots/snapshot_<timestamp>.json` |

Snapshots include the current frame/time, active actions, lifecycle events, and the most recent condition evaluations.

## Understanding F8 (Target Group Highlighting)

When you press F8, it cycles through each target group, providing both overlay and visual highlighting:

### In the Inspector Overlay:
- **Highlighted groups** appear with **cyan** header text
- **Normal groups** appear with **yellow** header text
- Pressing F8 repeatedly cycles through all groups and wraps around

### In the Game Window:
- **Lime green bounding boxes** are drawn around the highlighted sprite(s)
- For **single sprites**: One box around that sprite
- For **sprite lists**: Boxes around every sprite in the list
- Boxes have thick (3px) borders for easy visibility

This dual highlighting helps you:
- Identify which sprite/sprite_list a group of actions belongs to
- See exactly where the target is in your game world
- Track down specific actions when many are active
- Debug spatial issues by connecting actions to visible sprites

**Example:** In the invaders game, pressing F8 will cycle through:
1. `self.enemy_list` → Green boxes around ALL enemy sprites
2. Individual bullet sprites → Green box around each bullet
3. `self.player_sprite` → Green box around the player

## Visual Overlay Details

The inspector overlay (toggled with F3) shows information like:

```
ACE Inspector - 2 action(s)
```

## Understanding F4 (Timeline Window)

When you press F4:
- A separate window titled **"ACE Action Timeline"** will appear (or disappear if already visible)
- This window shows horizontal bars representing each action's lifetime
- The window can be resized and repositioned
- If no actions are active, the window will be empty
- Press F4 again to hide the window

**Note:** The timeline window is initially **hidden** by default. Press F4 once to show it.


## Troubleshooting

### "I press F4 but nothing happens"

**Check:**
1. Make sure you're pressing F4 while the **game window** has focus (not the terminal)
2. The timeline window might appear behind other windows - check your taskbar
3. The window starts hidden - press F4 to show it the first time
4. Look for a window titled "ACE Action Timeline"

### "The overlay is blocking my game"

- Press **F3** to toggle it off
- The overlay is positioned at the top-left by default
- It's semi-transparent and shouldn't block most gameplay

### "I don't see any actions in the timeline"

- Actions only appear when they're active
- Try moving your player or spawning enemies to create actions
- The space_clutter demo uses actions for star movement, enemies, and bullets

### "F6 only pauses part of my game"

- All movement in your game must involve Actions for the pause feature to work correctly.
- If you use the Arcade library to manage sprites separately from Arcade, then you will also need to implement a pause feature for Arcade as well.
- My suggestion is to just manage *all* sprite movement with ArcadeActions instead.

## Example Session

```bash
# Start the game with visualizer
ARCADEACTIONS_VISUALIZER=1 uv run python examples/space_clutter.py

# In the game window:
# 1. Press F3 to see the inspector overlay (top-left corner)
# 2. Press F4 to open the timeline window (separate window)
# 3. Press F5 to see velocity arrows on moving sprites
# 4. Press F6 to pause, F7 to step frame-by-frame
# 5. Play the game and watch actions appear/disappear in real-time
```

## Advanced Control

For typical use cases, the helper functions (`attach_visualizer()` or environment variable) manage everything automatically. However, if you need custom UI layouts or specialized tooling, you can create and manage the components manually:

- `InspectorOverlay` - The in-game action display panel
- `GuideManager` - Visual guides for velocity, bounds, and paths
- `ConditionDebugger` - Condition evaluation tracking
- `TimelineStrip` - Timeline visualization component
- `DebugControlManager` - Keyboard shortcut handler

Call their `update()` methods inside your game loop for full control. This is entirely optional and only needed for advanced customization.

## Technical Details

- **Inspector Overlay**: Rendered directly on the game window using Arcade's drawing primitives
- **Timeline Window**: A separate `arcade.Window` instance managed independently
- **Visual Guides**: Drawn as overlays on the game window (velocity arrows, bounds boxes, paths)
- **Condition Debugger**: Internal state tracking for condition evaluations (toggled with F4)

## Performance Impact

The visualizer adds some overhead:
- Minimal impact on gameplay (< 5% typically)
- Text rendering is optimized using `arcade.Text` objects
- Timeline updates are deferred until the window is visible
- No impact when `ARCADEACTIONS_VISUALIZER` is not set

## Validation

To verify the visualizer is working correctly:

1. `uv run python -m pytest tests/integration/test_visualizer_performance.py` — sanity/stress test (≈250 actions)
2. `uv run python -m pytest tests/integration/test_visualizer_controls.py` — keyboard shortcut coverage
3. Play an example (e.g. `examples/invaders.py`) with the debugger attached, press F3–F9, and confirm overlays behave as expected
4. Inspect the generated snapshot JSON to verify statistics, events, and evaluations are recorded
