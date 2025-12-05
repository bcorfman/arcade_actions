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

from .instrumentation import (
    DebugDataStore,
    ActionEvent,
    ConditionEvaluation,
    ActionSnapshot,
)
from .attach import (
    attach_visualizer,
    detach_visualizer,
    is_visualizer_attached,
    get_visualizer_session,
    enable_visualizer_hotkey,
    auto_attach_from_env,
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
    HighlightGuide,
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
