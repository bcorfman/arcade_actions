"""Integration tests for DevVisualizer GUI integration points.

These tests verify that GUI-dependent code (window attachment, drawing)
works correctly with real windows and OpenGL contexts.
"""

from __future__ import annotations

import pytest

import arcade

from actions.dev.visualizer import DevVisualizer


@pytest.mark.integration
class TestDevVisualizerIntegration:
    """Integration tests for DevVisualizer GUI integration."""

    def test_attach_to_window_full_integration(self, window):
        """Integration test: Verify all handlers are wrapped correctly when attaching to window."""
        if window is None:
            pytest.skip("No window available")

        dev_viz = DevVisualizer()
        original_draw = window.on_draw
        original_key_press = getattr(window, "on_key_press", None)
        original_mouse_press = getattr(window, "on_mouse_press", None)

        # Attach DevVisualizer
        result = dev_viz.attach_to_window(window)
        assert result is True
        assert dev_viz._attached is True

        # Verify handlers are wrapped
        assert window.on_draw != original_draw
        assert window.on_draw is not None

        if original_key_press:
            assert getattr(window, "on_key_press", None) != original_key_press

        if original_mouse_press:
            assert getattr(window, "on_mouse_press", None) != original_mouse_press

        # Verify original handlers are stored
        assert dev_viz._original_on_draw == original_draw
        if original_key_press:
            assert dev_viz._original_on_key_press == original_key_press

        # Detach and verify handlers are restored
        dev_viz.detach_from_window()
        assert window.on_draw == original_draw

    @pytest.mark.integration
    def test_draw_with_openGL_context(self, window):
        """Integration test: Verify draw() works with OpenGL context and doesn't crash."""
        if window is None:
            pytest.skip("No window available")

        # Skip if no OpenGL context (headless CI on Mac/Windows)
        try:
            _ = window.ctx  # Try to access OpenGL context
        except (RuntimeError, AttributeError):
            pytest.skip("No OpenGL context available (headless mode)")

        dev_viz = DevVisualizer()
        dev_viz.attach_to_window(window)
        dev_viz.show()

        # Should not crash
        dev_viz.draw()

        # Hide and verify draw returns early
        dev_viz.hide()
        dev_viz.draw()  # Should return early without drawing

    @pytest.mark.integration
    def test_draw_with_selection(self, window):
        """Integration test: Verify draw() works with selected sprites."""
        if window is None:
            pytest.skip("No window available")

        try:
            _ = window.ctx
        except (RuntimeError, AttributeError):
            pytest.skip("No OpenGL context available (headless mode)")

        dev_viz = DevVisualizer()
        sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.RED)
        dev_viz.scene_sprites.append(sprite)

        dev_viz.attach_to_window(window)
        dev_viz.show()
        # Select sprite by adding it to the selection set
        dev_viz.selection_manager._selected.add(sprite)

        # Should not crash when drawing with selection
        dev_viz.draw()
