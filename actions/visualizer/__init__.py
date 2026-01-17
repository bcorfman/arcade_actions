"""
ArcadeActions Visualizer - In-engine debugging and inspection tools.

This module provides runtime visualization for the ACE (ArcadeActions Conditional Engine)
including action inspection, condition debugging, visual guides, and performance monitoring.

Usage:
    from actions.visualizer import attach_visualizer

    # Attach once at startup (or rely on ARCADEACTIONS_VISUALIZER=1 env var)
    attach_visualizer()

    # After this call, F3-F9 shortcuts are active automatically
"""

from .attach import (
    attach_visualizer,
    auto_attach_from_env,
    detach_visualizer,
    enable_visualizer_hotkey,
    get_visualizer_session,
    is_visualizer_attached,
)
from .controls import DebugControlManager
from .guides import (
    BoundsGuide,
    GuideManager,
    HighlightGuide,
    PathGuide,
    VelocityGuide,
)
from .instrumentation import (
    ActionEvent,
    ActionSnapshot,
    ConditionEvaluation,
    DebugDataStore,
)
from .overlay import (
    ActionCard,
    InspectorOverlay,
    TargetGroup,
)
from .renderer import OverlayRenderer
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
    "HighlightGuide",
    "GuideManager",
    "DebugControlManager",
    "SnapshotExporter",
    "attach_visualizer",
    "detach_visualizer",
    "is_visualizer_attached",
    "get_visualizer_session",
    "enable_visualizer_hotkey",
    "auto_attach_from_env",
]


auto_attach_from_env()
