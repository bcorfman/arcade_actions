"""Global debug controls for ACE visualizer."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Callable

import arcade

from actions.visualizer.snapshot import SnapshotExporter
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.guides import GuideManager
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip


class ActionController(Protocol):
    """Protocol for controlling global action state."""

    def pause_all(self) -> None: ...

    def resume_all(self) -> None: ...

    def step_all(self, delta_time: float) -> None: ...


class DebugControlManager:
    """Handles keyboard shortcuts for debug visualization controls."""

    def __init__(
        self,
        *,
        overlay: InspectorOverlay,
        guides: GuideManager,
        condition_debugger: ConditionDebugger,
        timeline: TimelineStrip,
        snapshot_directory: Path,
        action_controller: ActionController,
        toggle_event_window: Callable[[bool], None],
        target_names_provider: Callable[[], dict[int, str]] | None = None,
        step_delta: float = 1 / 60,
    ) -> None:
        self.overlay = overlay
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.timeline = timeline
        self.snapshot_directory = snapshot_directory
        self.action_controller = action_controller
        self.toggle_event_window = toggle_event_window
        self.target_names_provider = target_names_provider
        self.step_delta = step_delta

        # Assume overlay provides access to debug store
        self._cached_target_names: dict[int, str] = {}
        self._target_names_frame = -1  # Track when we last refreshed target names
        self.snapshot_exporter = SnapshotExporter(
            self.overlay.debug_store,
            self.snapshot_directory,
            target_names_provider=self.get_target_names,
        )
        self.condition_panel_visible = False
        self.is_paused = False
        self.condition_debugger.clear()
        self._toggle_event_window_callback = self.toggle_event_window

    def handle_key_press(self, key: int, modifiers: int = 0) -> bool:
        """Handle a keyboard shortcut; returns True if handled."""
        if key == arcade.key.F3:
            self.overlay.cycle_position()
            return True

        if key == arcade.key.F4:
            self.condition_panel_visible = not self.condition_panel_visible
            self._toggle_event_window_callback(self.condition_panel_visible)
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
            self._refresh_target_names()
            try:
                path = self.snapshot_exporter.export()
                print(f"[ACE] Snapshot written to {path}")
            except Exception as exc:
                print(f"[ACE] Failed to write snapshot: {exc!r}")
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
        # Only refresh target names every 60 frames (~1 second at 60 FPS) to reduce overhead
        current_frame = self.overlay.debug_store.current_frame
        if current_frame - self._target_names_frame >= 60:
            self._refresh_target_names()
            self._target_names_frame = current_frame

        self.overlay.update()

        if self.condition_panel_visible:
            self.condition_debugger.update()
        else:
            self.condition_debugger.clear()

        guides_enabled = self.guides.any_enabled()
        if guides_enabled:
            self.timeline.update()
            if sprite_positions is None:
                sprite_positions = {}

            # Collect sprite sizes and IDs for highlight guide
            from actions.visualizer.attach import _collect_sprite_sizes_and_ids

            sprite_sizes, sprite_ids_in_target = _collect_sprite_sizes_and_ids()

            self.guides.update(
                self.overlay.debug_store.get_all_snapshots(),
                sprite_positions,
                highlighted_target_id=self.overlay.highlighted_target_id,
                sprite_sizes=sprite_sizes,
                sprite_ids_in_target=sprite_ids_in_target,
            )
        else:
            self.timeline.update()

    # ------------------------------------------------------------------ Helpers
    def _refresh_target_names(self) -> None:
        if self.target_names_provider is None:
            self._cached_target_names = {}
            return

        try:
            names = self.target_names_provider() or {}
        except Exception:
            self._cached_target_names = {}
            return

        normalized: dict[int, str] = {}
        for key, value in names.items():
            try:
                normalized[int(key)] = str(value)
            except (TypeError, ValueError):
                continue
        self._cached_target_names = normalized

    def get_target_names(self) -> dict[int, str]:
        """Return the most recently cached target-name mapping."""
        return dict(self._cached_target_names)
