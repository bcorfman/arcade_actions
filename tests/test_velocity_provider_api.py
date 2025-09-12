"""Tests for velocity_provider and boundary enter/exit functionality."""

import arcade
import pytest

from actions import Action, MoveUntil, infinite


@pytest.fixture
def sprite():
    """Create a test sprite."""
    sprite = arcade.Sprite(":resources:images/test_textures/test_texture.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestVelocityProvider:
    """Test velocity_provider functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_velocity_provider_basic(self, sprite):
        """Test basic velocity_provider functionality."""
        velocity_calls = []

        def velocity_provider():
            velocity_calls.append(True)
            return (5, 0)

        action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=velocity_provider,
        )
        action.apply(sprite, tag="test")

        Action.update_all(0.016)

        assert len(velocity_calls) == 2  # 1 from apply_effect + 1 from update_effect
        assert sprite.change_x == 5
        assert sprite.change_y == 0

    def test_velocity_provider_prevents_action_loops(self, sprite):
        """Test that velocity_provider prevents per-frame action creation loops."""
        call_count = 0

        def velocity_provider():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                return (10, 0)
            else:
                return (0, 0)

        action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=velocity_provider,
        )
        action.apply(sprite, tag="test")

        initial_action_count = len(Action._active_actions)

        for _ in range(10):
            Action.update_all(0.016)

        assert len(Action._active_actions) == initial_action_count
        assert call_count == 11  # 1 from apply_effect + 10 from update_effect

    def test_velocity_provider_left_boundary_logic(self, sprite):
        """Test player ship left boundary logic that prevents getting stuck."""
        SHIP_LEFT_BOUND = 50
        DRIFT_VELOCITY = -2
        MANUAL_VELOCITY = 8

        input_state = {"right": False}

        def velocity_provider():
            if input_state["right"]:
                return (MANUAL_VELOCITY, 0)

            if sprite.left <= SHIP_LEFT_BOUND:
                return (0, 0)
            return (DRIFT_VELOCITY, 0)

        sprite.left = SHIP_LEFT_BOUND + 10

        action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            bounds=(SHIP_LEFT_BOUND, 0, 200, 200),
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
        )
        action.apply(sprite, tag="test")

        # Test drift when away from boundary
        Action.update_all(0.016)
        assert sprite.change_x == DRIFT_VELOCITY

        # Test stop when at boundary
        sprite.left = SHIP_LEFT_BOUND
        Action.update_all(0.016)
        assert sprite.change_x == 0

        # Test manual control from boundary works
        input_state["right"] = True
        Action.update_all(0.016)
        assert sprite.change_x == MANUAL_VELOCITY


class TestBoundaryEnterExit:
    """Test boundary enter/exit events."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_boundary_enter_right(self, sprite):
        """Test boundary enter event for right boundary."""
        events = []

        def on_boundary_enter(sprite_obj, axis, side):
            events.append(("enter", axis, side))

        sprite.center_x = 195

        action = MoveUntil(
            velocity=(10, 0),
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="limit",
            on_boundary_enter=on_boundary_enter,
        )
        action.apply(sprite, tag="test")

        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        assert len(events) == 1
        assert events[0] == ("enter", "x", "right")

    def test_boundary_enter_exit_cycle(self, sprite):
        """Test complete enter/exit cycle for speed boost scenario."""
        events = []
        state = {"velocity": 10}

        def on_boundary_enter(sprite_obj, axis, side):
            events.append(("enter", axis, side))
            if side == "right":
                state["velocity"] = -10

        def on_boundary_exit(sprite_obj, axis, side):
            events.append(("exit", axis, side))

        def velocity_provider():
            return (state["velocity"], 0)

        sprite.center_x = 195

        action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            bounds=(0, 0, 200, 200),
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_boundary_enter,
            on_boundary_exit=on_boundary_exit,
        )
        action.apply(sprite, tag="test")

        # Hit boundary and reverse
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        # Move away from boundary
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        assert len(events) == 2
        assert events[0] == ("enter", "x", "right")
        assert events[1] == ("exit", "x", "right")
