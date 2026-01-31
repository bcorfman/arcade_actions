"""Unit tests for attach.py helper functions."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions.base import Action
from arcadeactions.visualizer.attach import (
    VisualizerSession,
    _collect_sprite_positions,
    _collect_sprite_sizes_and_ids,
    _collect_target_names_from_view,
    _open_event_window,
    attach_visualizer,
    detach_visualizer,
    get_visualizer_session,
    is_visualizer_attached,
)


@pytest.fixture(autouse=True)
def reset_session():
    """Reset visualizer session before each test."""
    yield
    detach_visualizer()
    # Clear module-level state
    import arcadeactions.visualizer.attach as attach_module

    attach_module._VISUALIZER_SESSION = None


class TestCollectSpritePositions:
    def test_empty_actions(self):
        original_actions = list(Action._active_actions)
        try:
            Action._active_actions.clear()
            positions = _collect_sprite_positions()
            assert positions == {}
        finally:
            Action._active_actions[:] = original_actions

    def test_single_sprite(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, x, y):
                    self.center_x = x
                    self.center_y = y

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            sprite = DummySprite(10, 20)
            Action._active_actions.append(DummyAction(sprite))
            positions = _collect_sprite_positions()
            assert positions[id(sprite)] == (10, 20)
        finally:
            Action._active_actions[:] = original_actions

    def test_sprite_list(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, x, y):
                    self.center_x = x
                    self.center_y = y

            class DummyList(list):
                pass

            sprite1 = DummySprite(1, 2)
            sprite2 = DummySprite(3, 4)
            sprite_list = DummyList([sprite1, sprite2])

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            Action._active_actions.append(DummyAction(sprite_list))
            positions = _collect_sprite_positions()
            assert positions[id(sprite1)] == (1, 2)
            assert positions[id(sprite2)] == (3, 4)
            # List itself should have average position
            assert id(sprite_list) in positions
        finally:
            Action._active_actions[:] = original_actions

    def test_sprite_list_skips_missing_position(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, x, y):
                    self.center_x = x
                    self.center_y = y

            class DummySpriteMissing:
                pass

            class DummyList(list):
                pass

            sprite_ok = DummySprite(5, 6)
            sprite_missing = DummySpriteMissing()
            sprite_list = DummyList([sprite_missing, sprite_ok])

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            Action._active_actions.append(DummyAction(sprite_list))
            positions = _collect_sprite_positions()
            assert id(sprite_ok) in positions
            assert id(sprite_missing) not in positions
            assert positions[id(sprite_list)] == (5, 6)
        finally:
            Action._active_actions[:] = original_actions

    def test_non_iterable_target_missing_position(self):
        original_actions = list(Action._active_actions)
        try:

            class DummyTarget:
                pass

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            Action._active_actions.append(DummyAction(DummyTarget()))
            positions = _collect_sprite_positions()
            assert isinstance(positions, dict)
            assert positions == {}
        finally:
            Action._active_actions[:] = original_actions

    def test_caching(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, x, y):
                    self.center_x = x
                    self.center_y = y

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            sprite = DummySprite(10, 20)
            Action._active_actions.append(DummyAction(sprite))

            # First call
            positions1 = _collect_sprite_positions()
            # Update position
            sprite.center_x = 30
            sprite.center_y = 40
            # Second call should use cache and update positions
            positions2 = _collect_sprite_positions()
            assert positions2[id(sprite)] == (30, 40)
        finally:
            Action._active_actions[:] = original_actions

    def test_action_without_target(self):
        original_actions = list(Action._active_actions)
        try:

            class DummyAction:
                pass

            Action._active_actions.append(DummyAction())
            positions = _collect_sprite_positions()
            # Should skip actions without targets
            assert isinstance(positions, dict)
        finally:
            Action._active_actions[:] = original_actions


class TestWindowHandlerWrapping:
    def test_attach_wraps_and_detach_restores_window_handlers(self, monkeypatch, tmp_path):
        class StubOverlay:
            def __init__(self, debug_store):
                self.debug_store = debug_store
                self.visible = True
                self.position = "upper_left"
                self.highlighted_target_id = None

            def update(self) -> None:
                return None

        class StubRenderer:
            def __init__(self, overlay):
                self.overlay = overlay

            def update(self) -> None:
                return None

            def draw(self) -> None:
                return None

        class StubGuides:
            def __init__(self, initial_enabled: bool = False):
                return None

            def update(self, *args, **kwargs) -> None:
                return None

            def any_enabled(self) -> bool:
                return False

        class StubConditionDebugger:
            def __init__(self, debug_store, max_entries: int = 50):
                self.debug_store = debug_store

            def update(self) -> None:
                return None

            def clear(self) -> None:
                return None

        class StubTimeline:
            def __init__(self, debug_store, max_entries: int = 100):
                self.debug_store = debug_store

            def update(self) -> None:
                return None

        class StubControlManager:
            def __init__(
                self, overlay, guides, condition_debugger, timeline, snapshot_directory, action_controller, **_
            ):
                self.overlay = overlay
                self.guides = guides
                self.condition_debugger = condition_debugger
                self.timeline = timeline

            def update(self, sprite_positions=None) -> None:
                return None

            def handle_key_press(self, symbol: int, modifiers: int) -> bool:
                return False

            def get_target_names(self) -> dict[int, str]:
                return {}

        class StubGuideRenderer:
            def __init__(self, guides):
                self.guides = guides

            def update(self) -> None:
                return None

            def draw(self) -> None:
                return None

        class StubWindow:
            def __init__(self) -> None:
                self.on_draw = lambda: "draw"
                self.on_key_press = lambda symbol, modifiers: False
                self.on_close = lambda: "close"

            def switch_to(self) -> None:
                return None

        window = StubWindow()
        original_on_draw = window.on_draw
        original_on_key_press = window.on_key_press
        original_on_close = window.on_close

        monkeypatch.setattr(arcade, "get_window", lambda: window)
        monkeypatch.setattr(arcade.window_commands, "get_window", lambda: window)
        monkeypatch.setattr(arcade.window_commands, "set_window", lambda value: None)

        session = attach_visualizer(
            snapshot_directory=tmp_path,
            overlay_cls=StubOverlay,
            renderer_cls=StubRenderer,
            guide_manager_cls=StubGuides,
            condition_debugger_cls=StubConditionDebugger,
            timeline_cls=StubTimeline,
            controls_cls=StubControlManager,
            guide_renderer_cls=StubGuideRenderer,
            event_window_cls=lambda *args, **kwargs: None,
        )

        assert session is not None
        assert getattr(window.on_draw, "__visualizer_overlay__", False)
        assert getattr(window.on_key_press, "__visualizer_key__", False)
        assert getattr(window.on_close, "__visualizer_close__", False)

        detach_visualizer()

        assert window.on_draw is original_on_draw
        assert window.on_key_press is original_on_key_press
        assert window.on_close is original_on_close


class TestCollectSpriteSizesAndIds:
    def test_empty_cache(self):
        sizes, ids = _collect_sprite_sizes_and_ids()
        assert sizes == {}
        assert ids == {}

    def test_single_sprite(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, x, y):
                    self.center_x = x
                    self.center_y = y
                    self.width = 50
                    self.height = 50

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            sprite = DummySprite(10, 20)
            Action._active_actions.append(DummyAction(sprite))
            # Need to populate cache first
            _collect_sprite_positions()
            sizes, ids = _collect_sprite_sizes_and_ids()
            assert sizes[id(sprite)] == (50, 50)
        finally:
            Action._active_actions[:] = original_actions

    def test_sprite_list(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, w, h):
                    self.width = w
                    self.height = h

            class DummyList(list):
                pass

            sprite1 = DummySprite(20, 20)
            sprite2 = DummySprite(30, 30)
            sprite_list = DummyList([sprite1, sprite2])

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            Action._active_actions.append(DummyAction(sprite_list))
            _collect_sprite_positions()
            sizes, ids = _collect_sprite_sizes_and_ids()
            assert sizes[id(sprite1)] == (20, 20)
            assert sizes[id(sprite2)] == (30, 30)
            assert ids[id(sprite_list)] == [id(sprite1), id(sprite2)]
        finally:
            Action._active_actions[:] = original_actions

    def test_sprite_list_skips_missing_sizes(self):
        original_actions = list(Action._active_actions)
        try:

            class DummySprite:
                def __init__(self, w, h):
                    self.width = w
                    self.height = h

            class DummySpriteMissing:
                pass

            class DummyList(list):
                pass

            sprite_ok = DummySprite(10, 20)
            sprite_missing = DummySpriteMissing()
            sprite_list = DummyList([sprite_ok, sprite_missing])

            class DummyAction:
                def __init__(self, target):
                    self.target = target

            Action._active_actions.append(DummyAction(sprite_list))
            _collect_sprite_positions()
            sizes, ids = _collect_sprite_sizes_and_ids()
            assert sizes[id(sprite_ok)] == (10, 20)
            assert id(sprite_missing) not in sizes
            assert ids[id(sprite_list)] == [id(sprite_ok)]
        finally:
            Action._active_actions[:] = original_actions


class TestCollectTargetNamesFromView:
    def test_no_window(self, monkeypatch):
        monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))
        names = _collect_target_names_from_view()
        assert names == {}

    def test_no_view(self, monkeypatch):
        class StubWindow:
            current_view = None

        monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())
        names = _collect_target_names_from_view()
        assert names == {}

    def test_finds_sprite_list(self, monkeypatch):
        sprite_list = arcade.SpriteList()
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite_list.append(sprite)

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

    def test_finds_sprite(self, monkeypatch):
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

    def test_skips_private_attributes(self, monkeypatch):
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

    def test_handles_exceptions(self, monkeypatch):
        class StubView:
            def __getattr__(self, name):
                if name == "problematic":
                    raise ValueError("Cannot access")
                return super().__getattribute__(name)

            def __init__(self):
                self.normal_list = arcade.SpriteList()

        stub_view = StubView()

        class StubWindow:
            def __init__(self):
                self.current_view = stub_view

        monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())
        names = _collect_target_names_from_view()
        # Should still find normal_list despite problematic attribute
        assert id(stub_view.normal_list) in names

    def test_finds_targets_from_actions(self, monkeypatch):
        sprite = arcade.Sprite(":resources:images/items/star.png")
        from arcadeactions.conditional import MoveUntil

        action = MoveUntil(velocity=(1, 0), condition=lambda: False)
        action.apply(sprite)

        class StubView:
            pass

        class StubWindow:
            def __init__(self):
                self.current_view = StubView()

        monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())
        names = _collect_target_names_from_view()
        # Should find sprite from action
        assert isinstance(names, dict)


class TestVisualizerSession:
    def test_keyboard_handler_property(self):
        from pathlib import Path

        from arcadeactions.visualizer.condition_panel import ConditionDebugger
        from arcadeactions.visualizer.controls import DebugControlManager
        from arcadeactions.visualizer.guides import GuideManager
        from arcadeactions.visualizer.instrumentation import DebugDataStore
        from arcadeactions.visualizer.overlay import InspectorOverlay
        from arcadeactions.visualizer.timeline import TimelineStrip

        debug_store = DebugDataStore()
        overlay = InspectorOverlay(debug_store)
        guides = GuideManager()
        condition_debugger = ConditionDebugger(debug_store)
        timeline = TimelineStrip(debug_store)

        class StubController:
            def pause_all(self):
                pass

            def resume_all(self):
                pass

            def step_all(self, delta_time):
                pass

        control_manager = DebugControlManager(
            overlay=overlay,
            guides=guides,
            condition_debugger=condition_debugger,
            timeline=timeline,
            snapshot_directory=Path("snapshots"),
            action_controller=StubController(),
            toggle_event_window=lambda x: None,
        )

        session = VisualizerSession(
            debug_store=debug_store,
            overlay=overlay,
            renderer=None,
            guides=guides,
            condition_debugger=condition_debugger,
            timeline=timeline,
            control_manager=control_manager,
            guide_renderer=None,
            event_window=None,
            snapshot_directory=Path("snapshots"),
            sprite_positions_provider=None,
            target_names_provider=None,
            wrapped_update_all=lambda *args: None,
            previous_update_all=lambda *args: None,
            previous_debug_store=None,
            previous_enable_flag=False,
        )
        assert session.keyboard_handler is not None
        assert callable(session.keyboard_handler)

    def test_keyboard_handler_none(self):
        session = VisualizerSession(
            debug_store=None,
            overlay=None,
            renderer=None,
            guides=None,
            condition_debugger=None,
            timeline=None,
            control_manager=None,
            guide_renderer=None,
            event_window=None,
            snapshot_directory=None,
            sprite_positions_provider=None,
            target_names_provider=None,
            wrapped_update_all=lambda *args: None,
            previous_update_all=lambda *args: None,
            previous_debug_store=None,
            previous_enable_flag=False,
        )
        assert session.keyboard_handler is None

    def test_draw_handler_property(self):
        from arcadeactions.visualizer.instrumentation import DebugDataStore
        from arcadeactions.visualizer.overlay import InspectorOverlay
        from arcadeactions.visualizer.renderer import OverlayRenderer

        debug_store = DebugDataStore()
        overlay = InspectorOverlay(debug_store)
        renderer = OverlayRenderer(overlay)

        session = VisualizerSession(
            debug_store=debug_store,
            overlay=overlay,
            renderer=renderer,
            guides=None,
            condition_debugger=None,
            timeline=None,
            control_manager=None,
            guide_renderer=None,
            event_window=None,
            snapshot_directory=None,
            sprite_positions_provider=None,
            target_names_provider=None,
            wrapped_update_all=lambda *args: None,
            previous_update_all=lambda *args: None,
            previous_debug_store=None,
            previous_enable_flag=False,
        )
        assert session.draw_handler is not None
        assert callable(session.draw_handler)

    def test_draw_handler_none(self):
        session = VisualizerSession(
            debug_store=None,
            overlay=None,
            renderer=None,
            guides=None,
            condition_debugger=None,
            timeline=None,
            control_manager=None,
            guide_renderer=None,
            event_window=None,
            snapshot_directory=None,
            sprite_positions_provider=None,
            target_names_provider=None,
            wrapped_update_all=lambda *args: None,
            previous_update_all=lambda *args: None,
            previous_debug_store=None,
            previous_enable_flag=False,
        )
        assert session.draw_handler is None


class TestSessionHelpers:
    def test_get_visualizer_session_not_attached(self):
        detach_visualizer()
        session = get_visualizer_session()
        assert session is None

    def test_is_visualizer_attached_false(self):
        detach_visualizer()
        assert is_visualizer_attached() is False


class TestEventWindowOpening:
    def test_open_event_window_headless_skips_visibility(self, monkeypatch, tmp_path):
        class StubOverlay:
            highlighted_target_id = None

        class StubEventWindow:
            def __init__(self, *args, **kwargs):
                self.visible_calls = []
                self.focus_calls = 0

            def set_visible(self, value: bool) -> None:
                self.visible_calls.append(value)

            def request_main_window_focus(self) -> None:
                self.focus_calls += 1

        session = VisualizerSession(
            debug_store=object(),
            overlay=StubOverlay(),
            renderer=None,
            guides=None,
            condition_debugger=None,
            timeline=None,
            control_manager=None,
            guide_renderer=None,
            event_window=None,
            snapshot_directory=tmp_path,
            sprite_positions_provider=None,
            target_names_provider=None,
            wrapped_update_all=lambda *args: None,
            previous_update_all=lambda *args: None,
            previous_debug_store=None,
            previous_enable_flag=False,
            window=None,
        )

        monkeypatch.setenv("CI", "true")
        monkeypatch.setattr(
            "arcadeactions.visualizer.attach.move_to_primary_monitor",
            lambda *args, **kwargs: True,
        )

        _open_event_window(session, None, StubEventWindow, lambda: None)

        assert session.event_window is not None
        assert session.event_window.visible_calls == []
        assert session.event_window.focus_calls == 0
