"""Tests for GroupHealth mixin."""

import pytest
import arcade
from actions.group import AttackGroup
from actions.group_health import GroupHealth
from actions.formation import arrange_line
from tests.conftest import ActionTestBase


class TestGroupHealth(ActionTestBase):
    """Test suite for GroupHealth mixin."""

    def test_group_health_creation(self):
        """Test creating a GroupHealth instance."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.health = 100  # Set health attribute
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        health = GroupHealth(group)

        assert health.parent_group == group
        assert health.total_health == 500  # 5 sprites * 100 HP
        assert health.max_health == 500

    def test_group_health_aggregation(self):
        """Test that GroupHealth aggregates sprite health correctly."""
        sprites = arcade.SpriteList()
        for i in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.health = 100 - i * 10  # Different health values
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        health = GroupHealth(group)

        # Total should be 100 + 90 + 80 = 270
        assert health.total_health == 270
        assert health.max_health == 300  # 3 sprites * 100 (max)

    def test_group_health_threshold(self):
        """Test GroupHealth threshold checking."""
        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.health = 100
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        health = GroupHealth(group)

        # Check threshold (50% of max)
        assert health.is_below_threshold(0.5) is False  # 500/500 = 100%

        # Damage some sprites
        sprites[0].health = 0
        sprites[1].health = 0
        health.update()  # Refresh aggregation

        # Now should be below 50% (300/500 = 60%, wait... 300/500 = 60%, so still above)
        # Let's damage more
        sprites[2].health = 0
        health.update()
        assert health.is_below_threshold(0.5) is True  # 200/500 = 40%

    def test_group_health_update(self):
        """Test that GroupHealth.update() refreshes aggregation."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.health = 100
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        health = GroupHealth(group)

        assert health.total_health == 300

        # Damage a sprite
        sprites[0].health = 50
        health.update()

        assert health.total_health == 250
