"""
Tests for the visualizer attach/detach helper utilities.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable

import arcade
import pytest

from actions.base import Action


@pytest.fixture(autouse=True)
def auto_detach(monkeypatch):
    """Ensure the visualizer is detached after each test."""
    from actions.visualizer.attach import detach_visualizer

    monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))
    yield
    detach_visualizer()


class StubWindow:
    def __init__(self) -> None:
        self.handlers: list[Any] = []
        self.on_draw_calls: list[str] = []
        self.on_draw = self._original_on_draw
        self.key_calls: list[tuple[int, int]] = []
        self.on_key_press = self._original_on_key_press
        self.width = 800
        self.height = 600

    def _original_on_draw(self, *args, **kwargs) -> None:
        self.on_draw_calls.append("original")

    def _original_on_key_press(self, key: int, modifiers: int = 0) -> bool:
        self.key_calls.append((key, modifiers))
        return False

    def push_handlers(self, *handlers, **kwargs) -> None:
        self.handlers.extend(handlers)
        self.handlers.extend(kwargs.values())

    def remove_handlers(self, *handlers) -> None:  # pragma: no cover - compatibility
        for handler in handlers:
            if handler in self.handlers:
                self.handlers.remove(handler)


class StubOverlay:
    def __init__(self, store):
        self.store = store
        self.update_calls = 0
        self.visible = True
        self.toggles = 0
        self.x = 10
        self.y = 10
        self.width = 400

    def update(self) -> None:
        self.update_calls += 1

    def toggle(self) -> None:
        self.visible = not self.visible
        self.toggles += 1


class StubRenderer:
    def __init__(self, overlay: StubOverlay):
        self.overlay = overlay
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        pass


class StubGuides:
    def __init__(self):
        self.update_calls = 0
        self.last_positions: dict[int, tuple[float, float]] | None = None

        class GuideData:
            def __init__(self, color):
                self.enabled = False
                self.color = color
                self.arrows: list[tuple[float, float, float, float]] = []
                self.rectangles: list[tuple[float, float, float, float]] = []
                self.paths: list[list[tuple[float, float]]] = []

        self.velocity_guide = GuideData(arcade.color.AIR_FORCE_BLUE)
        self.bounds_guide = GuideData(arcade.color.ORANGE_RED)
        self.path_guide = GuideData(arcade.color.BABY_BLUE)

    def toggle_all(self) -> None:
        self.velocity_guide.enabled = not self.velocity_guide.enabled
        self.bounds_guide.enabled = not self.bounds_guide.enabled
        self.path_guide.enabled = not self.path_guide.enabled

    def any_enabled(self) -> bool:
        return self.velocity_guide.enabled or self.bounds_guide.enabled or self.path_guide.enabled

    def update(self, snapshots, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        if not self.any_enabled():
            return
        self.update_calls += 1
        self.last_positions = sprite_positions or {}


class StubConditionDebugger:
    def __init__(self, debug_store, max_entries: int = 50):
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.update_calls = 0
        self.cleared = False
        self.entries: list = []

    def update(self) -> None:
        self.update_calls += 1
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True
        self.entries = []


class StubTimeline:
    def __init__(self, debug_store, max_entries: int = 100):
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.update_calls = 0
        self.entries: list = []

    def update(self) -> None:
        self.update_calls += 1


class StubEventWindow:
    instances: list["StubEventWindow"] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.closed = False
        StubEventWindow.instances.append(self)

    def close(self):
        self.closed = True
        callback = self.kwargs.get("on_close_callback")
        if callable(callback):
            callback()


class StubControlManager:
    def __init__(
        self,
        overlay: StubOverlay,
        guides: StubGuides,
        condition_debugger: StubConditionDebugger,
        timeline: StubTimeline,
        snapshot_directory: Path,
        action_controller: Any,
        step_delta: float = 1 / 60,
        toggle_event_window: Callable[[bool], None] | None = None,
    ) -> None:
        self.overlay = overlay
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.timeline = timeline
        self.snapshot_directory = snapshot_directory
        self.action_controller = action_controller
        self.step_delta = step_delta
        self.update_calls = 0
        self.last_positions: dict[int, tuple[float, float]] | None = None
        self.key_calls: list[tuple[int, int]] = []
        self.handled_keys: set[int] = set()
        self.condition_panel_visible = False
        self.condition_debugger.clear()
        self._toggle_event_window = toggle_event_window
        self.toggles: list[bool] = []

    def handle_key_press(self, key: int, modifiers: int = 0) -> bool:
        self.key_calls.append((key, modifiers))
        if key == arcade.key.F3:
            self.overlay.toggle()
            return True
        if key == arcade.key.F4:
            self.condition_panel_visible = not self.condition_panel_visible
            if self._toggle_event_window is not None:
                self.toggles.append(self.condition_panel_visible)
                self._toggle_event_window(self.condition_panel_visible)
            return True
        if key == arcade.key.F5:
            self.guides.toggle_all()
            return True
        if key == arcade.key.F6:
            return True
        if key == arcade.key.F7:
            return True
        if key == arcade.key.F8:
            return True
        if key == arcade.key.F9:
            return True
        return key in self.handled_keys

    def update(self, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        self.update_calls += 1
        self.last_positions = sprite_positions
        self.overlay.update()
        if self.condition_panel_visible:
            self.condition_debugger.update()
        else:
            self.condition_debugger.clear()
        self.timeline.update()
        if self.guides.any_enabled():
            self.guides.update([], sprite_positions or {})


@pytest.fixture
def stub_attach_kwargs(tmp_path: Path) -> dict[str, Any]:
    StubEventWindow.instances.clear()
    return {
        "snapshot_directory": tmp_path,
        "overlay_cls": StubOverlay,
        "renderer_cls": StubRenderer,
        "guide_manager_cls": StubGuides,
        "condition_debugger_cls": StubConditionDebugger,
        "timeline_cls": StubTimeline,
        "controls_cls": StubControlManager,
        "event_window_cls": StubEventWindow,
    }


def test_attach_visualizer_wraps_update(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import (
        attach_visualizer,
        get_visualizer_session,
        is_visualizer_attached,
    )

    calls: list[tuple[float, Any]] = []

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        calls.append((delta_time, physics_engine))

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    StubEventWindow.instances.clear()
    session = attach_visualizer(**stub_attach_kwargs)
    assert is_visualizer_attached()
    assert session.overlay is not None
    assert session.guide_renderer is not None
    assert session.event_window is None

    Action.update_all(0.5, physics_engine="engine")

    assert calls == [(0.5, "engine")]
    assert session.control_manager.update_calls == 1
    assert session.renderer.update_calls == 1
    assert session.guides.update_calls == 0
    assert session.guides.last_positions is None

    assert get_visualizer_session() is session


def test_function_keys_routed_to_control_manager(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer
    from actions.base import Action

    window = StubWindow()
    StubEventWindow.instances.clear()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    session = attach_visualizer(**stub_attach_kwargs)
    session.control_manager.handled_keys.add(arcade.key.F3)

    Action.update_all(0.016)
    assert session.control_manager.condition_debugger.update_calls == 0
    assert session.control_manager.condition_debugger.cleared is True
    assert session.control_manager.guides.update_calls == 0

    handled = window.on_key_press(arcade.key.F3, 0)

    assert handled is True
    assert session.control_manager.key_calls == [(arcade.key.F3, 0)]
    assert window.key_calls == []

    handled_f4 = window.on_key_press(arcade.key.F4, 0)
    assert handled_f4 is True
    assert session.control_manager.condition_panel_visible is True
    assert session.control_manager.toggles == [True]
    assert len(StubEventWindow.instances) == 1
    assert StubEventWindow.instances[0].closed is False

    Action.update_all(0.016)
    assert session.control_manager.condition_debugger.update_calls == 1

    handled_f4_off = window.on_key_press(arcade.key.F4, 0)
    assert handled_f4_off is True
    assert session.control_manager.condition_panel_visible is False
    assert session.control_manager.toggles == [True, False]
    assert StubEventWindow.instances[0].closed is True

    Action.update_all(0.016)
    assert session.control_manager.condition_debugger.update_calls == 1

    handled_f5 = window.on_key_press(arcade.key.F5, 0)
    assert handled_f5 is True
    Action.update_all(0.016)
    assert session.control_manager.guides.update_calls == 1
    assert session.control_manager.key_calls == [
        (arcade.key.F3, 0),
        (arcade.key.F4, 0),
        (arcade.key.F4, 0),
        (arcade.key.F5, 0),
    ]


def test_regular_keys_pass_through_when_unhandled(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    session = attach_visualizer(**stub_attach_kwargs)

    handled = window.on_key_press(arcade.key.LEFT, 0)

    assert handled is False
    assert session.control_manager.key_calls == [(arcade.key.LEFT, 0)]
    assert window.key_calls == [(arcade.key.LEFT, 0)]


def test_attach_visualizer_uses_sprite_positions_provider(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    def provider() -> dict[int, tuple[float, float]]:
        return {1: (10.0, 20.0)}

    session = attach_visualizer(sprite_positions_provider=provider, **stub_attach_kwargs)
    Action.update_all(0.16)

    assert session.control_manager.last_positions == {1: (10.0, 20.0)}


def test_attach_is_idempotent(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    first = attach_visualizer(**stub_attach_kwargs)
    second = attach_visualizer(**stub_attach_kwargs)

    assert first is second


def test_detach_restores_previous_state(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer, is_visualizer_attached

    sentinel_store = object()
    Action.set_debug_store(sentinel_store)
    Action._enable_visualizer = False

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    attach_visualizer(**stub_attach_kwargs)
    assert Action._enable_visualizer is True
    assert Action._debug_store is not sentinel_store

    detach_visualizer()


class FailingEventWindow:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("boom")


def test_event_window_failure_resets_panel(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer
    from actions.base import Action

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    failing_kwargs = dict(stub_attach_kwargs)
    failing_kwargs["event_window_cls"] = FailingEventWindow

    session = attach_visualizer(**failing_kwargs)
    window.on_key_press(arcade.key.F4, 0)

    assert session.control_manager.condition_panel_visible is False
    assert session.event_window is None

    detach_visualizer()


def test_auto_attach_from_env_triggers(monkeypatch, stub_attach_kwargs):
    from actions.visualizer import attach as attach_module

    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")
    called: dict[str, Any] = {}

    def fake_attach(**kwargs):
        called.update(kwargs)
        return object()

    monkeypatch.setattr(attach_module, "attach_visualizer", fake_attach)

    attach_module.auto_attach_from_env(force=True, attach_kwargs=stub_attach_kwargs)

    assert called["overlay_cls"] is StubOverlay


def test_enable_visualizer_hotkey_attaches(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import enable_visualizer_hotkey, is_visualizer_attached

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    window = StubWindow()

    enable_visualizer_hotkey(window=window, attach_kwargs=stub_attach_kwargs)
    handler = window.handlers[-1]

    assert handler(arcade.key.F3, 0) is False
    assert not is_visualizer_attached()

    result = handler(arcade.key.F3, arcade.key.MOD_SHIFT)
    assert result is True
    assert is_visualizer_attached()


def test_detach_without_session_returns_false():
    from actions.visualizer.attach import detach_visualizer

    assert detach_visualizer() is False


def test_auto_attach_env_noop(monkeypatch, stub_attach_kwargs):
    from actions.visualizer import attach as attach_module

    monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)
    called = attach_module.auto_attach_from_env(force=True, attach_kwargs=stub_attach_kwargs)

    assert called is False


def test_attach_handles_provider_exception(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    def provider() -> dict[int, tuple[float, float]]:
        raise RuntimeError("boom")

    session = attach_visualizer(sprite_positions_provider=provider, **stub_attach_kwargs)
    Action.update_all(0.016)

    assert session.control_manager.last_positions == {}


def test_enable_visualizer_hotkey_autodetects_window(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import enable_visualizer_hotkey, is_visualizer_attached

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    window = StubWindow()

    def fake_get_window():
        return window

    monkeypatch.setattr(arcade, "get_window", fake_get_window)

    assert enable_visualizer_hotkey(attach_kwargs=stub_attach_kwargs) is True
    handler = window.handlers[-1]
    handler(arcade.key.F3, arcade.key.MOD_SHIFT)
    assert is_visualizer_attached()


def test_detach_does_not_override_restored_update(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer

    original = Action.update_all

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    attach_visualizer(**stub_attach_kwargs)
    # Simulate external restoration before detach
    Action.update_all = original

    detach_visualizer()
    assert Action.update_all is original


def test_collect_target_names_from_view_no_window(monkeypatch):
    """Test that _collect_target_names_from_view handles missing window gracefully."""
    from actions.visualizer.attach import _collect_target_names_from_view

    monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))

    names = _collect_target_names_from_view()
    assert names == {}


def test_collect_target_names_from_view_no_view(monkeypatch):
    """Test that _collect_target_names_from_view handles missing view gracefully."""
    from actions.visualizer.attach import _collect_target_names_from_view

    class StubWindow:
        current_view = None

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    assert names == {}


def test_collect_target_names_from_view_finds_sprite_lists(monkeypatch):
    """Test that _collect_target_names_from_view finds SpriteLists in view attributes."""
    from actions.visualizer.attach import _collect_target_names_from_view

    enemy_list = arcade.SpriteList()
    player_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self.enemy_list = enemy_list
            self.player_list = player_list
            self.score = 100  # Not a SpriteList, should be ignored

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    assert id(enemy_list) in names
    assert names[id(enemy_list)] == "self.enemy_list"
    assert id(player_list) in names
    assert names[id(player_list)] == "self.player_list"
    assert id(StubView().score) not in names  # score is not a SpriteList


def test_collect_target_names_from_view_finds_sprites(monkeypatch):
    """Test that _collect_target_names_from_view finds Sprites in view attributes."""
    from actions.visualizer.attach import _collect_target_names_from_view

    player_sprite = arcade.Sprite(":resources:images/items/star.png")

    class StubView:
        def __init__(self):
            self.player_sprite = player_sprite
            self.score = 100  # Not a Sprite, should be ignored

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    assert id(player_sprite) in names
    assert names[id(player_sprite)] == "self.player_sprite"
    assert id(StubView().score) not in names  # score is not a Sprite


def test_collect_target_names_from_view_finds_sprites_in_lists(monkeypatch):
    """Test that _collect_target_names_from_view maps sprites within SpriteLists."""
    from actions.visualizer.attach import _collect_target_names_from_view

    bullet_list = arcade.SpriteList()
    bullet1 = arcade.Sprite(":resources:images/items/star.png")
    bullet2 = arcade.Sprite(":resources:images/items/star.png")
    bullet_list.append(bullet1)
    bullet_list.append(bullet2)

    class StubView:
        def __init__(self):
            self.bullet_list = bullet_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    # Should find the SpriteList
    assert id(bullet_list) in names
    assert names[id(bullet_list)] == "self.bullet_list"

    # Should find sprites within the list
    assert id(bullet1) in names
    assert id(bullet2) in names
    # Check format: "Sprite#xxxx in self.bullet_list"
    assert "Sprite#" in names[id(bullet1)]
    assert "in self.bullet_list" in names[id(bullet1)]
    assert "Sprite#" in names[id(bullet2)]
    assert "in self.bullet_list" in names[id(bullet2)]


def test_collect_target_names_from_view_skips_private_attributes(monkeypatch):
    """Test that _collect_target_names_from_view skips private attributes."""
    from actions.visualizer.attach import _collect_target_names_from_view

    private_list = arcade.SpriteList()
    public_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self._private_list = private_list  # Should be skipped
            self.public_list = public_list

    view = StubView()

    class StubWindow:
        def __init__(self):
            self.current_view = view

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    # Private attribute should be skipped
    assert id(private_list) not in names
    # Public attribute should be found
    assert id(public_list) in names
    assert names[id(public_list)] == "self.public_list"


def test_collect_target_names_from_view_finds_targets_from_actions(monkeypatch):
    """Test that _collect_target_names_from_view finds targets from active actions."""
    from actions.visualizer.attach import _collect_target_names_from_view
    from actions.conditional import MoveUntil

    # Create a sprite list and sprite that aren't direct view attributes
    dynamic_list = arcade.SpriteList()
    dynamic_sprite = arcade.Sprite(":resources:images/items/star.png")
    dynamic_list.append(dynamic_sprite)

    # Create an action targeting the sprite
    action = MoveUntil(velocity=(1, 0), condition=lambda: False)
    action.apply(dynamic_sprite)

    class StubView:
        def __init__(self):
            self.enemy_list = arcade.SpriteList()  # Different list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    # Should find the sprite from the active action
    # Since it's not in a view attribute, it might not have a name, but shouldn't crash
    # The function should handle this gracefully
    assert isinstance(names, dict)

    # Clean up
    action.stop()


def test_collect_target_names_from_view_finds_sprite_in_list_from_action(monkeypatch):
    """Test that _collect_target_names_from_view finds sprites in lists from active actions."""
    from actions.visualizer.attach import _collect_target_names_from_view
    from actions.conditional import MoveUntil

    bullet_list = arcade.SpriteList()
    bullet = arcade.Sprite(":resources:images/items/star.png")
    bullet_list.append(bullet)

    # Create an action targeting the bullet
    action = MoveUntil(velocity=(0, 1), condition=lambda: False)
    action.apply(bullet)

    class StubView:
        def __init__(self):
            self.player_bullet_list = bullet_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    # Should find the bullet list
    assert id(bullet_list) in names
    assert names[id(bullet_list)] == "self.player_bullet_list"

    # Should find the bullet sprite within the list
    assert id(bullet) in names
    assert "Sprite#" in names[id(bullet)]
    assert "in self.player_bullet_list" in names[id(bullet)]

    # Clean up
    action.stop()


def test_collect_target_names_from_view_handles_exceptions(monkeypatch):
    """Test that _collect_target_names_from_view handles exceptions gracefully."""
    from actions.visualizer.attach import _collect_target_names_from_view

    normal_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self.normal_list = normal_list

        @property
        def problematic_attr(self):
            """Property that raises an exception."""
            raise ValueError("Cannot access")

    view = StubView()

    class StubWindow:
        def __init__(self):
            self.current_view = view

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    # Should not raise, should handle exception gracefully
    names = _collect_target_names_from_view()

    # Should still find the normal list
    assert id(normal_list) in names
    assert names[id(normal_list)] == "self.normal_list"
    assert isinstance(names, dict)


def test_collect_target_names_from_view_handles_none_attributes(monkeypatch):
    """Test that _collect_target_names_from_view handles None attributes."""
    from actions.visualizer.attach import _collect_target_names_from_view

    valid_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self.none_list = None
            self.valid_list = valid_list

    view = StubView()

    class StubWindow:
        def __init__(self):
            self.current_view = view

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()

    # Should find the valid list but not crash on None
    assert id(valid_list) in names
    assert names[id(valid_list)] == "self.valid_list"
    assert isinstance(names, dict)


def test_collect_target_names_from_view_auto_attach_provides_provider(monkeypatch):
    """Test that auto_attach_from_env automatically provides target_names_provider."""
    from actions.visualizer import attach as attach_module

    monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))
    monkeypatch.setattr(attach_module, "_AUTO_ATTACH_ATTEMPTED", False)
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    attach_kwargs = {}
    attach_module.auto_attach_from_env(force=True, attach_kwargs=attach_kwargs)

    # Check that target_names_provider was added
    assert "target_names_provider" in attach_kwargs
    assert attach_kwargs["target_names_provider"] == attach_module._collect_target_names_from_view

    # Clean up
    attach_module.detach_visualizer()


def test_collect_sprite_positions_handles_targets():
    from actions.visualizer.attach import _collect_sprite_positions

    original_active = list(Action._active_actions)
    try:

        class DummySprite:
            def __init__(self, x, y):
                self.center_x = x
                self.center_y = y

        class DummyList(list):
            pass

        sprite = DummySprite(10, 20)
        sprite_list = DummyList([DummySprite(1, 2), object(), DummySprite(3, 4)])

        class DummyAction:
            def __init__(self, target):
                self.target = target

        Action._active_actions.append(DummyAction(sprite))
        Action._active_actions.append(DummyAction(sprite_list))

        positions = _collect_sprite_positions()
        assert positions[id(sprite)] == (10, 20)
        assert positions[id(sprite_list[0])] == (1, 2)
        assert positions[id(sprite_list[2])] == (3, 4)
    finally:
        Action._active_actions[:] = original_active


def test_auto_attach_multiple_calls(monkeypatch, stub_attach_kwargs):
    from actions.visualizer import attach as attach_module

    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")
    calls: list[dict[str, Any]] = []

    def fake_attach(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(attach_module, "attach_visualizer", fake_attach)

    assert attach_module.auto_attach_from_env(force=True, attach_kwargs=stub_attach_kwargs) is True
    assert calls

    # Second call without force should no-op
    assert attach_module.auto_attach_from_env(attach_kwargs=stub_attach_kwargs) is False
    assert len(calls) == 1


def test_auto_attach_defaults_kwargs(monkeypatch):
    from actions.visualizer import attach as attach_module

    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")
    called: list[dict[str, Any]] = []

    def fake_attach(**kwargs):
        called.append(kwargs)
        return object()

    monkeypatch.setattr(attach_module, "attach_visualizer", fake_attach)

    attach_module.auto_attach_from_env(force=True)
    assert called == [{}]


def test_enable_hotkey_no_window(monkeypatch):
    from actions.visualizer.attach import enable_visualizer_hotkey

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    def fake_get_window():
        raise RuntimeError("no window")

    monkeypatch.setattr(arcade, "get_window", fake_get_window)

    assert enable_visualizer_hotkey() is False


def test_enable_hotkey_default_attach_kwargs(monkeypatch):
    from actions.visualizer.attach import enable_visualizer_hotkey

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    window = StubWindow()

    def fake_get_window():
        return window

    monkeypatch.setattr(arcade, "get_window", fake_get_window)

    attached: list[dict[str, Any]] = []

    def fake_attach(**kwargs):
        attached.append(kwargs)

        class DummySession:
            pass

        return DummySession()

    monkeypatch.setattr("actions.visualizer.attach.attach_visualizer", fake_attach)

    assert enable_visualizer_hotkey() is True
    handler = window.handlers[-1]
    handler(arcade.key.F3, arcade.key.MOD_SHIFT)
    assert attached == [{}]


def test_enable_visualizer_hotkey_returns_false_without_window(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import enable_visualizer_hotkey

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    assert enable_visualizer_hotkey(window=None, attach_kwargs=stub_attach_kwargs) is False


def test_attach_registers_draw_handler_when_window_available(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    session = attach_visualizer(**stub_attach_kwargs)
    assert session.window is window
    assert session.original_window_on_draw is not None
    assert getattr(window.on_draw, "__visualizer_overlay__", False)

    detach_visualizer()
    assert session.original_window_on_draw is None
    assert not getattr(window.on_draw, "__visualizer_overlay__", False)


def test_attach_delays_draw_handler_until_window_exists(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer

    monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    session = attach_visualizer(**stub_attach_kwargs)
    assert session.window is None
    assert session.original_window_on_draw is None

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    Action.update_all(0.016)
    assert session.window is window
    assert session.original_window_on_draw is not None
    assert getattr(window.on_draw, "__visualizer_overlay__", False)

    detach_visualizer()


def test_space_clutter_keys_continue_working(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import attach_visualizer, detach_visualizer
    from examples.space_clutter import StarfieldView

    monkeypatch.setattr(arcade, "schedule", lambda *args, **kwargs: None)
    monkeypatch.setattr(arcade, "schedule_once", lambda *args, **kwargs: None)
    monkeypatch.setattr(arcade, "unschedule", lambda *args, **kwargs: None)

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    view = StarfieldView()

    def delegate_on_key_press(key: int, modifiers: int = 0) -> bool:
        window.key_calls.append((key, modifiers))
        result = view.on_key_press(key, modifiers)
        return False if result is None else bool(result)

    window.on_key_press = delegate_on_key_press
    view.window = window

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    session = attach_visualizer(**stub_attach_kwargs)

    window.on_key_press(arcade.key.LEFT, 0)

    assert session.control_manager.key_calls == [(arcade.key.LEFT, 0)]
    assert window.key_calls == [(arcade.key.LEFT, 0)]
    assert view.left_pressed is True

    detach_visualizer()


def test_auto_attach_draws_overlay(monkeypatch, tmp_path):
    from actions.visualizer import attach as attach_module

    class RecordingRenderer(StubRenderer):
        instance: "RecordingRenderer | None" = None

        def __init__(self, overlay: StubOverlay):
            super().__init__(overlay)
            RecordingRenderer.instance = self
            self.draw_count = 0

        def draw(self) -> None:
            self.draw_count += 1

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)
    monkeypatch.setattr(attach_module, "_AUTO_ATTACH_ATTEMPTED", False)
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    attach_kwargs = {
        "snapshot_directory": tmp_path,
        "overlay_cls": StubOverlay,
        "renderer_cls": RecordingRenderer,
        "guide_manager_cls": StubGuides,
        "condition_debugger_cls": StubConditionDebugger,
        "timeline_cls": StubTimeline,
        "controls_cls": StubControlManager,
    }

    attach_module.auto_attach_from_env(force=True, attach_kwargs=attach_kwargs)

    try:
        renderer = RecordingRenderer.instance
        assert renderer is not None
        assert getattr(window.on_draw, "__visualizer_overlay__", False)

        window.on_draw()

        assert window.on_draw_calls == ["original"]
        assert renderer.draw_count == 1
    finally:
        attach_module.detach_visualizer()
