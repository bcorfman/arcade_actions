"""Visualizer attach/detach helpers for ArcadeActions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import arcade

from actions.base import Action
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.controls import DebugControlManager
from actions.visualizer.guides import GuideManager
from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.renderer import OverlayRenderer
from actions.visualizer.timeline import TimelineStrip


SpritePositionsProvider = Callable[[], dict[int, tuple[float, float]]]

_WINDOW_SENTINEL = object()


@dataclass
class VisualizerSession:
    """Keeps track of the active visualizer attachment state."""

    debug_store: DebugDataStore
    overlay: InspectorOverlay
    renderer: OverlayRenderer
    guides: GuideManager
    condition_debugger: ConditionDebugger
    timeline: TimelineStrip
    control_manager: DebugControlManager
    snapshot_directory: Path
    sprite_positions_provider: SpritePositionsProvider | None
    wrapped_update_all: Callable[[type[Action], float, Any], None]
    previous_update_all: Callable[[type[Action], float, Any], None]
    previous_debug_store: Any
    previous_enable_flag: bool


_VISUALIZER_SESSION: VisualizerSession | None = None
_AUTO_ATTACH_ATTEMPTED = False


def get_visualizer_session() -> VisualizerSession | None:
    """Return the current visualizer session if attached."""

    return _VISUALIZER_SESSION


def is_visualizer_attached() -> bool:
    """Return True if the visualizer is currently attached."""

    return _VISUALIZER_SESSION is not None


def _collect_sprite_positions() -> dict[int, tuple[float, float]]:
    """Attempt to collect sprite positions from active actions."""

    positions: dict[int, tuple[float, float]] = {}
    # Iterate over active actions and attempt to read positions directly.
    for action in list(Action._active_actions):  # type: ignore[attr-defined]
        target = getattr(action, "target", None)
        if target is None:
            continue
        try:
            positions[id(target)] = (target.center_x, target.center_y)
            continue
        except AttributeError:
            pass

        # Try iterating if the target behaves like a sprite list.
        try:
            for sprite in target:
                try:
                    positions[id(sprite)] = (sprite.center_x, sprite.center_y)
                except AttributeError:
                    continue
        except TypeError:
            continue
    return positions


def attach_visualizer(
    *,
    debug_store: DebugDataStore | None = None,
    snapshot_directory: Path | str | None = None,
    sprite_positions_provider: SpritePositionsProvider | None = None,
    overlay_cls: type[InspectorOverlay] = InspectorOverlay,
    renderer_cls: type[OverlayRenderer] = OverlayRenderer,
    guide_manager_cls: type[GuideManager] = GuideManager,
    condition_debugger_cls: type[ConditionDebugger] = ConditionDebugger,
    timeline_cls: type[TimelineStrip] = TimelineStrip,
    controls_cls: type[DebugControlManager] = DebugControlManager,
    control_manager_kwargs: Optional[dict[str, Any]] = None,
) -> VisualizerSession:
    """
    Attach the visualizer instrumentation stack programmatically.

    Args:
        debug_store: Optional pre-existing debug store to reuse.
        snapshot_directory: Directory for exported snapshots.
        sprite_positions_provider: Optional callable returning sprite positions.
        overlay_cls: Custom overlay class for testing/extension.
        renderer_cls: Custom renderer class.
        guide_manager_cls: Custom guide manager class.
        condition_debugger_cls: Custom condition debugger class.
        timeline_cls: Custom timeline class.
        controls_cls: Custom control manager class.
        control_manager_kwargs: Extra kwargs passed to controls_cls.
    """

    global _VISUALIZER_SESSION

    if _VISUALIZER_SESSION is not None:
        return _VISUALIZER_SESSION

    previous_store = getattr(Action, "_debug_store", None)
    previous_enable_flag = getattr(Action, "_enable_visualizer", False)
    original_update_all = Action.update_all.__func__  # type: ignore[attr-defined]

    if debug_store is None:
        debug_store = DebugDataStore()

    Action.set_debug_store(debug_store)
    Action._enable_visualizer = True  # type: ignore[attr-defined]

    if snapshot_directory is None:
        snapshot_directory = Path("snapshots")
    else:
        snapshot_directory = Path(snapshot_directory)

    overlay = overlay_cls(debug_store)
    renderer = renderer_cls(overlay)
    guides = guide_manager_cls()
    condition_debugger = condition_debugger_cls(debug_store)
    timeline = timeline_cls(debug_store)

    if control_manager_kwargs is None:
        control_manager_kwargs = {}

    control_manager = controls_cls(
        overlay=overlay,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        snapshot_directory=snapshot_directory,
        action_controller=Action,
        **control_manager_kwargs,
    )

    if sprite_positions_provider is None:
        sprite_positions_provider = _collect_sprite_positions

    def wrapped_update_all(cls: type[Action], delta_time: float, physics_engine: Any = None) -> None:
        original_update_all(cls, delta_time, physics_engine=physics_engine)
        if _VISUALIZER_SESSION is None:
            return
        positions: dict[int, tuple[float, float]] = {}
        provider = _VISUALIZER_SESSION.sprite_positions_provider
        if provider is not None:
            try:
                positions = provider() or {}
            except Exception:
                positions = {}
        _VISUALIZER_SESSION.control_manager.update(positions)
        _VISUALIZER_SESSION.renderer.update()

    session = VisualizerSession(
        debug_store=debug_store,
        overlay=overlay,
        renderer=renderer,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        control_manager=control_manager,
        snapshot_directory=snapshot_directory,
        sprite_positions_provider=sprite_positions_provider,
        wrapped_update_all=wrapped_update_all,
        previous_update_all=original_update_all,
        previous_debug_store=previous_store,
        previous_enable_flag=previous_enable_flag,
    )

    Action.update_all = classmethod(wrapped_update_all)  # type: ignore[assignment]

    _VISUALIZER_SESSION = session
    return session


def detach_visualizer() -> bool:
    """Detach the visualizer and restore previous Action state."""

    global _VISUALIZER_SESSION
    if _VISUALIZER_SESSION is None:
        return False

    session = _VISUALIZER_SESSION

    current_update = getattr(Action.update_all, '__func__', Action.update_all)
    if current_update is session.wrapped_update_all:
        Action.update_all = classmethod(session.previous_update_all)  # type: ignore[assignment]
    Action.set_debug_store(session.previous_debug_store)
    Action._enable_visualizer = session.previous_enable_flag  # type: ignore[attr-defined]

    _VISUALIZER_SESSION = None
    return True


def auto_attach_from_env(*, force: bool = False, attach_kwargs: dict[str, Any] | None = None) -> bool:
    """Attach automatically when ARCADEACTIONS_VISUALIZER is set."""

    global _AUTO_ATTACH_ATTEMPTED
    if not force and _AUTO_ATTACH_ATTEMPTED:
        return False
    _AUTO_ATTACH_ATTEMPTED = True

    if os.getenv("ARCADEACTIONS_VISUALIZER") is None:
        return False

    if attach_kwargs is None:
        attach_kwargs = {}

    attach_visualizer(**attach_kwargs)
    return True


def enable_visualizer_hotkey(
    *,
    window: arcade.Window | None | object = _WINDOW_SENTINEL,
    key: int = arcade.key.F3,
    modifier: int = arcade.key.MOD_SHIFT,
    attach_kwargs: dict[str, Any] | None = None,
) -> bool:
    """Install a keyboard shortcut that attaches the visualizer on demand."""

    actual_window = window
    if actual_window is _WINDOW_SENTINEL:
        try:
            actual_window = arcade.get_window()
        except RuntimeError:
            actual_window = None

    if actual_window is None:
        return False

    if attach_kwargs is None:
        attach_kwargs = {}

    def on_key_press(symbol: int, modifiers: int) -> bool:
        if symbol == key and modifiers & modifier:
            if not is_visualizer_attached():
                attach_visualizer(**attach_kwargs)
            return True
        return False

    actual_window.push_handlers(on_key_press=on_key_press)
    return True
