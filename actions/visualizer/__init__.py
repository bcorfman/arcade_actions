"""
ArcadeActions Visualizer - In-engine debugging and inspection tools.

This module provides runtime visualization for the ACE (ArcadeActions Conditional Engine)
including action inspection, condition debugging, visual guides, and performance monitoring.

Usage:
    from actions import Action
    from actions.visualizer import DebugDataStore, InspectorOverlay, OverlayRenderer
    
    # Create debug store and inject it
    debug_store = DebugDataStore()
    Action.set_debug_store(debug_store)
    Action._enable_visualizer = True
    
    # Create overlay and renderer
    overlay = InspectorOverlay(debug_store)
    renderer = OverlayRenderer(overlay)
    
    # In game loop:
    def on_update(self, delta_time):
        Action.update_all(delta_time)
        overlay.update()
        renderer.update()
    
    def on_draw(self):
        renderer.draw()
"""

from .instrumentation import (
    DebugDataStore,
    ActionEvent,
    ConditionEvaluation,
    ActionSnapshot,
)
from .overlay import (
    InspectorOverlay,
    ActionCard,
    TargetGroup,
)
from .renderer import OverlayRenderer
from .guides import (
    VelocityGuide,
    BoundsGuide,
    PathGuide,
    GuideManager,
)
from .controls import DebugControlManager
from .snapshot import SnapshotExporter

__all__ = [
    "DebugDataStore",
    "ActionEvent",
    "ConditionEvaluation",
    "ActionSnapshot",
    "InspectorOverlay",
    "ActionCard",
    "TargetGroup",
    "OverlayRenderer",
    "VelocityGuide",
    "BoundsGuide",
    "PathGuide",
    "GuideManager",
    "DebugControlManager",
    "SnapshotExporter",
]

