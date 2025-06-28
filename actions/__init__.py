"""
Arcade Actions API - condition-based animation system.

This package provides an action system that works with Arcade's native sprite system.
Actions use condition-based calculations to abstract away repetitive code that often
needs to be written for each sprite.

Action Types:
    Movement: MoveUntil, MoveWhile, BoundedMove, WrappedMove
    Rotation: RotateUntil, RotateWhile
    Scaling: ScaleUntil, ScaleWhile
    Composite: Sequence, Spawn

"""

# Core classes
from .base import Action

# Action types
from .composite import Sequence, Spawn, sequence, spawn
from .move import BoundedMove, WrappedMove
from .pattern import AttackGroup, CirclePattern, GridPattern, LinePattern, VFormationPattern

__all__ = [
    # Core classes
    "Action",
    # Group management
    "AttackGroup",
    # Formation patterns
    "LinePattern",
    "GridPattern",
    "CirclePattern",
    "VFormationPattern",
    # Composite actions
    "Sequence",
    "Spawn",
    "sequence",
    "spawn",
    # Boundary actions
    "BoundedMove",
    "WrappedMove",
]
