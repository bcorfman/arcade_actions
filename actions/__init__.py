"""
ArcadeActions - A declarative action system for Arcade games.

Actions available:
- Movement: MoveUntil with built-in boundary checking
- Rotation: RotateUntil
- Scaling: ScaleUntil
- Visual: FadeUntil, BlinkUntil
- Path: FollowPathUntil
- Timing: DelayUntil, duration, time_elapsed
- Easing: Ease wrapper for smooth acceleration/deceleration effects
- Interpolation: TweenUntil for direct property animation from start to end value
- Composition: sequence() and parallel() functions for combining actions
- Formation: arrange_line, arrange_grid, arrange_circle, arrange_v_formation, arrange_diamond,
            arrange_triangle, arrange_hexagonal_grid, arrange_arc, arrange_concentric_rings,
            arrange_cross, arrange_arrow functions
- Movement Patterns: create_zigzag_pattern, create_wave_pattern, create_spiral_pattern, etc.
- Condition helpers: sprite_count, time_elapsed
- Experimental: SpritePool for zero-allocation gameplay
"""

# Core classes
from .base import Action

# Composition functions
from .composite import parallel, repeat, sequence

# Conditional actions
from .conditional import (
    BlinkUntil,
    CallbackUntil,
    CycleTexturesUntil,
    DelayUntil,
    EmitParticlesUntil,
    FadeUntil,
    FollowPathUntil,
    GlowUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    TweenUntil,
    duration,
    infinite,
)
from .axis_move import MoveXUntil, MoveYUntil
from .config import (
    apply_environment_configuration,
    clear_observed_actions,
    get_debug_actions,
    get_debug_options,
    observe_actions,
    set_debug_actions,
    set_debug_options,
)

# Display utilities
from .display import center_window

# Easing wrappers
from .easing import (
    Ease,
)

# Formation arrangement functions - LAZY LOADED (see __getattr__ below)
# from .formation import (...)

# Helper functions
from .helpers import (
    blink_until,
    callback_until,
    emit_particles_until,
    cycle_textures_until,
    delay_until,
    ease,
    glow_until,
    fade_until,
    follow_path_until,
    move_by,
    move_to,
    move_until,
    move_x_until,
    move_y_until,
    rotate_until,
    scale_until,
    tween_until,
)

# Instant actions
from .instant import MoveBy, MoveTo

# Movement patterns and condition helpers - LAZY LOADED (see __getattr__ below)
# from .pattern import (...)

# Experimental pools module
from .pools import SpritePool

__all__ = [
    # Core classes
    "Action",
    # Configuration
    "set_debug_actions",
    "get_debug_actions",
    "apply_environment_configuration",
    "set_debug_options",
    "get_debug_options",
    "observe_actions",
    "clear_observed_actions",
    # Conditional actions
    "MoveUntil",
    "MoveXUntil",
    "MoveYUntil",
    "RotateUntil",
    "ScaleUntil",
    "FadeUntil",
    "BlinkUntil",
    "CallbackUntil",
    "DelayUntil",
    "FollowPathUntil",
    "TweenUntil",
    "CycleTexturesUntil",
    "GlowUntil",
    "EmitParticlesUntil",
    "duration",
    "infinite",
    # Instant actions
    "MoveTo",
    "MoveBy",
    # Easing wrappers
    "Ease",
    # Composition functions
    "sequence",
    "parallel",
    "repeat",
    # Formation arrangement functions
    "arrange_arc",
    "arrange_arrow",
    "arrange_circle",
    "arrange_concentric_rings",
    "arrange_cross",
    "arrange_diamond",
    "arrange_grid",
    "arrange_hexagonal_grid",
    "arrange_line",
    "arrange_triangle",
    "arrange_v_formation",
    # Movement patterns
    "create_formation_entry_from_sprites",
    "create_zigzag_pattern",
    "create_wave_pattern",
    "create_spiral_pattern",
    "create_figure_eight_pattern",
    "create_orbit_pattern",
    "create_bounce_pattern",
    "create_patrol_pattern",
    # Condition helpers
    "time_elapsed",
    "sprite_count",
    # Helper functions
    "move_by",
    "move_to",
    "move_until",
    "move_x_until",
    "move_y_until",
    "rotate_until",
    "follow_path_until",
    "blink_until",
    "callback_until",
    "emit_particles_until",
    "delay_until",
    "tween_until",
    "scale_until",
    "fade_until",
    "cycle_textures_until",
    "ease",
    "glow_until",
    # display
    "center_window",
    # experimental pools
    "SpritePool",
]

# Apply environment-driven configuration at import time so applications can
# enable debugging via ARCADEACTIONS_DEBUG without additional code changes.
# This remains opt-in and side-effect free beyond toggling debug output.
apply_environment_configuration()


# Lazy loading for formation and pattern modules to avoid pulling in arcade
# until these functions are actually used
_LAZY_IMPORTS = {
    # Formation functions
    "arrange_arc": "formation",
    "arrange_arrow": "formation",
    "arrange_circle": "formation",
    "arrange_concentric_rings": "formation",
    "arrange_cross": "formation",
    "arrange_diamond": "formation",
    "arrange_grid": "formation",
    "arrange_hexagonal_grid": "formation",
    "arrange_line": "formation",
    "arrange_triangle": "formation",
    "arrange_v_formation": "formation",
    # Pattern functions
    "create_bounce_pattern": "pattern",
    "create_figure_eight_pattern": "pattern",
    "create_formation_entry_from_sprites": "pattern",
    "create_orbit_pattern": "pattern",
    "create_patrol_pattern": "pattern",
    "create_spiral_pattern": "pattern",
    "create_wave_pattern": "pattern",
    "create_zigzag_pattern": "pattern",
    "sprite_count": "pattern",
    "time_elapsed": "pattern",
}


def __getattr__(name: str):
    """Lazy-load formation and pattern modules to avoid importing arcade until needed."""
    if name in _LAZY_IMPORTS:
        module_name = _LAZY_IMPORTS[name]
        if module_name == "formation":
            from . import formation

            return getattr(formation, name)
        elif module_name == "pattern":
            from . import pattern

            return getattr(pattern, name)
    raise AttributeError(f"module 'actions' has no attribute '{name}'")
