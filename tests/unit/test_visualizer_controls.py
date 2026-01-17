"""Unit tests for debug control manager."""

from __future__ import annotations

import arcade
import pytest

from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.controls import DebugControlManager
from actions.visualizer.guides import GuideManager
from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.timeline import TimelineStrip


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


@pytest.fixture
def overlay(debug_store):
    return InspectorOverlay(debug_store=debug_store)


@pytest.fixture
def guides():
    return GuideManager(initial_enabled=False)


@pytest.fixture
def condition_debugger(debug_store):
    return ConditionDebugger(debug_store)


@pytest.fixture
def timeline(debug_store):
    return TimelineStrip(debug_store)


@pytest.fixture
def action_controller():
    class StubController:
        def pause_all(self):
            pass

        def resume_all(self):
            pass

        def step_all(self, delta_time):
            pass

    return StubController()


@pytest.fixture
def control_manager(tmp_path, overlay, guides, condition_debugger, timeline, action_controller):
    def toggle_event_window(open_state):
        pass

    return DebugControlManager(
        overlay=overlay,
        guides=guides,
        condition_debugger=condition_debugger,
        timeline=timeline,
        snapshot_directory=tmp_path,
        action_controller=action_controller,
        toggle_event_window=toggle_event_window,
    )


class TestDebugControlManager:
    def test_init(self, control_manager, tmp_path):
        assert control_manager.overlay is not None
        assert control_manager.guides is not None
        assert control_manager.condition_debugger is not None
        assert control_manager.timeline is not None
        assert control_manager.snapshot_directory == tmp_path
        assert control_manager.condition_panel_visible is False
        assert control_manager.is_paused is False

    def test_handle_key_press_f3(self, control_manager):
        # F3 cycles overlay position
        result = control_manager.handle_key_press(arcade.key.F3)
        assert result is True
        # Overlay position should have changed
        assert control_manager.overlay.position in ["upper_left", "upper_right", "lower_right", "lower_left"]

    def test_handle_key_press_f4(self, control_manager):
        # F4 toggles condition panel
        assert control_manager.condition_panel_visible is False
        result = control_manager.handle_key_press(arcade.key.F4)
        assert result is True
        assert control_manager.condition_panel_visible is True
        result = control_manager.handle_key_press(arcade.key.F4)
        assert result is True
        assert control_manager.condition_panel_visible is False

    def test_handle_key_press_f5(self, control_manager):
        # F5 toggles guides
        initial_state = control_manager.guides.velocity_guide.enabled
        result = control_manager.handle_key_press(arcade.key.F5)
        assert result is True
        assert control_manager.guides.velocity_guide.enabled != initial_state

    def test_handle_key_press_f6(self, control_manager):
        # F6 toggles pause
        assert control_manager.is_paused is False
        result = control_manager.handle_key_press(arcade.key.F6)
        assert result is True
        assert control_manager.is_paused is True
        result = control_manager.handle_key_press(arcade.key.F6)
        assert result is True
        assert control_manager.is_paused is False

    def test_handle_key_press_f7_when_paused(self, control_manager):
        # F7 steps when paused
        control_manager.is_paused = True
        step_called = []
        original_step = control_manager.action_controller.step_all

        def track_step(delta_time):
            step_called.append(delta_time)
            original_step(delta_time)

        control_manager.action_controller.step_all = track_step
        result = control_manager.handle_key_press(arcade.key.F7)
        assert result is True
        assert len(step_called) == 1
        assert step_called[0] == control_manager.step_delta

    def test_handle_key_press_f7_when_not_paused(self, control_manager):
        # F7 does nothing when not paused
        step_called = []
        original_step = control_manager.action_controller.step_all

        def track_step(delta_time):
            step_called.append(delta_time)
            original_step(delta_time)

        control_manager.action_controller.step_all = track_step
        control_manager.is_paused = False
        result = control_manager.handle_key_press(arcade.key.F7)
        assert result is True
        assert len(step_called) == 0  # Should not step when not paused

    def test_handle_key_press_f8(self, control_manager, debug_store):
        # F8 highlights next target
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        control_manager.overlay.update()
        result = control_manager.handle_key_press(arcade.key.F8)
        assert result is True
        assert control_manager.overlay.highlighted_target_id == 100

    def test_handle_key_press_f9(self, control_manager, debug_store, tmp_path, monkeypatch):
        # F9 exports snapshot
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        printed = []
        monkeypatch.setattr("builtins.print", lambda *args: printed.append(" ".join(str(a) for a in args)))
        result = control_manager.handle_key_press(arcade.key.F9)
        assert result is True
        assert len(printed) > 0
        assert any("Snapshot" in msg for msg in printed)

    def test_handle_key_press_unknown_key(self, control_manager):
        # Unknown keys return False
        result = control_manager.handle_key_press(arcade.key.A)
        assert result is False

    def test_update_refreshes_target_names(self, control_manager, monkeypatch):
        called = []

        def provider():
            called.append(True)
            return {100: "self.player"}

        control_manager.target_names_provider = provider
        control_manager._target_names_frame = -100  # Force refresh
        control_manager.update()
        assert len(called) > 0

    def test_update_updates_overlay(self, control_manager):
        update_calls = []
        original_update = control_manager.overlay.update

        def track_update():
            update_calls.append(True)
            original_update()

        control_manager.overlay.update = track_update
        control_manager.update()
        assert len(update_calls) == 1

    def test_update_condition_debugger_when_visible(self, control_manager):
        control_manager.condition_panel_visible = True
        update_calls = []
        original_update = control_manager.condition_debugger.update

        def track_update():
            update_calls.append(True)
            original_update()

        control_manager.condition_debugger.update = track_update
        control_manager.update()
        assert len(update_calls) == 1

    def test_update_clears_condition_debugger_when_not_visible(self, control_manager):
        control_manager.condition_panel_visible = False
        clear_calls = []
        original_clear = control_manager.condition_debugger.clear

        def track_clear():
            clear_calls.append(True)
            original_clear()

        control_manager.condition_debugger.clear = track_clear
        control_manager.update()
        assert len(clear_calls) == 1

    def test_update_updates_timeline(self, control_manager):
        update_calls = []
        original_update = control_manager.timeline.update

        def track_update():
            update_calls.append(True)
            original_update()

        control_manager.timeline.update = track_update
        control_manager.update()
        assert len(update_calls) == 1

    def test_update_updates_guides_when_enabled(self, control_manager, debug_store):
        control_manager.guides.velocity_guide.enabled = True
        update_calls = []
        original_update = control_manager.guides.update

        def track_update(*args, **kwargs):
            update_calls.append(True)
            original_update(*args, **kwargs)

        control_manager.guides.update = track_update
        control_manager.update(sprite_positions={100: (10.0, 20.0)})
        assert len(update_calls) == 1

    def test_update_skips_guides_when_disabled(self, control_manager):
        control_manager.guides.velocity_guide.enabled = False
        control_manager.guides.bounds_guide.enabled = False
        control_manager.guides.path_guide.enabled = False
        control_manager.guides.highlight_guide.enabled = False  # Disable highlight too
        update_calls = []
        original_update = control_manager.guides.update

        def track_update(*args, **kwargs):
            update_calls.append(True)
            original_update(*args, **kwargs)

        control_manager.guides.update = track_update
        control_manager.update()
        # Timeline still updates, but guides don't when all disabled
        assert len(update_calls) == 0

    def test_get_target_names(self, control_manager):
        control_manager._cached_target_names = {100: "self.player"}
        names = control_manager.get_target_names()
        assert names == {100: "self.player"}

    def test_get_target_names_empty(self, control_manager):
        control_manager._cached_target_names = {}
        names = control_manager.get_target_names()
        assert names == {}

    def test_refresh_target_names_no_provider(self, control_manager):
        control_manager.target_names_provider = None
        control_manager._refresh_target_names()
        assert control_manager._cached_target_names == {}

    def test_refresh_target_names_with_provider(self, control_manager):
        control_manager.target_names_provider = lambda: {100: "self.player"}
        control_manager._refresh_target_names()
        assert control_manager._cached_target_names == {100: "self.player"}

    def test_refresh_target_names_provider_exception(self, control_manager):
        def failing_provider():
            raise RuntimeError("boom")

        control_manager.target_names_provider = failing_provider
        control_manager._refresh_target_names()
        assert control_manager._cached_target_names == {}

    def test_refresh_target_names_normalizes_keys(self, control_manager):
        control_manager.target_names_provider = lambda: {"100": "self.player", 200: "self.enemy"}
        control_manager._refresh_target_names()
        assert control_manager._cached_target_names == {100: "self.player", 200: "self.enemy"}

    def test_refresh_target_names_invalid_keys(self, control_manager):
        control_manager.target_names_provider = lambda: {"invalid": "self.player", None: "self.enemy"}
        control_manager._refresh_target_names()
        # Invalid keys should be skipped
        assert "invalid" not in control_manager._cached_target_names
        assert None not in control_manager._cached_target_names

    def test_toggle_pause(self, control_manager):
        assert control_manager.is_paused is False
        control_manager._toggle_pause()
        assert control_manager.is_paused is True
        control_manager._toggle_pause()
        assert control_manager.is_paused is False
