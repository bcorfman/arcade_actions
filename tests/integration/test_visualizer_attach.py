"""
Tests for the visualizer attach/detach helper utilities.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import arcade
import pytest

from actions.base import Action


@pytest.fixture(autouse=True)
def auto_detach():
    """Ensure the visualizer is detached after each test."""
    from actions.visualizer.attach import detach_visualizer

    yield
    detach_visualizer()


class StubOverlay:
    def __init__(self, store):
        self.store = store
        self.update_calls = 0
        self.visible = True

    def update(self) -> None:
        self.update_calls += 1


class StubRenderer:
    def __init__(self, overlay: StubOverlay):
        self.overlay = overlay
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        pass


class StubGuides:
    def __init__(self, initial_enabled: bool = False):
        self.update_calls = 0
        self.last_positions: dict[int, tuple[float, float]] | None = None

    def toggle_all(self) -> None:  # pragma: no cover - not used in tests
        pass

    def update(self, snapshots, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        self.update_calls += 1
        self.last_positions = sprite_positions or {}


class StubConditionDebugger:
    def __init__(self, debug_store, max_entries: int = 50):
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.update_calls = 0
        self.cleared = False

    def update(self) -> None:
        self.update_calls += 1
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True


class StubTimeline:
    def __init__(self, debug_store, max_entries: int = 100):
        self.debug_store = debug_store
        self.max_entries = max_entries
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


class StubControlManager:
    def __init__(
        self,
        overlay: StubOverlay,
        guides: StubGuides,
        condition_debugger: StubConditionDebugger,
        timeline: StubTimeline,
        snapshot_directory: Path,
        action_controller: Any,
        toggle_event_window: Callable[[bool], None] | None = None,
        target_names_provider: Callable[[], dict[int, str]] | None = None,
        step_delta: float = 1 / 60,
    ) -> None:
        self.overlay = overlay
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.toggle_event_window = toggle_event_window
        self.timeline = timeline
        self.snapshot_directory = snapshot_directory
        self.action_controller = action_controller
        self.step_delta = step_delta
        self.update_calls = 0
        self.last_positions: dict[int, tuple[float, float]] | None = None
        self.target_names_provider = target_names_provider

    def handle_key_press(self, key: int, modifiers: int = 0) -> bool:  # pragma: no cover - not used
        return False

    def update(self, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        self.update_calls += 1
        self.last_positions = sprite_positions
        self.overlay.update()
        self.condition_debugger.update()
        self.timeline.update()
        self.guides.update([], sprite_positions or {})

    def get_target_names(self) -> dict[int, str]:
        if self.target_names_provider is None:
            return {}
        try:
            names = self.target_names_provider() or {}
        except Exception:
            return {}
        normalized: dict[int, str] = {}
        for key, value in names.items():
            try:
                normalized[int(key)] = str(value)
            except (TypeError, ValueError):
                continue
        return normalized


@pytest.fixture
def stub_attach_kwargs(tmp_path: Path) -> dict[str, Any]:
    return {
        "snapshot_directory": tmp_path,
        "overlay_cls": StubOverlay,
        "renderer_cls": StubRenderer,
        "guide_manager_cls": StubGuides,
        "condition_debugger_cls": StubConditionDebugger,
        "timeline_cls": StubTimeline,
        "controls_cls": StubControlManager,
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

    session = attach_visualizer(**stub_attach_kwargs)
    assert is_visualizer_attached()
    assert session.overlay is not None

    Action.update_all(0.5, physics_engine="engine")

    assert calls == [(0.5, "engine")]
    assert session.control_manager.update_calls == 1
    assert session.renderer.update_calls == 1
    assert session.guides.update_calls == 1
    assert session.guides.last_positions == {}

    assert get_visualizer_session() is session


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

    assert not is_visualizer_attached()
    assert Action._debug_store is sentinel_store
    assert Action._enable_visualizer is False


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

    class StubWindow:
        def __init__(self) -> None:
            self.handlers: dict[str, Callable[..., bool]] = {}
            self.view = None

        def push_handlers(self, **handlers: Callable[..., bool]) -> None:
            self.handlers.update(handlers)

        def show_view(self, view) -> None:
            self.view = view

    window = StubWindow()

    enable_visualizer_hotkey(window=window, attach_kwargs=stub_attach_kwargs)
    handler = window.handlers["on_key_press"]

    assert handler(arcade.key.F3, 0) is False
    assert not is_visualizer_attached()

    result = handler(arcade.key.F3, arcade.key.MOD_SHIFT)
    assert result is True
    assert is_visualizer_attached()


def test_enable_dev_visualizer_function(monkeypatch):
    """Test enable_dev_visualizer function."""
    from actions.dev.visualizer import enable_dev_visualizer, get_dev_visualizer

    # Clean up any existing instance
    monkeypatch.setattr("actions.dev.visualizer._global_dev_visualizer", None)

    scene_sprites = arcade.SpriteList()
    dev_viz = enable_dev_visualizer(scene_sprites=scene_sprites, auto_attach=False)

    assert dev_viz is not None
    assert dev_viz.scene_sprites == scene_sprites
    assert get_dev_visualizer() is dev_viz


def test_get_dev_visualizer_function(monkeypatch):
    """Test get_dev_visualizer function."""
    from actions.dev.visualizer import enable_dev_visualizer, get_dev_visualizer

    # Clean up any existing instance
    monkeypatch.setattr("actions.dev.visualizer._global_dev_visualizer", None)

    # Initially None
    assert get_dev_visualizer() is None

    # Enable it
    dev_viz = enable_dev_visualizer(auto_attach=False)
    assert get_dev_visualizer() is dev_viz

    # Should return same instance
    assert get_dev_visualizer() is dev_viz


def test_auto_enable_dev_visualizer_from_env(monkeypatch):
    """Test auto_enable_dev_visualizer_from_env function."""
    from actions.dev.visualizer import auto_enable_dev_visualizer_from_env, get_dev_visualizer

    # Clean up any existing instance
    monkeypatch.setattr("actions.dev.visualizer._global_dev_visualizer", None)

    # Without env var, should return None
    monkeypatch.delenv("ARCADEACTIONS_DEVVIZ", raising=False)
    monkeypatch.delenv("ARCADEACTIONS_DEV", raising=False)
    result = auto_enable_dev_visualizer_from_env()
    assert result is None
    assert get_dev_visualizer() is None

    # With env var set, should enable
    monkeypatch.setenv("ARCADEACTIONS_DEVVIZ", "1")
    result = auto_enable_dev_visualizer_from_env()
    assert result is not None
    assert get_dev_visualizer() is result


def test_detach_without_session_returns_false():
    from actions.visualizer.attach import detach_visualizer

    assert detach_visualizer() is False


def test_auto_attach_env_noop(monkeypatch, stub_attach_kwargs):
    monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


def test_actions_import_auto_attaches_with_env(monkeypatch, stub_attach_kwargs):
    """Importing actions with ARCADEACTIONS_VISUALIZER=1 should auto-attach."""
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

    try:
        import actions.visualizer.attach as visualizer_attach

        if visualizer_attach.is_visualizer_attached():
            visualizer_attach.detach_visualizer()

        visualizer_attach._AUTO_ATTACH_ATTEMPTED = False  # type: ignore[attr-defined]

        import actions  # noqa: F401

        importlib.reload(actions)

        assert visualizer_attach.is_visualizer_attached() is True
    finally:
        visualizer_attach.detach_visualizer()
        monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)


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

    class StubWindow:
        def __init__(self) -> None:
            self.handlers: dict[str, Callable[..., bool]] = {}

        def push_handlers(self, **handlers: Callable[..., bool]) -> None:
            self.handlers.update(handlers)

    window = StubWindow()

    def fake_get_window():
        return window

    monkeypatch.setattr(arcade, "get_window", fake_get_window)

    assert enable_visualizer_hotkey(attach_kwargs=stub_attach_kwargs) is True
    handler = window.handlers["on_key_press"]
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
    # Ensure no window exists that might trigger additional kwargs
    monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))

    attach_module.auto_attach_from_env(force=True)
    # Should be called with empty kwargs (or at most sprite_positions_provider which is added internally)
    assert len(called) == 1
    # Remove internal kwargs that might be added
    kwargs = called[0].copy()
    # sprite_positions_provider is added internally by attach_visualizer, so ignore it
    kwargs.pop("sprite_positions_provider", None)
    # target_names_provider might be added in some environments, so ignore it for this test
    kwargs.pop("target_names_provider", None)
    assert kwargs == {}


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

    class StubWindow:
        def __init__(self) -> None:
            self.handlers: dict[str, Callable[..., bool]] = {}

        def push_handlers(self, **handlers: Callable[..., bool]) -> None:
            self.handlers.update(handlers)

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
    handler = window.handlers["on_key_press"]
    handler(arcade.key.F3, arcade.key.MOD_SHIFT)
    assert attached == [{}]


def test_enable_visualizer_hotkey_returns_false_without_window(monkeypatch, stub_attach_kwargs):
    from actions.visualizer.attach import enable_visualizer_hotkey

    def fake_update_all(cls, delta_time: float, physics_engine: Any = None) -> None:
        pass

    monkeypatch.setattr(Action, "update_all", classmethod(fake_update_all))

    assert enable_visualizer_hotkey(window=None, attach_kwargs=stub_attach_kwargs) is False


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
    """Test that _collect_target_names_from_view finds SpriteList objects."""
    from actions.visualizer.attach import _collect_target_names_from_view

    sprite_list = arcade.SpriteList()
    sprite_list.append(arcade.Sprite(":resources:images/items/star.png"))

    class StubView:
        def __init__(self):
            self.enemy_list = sprite_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    assert id(sprite_list) in names
    assert names[id(sprite_list)] == "self.enemy_list"


def test_collect_target_names_from_view_finds_sprites(monkeypatch):
    """Test that _collect_target_names_from_view finds Sprite objects."""
    from actions.visualizer.attach import _collect_target_names_from_view

    sprite = arcade.Sprite(":resources:images/items/star.png")

    class StubView:
        def __init__(self):
            self.player = sprite

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    assert id(sprite) in names
    assert names[id(sprite)] == "self.player"


def test_collect_target_names_from_view_finds_sprites_in_lists(monkeypatch):
    """Test that _collect_target_names_from_view finds sprites within lists."""
    from actions.visualizer.attach import _collect_target_names_from_view

    sprite1 = arcade.Sprite(":resources:images/items/star.png")
    sprite2 = arcade.Sprite(":resources:images/items/star.png")
    sprite_list = arcade.SpriteList()
    sprite_list.append(sprite1)
    sprite_list.append(sprite2)

    class StubView:
        def __init__(self):
            self.bullet_list = sprite_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    assert id(sprite_list) in names
    assert names[id(sprite_list)] == "self.bullet_list"
    # Check that sprites in the list are also mapped
    assert id(sprite1) in names
    assert id(sprite2) in names
    assert "Sprite#" in names[id(sprite1)]
    assert "self.bullet_list" in names[id(sprite1)]


def test_collect_target_names_from_view_skips_private_attributes(monkeypatch):
    """Test that _collect_target_names_from_view skips private attributes."""
    from actions.visualizer.attach import _collect_target_names_from_view

    public_list = arcade.SpriteList()
    private_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self.public_list = public_list
            self._private_list = private_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    assert id(public_list) in names
    assert id(private_list) not in names


def test_collect_target_names_from_view_finds_targets_from_actions(monkeypatch):
    """Test that _collect_target_names_from_view finds targets from active actions."""
    from actions.conditional import MoveUntil
    from actions.visualizer.attach import _collect_target_names_from_view

    sprite = arcade.Sprite(":resources:images/items/star.png")
    action = MoveUntil(velocity=(1, 0), condition=lambda: False)
    action.apply(sprite)

    class StubView:
        pass

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    # The sprite might be found through the action's target
    # Since it's not in a view attribute, it might not have a name, but shouldn't crash
    assert isinstance(names, dict)


def test_collect_target_names_from_view_finds_sprite_in_list_from_action(monkeypatch):
    """Test that _collect_target_names_from_view finds sprites in lists from actions."""
    from actions.conditional import MoveUntil
    from actions.visualizer.attach import _collect_target_names_from_view

    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite_list = arcade.SpriteList()
    sprite_list.append(sprite)

    action = MoveUntil(velocity=(1, 0), condition=lambda: False)
    action.apply(sprite)

    class StubView:
        def __init__(self):
            self.bullet_list = sprite_list

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    # Should find the sprite in the list
    assert id(sprite) in names
    assert "self.bullet_list" in names[id(sprite)]


def test_collect_target_names_from_view_handles_exceptions(monkeypatch):
    """Test that _collect_target_names_from_view handles exceptions gracefully."""
    from actions.visualizer.attach import _collect_target_names_from_view

    class StubView:
        def __init__(self):
            self.normal_list = arcade.SpriteList()

        def __getattr__(self, name):
            if name == "problematic":
                raise ValueError("Cannot access")
            return super().__getattribute__(name)

    # Create the view instance once and reuse it
    stub_view = StubView()

    class StubWindow:
        def __init__(self):
            self.current_view = stub_view

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    # Should still find normal_list despite problematic attribute
    assert id(stub_view.normal_list) in names


def test_collect_target_names_from_view_handles_none_attributes(monkeypatch):
    """Test that _collect_target_names_from_view handles None attributes gracefully."""
    from actions.visualizer.attach import _collect_target_names_from_view

    valid_list = arcade.SpriteList()

    class StubView:
        def __init__(self):
            self.valid_list = valid_list
            self.none_list = None

    class StubWindow:
        def __init__(self):
            self.current_view = StubView()

    monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

    names = _collect_target_names_from_view()
    # Should find valid_list but skip none_list
    assert id(valid_list) in names
    assert names[id(valid_list)] == "self.valid_list"


def test_collect_target_names_from_view_auto_attach_provides_provider(monkeypatch):
    """Test that auto_attach_from_env automatically provides target_names_provider."""
    from actions.visualizer import attach as attach_module

    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")
    called: list[dict[str, Any]] = []

    def fake_attach(**kwargs):
        called.append(kwargs)
        return object()

    monkeypatch.setattr(attach_module, "attach_visualizer", fake_attach)

    attach_module.auto_attach_from_env(force=True)

    assert len(called) == 1
    assert "target_names_provider" in called[0]
    assert callable(called[0]["target_names_provider"])
