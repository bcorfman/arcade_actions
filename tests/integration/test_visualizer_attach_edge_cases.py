"""Edge case tests for attach.py to improve coverage."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import arcade
import pytest

from arcadeactions.visualizer.attach import (
    detach_visualizer,
)
from arcadeactions.visualizer.attach import attach_visualizer, get_visualizer_session
from arcadeactions.base import Action


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
        self.timeline = timeline
        self.update_calls = 0
        self.last_positions: dict[int, tuple[float, float]] | None = None
        self.target_names_provider = target_names_provider

    def update(self, sprite_positions: dict[int, tuple[float, float]] | None = None) -> None:
        self.update_calls += 1
        self.last_positions = sprite_positions

    def handle_key_press(self, symbol: int, modifiers: int) -> bool:
        return False

    def get_target_names(self) -> dict[int, str]:
        if self.target_names_provider is None:
            return {}
        return self.target_names_provider() or {}


@pytest.fixture(autouse=True)
def auto_detach():
    """Ensure the visualizer is detached after each test."""

    yield
    detach_visualizer()


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


class TestCollectTargetNames:
    """Test _collect_target_names_from_view edge cases."""

    def test_collect_target_names_no_view(self, monkeypatch):
        """Test _collect_target_names_from_view when window has no view."""
        from arcadeactions.visualizer.attach import _collect_target_names_from_view

        class StubWindow:
            current_view = None

        monkeypatch.setattr(arcade, "get_window", lambda: StubWindow())

        names = _collect_target_names_from_view()

        assert isinstance(names, dict)


class TestAttachUpdateAllWrapping:
    def test_attach_is_idempotent_for_update_all(self, tmp_path):
        """Ensure attach_visualizer does not wrap Action.update_all multiple times."""
        original_update = Action.update_all
        session = attach_visualizer(**stub_attach_kwargs(tmp_path))
        wrapped_update = Action.update_all

        session_again = attach_visualizer(**stub_attach_kwargs(tmp_path))

        assert session_again is session
        assert getattr(Action.update_all, "__func__", Action.update_all) is getattr(
            wrapped_update, "__func__", wrapped_update
        )
        original_func = getattr(original_update, "__func__", original_update)
        assert session.previous_update_all is original_func
