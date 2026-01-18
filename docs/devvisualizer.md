### DevVisualizer Development Tools (arcadeactions/dev/):
* SpritePrototypeRegistry: Decorator-based registry for sprite "prefabs" that can be spawned in the visualizer
  - Use @register_prototype("id") to register factory functions
  - Prototypes receive DevContext with scene_sprites reference
  - Sprites must have _prototype_id attribute set for serialization
* PaletteSidebar: Drag-and-drop interface for spawning prototypes into scene
  - Shows list of registered prototypes
  - Handles mouse drag operations to spawn sprites at world coordinates
  - Maintains drag ghost sprite during drag operation
* SelectionManager: Multi-selection system for sprites
  - Single click: select sprite (replaces previous selection)
  - Shift-click: add/remove sprite from selection
  - Click-drag marquee: box-select multiple sprites
  - Draws glowing outline around selected sprites
  - Stores selection in internal set, exposes via get_selected()
* ActionPresetRegistry: Decorator-based registry for composable Action presets
  - Use @register_preset("id", category="Movement", params={"speed": 4}) to register
  - Presets return unbound Action instances (not applied to targets)
  - Supports parameter editing for bulk application
  - Actions stored as metadata (_action_configs) in edit mode, not running
* BoundaryGizmo: Visual editor for MoveUntil action bounds
  - Detects sprites with MoveUntil actions that have bounds
  - Displays semi-transparent rectangle showing bounds
  - Four draggable corner handles for editing bounds
  - Updates action.bounds via set_bounds() method in real-time
* YAML Templates: Export/import sprite scenes with action configurations
  - export_template(sprites, path): Export scene to YAML file
  - load_scene_template(path, ctx): Import scene from YAML (clears and rebuilds)
  - Supports symbolic bound expressions (OFFSCREEN_LEFT, SCREEN_RIGHT, etc.)
  - Actions stored as preset recipes, not running instances (edit mode)
  - Round-trip editing: export → modify → reimport → re-export
* Edit Mode vs Runtime Mode:
  - Edit Mode: Sprites are static, actions stored as metadata (_action_configs)
  - No action.apply() calls during editing - sprites remain frozen
  - Actions only instantiated when exporting to runtime or previewing
  - This allows selection, positioning, and parameter editing without movement
* Integration Pattern:
  - DevVisualizer components are standalone and composable
  - Use PaletteSidebar for spawning, SelectionManager for selection
  - Apply presets via registry.create() and store as metadata
  - Use BoundaryGizmo when sprite with bounded action is selected
  - Export/import via templates module for persistence