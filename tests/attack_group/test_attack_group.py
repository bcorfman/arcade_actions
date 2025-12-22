"""Tests for AttackGroup core functionality."""

import pytest
import arcade
from actions.base import Action
from actions.formation import arrange_line, arrange_grid
from actions.frame_timing import after_frames
from actions.conditional import MoveUntil, infinite
from tests.conftest import ActionTestBase


class TestAttackGroup(ActionTestBase):
    """Test suite for AttackGroup core class."""

    def test_attack_group_creation(self):
        """Test creating an AttackGroup with sprites."""
        from actions.group import AttackGroup

        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")

        assert group.group_id == "test_group"
        assert len(group.sprites) == 5
        assert group.sprites == sprites
        assert group.formation_type is None
        assert len(group._home_slots) == 0

    def test_attack_group_place_formation(self):
        """Test placing sprites in a formation."""
        from actions.group import AttackGroup

        sprites = arcade.SpriteList()
        for _ in range(5):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        assert group.formation_type == "line"
        assert len(group._home_slots) == 5

        # Verify sprites are positioned
        for i, sprite in enumerate(sprites):
            assert sprite.center_x == 100 + i * 50
            assert sprite.center_y == 200
            # Verify home slot recorded
            assert id(sprite) in group._home_slots
            assert group._home_slots[id(sprite)] == (100 + i * 50, 200)

    def test_attack_group_place_grid(self):
        """Test placing sprites in a grid formation."""
        from actions.group import AttackGroup

        sprites = arcade.SpriteList()
        for _ in range(6):  # 2x3 grid
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_grid, rows=2, cols=3, start_x=100, start_y=300, spacing_x=50, spacing_y=40)

        assert group.formation_type == "grid"
        assert len(group._home_slots) == 6

        # Verify grid positions
        for i, sprite in enumerate(sprites):
            row = i // 3
            col = i % 3
            expected_x = 100 + col * 50
            expected_y = 300 + row * 40
            assert sprite.center_x == expected_x
            assert sprite.center_y == expected_y
            assert group._home_slots[id(sprite)] == (expected_x, expected_y)

    def test_attack_group_script_application(self):
        """Test applying a script action to the group."""
        from actions.group import AttackGroup

        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 100
            sprite.center_y = 200
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        move_action = MoveUntil((5, 0), after_frames(10))
        group.script(move_action, tag="group_move")

        # Verify action is applied to the sprite list
        assert move_action.target == sprites
        assert move_action.tag == "group_move"
        assert move_action in Action._active_actions

        # Update and verify movement
        for _ in range(10):
            Action.update_all(1.0 / 60.0)
            # Apply velocity to position (Arcade's sprite.update())
            for sprite in sprites:
                sprite.update()

        # Sprites should have moved
        for sprite in sprites:
            assert sprite.center_x > 100

    def test_attack_group_script_multiple_actions(self):
        """Test applying multiple actions as a script."""
        from actions.group import AttackGroup
        from actions.composite import sequence

        sprites = arcade.SpriteList()
        for _ in range(2):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 100
            sprite.center_y = 200
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        move1 = MoveUntil((5, 0), after_frames(5))
        move2 = MoveUntil((0, 5), after_frames(5))
        script = sequence(move1, move2)
        group.script(script, tag="group_script")

        assert script.target == sprites
        assert script.tag == "group_script"

    def test_attack_group_update(self):
        """Test AttackGroup.update() updates breakaway manager, not actions."""
        from actions.group import AttackGroup
        from actions.base import Action

        sprites = arcade.SpriteList()
        for _ in range(2):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.center_x = 100
            sprite.center_y = 200
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        move_action = MoveUntil((5, 0), after_frames(10))
        group.script(move_action)

        initial_x = sprites[0].center_x

        # Update actions (should be called once per frame at top level)
        Action.update_all(1.0 / 60.0)
        # Update group (updates breakaway manager, not actions)
        group.update(1.0 / 60.0)
        # Apply velocity to position (Arcade's sprite.update())
        for sprite in sprites:
            sprite.update()

        # Sprite should have moved
        assert sprites[0].center_x > initial_x

    def test_attack_group_home_slot_preservation(self):
        """Test that home slots are preserved after breakaway."""
        from actions.group import AttackGroup

        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprites.append(sprite)

        group = AttackGroup(sprites, group_id="test_group")
        group.place(arrange_line, start_x=100, start_y=200, spacing=50)

        # Verify home slots recorded
        for i, sprite in enumerate(sprites):
            expected_slot = (100 + i * 50, 200)
            assert group._home_slots[id(sprite)] == expected_slot

        # Move sprites manually
        for sprite in sprites:
            sprite.center_x += 100
            sprite.center_y += 50

        # Home slots should still be preserved
        for i, sprite in enumerate(sprites):
            expected_slot = (100 + i * 50, 200)
            assert group._home_slots[id(sprite)] == expected_slot
