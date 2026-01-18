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
from arcadeactions.visualizer import attach_visualizer

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
from arcadeactions.visualizer import enable_visualizer_hotkey

enable_visualizer_hotkey()  # registers Shift+F3 on the active window
```

Press **Shift+F3** any time during play to attach the debugger without restarting the game.

## What You'll See

When the visualizer is enabled, you get:

1. **Inspector Overlay** - A single-line action counter that cycles through 4 corner positions:
   - Shows: "ACE Visualizer - N actions"
   - Press F3 to cycle: upper-left → upper-right → lower-right → lower-left → off → upper-left

2. **ACE Action Timeline Window** - A separate window (press F4) showing:
   - Timeline bars for each action's lifetime
   - Color-coded by target type (Cyan=SpriteList, Orange=Sprite)
   - Start/end frames for completed actions
   - Active actions extend to the right edge
   - **Green outlines** around timeline bars for the F8-highlighted target

3. **Visual Guides** - Overlays on the game window (F5 toggle)
   - Velocity vectors showing sprite movement direction and speed 
   - Bounds rectangles for boundary detection 
   - Path splines for complex movement patterns 
   - **Lime green bounding boxes** around F8-highlighted sprites (always shown)

4. **Condition Debugger** - Internal state tracking for condition evaluations, providing behavior-level visibility

## Keyboard Shortcuts

Press these keys while the game window is focused:

| Key | Function | What Happens |
|-----|----------|--------------|
| **F3** | Cycle Overlay Position | Cycles the action counter through corners: upper-left → upper-right → lower-right → lower-left → off |
| **F4** | Toggle Timeline Window | Shows/hides the separate "ACE Action Timeline" window |
| **F5** | Toggle Visual Guides | Shows/hides velocity arrows, bounds rectangles, and path trails (F8 highlight boxes are always shown) |
| **F6** | Pause/Resume Actions | Freezes/unfreezes all action updates |
| **F7** | Step One Frame | When paused, advances actions by one frame |
| **F8** | Highlight Next Group | Cycles through target groups, highlighting each in the overlay with cyan color |
| **F9** | Export Snapshot | Saves current action state to `snapshots/snapshot_<timestamp>.json` |

Snapshots include the current frame/time, active actions, lifecycle events, and the most recent condition evaluations.

## Understanding F8 (Target Group Highlighting)

When you press F8, it cycles through each target (sprite or sprite list) with visual highlighting in **two places**:

### In the Game Window:
- **Lime green bounding boxes** (3px thick) are drawn around the highlighted sprite(s)
- For **single sprites**: One box around that sprite
- For **sprite lists**: Boxes around every sprite in the list

### In the Timeline Window (F4):
- **Lime green outlines** (3px thick) are drawn around timeline bars for the highlighted target
- Makes it easy to see all actions affecting the selected target
- Helps track action timing and lifecycle for specific sprites

### How It Works:
- F8 cycles through all unique targets that have actions
- The simple "ACE Visualizer - N actions" overlay stays unchanged
- Highlighting is purely visual (no filtering - all actions still shown)
- Press F8 repeatedly to cycle through all targets and wrap around

This highlighting helps you:
- Identify which sprite/sprite_list a group of actions belongs to
- See exactly where the target is in your game world
- Track down specific actions when many are active
- Debug spatial and timing issues by connecting actions to visible sprites

**Example:** In the invaders game, pressing F8 will cycle through:
1. `self.enemy_list` → Green boxes around ALL enemy sprites + green outlines on enemy movement/firing actions in timeline
2. Individual bullet sprites → Green box around each bullet + green outline on that bullet's movement action
3. `self.player_sprite` → Green box around the player + green outline on player movement action

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

- Press **F3** repeatedly to move it to a different corner or turn it off
- The overlay is a single line showing action count
- It cycles through 4 corners before turning off
- You can position it wherever is least intrusive

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
# 1. Look for "ACE Visualizer - N actions" at top-left (press F3 to move or hide)
# 2. Press F4 to open the timeline window (separate window with detailed action info)
# 3. Press F8 to cycle through targets - see green boxes in game + green outlines in timeline
# 4. Press F5 to see velocity arrows, bounds rectangles, and path trails
# 5. Press F6 to pause, F7 to step frame-by-frame
# 6. Play the game and watch actions appear/disappear in real-time
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
