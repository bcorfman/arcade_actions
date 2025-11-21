<!-- 8da86f9a-2892-40bf-a4e4-0a95ed0924b3 c13c3b01-a335-4792-8b08-aa5a42b00912 -->
# Milestone 0 – ACE Visualization Core

**Impact:** ★★★★★ &nbsp;&nbsp; **Duration:** 1 week (5–7 working days)

## Objectives

- Deliver in-engine visibility for every active action, condition, and composition
- Replace most console logging during interactive development while keeping minimal traces for headless/CI
- Establish performance guardrails so visualization never compromises gameplay frame rates

## Deliverables

1. **Runtime Inspector Overlay**

- Grouped by target (Sprite/SpriteList) with per-action cards, progress bars, tags, warnings
- Click-to-highlight: selecting a card outlines the sprite/list on screen; Shift+Click isolates
- Search/filter bar for tags and action classes

2. **Condition Debugger Panel**

- Live truth table (last result, timestamp/frame, input values)
- Shows pending on_stop payload; highlights recent state flips
- Ability to pin key conditions for quick reference

3. **Visual Debug Layers**

- Toggleable velocity vectors, boundary rectangles, path splines, trajectory ghosts, condition zones
- Rendered via reusable `arcade.ShapeElementList` pools; color-coded to match inspector entries

4. **Action Timeline Strip**

- Bottom overlay depicting sequence/parallel trees with per-action progress bars
- Hover tooltips show start frame, duration (if available), and condition summary

5. **Global Debug Controls**

- F-key shortcuts: `F3` inspector, `F4` condition watch, `F5` guides, `F6` pause actions, `F7` frame-step, `F8` highlight selection, `F9` snapshot dump
- Overlay toolbar mirroring shortcuts for discoverability

6. **Instrumentation & Telemetry**

- Hooks inside `Action.update_all()` gathering frame-by-frame state into a ring buffer
- Optional WebSocket export (localhost) for external viewers / secondary monitors
- Snapshot writer producing JSON dumps for offline analysis or headless runs

7. **Performance Guardrails & Logging Strategy**

- Pooled widgets, zero allocations per frame, stress-tested at 200+ actions maintaining ≥60 FPS
- Debug level gating: visualizer off by default in production builds
- Trimmed textual logging retained for headless/CI; documentation updated to recommend visualizer first

## Implementation Steps & To-Dos

1. **Instrumentation Layer (Day 1) — `m0-instrumentation`**

- Extend `Action` base with debug hooks: start/end notifications, condition evaluation reporting, on_stop payload capture
- Implement centralized debug data store (ring buffer + per-target index)

2. **Overlay Framework (Day 2) — `m0-overlay`**

- Set up `arcade.gui.UIManager` or immediate-mode layer for inspector panels
- Build reusable card widgets and layout containers (target groups, action rows)

3. **Visual Guides (Day 3) — `m0-visual-guides`**

- Create ShapeElementList pools for velocity arrows, bounds, paths, and trajectories
- Wire quick toggles; ensure colors match inspector selections

4. **Condition & Timeline Views (Day 4) — `m0-condition-timeline`**

- Implement condition watch panel with pinning/highlighting
- Render timeline strip with nested sequence/parallel bars and hover tooltips

5. **Controls & Snapshotting (Day 5) — `m0-controls`**

- Bind F-key shortcuts; add pause/frame-step integration with `Action` manager
- Implement snapshot writer and optional WebSocket streaming

6. **Performance & Polish (Day 6) — `m0-performance`**

- Stress test with synthetic scene (200+ actions) to profile overhead
- Tune rendering order, alpha blending, and batching to avoid frame drops
- Document usage (README section or docs/ace_visualizer.md)

7. **Validation & Demos (Day 7) — `m0-validation`**

- Run vertical slice level; verify boundary bounces, path-follow progress, and condition failures are all diagnosable via overlay alone
- Capture screenshots/gifs for documentation; record a brief walkthrough video

## Exit Criteria

- Developers can identify why an action stopped (or didn’t) using only the overlay and condition watch
- Overlay toggles/pause/frame-step work without affecting physics/Arcade timing actions
- Performance stays at ≥60 FPS in stress test; visualizer can be fully disabled via config
- Logging docs updated to position textual logging as secondary tooling for headless runs

### To-dos

- [ ] Implement ACE visualization overlay with inspector, condition debugger, and timeline controls
- [ ] Deliver hot-reload core watching code, maps, and assets
- [ ] Add incremental Scene/TileMap reload preserving entity state
- [ ] Create Tiled action schema exporter and JavaScript plug-in
- [ ] Introduce YAML prefab loader and Tiled template integration
- [ ] Load JSON/YAML behaviors and formation patterns without code edits
- [ ] Ship action inspector HUD with rewind/time-travel debugging
- [ ] Build headless automated playtest CLI and CI workflow
- [ ] Add telemetry hooks and real-time analytics dashboard
- [ ] Parallelize asset optimization with fingerprint cache
- [ ] Publish cookiecutter starter template bundling all tooling