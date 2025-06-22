"""
Arcade Actions API - Time-based sprite animation system.

This package provides a comprehensive action system for animating sprites over time.
Actions use time-based calculations (pixels per second) rather than frame-based
calculations for consistent behavior across different frame rates.

Key Classes:
    ActionSprite: A sprite that supports time-based actions
    SpriteGroup: A group of sprites with collision detection and actions
    Game: Base game class with built-in action support

Action Types:
    Movement: MoveBy, MoveTo, BoundaryAction with BounceBehavior/WrapBehavior
    Rotation: RotateBy, RotateTo
    Scaling: ScaleBy, ScaleTo
    Composite: Sequence, Spawn, Loop
    Timing: CallFunc

IMPORTANT: Velocity Unit Differences
----------------------------------
ActionSprite uses TIME-BASED velocity (pixels per second):
    sprite.change_x = 120  # means "120 pixels per second"

arcade.Sprite uses FRAME-BASED velocity (pixels per frame):
    sprite.change_x = 2    # means "2 pixels per frame" (120 pixels/second at 60fps)

Use the helper functions below for conversions when mixing both sprite types.
"""

# Core classes
from .base import Action, ActionSprite, InstantAction, IntervalAction

# Action types
from .composite import Loop, Sequence, Spawn, loop, sequence, spawn
from .game import Game
from .group import SpriteGroup
from .instant import CallFunc, CallFuncS, Hide, Place, Show, ToggleVisibility
from .interval import MoveBy, MoveTo, RotateBy, RotateTo, ScaleBy, ScaleTo
from .move import BounceBehavior, BoundaryAction, BoundsInfo, WrapBehavior
from .protocols import CompositeLike, GroupLike, MovementLike  # re-export for external typing

# Constants
ARCADE_FPS = 60
"""Standard Arcade frame rate used for velocity conversions."""


# Velocity conversion utilities
def arcade_to_actions_velocity(arcade_velocity: float, fps: float = ARCADE_FPS) -> float:
    """Convert arcade.Sprite velocity (pixels/frame) to ActionSprite velocity (pixels/second).

    Args:
        arcade_velocity: Velocity in pixels per frame (arcade.Sprite format)
        fps: Frame rate to use for conversion (default: 60)

    Returns:
        Velocity in pixels per second (ActionSprite format)

    Example:
        # Convert arcade.Sprite velocity to ActionSprite velocity
        arcade_vel = 2.0  # 2 pixels per frame
        actions_vel = arcade_to_actions_velocity(arcade_vel)  # 120 pixels per second
    """
    return arcade_velocity * fps


def actions_to_arcade_velocity(actions_velocity: float, fps: float = ARCADE_FPS) -> float:
    """Convert ActionSprite velocity (pixels/second) to arcade.Sprite velocity (pixels/frame).

    Args:
        actions_velocity: Velocity in pixels per second (ActionSprite format)
        fps: Frame rate to use for conversion (default: 60)

    Returns:
        Velocity in pixels per frame (arcade.Sprite format)

    Example:
        # Convert ActionSprite velocity to arcade.Sprite velocity
        actions_vel = 120.0  # 120 pixels per second
        arcade_vel = actions_to_arcade_velocity(actions_vel)  # 2.0 pixels per frame
    """
    return actions_velocity / fps


# Convenience aliases for common conversions
def fps_to_seconds(frame_velocity: float, fps: float = ARCADE_FPS) -> float:
    """Alias for arcade_to_actions_velocity() - convert frame-based to time-based velocity."""
    return arcade_to_actions_velocity(frame_velocity, fps)


def seconds_to_fps(time_velocity: float, fps: float = ARCADE_FPS) -> float:
    """Alias for actions_to_arcade_velocity() - convert time-based to frame-based velocity."""
    return actions_to_arcade_velocity(time_velocity, fps)


# Convenience functions for boundary behaviors
def BoundedMove(get_bounds, bounce_horizontal=True, bounce_vertical=True, on_bounce=None, movement_action=None):
    """Create a BoundaryAction with bounce behavior (replaces old BoundedMove).

    Args:
        get_bounds: Function returning (left, bottom, right, top) boundaries
        bounce_horizontal: Whether to bounce on horizontal boundaries
        bounce_vertical: Whether to bounce on vertical boundaries
        on_bounce: Optional callback when bounce occurs
        movement_action: Optional movement action to wrap

    Returns:
        BoundaryAction configured with BounceBehavior

    Example:
        # Standalone boundary action:
        action = BoundedMove(lambda: (0, 0, 800, 600))
        sprite.do(action)

        # Wrapping a movement action:
        move = MoveBy((100, 0), 1.0)
        bounded_move = BoundedMove(lambda: (0, 0, 800, 600), movement_action=move)
        sprite.do(bounded_move)
    """
    behavior = BounceBehavior(horizontal=bounce_horizontal, vertical=bounce_vertical, callback=on_bounce)
    return BoundaryAction(get_bounds, behavior, movement_action)


def WrappedMove(get_bounds, wrap_horizontal=True, wrap_vertical=True, on_wrap=None, movement_action=None):
    """Create a BoundaryAction with wrap behavior (replaces old WrappedMove).

    Args:
        get_bounds: Function returning (width, height) screen dimensions
        wrap_horizontal: Whether to wrap on horizontal boundaries
        wrap_vertical: Whether to wrap on vertical boundaries
        on_wrap: Optional callback when wrap occurs
        movement_action: Optional movement action to wrap

    Returns:
        BoundaryAction configured with WrapBehavior

    Example:
        # Standalone boundary action:
        action = WrappedMove(lambda: (800, 600))
        sprite.do(action)

        # Wrapping a movement action:
        move = MoveBy((100, 0), 1.0)
        wrapped_move = WrappedMove(lambda: (800, 600), movement_action=move)
        sprite.do(wrapped_move)
    """
    behavior = WrapBehavior(horizontal=wrap_horizontal, vertical=wrap_vertical, callback=on_wrap)
    return BoundaryAction(get_bounds, behavior, movement_action)


__all__ = [
    # Core classes
    "Action",
    "ActionSprite",
    "Game",
    "SpriteGroup",
    # Action base classes
    "InstantAction",
    "IntervalAction",
    # Composite actions
    "Loop",
    "Sequence",
    "Spawn",
    "loop",
    "sequence",
    "spawn",
    # Instant actions
    "CallFunc",
    "CallFuncS",
    "Hide",
    "Place",
    "Show",
    "ToggleVisibility",
    # Interval actions
    "MoveBy",
    "MoveTo",
    "RotateBy",
    "RotateTo",
    "ScaleBy",
    "ScaleTo",
    # Boundary actions
    "BoundaryAction",
    "BounceBehavior",
    "WrapBehavior",
    "BoundsInfo",
    "BoundedMove",  # Convenience function
    "WrappedMove",  # Convenience function
    # Constants and utilities
    "ARCADE_FPS",
    "arcade_to_actions_velocity",
    "actions_to_arcade_velocity",
    "fps_to_seconds",
    "seconds_to_fps",
]
