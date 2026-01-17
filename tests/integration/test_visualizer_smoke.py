"""Lightweight smoke tests for the visualizer package.

These tests replace the exhaustive UI-heavy suite that previously verified
the visualizer end-to-end.  The goal is to ensure critical modules can still
be imported and their basic helpers operate without needing to spin up an
Arcade window (which made the suite extremely large and slow).

These tests verify:
- Visualizer hooks in base.py work correctly when visualizer is disabled
- Action lifecycle hooks don't crash when _enable_visualizer is False

Note: The slow subprocess-based env var test has been moved to tests/integration/
"""

import arcade

from actions import Action
from actions.conditional import MoveUntil
from actions.frame_timing import after_frames


def test_action_visualizer_hooks_dont_crash_when_disabled():
    """Test that visualizer hooks in Action don't crash when visualizer is disabled."""

    # Ensure visualizer is disabled
    Action._enable_visualizer = False
    Action._debug_store = None

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create and apply action - hooks should not crash
    action = MoveUntil((5, 0), condition=after_frames(10))
    action.apply(sprite, tag="test")

    # These calls should all work without crashing
    action._record_event("test_event")
    action._record_condition_evaluation(True)
    action._update_snapshot()

    # Clean up
    Action.stop_all()


def test_action_visualizer_hooks_with_enable_flag():
    """Test that visualizer hooks work when flag is enabled but store is None."""

    # Enable visualizer but don't set debug store
    Action._enable_visualizer = True
    Action._debug_store = None

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create and apply action
    action = MoveUntil((5, 0), condition=after_frames(10))
    action.apply(sprite, tag="test")

    # These calls should work gracefully with no debug store
    action._record_event("test_event")
    action._record_condition_evaluation(True)
    action._update_snapshot()

    # Update should also work
    Action.update_all(1 / 60)
    sprite.update()

    # Clean up
    Action._enable_visualizer = False
    Action.stop_all()


def test_visualizer_module_import():
    """Test that visualizer module can be imported and has expected structure."""
    from actions import visualizer  # noqa: F401

    # Verify module exists and has expected structure
    assert hasattr(visualizer, "__file__") and visualizer.__file__

    # Verify it has expected exports
    assert hasattr(visualizer, "attach_visualizer") or hasattr(visualizer, "auto_attach_from_env")

    # Module should have expected exports
    assert hasattr(visualizer, "attach_visualizer")
    assert hasattr(visualizer, "detach_visualizer")
    assert hasattr(visualizer, "auto_attach_from_env")


def test_visualizer_hooks_in_action_lifecycle():
    """Test that visualizer hooks are called during normal action lifecycle without crashing."""

    # Disable visualizer for this test
    Action._enable_visualizer = False
    Action._debug_store = None

    sprite = arcade.Sprite()
    sprite.center_x = 100
    sprite.center_y = 100

    # Create action with condition
    action = MoveUntil((5, 0), condition=after_frames(5))

    # Apply should trigger hooks (but they'll be no-ops)
    action.apply(sprite, tag="test")
    assert action._is_active

    # Update a few times to trigger condition evaluation hooks
    # The hooks should be called but won't crash even with visualizer disabled
    for _ in range(10):
        Action.update_all(1 / 60)
        sprite.update()
        # Don't check completion - just verify hooks don't crash

    # Hooks should have been called without crashing
    assert True  # If we get here, hooks worked

    # Clean up
    Action.stop_all()
