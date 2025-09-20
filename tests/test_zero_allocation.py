"""Test suite for zero-allocation gameplay features.

This test suite covers:
1. Enhanced arrange_* functions with sprites parameter validation
2. SpritePool functionality for zero-allocation gameplay
3. Integration tests for the recommended usage patterns
"""

import arcade
import pytest

from actions.formation import (
    arrange_arc,
    arrange_arrow,
    arrange_circle,
    arrange_concentric_rings,
    arrange_cross,
    arrange_diamond,
    arrange_grid,
    arrange_hexagonal_grid,
    arrange_line,
    arrange_triangle,
    arrange_v_formation,
)


@pytest.fixture(autouse=True)
def cleanup_actions():
    """Clean up actions after each test."""
    from actions.base import Action

    yield
    Action.stop_all()


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


def create_test_sprite_list(count=5) -> arcade.SpriteList:
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    for i in range(count):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite_list.append(sprite)
    return sprite_list


# ================================================================================
# PARAMETER VALIDATION TESTS
# ================================================================================


class TestArrangeFunctionParameterValidation:
    """Test parameter validation for arrange functions."""

    def test_arrange_line_exactly_one_of_sprites_or_count_required(self):
        """Test that arrange_line requires exactly one of sprites or count."""
        # Should work with sprites provided (no count needed)
        sprites = create_test_sprite_list(3)
        result = arrange_line(sprites, start_x=0, start_y=0)
        assert len(result) == 3

        # Should work with count provided (no sprites)
        result = arrange_line(count=3, start_x=0, start_y=0)
        assert len(result) == 3

        # Should fail with neither
        with pytest.raises(ValueError, match="When \\*sprites\\* is None you must supply a positive \\*count\\*"):
            arrange_line()

        # Should fail with both sprites and count (this is the new validation)
        sprites = create_test_sprite_list(3)
        with pytest.raises(ValueError, match="Cannot specify both 'sprites' and 'count'"):
            arrange_line(sprites, count=5, start_x=0, start_y=0)

    def test_arrange_grid_exactly_one_of_sprites_or_count_required(self):
        """Test that arrange_grid requires exactly one of sprites or count."""
        # Should work with sprites provided
        sprites = create_test_sprite_list(6)
        result = arrange_grid(sprites, rows=2, cols=3, start_x=0, start_y=0)
        assert len(result) == 6

        # Should work with implicit count from rows*cols
        result = arrange_grid(rows=2, cols=3, start_x=0, start_y=0)
        assert len(result) == 6

        # Should fail with both sprites and explicit dimensions that don't match
        sprites = create_test_sprite_list(4)
        with pytest.raises(ValueError, match="sprite count \\(4\\) does not match rows \\* cols \\(6\\)"):
            arrange_grid(sprites, rows=2, cols=3, start_x=0, start_y=0)

    def test_arrange_circle_exactly_one_of_sprites_or_count_required(self):
        """Test that arrange_circle requires exactly one of sprites or count."""
        # Should work with sprites provided
        sprites = create_test_sprite_list(4)
        result = arrange_circle(sprites, center_x=100, center_y=100)
        assert len(result) == 4

        # Should work with count provided
        result = arrange_circle(count=4, center_x=100, center_y=100)
        assert len(result) == 4

        # Should fail with neither
        with pytest.raises(ValueError, match="When \\*sprites\\* is None you must supply a positive \\*count\\*"):
            arrange_circle()

        # Should fail with both
        sprites = create_test_sprite_list(4)
        with pytest.raises(ValueError, match="Cannot specify both 'sprites' and 'count'"):
            arrange_circle(sprites, count=6, center_x=100, center_y=100)

    def test_all_arrange_functions_parameter_validation(self):
        """Test parameter validation for all arrange functions."""
        functions_requiring_count = [
            (arrange_line, {"start_x": 0, "start_y": 0}),
            (arrange_circle, {"center_x": 100, "center_y": 100}),
            (arrange_v_formation, {"apex_x": 100, "apex_y": 100}),
            (arrange_diamond, {"center_x": 100, "center_y": 100}),
            (arrange_triangle, {"apex_x": 100, "apex_y": 100}),
            (arrange_arc, {"center_x": 100, "center_y": 100, "radius": 50, "start_angle": 0, "end_angle": 180}),
            (arrange_cross, {"center_x": 100, "center_y": 100}),
            (arrange_arrow, {"tip_x": 100, "tip_y": 100}),
        ]

        functions_with_implicit_count = [
            (arrange_grid, {"rows": 2, "cols": 3, "start_x": 0, "start_y": 0}),
            (arrange_hexagonal_grid, {"rows": 2, "cols": 3, "start_x": 0, "start_y": 0}),
            (arrange_concentric_rings, {"center_x": 100, "center_y": 100, "radii": [50], "sprites_per_ring": [4]}),
        ]

        # Test functions that require explicit count
        for func, base_kwargs in functions_requiring_count:
            # Should work with sprites
            sprites = create_test_sprite_list(4)
            result = func(sprites, **base_kwargs)
            assert len(result) == 4

            # Should work with count
            result = func(count=4, **base_kwargs)
            assert len(result) == 4

            # Should fail with both
            sprites = create_test_sprite_list(4)
            with pytest.raises(ValueError, match="Cannot specify both 'sprites' and 'count'"):
                func(sprites, count=6, **base_kwargs)

        # Test functions with implicit count calculation
        for func, base_kwargs in functions_with_implicit_count:
            # Should work with sprites (matching expected count)
            expected_count = self._calculate_expected_count(func, base_kwargs)
            sprites = create_test_sprite_list(expected_count)
            result = func(sprites, **base_kwargs)
            assert len(result) == expected_count

            # Should work without sprites (creates sprites)
            result = func(**base_kwargs)
            assert len(result) == expected_count

    def _calculate_expected_count(self, func, kwargs):
        """Calculate expected sprite count for functions with implicit count."""
        if func == arrange_grid or func == arrange_hexagonal_grid:
            return kwargs["rows"] * kwargs["cols"]
        elif func == arrange_concentric_rings:
            return sum(kwargs["sprites_per_ring"])
        else:
            return 1  # Default for unknown functions


# ================================================================================
# SPRITE POOL TESTS
# ================================================================================


class TestSpritePool:
    """Test SpritePool functionality."""

    def test_sprite_pool_creation(self):
        """Test SpritePool creation with factory and max_size."""
        from actions.pools import SpritePool

        def make_enemy():
            return arcade.Sprite(":resources:images/enemies/bee.png", scale=0.5)

        pool = SpritePool(make_enemy, max_size=100)
        assert pool.max_size == 100
        assert len(pool._inactive_sprites) == 0
        assert len(pool._active_sprites) == 0

    def test_sprite_pool_acquire_basic(self):
        """Test basic acquire functionality."""
        from actions.pools import SpritePool

        def make_block():
            return arcade.Sprite(":resources:images/items/star.png", scale=0.8)

        pool = SpritePool(make_block, max_size=50)

        # Acquire some sprites
        sprites = pool.acquire(5)
        assert len(sprites) == 5

        # All sprites should be invisible and unattached
        for sprite in sprites:
            assert not sprite.visible
            assert len(sprite.sprite_lists) == 0
            assert sprite.center_x == 0  # Default position
            assert sprite.center_y == 0

        # Pool should track them as active
        assert len(pool._active_sprites) == 5
        assert len(pool._inactive_sprites) == 0

    def test_sprite_pool_acquire_creates_new_sprites(self):
        """Test that acquire creates new sprites when pool is empty."""
        from actions.pools import SpritePool

        call_count = 0

        def make_tracked_sprite():
            nonlocal call_count
            call_count += 1
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.test_id = call_count  # Add tracking
            return sprite

        pool = SpritePool(make_tracked_sprite, max_size=10)

        sprites = pool.acquire(3)
        assert len(sprites) == 3
        assert call_count == 3  # Should have called factory 3 times

        # Each sprite should have unique test_id
        test_ids = [sprite.test_id for sprite in sprites]
        assert len(set(test_ids)) == 3

    def test_sprite_pool_release_basic(self):
        """Test basic release functionality."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=20)

        # Acquire and modify sprites
        sprites = pool.acquire(3)
        for i, sprite in enumerate(sprites):
            sprite.center_x = 100 + i * 50
            sprite.center_y = 200 + i * 30
            sprite.visible = True
            sprite.alpha = 128

        # Add to a sprite list
        sprite_list = arcade.SpriteList()
        for sprite in sprites:
            sprite_list.append(sprite)

        # Release sprites back to pool
        pool.release(sprites)

        # Sprites should be hidden and detached
        for sprite in sprites:
            assert not sprite.visible
            assert sprite.alpha == 255  # Reset to full alpha
            assert len(sprite.sprite_lists) == 0
            assert sprite.center_x == 0  # Reset position
            assert sprite.center_y == 0

        # Pool should track them as inactive
        assert len(pool._active_sprites) == 0
        assert len(pool._inactive_sprites) == 3

    def test_sprite_pool_release_removes_from_sprite_lists(self):
        """Test that release removes sprites from all sprite lists."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=20)
        sprites = pool.acquire(2)

        # Add to multiple sprite lists
        list1 = arcade.SpriteList()
        list2 = arcade.SpriteList()
        for sprite in sprites:
            list1.append(sprite)
            list2.append(sprite)

        assert len(list1) == 2
        assert len(list2) == 2

        # Release sprites
        pool.release(sprites)

        # Should be removed from all lists
        assert len(list1) == 0
        assert len(list2) == 0
        for sprite in sprites:
            assert len(sprite.sprite_lists) == 0

    def test_sprite_pool_acquire_reuses_released_sprites(self):
        """Test that acquire reuses previously released sprites."""
        from actions.pools import SpritePool

        call_count = 0

        def make_tracked_sprite():
            nonlocal call_count
            call_count += 1
            sprite = arcade.Sprite(":resources:images/items/star.png")
            sprite.test_id = call_count
            return sprite

        pool = SpritePool(make_tracked_sprite, max_size=10)

        # Acquire, then release
        sprites = pool.acquire(3)
        original_ids = [sprite.test_id for sprite in sprites]
        pool.release(sprites)

        # Acquire again - should reuse same sprites
        new_sprites = pool.acquire(3)
        new_ids = [sprite.test_id for sprite in new_sprites]

        # Should reuse sprites (same IDs) and not call factory again
        assert call_count == 3  # Still only 3 calls
        assert set(original_ids) == set(new_ids)

    def test_sprite_pool_assign_basic(self):
        """Test basic assign functionality."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=20)

        # Create external sprites
        external_sprites = [arcade.Sprite(":resources:images/enemies/bee.png") for _ in range(3)]
        for i, sprite in enumerate(external_sprites):
            sprite.center_x = 100 + i * 50
            sprite.visible = True

        # Assign to pool
        pool.assign(external_sprites)

        # Sprites should be hidden and reset
        for sprite in external_sprites:
            assert not sprite.visible
            assert sprite.center_x == 0
            assert sprite.center_y == 0
            assert len(sprite.sprite_lists) == 0

        # Pool should track them as inactive
        assert len(pool._inactive_sprites) == 3
        assert len(pool._active_sprites) == 0

    def test_sprite_pool_assign_then_acquire(self):
        """Test that assigned sprites can be acquired later."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=20)

        # Create and assign external sprites
        external_sprites = [arcade.Sprite(":resources:images/enemies/bee.png") for _ in range(2)]
        for sprite in external_sprites:
            sprite.test_marker = "external"  # Mark them

        pool.assign(external_sprites)

        # Acquire sprites - should get the assigned ones
        acquired = pool.acquire(2)
        assert len(acquired) == 2

        # Should get the external sprites back
        markers = [sprite.test_marker for sprite in acquired if hasattr(sprite, "test_marker")]
        assert len(markers) == 2
        assert all(marker == "external" for marker in markers)

    def test_sprite_pool_max_size_enforcement(self):
        """Test that max_size prevents runaway growth."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=5)

        # Try to assign more sprites than max_size
        many_sprites = [arcade.Sprite(":resources:images/enemies/bee.png") for _ in range(10)]

        with pytest.raises(ValueError, match="Cannot assign .* sprites.*would exceed max_size"):
            pool.assign(many_sprites)

        # Pool should be unaffected
        assert len(pool._inactive_sprites) == 0

    def test_sprite_pool_max_size_with_acquire(self):
        """Test max_size behavior with acquire operations."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=5)

        # Should be able to acquire up to max_size
        sprites = pool.acquire(5)
        assert len(sprites) == 5

        # Should raise error when trying to acquire more
        with pytest.raises(ValueError, match="Cannot acquire .* sprites.*would exceed max_size"):
            pool.acquire(1)

    def test_sprite_pool_partial_release(self):
        """Test releasing only some of the acquired sprites."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=10)

        sprites = pool.acquire(5)
        assert len(pool._active_sprites) == 5

        # Release only some sprites
        pool.release(sprites[:2])

        assert len(pool._active_sprites) == 3
        assert len(pool._inactive_sprites) == 2

    def test_sprite_pool_release_non_active_sprites_ignored(self):
        """Test that releasing non-active sprites is safely ignored."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png")

        pool = SpritePool(make_sprite, max_size=10)

        # Create external sprite not from pool
        external_sprite = arcade.Sprite(":resources:images/items/star.png")

        # Should not raise error, but should be ignored
        pool.release([external_sprite])

        assert len(pool._active_sprites) == 0
        assert len(pool._inactive_sprites) == 0


# ================================================================================
# INTEGRATION TESTS - RECOMMENDED USAGE PATTERNS
# ================================================================================


class TestZeroAllocationIntegration:
    """Test the recommended zero-allocation usage patterns."""

    def test_recommended_usage_pattern_boot_time(self):
        """Test the boot-time setup pattern from the requirements."""
        from actions.pools import SpritePool

        def make_block():
            sprite = arcade.Sprite(":resources:images/items/star.png", scale=0.8)
            return sprite

        # Boot-time setup
        pool = SpritePool(make_block, max_size=300)
        blocks = pool.acquire(150)

        # Arrange in formation
        arranged_blocks = arrange_grid(sprites=blocks, rows=30, cols=5, start_x=0, start_y=0)

        # Verify arrangement worked
        assert len(arranged_blocks) == 150
        # arrange_grid should work with lists and return a SpriteList
        assert isinstance(arranged_blocks, arcade.SpriteList)

        # Verify positions are set
        first_block = blocks[0]
        assert first_block.center_x == 0
        assert first_block.center_y == 0

        second_block = blocks[1]  # Second in first row
        assert second_block.center_x == 60  # Default spacing_x
        assert second_block.center_y == 0

        # Return to pool (invisible & neutral)
        pool.assign(blocks)

        # Verify sprites are hidden and reset
        for block in blocks:
            assert not block.visible
            assert block.center_x == 0
            assert block.center_y == 0

    def test_recommended_usage_pattern_wave_spawning(self):
        """Test the in-wave spawning pattern from the requirements."""
        from actions.pools import SpritePool

        def make_block():
            return arcade.Sprite(":resources:images/items/star.png", scale=0.5)

        # Setup pool
        pool = SpritePool(make_block, max_size=300)

        # Simulate wave spawning
        WINDOW_WIDTH = 800
        TUNNEL_HEIGHT = 200
        shield_width = 10

        shield = pool.acquire(shield_width * 30)  # width * 30 sprites

        arrange_grid(
            sprites=shield,
            rows=30,
            cols=shield_width,
            start_x=WINDOW_WIDTH + 50,  # Off-screen start
            start_y=TUNNEL_HEIGHT,
        )

        # Verify shield arrangement
        assert len(shield) == 300

        # First sprite should be at start position
        assert shield[0].center_x == WINDOW_WIDTH + 50
        assert shield[0].center_y == TUNNEL_HEIGHT

        # Sprites should form a grid
        # Second sprite (same row, next column)
        assert shield[1].center_x == WINDOW_WIDTH + 50 + 60  # spacing_x
        assert shield[1].center_y == TUNNEL_HEIGHT

        # Sprite in second row
        assert shield[shield_width].center_x == WINDOW_WIDTH + 50
        assert shield[shield_width].center_y == TUNNEL_HEIGHT + 50  # spacing_y

        # Return sprites to pool when wave ends
        pool.release(shield)

        # Verify all sprites are available for next wave
        assert len(pool._inactive_sprites) == 300
        assert len(pool._active_sprites) == 0

    def test_zero_allocation_no_sprite_creation_during_gameplay(self):
        """Test that no new sprites are created during gameplay with proper pooling."""
        from actions.pools import SpritePool

        creation_count = 0

        def tracked_factory():
            nonlocal creation_count
            creation_count += 1
            return arcade.Sprite(":resources:images/items/star.png")

        # Pre-allocate maximum sprites
        pool = SpritePool(tracked_factory, max_size=100)
        initial_sprites = pool.acquire(100)
        pool.assign(initial_sprites)  # Put them back in pool

        assert creation_count == 100  # All sprites created during setup

        # Simulate multiple waves without creating new sprites
        for wave in range(10):
            # Acquire sprites for this wave
            wave_sprites = pool.acquire(20)

            # Position them
            arrange_line(sprites=wave_sprites, start_x=wave * 100, start_y=300)

            # Simulate wave completion
            pool.release(wave_sprites)

        # No new sprites should have been created
        assert creation_count == 100

    def test_sprite_pool_with_all_arrange_functions(self):
        """Test that SpritePool works with all arrange functions."""
        from actions.pools import SpritePool

        def make_sprite():
            return arcade.Sprite(":resources:images/items/star.png", scale=0.6)

        pool = SpritePool(make_sprite, max_size=50)

        # Test each arrange function with pooled sprites
        test_cases = [
            (arrange_line, {"start_x": 0, "start_y": 0}, 5),
            (arrange_grid, {"rows": 2, "cols": 3, "start_x": 100, "start_y": 100}, 6),
            (arrange_circle, {"center_x": 200, "center_y": 200, "radius": 50}, 8),
            (arrange_v_formation, {"apex_x": 300, "apex_y": 300}, 7),
            (arrange_diamond, {"center_x": 400, "center_y": 400}, 9),
            (arrange_triangle, {"apex_x": 500, "apex_y": 500}, 6),
            (arrange_hexagonal_grid, {"rows": 2, "cols": 2, "start_x": 600, "start_y": 600}, 4),
            (arrange_arc, {"center_x": 700, "center_y": 700, "radius": 60, "start_angle": 0, "end_angle": 180}, 5),
            (arrange_concentric_rings, {"center_x": 100, "center_y": 500, "radii": [40], "sprites_per_ring": [6]}, 6),
            (arrange_cross, {"center_x": 200, "center_y": 500}, 9),
            (arrange_arrow, {"tip_x": 300, "tip_y": 500}, 7),
        ]

        for arrange_func, kwargs, sprite_count in test_cases:
            # Acquire sprites from pool
            sprites = pool.acquire(sprite_count)

            # Apply arrangement
            result = arrange_func(sprites=sprites, **kwargs)

            # Should return a SpriteList containing the sprites
            assert isinstance(result, arcade.SpriteList)
            assert len(result) == sprite_count

            # Verify sprites are positioned (not at origin)
            positioned_sprites = [s for s in sprites if s.center_x != 0 or s.center_y != 0]
            assert len(positioned_sprites) > 0, f"{arrange_func.__name__} should position sprites"

            # Return to pool
            pool.release(sprites)

    def test_backward_compatibility_existing_api_unchanged(self):
        """Test that existing API still works unchanged."""
        # All existing calls should work exactly as before

        # Create sprites without pool - should work as before
        line_sprites = arrange_line(count=5, start_x=100, start_y=200)
        assert len(line_sprites) == 5
        assert line_sprites[0].center_x == 100

        grid_sprites = arrange_grid(rows=2, cols=3, start_x=200, start_y=300)
        assert len(grid_sprites) == 6

        circle_sprites = arrange_circle(count=8, center_x=300, center_y=400, radius=80)
        assert len(circle_sprites) == 8

        # Arrange existing sprites - should work as before
        existing_sprites = create_test_sprite_list(4)
        result = arrange_circle(existing_sprites, center_x=400, center_y=500, radius=100)
        assert result is existing_sprites
        assert len(result) == 4
