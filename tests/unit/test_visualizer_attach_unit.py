"""Unit tests for visualizer attach helpers."""

from __future__ import annotations

from pathlib import Path

import arcade
import pytest

from arcadeactions.base import Action
from arcadeactions.visualizer import _session
from arcadeactions.visualizer.attach import (
    attach_visualizer,
    auto_attach_from_env,
    detach_visualizer,
    enable_visualizer_hotkey,
)


class StubDebugStore:
    pass


class StubOverlay:
    def __init__(self, _store: object) -> None:
        self.highlighted_target_id = None
        self.visible = True


class StubRenderer:
    def __init__(self, _overlay: object) -> None:
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        return None


class StubGuides:
    def __init__(self, initial_enabled: bool = False) -> None:  # noqa: ARG002
        self.update_calls = 0

    def update(self, *_args: object, **_kwargs: object) -> None:
        self.update_calls += 1


class StubConditionDebugger:
    def __init__(self, _store: object, max_entries: int = 50) -> None:  # noqa: ARG002
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def clear(self) -> None:
        return None


class StubTimeline:
    def __init__(self, _store: object, max_entries: int = 100) -> None:  # noqa: ARG002
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


class StubGuideRenderer:
    def __init__(self, _guides: object) -> None:
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        return None


class StubEventWindow:
    def __init__(self, **_kwargs: object) -> None:
        self.visible = False
        self.close_calls = 0
        self.focus_calls = 0
        self.width = 320
        self.height = 200
        self.location_calls: list[tuple[int, int]] = []

    def set_visible(self, visible: bool) -> None:
        self.visible = visible

    def set_location(self, x: int, y: int) -> None:
        self.location_calls.append((x, y))

    def close(self) -> None:
        self.close_calls += 1

    def request_main_window_focus(self) -> None:
        self.focus_calls += 1


class StubControlManager:
    def __init__(
        self,
        *,
        overlay: object,
        guides: object,
        condition_debugger: object,
        timeline: object,
        snapshot_directory: Path,
        action_controller: object,
        toggle_event_window,
        target_names_provider=None,
        **_kwargs: object,
    ) -> None:
        self.overlay = overlay
        self.guides = guides
        self.condition_debugger = condition_debugger
        self.timeline = timeline
        self.snapshot_directory = snapshot_directory
        self.action_controller = action_controller
        self.toggle_event_window = toggle_event_window
        self.target_names_provider = target_names_provider
        self.condition_panel_visible = False

    def get_target_names(self) -> dict[int, str]:
        if self.target_names_provider is None:
            return {}
        return self.target_names_provider()

    def update(self, _positions=None) -> None:
        return None

    def handle_key_press(self, _symbol: int, _modifiers: int) -> bool:
        return False


@pytest.fixture(autouse=True)
def reset_visualizer_state():
    _session._VISUALIZER_SESSION = None
    _session._AUTO_ATTACH_ATTEMPTED = False
    Action.stop_all()
    yield
    detach_visualizer()
    Action.stop_all()


def _attach_kwargs(tmp_path: Path) -> dict[str, object]:
    return {
        "debug_store": StubDebugStore(),
        "snapshot_directory": tmp_path,
        "overlay_cls": StubOverlay,
        "renderer_cls": StubRenderer,
        "guide_manager_cls": StubGuides,
        "condition_debugger_cls": StubConditionDebugger,
        "timeline_cls": StubTimeline,
        "controls_cls": StubControlManager,
        "guide_renderer_cls": StubGuideRenderer,
        "event_window_cls": StubEventWindow,
    }


def test_attach_visualizer_idempotent(tmp_path: Path) -> None:
    session = attach_visualizer(**_attach_kwargs(tmp_path))
    session_again = attach_visualizer(**_attach_kwargs(tmp_path))

    assert session_again is session


def test_detach_restores_debug_store(tmp_path: Path) -> None:
    original_store = getattr(Action, "_debug_store", None)
    attach_visualizer(**_attach_kwargs(tmp_path))

    assert detach_visualizer() is True
    assert getattr(Action, "_debug_store", None) is original_store


def test_toggle_event_window_open_and_close(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CI", "false")
    monkeypatch.setenv("GITHUB_ACTIONS", "false")
    session = attach_visualizer(**_attach_kwargs(tmp_path))
    manager = session.control_manager

    manager.toggle_event_window(True)

    assert session.event_window is not None
    assert session.event_window.visible is True
    assert session.event_window.focus_calls == 1

    manager.toggle_event_window(False)

    assert session.event_window is None


def test_auto_attach_from_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")
    result = auto_attach_from_env(attach_kwargs=_attach_kwargs(tmp_path))

    assert result is True
    assert _session._VISUALIZER_SESSION is not None


def test_enable_visualizer_hotkey(monkeypatch, tmp_path: Path) -> None:
    handlers = {}

    class StubWindow:
        def push_handlers(self, **kwargs):  # noqa: ANN002
            handlers.update(kwargs)

    window = StubWindow()
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    assert enable_visualizer_hotkey(attach_kwargs=_attach_kwargs(tmp_path)) is True
    assert "on_key_press" in handlers

    result = handlers["on_key_press"](arcade.key.F3, arcade.key.MOD_SHIFT)
    assert result is True
    assert _session._VISUALIZER_SESSION is not None
