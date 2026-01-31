"""Helper functions for DevVisualizer palette lifecycle and positioning."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import arcade


class PaletteHost(Protocol):
    """Protocol for DevVisualizer palette coordination."""

    visible: bool
    window: arcade.Window | None
    palette_window: Any | None
    _palette_show_pending: bool
    _window_decoration_dx: int | None
    _window_decoration_dy: int | None
    _EXTRA_FRAME_PAD: int
    _is_detaching: bool
    ctx: Any
    _position_tracker: Any

    def update_main_window_position(self) -> bool: ...

    def _get_tracked_window_position(self, window: arcade.Window) -> tuple[int, int] | None: ...

    def handle_key_press(self, key: int, modifiers: int) -> bool: ...

    def _create_palette_window(self) -> None: ...

    def _position_palette_window(self, *, force: bool = False) -> bool: ...


def poll_show_palette(
    host: PaletteHost,
    *,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    """Wait until main window has a real location, then position & show palette."""
    if not host.visible:
        host._palette_show_pending = False
        return
    if not _ensure_window(host):
        _schedule_poll(host, get_primary_monitor_rect, palette_window_cls, registry_provider)
        return
    if not _window_has_valid_location(host.window):
        _schedule_poll(host, get_primary_monitor_rect, palette_window_cls, registry_provider)
        return
    _update_window_decorations(host)
    if not host.visible:
        host._palette_show_pending = False
        return
    _show_palette_window(host, palette_window_cls, registry_provider)


def _schedule_poll(
    host: PaletteHost,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    arcade.schedule_once(lambda dt: poll_show_palette(  # noqa: B023
        host,
        get_primary_monitor_rect=get_primary_monitor_rect,
        palette_window_cls=palette_window_cls,
        registry_provider=registry_provider,
    ), 0.05)


def _ensure_window(host: PaletteHost) -> bool:
    if host.window is not None:
        return True
    try:
        host.window = arcade.get_window()
    except RuntimeError:
        pass
    return host.window is not None


def _window_has_valid_location(window: arcade.Window | None) -> bool:
    if window is None:
        return False
    try:
        x, y = window.get_location()
        return (x, y) != (0, 0) and x > -32000 and y > -32000
    except Exception:
        return False


def _update_window_decorations(host: PaletteHost) -> None:
    if host._window_decoration_dx is not None or host.window is None:
        return
    try:
        from arcadeactions.dev import window_decorations

        calc_dx, calc_dy = window_decorations.measure_window_decoration_deltas(host.window)
        if calc_dx is not None or calc_dy is not None:
            host._window_decoration_dx = calc_dx
            host._window_decoration_dy = calc_dy
    except Exception as exc:
        print(f"[DevVisualizer] _poll_show_palette: Exception measuring decorations: {exc}")
        import traceback

        traceback.print_exc()


def _show_palette_window(
    host: PaletteHost,
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    if host.palette_window is None:
        host._create_palette_window()
    if host.palette_window is None:
        print("[DevVisualizer] Failed to create palette window, deferring show")
        host._palette_show_pending = False
        return
    host.update_main_window_position()
    host._position_palette_window(force=True)
    host.palette_window.show_window()
    host._palette_show_pending = False


def create_palette_window(
    host: PaletteHost,
    *,
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    """Create the palette window."""

    def on_palette_close():
        if not host._is_detaching and host.window:
            try:
                if not host.window.closed:
                    host.window.close()
            except Exception:
                pass
        host.palette_window = None

    def forward_key_handler(key: int, modifiers: int) -> bool:
        if not host.visible:
            return False
        return host.handle_key_press(key, modifiers)

    host.palette_window = palette_window_cls(
        registry=registry_provider(),
        ctx=host.ctx,
        on_close_callback=on_palette_close,
        forward_key_handler=forward_key_handler,
        main_window=host.window,
    )


def get_window_location(host: PaletteHost, window: Any) -> tuple[int, int] | None:
    """Safely get window location, using tracked positions when available."""
    if window is None:
        return None

    if hasattr(window, "get_location"):
        try:
            location = window.get_location()
            if location and location != (0, 0) and location[0] > -32000 and location[1] > -32000:
                return (int(location[0]), int(location[1]))
        except Exception:
            pass

    tracked_pos = host._get_tracked_window_position(window)
    if tracked_pos and tracked_pos != (0, 0):
        return tracked_pos

    stored = getattr(window, "_arcadeactions_last_set_location", None)
    if stored and stored != (0, 0):
        return stored

    if hasattr(window, "location"):
        loc = window.location
        if isinstance(loc, tuple) and len(loc) == 2:
            return (int(loc[0]), int(loc[1]))

    return None


def position_palette_window(
    host: PaletteHost,
    *,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    force: bool = False,
) -> bool:
    """Position palette window relative to main window."""
    if host.palette_window is None:
        print("[DevVisualizer] No palette window, returning False")
        return False

    if host.palette_window.visible and not force:
        print("[DevVisualizer] Palette window is visible, not repositioning")
        return False

    anchor_window = _select_anchor_window(host)

    if anchor_window is None:
        print("[DevVisualizer] Anchor window is None")
        return False

    primary_rect = _get_primary_rect(get_primary_monitor_rect)
    if primary_rect is None:
        return False

    main_x, main_y = _resolve_main_location(host, anchor_window, primary_rect)
    palette_x, palette_y = _compute_palette_position(host, main_x, main_y, primary_rect)
    return _set_palette_position(host, palette_x, palette_y)


def _select_anchor_window(host: PaletteHost) -> arcade.Window | None:
    anchor_window = host.window
    try:
        current_window = arcade.get_window()
    except RuntimeError:
        return anchor_window
    if current_window is None or host.window == current_window:
        return anchor_window
    test_loc = host._get_tracked_window_position(current_window)
    if test_loc is None and hasattr(current_window, "get_location"):
        try:
            test_loc = current_window.get_location()
        except Exception:
            test_loc = None
    if test_loc and test_loc != (0, 0) and test_loc[0] > -32000 and test_loc[1] > -32000:
        host.window = current_window
        return current_window
    return anchor_window


def _get_primary_rect(
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
) -> tuple[int, int, int, int] | None:
    return get_primary_monitor_rect()


def _resolve_main_location(
    host: PaletteHost,
    anchor_window: arcade.Window,
    primary_rect: tuple[int, int, int, int],
) -> tuple[int, int]:
    primary_x, primary_y, primary_w, primary_h = primary_rect
    main_location = get_window_location(host, anchor_window)
    if main_location is None:
        main_x = primary_x + primary_w // 4
        main_y = primary_y + primary_h // 4
        return (main_x, main_y)
    return main_location


def _compute_palette_position(
    host: PaletteHost,
    main_x: int,
    main_y: int,
    primary_rect: tuple[int, int, int, int],
) -> tuple[int, int]:
    primary_x, primary_y, _primary_w, _primary_h = primary_rect
    main_offset_x = main_x - primary_x
    deco_dx = host._window_decoration_dx or 0
    deco_dy = host._window_decoration_dy or 0
    palette_width = host.palette_window.width
    palette_right_border = deco_dx if deco_dx > 0 else 0
    palette_x = int(
        primary_x + main_offset_x - palette_width - deco_dx - palette_right_border - host._EXTRA_FRAME_PAD
    )
    palette_y = int(main_y - deco_dy)
    return palette_x, palette_y


def _set_palette_position(host: PaletteHost, palette_x: int, palette_y: int) -> bool:
    try:
        host.palette_window.set_location(palette_x, palette_y)
        host._position_tracker.track_known_position(host.palette_window, palette_x, palette_y)
        return True
    except Exception as exc:
        print(f"[DevVisualizer] Failed to position palette window: {exc}")
        return False


def toggle_palette(
    host: PaletteHost,
    *,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    """Toggle palette window visibility."""
    if host.palette_window is None:
        create_palette_window(host, palette_window_cls=palette_window_cls, registry_provider=registry_provider)
    if host.palette_window:
        was_visible = host.palette_window.visible
        if not was_visible:
            tracked = host.update_main_window_position()
            if tracked:
                host._position_palette_window(force=False)
            else:
                print("[DevVisualizer] Deferring palette positioning until window location is known (toggle)")
        host.palette_window.toggle_window()
        if not was_visible and host.palette_window.visible:
            host.palette_window.request_main_window_focus()
