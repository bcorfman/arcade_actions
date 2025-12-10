---
name: 10× Developer Speed Boost for ArcadeActions Games
overview: "Extend ArcadeActions with hot-reload, development visualization, and visual editing tools. Builds on the existing visualizer infrastructure to solve core development bottlenecks: seeing sprite positions while coding, accurate positioning, animation tuning, and instant feedback without game restarts. Works for any ArcadeActions game, not just Laser Gates."
todos:
  - id: hot-reload-core
    content: Implement file watcher and hot-reload manager for Python modules, preserving game state and active actions
    status: pending
  - id: dev-visualizer
    content: Build development visualizer view with grid overlay, sprite position display, and time controls (extends existing visualizer)
    status: pending
    dependencies:
      - hot-reload-core
  - id: code-sync
    content: Create code parser and two-way sync between code positions and visual sprites
    status: pending
    dependencies:
      - dev-visualizer
  - id: animation-inspector
    content: Build animation inspector with live controls, timeline scrubber, and preset system for CycleTexturesUntil and other animation actions
    status: pending
    dependencies:
      - dev-visualizer
  - id: visual-positioning
    content: Implement drag-and-drop sprite positioning with snap-to-grid and formation helpers
    status: pending
    dependencies:
      - dev-visualizer
      - code-sync
  - id: scene-templates
    content: Create scene template library with save/load and template browser
    status: pending
    dependencies:
      - dev-visualizer
      - visual-positioning
  - id: scene-validator
    content: Build scene validator and quick test mode for automated bug detection
    status: pending
    dependencies:
      - hot-reload-core
      - dev-visualizer
---

# 10× Developer Speed Boost for ArcadeActions Games

This plan extends ArcadeActions with development-focused tools that transform game creation from blind code-writing to visual, hot-reloadable workflows. Builds on the existing visualizer infrastructure to solve core bottlenecks: **visualization during coding**, **accurate positioning**, **animation creation/tuning**, and **instant feedback**.

**Target:** Any game using ArcadeActions (Laser Gates, Space Clutter, etc.)

**Expected Outcome:** 10× faster content creation (from hours of trial-and-error to minutes of visual editing).

---

## PHASE 1: Hot-Reload & Development Mode (Must-Have, ~3 weeks)

Enable instant feedback on code changes and development-focused visualization.

---

### 1. Hot-Reload Core (impact ★★★★★, week 1)

**Goal:** See code changes in-game within ≤1s, no restart. Preserve game state (player position, active actions, sprite positions).

**Implementation**

1. File watcher service (`actions/dev/watch.py`)

   - Monitor: `*.py` files in project (configurable paths)
   - Use `watchdog` library with debouncing (300ms window)
   - Track file modification times to avoid duplicate reloads

2. Hot-reload manager (`actions/dev/reload.py`)

   - `importlib.reload()` for Python modules
   - Smart reload strategy:
     - Preserve: sprite positions, active actions, game state
     - Rebuild: action instances, wave/scene objects
     - Freeze updates during swap (1 frame pause)
   - Integration with `Action.update_all()` to pause during reload

3. Development mode toggle (`actions/dev/__init__.py`)

   - `enable_dev_mode()` function to activate hot-reload
   - Environment variable: `ARCADEACTIONS_DEV=1` auto-enables
   - Keyboard shortcut: `R` key forces full reload
   - Visual indicator: brief flash/overlay when reload happens

4. State preservation

   - Serialize sprite positions before reload
   - Preserve action tags and active state
   - Restore after module reload
   - Handle edge cases: deleted classes, changed signatures

**Exit Criteria**

- Edit wave class, save → see change in <1s
- Modify sprite positioning code → updates without losing player position
- No crashes across 50 consecutive reloads
- Works with existing visualizer (no conflicts)

**Files to Create**

- `actions/dev/__init__.py`
- `actions/dev/watch.py`
- `actions/dev/reload.py`

**Dependencies:** None (uses existing `Action` infrastructure)

---

### 2. Development Visualizer Mode (★★★★★, week 1-2)

**Goal:** See sprite layout and positions in real-time while coding. Isolated view mode for content creation.

**Implementation**

1. Dev visualizer view (`actions/dev/visualizer.py`)

   - Extends existing visualizer with development-focused features
   - Toggle with `F6` key (separate from debug visualizer `F3`)
   - Shows: sprite positions, coordinate grid, boundary overlays
   - Isolated mode: load specific scene/wave without full game

2. Coordinate grid overlay

   - Toggle with `G` key in dev mode
   - Shows pixel coordinates at cursor position
   - Draws reference lines for common boundaries
   - Configurable grid spacing (10px, 50px, 100px)
   - Highlights key positions: `WINDOW_WIDTH`, boundaries, spawn points

3. Sprite position inspector

   - Hover over sprite → shows `(left, top, center_x, center_y)` in overlay
   - Click sprite → highlights it, shows full properties in sidebar
   - Draws bounding boxes for all sprites
   - Shows action associations (which actions affect this sprite)

4. Scene/wave preview mode

   - Load any scene/wave class and visualize immediately
   - No player ship, no collisions - just visual layout
   - Time controls: pause (`Space`), step frame-by-frame (`→`), speed multiplier (`1`, `2`, `5`)
   - Export screenshot of current layout

5. Integration with existing visualizer

   - Works alongside existing `attach_visualizer()` system
   - Dev mode uses different overlay (development-focused)
   - Can run both simultaneously (dev mode + debug visualizer)

**Exit Criteria**

- Press `F6` → see current scene layout with grid overlay
- Hover over sprite → see exact coordinates
- Edit positioning code → see new positions on reload without restart
- Grid overlay shows if sprite is at expected position

**Files to Create**

- `actions/dev/visualizer.py`
- `actions/dev/grid_overlay.py`
- `actions/dev/position_inspector.py`

**Dependencies:** Hot-Reload Core, existing visualizer infrastructure

---

### 3. Live Code Sync (★★★★☆, week 2)

**Goal:** Two-way sync between code and visual. See sprite positions update as you type, edit code from visual editor.

**Implementation**

1. Code position parser (`actions/dev/code_parser.py`)

   - Parse Python files to find sprite position assignments
   - Extract: `sprite.left = X`, `sprite.top = Y`, `sprite.center_x = X`, `arrange_grid(...)`
   - Track line numbers for each sprite position
   - Support common patterns: direct assignment, formation functions, loops

2. Visual position markers

   - In dev visualizer, show line numbers for each sprite position
   - Click sprite → jump to editor (if editor supports LSP/URI scheme)
   - Edit code → visualizer highlights which sprites changed
   - Color-code: green (unchanged), yellow (modified), red (error)

3. Reverse sync: visual → code

   - Drag sprite in visualizer → update code file
   - Or: select sprite, type new coordinates → code updates
   - Format: preserves code style, comments, variable names
   - Backup original file before modification

4. Editor integration (optional)

   - VSCode extension or LSP server for position sync
   - Hover over coordinate in code → show sprite in visualizer
   - Or simpler: command-line tool that watches code and sends updates via file/pipe

**Exit Criteria**

- Edit `forcefield.py` line 74 → see marker move in visualizer on reload
- Drag sprite in visualizer → code file updates with new coordinates
- No false positives (marking wrong lines)
- Code formatting preserved

**Files to Create**

- `actions/dev/code_parser.py`
- `actions/dev/sync.py` (code ↔ visual sync)
- `actions/dev/editor_integration.py` (optional LSP/extension)

**Dependencies:** Development Visualizer

---

### 4. Animation Inspector & Tuner (★★★★☆, week 2-3)

**Goal:** See animations play in real-time, adjust timing visually without guessing frame counts or FPS values.

**Implementation**

1. Animation inspector (`actions/dev/animation_inspector.py`)

   - Overlay showing active animations on selected sprites
   - Displays: current frame, FPS, texture cycle direction, elapsed time
   - Timeline scrubber: drag to see animation at any point
   - Works with `CycleTexturesUntil`, `BlinkUntil`, `TweenUntil`

2. Live animation controls

   - Slider for `frames_per_second` → see effect instantly
   - Toggle `direction` (1 vs -1) → see reverse immediately
   - Pause/resume individual animations
   - Speed multiplier: 0.5x, 1x, 2x, 5x

3. Animation presets

   - Save/load animation configs (FPS, direction, texture list, duration)
   - Quick buttons: "Fast", "Medium", "Slow" for common speeds
   - Compare: side-by-side view of two animation settings
   - Export preset as code snippet

4. Texture cycle visualization

   - Show which texture is active in cycle (index 0, 1, 2...)
   - Draw texture index on sprite
   - Highlight when cycle completes
   - Show texture previews in sidebar

5. Integration with existing actions

   - Works with all animation actions: `CycleTexturesUntil`, `BlinkUntil`, `TweenUntil`, `FadeUntil`
   - Shows action parameters in inspector
   - Can modify parameters live (updates action instance)

**Exit Criteria**

- Select animated sprite → see FPS slider, adjust from 100 to 50 → see slowdown instantly
- Scrub timeline → see animation frame-by-frame
- Save animation preset → reload in 5 seconds
- Works with `CycleTexturesUntil` from Laser Gates forcefields

**Files to Create**

- `actions/dev/animation_inspector.py`
- `actions/dev/animation_presets.py`
- `actions/dev/timeline_scrubber.py`

**Dependencies:** Development Visualizer

---

## PHASE 2: Visual Positioning Tools (High-Value, ~2 weeks)

Make positioning sprites as easy as drag-and-drop.

---

### 5. Visual Sprite Positioning (★★★★☆, week 3-4)

**Goal:** Drag sprites to position them, see coordinates update in real-time. No manual coordinate math.

**Implementation**

1. Drag-and-drop in dev visualizer

   - Click and drag sprite → moves in real-time
   - Shows coordinate preview while dragging
   - Snap to grid option (toggle with `S` key)
   - Snap to common positions: boundaries, other sprites, formation points

2. Multi-sprite operations

   - Select multiple sprites (Ctrl+click) → move as group
   - Arrange tools: "Align left/right/top/bottom", "Distribute evenly", "Grid layout"
   - Relative positioning: "Move 10px right", "Space 20px apart"
   - Undo/redo for positioning operations

3. Formation helpers

   - Visual grid tool for `arrange_grid()` calls
   - Preview grid before applying
   - Adjust spacing visually with sliders
   - Works with all formation functions: grid, circle, line, V-formation, etc.

4. Coordinate helpers

   - Smart suggestions: "Position at screen edge" → sets appropriate coordinate
   - Relative to other sprites: "Place 220px after sprite[i-1]"
   - Math expressions: `WINDOW_WIDTH + WALL_WIDTH + i * 220` → shows result
   - Copy coordinates: click to copy `(x, y)` to clipboard

5. Code generation

   - After positioning, generate Python code
   - Or update existing position assignments
   - Preserves code style and variable names
   - Supports multiple code styles (direct assignment, formation functions)

**Exit Criteria**

- Drag sprite → see `left` and `top` update in overlay
- Arrange 3 sprites with "Distribute evenly" → spacing calculated automatically
- Generate code → pastes into editor correctly
- Works with `arrange_grid()` from Laser Gates dense pack waves

**Files to Create**

- `actions/dev/positioning.py` (drag handlers)
- `actions/dev/formations.py` (grid/arrangement tools)
- `actions/dev/code_generator.py` (generate position code)

**Dependencies:** Development Visualizer, Code Sync

---

### 6. Scene Template System (★★★☆☆, week 4)

**Goal:** Save/load scene/wave configurations. Start from templates instead of writing from scratch.

**Implementation**

1. Scene serialization (`actions/dev/templates.py`)

   - Save scene state to JSON/YAML: sprite positions, animations, actions, formation configs
   - Load template → instantiate scene/wave class with saved config
   - Preserve: positions, colors, spacing, animation speeds, action parameters

2. Template library

   - Built-in templates for common patterns
   - Custom templates: save your scenes as templates
   - Template browser in dev visualizer (press `T`)
   - Template metadata: name, description, tags, preview image

3. Template variations

   - Start from template → modify visually → save as new template
   - Compare templates side-by-side
   - Template parameters: "Dense Pack (width=5)" vs "Dense Pack (width=10)"
   - Version history for templates

4. Quick scene creation

   - "New scene from template" → dev visualizer opens with template loaded
   - Adjust positions/animation → test → save as new scene class
   - Export template as Python code (generates scene class)

**Exit Criteria**

- Load "Dense Pack" template → see sprites positioned correctly
- Modify spacing → save as "Dense Pack (wide)" template
- Create new scene from template in <30 seconds
- Template exports as valid Python code

**Files to Create**

- `actions/dev/templates.py`
- `actions/templates/` directory with example templates
- `actions/dev/template_browser.py`

**Dependencies:** Development Visualizer, Positioning Tools

---

## PHASE 3: Workflow Automation (Nice-to-Have, ~1 week)

Speed up common tasks and eliminate repetitive work.

---

### 7. Scene Testing & Validation (★★★☆☆, week 5)

**Goal:** Automatically test scenes, catch common bugs (sprites off-screen, animations broken, invalid actions).

**Implementation**

1. Scene validator (`actions/dev/validator.py`)

   - Checks: all sprites within bounds, animations have textures, actions are valid
   - Runs automatically on reload
   - Shows warnings in dev visualizer overlay
   - Validates: formation parameters, action conditions, boundary settings

2. Quick test mode

   - "Test scene" button → runs scene with minimal game context
   - Auto-advances through scene (or simple bot)
   - Records: collisions work, scene completes, no crashes
   - Performance check: FPS impact of scene

3. Performance profiler

   - Shows FPS impact of scene
   - Highlights expensive operations (too many sprites, complex animations)
   - Suggests optimizations (use SpritePool, reduce action count)
   - Memory usage tracking

4. Integration with existing tests

   - Can export scene as test fixture
   - Validates scene works with existing test framework
   - Generates unit tests for scene behavior

**Exit Criteria**

- Invalid scene (sprite at x=-1000) → shows warning on reload
- "Test scene" → completes in 10 seconds, shows pass/fail
- Performance warning if FPS drops below 55
- Works with existing pytest infrastructure

**Files to Create**

- `actions/dev/validator.py`
- `actions/dev/tester.py`
- `actions/dev/profiler.py`

**Dependencies:** Hot-Reload, Development Visualizer

---

## Integration with Existing ArcadeActions

### Extending Current Visualizer

The development tools integrate with the existing visualizer system:

- **Existing visualizer** (`F3`): Debug-focused, shows action lifecycle, condition evaluation
- **Dev visualizer** (`F6`): Development-focused, shows sprite positions, coordinate grid, editing tools
- **Both can run simultaneously**: Debug overlay + dev tools

### API Design

```python
from actions.dev import enable_dev_mode, DevVisualizer

# Enable development mode (hot-reload + dev tools)
enable_dev_mode(
    watch_paths=["src/my_game/waves/", "src/my_game/scenes/"],
    auto_reload=True
)

# Or use environment variable
# ARCADEACTIONS_DEV=1 uv run python game.py

# Dev visualizer can be attached separately
dev_viz = DevVisualizer()
dev_viz.attach_to_window(window)
```

### Keyboard Shortcuts

- `R`: Force reload (dev mode)
- `F6`: Toggle dev visualizer
- `G`: Toggle coordinate grid
- `S`: Toggle snap-to-grid
- `T`: Open template browser
- `Space`: Pause/resume (in dev visualizer)
- `→`: Step frame (in dev visualizer)

---

## Delivery Strategy

### Sprint Cadence

- **Week 1:** Hot-reload core + basic dev visualizer (must-have)
- **Week 2:** Animation inspector + code sync (high-value)
- **Week 3-4:** Positioning tools + templates (high-value)
- **Week 5:** Testing/validation (nice-to-have)

### Success Metrics

Track weekly:

1. **Iteration time:** Seconds from code edit to visual feedback (target: <2s)
2. **Positioning accuracy:** First-try success rate for sprite placement (target: >80%)
3. **Scene creation time:** Minutes to create new scene (target: <10 min, from 60+ min baseline)
4. **Animation tuning time:** Seconds to adjust animation speed (target: <5s, from 2+ min baseline)

Target by end of Phase 1:

- See sprite positions while coding (0s wait time)
- Adjust coordinates with visual feedback (<2s to see change)
- Tune animations in real-time (<1s to see change)

---

## Key Differences from Original Plan

**Removed (not relevant for general ArcadeActions):**

- Tiled integration (game-specific, not library-level)
- YAML behavior trees (actions use Python directly)
- Telemetry dashboard (not needed for development workflow)

**Added (specific to development bottlenecks):**

- Dev visualizer mode (see sprites while coding)
- Live code sync (two-way between code and visual)
- Animation inspector (tune animations visually)
- Visual positioning (drag sprites instead of guessing coordinates)
- Scene templates (start from examples)

**Kept (still valuable):**

- Hot-reload core (instant feedback)
- File watching (auto-reload on save)
- Builds on existing visualizer infrastructure

---

## ROI Calculation

**Without tooling (baseline):**

- Create new scene: 60+ minutes (write code, run game, adjust coordinates, repeat)
- Tune animation: 2+ minutes per adjustment (edit code, restart, test)
- Position sprites: 10+ minutes of coordinate guessing

**With Phase 1 tooling:**

- Create new scene: 10 minutes (visual editor, see positions, drag to adjust)
- Tune animation: 5 seconds (slider in dev visualizer)
- Position sprites: 1 minute (drag sprites, see coordinates)

**10× speedup achieved in scene creation workflow.**

---

## Files Structure

```
actions/
├── dev/                    # New development tools module
│   ├── __init__.py
│   ├── watch.py           # File watcher
│   ├── reload.py          # Hot-reload manager
│   ├── visualizer.py      # Dev visualizer view
│   ├── grid_overlay.py    # Coordinate grid
│   ├── position_inspector.py
│   ├── code_parser.py     # Parse code for positions
│   ├── sync.py            # Code ↔ visual sync
│   ├── animation_inspector.py
│   ├── animation_presets.py
│   ├── positioning.py    # Drag-and-drop
│   ├── formations.py     # Visual formation tools
│   ├── code_generator.py
│   ├── templates.py      # Scene templates
│   ├── template_browser.py
│   ├── validator.py
│   ├── tester.py
│   └── profiler.py
└── templates/             # Built-in templates
    ├── dense_pack.yaml
    ├── forcefield.yaml
    └── ...
```