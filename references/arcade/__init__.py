"""
The Arcade Library

A Python simple, easy to use module for creating 2D games.
"""

# flake8: noqa: E402
# Error out if we import Arcade with an incompatible version of Python.
import os
import sys
from pathlib import Path
from typing import Final

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 10):
    sys.exit("The Arcade Library requires Python 3.10 or higher.")


def configure_logging(level: int | None = None):
    """Set up basic logging.

    Args:
        level: The log level. Defaults to DEBUG.
    """
    import logging

    level = level or logging.DEBUG
    LOG = logging.getLogger(__name__)
    # Do not add a new handler if we already have one
    if not LOG.handlers:
        LOG.propagate = False
        LOG.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter("%(relativeCreated)s %(name)s %(levelname)s - %(message)s"))
        LOG.addHandler(ch)


# The following is used to load ffmpeg libraries.
# Currently Arcade is only shipping binaries for Mac OS
# as ffmpeg is not needed for support on Windows and Linux.
# However it is setup to load ffmpeg if the binaries are present
# on Windows and Linux. So if you need ffmpeg you can simply
# drop the binaries in the "lib" folder of Arcade
lib_location = Path(__file__).parent.absolute()
lib_location = lib_location / "lib"

if sys.platform == "darwin" or sys.platform.startswith("linux"):
    if "LD_LIBRARY_PATH" in os.environ:
        os.environ["LD_LIBRARY_PATH"] += ":" + str(lib_location)
    else:
        os.environ["LD_LIBRARY_PATH"] = str(lib_location)
else:
    os.environ["PATH"] += str(lib_location)

import pyglet

# Enable HiDPI support using stretch mode
if os.environ.get("ARCADE_TEST"):
    pyglet.options.dpi_scaling = "real"
else:
    pyglet.options.dpi_scaling = "stretch"

# Env variable shortcut for headless mode
headless: Final[bool] = bool(os.environ.get("ARCADE_HEADLESS"))
if headless:
    pyglet.options.headless = headless


# from arcade import utils
# Disable shadow window on macs and in headless mode.
# if sys.platform == "darwin" or os.environ.get("ARCADE_HEADLESS") or utils.is_raspberry_pi():
# NOTE: We always disable shadow window now to have consistent behavior across platforms.
pyglet.options.shadow_window = False

# Imports from modules that don't do anything circular

# Complex imports with potential circularity
from .application import (
    MOUSE_BUTTON_LEFT,
    MOUSE_BUTTON_MIDDLE,
    MOUSE_BUTTON_RIGHT,
    NoOpenGLException,
    View,
    Window,
    get_screens,
    open_window,
)
from .draw import (
    draw_arc_filled,
    draw_arc_outline,
    draw_circle_filled,
    draw_circle_outline,
    draw_ellipse_filled,
    draw_ellipse_outline,
    draw_lbwh_rectangle_filled,
    draw_lbwh_rectangle_outline,
    draw_line,
    draw_line_strip,
    draw_lines,
    draw_lrbt_rectangle_filled,
    draw_lrbt_rectangle_outline,
    draw_parabola_filled,
    draw_parabola_outline,
    draw_point,
    draw_points,
    draw_polygon_filled,
    draw_polygon_outline,
    draw_rect_filled,
    draw_rect_outline,
    draw_sprite,
    draw_sprite_rect,
    draw_texture_rect,
    draw_triangle_filled,
    draw_triangle_outline,
    get_points_for_thick_line,
)
from .screenshot import get_image, get_pixel
from .sections import Section, SectionManager
from .texture import (
    SpriteSheet,
    Texture,
    TextureCacheManager,
    get_default_image,
    get_default_texture,
    load_image,
    load_spritesheet,
    load_texture,
    make_circle_texture,
    make_soft_circle_texture,
    make_soft_square_texture,
)
from .window_commands import (
    close_window,
    exit,
    finish_render,
    get_display_size,
    get_window,
    run,
    schedule,
    schedule_once,
    set_background_color,
    set_window,
    start_render,
    unschedule,
)

# We don't have joysticks game controllers in headless mode
if not headless:
    from .controller import ControllerManager, get_controllers
    from .joysticks import get_game_controllers, get_joysticks

# For ease of access for beginners
from pyglet.math import Vec2, Vec3, Vec4

from arcade import camera as camera

# Module imports
from arcade import color as color
from arcade import csscolor as csscolor
from arcade import experimental as experimental
from arcade import hitbox as hitbox
from arcade import key as key
from arcade import math as math
from arcade import resources as resources
from arcade import shape_list as shape_list
from arcade import types as types
from arcade import uicolor as uicolor
from arcade.types import rect

from .camera import Camera2D
from .context import ArcadeContext
from .paths import AStarBarrierList, astar_calculate_path, has_line_of_sight
from .perf_graph import PerfGraph
from .perf_info import (
    clear_timings,
    disable_timings,
    enable_timings,
    get_fps,
    get_timings,
    print_timings,
    timings_enabled,
)
from .physics_engines import PhysicsEnginePlatformer, PhysicsEngineSimple
from .pymunk_physics_engine import PymunkException, PymunkPhysicsEngine, PymunkPhysicsObject
from .scene import Scene, SceneKeyError
from .sound import Sound, load_sound, play_sound, stop_sound

# from .sprite import SimpleSprite
from .sprite import (
    FACE_DOWN,
    FACE_LEFT,
    FACE_RIGHT,
    FACE_UP,
    AnimatedWalkingSprite,
    BasicSprite,
    PyMunk,
    PymunkMixin,
    Sprite,
    SpriteCircle,
    SpriteSolidColor,
    SpriteType,
    SpriteType_co,
    TextureAnimation,
    TextureAnimationSprite,
    TextureKeyframe,
    load_animated_gif,
)
from .sprite_list import (
    SpatialHash,
    SpriteList,
    SpriteSequence,
    check_for_collision,
    check_for_collision_with_list,
    check_for_collision_with_lists,
    get_closest_sprite,
    get_distance_between_sprites,
    get_sprites_at_exact_point,
    get_sprites_at_point,
    get_sprites_in_rect,
)
from .text import (
    Text,
    create_text_sprite,
    draw_text,
    load_font,
)
from .texture_atlas import DefaultTextureAtlas
from .tilemap import TileMap, load_tilemap
from .types.rect import LBWH, LRBT, XYWH, Rect
from .version import VERSION

__all__ = [
    "AStarBarrierList",
    "AnimatedWalkingSprite",
    "TextureAnimationSprite",
    "TextureAnimation",
    "TextureKeyframe",
    "ArcadeContext",
    "ControllerManager",
    "FACE_DOWN",
    "FACE_LEFT",
    "FACE_RIGHT",
    "FACE_UP",
    "MOUSE_BUTTON_LEFT",
    "MOUSE_BUTTON_MIDDLE",
    "MOUSE_BUTTON_RIGHT",
    "NoOpenGLException",
    "PerfGraph",
    "PhysicsEnginePlatformer",
    "PhysicsEngineSimple",
    "PyMunk",
    "PymunkException",
    "PymunkPhysicsEngine",
    "PymunkPhysicsObject",
    "Rect",
    "LBWH",
    "LRBT",
    "XYWH",
    "Section",
    "SectionManager",
    "Scene",
    "SceneKeyError",
    "Sound",
    "BasicSprite",
    "Sprite",
    "SpriteType",
    "SpriteType_co",
    "PymunkMixin",
    "SpriteCircle",
    "SpriteList",
    "SpriteSequence",
    "SpriteSolidColor",
    "Text",
    "Texture",
    "TextureCacheManager",
    "SpriteSheet",
    "DefaultTextureAtlas",
    "TileMap",
    "VERSION",
    "Vec2",
    "Vec3",
    "Vec4",
    "View",
    "Window",
    "astar_calculate_path",
    "check_for_collision",
    "check_for_collision_with_list",
    "check_for_collision_with_lists",
    "close_window",
    "disable_timings",
    "draw_arc_filled",
    "draw_arc_outline",
    "draw_circle_filled",
    "draw_circle_outline",
    "draw_ellipse_filled",
    "draw_ellipse_outline",
    "draw_line",
    "draw_line_strip",
    "draw_lines",
    "draw_lrbt_rectangle_filled",
    "draw_lrbt_rectangle_filled",
    "draw_lrbt_rectangle_outline",
    "draw_lrbt_rectangle_outline",
    "draw_parabola_filled",
    "draw_parabola_outline",
    "draw_point",
    "draw_points",
    "draw_polygon_filled",
    "draw_polygon_outline",
    "draw_rect_filled",
    "draw_rect_outline",
    "draw_text",
    "draw_texture_rect",
    "draw_sprite",
    "draw_sprite_rect",
    "draw_triangle_filled",
    "draw_triangle_outline",
    "draw_lbwh_rectangle_filled",
    "draw_lbwh_rectangle_outline",
    "enable_timings",
    "exit",
    "finish_render",
    "get_closest_sprite",
    "get_display_size",
    "get_distance_between_sprites",
    "get_sprites_in_rect",
    "get_controllers",
    "get_game_controllers",
    "get_image",
    "get_joysticks",
    "get_pixel",
    "get_points_for_thick_line",
    "get_screens",
    "get_sprites_at_exact_point",
    "get_sprites_at_point",
    "SpatialHash",
    "get_timings",
    "create_text_sprite",
    "clear_timings",
    "get_window",
    "get_fps",
    "has_line_of_sight",
    "load_animated_gif",
    "load_font",
    "load_sound",
    "load_spritesheet",
    "load_texture",
    "load_image",
    "make_circle_texture",
    "make_soft_circle_texture",
    "make_soft_square_texture",
    "open_window",
    "print_timings",
    "play_sound",
    "load_tilemap",
    "run",
    "schedule",
    "set_background_color",
    "set_window",
    "start_render",
    "stop_sound",
    "timings_enabled",
    "unschedule",
    "schedule_once",
    "get_default_texture",
    "get_default_image",
    "hitbox",
    "experimental",
    "rect",
    "color",
    "csscolor",
    "uicolor",
    "key",
    "resources",
    "types",
    "math",
    "shape_list",
    "Camera2D",
]

__version__ = VERSION

# Piggyback on pyglet's doc run detection
if not getattr(sys, "is_pyglet_doc_run", False):
    # Load additional game controller mappings to Pyglet
    if not headless:
        try:
            import pyglet.input.controller

            mappings_file = resources.resolve(":system:gamecontrollerdb.txt")
            # TODO: remove string conversion once fixed upstream
            pyglet.input.controller.add_mappings_from_file(str(mappings_file))
        except AssertionError:
            pass
