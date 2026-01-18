"""AttackGroup system for synchronized sprite formations and coordinated actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade

    from arcadeactions.base import Action
    from arcadeactions.group_state import BreakawayManager
else:
    arcade = None  # type: ignore
    Action = Any
    BreakawayManager = Any


def _log_group_metrics(group: AttackGroup, delta_time: float) -> None:
    """Log group metrics for debug telemetry (level 2+)."""
    from arcadeactions.base import Action

    if Action.debug_level < 2:
        return

    # Check if AttackGroup is in debug filter
    if not Action.debug_all:
        include = Action.debug_include_classes
        if include and "AttackGroup" not in include:
            return

    # Log basic metrics
    breakaway_count = 0
    if group._breakaway_manager:
        breakaway_count = len(group._breakaway_manager.breakaway_sprites)

    print(
        f"[AA L2 AttackGroup] id={group.group_id}, sprites={len(group.sprites)}, "
        f"formation={group.formation_type}, breakaway_count={breakaway_count}"
    )


class AttackGroup:
    """Manages a group of sprites in a synchronized formation with coordinated actions.

    AttackGroup wraps a SpriteList and provides:
    - Formation placement (grid, line, V-formation, etc.)
    - Synchronized action scripts applied to all sprites
    - Breakaway behaviors (sprites detach for attacks, then return)
    - Path-based entry sequences (leader/follower patterns)

    Args:
        sprites: SpriteList or list of sprites to manage
        group_id: Optional identifier for this group (used in YAML export/import)

    Example:
        # Create group and place in formation
        sprites = arcade.SpriteList()
        for _ in range(10):
            sprites.append(arcade.Sprite(":resources:images/items/star.png"))

        group = AttackGroup(sprites, group_id="wave1")
        group.place(arrange_grid, rows=2, cols=5, start_x=100, start_y=400)

        # Apply synchronized movement
        from arcadeactions.conditional import MoveUntil
        from arcadeactions.frame_timing import after_frames
        move = MoveUntil((2, 0), after_frames(60))
        group.script(move, tag="patrol")
    """

    def __init__(self, sprites: arcade.SpriteList | list[arcade.Sprite], group_id: str | None = None):
        import arcade

        # Convert list to SpriteList if needed
        if isinstance(sprites, list):
            sprite_list = arcade.SpriteList()
            for sprite in sprites:
                sprite_list.append(sprite)
            sprites = sprite_list

        self.sprites = sprites
        self.group_id = group_id
        self.formation_type: str | None = None
        self._home_slots: dict[int, tuple[float, float]] = {}  # sprite_id -> (x, y)
        self._breakaway_manager: BreakawayManager | None = None

    def place(
        self,
        formation_fn: Callable[..., arcade.SpriteList],
        **kwargs: Any,
    ) -> None:
        """Place sprites in a formation and record home slot coordinates.

        Args:
            formation_fn: Formation function from arcadeactions.formation (e.g., arrange_grid, arrange_line)
            **kwargs: Parameters passed to formation_fn

        Example:
            group.place(arrange_grid, rows=3, cols=5, start_x=100, start_y=400)
            group.place(arrange_line, start_x=0, start_y=300, spacing=50)
        """
        # Determine formation type from function name
        fn_name = formation_fn.__name__
        if fn_name.startswith("arrange_"):
            self.formation_type = fn_name[8:]  # Remove "arrange_" prefix
        else:
            self.formation_type = fn_name

        # Apply formation
        formation_fn(self.sprites, **kwargs)

        # Record home slots for each sprite
        self._home_slots.clear()
        for sprite in self.sprites:
            self._home_slots[id(sprite)] = (sprite.center_x, sprite.center_y)

    def script(self, action: Action, tag: str | None = None) -> None:
        """Apply a synchronized action script to all sprites in the group.

        The action is applied to the entire SpriteList, so all sprites move together.

        Args:
            action: Action to apply (can be a single action or composite)
            tag: Optional tag for the action

        Example:
            from arcadeactions.conditional import MoveUntil
            from arcadeactions.frame_timing import after_frames
            move = MoveUntil((5, 0), after_frames(60))
            group.script(move, tag="patrol")
        """
        action.apply(self.sprites, tag=tag)

    def update(self, delta_time: float) -> None:
        """Update breakaway manager for this group.

        Note: This does NOT call Action.update_all() - that should be called once
        per frame at the top level of your game loop. This method only updates
        the breakaway manager state.

        Args:
            delta_time: Time elapsed since last update (in seconds)
        """
        from arcadeactions.base import Action

        # Update breakaway manager if present
        if self._breakaway_manager:
            self._breakaway_manager.update(delta_time)

        # Debug telemetry (level 2+)
        if Action.debug_level >= 2:
            _log_group_metrics(self, delta_time)

    def get_home_slot(self, sprite: arcade.Sprite) -> tuple[float, float] | None:
        """Get the home slot coordinates for a sprite.

        Args:
            sprite: Sprite to look up

        Returns:
            (x, y) coordinates of home slot, or None if not found
        """
        return self._home_slots.get(id(sprite))

    def set_breakaway_manager(self, manager: Any) -> None:
        """Set the breakaway manager for this group.

        Args:
            manager: BreakawayManager instance (from group_state module)
        """
        self._breakaway_manager = manager

    def get_breakaway_manager(self) -> Any:
        """Get the breakaway manager for this group.

        Returns:
            BreakawayManager instance, or None if not set
        """
        return self._breakaway_manager

    def entry_path(
        self,
        leader_path: list[tuple[float, float]],
        velocity: float = 150.0,
        spacing_frames: int = 5,
        tag: str | None = None,
    ) -> None:
        """Create a path-based entry sequence with leader/follower pattern.

        The first sprite (leader) follows the path immediately. Each follower
        sprite waits a delay (spacing_frames * follower_index) before starting
        the same path. At path completion, each sprite tweens to its home slot.

        Args:
            leader_path: List of waypoints for FollowPathUntil
            velocity: Speed along the path (pixels per second)
            spacing_frames: Frames between each follower starting the path
            tag: Optional tag for the entry actions

        Example:
            from arcadeactions.presets.entry_paths import loop_the_loop
            path = loop_the_loop(start_x=400, start_y=-100, end_x=400, end_y=500)
            group.entry_path(path, velocity=150, spacing_frames=5)
        """
        from arcadeactions.composite import parallel, sequence
        from arcadeactions.conditional import FollowPathUntil, TweenUntil, infinite
        from arcadeactions.frame_timing import after_frames, seconds_to_frames

        if not self.sprites:
            return

        # Leader sprite: FollowPathUntil then TweenUntil to home slot
        leader = self.sprites[0]
        leader_home = self.get_home_slot(leader)
        if leader_home:
            # Use infinite condition - FollowPathUntil will complete automatically
            # when it reaches the end of the path (_curve_progress >= 1.0)
            leader_path_action = FollowPathUntil(
                leader_path.copy(),
                velocity,
                infinite,
            )
            # Use lambda to capture sprite position when tween starts (after path completes)
            leader_return_x = TweenUntil(
                lambda sprite: sprite.center_x,
                leader_home[0],
                "center_x",
                after_frames(seconds_to_frames(0.5)),
            )
            leader_return_y = TweenUntil(
                lambda sprite: sprite.center_y,
                leader_home[1],
                "center_y",
                after_frames(seconds_to_frames(0.5)),
            )
            leader_sequence = sequence(leader_path_action, parallel(leader_return_x, leader_return_y))
            leader_sequence.apply(leader, tag=tag or "entry_leader")

        # Follower sprites: DelayUntil + FollowPathUntil + TweenUntil
        for i, follower in enumerate(self.sprites[1:], start=1):
            follower_home = self.get_home_slot(follower)
            if not follower_home:
                continue

            delay_frames = i * spacing_frames
            delay_action = after_frames(delay_frames)

            # Use infinite condition - FollowPathUntil will complete automatically
            follower_path_action = FollowPathUntil(
                leader_path.copy(),
                velocity,
                infinite,
            )

            # Use lambda to capture sprite position when tween starts (after path completes)
            follower_return_x = TweenUntil(
                lambda sprite: sprite.center_x,
                follower_home[0],
                "center_x",
                after_frames(seconds_to_frames(0.5)),
            )
            follower_return_y = TweenUntil(
                lambda sprite: sprite.center_y,
                follower_home[1],
                "center_y",
                after_frames(seconds_to_frames(0.5)),
            )

            # Create sequence: delay -> path -> return
            from arcadeactions.conditional import DelayUntil

            follower_sequence = sequence(
                DelayUntil(delay_action),
                follower_path_action,
                parallel(follower_return_x, follower_return_y),
            )
            follower_sequence.apply(follower, tag=tag or f"entry_follower_{i}")
