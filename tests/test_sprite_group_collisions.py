"""
Test suite for SpriteGroup collision detection functionality.
"""

from unittest.mock import Mock

import pytest

from actions.base import ActionSprite
from actions.group import SpriteGroup
from actions.protocols import ArcadeCollisionDetector, BoundingBoxCollisionDetector, MockCollisionDetector


class TestSpriteGroupCollisions:
    """Test suite for SpriteGroup collision detection."""

    @pytest.fixture
    def sprites_group(self):
        """Create a SpriteGroup with test sprites."""
        # Create test sprites with simple textures, positioned apart to avoid accidental collisions
        sprite1 = ActionSprite(":resources:images/items/star.png", center_x=50, center_y=50)
        sprite2 = ActionSprite(":resources:images/items/star.png", center_x=150, center_y=50)
        return SpriteGroup([sprite1, sprite2])

    @pytest.fixture
    def target_group(self):
        """Create a target SpriteGroup for collision testing."""
        # Position targets away from sprites by default
        target1 = ActionSprite(":resources:images/items/star.png", center_x=300, center_y=300)
        target2 = ActionSprite(":resources:images/items/star.png", center_x=400, center_y=300)
        return SpriteGroup([target1, target2])

    def test_on_collision_with_returns_self(self, sprites_group, target_group):
        """Test that on_collision_with returns self for method chaining."""
        mock_callback = Mock()
        result = sprites_group.on_collision_with(target_group, mock_callback)
        assert result is sprites_group

    def test_on_collision_with_method_chaining(self, sprites_group, target_group):
        """Test that collision handlers can be chained."""
        callback1 = Mock()
        callback2 = Mock()

        result = sprites_group.on_collision_with(target_group, callback1).on_collision_with(target_group, callback2)

        assert result is sprites_group
        assert len(sprites_group._collision_handlers) == 2

    def test_collision_handler_registration(self, sprites_group, target_group):
        """Test that collision handlers are properly registered."""
        mock_callback = Mock()

        sprites_group.on_collision_with(target_group, mock_callback)

        assert len(sprites_group._collision_handlers) == 1
        registered_group, registered_callback = sprites_group._collision_handlers[0]
        assert registered_group is target_group
        assert registered_callback is mock_callback

    def test_multiple_collision_handlers(self, sprites_group, target_group):
        """Test that multiple collision handlers can be registered."""
        callback1 = Mock()
        callback2 = Mock()
        target_group2 = SpriteGroup()

        sprites_group.on_collision_with(target_group, callback1)
        sprites_group.on_collision_with(target_group2, callback2)

        assert len(sprites_group._collision_handlers) == 2

    def test_update_collisions_no_collision(self, sprites_group, target_group):
        """Test update_collisions when no collisions occur."""
        mock_callback = Mock()

        # Position sprites so they don't collide
        for sprite in sprites_group:
            sprite.center_x = 0
            sprite.center_y = 0
        for sprite in target_group:
            sprite.center_x = 500
            sprite.center_y = 500

        sprites_group.on_collision_with(target_group, mock_callback)
        sprites_group.update_collisions()

        mock_callback.assert_not_called()

    def test_update_collisions_with_collision(self, sprites_group, target_group):
        """Test update_collisions when collisions occur."""
        mock_callback = Mock()

        # Position sprites so they collide (same position)
        sprites_group[0].center_x = 100
        sprites_group[0].center_y = 100
        target_group[0].center_x = 100
        target_group[0].center_y = 100

        sprites_group.on_collision_with(target_group, mock_callback)
        sprites_group.update_collisions()

        # Should be called once for the colliding sprite
        mock_callback.assert_called_once()
        args = mock_callback.call_args[0]
        assert args[0] is sprites_group[0]  # The sprite that collided
        assert target_group[0] in args[1]  # The hit sprites list

    def test_collision_callback_parameters(self, sprites_group, target_group):
        """Test that collision callbacks receive correct parameters."""
        collisions_detected = []

        def collision_callback(sprite, hit_sprites):
            collisions_detected.append((sprite, hit_sprites))

        # Position first sprite to collide with first target
        sprites_group[0].center_x = 100
        sprites_group[0].center_y = 100
        target_group[0].center_x = 100
        target_group[0].center_y = 100

        # Position second sprite away from targets
        sprites_group[1].center_x = 500
        sprites_group[1].center_y = 500

        sprites_group.on_collision_with(target_group, collision_callback)
        sprites_group.update_collisions()

        assert len(collisions_detected) == 1
        colliding_sprite, hit_sprites = collisions_detected[0]
        assert colliding_sprite is sprites_group[0]
        assert target_group[0] in hit_sprites

    def test_multiple_collisions_for_single_sprite(self, sprites_group, target_group):
        """Test handling multiple collisions for a single sprite."""
        mock_callback = Mock()

        # Position one sprite to collide with multiple targets
        sprites_group[0].center_x = 100
        sprites_group[0].center_y = 100
        target_group[0].center_x = 100
        target_group[0].center_y = 100
        target_group[1].center_x = 100
        target_group[1].center_y = 100

        # Position second sprite away
        sprites_group[1].center_x = 500
        sprites_group[1].center_y = 500

        sprites_group.on_collision_with(target_group, mock_callback)
        sprites_group.update_collisions()

        # Should be called once for the sprite, with multiple hits
        mock_callback.assert_called_once()
        args = mock_callback.call_args[0]
        assert args[0] is sprites_group[0]
        assert len(args[1]) == 2  # Both targets should be in hit list

    def test_collision_with_list_instead_of_spritegroup(self, sprites_group):
        """Test collision detection with a regular list of sprites."""
        mock_callback = Mock()

        # Create regular sprites in a list
        target_sprites = [
            ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100),
            ActionSprite(":resources:images/items/star.png", center_x=200, center_y=100),
        ]

        # Position sprite to collide
        sprites_group[0].center_x = 100
        sprites_group[0].center_y = 100

        sprites_group.on_collision_with(target_sprites, mock_callback)
        sprites_group.update_collisions()

        mock_callback.assert_called_once()

    def test_collision_with_empty_group(self, sprites_group):
        """Test collision detection with an empty target group."""
        mock_callback = Mock()
        empty_group = SpriteGroup()

        sprites_group.on_collision_with(empty_group, mock_callback)
        sprites_group.update_collisions()

        mock_callback.assert_not_called()

    def test_empty_sprite_group_collisions(self, target_group):
        """Test collision detection when the checking group is empty."""
        mock_callback = Mock()
        empty_group = SpriteGroup()

        empty_group.on_collision_with(target_group, mock_callback)
        empty_group.update_collisions()

        mock_callback.assert_not_called()

    def test_collision_handlers_persist_after_sprite_removal(self, sprites_group, target_group):
        """Test that collision handlers persist when sprites are removed."""
        mock_callback = Mock()

        sprites_group.on_collision_with(target_group, mock_callback)

        # Remove a sprite
        removed_sprite = sprites_group[0]
        sprites_group.remove(removed_sprite)

        # Handlers should still be registered
        assert len(sprites_group._collision_handlers) == 1

        # Position remaining sprite to collide
        sprites_group[0].center_x = 100
        sprites_group[0].center_y = 100
        target_group[0].center_x = 100
        target_group[0].center_y = 100

        sprites_group.update_collisions()
        mock_callback.assert_called_once()

    def test_integration_with_invaders_style_collision(self):
        """Test collision detection in a scenario similar to the invaders game."""
        # Create bullet group and enemy group
        bullets = SpriteGroup()
        enemies = SpriteGroup()
        shields = SpriteGroup()

        # Create test sprites
        bullet = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        shield = ActionSprite(":resources:images/items/star.png", center_x=200, center_y=200)

        bullets.append(bullet)
        enemies.append(enemy)
        shields.append(shield)

        # Track collision results
        collision_results = []

        def bullet_enemy_collision(bullet, hit_enemies):
            collision_results.append(("bullet_enemy", bullet, hit_enemies))
            bullet.remove_from_sprite_lists()
            for enemy in hit_enemies:
                enemy.remove_from_sprite_lists()

        def bullet_shield_collision(bullet, hit_shields):
            collision_results.append(("bullet_shield", bullet, hit_shields))
            bullet.remove_from_sprite_lists()
            for shield in hit_shields:
                shield.remove_from_sprite_lists()

        # Setup collision handlers (method chaining)
        bullets.on_collision_with(enemies, bullet_enemy_collision).on_collision_with(shields, bullet_shield_collision)

        # Update collisions
        bullets.update_collisions()

        # Should detect bullet-enemy collision, not bullet-shield
        assert len(collision_results) == 1
        assert collision_results[0][0] == "bullet_enemy"
        assert collision_results[0][1] is bullet
        assert enemy in collision_results[0][2]

        # Bullet and enemy should be removed
        assert len(bullets) == 0
        assert len(enemies) == 0
        assert len(shields) == 1  # Shield untouched


class TestCollisionDetectorInjection:
    """Test suite for collision detector dependency injection."""

    def test_default_collision_detector_is_arcade(self):
        """Test that SpriteGroup uses ArcadeCollisionDetector by default."""
        sprites_group = SpriteGroup()
        # The default detector should be ArcadeCollisionDetector
        assert isinstance(sprites_group._collision_detector, ArcadeCollisionDetector)

    def test_mock_collision_detector_injection(self):
        """Test injecting MockCollisionDetector for controlled testing."""
        # Setup - inject mock collision detector
        mock_detector = MockCollisionDetector()
        bullets = SpriteGroup(collision_detector=mock_detector)
        enemies = SpriteGroup()

        # Create test sprites
        bullet = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=200, center_y=200)
        bullets.append(bullet)
        enemies.append(enemy)

        # Pre-configure collision result
        mock_detector.set_collision_result(bullet, tuple(enemies), [enemy])

        # Setup collision handler
        collisions_detected = []

        def on_collision(bullet, hit_enemies):
            collisions_detected.append((bullet, hit_enemies))

        bullets.on_collision_with(enemies, on_collision)
        bullets.update_collisions()

        # Verify mock was used - should detect collision even though sprites are far apart
        assert len(collisions_detected) == 1
        assert collisions_detected[0][0] is bullet
        assert enemy in collisions_detected[0][1]

    def test_mock_collision_detector_no_result_configured(self):
        """Test MockCollisionDetector returns no collisions when no results configured."""
        mock_detector = MockCollisionDetector()
        bullets = SpriteGroup(collision_detector=mock_detector)
        enemies = SpriteGroup()

        # Create overlapping sprites (would normally collide)
        bullet = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        bullets.append(bullet)
        enemies.append(enemy)

        # Don't configure any collision results

        # Setup collision handler
        collisions_detected = []

        def on_collision(bullet, hit_enemies):
            collisions_detected.append((bullet, hit_enemies))

        bullets.on_collision_with(enemies, on_collision)
        bullets.update_collisions()

        # Should detect no collisions since mock has no configured results
        assert len(collisions_detected) == 0

    def test_bounding_box_collision_detector_injection(self):
        """Test injecting BoundingBoxCollisionDetector for OpenGL-free testing."""
        # Setup - inject bounding box collision detector
        bbox_detector = BoundingBoxCollisionDetector()
        bullets = SpriteGroup(collision_detector=bbox_detector)
        enemies = SpriteGroup()

        # Create overlapping sprites
        bullet = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        bullets.append(bullet)
        enemies.append(enemy)

        # Setup collision handler
        collisions_detected = []

        def on_collision(bullet, hit_enemies):
            collisions_detected.append((bullet, hit_enemies))

        bullets.on_collision_with(enemies, on_collision)
        bullets.update_collisions()

        # Should detect collision since sprites overlap
        assert len(collisions_detected) == 1
        assert collisions_detected[0][0] is bullet
        assert enemy in collisions_detected[0][1]

    def test_bounding_box_collision_detector_no_overlap(self):
        """Test BoundingBoxCollisionDetector doesn't detect non-overlapping sprites."""
        bbox_detector = BoundingBoxCollisionDetector()
        bullets = SpriteGroup(collision_detector=bbox_detector)
        enemies = SpriteGroup()

        # Create non-overlapping sprites (sprites are 128x128, so 300 pixels apart ensures no overlap)
        bullet = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=400, center_y=400)
        bullets.append(bullet)
        enemies.append(enemy)

        # Setup collision handler
        collisions_detected = []

        def on_collision(bullet, hit_enemies):
            collisions_detected.append((bullet, hit_enemies))

        bullets.on_collision_with(enemies, on_collision)
        bullets.update_collisions()

        # Should detect no collisions since sprites don't overlap
        assert len(collisions_detected) == 0

    def test_different_collision_detectors_per_group(self):
        """Test that different SpriteGroups can use different collision detectors."""
        # Create groups with different collision detectors
        mock_detector = MockCollisionDetector()
        bbox_detector = BoundingBoxCollisionDetector()

        bullets_mock = SpriteGroup(collision_detector=mock_detector)
        bullets_bbox = SpriteGroup(collision_detector=bbox_detector)
        enemies = SpriteGroup()

        # Create test sprites
        bullet1 = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        bullet2 = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)

        bullets_mock.append(bullet1)
        bullets_bbox.append(bullet2)
        enemies.append(enemy)

        # Configure mock to return no collisions
        mock_detector.set_collision_result(bullet1, tuple(enemies), [])

        # Setup collision handlers
        mock_collisions = []
        bbox_collisions = []

        def on_mock_collision(bullet, hit_enemies):
            mock_collisions.append((bullet, hit_enemies))

        def on_bbox_collision(bullet, hit_enemies):
            bbox_collisions.append((bullet, hit_enemies))

        bullets_mock.on_collision_with(enemies, on_mock_collision)
        bullets_bbox.on_collision_with(enemies, on_bbox_collision)

        # Update collisions
        bullets_mock.update_collisions()
        bullets_bbox.update_collisions()

        # Mock should detect no collisions (configured to return empty list)
        assert len(mock_collisions) == 0

        # BoundingBox should detect collision (sprites overlap)
        assert len(bbox_collisions) == 1
        assert bbox_collisions[0][0] is bullet2
        assert enemy in bbox_collisions[0][1]

    def test_collision_detector_protocol_compliance(self):
        """Test that all collision detectors follow the protocol interface."""
        detectors = [ArcadeCollisionDetector(), MockCollisionDetector(), BoundingBoxCollisionDetector()]

        # Create test sprites
        sprite = ActionSprite(":resources:images/items/star.png", center_x=100, center_y=100)
        target_group = [ActionSprite(":resources:images/items/star.png", center_x=200, center_y=200)]

        for detector in detectors:
            # Each detector should have check_collision method
            assert hasattr(detector, "check_collision")

            # Method should be callable and return a list
            result = detector.check_collision(sprite, target_group)
            assert isinstance(result, list)

            # All items in result should be sprites
            for hit_sprite in result:
                assert hasattr(hit_sprite, "center_x")  # Basic sprite check
