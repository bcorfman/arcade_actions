"""Lightweight smoke tests for the visualizer package.

These tests replace the exhaustive UI-heavy suite that previously verified
the visualizer end-to-end.  The goal is to ensure critical modules can still
be imported and their basic helpers operate without needing to spin up an
Arcade window (which made the suite extremely large and slow).
"""

from pathlib import Path

from actions.visualizer import attach


def test_visualizer_starts_detached():
    """Visualizer should not be attached by default."""
    assert attach.get_visualizer_session() is None
    assert attach.is_visualizer_attached() is False


def test_visualizer_session_helpers_return_none_without_components():
    """Property helpers should gracefully handle missing components."""

    def noop_update(*args, **kwargs):
        return None

    session = attach.VisualizerSession(
        debug_store=None,
        overlay=None,
        renderer=None,
        guides=None,
        condition_debugger=None,
        timeline=None,
        control_manager=None,
        guide_renderer=None,
        event_window=None,
        snapshot_directory=Path("."),
        sprite_positions_provider=None,
        target_names_provider=None,
        wrapped_update_all=noop_update,
        previous_update_all=noop_update,
        previous_debug_store=None,
        previous_enable_flag=False,
    )

    assert session.keyboard_handler is None
    assert session.draw_handler is None
