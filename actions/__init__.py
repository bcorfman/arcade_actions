"""
Arcade Actions API - condition-based animation system.

This package provides an action system that works with Arcade's native sprite system.
Actions use condition-based calculations to abstract away repetitive code that often
needs to be written for each sprite.

Action Types:
    Movement: MoveUntil, MoveWhile, BoundedMove, WrappedMove
    Rotation: RotateUntil, RotateWhile
    Scaling: ScaleUntil, ScaleWhile
    Visual: FadeUntil, FadeWhile, BlinkUntil, BlinkWhile
    Timing: DelayUntil
    Composite: Sequence, Spawn

"""

# Core classes
from .base import Action, GroupAction, SpriteGroup
from .composite import Sequence, Spawn, sequence, spawn

# Action types
from .conditional import (
    BlinkUntil,
    BlinkWhile,
    DelayUntil,
    FadeUntil,
    FadeWhile,
    FollowPathUntil,
    FollowPathWhile,
    MoveUntil,
    MoveWhile,
    RotateUntil,
    RotateWhile,
    ScaleUntil,
    ScaleWhile,
    duration_condition,
)
from .move import BoundedMove, WrappedMove
from .pattern import (
    AttackGroup,
    CirclePattern,
    GridPattern,
    LinePattern,
    VFormationPattern,
    sprite_count_condition,
    time_elapsed_condition,
)

__all__ = [
    # Core classes
    "Action",
    "SpriteGroup",
    "GroupAction",
    # Group management
    "AttackGroup",
    # Formation patterns
    "LinePattern",
    "GridPattern",
    "CirclePattern",
    "VFormationPattern",
    # Conditional actions
    "MoveUntil",
    "MoveWhile",
    "RotateUntil",
    "RotateWhile",
    "ScaleUntil",
    "ScaleWhile",
    "FadeUntil",
    "FadeWhile",
    "BlinkUntil",
    "BlinkWhile",
    "DelayUntil",
    "FollowPathUntil",
    "FollowPathWhile",
    "duration_condition",
    # Composite actions
    "Sequence",
    "Spawn",
    "sequence",
    "spawn",
    # Boundary actions
    "BoundedMove",
    "WrappedMove",
    # Pattern management and helpers
    "time_elapsed_condition",
    "sprite_count_condition",
]
