"""Test that F7 step actually moves sprites (reproducing invaders.py issue)."""

from __future__ import annotations

import arcade
import pytest

from arcadeactions import Action, move_until
from arcadeactions.conditional import infinite
from arcadeactions.visualizer import detach_visualizer, get_visualizer_session
from tests.conftest import ActionTestBase


class TestStepMovesSprites(ActionTestBase):
    """Test that stepping with F7 actually moves sprites."""

    def test_step_moves_sprites_like_invaders(self, test_sprite):
        """Reproduce the invaders.py behavior: F6 pauses, F7 steps and moves sprites.

        This test simulates what happens in invaders.py:
        1. Create a sprite with MoveUntil action
        2. Run normally for a few frames
        3. Press F6 to pause
        4. Press F7 to step - sprite should move exactly one frame
        5. Verify sprite position changed appropriately
        """
        # Setup - similar to invaders.py enemy movement
        sprite = test_sprite
        sprite.center_x = 200
        sprite.center_y = 200

        # Create movement action (like enemy_list movement in invaders)
        velocity = (2, 0)  # ENEMY_SPEED from invaders.py
        action = move_until(sprite, velocity=velocity, condition=infinite)

        # Run normally for a few frames (like game running before pause)
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # This is what arcade does in the game loop

        position_before_pause = (sprite.center_x, sprite.center_y)
        frame_before_pause = Action.current_frame()

        # Press F6 to pause
        Action.pause_all()
        assert action._paused

        # Sprite should not move while paused
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()

        assert sprite.center_x == position_before_pause[0]
        assert sprite.center_y == position_before_pause[1]
        assert Action.current_frame() == frame_before_pause  # Frame counter doesn't advance

        # Press F7 to step - THIS IS THE KEY TEST
        # F7 handler calls step_all(), then returns
        Action.step_all(0.016)

        # After F7 handler returns, arcade's main loop calls on_update()
        # on_update() calls Action.update_all() THEN sprite.update()
        # This is the critical order that was broken before the fix
        Action.update_all(0.016)  # Should preserve velocities for this frame
        sprite.update()  # Sprite moves using velocities from step

        # Sprite should have moved exactly one frame
        expected_x = position_before_pause[0] + velocity[0]
        expected_y = position_before_pause[1] + velocity[1]

        assert sprite.center_x == expected_x, (
            f"After step, sprite should move from {position_before_pause[0]} to {expected_x}, but got {sprite.center_x}"
        )
        assert sprite.center_y == expected_y
        assert Action.current_frame() == frame_before_pause + 1

        # After step, sprite should be paused again (not continue moving)
        assert action._paused

        # Verify sprite doesn't continue moving on next frame
        # Next frame: on_update() calls Action.update_all() then sprite.update()
        position_after_step = (sprite.center_x, sprite.center_y)
        Action.update_all(0.016)  # Should clear velocities now
        sprite.update()  # Should not move because velocities are cleared

        assert sprite.center_x == position_after_step[0], (
            "Sprite should stay paused after step, but it continued moving"
        )
        assert sprite.center_y == position_after_step[1]

    @pytest.mark.usefixtures("window")
    def test_step_with_visualizer_attached(self, monkeypatch, window: arcade.Window | None, test_sprite):
        """Test F7 step with visualizer attached (full integration test)."""
        monkeypatch.setenv("ARCADEACTIONS_VISUALIZER", "1")

        try:
            # Clean slate
            try:
                detach_visualizer()
            except Exception:
                pass

            # Setup stub window if needed
            if window is None or not hasattr(window, "show_view"):

                class StubWindow:
                    def __init__(self) -> None:
                        self.handlers: dict[str, object] = {}
                        self._view = None
                        self.width = 800
                        self.height = 600

                    @property
                    def current_view(self):
                        return self._view

                    def push_handlers(self, **handlers: object) -> None:
                        self.handlers.update(handlers)

                    def show_view(self, view) -> None:
                        self._view = view
                        view.window = self

                    def set_visible(self, value: bool) -> None:
                        self.visible = value

                window = StubWindow()
            else:
                if not hasattr(window, "current_view"):
                    monkeypatch.setattr(
                        type(window), "current_view", property(lambda self: getattr(self, "_view", None))
                    )

            arcade.set_window(window)

            # Attach visualizer
            from arcadeactions.visualizer import attach as visualizer_attach

            visualizer_attach._AUTO_ATTACH_ATTEMPTED = False
            visualizer_attach.auto_attach_from_env(force=True)
            session = get_visualizer_session()
            assert session is not None

            # Trigger lazy initialization
            if session.keyboard_handler is None:
                Action.update_all(0.016)
                session = get_visualizer_session()
                assert session is not None

            assert session.keyboard_handler is not None

            # Setup sprite with movement
            sprite = test_sprite
            sprite.center_x = 300
            sprite.center_y = 300

            velocity = (3, 2)
            action = move_until(sprite, velocity=velocity, condition=infinite)

            # Run for a few frames
            for _ in range(5):
                Action.update_all(0.016)
                sprite.update()

            position_before_pause = (sprite.center_x, sprite.center_y)

            # Press F6 to pause
            session.keyboard_handler(arcade.key.F6, 0)
            assert session.control_manager.is_paused
            assert action._paused

            # Press F7 to step
            # F7 handler calls step_all(), then returns
            session.keyboard_handler(arcade.key.F7, 0)

            # After F7 handler, arcade calls on_update()
            # on_update() calls Action.update_all() then sprite.update()
            Action.update_all(0.016)  # Preserves velocities for this frame
            sprite.update()  # Sprite moves

            # Verify sprite moved exactly one frame
            expected_x = position_before_pause[0] + velocity[0]
            expected_y = position_before_pause[1] + velocity[1]

            assert sprite.center_x == expected_x, (
                f"With visualizer, after F7 step, sprite should move from {position_before_pause[0]} "
                f"to {expected_x}, but got {sprite.center_x}"
            )
            assert sprite.center_y == expected_y

            # Should still be paused
            assert session.control_manager.is_paused
            assert action._paused

        finally:
            detach_visualizer()
            # Restore test window
            try:
                from tests.conftest import _global_test_window

                if _global_test_window is not None:
                    arcade.set_window(_global_test_window)
            except (ImportError, AttributeError):
                pass
            monkeypatch.delenv("ARCADEACTIONS_VISUALIZER", raising=False)
