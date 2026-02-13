"""Helper functions for DevVisualizer palette lifecycle and positioning.

These helpers intentionally avoid relying on Arcade's global "current window"
state. With multiple windows (main + palette), `arcade.get_window()` can return
the palette window depending on focus, which can cause incorrect anchoring and
positional drift.
"""

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
    _palette_desired_visible: bool
    _window_decoration_dx: int | None
    _window_decoration_dy: int | None
    _EXTRA_FRAME_PAD: int
    _is_detaching: bool
    ctx: Any
    _position_tracker: Any

    def update_main_window_position(self) -> bool: ...

    def _get_tracked_window_position(self, window: arcade.Window) -> tuple[int, int] | None: ...

    def handle_key_press(self, key: int, modifiers: int) -> bool: ...
    def toggle(self) -> None: ...
    def toggle_palette(self) -> None: ...
    def toggle_command_palette(self) -> None: ...

    def _create_palette_window(self) -> None: ...

    def _position_palette_window(self, *, force: bool = False) -> bool: ...

    def _restore_palette_location_after_show(self) -> None: ...

    def _activate_main_window(self) -> None: ...


def poll_show_palette(
    host: PaletteHost,
    *,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    """Wait until main window has a real location, then position & show palette."""
    # Only show if the palette is desired and a show poll is pending. This avoids
    # unexpected palette opens from stale scheduled callbacks.
    if not host._palette_desired_visible:
        host._palette_show_pending = False
        return
    if not host._palette_show_pending:
        return
    if not _ensure_window(host):
        _schedule_poll(host, get_primary_monitor_rect, palette_window_cls, registry_provider)
        return
    if not _window_has_valid_location(host.window):
        _schedule_poll(host, get_primary_monitor_rect, palette_window_cls, registry_provider)
        return
    _update_window_decorations(host)
    _show_palette_window(host, palette_window_cls, registry_provider)


def _schedule_poll(
    host: PaletteHost,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    arcade.schedule_once(
        lambda dt: poll_show_palette(  # noqa: B023
            host,
            get_primary_monitor_rect=get_primary_monitor_rect,
            palette_window_cls=palette_window_cls,
            registry_provider=registry_provider,
        ),
        0.05,
    )


def _ensure_window(host: PaletteHost) -> bool:
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
    except Exception:
        # Decoration measurement is best-effort; positioning still works without it.
        return


def _show_palette_window(
    host: PaletteHost,
    palette_window_cls: Callable[..., Any],
    registry_provider: Callable[[], Any],
) -> None:
    if host.palette_window is None:
        host._create_palette_window()
    if host.palette_window is None:
        host._palette_show_pending = False
        return
    host.update_main_window_position()
    host._position_palette_window(force=True)
    host.palette_window.show_window()
    host._restore_palette_location_after_show()
    host._activate_main_window()
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
        if key == arcade.key.F12:
            host.toggle()
            return True
        if key == arcade.key.F11:
            host.toggle_palette()
            return True
        if key == arcade.key.F8:
            host.toggle_command_palette()
            return True
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
    try:
        location = window.get_location()
        if location and location != (0, 0) and location[0] > -32000 and location[1] > -32000:
            return (int(location[0]), int(location[1]))
    except Exception:
        location = None

    tracked_pos = host._get_tracked_window_position(window)
    if tracked_pos and tracked_pos != (0, 0) and tracked_pos[0] > -32000 and tracked_pos[1] > -32000:
        return tracked_pos

    return None


def position_palette_window(
    host: PaletteHost,
    *,
    get_primary_monitor_rect: Callable[[], tuple[int, int, int, int] | None],
    force: bool = False,
) -> bool:
    """Position palette window relative to main window."""
    if host.palette_window is None:
        return False

    if host.palette_window.visible and not force:
        return False

    anchor_window = host.window
    if anchor_window is None:
        return False

    primary_rect = _get_primary_rect(get_primary_monitor_rect)
    if primary_rect is None:
        return False

    main_x, main_y = _resolve_main_location(host, anchor_window, primary_rect)
    palette_x, palette_y = _compute_palette_position(host, main_x, main_y, primary_rect)
    return _set_palette_position(host, palette_x, palette_y)


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
    """Compute palette window location given the main window's location.

    We intentionally avoid applying decoration deltas here.

    `Window.set_location()` and `Window.get_location()` are not consistent across
    platforms/WMs about whether the coordinate refers to the client area or the
    decorated frame. Applying a measured decoration delta can cause the palette
    to drift on show/hide (map/unmap) cycles.

    Instead, we place the palette relative to the main window's reported
    location and cache the palette's OS-reported location after the first
    successful placement (see DevVisualizer), so subsequent toggles can reuse a
    stable absolute position.
    """
    primary_x, primary_y, _primary_w, _primary_h = primary_rect
    main_offset_x = main_x - primary_x
    palette_width = host.palette_window.width
    palette_x = int(primary_x + main_offset_x - palette_width - host._EXTRA_FRAME_PAD)
    palette_y = int(main_y)
    return palette_x, palette_y


def _set_palette_position(host: PaletteHost, palette_x: int, palette_y: int) -> bool:
    try:
        host.palette_window.set_location(palette_x, palette_y)
        host.palette_window._arcadeactions_last_set_location = (palette_x, palette_y)  # type: ignore[attr-defined]
        host._position_tracker.track_known_position(host.palette_window, palette_x, palette_y)
        return True
    except Exception:
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
        host.palette_window.toggle_window()
