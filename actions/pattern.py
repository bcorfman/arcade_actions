import math
from collections.abc import Callable
from typing import Optional

import arcade

from actions.base import Action


class _Pattern:
    """Base class for attack patterns."""

    def __init__(self, name: str):
        self.name = name

    def apply(self, attack_group: "AttackGroup", *args, **kwargs):
        raise NotImplementedError("Subclasses must implement apply()")


class LinePattern(_Pattern):
    """Pattern for arranging sprites in a horizontal line.

    Positions sprites in a straight line with configurable spacing between them.
    Useful for creating horizontal formations, bullet patterns, or UI elements.

    Args:
        spacing: Distance between sprite centers in pixels (default: 50.0)

    Example:
        pattern = LinePattern(spacing=80.0)
        pattern.apply(attack_group, start_x=100, start_y=300)
        # Sprites positioned at (100,300), (180,300), (260,300), etc.
    """

    def __init__(self, spacing: float = 50.0):
        super().__init__("line")
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", start_x: float = 0, start_y: float = 0):
        """Apply line pattern to the attack group."""
        for i, sprite in enumerate(attack_group.sprites):
            sprite.center_x = start_x + i * self.spacing
            sprite.center_y = start_y


class GridPattern(_Pattern):
    """Pattern for arranging sprites in a rectangular grid formation.

    Creates rows and columns of sprites with configurable spacing.
    Perfect for Space Invaders-style enemy formations or organized layouts.

    Args:
        rows: Number of rows in the grid (default: 5)
        cols: Number of columns in the grid (default: 10)
        spacing_x: Horizontal spacing between sprites in pixels (default: 60.0)
        spacing_y: Vertical spacing between sprites in pixels (default: 50.0)

    Example:
        pattern = GridPattern(rows=3, cols=5, spacing_x=80, spacing_y=60)
        pattern.apply(attack_group, start_x=200, start_y=400)
        # Creates 3x5 grid starting at (200,400)
    """

    def __init__(self, rows: int = 5, cols: int = 10, spacing_x: float = 60.0, spacing_y: float = 50.0):
        super().__init__("grid")
        self.rows = rows
        self.cols = cols
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

    def apply(self, attack_group: "AttackGroup", start_x: float = 100, start_y: float = 500):
        """Apply grid pattern to the attack group."""
        for i, sprite in enumerate(attack_group.sprites):
            row = i // self.cols
            col = i % self.cols
            sprite.center_x = start_x + col * self.spacing_x
            sprite.center_y = start_y - row * self.spacing_y


class CirclePattern(_Pattern):
    """Pattern for arranging sprites in a circular formation.

    Distributes sprites evenly around a circle with configurable radius.
    Great for radial bullet patterns or defensive formations.

    Args:
        radius: Radius of the circle in pixels (default: 100.0)

    Example:
        pattern = CirclePattern(radius=150.0)
        pattern.apply(attack_group, center_x=400, center_y=300)
        # Sprites arranged in circle around (400,300) with radius 150
    """

    def __init__(self, radius: float = 100.0):
        super().__init__("circle")
        self.radius = radius

    def apply(self, attack_group: "AttackGroup", center_x: float = 400, center_y: float = 300):
        """Apply circle pattern to the attack group."""
        count = len(attack_group.sprites)
        if count == 0:
            return

        angle_step = 2 * math.pi / count
        for i, sprite in enumerate(attack_group.sprites):
            angle = i * angle_step
            sprite.center_x = center_x + math.cos(angle) * self.radius
            sprite.center_y = center_y + math.sin(angle) * self.radius


class VFormationPattern(_Pattern):
    """Pattern for arranging sprites in a V or wedge formation.

    Creates a V-shaped formation with one sprite at the apex and others
    arranged alternately on left and right sides. Useful for flying formations
    or arrow-like attack patterns.

    Args:
        angle: Angle of the V formation in degrees (default: 45.0)
        spacing: Distance between sprites in the formation (default: 50.0)

    Example:
        pattern = VFormationPattern(angle=30.0, spacing=60.0)
        pattern.apply(attack_group, apex_x=400, apex_y=500)
        # Creates V formation with apex at (400,500)
    """

    def __init__(self, angle: float = 45.0, spacing: float = 50.0):
        super().__init__("v_formation")
        self.angle = math.radians(angle)
        self.spacing = spacing

    def apply(self, attack_group: "AttackGroup", apex_x: float = 400, apex_y: float = 500):
        """Apply V formation pattern to the attack group."""
        sprites = list(attack_group.sprites)
        count = len(sprites)
        if count == 0:
            return

        # Place the first sprite at the apex
        sprites[0].center_x = apex_x
        sprites[0].center_y = apex_y

        # Place remaining sprites alternating on left and right sides
        for i in range(1, count):
            side = 1 if i % 2 == 1 else -1  # Alternate sides
            distance = (i + 1) // 2 * self.spacing

            offset_x = side * math.cos(self.angle) * distance
            offset_y = -math.sin(self.angle) * distance

            sprites[i].center_x = apex_x + offset_x
            sprites[i].center_y = apex_y + offset_y


class AttackGroup:
    """A high-level controller for managing groups of sprites with attack patterns.

    AttackGroup provides a game-oriented wrapper around SpriteGroup with additional
    features for managing sprite lifecycles, attack patterns, scheduling, and hierarchical
    group relationships. It's designed for complex game scenarios like enemy formations,
    bullet patterns, and coordinated attacks.

    Key features:
    - Automatic lifecycle management (birth time, destruction)
    - Attack pattern application (LinePattern, GridPattern, etc.)
    - Event scheduling for delayed actions
    - Hierarchical relationships (parent/child groups)
    - Breakaway mechanics for dynamic group splitting
    - Pause/resume support

    Args:
        sprite_group: The SpriteGroup to manage
        name: Optional name for debugging and identification
        parent: Optional parent AttackGroup for hierarchical management

    Example:
        enemies = SpriteGroup([enemy1, enemy2, enemy3])
        formation = AttackGroup(enemies, name="enemy_wave_1")

        # Apply formation pattern
        pattern = GridPattern(rows=2, cols=3)
        pattern.apply(formation, start_x=200, start_y=400)

        # Schedule coordinated movement
        formation.schedule_attack(2.0, formation.do, MoveBy((100, -50), 1.5))

        # Update in game loop
        formation.update(delta_time)
    """

    def __init__(
        self,
        sprite_group: "SpriteGroup",
        name: str | None = None,
        parent: Optional["AttackGroup"] = None,
    ):
        self.sprites = sprite_group
        self.time_of_birth = arcade.clock.GLOBAL_CLOCK.time
        self.is_destroyed = False
        self.name = name
        self._scheduled_wrappers: list[tuple[Callable, bool]] = []  # (wrapper, repeat)
        self.actions: list[Action] = []  # Track running group actions
        self.parent = parent
        self.children: list[AttackGroup] = []  # Child attack groups
        self.on_destroy_callbacks: list[Callable[[AttackGroup], None]] = []
        self.on_breakaway_callbacks: list[Callable[[AttackGroup], None]] = []
        self._paused = False

    def update(self, delta_time: float):
        """Update the attack group and its actions."""
        if self._paused:
            return

        self.sprites.update(delta_time)
        for wrapper, _ in self._scheduled_wrappers:
            wrapper(delta_time)

        for action in self.actions:
            action.update(delta_time)

        if len(self.sprites) == 0:
            self.destroy()

    def do(self, action: Action) -> Action:
        """Assign an action to all sprites in the group - SAME INTERFACE as individual sprites."""
        group_action = self.sprites.do(action)
        # Track and handle pause
        self.actions.append(group_action)
        if self._paused:
            group_action.pause()
        return group_action

    def schedule_attack(self, delay: float, func: Callable, *args, **kwargs) -> int:
        """Schedule an attack event after X seconds."""

        # Implement scheduling via arcade.schedule_once
        def _wrapper(_dt):
            func(*args, **kwargs)

        arcade.schedule_once(_wrapper, delay)
        self._scheduled_wrappers.append((_wrapper, False))
        return len(self._scheduled_wrappers) - 1

    def breakaway(self, breakaway_sprites: list) -> "AttackGroup":
        """Remove given sprites and create a new AttackGroup."""
        new_sprite_group = self.sprites.breakaway(breakaway_sprites)
        new_group = AttackGroup(
            new_sprite_group,
            name=f"{self.name}_breakaway",
            parent=self,
        )
        self.children.append(new_group)
        # Unschedule arcade callbacks
        for wrapper, _ in self._scheduled_wrappers:
            arcade.unschedule(wrapper)
        self._scheduled_wrappers.clear()
        # Stop running actions
        for action in self.actions:
            action.stop()
        self.actions.clear()
        for callback in self.on_breakaway_callbacks:
            callback(new_group)
        return new_group

    def destroy(self):
        """Clean up resources."""
        if self.is_destroyed:
            return
        self.is_destroyed = True
        # Stop all actions
        for action in self.actions:
            action.stop()
        self.actions.clear()
        # Notify callbacks
        for callback in self.on_destroy_callbacks:
            callback(self)

    def on_destroy(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when the group is destroyed."""
        self.on_destroy_callbacks.append(callback)

    def on_breakaway(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when sprites break away."""
        self.on_breakaway_callbacks.append(callback)

    def __repr__(self):
        return f"<AttackGroup name={self.name} sprites={len(self.sprites)} actions={len(self.actions)}>"
