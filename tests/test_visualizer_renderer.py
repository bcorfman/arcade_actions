"""Tests for OverlayRenderer behaviour and drawing paths."""

from __future__ import annotations

import arcade
import pytest

from actions.visualizer.instrumentation import DebugDataStore
from actions.visualizer.overlay import InspectorOverlay
from actions.visualizer.renderer import OverlayRenderer


@pytest.fixture
def overlay_with_progress():
    store = DebugDataStore()
    store.update_snapshot(
        action_id=1,
        action_type="MoveUntil",
        target_id=100,
        target_type="Sprite",
        tag="movement",
        is_active=True,
        is_paused=False,
        factor=1.0,
        elapsed=0.0,
        progress=0.5,
    )
    overlay = InspectorOverlay(debug_store=store)
    overlay.update()
    return overlay


def test_renderer_skips_when_not_visible(overlay_with_progress):
    overlay_with_progress.visible = False
    renderer = OverlayRenderer(overlay_with_progress)
    renderer.update()
    assert renderer.text_objects == []


def test_renderer_collects_rectangles_and_text(monkeypatch, overlay_with_progress):
    renderer = OverlayRenderer(overlay_with_progress)
    renderer.update()

    # Title + header + body lines + progress -> ensure multiple text objects
    assert len(renderer.text_objects) >= 3
    assert len(renderer._background_rects) == 1
    assert len(renderer._progress_rects) == 1

    drawn_rects = []
    drawn_text = []

    def fake_draw_lbwh_rectangle_filled(x, y, width, height, color):
        drawn_rects.append((x, y, width, height, color))

    def fake_text_draw(self):
        drawn_text.append(id(self))

    monkeypatch.setattr(arcade, "draw_lbwh_rectangle_filled", fake_draw_lbwh_rectangle_filled)
    monkeypatch.setattr(arcade.Text, "draw", fake_text_draw, raising=False)

    renderer.draw()
    assert drawn_rects == renderer._background_rects + renderer._progress_rects
    assert len(drawn_text) == len(renderer.text_objects)


def test_renderer_handles_cards_without_progress():
    store = DebugDataStore()
    store.update_snapshot(
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
    overlay = InspectorOverlay(debug_store=store)
    overlay.update()

    renderer = OverlayRenderer(overlay)
    renderer.update()

    assert renderer._background_rects == []
    assert renderer._progress_rects == []
