"""GroupHealth mixin for aggregating sprite health across AttackGroup."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from actions.group import AttackGroup
else:
    AttackGroup = Any


class GroupHealth:
    """Tracks aggregate health across sprites in an AttackGroup.

    This mixin aggregates the `health` attribute from all sprites in the group
    and provides threshold checking for triggering last-stand behaviors.

    Args:
        parent_group: AttackGroup to track health for
        health_attribute: Name of the health attribute on sprites (default: "health")

    Example:
        group = AttackGroup(sprites, group_id="enemies")
        health = GroupHealth(group)

        # Check if group is below 50% health
        if health.is_below_threshold(0.5):
            # Trigger last-stand behavior
            group.breakaway(...)
    """

    def __init__(self, parent_group: AttackGroup, health_attribute: str = "health"):
        self.parent_group = parent_group
        self.health_attribute = health_attribute
        self.total_health: float = 0.0
        self.max_health: float = 0.0
        self._update_health()

    def _update_health(self) -> None:
        """Recalculate total and max health from sprites."""
        total = 0.0
        max_total = 0.0

        for sprite in self.parent_group.sprites:
            health_value = getattr(sprite, self.health_attribute, 0)
            if isinstance(health_value, (int, float)):
                total += health_value
                # Assume max health is 100 if not specified
                max_health = getattr(sprite, "max_health", 100)
                max_total += max_health

        self.total_health = total
        self.max_health = max_total

    def update(self) -> None:
        """Refresh health aggregation from current sprite states."""
        self._update_health()

    def is_below_threshold(self, threshold: float) -> bool:
        """Check if group health is below the given threshold.

        Args:
            threshold: Threshold as fraction of max health (0.0 to 1.0)

        Returns:
            True if current health / max health < threshold
        """
        if self.max_health <= 0:
            return False

        health_ratio = self.total_health / self.max_health
        return health_ratio < threshold

    def get_health_ratio(self) -> float:
        """Get current health as a ratio of max health.

        Returns:
            Ratio from 0.0 (dead) to 1.0 (full health)
        """
        if self.max_health <= 0:
            return 1.0

        return self.total_health / self.max_health
