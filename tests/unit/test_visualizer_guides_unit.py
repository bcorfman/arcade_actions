"""Unit tests for visualizer guides."""

from __future__ import annotations

from arcadeactions.visualizer.guides import GuideManager, HighlightGuide, VelocityGuide


class StubSnapshot:
    def __init__(
        self,
        *,
        target_id: int,
        action_type: str = "MoveUntil",
        velocity: tuple[float, float] | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.target_id = target_id
        self.action_type = action_type
        self.velocity = velocity
        self.bounds = bounds
        self.metadata = metadata or {}


def test_velocity_guide_uses_sprite_ids_metadata() -> None:
    guide = VelocityGuide(enabled=True)
    snapshots = [
        StubSnapshot(
            target_id=1,
            velocity=(2, 3),
            metadata={"sprite_ids": [10, 11]},
        )
    ]
    sprite_positions = {10: (5, 5), 11: (10, 10)}

    guide.update(snapshots, sprite_positions)

    assert len(guide.arrows) == 2
    assert guide.arrows[0][:2] == (5, 5)


def test_velocity_guide_skips_when_disabled() -> None:
    guide = VelocityGuide(enabled=False)
    snapshots = [StubSnapshot(target_id=1, velocity=(2, 3))]
    guide.update(snapshots, {1: (5, 5)})
    assert guide.arrows == []


def test_highlight_guide_sprite_list() -> None:
    guide = HighlightGuide(enabled=True)
    sprite_positions = {1: (10, 10), 2: (20, 20)}
    sprite_sizes = {1: (4, 6), 2: (10, 10)}
    sprite_ids_in_target = {99: [1, 2]}

    guide.update(
        highlighted_target_id=99,
        sprite_positions=sprite_positions,
        sprite_sizes=sprite_sizes,
        sprite_ids_in_target=sprite_ids_in_target,
    )

    assert len(guide.rectangles) == 2
    assert guide.rectangles[0][0] == 8  # left = 10 - 2


def test_guide_manager_any_enabled() -> None:
    manager = GuideManager(initial_enabled=False)
    assert manager.any_enabled() is True  # highlight guide defaults to enabled

    manager.highlight_guide.enabled = False
    assert manager.any_enabled() is False
