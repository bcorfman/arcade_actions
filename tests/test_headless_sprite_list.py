"""Tests for headless/CI sprite list behaviour.

These tests give us confidence that the HeadlessWindow fallback used on
Windows/macOS CI continues to work without requiring the full GitHub Actions
matrix.
"""

from __future__ import annotations

import arcade
import pytest

from tests.conftest import HeadlessWindow


@pytest.fixture
def headless_environment(monkeypatch: pytest.MonkeyPatch) -> HeadlessWindow:
    """Simulate the headless CI environment used on Windows/macOS."""

    window = HeadlessWindow(800, 600, visible=False)

    # Replace the arcade.Window class so new windows are headless
    monkeypatch.setattr(arcade, "Window", HeadlessWindow)

    # Patch the top-level get_window helper
    monkeypatch.setattr(arcade, "get_window", lambda: window)

    # Patch the window_commands helpers Arcade re-exports
    try:
        import arcade.window_commands as window_commands

        monkeypatch.setattr(window_commands, "get_window", lambda: window)
    except ImportError:  # pragma: no cover - defensive
        window_commands = None

    # Patch the SpriteList module helpers
    import arcade.sprite_list.sprite_list as sprite_list_module

    monkeypatch.setattr(sprite_list_module, "get_window", lambda: window)

    # Force SpriteList to be lazy so it does not touch OpenGL resources
    original_init = sprite_list_module.SpriteList.__init__

    def lazy_init(self, *args, **kwargs):
        kwargs["lazy"] = True
        return original_init(self, *args, **kwargs)

    monkeypatch.setattr(sprite_list_module.SpriteList, "__init__", lazy_init)

    return window


def test_headless_sprite_list_creation(headless_environment: HeadlessWindow) -> None:
    """SpriteList can be created in headless mode without raising errors."""

    from arcade.sprite_list.sprite_list import SpriteList

    sprite_list = SpriteList()

    # SpriteList should stay uninitialised until draw() / explicit initialise
    assert not sprite_list._initialized


def test_headless_window_ctx_raises(headless_environment: HeadlessWindow) -> None:
    """Headless window exposes the same ctx failure behaviour our fixture relies on."""

    with pytest.raises(RuntimeError):
        _ = headless_environment.ctx
