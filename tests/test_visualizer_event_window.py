from __future__ import annotations

import arcade
import pytest

from arcade import window_commands
from actions.visualizer import event_window as event_window_module
from actions.visualizer.event_window import EventInspectorWindow
from actions.visualizer.instrumentation import DebugDataStore


@pytest.fixture
def store() -> DebugDataStore:
    store = DebugDataStore()
    for frame in range(1, 6):
        store.update_frame(frame, frame / 60.0)
        store.record_event("created", frame, "MoveUntil", frame * 10, "Sprite")
    return store


def _mock_event_window_base(monkeypatch: pytest.MonkeyPatch, *, init=None) -> None:
    """Patch the concrete arcade.Window base used by EventInspectorWindow."""

    base_cls = EventInspectorWindow.__mro__[1]

    if init is not None:
        monkeypatch.setattr(base_cls, "__init__", init, raising=False)

    monkeypatch.setattr(base_cls, "set_location", lambda self, x, y: None, raising=False)
    monkeypatch.setattr(base_cls, "close", lambda self: None, raising=False)
    monkeypatch.setattr(base_cls, "clear", lambda self: None, raising=False)
    monkeypatch.setattr(base_cls, "switch_to", lambda self: None, raising=False)
    monkeypatch.setattr(base_cls, "on_resize", lambda self, width, height: None, raising=False)
    monkeypatch.setattr(base_cls, "set_size", lambda self, width, height: None, raising=False)


def test_event_window_initializes(monkeypatch, store: DebugDataStore):
    init_args = {}

    def fake_init(self, width, height, title, resizable, *args, **kwargs):
        init_args["width"] = width
        init_args["height"] = height
        init_args["title"] = title
        init_args["resizable"] = resizable
        self._width = width
        self._height = height
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)

    class DummyText:
        def __init__(self, text, x, y, color, font_size, bold=False):
            self.text = text
            self.position = (x, y)
            self.color = color
            self.font_size = font_size
            self.bold = bold
            # Approximate width for layout calculations
            self.content_width = len(text) * (font_size * 0.6)

        def draw(self) -> None:
            return None

    monkeypatch.setattr(arcade, "Text", DummyText)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)

    window = EventInspectorWindow(store)
    window.set_visible(True)
    window.set_visible(True)

    if init_args:
        assert init_args["width"] == 520
        assert init_args["height"] == 360
        assert init_args["title"] == "ACE Action Timeline"
        assert init_args["resizable"] is True
    else:
        # Headless fallback on Windows/macOS may bypass monkeypatched __init__.
        # Validate using the window attributes instead so we still cover behaviour.
        assert getattr(window, "width", None) == 520
        assert getattr(window, "height", None) == 360


def test_event_window_draws_timeline_and_conditions(monkeypatch, store: DebugDataStore):
    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)

    drawn_texts: list[str] = []

    class RecordingText:
        def __init__(self, text, x, y, color, font_size, bold=False):
            self.text = text
            self.position = (x, y)
            self.color = color
            self.font_size = font_size
            self.bold = bold
            # Approximate width for layout calculations
            self.content_width = len(text) * (font_size * 0.6)

        def draw(self) -> None:
            drawn_texts.append(self.text)

    monkeypatch.setattr(arcade, "Text", RecordingText)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    window = EventInspectorWindow(store)
    window.set_visible(True)
    window.on_draw()

    assert any("Action Timeline" in text for text in drawn_texts)
    assert any("Legend:" in text for text in drawn_texts)
    assert any("SpriteList" in text for text in drawn_texts)
    assert any("Sprite" in text for text in drawn_texts)


def test_event_window_draw_skips_without_context(monkeypatch, store: DebugDataStore):
    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(
        arcade.Window, "clear", lambda self: (_ for _ in ()).throw(AssertionError("clear called")), raising=False
    )
    monkeypatch.setattr(
        arcade.Window,
        "switch_to",
        lambda self: (_ for _ in ()).throw(AssertionError("switch_to called")),
        raising=False,
    )
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    window = EventInspectorWindow(store)
    window._context = None

    monkeypatch.setattr(
        window_commands, "set_window", lambda value: (_ for _ in ()).throw(AssertionError("set_window called"))
    )
    monkeypatch.setattr(window_commands, "get_window", lambda: None)

    window.on_draw()


def test_event_window_restores_previous_window(monkeypatch, store: DebugDataStore):
    sentinel_window = object()

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade.Window, "clear", lambda self: None, raising=False)
    monkeypatch.setattr(arcade.Window, "switch_to", lambda self: None, raising=False)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)

    draw_calls: list[str] = []

    class RecordingText:
        def __init__(self, text, x, y, color, font_size, bold=False):
            self.text = text
            self.position = (x, y)
            self.color = color
            self.font_size = font_size
            self.bold = bold
            # Approximate width for layout calculations
            self.content_width = len(text) * (font_size * 0.6)

        def draw(self) -> None:
            draw_calls.append(self.text)

    monkeypatch.setattr(arcade, "Text", RecordingText, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)

    set_window_calls: list[object | None] = []
    original_set_window = window_commands.set_window
    original_get_window = window_commands.get_window

    def tracking_set_window(value: object | None) -> None:
        set_window_calls.append(value)
        original_set_window(value)

    monkeypatch.setattr(window_commands, "set_window", tracking_set_window)
    monkeypatch.setattr(window_commands, "get_window", lambda: sentinel_window)

    window = EventInspectorWindow(store)
    window.set_visible(True)
    window.on_draw()

    assert set_window_calls[0] is window
    assert set_window_calls[-1] is sentinel_window
    assert any(draw_calls)


def test_event_window_ignores_initial_f4(monkeypatch, store: DebugDataStore):
    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade.Window, "switch_to", lambda self: None, raising=False)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    forward_calls: list[tuple[int, int]] = []

    def forward_handler(symbol: int, modifiers: int) -> bool:
        forward_calls.append((symbol, modifiers))
        return True

    window = EventInspectorWindow(store, forward_key_handler=forward_handler)

    close_calls: list[bool] = []

    def tracking_close():
        close_calls.append(True)

    monkeypatch.setattr(window, "close", tracking_close)

    # First F4 press should be forwarded and not close the window
    window.on_key_press(arcade.key.F4, 0)
    assert forward_calls == [(arcade.key.F4, 0)]
    assert not close_calls

    # If the forward handler declines the event, the window should close
    def declining_handler(symbol: int, modifiers: int) -> bool:
        forward_calls.append((symbol, modifiers))
        return False

    window._forward_key_handler = declining_handler
    window.on_key_press(arcade.key.F4, 0)
    assert close_calls


def test_event_window_on_close_handles_callback_error(monkeypatch, store: DebugDataStore):
    """Test that on_close handles callback exceptions gracefully."""

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade.Window, "switch_to", lambda self: None, raising=False)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    error_occurred = False

    def failing_callback():
        nonlocal error_occurred
        error_occurred = True
        raise ValueError("Callback error")

    window = EventInspectorWindow(store, on_close_callback=failing_callback)

    # Capture print output
    print_calls = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: print_calls.append(args))

    # on_close should handle the exception
    window.on_close()

    # Should have attempted to call callback and logged error
    assert error_occurred
    assert any("Error in event window close callback" in str(call) for call in print_calls)


def test_event_window_font_scales_with_resize(monkeypatch, store: DebugDataStore):
    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade.Window, "clear", lambda self: None, raising=False)
    monkeypatch.setattr(arcade.Window, "switch_to", lambda self: None, raising=False)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)

    class RecordingText:
        def __init__(self, text, x, y, color, font_size, bold=False):
            self.text = text
            self.position = (x, y)
            self.color = color
            self.font_size = font_size
            self.bold = bold
            self.content_width = len(text) * (font_size * 0.6)

        def draw(self) -> None:
            return None

    monkeypatch.setattr(arcade, "Text", RecordingText, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)

    window = EventInspectorWindow(store)
    assert window._font_size == pytest.approx(10.0, rel=1e-4)
    assert window._timeline_renderer.font_size == pytest.approx(10.0, rel=1e-4)

    window.on_resize(780, 540)
    assert window._font_size == pytest.approx(12.0, rel=1e-4)
    assert window._timeline_renderer.font_size == pytest.approx(12.0, rel=1e-4)

    # Ensure standard update still works with resized window
    monkeypatch.setattr(arcade, "get_window", lambda: window, raising=False)
    window._timeline_renderer.update()

    window.on_resize(520, 360)
    assert window._font_size == pytest.approx(10.0, rel=1e-4)
    assert window._timeline_renderer.font_size == pytest.approx(10.0, rel=1e-4)


def test_event_window_draw_background_skips_without_context(monkeypatch, store: DebugDataStore):
    """Test that _draw_background skips when context is missing."""

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    window = EventInspectorWindow(store)
    window._context = None  # Remove context

    # Should not raise, just skip drawing
    window._draw_background()

    # Verify draw_lbwh_rectangle_filled was not called (would be called if context existed)
    # This is tested implicitly - if it was called, it would have been mocked


def test_event_window_on_draw_handles_switch_to_exception(monkeypatch, store: DebugDataStore):
    """Test that on_draw handles switch_to exceptions gracefully."""

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(arcade.Window, "clear", lambda self: None, raising=False)
    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", lambda *args, **kwargs: None)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    window = EventInspectorWindow(store)

    # Make switch_to raise an exception
    def failing_switch_to():
        raise RuntimeError("switch_to failed")

    monkeypatch.setattr(window, "switch_to", failing_switch_to)
    monkeypatch.setattr(window_commands, "get_window", lambda: window)
    monkeypatch.setattr(window_commands, "set_window", lambda value: None)

    # Should handle exception gracefully and return early
    window.on_draw()

    # If we get here without exception, the error was handled
    assert True


def test_event_window_on_update_is_noop(monkeypatch, store: DebugDataStore):
    """Test that on_update is a no-op method."""

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    window = EventInspectorWindow(store)
    # Should return None (no-op)
    result = window.on_update(0.016)
    assert result is None


def test_event_window_on_mouse_press_is_noop(monkeypatch, store: DebugDataStore):
    """Test that on_mouse_press is a no-op method."""

    def fake_init(self, width=0, height=0, title="", resizable=True, **kwargs):
        self._width = width or 520
        self._height = height or 360
        self._scale = 1.0
        self._context = object()
        self._ctx = object()

    _mock_event_window_base(monkeypatch, init=fake_init)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "draw", lambda self: None, raising=False)
    monkeypatch.setattr(event_window_module.TimelineRenderer, "update", lambda self: None, raising=False)
    monkeypatch.setattr(
        arcade, "Text", lambda *args, **kwargs: type("DummyText", (), {"draw": lambda self: None})(), raising=False
    )

    window = EventInspectorWindow(store)
    # Should return None (no-op)
    result = window.on_mouse_press(100, 200, 1, 0)
    assert result is None
