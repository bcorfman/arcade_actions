---
name: Milestone 0 – ACE Visualization Core
overview: ""
todos:
  - id: d2cfbde2-d802-471c-8f51-7f500c41801d
    content: Implement ACE visualization overlay with inspector, condition debugger, and timeline controls
    status: pending
  - id: c41a0b90-4270-4bdb-a22b-2438b24de865
    content: Deliver hot-reload core watching code, maps, and assets
    status: pending
  - id: f8d15896-3361-4514-a0a7-ce5f0a248a09
    content: Add incremental Scene/TileMap reload preserving entity state
    status: pending
  - id: 62331da1-e88d-492a-936e-bd50eada66e5
    content: Create Tiled action schema exporter and JavaScript plug-in
    status: pending
  - id: 771954fa-b75f-47e0-9498-541de3f740e8
    content: Introduce YAML prefab loader and Tiled template integration
    status: pending
  - id: ae144dad-58f3-4f37-b4d4-eea5747ae808
    content: Load JSON/YAML behaviors and formation patterns without code edits
    status: pending
  - id: 326cc277-72a8-4e8e-b03b-3018b1fca0fe
    content: Ship action inspector HUD with rewind/time-travel debugging
    status: pending
  - id: b5f101f5-8c3c-4ad4-a1b1-fa191a7a59d8
    content: Build headless automated playtest CLI and CI workflow
    status: pending
  - id: 406fa6f8-5862-4ce2-9146-497c0d496da4
    content: Add telemetry hooks and real-time analytics dashboard
    status: pending
  - id: 34487f72-89e4-452e-be32-ebf2d34ba2b9
    content: Parallelize asset optimization with fingerprint cache
    status: pending
  - id: 3348928f-0998-4555-8676-aff909f9c0e9
    content: Publish cookiecutter starter template bundling all tooling
    status: pending
---

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