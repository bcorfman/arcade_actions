"""Visualizer attach/detach helpers for ArcadeActions."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import arcade
from arcade import window_commands

from arcadeactions.base import Action
from arcadeactions.display import move_to_primary_monitor
from arcadeactions.visualizer.condition_panel import ConditionDebugger
from arcadeactions.visualizer.controls import DebugControlManager
from arcadeactions.visualizer.event_window import EventInspectorWindow
from arcadeactions.visualizer.guides import GuideManager
from arcadeactions.visualizer.instrumentation import DebugDataStore
from arcadeactions.visualizer.overlay import InspectorOverlay
from arcadeactions.visualizer.renderer import GuideRenderer, OverlayRenderer
from arcadeactions.visualizer.timeline import TimelineStrip
from arcadeactions.visualizer._collectors import (
    SpritePositionsProvider,
    TargetNamesProvider,
    _collect_sprite_positions,
    _collect_sprite_sizes_and_ids,
    _collect_target_names_from_view,
)
from arcadeactions.visualizer._session import (
    VisualizerSession,
    get_visualizer_session,
    is_visualizer_attached,
)
import arcadeactions.visualizer._session as _session
from arcadeactions.visualizer._window_hooks import _install_window_handler, _remove_window_handler

_WINDOW_SENTINEL = object()

__all__ = [
    "attach_visualizer",
    "detach_visualizer",
    "auto_attach_from_env",
    "enable_visualizer_hotkey",
    "_collect_sprite_positions",
    "_collect_sprite_sizes_and_ids",
    "_collect_target_names_from_view",
]


def attach_visualizer(
    *,
    debug_store: DebugDataStore | None = None,
    snapshot_directory: Path | str | None = None,
    sprite_positions_provider: SpritePositionsProvider | None = None,
    target_names_provider: TargetNamesProvider | None = None,
    overlay_cls: type[InspectorOverlay] = InspectorOverlay,
    renderer_cls: type[OverlayRenderer] = OverlayRenderer,
    guide_manager_cls: type[GuideManager] = GuideManager,
    condition_debugger_cls: type[ConditionDebugger] = ConditionDebugger,
    timeline_cls: type[TimelineStrip] = TimelineStrip,
    controls_cls: type[DebugControlManager] = DebugControlManager,
    guide_renderer_cls: type[GuideRenderer] = GuideRenderer,
    event_window_cls: type[EventInspectorWindow] = EventInspectorWindow,
    control_manager_kwargs: dict[str, Any] | None = None,
) -> VisualizerSession:
    """
    Attach the visualizer instrumentation stack programmatically.

    Args:
        debug_store: Optional pre-existing debug store to reuse.
        snapshot_directory: Directory for exported snapshots.
        sprite_positions_provider: Optional callable returning sprite positions.
        target_names_provider: Optional callable returning target names mapping target_id to name string.
        overlay_cls: Custom overlay class for testing/extension.
        renderer_cls: Custom renderer class.
        guide_manager_cls: Custom guide manager class.
        condition_debugger_cls: Custom condition debugger class.
        timeline_cls: Custom timeline class.
        controls_cls: Custom control manager class.
        guide_renderer_cls: Renderer class for world-space guides.
        event_window_cls: Window class used for displaying events.
        control_manager_kwargs: Extra kwargs passed to controls_cls.
    """

    if _session._VISUALIZER_SESSION is not None:
        return _session._VISUALIZER_SESSION

    previous_store = getattr(Action, "_debug_store", None)
    previous_enable_flag = getattr(Action, "_enable_visualizer", False)
    original_update_all = Action.update_all.__func__  # type: ignore[attr-defined]

    debug_store = debug_store or DebugDataStore()
    _enable_action_debugging(debug_store)

    snapshot_directory = _normalize_snapshot_directory(snapshot_directory)

    overlay = overlay_cls(debug_store)
    renderer = renderer_cls(overlay)
    guides = guide_manager_cls(initial_enabled=False)  # Guides start disabled, press F5 to enable
    condition_debugger = condition_debugger_cls(debug_store)
    timeline = timeline_cls(debug_store)
    guide_renderer = guide_renderer_cls(guides)

    control_manager_kwargs, final_target_names_provider = _prepare_control_manager_kwargs(
        control_manager_kwargs, target_names_provider
    )

    session_holder: dict[str, VisualizerSession | None] = {"session": None}
    control_manager_holder: dict[str, DebugControlManager | None] = {"manager": None}

    toggle_event_window = _build_event_window_toggle(
        session_holder,
        control_manager_holder,
        event_window_cls,
    )

    control_manager = _create_control_manager(
        controls_cls,
        overlay,
        guides,
        condition_debugger,
        timeline,
        snapshot_directory,
        toggle_event_window,
        final_target_names_provider,
        control_manager_kwargs,
    )
    control_manager_holder["manager"] = control_manager
    target_names_lookup = control_manager.get_target_names

    sprite_positions_provider = sprite_positions_provider or _collect_sprite_positions

    wrapped_update_all = _wrap_update_all(original_update_all)

    session = VisualizerSession(
        debug_store=debug_store,
        overlay=overlay,
        renderer=renderer,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        control_manager=control_manager,
        guide_renderer=guide_renderer,
        event_window=None,
        snapshot_directory=snapshot_directory,
        sprite_positions_provider=sprite_positions_provider,
        target_names_provider=target_names_lookup,
        wrapped_update_all=wrapped_update_all,
        previous_update_all=original_update_all,
        previous_debug_store=previous_store,
        previous_enable_flag=previous_enable_flag,
    )
    session_holder["session"] = session

    Action.update_all = classmethod(wrapped_update_all)  # type: ignore[assignment]

    _session._VISUALIZER_SESSION = session
    _install_window_handler(session)
    return session


def detach_visualizer() -> bool:
    """Detach the visualizer and restore previous Action state."""

    if _session._VISUALIZER_SESSION is None:
        return False

    session = _session._VISUALIZER_SESSION
    _restore_action_state(session)
    _remove_window_handler(session)
    _session._VISUALIZER_SESSION = None
    return True


def auto_attach_from_env(*, force: bool = False, attach_kwargs: dict[str, Any] | None = None) -> bool:
    """Attach automatically when ARCADEACTIONS_VISUALIZER is set."""

    if not force and _session._AUTO_ATTACH_ATTEMPTED:
        return False
    _session._AUTO_ATTACH_ATTEMPTED = True

    if os.getenv("ARCADEACTIONS_VISUALIZER") is None:
        return False

    if attach_kwargs is None:
        attach_kwargs = {}

    # Automatically provide target names if not explicitly provided
    if "target_names_provider" not in attach_kwargs:
        attach_kwargs["target_names_provider"] = _collect_target_names_from_view

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


def _enable_action_debugging(debug_store: DebugDataStore) -> None:
    Action.set_debug_store(debug_store)
    Action._enable_visualizer = True  # type: ignore[attr-defined]


def _normalize_snapshot_directory(snapshot_directory: Path | str | None) -> Path:
    if snapshot_directory is None:
        return Path("snapshots")
    return Path(snapshot_directory)


def _prepare_control_manager_kwargs(
    control_manager_kwargs: dict[str, Any] | None,
    target_names_provider: TargetNamesProvider | None,
) -> tuple[dict[str, Any], TargetNamesProvider | None]:
    if control_manager_kwargs is None:
        control_manager_kwargs = {}
    else:
        control_manager_kwargs = dict(control_manager_kwargs)
    if "target_names_provider" not in control_manager_kwargs:
        control_manager_kwargs["target_names_provider"] = target_names_provider
    return control_manager_kwargs, control_manager_kwargs.pop("target_names_provider")


def _build_event_window_toggle(
    session_holder: dict[str, VisualizerSession | None],
    control_manager_holder: dict[str, DebugControlManager | None],
    event_window_cls: type[EventInspectorWindow],
) -> Callable[[bool], None]:
    def _on_event_window_closed() -> None:
        session = session_holder["session"]
        manager = control_manager_holder["manager"]
        if session is not None:
            session.event_window = None
            if session.window is not None:
                window_commands.set_window(session.window)
        if manager is not None:
            manager.condition_panel_visible = False

    def toggle_event_window(open_state: bool) -> None:
        session = session_holder["session"]
        manager = control_manager_holder["manager"]
        if session is None:
            return
        if open_state:
            _open_event_window(session, manager, event_window_cls, _on_event_window_closed)
        else:
            _close_event_window(session)

    return toggle_event_window


def _open_event_window(
    session: VisualizerSession,
    manager: DebugControlManager | None,
    event_window_cls: type[EventInspectorWindow],
    on_close_callback: Callable[[], None],
) -> None:
    if session.event_window is not None:
        return
    try:
        # Create provider function for highlighted target ID.
        def get_highlighted_target() -> int | None:
            return session.overlay.highlighted_target_id

        window = event_window_cls(
            debug_store=session.debug_store,
            on_close_callback=on_close_callback,
            target_names_provider=session.target_names_provider,
            highlighted_target_provider=get_highlighted_target,
            forward_key_handler=manager.handle_key_press if manager is not None else None,
            main_window=session.window,
        )
    except Exception as exc:
        print(f"[ACE] Failed to open event window: {exc!r}")
        if manager is not None:
            manager.condition_panel_visible = False
        return
    move_to_primary_monitor(window, offset_x=40, offset_y=60)
    headless_mode = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    if not headless_mode:
        window.set_visible(True)
    session.event_window = window
    if not headless_mode:
        window.request_main_window_focus()


def _close_event_window(session: VisualizerSession) -> None:
    if session.event_window is None:
        return
    try:
        session.event_window.close()
    except Exception as exc:
        print(f"[ACE] Error closing debugger window: {exc!r}")
    session.event_window = None
    if session.window is not None:
        window_commands.set_window(session.window)


def _create_control_manager(
    controls_cls: type[DebugControlManager],
    overlay: InspectorOverlay,
    guides: GuideManager,
    condition_debugger: ConditionDebugger,
    timeline: TimelineStrip,
    snapshot_directory: Path,
    toggle_event_window: Callable[[bool], None],
    target_names_provider: TargetNamesProvider | None,
    control_manager_kwargs: dict[str, Any],
) -> DebugControlManager:
    return controls_cls(
        overlay=overlay,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        snapshot_directory=snapshot_directory,
        action_controller=Action,
        toggle_event_window=toggle_event_window,
        target_names_provider=target_names_provider,
        **control_manager_kwargs,
    )


def _wrap_update_all(original_update_all: Callable[..., None]) -> Callable[..., None]:
    def wrapped_update_all(cls: type[Action], delta_time: float, physics_engine: Any = None) -> None:
        original_update_all(cls, delta_time, physics_engine=physics_engine)
        session = _session._VISUALIZER_SESSION
        if session is None:
            return
        _install_window_handler(session)
        positions = _collect_positions(session)
        session.control_manager.update(positions)
        session.renderer.update()
        session.guide_renderer.update()

    return wrapped_update_all


def _collect_positions(session: VisualizerSession) -> dict[int, tuple[float, float]]:
    provider = session.sprite_positions_provider
    if provider is None:
        return {}
    try:
        return provider() or {}
    except Exception:
        return {}


def _restore_action_state(session: VisualizerSession) -> None:
    current_update = getattr(Action.update_all, "__func__", Action.update_all)
    if current_update is session.wrapped_update_all:
        Action.update_all = classmethod(session.previous_update_all)  # type: ignore[assignment]
    Action.set_debug_store(session.previous_debug_store)
    Action._enable_visualizer = session.previous_enable_flag  # type: ignore[attr-defined]
    if session.event_window is not None:
        try:
            session.event_window.close()
        except Exception as exc:
            print(f"[ACE] Error closing debugger window during detach: {exc!r}")
        session.event_window = None
