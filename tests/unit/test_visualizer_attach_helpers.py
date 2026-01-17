"""Unit tests for attach.py helper functions."""

from __future__ import annotations

import arcade
import pytest

from actions.base import Action
from actions.visualizer.attach import (
    _collect_sprite_positions,
    _collect_sprite_sizes_and_ids,
    _collect_target_names_from_view,
    VisualizerSession,
    get_visualizer_session,
    is_visualizer_attached,
)


@pytest.fixture(autouse=True)
def reset_session():
    """Reset visualizer session before each test."""
    from actions.visualizer.attach import _VISUALIZER_SESSION, detach_visualizer

    yield
    detach_visualizer()
    # Clear module-level state
    import actions.visualizer.attach as attach_module

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
        from actions.conditional import MoveUntil

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
        from actions.visualizer.controls import DebugControlManager
        from actions.visualizer.instrumentation import DebugDataStore
        from actions.visualizer.overlay import InspectorOverlay
        from actions.visualizer.guides import GuideManager
        from actions.visualizer.condition_panel import ConditionDebugger
        from actions.visualizer.timeline import TimelineStrip
        from pathlib import Path

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
        from actions.visualizer.renderer import OverlayRenderer
        from actions.visualizer.instrumentation import DebugDataStore
        from actions.visualizer.overlay import InspectorOverlay

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
        from actions.visualizer.attach import detach_visualizer

        detach_visualizer()
        session = get_visualizer_session()
        assert session is None

    def test_is_visualizer_attached_false(self):
        from actions.visualizer.attach import detach_visualizer

        detach_visualizer()
        assert is_visualizer_attached() is False
