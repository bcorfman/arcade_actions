"""Breakaway state management for AttackGroup."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade
    from actions.group import AttackGroup
    from actions.base import Action
else:
    arcade = None  # type: ignore
    AttackGroup = Any
    Action = Any


class GroupStage(Enum):
    """State stages for AttackGroup breakaway behavior."""

    IN_FORMATION = "in_formation"
    BREAKAWAY = "breakaway"
    RETURNING = "returning"


class BreakawayStrategy(ABC):
    """Base interface for breakaway strategies.

    This allows pluggable breakaway behaviors. The default deterministic strategy
    uses FollowPathUntil for dives and TweenUntil for returns. Future strategies
    (e.g., SwarmUntil) can be implemented by subclassing this interface.
    """

    @abstractmethod
    def create_breakaway_actions(
        self,
        sprites: arcade.SpriteList,
        parent_group: AttackGroup,
        dive_path: list[tuple[float, float]] | None = None,
        dive_velocity: float = 150.0,
        **kwargs: Any,
    ) -> Action:
        """Create actions for breakaway sprites.

        Args:
            sprites: Sprites that are breaking away
            parent_group: The parent AttackGroup these sprites belong to
            dive_path: Optional dive path (control points for FollowPathUntil)
            dive_velocity: Speed for dive movement
            **kwargs: Additional strategy-specific parameters

        Returns:
            Action to apply to the breakaway sprites
        """
        pass


class DeterministicBreakawayStrategy(BreakawayStrategy):
    """Deterministic dive-and-return strategy using FollowPathUntil and TweenUntil."""

    def create_breakaway_actions(
        self,
        sprites: arcade.SpriteList,
        parent_group: AttackGroup,
        dive_path: list[tuple[float, float]] | None = None,
        dive_velocity: float = 150.0,
        **kwargs: Any,
    ) -> Action:
        """Create deterministic dive and return actions.

        Each sprite dives along the path, then tweens back to its home slot.
        """
        from actions.conditional import FollowPathUntil, TweenUntil
        from actions.composite import sequence
        from actions.frame_timing import after_frames, seconds_to_frames

        if dive_path is None:
            # Default straight dive
            if len(sprites) > 0:
                start_y = sprites[0].center_y
                dive_path = [(sprites[0].center_x, start_y), (sprites[0].center_x, start_y - 200)]

        # Create per-sprite actions
        actions = []
        for sprite in sprites:
            home_slot = parent_group.get_home_slot(sprite)
            if home_slot is None:
                continue

            # Dive action
            dive_action = FollowPathUntil(
                dive_path.copy(),
                dive_velocity,
                after_frames(seconds_to_frames(2.0)),  # Default 2 second dive
            )

            # Return action - tween back to home slot
            return_action = TweenUntil(
                sprite.center_x,
                home_slot[0],
                "center_x",
                after_frames(seconds_to_frames(1.0)),
            )
            return_action_y = TweenUntil(
                sprite.center_y,
                home_slot[1],
                "center_y",
                after_frames(seconds_to_frames(1.0)),
            )

            # Sequence: dive then return
            sprite_sequence = sequence(dive_action, return_action, return_action_y)
            actions.append(sprite_sequence)

        # Return parallel of all sprite sequences
        if len(actions) == 1:
            return actions[0]
        elif len(actions) > 1:
            from actions.composite import parallel

            return parallel(*actions)
        else:
            # No valid sprites - return a no-op delay
            from actions.conditional import DelayUntil

            return DelayUntil(after_frames(1))


class BreakawayManager:
    """Manages breakaway behaviors for an AttackGroup.

    Tracks which sprites have broken away, manages child AttackGroups for breakaway sprites,
    and handles the return-to-formation logic.
    """

    def __init__(self, parent_group: AttackGroup):
        self.parent_group = parent_group
        self.stage = GroupStage.IN_FORMATION
        self.breakaway_sprites: set[arcade.Sprite] = set()
        self.breakaway_groups: list[AttackGroup] = []
        self._strategy: BreakawayStrategy | None = None
        self._trigger_type: str | None = None
        self._trigger_config: dict[str, Any] = {}
        self._breakaway_count: int = 0

    def setup_breakaway(
        self,
        trigger: str,
        count: int = 1,
        strategy: str = "deterministic",
        **kwargs: Any,
    ) -> None:
        """Configure breakaway behavior.

        Args:
            trigger: Trigger type ("timer", "callback", "health", "spatial")
            count: Number of sprites to break away
            strategy: Strategy name ("deterministic" or future "swarm")
            **kwargs: Strategy-specific parameters (dive_path, dive_velocity, etc.)
        """
        import arcade
        from actions.base import Action

        self._trigger_type = trigger
        self._breakaway_count = count

        # Select strategy
        if strategy == "deterministic":
            self._strategy = DeterministicBreakawayStrategy()
        else:
            raise ValueError(f"Unknown breakaway strategy: {strategy}")

        # Store trigger config
        if trigger == "timer":
            self._trigger_config = {"seconds": kwargs.get("seconds", 3.0)}
            # Initialize frame tracking
            self._trigger_start_frame = Action.current_frame()
            self._trigger_frame_count = int(self._trigger_config.get("seconds", 3.0) * 60)  # 60 FPS
        elif trigger == "callback":
            self._trigger_config = {"callback": kwargs.get("callback")}
        elif trigger == "health":
            self._trigger_config = {"threshold": kwargs.get("threshold", 0.5)}
        elif trigger == "spatial":
            self._trigger_config = {"condition": kwargs.get("condition")}
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

        # Store strategy-specific config
        self._strategy_config = kwargs

    def update(self, delta_time: float) -> None:
        """Update breakaway manager state.

        Args:
            delta_time: Time elapsed since last update
        """
        # Check trigger conditions
        if self.stage == GroupStage.IN_FORMATION and self._trigger_type:
            trigger_met = self._check_trigger()
            if trigger_met:
                self._trigger_breakaway()
                _log_breakaway_event(self, "triggered")

        # Update breakaway groups
        for breakaway_group in self.breakaway_groups:
            breakaway_group.update(delta_time)

        # Check for returns
        if self.stage == GroupStage.BREAKAWAY:
            self._check_returns()

    def _check_trigger(self) -> bool:
        """Check if breakaway trigger condition is met."""
        if self._trigger_type == "timer":
            # Frame-based timer using Action frame counter
            from actions.base import Action

            if not hasattr(self, "_trigger_start_frame"):
                self._trigger_start_frame = Action.current_frame()
                self._trigger_frame_count = int(self._trigger_config.get("seconds", 3.0) * 60)  # 60 FPS

            elapsed_frames = Action.current_frame() - self._trigger_start_frame
            if elapsed_frames >= self._trigger_frame_count:
                return True
        elif self._trigger_type == "callback":
            callback = self._trigger_config.get("callback")
            if callback and callback():
                return True
        elif self._trigger_type == "health":
            # Health-based triggers would check group health
            # This is a placeholder for future GroupHealth integration
            pass
        elif self._trigger_type == "spatial":
            condition = self._trigger_config.get("condition")
            if condition and condition():
                return True

        return False

    def _trigger_breakaway(self) -> None:
        """Trigger breakaway for configured number of sprites."""
        if self.stage != GroupStage.IN_FORMATION:
            return

        if not self._strategy:
            return

        # Select sprites to break away
        sprites_to_break = list(self.parent_group.sprites)[: self._breakaway_count]
        if not sprites_to_break:
            return

        # Create breakaway sprite list
        import arcade

        breakaway_list = arcade.SpriteList()
        for sprite in sprites_to_break:
            breakaway_list.append(sprite)
            self.breakaway_sprites.add(sprite)

        # Create breakaway group
        from actions.group import AttackGroup

        breakaway_group = AttackGroup(breakaway_list, group_id=f"{self.parent_group.group_id}_breakaway")
        self.breakaway_groups.append(breakaway_group)

        # Create and apply breakaway actions
        # Extract strategy-specific params, excluding ones we pass explicitly
        strategy_kwargs = {k: v for k, v in self._strategy_config.items() if k not in ("dive_path", "dive_velocity")}
        dive_path = self._strategy_config.get("dive_path")
        dive_velocity = self._strategy_config.get("dive_velocity", 150.0)
        breakaway_action = self._strategy.create_breakaway_actions(
            breakaway_list,
            self.parent_group,
            dive_path=dive_path,
            dive_velocity=dive_velocity,
            **strategy_kwargs,
        )

        breakaway_group.script(breakaway_action, tag="breakaway")

        # Update stage
        self.stage = GroupStage.BREAKAWAY

    def _check_returns(self) -> None:
        """Check if breakaway sprites have returned to formation."""
        # This is a simplified check - in reality we'd check if return actions are complete
        # For now, we'll rely on external code to call rejoin() when appropriate
        pass

    def rejoin(self, sprite: arcade.Sprite) -> None:
        """Rejoin a sprite back to the parent group.

        Args:
            sprite: Sprite to rejoin
        """
        if sprite not in self.breakaway_sprites:
            return

        self.breakaway_sprites.remove(sprite)

        # Remove from breakaway groups
        for breakaway_group in self.breakaway_groups[:]:
            if sprite in breakaway_group.sprites:
                breakaway_group.sprites.remove(sprite)
                if len(breakaway_group.sprites) == 0:
                    self.breakaway_groups.remove(breakaway_group)

        # If all sprites returned, update stage
        if len(self.breakaway_sprites) == 0:
            self.stage = GroupStage.IN_FORMATION


def _log_breakaway_event(manager: BreakawayManager, event: str) -> None:
    """Log breakaway events for debug telemetry (level 2+)."""
    from actions.base import Action

    if Action.debug_level < 2:
        return

    if not Action.debug_all:
        include = Action.debug_include_classes
        if include and "BreakawayManager" not in include:
            return

    print(
        f"[AA L2 BreakawayManager] event={event}, stage={manager.stage}, "
        f"breakaway_count={len(manager.breakaway_sprites)}"
    )
