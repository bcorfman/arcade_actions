"""Visualizer session state for ACE visualizer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import arcade

from arcadeactions.base import Action
from arcadeactions.visualizer.condition_panel import ConditionDebugger
from arcadeactions.visualizer.controls import DebugControlManager
from arcadeactions.visualizer.event_window import EventInspectorWindow
from arcadeactions.visualizer.guides import GuideManager
from arcadeactions.visualizer.instrumentation import DebugDataStore
from arcadeactions.visualizer.overlay import InspectorOverlay
from arcadeactions.visualizer.renderer import GuideRenderer, OverlayRenderer
from arcadeactions.visualizer.timeline import TimelineStrip

SpritePositionsProvider = Callable[[], dict[int, tuple[float, float]]]
TargetNamesProvider = Callable[[], dict[int, str]]


class VisualizerSession:
    """Keeps track of the active visualizer attachment state."""

    def __init__(
        self,
        *,
        debug_store: DebugDataStore,
        overlay: InspectorOverlay,
        renderer: OverlayRenderer,
        guides: GuideManager,
        condition_debugger: ConditionDebugger,
        timeline: TimelineStrip,
        control_manager: DebugControlManager,
        guide_renderer: GuideRenderer,
        event_window: EventInspectorWindow | None,
        snapshot_directory: Path,
        sprite_positions_provider: SpritePositionsProvider | None,
        target_names_provider: TargetNamesProvider | None,
        wrapped_update_all: Callable[[type[Action], float, Any], None],
        previous_update_all: Callable[[type[Action], float, Any], None],
        previous_debug_store: Any,
        previous_enable_flag: bool,
        window: arcade.Window | None = None,
        original_window_on_draw: Callable[..., Any] | None = None,
        original_window_on_key_press: Callable[..., Any] | None = None,
        original_window_on_close: Callable[..., Any] | None = None,
        key_handler: Callable[[int, int], bool] | None = None,
    ) -> None:
        self.debug_store = debug_store
        self.overlay = overlay
        self.renderer = renderer
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.timeline = timeline
        self.control_manager = control_manager
        self.guide_renderer = guide_renderer
        self.event_window = event_window
        self.snapshot_directory = snapshot_directory
        self.sprite_positions_provider = sprite_positions_provider
        self.target_names_provider = target_names_provider
        self.wrapped_update_all = wrapped_update_all
        self.previous_update_all = previous_update_all
        self.previous_debug_store = previous_debug_store
        self.previous_enable_flag = previous_enable_flag
        self.window = window
        self.original_window_on_draw = original_window_on_draw
        self.original_window_on_key_press = original_window_on_key_press
        self.original_window_on_close = original_window_on_close
        self.key_handler = key_handler

    @property
    def keyboard_handler(self) -> Callable[[int, int], bool] | None:
        """Convenience property for tests - returns key handler that delegates to control_manager."""
        if self.control_manager is None:
            return None
        return self.control_manager.handle_key_press

    @property
    def draw_handler(self) -> Callable[[], None] | None:
        """Convenience property for tests - returns draw handler."""
        if self.renderer is None:
            return None
        return self.renderer.draw


_VISUALIZER_SESSION: VisualizerSession | None = None
_AUTO_ATTACH_ATTEMPTED = False


def get_visualizer_session() -> VisualizerSession | None:
    """Return the current visualizer session if attached."""

    return _VISUALIZER_SESSION


def is_visualizer_attached() -> bool:
    """Return True if the visualizer is currently attached."""

    return _VISUALIZER_SESSION is not None
