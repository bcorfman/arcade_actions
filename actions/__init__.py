"""
ArcadeActions - A declarative action system for Arcade games.

Actions available:
- Movement: MoveUntil with built-in boundary checking
- Rotation: RotateUntil
- Scaling: ScaleUntil
- Visual: FadeUntil, BlinkUntil
- Path: FollowPathUntil
- Timing: DelayUntil, duration, time_elapsed
- Easing: Easing wrapper for smooth acceleration/deceleration effects
- Composition: sequence() and parallel() functions for combining actions
- Formation: arrange_line, arrange_grid, arrange_circle, arrange_v_formation functions
- Condition helpers: sprite_count, time_elapsed
"""

# Core classes
from .base import Action

# Composition functions
from .composite import parallel, sequence

# Conditional actions
from .conditional import (
    BlinkUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    InterpolateUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    duration,
)

# Easing wrappers
from .easing import (
    Easing,
)

# Formation arrangement functions
from .pattern import (
    arrange_circle,
    arrange_grid,
    arrange_line,
    arrange_v_formation,
    sprite_count,
    time_elapsed,
)

__all__ = [
    # Core classes
    "Action",
    # Conditional actions
    "MoveUntil",
    "RotateUntil",
    "ScaleUntil",
    "FadeUntil",
    "BlinkUntil",
    "DelayUntil",
    "FollowPathUntil",
    "duration",
    # Easing wrappers
    "Easing",
    # Composition functions
    "sequence",
    "parallel",
    # Formation arrangement functions
    "arrange_line",
    "arrange_grid",
    "arrange_circle",
    "arrange_v_formation",
    # Condition helpers
    "time_elapsed",
    "sprite_count",
]
