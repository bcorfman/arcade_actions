"""
Attack patterns and group management.
"""

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
    """A high-level controller for managing groups of sprites using conditional actions.

    AttackGroup provides a game-oriented wrapper around SpriteList that leverages
    the conditional action system for lifecycle management, scheduling, and coordinated
    behavior. It accepts any Actions directly rather than wrapping them.

    Key features:
    - Conditional lifecycle management (auto-destroy when empty)
    - Action-based scheduling using any conditional actions
    - Hierarchical relationships with conditional breakaways
    - Formation patterns with any actions
    - Leverages global Action system - just applies actions to groups

    Args:
        sprite_list: The SpriteList to manage
        name: Optional name for debugging and identification
        parent: Optional parent AttackGroup for hierarchical management
        auto_destroy_when_empty: Whether to auto-destroy when no sprites remain

    Example:
        enemies = arcade.SpriteList([enemy1, enemy2, enemy3])
        formation = AttackGroup(enemies, name="enemy_wave_1")

        # Apply formation pattern
        pattern = GridPattern(rows=2, cols=3)
        pattern.apply(formation, start_x=200, start_y=400)

        # Create your own conditional actions and apply them directly
        from actions.conditional import DelayUntil, MoveUntil, FadeUntil, duration_condition

        # Wait 2 seconds, then move formation down at 50 pixels/sec for 1.5 seconds
        delay_action = DelayUntil(duration_condition(2.0))
        move_action = MoveUntil((0, -50), duration_condition(1.5))
        formation.schedule_sequence(delay_action, move_action, tag="movement")

        # Fade out while moving - create your own actions
        fade_action = FadeUntil(-50.0, lambda: any(s.alpha <= 100 for s in enemies))
        formation.schedule_spawn(move_action, fade_action, tag="fade_and_move")

        # Auto-lifecycle management happens via conditional actions
        # No manual update() needed - actions handle everything

        # Clean design: you create Actions, AttackGroup applies them to groups
    """

    def __init__(
        self,
        sprite_list: arcade.SpriteList,
        name: str | None = None,
        parent: Optional["AttackGroup"] = None,
        auto_destroy_when_empty: bool = True,
    ):
        self.sprites = sprite_list
        self.name = name
        self.parent = parent
        self.children: list[AttackGroup] = []
        self.is_destroyed = False

        # Callbacks for lifecycle events
        self.on_destroy_callbacks: list[Callable[[AttackGroup], None]] = []
        self.on_breakaway_callbacks: list[Callable[[AttackGroup], None]] = []

        # Set up conditional lifecycle management if requested
        if auto_destroy_when_empty:
            self._setup_auto_destroy()

    def _setup_auto_destroy(self):
        """Set up conditional action to auto-destroy when empty."""
        from actions.conditional import DelayUntil

        def empty_condition():
            return len(self.sprites) == 0

        def on_empty():
            self.destroy()

        # Create a conditional action that checks for empty state
        auto_destroy_action = DelayUntil(empty_condition, on_empty, check_interval=0.1)
        auto_destroy_action.apply(self.sprites, tag=f"auto_destroy_{id(self)}")

    def apply_action(self, action: Action, tag: str = "group_action") -> Action:
        """Apply any action to all sprites in the group.

        Args:
            action: Any Action to apply to the group's sprites
            tag: Tag for the action (default: "group_action")

        Returns:
            The applied action
        """
        return action.apply(self.sprites, tag=tag)

    def schedule_action(self, delay_seconds: float, action: Action, tag: str = "scheduled") -> Action:
        """Schedule any action to run after a delay.

        Args:
            delay_seconds: Delay in seconds before action starts
            action: Any Action to run after the delay
            tag: Tag for the scheduled action

        Returns:
            The sequence action (delay + main action)
        """
        from actions.composite import Sequence
        from actions.conditional import DelayUntil, duration_condition

        delay_action = DelayUntil(duration_condition(delay_seconds))
        sequence = Sequence(delay_action, action)
        return sequence.apply(self.sprites, tag=tag)

    def schedule_sequence(self, *actions: Action, tag: str = "sequence") -> Action:
        """Schedule a sequence of any actions.

        Args:
            *actions: Any Actions to run in sequence
            tag: Tag for the sequence

        Returns:
            The sequence action
        """
        from actions.composite import Sequence

        sequence = Sequence(*actions)
        return sequence.apply(self.sprites, tag=tag)

    def schedule_spawn(self, *actions: Action, tag: str = "spawn") -> Action:
        """Schedule multiple actions to run in parallel.

        Args:
            *actions: Any Actions to run in parallel
            tag: Tag for the spawn

        Returns:
            The spawn action
        """
        from actions.composite import Spawn

        spawn = Spawn(*actions)
        return spawn.apply(self.sprites, tag=tag)

    def setup_conditional_breakaway(
        self, breakaway_condition: Callable, sprites_to_break: list, tag: str = "breakaway"
    ) -> Action:
        """Set up conditional breakaway using actions.

        Args:
            breakaway_condition: Function returning True when breakaway should happen
            sprites_to_break: List of sprites that should break away
            tag: Tag for the breakaway action

        Returns:
            The breakaway monitoring action
        """
        from actions.conditional import DelayUntil

        def on_breakaway():
            self.breakaway(sprites_to_break)

        breakaway_action = DelayUntil(breakaway_condition, on_breakaway, check_interval=0.1)
        return breakaway_action.apply(self.sprites, tag=tag)

    def breakaway(self, breakaway_sprites: list) -> "AttackGroup":
        """Remove given sprites and create a new AttackGroup.

        Args:
            breakaway_sprites: List of sprites to remove from this group

        Returns:
            New AttackGroup containing the broken away sprites
        """
        # Create new sprite list for breakaway sprites
        new_sprite_list = arcade.SpriteList()

        # Move sprites to new list
        for sprite in breakaway_sprites:
            if sprite in self.sprites:
                self.sprites.remove(sprite)
                new_sprite_list.append(sprite)

        # Create new attack group
        new_group = AttackGroup(
            new_sprite_list,
            name=f"{self.name}_breakaway" if self.name else "breakaway",
            parent=self,
            auto_destroy_when_empty=True,
        )
        self.children.append(new_group)

        # Stop all actions on the sprites that broke away
        for sprite in breakaway_sprites:
            Action.stop(sprite)

        # Notify callbacks
        for callback in self.on_breakaway_callbacks:
            callback(new_group)

        return new_group

    def stop_all_actions(self, tag: str | None = None):
        """Stop all actions on the group's sprites.

        Args:
            tag: If provided, only stop actions with this tag
        """
        if tag:
            Action.stop(self.sprites, tag=tag)
        else:
            Action.stop(self.sprites)

    def pause_all_actions(self, tag: str | None = None):
        """Pause all actions on the group's sprites.

        This requires manually tracking and pausing actions since there's
        no global pause system yet.
        """
        # Get all actions for this sprite list and pause them
        actions = Action.get_tag_actions(tag) if tag else Action._active_actions
        for action in actions:
            if action.target == self.sprites:
                action.pause()

    def resume_all_actions(self, tag: str | None = None):
        """Resume all actions on the group's sprites."""
        # Get all actions for this sprite list and resume them
        actions = Action.get_tag_actions(tag) if tag else Action._active_actions
        for action in actions:
            if action.target == self.sprites:
                action.resume()

    def destroy(self):
        """Destroy the attack group using conditional actions for cleanup."""
        if self.is_destroyed:
            return

        self.is_destroyed = True

        # Stop all actions on our sprites
        self.stop_all_actions()

        # Clear the sprite list
        self.sprites.clear()

        # Notify callbacks
        for callback in self.on_destroy_callbacks:
            callback(self)

        # Clean up references
        self.children.clear()

    def on_destroy(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when the group is destroyed."""
        self.on_destroy_callbacks.append(callback)

    def on_breakaway(self, callback: Callable[["AttackGroup"], None]):
        """Register a callback for when sprites break away."""
        self.on_breakaway_callbacks.append(callback)

    def get_active_actions(self, tag: str | None = None) -> list[Action]:
        """Get all active actions on this group's sprites.

        Args:
            tag: If provided, only return actions with this tag

        Returns:
            List of active actions
        """
        if tag:
            return Action.get_tag_actions(tag, self.sprites)
        else:
            return [action for action in Action._active_actions if action.target == self.sprites]

    @property
    def sprite_count(self) -> int:
        """Get the number of sprites in the group."""
        return len(self.sprites)

    @property
    def is_empty(self) -> bool:
        """Check if the group has no sprites."""
        return len(self.sprites) == 0

    def __repr__(self):
        active_action_count = len(self.get_active_actions())
        return f"<AttackGroup name={self.name} sprites={len(self.sprites)} active_actions={active_action_count}>"


def create_enemy_formation_demo() -> AttackGroup:
    """Create a complete demonstration of AttackGroup using conditional actions.

    This shows how to build complex behaviors using only conditional actions
    and AttackGroup's simplified API.

    Returns:
        Configured AttackGroup ready for action
    """
    import arcade

    from actions.conditional import DelayUntil, FadeUntil, MoveUntil, duration_condition

    # Create enemy sprites
    enemies = arcade.SpriteList()
    for i in range(12):
        enemy = arcade.Sprite(":resources:images/enemies/bee.png", scale=0.5)
        enemy.center_x = 100 + (i % 4) * 80
        enemy.center_y = 500 + (i // 4) * 60
        enemies.append(enemy)

    # Create attack group with conditional lifecycle
    formation = AttackGroup(enemies, name="enemy_wave_1", auto_destroy_when_empty=True)

    # Example 1: Wait 2 seconds, then move formation down
    delay_action = DelayUntil(duration_condition(2.0))
    move_action = MoveUntil((0, -50), duration_condition(3.0))  # velocity (x, y) in pixels/sec
    formation.schedule_sequence(delay_action, move_action, tag="initial_descent")

    # Example 2: Set up conditional breakaway when formation reaches bottom
    def reached_bottom():
        return any(sprite.center_y < 100 for sprite in enemies)

    bottom_sprites = [sprite for sprite in enemies if sprite.center_y < 200]
    formation.setup_conditional_breakaway(reached_bottom, bottom_sprites, tag="bottom_breakaway")

    # Example 3: Fade and move in parallel after initial movement
    fade_action = FadeUntil(-30.0, lambda: enemies[0].alpha <= 100)  # Fade until first sprite is nearly transparent
    move_action2 = MoveUntil((-25, -25), duration_condition(2.0))  # Diagonal retreat

    # Run fade and movement in parallel after initial sequence
    formation.schedule_spawn(fade_action, move_action2, tag="fade_and_move")

    # Example 4: Conditional movement based on sprite count
    def few_sprites_left():
        return len(enemies) <= 3

    # When only a few sprites left, they move faster
    fast_retreat = MoveUntil((100, -100), duration_condition(1.0))
    formation.schedule_action(5.0, fast_retreat, tag="desperate_retreat")

    # Example 5: Register lifecycle callbacks
    def on_formation_destroyed(group):
        print(f"Formation {group.name} was destroyed!")

    def on_sprites_break_away(new_group):
        print(f"Sprites broke away into {new_group.name}")
        # Apply different actions to breakaway group
        panic_action = MoveUntil((200, -200), duration_condition(0.5))
        new_group.apply_action(panic_action, tag="panic")

    formation.on_destroy(on_formation_destroyed)
    formation.on_breakaway(on_sprites_break_away)

    return formation


# Helper functions for common condition patterns
def time_elapsed_condition(seconds: float) -> Callable:
    """Create a condition that becomes true after specified seconds.

    Args:
        seconds: Time in seconds

    Returns:
        Condition function
    """
    import time

    start_time = time.time()
    return lambda: time.time() - start_time >= seconds


def sprite_count_condition(sprite_list: arcade.SpriteList, target_count: int, comparison: str = "<=") -> Callable:
    """Create a condition based on sprite count.

    Args:
        sprite_list: The sprite list to monitor
        target_count: The target count to compare against
        comparison: Comparison operator ("<=", ">=", "==", "<", ">")

    Returns:
        Condition function
    """
    comparisons = {
        "<=": lambda x, y: x <= y,
        ">=": lambda x, y: x >= y,
        "==": lambda x, y: x == y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
    }

    compare_func = comparisons.get(comparison, comparisons["<="])
    return lambda: compare_func(len(sprite_list), target_count)
