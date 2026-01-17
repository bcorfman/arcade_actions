"""Visualizer attach/detach helpers for ArcadeActions."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import arcade
from arcade import window_commands

from actions.base import Action
from actions.display import move_to_primary_monitor
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.controls import DebugControlManager
from actions.visualizer.event_window import EventInspectorWindow
from actions.visualizer.guides import GuideManager
from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.renderer import GuideRenderer, OverlayRenderer
from actions.visualizer.timeline import TimelineStrip

SpritePositionsProvider = Callable[[], dict[int, tuple[float, float]]]
TargetNamesProvider = Callable[[], dict[int, str]]

_WINDOW_SENTINEL = object()


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


# Cache for sprite positions to avoid expensive recalculation every frame
_position_cache: dict[int, tuple[float, float]] = {}
_cached_action_count = 0
_cached_action_ids: set[int] = set()
_cached_targets: dict[int, object] = {}  # target_id -> target object


def _collect_sprite_positions() -> dict[int, tuple[float, float]]:
    """Attempt to collect sprite positions from active actions.

    Uses caching to avoid expensive iteration when action set hasn't changed.
    """
    global _position_cache, _cached_action_count, _cached_action_ids, _cached_targets

    current_actions = Action._active_actions  # type: ignore[attr-defined]
    current_count = len(current_actions)
    current_ids = {id(a) for a in current_actions}

    # If action set hasn't changed, use cached targets and update positions
    if current_count == _cached_action_count and current_ids == _cached_action_ids:
        # Fast path: update positions from cached targets
        positions = {}
        for target_id, target in _cached_targets.items():
            try:
                if hasattr(target, "center_x") and hasattr(target, "center_y"):
                    positions[target_id] = (target.center_x, target.center_y)
                else:
                    # SpriteList case - calculate average and update individual sprites
                    sum_x = 0.0
                    sum_y = 0.0
                    count = 0
                    try:
                        for sprite in target:
                            try:
                                sprite_id = id(sprite)
                                positions[sprite_id] = (sprite.center_x, sprite.center_y)
                                sum_x += sprite.center_x
                                sum_y += sprite.center_y
                                count += 1
                            except AttributeError:
                                continue
                        if count:
                            positions[target_id] = (sum_x / count, sum_y / count)
                    except TypeError:
                        pass
            except (AttributeError, TypeError):
                continue
        _position_cache = positions
        return positions

    # Slow path: rebuild cache from scratch
    positions: dict[int, tuple[float, float]] = {}
    _cached_targets.clear()

    for action in current_actions:
        target = getattr(action, "target", None)
        if target is None:
            continue

        target_id = id(target)

        sprite_target = True
        try:
            positions[target_id] = (target.center_x, target.center_y)
            _cached_targets[target_id] = target
        except AttributeError:
            # Not a sprite-like target, fall back to iteration path.
            sprite_target = False

        if sprite_target:
            continue

        # Try iterating if the target behaves like a sprite list.
        try:
            sum_x = 0.0
            sum_y = 0.0
            count = 0
            for sprite in target:
                try:
                    sprite_id = id(sprite)
                    positions[sprite_id] = (sprite.center_x, sprite.center_y)
                    sum_x += sprite.center_x
                    sum_y += sprite.center_y
                    count += 1
                except AttributeError:
                    continue
            if count:
                positions[target_id] = (sum_x / count, sum_y / count)
            _cached_targets[target_id] = target
        except TypeError:
            continue

    _position_cache = positions
    _cached_action_count = current_count
    _cached_action_ids = current_ids
    return positions


def _collect_sprite_sizes_and_ids() -> tuple[dict[int, tuple[float, float]], dict[int, list[int]]]:
    """Collect sprite sizes and sprite IDs that belong to each target.

    Returns:
        Tuple of (sprite_sizes, sprite_ids_in_target)
        - sprite_sizes: Dict mapping sprite ID to (width, height)
        - sprite_ids_in_target: Dict mapping target ID to list of sprite IDs it contains
    """
    sprite_sizes: dict[int, tuple[float, float]] = {}
    sprite_ids_in_target: dict[int, list[int]] = {}

    # Use cached targets from position collection
    for target_id, target in _cached_targets.items():
        try:
            # Check if target is a single sprite
            if hasattr(target, "width") and hasattr(target, "height"):
                sprite_sizes[target_id] = (target.width, target.height)
            else:
                # Target is a SpriteList - collect all sprites in it
                sprite_list = []
                try:
                    for sprite in target:
                        try:
                            sprite_id = id(sprite)
                            if hasattr(sprite, "width") and hasattr(sprite, "height"):
                                sprite_sizes[sprite_id] = (sprite.width, sprite.height)
                                sprite_list.append(sprite_id)
                        except AttributeError:
                            continue
                    if sprite_list:
                        sprite_ids_in_target[target_id] = sprite_list
                except TypeError:
                    pass
        except (AttributeError, TypeError):
            continue

    return sprite_sizes, sprite_ids_in_target


def _collect_target_names_from_view() -> dict[int, str]:
    """Attempt to collect target names from the current game view.

    Inspects the current view's attributes to find SpriteLists and Sprites,
    mapping their IDs to their attribute names (e.g., "self.enemy_list").
    Also inspects active actions to map their targets.
    """
    import arcade  # Import at function level to avoid circular imports

    names: dict[int, str] = {}

    try:
        window = arcade.get_window()
    except RuntimeError:
        window = None

    view = None
    if window is not None:
        view = getattr(window, "current_view", None)

    if view is not None:
        for attr_name in dir(view):
            # Skip private attributes and methods
            if attr_name.startswith("_"):
                continue

            try:
                attr_value = getattr(view, attr_name, None)
                if attr_value is None:
                    continue

                # Check if it's a SpriteList
                # Note: Using isinstance for external library types (arcade) is acceptable
                # per project guidelines - this is not checking our own interfaces
                if isinstance(attr_value, arcade.SpriteList):
                    target_id = id(attr_value)
                    # Use "self" to match how attributes are referenced in class methods
                    names[target_id] = f"self.{attr_name}"

                    # Also map individual sprites in the list with hex ID
                    try:
                        for sprite in attr_value:
                            sprite_id = id(sprite)
                            hex_id = hex(sprite_id)[-4:]  # Last 4 hex chars for brevity
                            names[sprite_id] = f"Sprite#{hex_id} in self.{attr_name}"
                    except (TypeError, AttributeError):
                        pass

                # Check if it's a Sprite
                elif isinstance(attr_value, arcade.Sprite):
                    target_id = id(attr_value)
                    names[target_id] = f"self.{attr_name}"

            except Exception:
                # Skip attributes that can't be accessed
                continue

    # Also inspect active actions to find targets that might not be direct view attributes
    # This helps catch dynamically created sprites (like bullets)
    try:
        for action in list(Action._active_actions):  # type: ignore[attr-defined]
            target = getattr(action, "target", None)
            if target is None:
                continue

            target_id = id(target)

            # If we already have a name for this target, skip it
            if target_id in names:
                continue

            # Try to find this target in view attributes by comparing IDs
            if view is not None:
                found_name = None
                for attr_name in dir(view):
                    if attr_name.startswith("_"):
                        continue
                    try:
                        attr_value = getattr(view, attr_name, None)
                        if attr_value is target:  # Identity check, not equality
                            found_name = f"self.{attr_name}"
                            break
                        # Also check if it's a SpriteList containing this sprite
                        if isinstance(attr_value, arcade.SpriteList):
                            try:
                                for sprite in attr_value:
                                    if sprite is target:  # Identity check
                                        hex_id = hex(target_id)[-4:]
                                        found_name = f"Sprite#{hex_id} in self.{attr_name}"
                                        break
                            except (TypeError, AttributeError):
                                pass
                        if found_name:
                            break
                    except Exception:
                        continue

                if found_name:
                    names[target_id] = found_name
                    continue

            # If not found in view, check if it's a Sprite and try to find which list contains it
            if isinstance(target, arcade.Sprite) and view is not None:
                for attr_name in dir(view):
                    if attr_name.startswith("_"):
                        continue
                    try:
                        attr_value = getattr(view, attr_name, None)
                        if isinstance(attr_value, arcade.SpriteList):
                            try:
                                if target in attr_value:  # Membership check
                                    hex_id = hex(target_id)[-4:]
                                    names[target_id] = f"Sprite#{hex_id} in self.{attr_name}"
                                    break
                            except (TypeError, AttributeError):
                                pass
                    except Exception:
                        continue

    except Exception:
        # If inspecting actions fails, just return what we have from the view
        pass

    return names


def _install_window_handler(session: VisualizerSession) -> None:
    """Register window hooks so the overlay renders and function keys work."""

    try:
        window = arcade.get_window()
    except RuntimeError:
        window = None

    if window is None:
        return

    if session.window is not None and session.window is not window:
        _remove_window_handler(session)

    # Wrap on_draw to render overlay
    current_on_draw = getattr(window, "on_draw", None)
    if current_on_draw is not None:
        if getattr(current_on_draw, "__visualizer_overlay__", False):
            session.original_window_on_draw = getattr(current_on_draw, "__visualizer_original__", None)
        elif session.original_window_on_draw is None:

            def overlay_on_draw(*args: Any, **kwargs: Any) -> Any:
                result: Any = None
                try:
                    result = current_on_draw(*args, **kwargs)
                finally:
                    if is_visualizer_attached() and _VISUALIZER_SESSION is session:
                        render_window = session.window
                        previous_window: arcade.Window | None = None
                        if render_window is not None:
                            try:
                                try:
                                    previous_window = window_commands.get_window()
                                except RuntimeError:
                                    previous_window = None
                                if previous_window is not render_window:
                                    window_commands.set_window(render_window)
                                    render_window.switch_to()
                            except Exception:
                                render_window = None
                        try:
                            session.renderer.draw()
                            session.guide_renderer.draw()
                        except Exception:
                            pass
                        if render_window is not None and previous_window is not render_window:
                            window_commands.set_window(previous_window)
                return result

            overlay_on_draw.__visualizer_overlay__ = True
            overlay_on_draw.__visualizer_original__ = current_on_draw
            window.on_draw = overlay_on_draw  # type: ignore[assignment]
            session.original_window_on_draw = current_on_draw

    # Wrap on_key_press to handle debugger hotkeys while preserving game input
    current_on_key_press = getattr(window, "on_key_press", None)
    if current_on_key_press is not None:
        if getattr(current_on_key_press, "__visualizer_key__", False):
            session.original_window_on_key_press = getattr(current_on_key_press, "__visualizer_key_original__", None)
        elif session.original_window_on_key_press is None:

            def overlay_on_key_press(symbol: int, modifiers: int) -> bool:
                handled = False
                if is_visualizer_attached() and _VISUALIZER_SESSION is session and session.control_manager is not None:
                    try:
                        handled = bool(session.control_manager.handle_key_press(symbol, modifiers))
                    except Exception:
                        handled = False
                if handled:
                    return True

                if current_on_key_press is not None:
                    result = current_on_key_press(symbol, modifiers)
                    if result is None:
                        return False
                    return bool(result)
                return False

            overlay_on_key_press.__visualizer_key__ = True
            overlay_on_key_press.__visualizer_key_original__ = current_on_key_press
            window.on_key_press = overlay_on_key_press  # type: ignore[assignment]
            session.original_window_on_key_press = current_on_key_press

    # Wrap on_close to close debugger window when main window closes
    current_on_close = getattr(window, "on_close", None)
    if current_on_close is not None:
        if getattr(current_on_close, "__visualizer_close__", False):
            session.original_window_on_close = getattr(current_on_close, "__visualizer_close_original__", None)
        elif session.original_window_on_close is None:

            def overlay_on_close(*args: Any, **kwargs: Any) -> Any:
                # Close debugger window if it exists
                if session.event_window is not None:
                    try:
                        session.event_window.close()
                    except Exception as exc:
                        print(f"[ACE] Error closing debugger window: {exc!r}")
                    session.event_window = None
                # Call original handler if it exists
                if current_on_close is not None:
                    return current_on_close(*args, **kwargs)
                return None

            overlay_on_close.__visualizer_close__ = True
            overlay_on_close.__visualizer_close_original__ = current_on_close
            window.on_close = overlay_on_close  # type: ignore[assignment]
            session.original_window_on_close = current_on_close

    session.window = window


def _remove_window_handler(session: VisualizerSession) -> None:
    """Remove any previously registered draw handler."""

    if session.window is None:
        session.original_window_on_draw = None
        session.original_window_on_key_press = None
        session.original_window_on_close = None
        return

    current_on_draw = getattr(session.window, "on_draw", None)
    should_restore = getattr(current_on_draw, "__visualizer_overlay__", False)

    if session.original_window_on_draw is not None and should_restore:
        session.window.on_draw = session.original_window_on_draw  # type: ignore[assignment]

    current_on_key_press = getattr(session.window, "on_key_press", None)
    key_should_restore = getattr(current_on_key_press, "__visualizer_key__", False)

    if session.original_window_on_key_press is not None and key_should_restore:
        session.window.on_key_press = session.original_window_on_key_press  # type: ignore[assignment]

    current_on_close = getattr(session.window, "on_close", None)
    close_should_restore = getattr(current_on_close, "__visualizer_close__", False)

    if session.original_window_on_close is not None and close_should_restore:
        session.window.on_close = session.original_window_on_close  # type: ignore[assignment]

    session.window = None
    session.original_window_on_draw = None
    session.original_window_on_key_press = None
    session.original_window_on_close = None


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
    guides = guide_manager_cls(initial_enabled=False)  # Guides start disabled, press F5 to enable
    condition_debugger = condition_debugger_cls(debug_store)
    timeline = timeline_cls(debug_store)
    guide_renderer = guide_renderer_cls(guides)

    if control_manager_kwargs is None:
        control_manager_kwargs = {}
    else:
        control_manager_kwargs = dict(control_manager_kwargs)
    if "target_names_provider" not in control_manager_kwargs:
        control_manager_kwargs["target_names_provider"] = target_names_provider
    final_target_names_provider = control_manager_kwargs.pop("target_names_provider")

    session_holder: dict[str, VisualizerSession | None] = {"session": None}
    control_manager_holder: dict[str, DebugControlManager | None] = {"manager": None}

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
            if session.event_window is not None:
                return
            try:
                # Create provider function for highlighted target ID
                def get_highlighted_target() -> int | None:
                    if session is None or session.overlay is None:
                        return None
                    return session.overlay.highlighted_target_id

                window = event_window_cls(
                    debug_store=session.debug_store,
                    on_close_callback=_on_event_window_closed,
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
            # Position window before making it visible to avoid visible jump
            move_to_primary_monitor(window, offset_x=40, offset_y=60)
            window.set_visible(True)
            session.event_window = window
            window.request_main_window_focus()
        else:
            if session.event_window is not None:
                try:
                    session.event_window.close()
                except Exception as exc:
                    print(f"[ACE] Error closing debugger window: {exc!r}")
                session.event_window = None
                if session.window is not None:
                    window_commands.set_window(session.window)

    control_manager = controls_cls(
        overlay=overlay,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        snapshot_directory=snapshot_directory,
        action_controller=Action,
        toggle_event_window=toggle_event_window,
        target_names_provider=final_target_names_provider,
        **control_manager_kwargs,
    )
    control_manager_holder["manager"] = control_manager
    target_names_lookup = control_manager.get_target_names

    if sprite_positions_provider is None:
        sprite_positions_provider = _collect_sprite_positions

    def wrapped_update_all(cls: type[Action], delta_time: float, physics_engine: Any = None) -> None:
        original_update_all(cls, delta_time, physics_engine=physics_engine)
        if _VISUALIZER_SESSION is None:
            return
        _install_window_handler(_VISUALIZER_SESSION)
        session = _VISUALIZER_SESSION

        # Collect sprite positions (cached for performance)
        # Note: positions are primarily used for guides, but we collect them always
        # for test compatibility and potential future use
        positions: dict[int, tuple[float, float]] = {}
        provider = session.sprite_positions_provider
        if provider is not None:
            try:
                positions = provider() or {}
            except Exception:
                positions = {}

        session.control_manager.update(positions)
        session.renderer.update()
        session.guide_renderer.update()

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

    _VISUALIZER_SESSION = session
    _install_window_handler(session)
    return session


def detach_visualizer() -> bool:
    """Detach the visualizer and restore previous Action state."""

    global _VISUALIZER_SESSION
    if _VISUALIZER_SESSION is None:
        return False

    session = _VISUALIZER_SESSION

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
    _remove_window_handler(session)

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
