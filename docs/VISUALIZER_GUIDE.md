# ArcadeActions Visualizer Guide

## How to Enable

Set the environment variable before running your game:

```bash
ARCADEACTIONS_VISUALIZER=1 uv run python examples/space_clutter.py
```

## What You'll See

When the visualizer is enabled, you get:

1. **Inspector Overlay** - A panel in the top-left corner of your game window showing:
   - All active actions
   - Their targets (sprites/sprite lists)
   - Progress bars for actions that report progress
   - Current state information

2. **ACE Action Timeline Window** - A separate window showing:
   - Timeline bars for each action's lifetime
   - Color-coded by target type (Cyan=SpriteList, Orange=Sprite)
   - Start/end frames for completed actions
   - Active actions extend to the right edge

## Keyboard Shortcuts

Press these keys while the game window is focused:

| Key | Function | What Happens |
|-----|----------|--------------|
| **F3** | Toggle Inspector Overlay | Shows/hides the overlay panel in the game window |
| **F4** | Toggle Timeline Window | Shows/hides the separate "ACE Action Timeline" window |
| **F5** | Toggle Visual Guides | Shows/hides velocity arrows, bounds rectangles, and path trails |
| **F6** | Pause/Resume Actions | Freezes/unfreezes all action updates |
| **F7** | Step One Frame | When paused, advances actions by one frame |
| **F8** | Highlight Next Action | Cycles through actions, highlighting each in the overlay |
| **F9** | Export Snapshot | Saves current action state to `snapshots/` directory |

## Understanding F4 (Timeline Window)

When you press F4:
- A separate window titled **"ACE Action Timeline"** will appear (or disappear if already visible)
- This window shows horizontal bars representing each action's lifetime
- The window can be resized and repositioned
- If no actions are active, the window will be empty
- Press F4 again to hide the window

**Note:** The timeline window is initially **hidden** by default. Press F4 once to show it.

## Visual Overlay Details

The inspector overlay (toggled with F3) shows information like:

```
ACE Inspector - 2 action(s)

SpriteList (id: 140234567890) - 1 action(s)
  [MoveUntil] v=(2.0, 0.0) | Running
  ████████████░░░░░░░░░░░░ 45%

Sprite (id: 140234567891) - 1 action(s)
  [BlinkUntil] interval=30 | Running
```

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


