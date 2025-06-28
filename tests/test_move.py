"""Test suite for move.py - Boundary movement actions."""

import arcade

from actions.base import Action
from actions.move import BoundedMove, WrappedMove


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 400
    sprite.center_y = 300
    sprite.width = 32
    sprite.height = 32
    return sprite


def create_test_sprite_list():
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    for i in range(3):
        sprite = create_test_sprite()
        sprite.center_x = 400 + i * 50
        sprite_list.append(sprite)
    return sprite_list


class MockMovementAction(Action):
    """Mock movement action for testing boundary wrappers."""

    def __init__(self, velocity: tuple[float, float], duration: float = 1.0):
        super().__init__()
        self.velocity = velocity
        self.duration = duration
        self.time_elapsed = 0.0

    def apply_effect(self):
        """Apply velocity to sprites."""

        def set_velocity(sprite):
            sprite.change_x, sprite.change_y = self.velocity

        self.for_each_sprite(set_velocity)

    def update_effect(self, delta_time: float):
        """Update movement duration."""
        self.time_elapsed += delta_time
        if self.time_elapsed >= self.duration:
            self.done = True

    def remove_effect(self):
        """Stop movement by clearing velocity."""

        def clear_velocity(sprite):
            sprite.change_x = 0
            sprite.change_y = 0

        self.for_each_sprite(clear_velocity)

    def clone(self):
        return MockMovementAction(self.velocity, self.duration)


class TestWrappedMove:
    """Test suite for WrappedMove action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_wrapped_move_initialization(self):
        """Test WrappedMove initialization."""
        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((100, 0))

        wrap_action = WrappedMove(get_bounds, movement_action)

        assert wrap_action.get_bounds == get_bounds
        assert wrap_action.movement_action == movement_action
        assert wrap_action.wrap_horizontal
        assert wrap_action.wrap_vertical
        assert wrap_action.on_wrap is None

    def test_wrapped_move_with_options(self):
        """Test WrappedMove with custom options."""
        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((100, 0))

        def on_wrap(sprite, axis):
            pass

        wrap_action = WrappedMove(
            get_bounds, movement_action, wrap_horizontal=False, wrap_vertical=True, on_wrap=on_wrap
        )

        assert not wrap_action.wrap_horizontal
        assert wrap_action.wrap_vertical
        assert wrap_action.on_wrap == on_wrap

    def test_wrapped_move_right_edge(self):
        """Test wrapping when sprite moves off right edge."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((200, 0), 0.1)  # Move right quickly
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Should have wrapped to left side
        assert sprite.center_x < 0

    def test_wrapped_move_left_edge(self):
        """Test wrapping when sprite moves off left edge."""
        sprite = create_test_sprite()
        sprite.center_x = 50  # Near left edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((-200, 0), 0.1)  # Move left quickly
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Should have wrapped to right side
        assert sprite.center_x > 800

    def test_wrapped_move_top_edge(self):
        """Test wrapping when sprite moves off top edge."""
        sprite = create_test_sprite()
        sprite.center_y = 550  # Near top edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((0, 200), 0.1)  # Move up quickly
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Should have wrapped to bottom
        assert sprite.center_y < 0

    def test_wrapped_move_bottom_edge(self):
        """Test wrapping when sprite moves off bottom edge."""
        sprite = create_test_sprite()
        sprite.center_y = 50  # Near bottom edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((0, -200), 0.1)  # Move down quickly
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Should have wrapped to top
        assert sprite.center_y > 600

    def test_wrapped_move_callback(self):
        """Test wrap callback is triggered."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        wrap_events = []

        def on_wrap(sprite_ref, axis):
            wrap_events.append((sprite_ref, axis))

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((200, 0), 0.1)  # Move right quickly
        wrap_action = WrappedMove(get_bounds, movement_action, on_wrap=on_wrap)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Callback should have been triggered
        assert len(wrap_events) >= 1
        assert wrap_events[0][0] == sprite
        assert wrap_events[0][1] == "x"

    def test_wrapped_move_disable_horizontal(self):
        """Test disabling horizontal wrapping."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((200, 0), 0.1)  # Move right quickly
        wrap_action = WrappedMove(get_bounds, movement_action, wrap_horizontal=False)

        wrap_action.apply(sprite)

        # Update movement and wrapping
        Action.update_all(0.016)
        sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # Should not have wrapped horizontally
        assert sprite.center_x > 800  # Moved off edge without wrapping

    def test_wrapped_move_sprite_list(self):
        """Test WrappedMove with multiple sprites."""
        sprite_list = create_test_sprite_list()
        for sprite in sprite_list:
            sprite.center_x = 750  # All near right edge

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((200, 0), 0.1)  # Move right quickly
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite_list)

        # Update movement and wrapping
        Action.update_all(0.016)
        for sprite in sprite_list:
            sprite.update()  # Apply velocity
        wrap_action.update(0.016)

        # All sprites should have wrapped
        for sprite in sprite_list:
            assert sprite.center_x < 0

    def test_wrapped_move_action_completion(self):
        """Test that WrappedMove completes when movement action completes."""
        sprite = create_test_sprite()

        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((100, 0), 0.05)  # Short duration
        wrap_action = WrappedMove(get_bounds, movement_action)

        wrap_action.apply(sprite)

        # Update until movement completes
        for _ in range(10):
            Action.update_all(0.016)
            sprite.update()
            if wrap_action.done:
                break

        assert wrap_action.done
        assert movement_action.done


class TestBoundedMove:
    """Test suite for BoundedMove action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_bounded_move_initialization(self):
        """Test BoundedMove initialization."""
        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((100, 0))

        bounce_action = BoundedMove(get_bounds, movement_action)

        assert bounce_action.get_bounds == get_bounds
        assert bounce_action.movement_action == movement_action
        assert bounce_action.bounce_horizontal
        assert bounce_action.bounce_vertical
        assert bounce_action.on_bounce is None

    def test_bounded_move_with_options(self):
        """Test BoundedMove with custom options."""
        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((100, 0))

        def on_bounce(sprite, axis):
            pass

        bounce_action = BoundedMove(
            get_bounds, movement_action, bounce_horizontal=False, bounce_vertical=True, on_bounce=on_bounce
        )

        assert not bounce_action.bounce_horizontal
        assert bounce_action.bounce_vertical
        assert bounce_action.on_bounce == on_bounce

    def test_bounded_move_right_edge(self):
        """Test bouncing when sprite hits right edge."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((200, 0), 1.0)  # Move right quickly
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # Should have bounced back inside bounds
        assert sprite.center_x <= 800

    def test_bounded_move_left_edge(self):
        """Test bouncing when sprite hits left edge."""
        sprite = create_test_sprite()
        sprite.center_x = 50  # Near left edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((-200, 0), 1.0)  # Move left quickly
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # Should have bounced back inside bounds
        assert sprite.center_x >= 0

    def test_bounded_move_top_edge(self):
        """Test bouncing when sprite hits top edge."""
        sprite = create_test_sprite()
        sprite.center_y = 550  # Near top edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((0, 200), 1.0)  # Move up quickly
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # Should have bounced back inside bounds
        assert sprite.center_y <= 600

    def test_bounded_move_bottom_edge(self):
        """Test bouncing when sprite hits bottom edge."""
        sprite = create_test_sprite()
        sprite.center_y = 50  # Near bottom edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((0, -200), 1.0)  # Move down quickly
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # Should have bounced back inside bounds
        assert sprite.center_y >= 0

    def test_bounded_move_callback(self):
        """Test bounce callback is triggered."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        bounce_events = []

        def on_bounce(sprite_ref, axis):
            bounce_events.append((sprite_ref, axis))

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((200, 0), 1.0)  # Move right quickly
        bounce_action = BoundedMove(get_bounds, movement_action, on_bounce=on_bounce)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(10):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)
            if bounce_events:
                break

        # Callback should have been triggered
        assert len(bounce_events) >= 1
        assert bounce_events[0][0] == sprite
        assert bounce_events[0][1] == "x"

    def test_bounded_move_disable_horizontal(self):
        """Test disabling horizontal bouncing."""
        sprite = create_test_sprite()
        sprite.center_x = 750  # Near right edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((200, 0), 1.0)  # Move right quickly
        bounce_action = BoundedMove(get_bounds, movement_action, bounce_horizontal=False)

        bounce_action.apply(sprite)

        # Update movement and bouncing multiple times
        for _ in range(5):
            Action.update_all(0.016)
            sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # Should not have bounced horizontally
        assert sprite.center_x > 800  # Moved off edge without bouncing

    def test_bounded_move_sprite_list(self):
        """Test BoundedMove with multiple sprites."""
        sprite_list = create_test_sprite_list()
        for sprite in sprite_list:
            sprite.center_x = 750  # All near right edge

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((200, 0), 1.0)  # Move right quickly
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite_list)

        # Update movement and bouncing multiple times
        for _ in range(10):
            Action.update_all(0.016)
            for sprite in sprite_list:
                sprite.update()  # Apply velocity
            bounce_action.update(0.016)

        # All sprites should be within bounds
        for sprite in sprite_list:
            assert sprite.center_x <= 800

    def test_bounded_move_action_completion(self):
        """Test that BoundedMove completes when movement action completes."""
        sprite = create_test_sprite()

        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((100, 0), 0.05)  # Short duration
        bounce_action = BoundedMove(get_bounds, movement_action)

        bounce_action.apply(sprite)

        # Update until movement completes
        for _ in range(10):
            Action.update_all(0.016)
            sprite.update()
            if bounce_action.done:
                break

        assert bounce_action.done
        assert movement_action.done

    def test_bounded_move_clone(self):
        """Test BoundedMove cloning."""
        get_bounds = lambda: (0, 0, 800, 600)
        movement_action = MockMovementAction((100, 0))

        def on_bounce(sprite, axis):
            pass

        bounce_action = BoundedMove(get_bounds, movement_action, bounce_horizontal=False, on_bounce=on_bounce)

        cloned = bounce_action.clone()

        assert cloned is not bounce_action
        assert cloned.get_bounds == get_bounds
        assert cloned.movement_action is not movement_action
        assert cloned.bounce_horizontal == False
        assert cloned.on_bounce == on_bounce


class TestBoundaryActionsIntegration:
    """Test suite for boundary actions integration."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_wrapped_move_clone(self):
        """Test WrappedMove cloning."""
        get_bounds = lambda: (800, 600)
        movement_action = MockMovementAction((100, 0))

        def on_wrap(sprite, axis):
            pass

        wrap_action = WrappedMove(get_bounds, movement_action, wrap_horizontal=False, on_wrap=on_wrap)

        cloned = wrap_action.clone()

        assert cloned is not wrap_action
        assert cloned.get_bounds == get_bounds
        assert cloned.movement_action is not movement_action
        assert cloned.wrap_horizontal == False
        assert cloned.on_wrap == on_wrap
