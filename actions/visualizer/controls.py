"""Global debug controls for ACE visualizer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import arcade

from actions.visualizer.snapshot import SnapshotExporter
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.guides import GuideManager
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip


class ActionController(Protocol):
    """Protocol for controlling global action state."""

    def pause_all(self) -> None:
        ...

    def resume_all(self) -> None:
        ...

    def step_all(self, delta_time: float) -> None:
        ...


@dataclass
class DebugControlManager:
    """Handles keyboard shortcuts for debug visualization controls."""

    overlay: InspectorOverlay
    guides: GuideManager
    condition_debugger: ConditionDebugger
    timeline: TimelineStrip
    snapshot_directory: Path
    action_controller: ActionController
    step_delta: float = 1 / 60

    def __post_init__(self) -> None:
        # Assume overlay provides access to debug store
        self.snapshot_exporter = SnapshotExporter(self.overlay.debug_store, self.snapshot_directory)
        self.condition_panel_visible = True
        self.is_paused = False

    def handle_key_press(self, key: int, modifiers: int = 0) -> bool:
        """Handle a keyboard shortcut; returns True if handled."""
        if key == arcade.key.F3:
            self.overlay.toggle()
            return True

        if key == arcade.key.F4:
            self.condition_panel_visible = not self.condition_panel_visible
            return True

        if key == arcade.key.F5:
            self.guides.toggle_all()
            return True

        if key == arcade.key.F6:
            self._toggle_pause()
            return True

        if key == arcade.key.F7:
            if self.is_paused:
                self.action_controller.step_all(self.step_delta)
            return True

        if key == arcade.key.F8:
            self.overlay.highlight_next()
            return True

        if key == arcade.key.F9:
            self.snapshot_exporter.export()
            return True

        return False

    def _toggle_pause(self) -> None:
        if self.is_paused:
            self.action_controller.resume_all()
            self.is_paused = False
        else:
            self.action_controller.pause_all()
            self.is_paused = True

    def update(self, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        """Update all connected components."""
        self.overlay.update()

        if self.condition_panel_visible:
            self.condition_debugger.update()
        else:
            self.condition_debugger.clear()

        self.timeline.update()

        if sprite_positions is None:
            sprite_positions = {}
        self.guides.update(self.overlay.debug_store.get_all_snapshots(), sprite_positions)
