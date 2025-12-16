"""Unit tests for visualizer renderer components."""

from __future__ import annotations

import arcade
import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay, ActionCard, TargetGroup
from actions.visualizer.renderer import (
    OverlayRenderer,
    ConditionPanelRenderer,
    TimelineRenderer,
    GuideRenderer,
    _sync_text_objects,
    _TextSpec,
)
from actions.visualizer.condition_panel import ConditionDebugger
from actions.visualizer.timeline import TimelineStrip
from actions.visualizer.guides import GuideManager


@pytest.fixture
def debug_store():
    store = DebugDataStore()
    store.update_frame(1, 0.016)
    return store


@pytest.fixture
def overlay(debug_store):
    overlay = InspectorOverlay(debug_store=debug_store)
    return overlay


class TestOverlayRenderer:
    def test_init(self, overlay):
        renderer = OverlayRenderer(overlay)
        assert renderer.overlay is overlay
        assert renderer.font_size == 10
        assert renderer.line_height == 14
        assert renderer.text_objects == []
        assert renderer._text_specs == []
        assert renderer._last_text_specs == []

    def test_update_when_not_visible(self, overlay):
        overlay.visible = False
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert renderer.text_objects == []
        assert renderer._text_specs == []
        assert renderer._background_rects == []
        assert renderer._progress_rects == []

    def test_update_when_visible_no_window(self, overlay, monkeypatch):
        overlay.visible = True
        monkeypatch.setattr(arcade, "get_window", lambda: (_ for _ in ()).throw(RuntimeError("no window")))
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1  # Title only

    def test_update_with_window(self, overlay, monkeypatch):
        overlay.visible = True
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1  # Title

    def test_update_position_upper_left(self, overlay, monkeypatch):
        overlay.visible = True
        overlay.position = "upper_left"
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1
        spec = renderer._text_specs[0]
        assert spec.x == 20  # buffer
        assert spec.y == 720 - 20 - 12  # window_height - buffer - text_height

    def test_update_position_upper_right(self, overlay, monkeypatch):
        overlay.visible = True
        overlay.position = "upper_right"
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1
        spec = renderer._text_specs[0]
        assert spec.x < 1280  # Should be positioned from right

    def test_update_position_lower_right(self, overlay, monkeypatch):
        overlay.visible = True
        overlay.position = "lower_right"
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1
        spec = renderer._text_specs[0]
        assert spec.y == 20  # buffer

    def test_update_position_lower_left(self, overlay, monkeypatch):
        overlay.visible = True
        overlay.position = "lower_left"
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        renderer = OverlayRenderer(overlay)
        renderer.update()
        assert len(renderer._text_specs) == 1
        spec = renderer._text_specs[0]
        assert spec.x == 20  # buffer
        assert spec.y == 20  # buffer

    def test_render_group(self, overlay, debug_store, monkeypatch):
        overlay.visible = True
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=0.5,
        )
        overlay.update()
        
        renderer = OverlayRenderer(overlay)
        renderer.update()
        # Simplified overlay only shows title, not groups
        assert len(renderer._text_specs) == 1

    def test_render_card(self, overlay, debug_store, monkeypatch):
        overlay.visible = True
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=0.5,
        )
        overlay.update()
        
        renderer = OverlayRenderer(overlay)
        renderer.update()
        # Simplified overlay only shows title
        assert len(renderer._text_specs) == 1

    def test_draw_when_not_visible(self, overlay):
        overlay.visible = False
        renderer = OverlayRenderer(overlay)
        renderer.update()
        renderer.draw()  # Should not crash

    def test_draw_with_gl_exception(self, overlay, monkeypatch):
        overlay.visible = True
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer = OverlayRenderer(overlay)
        renderer.update()
        
        from pyglet.gl.lib import GLException
        
        call_count = 0
        def fake_draw(self):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise GLException("OpenGL error")
        
        monkeypatch.setattr(arcade.Text, "draw", fake_draw)
        renderer.draw()  # Should recover from GLException
        assert call_count == 2  # Should retry

    def test_text_width_cache(self, overlay, monkeypatch):
        overlay.visible = True
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer = OverlayRenderer(overlay)
        renderer.update()
        
        # First update should cache text width
        assert len(renderer._text_width_cache) > 0
        
        # Second update should use cache
        renderer.update()
        assert len(renderer._text_width_cache) > 0


class TestConditionPanelRenderer:
    def test_init(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        renderer = ConditionPanelRenderer(debugger)
        assert renderer.debugger is debugger
        assert renderer.width == 320
        assert renderer.max_rows == 14
        assert renderer.font_size == 10
        assert renderer.line_height == 16
        assert renderer.margin == 8

    def test_update_not_visible(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        renderer = ConditionPanelRenderer(debugger)
        renderer.update(visible=False)
        assert renderer._visible is False
        assert renderer.text_objects == []
        assert renderer._text_specs == []
        assert renderer._background_rect is None

    def test_update_visible_no_entries(self, debug_store, monkeypatch):
        debugger = ConditionDebugger(debug_store)
        renderer = ConditionPanelRenderer(debugger)
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update(visible=True)
        assert renderer._visible is True
        assert len(renderer._text_specs) >= 1  # Header at minimum

    def test_update_with_entries(self, debug_store, monkeypatch):
        debugger = ConditionDebugger(debug_store)
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=True,
            condition_str="lambda: True",
        )
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        debugger.update()
        
        renderer = ConditionPanelRenderer(debugger)
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update(visible=True)
        assert renderer._visible is True
        assert len(renderer._text_specs) >= 2  # Header + entry

    def test_update_with_long_result(self, debug_store, monkeypatch):
        debugger = ConditionDebugger(debug_store)
        long_result = "x" * 100
        debug_store.record_condition_evaluation(
            action_id=1,
            action_type="MoveUntil",
            result=long_result,
            condition_str="lambda: True",
        )
        debug_store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        debugger.update()
        
        renderer = ConditionPanelRenderer(debugger)
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update(visible=True)
        # Check that long results are truncated (condition panel truncates result strings)
        text_specs = [s.text for s in renderer._text_specs]
        # Find the line with the result
        result_lines = [t for t in text_specs if "->" in t]
        if result_lines:
            # Result part should be truncated if too long
            result_part = result_lines[0].split("->")[-1].strip()
            assert len(result_part) <= 60 or result_part.endswith("...")

    def test_draw_not_visible(self, debug_store):
        debugger = ConditionDebugger(debug_store)
        renderer = ConditionPanelRenderer(debugger)
        renderer.update(visible=False)
        renderer.draw()  # Should not crash

    def test_draw_with_gl_exception(self, debug_store, monkeypatch):
        debugger = ConditionDebugger(debug_store)
        renderer = ConditionPanelRenderer(debugger)
        window = type("Window", (), {"width": 1280, "height": 720})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update(visible=True)
        
        from pyglet.gl.lib import GLException
        
        call_count = 0
        def fake_draw(self):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise GLException("OpenGL error")
        
        monkeypatch.setattr(arcade.Text, "draw", fake_draw)
        renderer.draw()  # Should recover from GLException
        assert call_count >= 2  # Should retry (may retry multiple times)


class TestTimelineRenderer:
    def test_init(self, debug_store):
        timeline = TimelineStrip(debug_store)
        renderer = TimelineRenderer(timeline)
        assert renderer.timeline is timeline
        assert renderer.width == 420
        assert renderer.height == 90
        assert renderer.margin == 8

    def test_set_font_size(self, debug_store):
        timeline = TimelineStrip(debug_store)
        renderer = TimelineRenderer(timeline)
        renderer.set_font_size(11.0)
        assert renderer.font_size == 11.0

    def test_set_font_size_invalid(self, debug_store):
        timeline = TimelineStrip(debug_store)
        renderer = TimelineRenderer(timeline)
        with pytest.raises(ValueError):
            renderer.set_font_size(-1.0)

    def test_update_no_entries(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        renderer = TimelineRenderer(timeline)
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        assert renderer._background_rect is None
        assert renderer._bars == []
        assert renderer.text_objects == []

    def test_update_with_entries(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        debug_store.update_frame(1, 0.016)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
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
        timeline.update()
        
        renderer = TimelineRenderer(timeline)
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        assert renderer._background_rect is not None
        assert len(renderer._bars) >= 1

    def test_update_with_highlighted_target(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        debug_store.update_frame(1, 0.016)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
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
        timeline.update()
        
        highlighted_called = []
        def highlighted_provider():
            highlighted_called.append(True)
            return 100
        
        renderer = TimelineRenderer(
            timeline,
            highlighted_target_provider=highlighted_provider,
        )
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        assert len(highlighted_called) > 0
        assert len(renderer._highlight_outlines) >= 1

    def test_update_with_target_names(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        debug_store.update_frame(1, 0.016)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
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
        timeline.update()
        
        names_provider_called = []
        def names_provider():
            names_provider_called.append(True)
            return {100: "self.player"}
        
        renderer = TimelineRenderer(
            timeline,
            target_names_provider=names_provider,
        )
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        assert len(names_provider_called) > 0
        text_specs = [s.text for s in renderer._text_specs]
        assert any("self.player" in text for text in text_specs)

    def test_draw_no_background(self, debug_store):
        timeline = TimelineStrip(debug_store)
        renderer = TimelineRenderer(timeline)
        renderer.draw()  # Should not crash when _background_rect is None

    def test_draw_with_bars(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        debug_store.update_frame(1, 0.016)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
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
        timeline.update()
        
        renderer = TimelineRenderer(timeline)
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        renderer.draw()  # Should not crash

    def test_draw_with_gl_exception(self, debug_store, monkeypatch):
        timeline = TimelineStrip(debug_store)
        debug_store.update_frame(1, 0.016)
        debug_store.record_event("created", 1, "MoveUntil", 100, "Sprite")
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
        timeline.update()
        
        renderer = TimelineRenderer(timeline)
        window = type("Window", (), {"width": 800, "height": 600})()
        monkeypatch.setattr(arcade, "get_window", lambda: window)
        
        renderer.update()
        
        from pyglet.gl.lib import GLException
        
        call_count = 0
        def fake_draw(self):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise GLException("OpenGL error")
        
        monkeypatch.setattr(arcade.Text, "draw", fake_draw)
        renderer.draw()  # Should recover from GLException
        assert call_count == 2  # Should retry


class TestGuideRenderer:
    def test_init(self):
        guide_manager = GuideManager()
        renderer = GuideRenderer(guide_manager)
        assert renderer.guide_manager is guide_manager

    def test_update(self):
        guide_manager = GuideManager()
        renderer = GuideRenderer(guide_manager)
        renderer.update()  # Should not crash

    def test_draw_no_guides_enabled(self):
        guide_manager = GuideManager(initial_enabled=False)
        renderer = GuideRenderer(guide_manager)
        renderer.draw()  # Should not crash

    def test_draw_with_velocity_guide(self, debug_store):
        guide_manager = GuideManager(initial_enabled=True)
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
            velocity=(5.0, 0.0),
        )
        guide_manager.velocity_guide.enabled = True
        guide_manager.update(
            debug_store.get_all_snapshots(),
            {100: (100.0, 200.0)},
        )
        
        renderer = GuideRenderer(guide_manager)
        renderer.draw()  # Should not crash

    def test_draw_with_bounds_guide(self, debug_store):
        guide_manager = GuideManager(initial_enabled=True)
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
            bounds=(0.0, 0.0, 800.0, 600.0),
        )
        guide_manager.bounds_guide.enabled = True
        guide_manager.update(
            debug_store.get_all_snapshots(),
            {100: (100.0, 200.0)},
        )
        
        renderer = GuideRenderer(guide_manager)
        renderer.draw()  # Should not crash

    def test_draw_with_path_guide(self, debug_store):
        guide_manager = GuideManager(initial_enabled=True)
        debug_store.update_snapshot(
            action_id=1,
            action_type="FollowPathUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            metadata={"path_points": [(0, 0), (100, 100), (200, 200)]},
        )
        guide_manager.path_guide.enabled = True
        guide_manager.update(
            debug_store.get_all_snapshots(),
            {100: (100.0, 200.0)},
        )
        
        renderer = GuideRenderer(guide_manager)
        renderer.draw()  # Should not crash

    def test_draw_with_highlight_guide(self, debug_store):
        guide_manager = GuideManager(initial_enabled=True)
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
        guide_manager.highlight_guide.enabled = True
        guide_manager.update(
            debug_store.get_all_snapshots(),
            {100: (100.0, 200.0)},
            highlighted_target_id=100,
            sprite_sizes={100: (50.0, 50.0)},
        )
        
        renderer = GuideRenderer(guide_manager)
        renderer.draw()  # Should not crash


class TestSyncTextObjects:
    def test_sync_empty(self):
        text_objects = []
        specs = []
        last_specs = []
        _sync_text_objects(text_objects, specs, last_specs)
        assert text_objects == []
        assert last_specs == []

    def test_sync_new_specs(self):
        text_objects = []
        specs = [
            _TextSpec("Hello", 10, 20, arcade.color.WHITE, 12),
            _TextSpec("World", 10, 40, arcade.color.WHITE, 12),
        ]
        last_specs = []
        _sync_text_objects(text_objects, specs, last_specs)
        assert len(text_objects) == 2
        assert len(last_specs) == 2

    def test_sync_same_specs(self):
        text_objects = []
        spec = _TextSpec("Hello", 10, 20, arcade.color.WHITE, 12)
        specs = [spec]
        last_specs = [spec]
        _sync_text_objects(text_objects, specs, last_specs)
        # Should not recreate objects if specs haven't changed
        assert len(text_objects) == 0

    def test_sync_changed_specs(self):
        text_objects = []
        old_spec = _TextSpec("Hello", 10, 20, arcade.color.WHITE, 12)
        new_spec = _TextSpec("World", 10, 20, arcade.color.WHITE, 12)
        specs = [new_spec]
        last_specs = [old_spec]
        _sync_text_objects(text_objects, specs, last_specs)
        assert len(text_objects) == 1
        assert len(last_specs) == 1

