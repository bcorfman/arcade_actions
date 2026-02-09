"""Compatibility re-exports for conditional action imports."""

from arcadeactions._shared_logging import _debug_log
from arcadeactions.callbacks import CallbackUntil, DelayFrames
from arcadeactions.effects import BlinkUntil, CycleTexturesUntil, EmitParticlesUntil, GlowUntil
from arcadeactions.frame_conditions import _clone_condition, _extract_duration_seconds, infinite
from arcadeactions.movement import MoveUntil, RotateUntil
from arcadeactions.parametric import ParametricMotionUntil
from arcadeactions.paths import FollowPathUntil
from arcadeactions.transforms import FadeTo, FadeUntil, ScaleUntil, TweenUntil

__all__ = [
    "MoveUntil",
    "RotateUntil",
    "ScaleUntil",
    "FadeTo",
    "FadeUntil",
    "BlinkUntil",
    "CallbackUntil",
    "DelayFrames",
    "FollowPathUntil",
    "TweenUntil",
    "CycleTexturesUntil",
    "GlowUntil",
    "EmitParticlesUntil",
    "ParametricMotionUntil",
    "infinite",
    "_clone_condition",
    "_extract_duration_seconds",
    "_debug_log",
]
