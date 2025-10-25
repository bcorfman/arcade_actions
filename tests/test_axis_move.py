"""
Tests for axis-specific movement actions (MoveXUntil, MoveYUntil).

These tests verify that axis-specific actions only affect their respective axes
and can be safely composed via parallel() for orthogonal motion.
"""

import pytest
import arcade
from actions.base import Action
from actions.conditional import infinite
from actions.composite import parallel
from actions.axis_move import MoveXUntil, MoveYUntil


def create_test_sprite() -> arcade.Sprite:
    """Create a test sprite for movement tests."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


def create_test_sprite_list() -> arcade.SpriteList:
    """Create a test sprite list for movement tests."""
    sprites = arcade.SpriteList()
    for i in range(3):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite.center_y = 100 + i * 30
        sprites.append(sprite)
    return sprites


class TestMoveXUntil:
    """Test suite for MoveXUntil - X-axis only movement."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_x_until_constructor(self):
        """Test MoveXUntil constructor with all parameters."""
        bounds = (0, 0, 800, 600)
        on_stop_called = False

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        def velocity_provider():
            return (5, 0)

        def on_boundary_enter(sprite, axis, side):
            pass

        def on_boundary_exit(sprite, axis, side):
            pass

        action = MoveXUntil(
            velocity=(3, 0),
            condition=infinite,
            on_stop=on_stop,
            bounds=bounds,
            boundary_behavior="bounce",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )

        assert action.target_velocity == (3, 0)
        assert action.current_velocity == (3, 0)
        assert action.bounds == bounds
        assert action.boundary_behavior == "bounce"
        assert action.velocity_provider == velocity_provider
        assert action.on_boundary_enter == on_boundary_enter
        assert action.on_boundary_exit == on_boundary_exit

    def test_move_x_until_only_affects_x_axis(self, test_sprite):
        """Test that MoveXUntil only modifies change_x, not change_y."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveXUntil(velocity=(5, 0), condition=infinite)
        action.apply(test_sprite)

        # Should only set change_x, leave change_y untouched
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 0

    def test_move_x_until_preserves_existing_y_velocity(self, test_sprite):
        """Test that MoveXUntil preserves existing Y velocity."""
        test_sprite.change_x = 0
        test_sprite.change_y = 10  # Pre-existing Y velocity

        action = MoveXUntil(velocity=(5, 0), condition=infinite)
        action.apply(test_sprite)

        # Should set change_x but preserve change_y
        assert test_sprite.change_x == 5
        assert test_sprite.change_y == 10

    def test_move_x_until_clone(self):
        """Test MoveXUntil clone functionality."""
        bounds = (0, 0, 800, 600)
        action = MoveXUntil(velocity=(4, 0), condition=infinite, bounds=bounds, boundary_behavior="wrap")

        cloned = action.clone()

        assert isinstance(cloned, MoveXUntil)
        assert cloned.target_velocity == (4, 0)
        assert cloned.bounds == bounds
        assert cloned.boundary_behavior == "wrap"
        assert cloned is not action  # Different instance

    def test_move_x_until_reset(self, test_sprite):
        """Test MoveXUntil reset functionality."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveXUntil(velocity=(6, 0), condition=infinite)
        action.apply(test_sprite)

        # Modify velocity
        action.current_velocity = (2, 0)
        test_sprite.change_x = 2

        # Reset should restore original velocity
        action.reset()
        assert action.current_velocity == (6, 0)
        assert test_sprite.change_x == 6
        assert test_sprite.change_y == 0  # Still untouched

    def test_move_x_until_sprite_list(self, test_sprite_list):
        """Test MoveXUntil with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = MoveXUntil(velocity=(7, 0), condition=infinite)
        action.apply(test_sprite_list)

        # All sprites should have X velocity, no Y velocity
        for sprite in test_sprite_list:
            assert sprite.change_x == 7
            assert sprite.change_y == 0


class TestMoveYUntil:
    """Test suite for MoveYUntil - Y-axis only movement."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_y_until_constructor(self):
        """Test MoveYUntil constructor with all parameters."""
        bounds = (0, 0, 800, 600)
        on_stop_called = False

        def on_stop():
            nonlocal on_stop_called
            on_stop_called = True

        def velocity_provider():
            return (0, 5)

        def on_boundary_enter(sprite, axis, side):
            pass

        def on_boundary_exit(sprite, axis, side):
            pass

        action = MoveYUntil(
            velocity=(0, 3),
            condition=infinite,
            on_stop=on_stop,
            bounds=bounds,
            boundary_behavior="bounce",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )

        assert action.target_velocity == (0, 3)
        assert action.current_velocity == (0, 3)
        assert action.bounds == bounds
        assert action.boundary_behavior == "bounce"
        assert action.velocity_provider == velocity_provider
        assert action.on_boundary_enter == on_boundary_enter
        assert action.on_boundary_exit == on_boundary_exit

    def test_move_y_until_only_affects_y_axis(self, test_sprite):
        """Test that MoveYUntil only modifies change_y, not change_x."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 5), condition=infinite)
        action.apply(test_sprite)

        # Should only set change_y, leave change_x untouched
        assert test_sprite.change_x == 0
        assert test_sprite.change_y == 5

    def test_move_y_until_preserves_existing_x_velocity(self, test_sprite):
        """Test that MoveYUntil preserves existing X velocity."""
        test_sprite.change_x = 10  # Pre-existing X velocity
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 5), condition=infinite)
        action.apply(test_sprite)

        # Should set change_y but preserve change_x
        assert test_sprite.change_x == 10
        assert test_sprite.change_y == 5

    def test_move_y_until_clone(self):
        """Test MoveYUntil clone functionality."""
        bounds = (0, 0, 800, 600)
        action = MoveYUntil(velocity=(0, 4), condition=infinite, bounds=bounds, boundary_behavior="wrap")

        cloned = action.clone()

        assert isinstance(cloned, MoveYUntil)
        assert cloned.target_velocity == (0, 4)
        assert cloned.bounds == bounds
        assert cloned.boundary_behavior == "wrap"
        assert cloned is not action  # Different instance

    def test_move_y_until_reset(self, test_sprite):
        """Test MoveYUntil reset functionality."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 6), condition=infinite)
        action.apply(test_sprite)

        # Modify velocity
        action.current_velocity = (0, 2)
        test_sprite.change_y = 2

        # Reset should restore original velocity
        action.reset()
        assert action.current_velocity == (0, 6)
        assert test_sprite.change_x == 0  # Still untouched
        assert test_sprite.change_y == 6

    def test_move_y_until_sprite_list(self, test_sprite_list):
        """Test MoveYUntil with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        action = MoveYUntil(velocity=(0, 7), condition=infinite)
        action.apply(test_sprite_list)

        # All sprites should have Y velocity, no X velocity
        for sprite in test_sprite_list:
            assert sprite.change_x == 0
            assert sprite.change_y == 7


class TestAxisComposition:
    """Test suite for composing axis-specific actions via parallel()."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_x_and_y_movement(self, test_sprite):
        """Test composing MoveXUntil and MoveYUntil via parallel()."""
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        x_action = MoveXUntil(velocity=(-3, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, 2), condition=infinite)

        parallel(x_action, y_action).apply(test_sprite)

        # Should have both X and Y velocities
        assert test_sprite.change_x == -3
        assert test_sprite.change_y == 2

    def test_parallel_x_and_y_with_different_boundaries(self, test_sprite):
        """Test composing X and Y actions with different boundary behaviors."""
        test_sprite.center_x = 100  # At left boundary
        test_sprite.center_y = 100  # At bottom boundary
        test_sprite.change_x = 0
        test_sprite.change_y = 0

        bounds = (100, 100, 800, 600)

        x_action = MoveXUntil(
            velocity=(-5, 0),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="limit",  # X limited
        )
        y_action = MoveYUntil(
            velocity=(0, -5),
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",  # Y bounces
        )

        parallel(x_action, y_action).apply(test_sprite)

        # Both velocities should be set initially
        assert test_sprite.change_x == -5
        assert test_sprite.change_y == -5

        # Test that the actions were created with correct boundary behaviors
        assert x_action.boundary_behavior == "limit"
        assert y_action.boundary_behavior == "bounce"

    def test_parallel_with_sprite_list(self, test_sprite_list):
        """Test parallel composition with sprite list."""
        for sprite in test_sprite_list:
            sprite.change_x = 0
            sprite.change_y = 0

        x_action = MoveXUntil(velocity=(4, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, -2), condition=infinite)

        parallel(x_action, y_action).apply(test_sprite_list)

        # All sprites should have both velocities
        for sprite in test_sprite_list:
            assert sprite.change_x == 4
            assert sprite.change_y == -2


class TestAxisDurationAndVelocityProvider:
    """Test suite for duration and velocity_provider in axis-specific actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_x_until_with_duration(self):
        """Test MoveXUntil with duration-based condition."""
        from actions.conditional import duration

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveXUntil(
            velocity=(5, 0),
            condition=duration(0.1),
        )
        action.apply(sprite)

        # Should be active initially
        assert not action.done

        # Update for less than duration
        Action.update_all(0.05)
        assert not action.done

        # Update to exceed duration
        Action.update_all(0.06)
        assert action.done

    def test_move_y_until_with_duration(self):
        """Test MoveYUntil with duration-based condition."""
        from actions.conditional import duration

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveYUntil(
            velocity=(0, 5),
            condition=duration(0.1),
        )
        action.apply(sprite)

        # Should be active initially
        assert not action.done

        # Update for less than duration
        Action.update_all(0.05)
        assert not action.done

        # Update to exceed duration
        Action.update_all(0.06)
        assert action.done

    def test_move_x_until_with_velocity_provider(self):
        """Test MoveXUntil with velocity_provider."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        sprite.change_y = 10  # Pre-existing Y velocity

        velocity_state = {"vx": 5}

        def velocity_provider():
            return (velocity_state["vx"], 0)

        action = MoveXUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=velocity_provider,
        )
        action.apply(sprite)

        Action.update_all(1 / 60)
        assert sprite.change_x == 5
        assert sprite.change_y == 10  # Y preserved

        # Change velocity via provider
        velocity_state["vx"] = 10
        Action.update_all(1 / 60)
        assert sprite.change_x == 10
        assert sprite.change_y == 10  # Y still preserved

    def test_move_y_until_with_velocity_provider(self):
        """Test MoveYUntil with velocity_provider."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        sprite.change_x = 10  # Pre-existing X velocity

        velocity_state = {"vy": 5}

        def velocity_provider():
            return (0, velocity_state["vy"])

        action = MoveYUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=velocity_provider,
        )
        action.apply(sprite)

        Action.update_all(1 / 60)
        assert sprite.change_x == 10  # X preserved
        assert sprite.change_y == 5

        # Change velocity via provider
        velocity_state["vy"] = 10
        Action.update_all(1 / 60)
        assert sprite.change_x == 10  # X still preserved
        assert sprite.change_y == 10

    def test_move_x_until_velocity_provider_exception(self):
        """Test MoveXUntil handles velocity_provider exceptions gracefully."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        call_count = {"count": 0}

        def failing_provider():
            call_count["count"] += 1
            if call_count["count"] > 1:
                raise RuntimeError("Provider failed!")
            return (5, 0)

        action = MoveXUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=failing_provider,
        )
        action.apply(sprite)

        # First call should work
        Action.update_all(1 / 60)
        assert sprite.change_x == 5

        # Second call should fail but action continues with current velocity
        Action.update_all(1 / 60)
        assert not action.done  # Should still be running

        action.stop()

    def test_move_y_until_velocity_provider_exception(self):
        """Test MoveYUntil handles velocity_provider exceptions gracefully."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        call_count = {"count": 0}

        def failing_provider():
            call_count["count"] += 1
            if call_count["count"] > 1:
                raise RuntimeError("Provider failed!")
            return (0, 5)

        action = MoveYUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=failing_provider,
        )
        action.apply(sprite)

        # First call should work
        Action.update_all(1 / 60)
        assert sprite.change_y == 5

        # Second call should fail but action continues with current velocity
        Action.update_all(1 / 60)
        assert not action.done  # Should still be running

        action.stop()

    def test_move_x_until_duration_with_on_stop(self):
        """Test MoveXUntil duration completion calls on_stop."""
        from actions.conditional import duration

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        on_stop_called = {"called": False}

        def on_stop():
            on_stop_called["called"] = True

        action = MoveXUntil(
            velocity=(5, 0),
            condition=duration(0.1),
            on_stop=on_stop,
        )
        action.apply(sprite)

        # Update to exceed duration
        Action.update_all(0.11)

        assert action.done
        assert on_stop_called["called"]

    def test_move_y_until_duration_with_on_stop(self):
        """Test MoveYUntil duration completion calls on_stop."""
        from actions.conditional import duration

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        on_stop_called = {"called": False}

        def on_stop():
            on_stop_called["called"] = True

        action = MoveYUntil(
            velocity=(0, 5),
            condition=duration(0.1),
            on_stop=on_stop,
        )
        action.apply(sprite)

        # Update to exceed duration
        Action.update_all(0.11)

        assert action.done
        assert on_stop_called["called"]


class TestAxisBoundaryBehaviors:
    """Test suite for boundary behaviors in axis-specific actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_x_until_bounce_behavior(self):
        """Test that MoveXUntil correctly bounces off X-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 300

        boundary_hits = []

        def on_boundary(s, axis, side):
            boundary_hits.append((axis, side))

        action = MoveXUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="bounce",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move right towards boundary
        for _ in range(25):  # Should hit right boundary at x=200
            Action.update_all(1 / 60)
            sprite.update()

        # Should have bounced and be moving left
        assert sprite.change_x < 0, "Should be moving left after bouncing off right boundary"
        assert 0 < sprite.center_x <= 200, "Should be within bounds after bounce"
        assert ("x", "right") in boundary_hits, "Should have hit right boundary"

        # Continue moving left towards left boundary
        for _ in range(50):  # Should hit left boundary at x=0
            Action.update_all(1 / 60)
            sprite.update()

        # Should have bounced again and be moving right
        assert sprite.change_x > 0, "Should be moving right after bouncing off left boundary"
        assert 0 <= sprite.center_x < 200, "Should be within bounds after second bounce"
        assert ("x", "left") in boundary_hits, "Should have hit left boundary"

        action.stop()

    def test_move_y_until_bounce_behavior(self):
        """Test that MoveYUntil correctly bounces off Y-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 100

        boundary_hits = []

        def on_boundary(s, axis, side):
            boundary_hits.append((axis, side))

        action = MoveYUntil(
            velocity=(0, 5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="bounce",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move up towards boundary
        for _ in range(25):  # Should hit top boundary at y=200
            Action.update_all(1 / 60)
            sprite.update()

        # Should have bounced and be moving down
        assert sprite.change_y < 0, "Should be moving down after bouncing off top boundary"
        assert 0 < sprite.center_y <= 200, "Should be within bounds after bounce"
        assert ("y", "top") in boundary_hits, "Should have hit top boundary"

        # Continue moving down towards bottom boundary
        for _ in range(50):  # Should hit bottom boundary at y=0
            Action.update_all(1 / 60)
            sprite.update()

        # Should have bounced again and be moving up
        assert sprite.change_y > 0, "Should be moving up after bouncing off bottom boundary"
        assert 0 <= sprite.center_y < 200, "Should be within bounds after second bounce"
        assert ("y", "bottom") in boundary_hits, "Should have hit bottom boundary"

        action.stop()

    def test_move_x_until_wrap_behavior(self):
        """Test that MoveXUntil correctly wraps around X-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 180
        sprite.center_y = 300

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1

        action = MoveXUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="wrap",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move right past boundary
        for _ in range(10):  # Should wrap from right to left
            Action.update_all(1 / 60)
            sprite.update()

        # Should have wrapped to left side
        assert sprite.center_x < 50, "Should have wrapped to left side"
        assert sprite.change_x == 5, "Velocity should remain unchanged after wrap"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_x_until_wrap_left_boundary(self):
        """Test that MoveXUntil wraps when hitting left boundary."""
        sprite = arcade.Sprite()
        sprite.center_x = 20
        sprite.center_y = 300

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert side == "left", "Should hit left boundary"

        action = MoveXUntil(
            velocity=(-5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="wrap",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move left past boundary
        for _ in range(10):  # Should wrap from left to right
            Action.update_all(1 / 60)
            sprite.update()

        # Should have wrapped to right side
        assert sprite.center_x > 150, "Should have wrapped to right side"
        assert sprite.change_x == -5, "Velocity should remain unchanged after wrap"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_x_until_limit_left_boundary(self):
        """Test that MoveXUntil limits movement at left X-axis boundary."""
        sprite = arcade.Sprite()
        sprite.center_x = 20
        sprite.center_y = 300

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert axis == "x", "Should only trigger on X-axis"
            assert side == "left", "Should hit left boundary"

        action = MoveXUntil(
            velocity=(-5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move left to boundary
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Should be stopped at boundary
        assert sprite.center_x == 0, "Should be stopped at left boundary"
        assert sprite.change_x == 0, "Velocity should be zero at limit"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_y_until_wrap_behavior(self):
        """Test that MoveYUntil correctly wraps around Y-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 180

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1

        action = MoveYUntil(
            velocity=(0, 5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="wrap",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move up past boundary
        for _ in range(10):  # Should wrap from top to bottom
            Action.update_all(1 / 60)
            sprite.update()

        # Should have wrapped to bottom side
        assert sprite.center_y < 50, "Should have wrapped to bottom side"
        assert sprite.change_y == 5, "Velocity should remain unchanged after wrap"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_y_until_wrap_bottom_boundary(self):
        """Test that MoveYUntil wraps when hitting bottom boundary."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 20

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert side == "bottom", "Should hit bottom boundary"

        action = MoveYUntil(
            velocity=(0, -5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="wrap",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move down past boundary
        for _ in range(10):  # Should wrap from bottom to top
            Action.update_all(1 / 60)
            sprite.update()

        # Should have wrapped to top side
        assert sprite.center_y > 150, "Should have wrapped to top side"
        assert sprite.change_y == -5, "Velocity should remain unchanged after wrap"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_y_until_limit_bottom_boundary(self):
        """Test that MoveYUntil limits movement at bottom Y-axis boundary."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 20

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert axis == "y", "Should only trigger on Y-axis"
            assert side == "bottom", "Should hit bottom boundary"

        action = MoveYUntil(
            velocity=(0, -5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move down to boundary
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Should be stopped at boundary
        assert sprite.center_y == 0, "Should be stopped at bottom boundary"
        assert sprite.change_y == 0, "Velocity should be zero at limit"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_x_until_limit_behavior(self):
        """Test that MoveXUntil correctly limits movement at X-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 180
        sprite.center_y = 300

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert axis == "x", "Should only trigger on X-axis"
            assert side == "right", "Should hit right boundary"

        action = MoveXUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move right to boundary
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Should be stopped at boundary
        assert sprite.center_x == 200, "Should be stopped at right boundary"
        assert sprite.change_x == 0, "Velocity should be zero at limit"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_y_until_limit_behavior(self):
        """Test that MoveYUntil correctly limits movement at Y-axis boundaries."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 180

        boundary_hit = {"count": 0}

        def on_boundary(s, axis, side):
            boundary_hit["count"] += 1
            assert axis == "y", "Should only trigger on Y-axis"
            assert side == "top", "Should hit top boundary"

        action = MoveYUntil(
            velocity=(0, 5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary,
        )
        action.apply(sprite)

        # Move up to boundary
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Should be stopped at boundary
        assert sprite.center_y == 200, "Should be stopped at top boundary"
        assert sprite.change_y == 0, "Velocity should be zero at limit"
        assert boundary_hit["count"] >= 1, "Boundary callback should have been called"

        action.stop()

    def test_move_x_until_preserves_y_velocity_with_bounce(self):
        """Test that MoveXUntil with bounce behavior doesn't affect Y velocity."""
        sprite = arcade.Sprite()
        sprite.center_x = 180
        sprite.center_y = 300
        sprite.change_y = 3  # Set an initial Y velocity

        action = MoveXUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 600),
            boundary_behavior="bounce",
        )
        action.apply(sprite)

        # Move and bounce
        for _ in range(30):
            Action.update_all(1 / 60)

        # Y velocity should be preserved throughout
        assert sprite.change_y == 3, "Y velocity should remain unchanged despite X bounce"

        action.stop()

    def test_move_y_until_preserves_x_velocity_with_bounce(self):
        """Test that MoveYUntil with bounce behavior doesn't affect X velocity."""
        sprite = arcade.Sprite()
        sprite.center_x = 300
        sprite.center_y = 180
        sprite.change_x = 3  # Set an initial X velocity

        action = MoveYUntil(
            velocity=(0, 5),
            condition=infinite,
            bounds=(0, 0, 600, 200),
            boundary_behavior="bounce",
        )
        action.apply(sprite)

        # Move and bounce
        for _ in range(30):
            Action.update_all(1 / 60)

        # X velocity should be preserved throughout
        assert sprite.change_x == 3, "X velocity should remain unchanged despite Y bounce"

        action.stop()

    def test_composed_bounce_behavior(self):
        """Test that MoveXUntil and MoveYUntil can be composed with independent bounce behavior."""
        sprite = arcade.Sprite()
        sprite.center_x = 180
        sprite.center_y = 180

        x_action = MoveXUntil(
            velocity=(5, 0),
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="bounce",
        )

        y_action = MoveYUntil(
            velocity=(0, 3),
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="bounce",
        )

        composed = parallel(x_action, y_action)
        composed.apply(sprite)

        # Run for several bounces
        for _ in range(100):
            Action.update_all(1 / 60)

        # Both axes should be bouncing independently
        assert 0 <= sprite.center_x <= 200, "X should stay within bounds"
        assert 0 <= sprite.center_y <= 200, "Y should stay within bounds"

        # Velocities should be non-zero (bouncing)
        assert sprite.change_x != 0, "X velocity should be non-zero (bouncing)"
        assert sprite.change_y != 0, "Y velocity should be non-zero (bouncing)"

        composed.stop()


class TestAxisMoveIntegration:
    """Integration tests for axis-specific movement actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_axis_move_action_contracts(self):
        """Test that axis-specific actions follow Action contracts."""
        x_action = MoveXUntil(velocity=(1, 0), condition=infinite)
        y_action = MoveYUntil(velocity=(0, 1), condition=infinite)

        # Test that they have required Action methods
        assert hasattr(x_action, "apply")
        assert hasattr(x_action, "clone")
        assert hasattr(x_action, "reset")
        assert hasattr(x_action, "update_effect")

        assert hasattr(y_action, "apply")
        assert hasattr(y_action, "clone")
        assert hasattr(y_action, "reset")
        assert hasattr(y_action, "update_effect")

        # Test cloning
        x_clone = x_action.clone()
        y_clone = y_action.clone()

        assert isinstance(x_clone, MoveXUntil)
        assert isinstance(y_clone, MoveYUntil)
        assert x_clone.target_velocity == (1, 0)
        assert y_clone.target_velocity == (0, 1)
