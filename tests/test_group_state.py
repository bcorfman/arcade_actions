from __future__ import annotations

import arcade

from arcadeactions.conditional import DelayFrames
from arcadeactions.group_state import DeterministicBreakawayStrategy


def test_deterministic_breakaway_strategy_returns_noop_delay_when_no_valid_sprites():
    strategy = DeterministicBreakawayStrategy()

    sprites = arcade.SpriteList()
    sprites.append(arcade.SpriteSolidColor(10, 10, color=arcade.color.WHITE))

    class StubGroup:
        def get_home_slot(self, sprite):
            return None

    action = strategy.create_breakaway_actions(sprites, parent_group=StubGroup())
    assert isinstance(action, DelayFrames)
