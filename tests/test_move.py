"""Test suite for boundary functionality in MoveUntil action."""

import arcade

from actions import move_until
from actions.base import Action
from actions.conditional import MoveUntil, infinite
from actions.pattern import time_elapsed, create_bounce_pattern, create_patrol_pattern


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestMoveUntilBoundaries:
    """Test suite for MoveUntil boundary functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_until_with_bounce_boundaries(self):
        """Test MoveUntil with bouncing boundaries using edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is very close to right boundary (800)
        sprite.right = 795

        # Create bounds (left, bottom, right, top) - now edge-based
        bounds = (0, 0, 800, 600)

        # Move right - should hit boundary and bounce
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have hit boundary and bounced
        assert sprite.change_x < 0  # Moving left now
        assert sprite.right <= 800  # Right edge kept in bounds

    def test_move_until_with_wrap_boundaries(self):
        """Test MoveUntil with wrapping boundaries using edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is very close to right boundary
        sprite.right = 795

        bounds = (0, 0, 800, 600)

        # Move right - should wrap to left side
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to left side - left edge at left bound
        assert sprite.left == 0  # Left edge wrapped to left boundary

    def test_move_until_with_boundary_callback(self):
        """Test MoveUntil boundary callback functionality with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is near right boundary
        sprite.right = 795

        boundary_hits = []

        def on_boundary_enter(hitting_sprite, axis, side):
            boundary_hits.append((hitting_sprite, axis, side))

        bounds = (0, 0, 800, 600)
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary_enter=on_boundary_enter,
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have called boundary enter callback once on X/right
        assert len(boundary_hits) >= 1
        assert boundary_hits[0][0] == sprite
        assert boundary_hits[0][1] == "x"
        assert boundary_hits[0][2] in ("right", "left", "top", "bottom")

    def test_move_until_vertical_boundaries(self):
        """Test MoveUntil with vertical boundary interactions using edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is very close to top boundary
        sprite.top = 595

        bounds = (0, 0, 800, 600)

        # Move up - should hit top boundary and bounce
        move_until(
            sprite,
            velocity=(0, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have bounced (reversed Y velocity)
        assert sprite.change_y < 0  # Moving down now
        assert sprite.top <= 600  # Top edge kept in bounds

    def test_move_until_no_boundaries(self):
        """Test MoveUntil without boundary checking."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x

        # No bounds specified - should move normally
        move_until(sprite, velocity=(100, 0), condition=time_elapsed(1.0), tag="movement")

        Action.update_all(0.5)
        sprite.update()  # Apply velocity to position

        # Should move normally without boundary interference
        assert sprite.center_x > initial_x
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert sprite.change_x == 100  # Velocity unchanged

    def test_move_until_multiple_sprites_boundaries(self):
        """Test MoveUntil boundary checking with multiple sprites using edge-based coordinates."""
        sprites = arcade.SpriteList()
        for i in range(3):
            sprite = create_test_sprite()
            # Position sprites so their right edges are near right boundary
            sprite.right = 795 + i * 0.1
            sprites.append(sprite)

        bounds = (0, 0, 800, 600)

        move_until(
            sprites,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="group_movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprites to new positions
        for sprite in sprites:
            sprite.update()
        # Check boundaries on new positions
        Action.update_all(0.001)

        # All sprites should have bounced
        for sprite in sprites:
            assert sprite.change_x < 0  # All moving left now
            assert sprite.right <= 800  # All right edges kept in bounds

    def test_move_until_wrap_vertical_boundaries(self):
        """Test MoveUntil with vertical wrapping boundaries using edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is near top boundary
        sprite.top = 595

        bounds = (0, 0, 800, 600)

        # Move up - should wrap to bottom
        move_until(
            sprite,
            velocity=(0, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement_wrap_y",
        )

        # Update action to set velocity and apply movement
        Action.update_all(0.1)
        sprite.update()
        # Run boundary processing
        Action.update_all(0.001)

        # Should have wrapped to bottom side - bottom edge at bottom bound
        assert sprite.bottom == 0

    def test_move_until_wrap_both_axes(self):
        """Test MoveUntil with wrapping on both axes simultaneously using edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right and top edges are near boundaries
        sprite.right = 795
        sprite.top = 595

        bounds = (0, 0, 800, 600)

        # Move diagonally up-right - should wrap to (left, bottom)
        move_until(
            sprite,
            velocity=(100, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement_wrap_xy",
        )

        # Update action to set velocity and apply movement
        Action.update_all(0.1)
        sprite.update()
        # Run boundary processing
        Action.update_all(0.001)

        # Should have wrapped on both axes - edges at bounds
        assert sprite.left == 0
        assert sprite.bottom == 0

    def test_move_until_limit_debounce_x(self):
        """Limit behavior should fire one enter on approach and one exit on retreat (X) with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is near right boundary
        sprite.right = 795

        bounds = (0, 0, 800, 600)
        events: list[tuple[str, str, str]] = []

        def on_enter(s, axis, side):
            events.append(("enter", axis, side))

        def on_exit(s, axis, side):
            events.append(("exit", axis, side))

        action = move_until(
            sprite,
            velocity=(10, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
            tag="limit_debounce_x",
        )

        # Apply initial velocity and movement toward boundary
        Action.update_all(0.05)
        sprite.update()
        Action.update_all(0.001)

        # Should have exactly one enter to right on X
        assert ("enter", "x", "right") in events
        assert events.count(("enter", "x", "right")) == 1

        # Continue pushing into the boundary for a few frames - no additional enters
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()
            Action.update_all(0.001)
        assert events.count(("enter", "x", "right")) == 1

        # Now retreat from the boundary by reversing velocity
        action.set_current_velocity((-10, 0))
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        # Exactly one exit should be recorded
        assert events.count(("exit", "x", "right")) == 1

    def test_move_until_limit_debounce_y(self):
        """Limit behavior should fire one enter on approach and one exit on retreat (Y) with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is near top boundary
        sprite.top = 595

        bounds = (0, 0, 800, 600)
        events: list[tuple[str, str, str]] = []

        def on_enter(s, axis, side):
            events.append(("enter", axis, side))

        def on_exit(s, axis, side):
            events.append(("exit", axis, side))

        action = move_until(
            sprite,
            velocity=(0, 10),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
            tag="limit_debounce_y",
        )

        # Apply initial velocity and movement toward boundary
        Action.update_all(0.05)
        sprite.update()
        Action.update_all(0.001)

        # Should have exactly one enter to top on Y
        assert ("enter", "y", "top") in events
        assert events.count(("enter", "y", "top")) == 1

        # Continue pushing into the boundary for a few frames - no additional enters
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()
            Action.update_all(0.001)
        assert events.count(("enter", "y", "top")) == 1

        # Now retreat from the boundary by reversing velocity
        action.set_current_velocity((0, -10))
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        # Exactly one exit should be recorded
        assert events.count(("exit", "y", "top")) == 1


class TestPriority3_BoundaryBehaviorMethods:
    """Test boundary behavior methods for MoveUntil boundary helpers."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_wrap_behavior_left_to_right(self):
        """Test wrap boundary behavior when crossing left boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its left edge is just inside left boundary
        sprite.left = 5

        bounds = (0, 0, 800, 600)
        action = MoveUntil((-100, 0), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to right side - right edge at right bound
        assert sprite.right == 800

    def test_wrap_behavior_right_to_left(self):
        """Test wrap boundary behavior when crossing right boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is near right boundary
        sprite.right = 795

        bounds = (0, 0, 800, 600)
        action = MoveUntil((100, 0), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to left side - left edge at left bound
        assert sprite.left == 0

    def test_wrap_behavior_bottom_to_top(self):
        """Test wrap boundary behavior when crossing bottom boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its bottom edge is near bottom boundary
        sprite.bottom = 5

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, -100), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to top side - top edge at top bound
        assert sprite.top == 600

    def test_wrap_behavior_top_to_bottom(self):
        """Test wrap boundary behavior when crossing top boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is near top boundary
        sprite.top = 595

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, 100), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to bottom side - bottom edge at bottom bound
        assert sprite.bottom == 0

    def test_limit_behavior_left_boundary(self):
        """Test limit boundary behavior at left boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its left edge is left of boundary
        sprite.left = 50

        bounds = (100, 0, 800, 600)
        action = MoveUntil((-5, 0), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update action - should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity applied - left edge at left bound
        assert sprite.left == 100
        assert sprite.change_x == 0

    def test_limit_behavior_bottom_boundary(self):
        """Test limit boundary behavior at bottom boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its bottom edge is below boundary
        sprite.bottom = 50

        bounds = (0, 100, 800, 600)
        action = MoveUntil((0, -5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update action - should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity applied - bottom edge at bottom bound
        assert sprite.bottom == 100
        assert sprite.change_y == 0

    def test_limit_behavior_top_boundary(self):
        """Test limit boundary behavior at top boundary with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is above boundary
        sprite.top = 650

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, 5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity - top edge at top bound
        assert sprite.top == 600
        assert sprite.change_y == 0


class TestPriority1_VelocityProviderBoundaryCallbacks:
    """Test MoveUntil with velocity_provider and boundary callbacks - covers lines 238-248, 260-282."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_velocity_provider_boundary_enter_right(self):
        """Test velocity provider triggers boundary enter on right with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its right edge is near right boundary
        sprite.right = 795

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (100, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (100, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit right boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("x", "right") in enter_calls

    def test_velocity_provider_boundary_enter_left(self):
        """Test velocity provider triggers boundary enter on left with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its left edge is near left boundary
        sprite.left = 5

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (-100, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (-100, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit left boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("x", "left") in enter_calls

    def test_velocity_provider_boundary_enter_top(self):
        """Test velocity provider triggers boundary enter on top with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is near top boundary
        sprite.top = 595

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (0, 100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, 100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit top boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("y", "top") in enter_calls

    def test_velocity_provider_boundary_enter_bottom(self):
        """Test velocity provider triggers boundary enter on bottom with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its bottom edge is near bottom boundary
        sprite.bottom = 5

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (0, -100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, -100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit bottom boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("y", "bottom") in enter_calls

    def test_velocity_provider_boundary_exit_vertical(self):
        """Test velocity provider triggers boundary exit on vertical with edge-based coordinates."""
        sprite = create_test_sprite()
        # Position sprite so its top edge is beyond top boundary
        sprite.top = 605

        exit_calls = []
        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def on_exit(s, axis, side):
            exit_calls.append((axis, side))

        # First move down to enter boundary
        def velocity_provider():
            return (0, 100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, 100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
        )
        action.apply(sprite, tag="move")

        # First update - enter boundary
        Action.update_all(1 / 60)
        assert len(enter_calls) > 0

        # Change direction to exit boundary
        action.velocity_provider = lambda: (0, -100)

        # Next update - exit boundary
        Action.update_all(1 / 60)

        assert len(exit_calls) > 0
        assert ("y", "top") in exit_calls


class TestBounceStepBoundaryResponse:
    """Test that bounce/patrol actions respond to boundary checking when stepped after pause.

    Reproduces the issue where F6 (pause) followed by F7 (step) causes sprites
    to continue at original velocity without responding to boundaries.

    CRITICAL BUG: After F7 (step), sprites continue moving as if unpaused instead
    of staying paused and stepping frame-by-frame.
    """

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_bounce_responds_to_boundary_when_stepped_after_pause(self):
        """Test that bounce actions check boundaries during step after pause.

        Reproduces the issue where F6 (pause) followed by F7 (step) causes
        sprites to continue at original velocity without responding to boundaries.
        """
        sprite = create_test_sprite()
        sprite.center_x = 230  # Right edge = 230 + 64 = 294, close to boundary at 300
        sprite.center_y = 200

        # Create bounce pattern moving RIGHT toward boundary (like pattern_demo.py)
        bounds = (100, 100, 300, 300)
        bounce = create_bounce_pattern(velocity=(10, 0), bounds=bounds)
        bounce.apply(sprite)

        # Apply velocity once to set it on sprite (but don't move yet)
        Action.update_all(1 / 60)
        # Don't call sprite.update() yet - we want sprite to be BEFORE boundary

        # Position sprite so its right edge is just before boundary
        # Right boundary is at 300, sprite width is 128 (radius=64)
        # So center_x = 300 - 64 = 236 would put right edge at boundary
        # We want it slightly before: center_x = 235, right_edge = 299
        sprite.center_x = 235  # Right edge will be 299, just before boundary
        sprite.right = 299  # Ensure right edge is exactly at 299

        # Pause (like F6) - should save current velocity
        Action.pause_all()
        saved_velocity = bounce._paused_velocity
        assert saved_velocity[0] > 0, f"Expected saved velocity moving right, got {saved_velocity}"

        # Step (like F7) - should restore velocity AND check boundaries
        # During this step, sprite at right_edge=299 with velocity=10 would cross boundary
        Action.step_all(1 / 60)

        # Right edge before update: 299
        # Velocity: 10 (moving right)
        # After update, right edge would be: 299 + 10 = 309 (crosses boundary at 300)
        # Boundary check should reverse velocity BEFORE sprite.update() is called
        sprite_right_edge_before_update = sprite.right
        velocity_after_step_all = sprite.change_x

        # Boundary check should have run during step_all() and reversed velocity
        # because: sprite.right (299) + sprite.change_x (10) > 300
        assert sprite.change_x < 0, (
            f"After step_all(), boundary check should have reversed velocity. "
            f"Sprite at right_edge={sprite_right_edge_before_update:.1f} with velocity={velocity_after_step_all} "
            f"would cross boundary at 300, but velocity not reversed. "
            f"Got {sprite.change_x}, expected negative. "
            f"Action current_velocity={bounce.current_velocity}"
        )
        assert bounce.current_velocity[0] < 0, (
            f"Action current_velocity should be negative after boundary check in step_all(), "
            f"got {bounce.current_velocity}"
        )

        # Now apply the reversed velocity
        sprite.update()
        # Sprite should move left now (velocity was reversed)
        assert sprite.change_x < 0, f"Sprite should be moving left after bounce, got {sprite.change_x}"

        # Step again - should continue in reversed direction
        Action.step_all(1 / 60)
        sprite.update()
        assert sprite.change_x < 0, f"After second step, sprite should still be moving left, got {sprite.change_x}"

    def test_bounce_continues_at_saved_velocity_without_boundary_check_on_step(self):
        """Test reproduces the bug: bounce continues at saved velocity without boundary check.

        This test reproduces the exact issue the user described:
        - Sprite is moving, then paused (F6)
        - When stepped (F7), sprite continues at saved velocity
        - Boundary checking doesn't happen during the step
        - Sprite crosses boundary without bouncing
        """
        sprite = create_test_sprite()
        sprite.center_x = 200
        sprite.center_y = 200

        # Create bounce pattern (like pattern_demo.py)
        bounds = (100, 100, 300, 300)
        bounce = create_bounce_pattern(velocity=(2, 1), bounds=bounds)
        bounce.apply(sprite)

        # Let sprite move normally for a bit (like in the demo)
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Now sprite is moving somewhere - pause it (like F6)
        # At this point, sprite has some velocity saved
        Action.pause_all()

        # Get the saved velocity - this is what will be restored on step
        saved_velocity_before_step = bounce._paused_velocity
        position_before_step = (sprite.center_x, sprite.center_y)
        velocity_before_step = (sprite.change_x, sprite.change_y)

        # Position sprite so it would cross boundary during step
        # Right boundary is at 300, sprite width 128, so right edge = center_x + 64
        # Set center_x so right edge is just before boundary
        sprite.center_x = 235  # Right edge = 299
        sprite.right = 299

        # Set velocity manually to ensure we're moving right toward boundary
        # The saved velocity might have been reversed already
        bounce._paused_velocity = (10, 0)  # Force saved velocity to be moving right
        bounce.current_velocity = (10, 0)
        sprite.change_x = 10

        # Step (like F7) - should restore velocity and check boundaries
        Action.step_all(1 / 60)

        # At this point:
        # - Velocity should be restored from saved_velocity (10, moving right)
        # - Boundary check should see: right_edge (299) + velocity (10) > boundary (300)
        # - Boundary check should reverse velocity BEFORE sprite.update()

        sprite_right_edge_before_update = sprite.right
        velocity_after_step_all = sprite.change_x
        current_velocity_after_step = bounce.current_velocity[0]

        # BUG REPRODUCTION: When sprite at right_edge=299 with velocity=10 would cross boundary at 300,
        # the boundary check should reverse velocity, but it's NOT happening during step cycles
        # This is the exact bug the user described
        would_cross = sprite_right_edge_before_update + velocity_after_step_all > 300

        if would_cross:
            # This assertion will FAIL if the bug exists (velocity not reversed)
            # It will PASS if the bug is fixed (velocity correctly reversed)
            assert sprite.change_x < 0, (
                f"BUG REPRODUCTION: After step_all(), sprite at right_edge={sprite_right_edge_before_update:.1f} "
                f"with velocity={velocity_after_step_all} would cross boundary at 300, "
                f"but velocity was NOT reversed during step_all(). "
                f"Got sprite.change_x={sprite.change_x} (expected negative), "
                f"Action current_velocity={bounce.current_velocity} (expected negative X). "
                f"This indicates boundary checking is not working during step cycles. "
                f"The sprite continues at its original saved velocity without responding to boundaries."
            )
            assert bounce.current_velocity[0] < 0, (
                f"Action current_velocity should be negative after boundary check in step_all(), "
                f"got {bounce.current_velocity}"
            )

        # Apply velocity and verify boundary check worked
        sprite.update()

        # If sprite crossed boundary, velocity should have been reversed
        if sprite.right > 300:
            assert sprite.change_x < 0, (
                f"Sprite crossed boundary but velocity not reversed. Got {sprite.change_x}, expected negative"
            )

    def test_patrol_responds_to_boundary_when_stepped_after_pause(self):
        """Test that patrol actions check boundaries during step after pause."""
        sprite = create_test_sprite()
        sprite.center_x = 200
        sprite.center_y = 100

        # Create patrol pattern moving RIGHT (like pattern_demo.py)
        bounds = (100, 0, 300, 600)
        velocity = (2.0, 0.0)  # Use same velocity as pattern_demo.py
        patrol = create_patrol_pattern(velocity, bounds)
        patrol.apply(sprite)

        # Let sprite move for a bit (like in demo)
        for _ in range(10):
            Action.update_all(1 / 60)
            sprite.update()

        # Pause (like F6)
        Action.pause_all()
        saved_velocity = patrol._paused_velocity

        # Position sprite just before right boundary
        # Right boundary is at 300, sprite width 128, so right edge = center_x + 64
        # Set center_x so right edge is just before boundary
        sprite.center_x = 235  # Right edge = 299
        sprite.right = 299

        # Step (like F7) - should restore velocity AND check boundaries
        Action.step_all(1 / 60)

        # Check if sprite would cross boundary
        sprite_right_edge = sprite.right  # Should be 299
        would_cross = sprite_right_edge + sprite.change_x > 300

        if would_cross:
            # Would cross boundary - velocity should be reversed
            assert sprite.change_x < 0, (
                f"Patrol sprite would cross right boundary (right_edge={sprite_right_edge:.1f}, "
                f"velocity={sprite.change_x}, boundary=300), but velocity not reversed. "
                f"Action current_velocity={patrol.current_velocity}"
            )
            assert patrol.current_velocity[0] < 0, (
                f"Action current_velocity should be negative after boundary check, got {patrol.current_velocity}"
            )

        # Apply the velocity
        sprite.update()

        # If we crossed boundary, verify velocity was reversed
        if sprite.right > 300:
            assert sprite.change_x < 0, (
                f"Patrol sprite crossed boundary but velocity not reversed. Got {sprite.change_x}, expected negative"
            )

    def test_step_keeps_sprites_paused_after_step_cycle(self):
        """Test that after stepping (F7), sprites advance one frame then stop.

        Correct behavior:
        - Pause with F6 - sprites stop
        - Step with F7 - advances ONE frame while paused
        - Game loop continues - sprites should NOT continue moving

        This test matches the real game loop sequence where on_update() calls
        Action.update_all() BEFORE sprite.update().
        """
        sprite = create_test_sprite()
        sprite.center_x = 200
        sprite.center_y = 200

        # Create bounce pattern (like pattern_demo.py)
        bounds = (100, 100, 300, 300)
        bounce = create_bounce_pattern(velocity=(2, 1), bounds=bounds)
        bounce.apply(sprite)

        # Move sprite normally for a bit
        for _ in range(5):
            Action.update_all(1 / 60)
            sprite.update()

        position_before_pause = (sprite.center_x, sprite.center_y)

        # Pause (F6) - should stop sprite
        Action.pause_all()
        assert bounce._paused, "Action should be paused after pause_all()"
        assert sprite.change_x == 0.0 and sprite.change_y == 0.0, (
            f"Velocities should be cleared after pause, got ({sprite.change_x}, {sprite.change_y})"
        )

        # Step (F7) - key handler calls step_all(), then returns
        Action.step_all(1 / 60)

        # After F7 handler returns, arcade's main loop calls on_update()
        # on_update() calls Action.update_all() THEN sprite.update()
        assert bounce._paused, "Action should still be paused after step_all()"

        # Simulate game loop: on_update() calls update_all() then sprite.update()
        Action.update_all(1 / 60)  # Preserves velocities for this frame
        sprite.update()  # Sprite moves using velocities from step
        position_after_step = (sprite.center_x, sprite.center_y)

        # Verify sprite moved one frame
        assert position_after_step != position_before_pause, (
            f"Sprite should have moved one frame during step. "
            f"Before: {position_before_pause}, After: {position_after_step}"
        )

        # Next frame: on_update() calls update_all() then sprite.update()
        Action.update_all(1 / 60)  # Should clear velocities now (step flag was consumed)
        sprite.update()  # Should not move because velocities are cleared
        position_after_second_update = (sprite.center_x, sprite.center_y)

        # After the step frame completes, sprites should stay paused
        assert position_after_second_update == position_after_step, (
            f"After step completes, sprite should stay paused. "
            f"Position changed from {position_after_step} to {position_after_second_update}. "
            f"Sprite velocities after update_all(): ({sprite.change_x}, {sprite.change_y}). "
            f"Action paused: {bounce._paused}."
        )

        # Velocities should be cleared after update_all() is called (actions are paused)
        assert sprite.change_x == 0.0 and sprite.change_y == 0.0, (
            f"After step completes and next update_all() is called, velocities should be cleared "
            f"since actions are paused. Got ({sprite.change_x}, {sprite.change_y}), expected (0, 0)."
        )
