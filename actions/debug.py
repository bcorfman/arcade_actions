from __future__ import annotations

"""Runtime debugging helpers for ArcadeActions.

Currently contains a MotionDebugger action that watches sprites for
single-frame world-space jumps that exceed a configurable threshold and
prints a console message when such an event occurs.
"""

import math
import time

import arcade

from actions.base import Action
from actions.conditional import infinite

__all__ = ["MotionDebugger", "attach_motion_debugger"]


class MotionDebugger(Action):
    """Detect large per-frame jumps in sprite world positions.

    Useful for diagnosing continuity problems when actions are restarted
    (e.g. `_Repeat` cloning) or when patterns mis-compute their offsets.
    """

    def __init__(self, threshold: float = 20.0):
        super().__init__(condition=infinite)
        self.threshold = threshold
        self._prev_positions: dict[int, tuple[float, float]] = {}

    # ---------------- Action hooks ----------------
    def apply_effect(self) -> None:  # noqa: D401 – imperative style
        """Capture initial positions for all bound sprites."""

        def _capture(sprite: arcade.Sprite):
            self._prev_positions[id(sprite)] = (sprite.center_x, sprite.center_y)

        self.for_each_sprite(_capture)

    def update_effect(self, delta_time: float) -> None:  # noqa: D401
        """Check displacements and log if they exceed *threshold*."""

        ts = f"{time.time():.3f}"

        def _check(sprite: arcade.Sprite):
            sid = id(sprite)
            prev = self._prev_positions.get(sid, (sprite.center_x, sprite.center_y))
            dx = sprite.center_x - prev[0]
            dy = sprite.center_y - prev[1]
            jump = math.hypot(dx, dy)
            if jump > self.threshold:
                print(
                    f"[MotionDebugger] t={ts} sprite_id={sid} Δ={jump:.2f}px "
                    f"(threshold={self.threshold}) pos_prev={prev} pos_now={(sprite.center_x, sprite.center_y)}"
                )
            self._prev_positions[sid] = (sprite.center_x, sprite.center_y)

        self.for_each_sprite(_check)

    # No special removal required.
    def clone(self) -> MotionDebugger:  # type: ignore[name-defined]
        return MotionDebugger(self.threshold)


# ---------------- Helper --------------------


def attach_motion_debugger(
    target: arcade.Sprite | arcade.SpriteList, *, threshold: float = 20.0, tag: str | None = "motion_debugger"
) -> MotionDebugger:
    """Convenience helper – apply a MotionDebugger to *target* and return it."""
    dbg = MotionDebugger(threshold)
    dbg.apply(target, tag=tag)
    return dbg
