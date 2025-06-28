"""Test suite for pattern.py - Attack patterns and AttackGroup."""

import arcade

from actions.base import Action
from actions.pattern import (
    AttackGroup,
    CirclePattern,
    GridPattern,
    LinePattern,
    VFormationPattern,
)


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


def create_test_sprite_list(count=5):
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    for i in range(count):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite_list.append(sprite)
    return sprite_list


class MockAction(Action):
    """Mock action for testing AttackGroup."""

    def __init__(self, name="mock"):
        super().__init__()
        self.name = name
        self.applied = False

    def apply_effect(self):
        self.applied = True

    def clone(self):
        return MockAction(self.name)


class TestLinePattern:
    """Test suite for LinePattern."""

    def test_line_pattern_initialization(self):
        """Test LinePattern initialization."""
        pattern = LinePattern()
        assert pattern.name == "line"
        assert pattern.spacing == 50.0

        pattern_custom = LinePattern(spacing=80.0)
        assert pattern_custom.spacing == 80.0

    def test_line_pattern_apply(self):
        """Test LinePattern apply method."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)
        pattern = LinePattern(spacing=60.0)

        pattern.apply(attack_group, start_x=100, start_y=200)

        # Check sprite positions
        assert sprite_list[0].center_x == 100
        assert sprite_list[0].center_y == 200
        assert sprite_list[1].center_x == 160
        assert sprite_list[1].center_y == 200
        assert sprite_list[2].center_x == 220
        assert sprite_list[2].center_y == 200

    def test_line_pattern_default_position(self):
        """Test LinePattern with default position."""
        sprite_list = create_test_sprite_list(2)
        attack_group = AttackGroup(sprite_list)
        pattern = LinePattern()

        pattern.apply(attack_group)

        # Check default positions
        assert sprite_list[0].center_x == 0
        assert sprite_list[0].center_y == 0
        assert sprite_list[1].center_x == 50
        assert sprite_list[1].center_y == 0


class TestGridPattern:
    """Test suite for GridPattern."""

    def test_grid_pattern_initialization(self):
        """Test GridPattern initialization."""
        pattern = GridPattern()
        assert pattern.name == "grid"
        assert pattern.rows == 5
        assert pattern.cols == 10
        assert pattern.spacing_x == 60.0
        assert pattern.spacing_y == 50.0

        pattern_custom = GridPattern(rows=3, cols=4, spacing_x=80, spacing_y=70)
        assert pattern_custom.rows == 3
        assert pattern_custom.cols == 4
        assert pattern_custom.spacing_x == 80
        assert pattern_custom.spacing_y == 70

    def test_grid_pattern_apply(self):
        """Test GridPattern apply method."""
        sprite_list = create_test_sprite_list(6)  # 2x3 grid
        attack_group = AttackGroup(sprite_list)
        pattern = GridPattern(rows=2, cols=3, spacing_x=80, spacing_y=60)

        pattern.apply(attack_group, start_x=200, start_y=400)

        # Check sprite positions for 2x3 grid
        # Row 0
        assert sprite_list[0].center_x == 200  # Col 0
        assert sprite_list[0].center_y == 400
        assert sprite_list[1].center_x == 280  # Col 1
        assert sprite_list[1].center_y == 400
        assert sprite_list[2].center_x == 360  # Col 2
        assert sprite_list[2].center_y == 400

        # Row 1
        assert sprite_list[3].center_x == 200  # Col 0
        assert sprite_list[3].center_y == 340  # Y decreased by spacing_y
        assert sprite_list[4].center_x == 280  # Col 1
        assert sprite_list[4].center_y == 340
        assert sprite_list[5].center_x == 360  # Col 2
        assert sprite_list[5].center_y == 340

    def test_grid_pattern_default_position(self):
        """Test GridPattern with default position."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)
        pattern = GridPattern(cols=3)

        pattern.apply(attack_group)

        # Check default positions
        assert sprite_list[0].center_x == 100
        assert sprite_list[0].center_y == 500


class TestCirclePattern:
    """Test suite for CirclePattern."""

    def test_circle_pattern_initialization(self):
        """Test CirclePattern initialization."""
        pattern = CirclePattern()
        assert pattern.name == "circle"
        assert pattern.radius == 100.0

        pattern_custom = CirclePattern(radius=150.0)
        assert pattern_custom.radius == 150.0

    def test_circle_pattern_apply(self):
        """Test CirclePattern apply method."""
        sprite_list = create_test_sprite_list(4)  # 4 sprites for easier math
        attack_group = AttackGroup(sprite_list)
        pattern = CirclePattern(radius=100.0)

        pattern.apply(attack_group, center_x=400, center_y=300)

        # Check that sprites are positioned around the circle
        # With 4 sprites, they should be at 90-degree intervals
        import math

        for i, sprite in enumerate(sprite_list):
            angle = i * 2 * math.pi / 4
            expected_x = 400 + math.cos(angle) * 100
            expected_y = 300 + math.sin(angle) * 100

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1

    def test_circle_pattern_empty_group(self):
        """Test CirclePattern with empty group."""
        sprite_list = arcade.SpriteList()
        attack_group = AttackGroup(sprite_list)
        pattern = CirclePattern()

        # Should not raise error
        pattern.apply(attack_group, center_x=400, center_y=300)

    def test_circle_pattern_default_position(self):
        """Test CirclePattern with default position."""
        sprite_list = create_test_sprite_list(2)
        attack_group = AttackGroup(sprite_list)
        pattern = CirclePattern()

        pattern.apply(attack_group)

        # Check default center position is used
        import math

        for i, sprite in enumerate(sprite_list):
            angle = i * 2 * math.pi / 2
            expected_x = 400 + math.cos(angle) * 100
            expected_y = 300 + math.sin(angle) * 100

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1


class TestVFormationPattern:
    """Test suite for VFormationPattern."""

    def test_v_formation_pattern_initialization(self):
        """Test VFormationPattern initialization."""
        pattern = VFormationPattern()
        assert pattern.name == "v_formation"
        import math

        assert abs(pattern.angle - math.radians(45.0)) < 0.1
        assert pattern.spacing == 50.0

        pattern_custom = VFormationPattern(angle=30.0, spacing=60.0)
        assert abs(pattern_custom.angle - math.radians(30.0)) < 0.1
        assert pattern_custom.spacing == 60.0

    def test_v_formation_pattern_apply(self):
        """Test VFormationPattern apply method."""
        sprite_list = create_test_sprite_list(5)
        attack_group = AttackGroup(sprite_list)
        pattern = VFormationPattern(angle=45.0, spacing=50.0)

        pattern.apply(attack_group, apex_x=400, apex_y=500)

        # First sprite should be at apex
        assert sprite_list[0].center_x == 400
        assert sprite_list[0].center_y == 500

        # Remaining sprites should alternate sides
        import math

        angle_rad = math.radians(45.0)

        # Second sprite (right side)
        expected_x = 400 + math.cos(angle_rad) * 50
        expected_y = 500 - math.sin(angle_rad) * 50
        assert abs(sprite_list[1].center_x - expected_x) < 0.1
        assert abs(sprite_list[1].center_y - expected_y) < 0.1

        # Third sprite (left side)
        expected_x = 400 - math.cos(angle_rad) * 50
        expected_y = 500 - math.sin(angle_rad) * 50
        assert abs(sprite_list[2].center_x - expected_x) < 0.1
        assert abs(sprite_list[2].center_y - expected_y) < 0.1

    def test_v_formation_pattern_empty_group(self):
        """Test VFormationPattern with empty group."""
        sprite_list = arcade.SpriteList()
        attack_group = AttackGroup(sprite_list)
        pattern = VFormationPattern()

        # Should not raise error
        pattern.apply(attack_group, apex_x=400, apex_y=500)

    def test_v_formation_pattern_single_sprite(self):
        """Test VFormationPattern with single sprite."""
        sprite_list = create_test_sprite_list(1)
        attack_group = AttackGroup(sprite_list)
        pattern = VFormationPattern()

        pattern.apply(attack_group, apex_x=400, apex_y=500)

        # Single sprite should be at apex
        assert sprite_list[0].center_x == 400
        assert sprite_list[0].center_y == 500


class TestAttackGroup:
    """Test suite for AttackGroup."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_attack_group_initialization(self):
        """Test AttackGroup initialization."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)

        assert attack_group.sprites == sprite_list
        assert attack_group.name is None
        assert attack_group.parent is None
        assert isinstance(attack_group.time_of_birth, (int, float))  # Just check it's a number

    def test_attack_group_with_name_and_parent(self):
        """Test AttackGroup with name and parent."""
        sprite_list = create_test_sprite_list(3)
        parent_group = AttackGroup(arcade.SpriteList())
        attack_group = AttackGroup(sprite_list, name="test_group", parent=parent_group)

        assert attack_group.name == "test_group"
        assert attack_group.parent == parent_group

    def test_attack_group_do_action(self):
        """Test AttackGroup do method."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)
        action = MockAction("test_action")

        returned_action = attack_group.do(action)

        assert returned_action == action
        assert action.target == sprite_list
        assert action.applied

    def test_attack_group_update(self):
        """Test AttackGroup update method."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)

        # Should not raise error
        attack_group.update(0.016)

    def test_attack_group_schedule_attack(self):
        """Test AttackGroup schedule_attack method."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)

        callback_called = False

        def test_callback():
            nonlocal callback_called
            callback_called = True

        event_id = attack_group.schedule_attack(0.1, test_callback)

        assert isinstance(event_id, int)
        # Note: In a real test, you'd need to simulate time passage to test the callback

    def test_attack_group_breakaway(self):
        """Test AttackGroup breakaway method."""
        sprite_list = create_test_sprite_list(5)
        attack_group = AttackGroup(sprite_list)

        # Break away some sprites
        breakaway_sprites = [sprite_list[1], sprite_list[3]]
        new_group = attack_group.breakaway(breakaway_sprites)

        assert isinstance(new_group, AttackGroup)
        assert len(new_group.sprites) == 2
        assert new_group.sprites[0] == sprite_list[1]
        assert new_group.sprites[1] == sprite_list[3]
        assert new_group.parent == attack_group

        # Original group should have remaining sprites
        assert len(attack_group.sprites) == 3

    def test_attack_group_destroy(self):
        """Test AttackGroup destroy method."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)

        destroy_called = False

        def on_destroy(group):
            nonlocal destroy_called
            destroy_called = True

        attack_group.on_destroy(on_destroy)
        attack_group.destroy()

        assert destroy_called
        assert len(attack_group.sprites) == 0

    def test_attack_group_callbacks(self):
        """Test AttackGroup callback registration."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list)

        destroy_callback_called = False
        breakaway_callback_called = False

        def on_destroy(group):
            nonlocal destroy_callback_called
            destroy_callback_called = True

        def on_breakaway(group):
            nonlocal breakaway_callback_called
            breakaway_callback_called = True

        attack_group.on_destroy(on_destroy)
        attack_group.on_breakaway(on_breakaway)

        # Test breakaway callback
        breakaway_sprites = [sprite_list[0]]
        attack_group.breakaway(breakaway_sprites)
        assert breakaway_callback_called

        # Test destroy callback
        attack_group.destroy()
        assert destroy_callback_called

    def test_attack_group_repr(self):
        """Test AttackGroup string representation."""
        sprite_list = create_test_sprite_list(3)
        attack_group = AttackGroup(sprite_list, name="test_group")

        repr_str = repr(attack_group)
        assert "AttackGroup" in repr_str
        assert "test_group" in repr_str


class TestPatternIntegration:
    """Test suite for pattern integration with AttackGroup."""

    def test_pattern_with_attack_group_workflow(self):
        """Test complete workflow with patterns and AttackGroup."""
        sprite_list = create_test_sprite_list(6)
        attack_group = AttackGroup(sprite_list, name="formation")

        # Apply grid pattern
        grid_pattern = GridPattern(rows=2, cols=3)
        grid_pattern.apply(attack_group, start_x=200, start_y=400)

        # Verify grid formation
        assert sprite_list[0].center_x == 200
        assert sprite_list[0].center_y == 400
        assert sprite_list[3].center_x == 200
        assert sprite_list[3].center_y == 350  # Row 1, Y decreased

        # Apply action to group
        action = MockAction("move_formation")
        attack_group.do(action)

        assert action.applied
        assert action.target == sprite_list

    def test_multiple_patterns_on_same_group(self):
        """Test applying multiple patterns to the same group."""
        sprite_list = create_test_sprite_list(4)
        attack_group = AttackGroup(sprite_list)

        # First apply line pattern
        line_pattern = LinePattern(spacing=60)
        line_pattern.apply(attack_group, start_x=100, start_y=200)

        # Verify line formation
        assert sprite_list[0].center_x == 100
        assert sprite_list[1].center_x == 160

        # Then apply circle pattern (overwrites positions)
        circle_pattern = CirclePattern(radius=50)
        circle_pattern.apply(attack_group, center_x=300, center_y=300)

        # Verify circle formation (positions should be different now)
        import math

        for i, sprite in enumerate(sprite_list):
            angle = i * 2 * math.pi / 4
            expected_x = 300 + math.cos(angle) * 50
            expected_y = 300 + math.sin(angle) * 50

            assert abs(sprite.center_x - expected_x) < 0.1
            assert abs(sprite.center_y - expected_y) < 0.1
