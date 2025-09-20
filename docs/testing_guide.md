"""Testing Guide for arcade_actions

This guide covers testing patterns and best practices for the arcade_actions library.
"""

# Testing Guide

## Test Structure and Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

```python
import pytest
from actions import Action

class ActionTestBase:
    """Base class for action tests with common setup and teardown."""
    
    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

@pytest.fixture
def test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite

@pytest.fixture
def test_sprite_list() -> arcade.SpriteList:
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    sprite1 = arcade.Sprite(":resources:images/items/star.png")
    sprite2 = arcade.Sprite(":resources:images/items/star.png")
    sprite_list.append(sprite1)
    sprite_list.append(sprite2)
    return sprite_list
```

## Basic Action Testing

Test basic action functionality using the global action update system:

```python
from actions import Action, move_until, rotate_until, duration, infinite

class TestMoveUntil(ActionTestBase):
    """Test suite for MoveUntil action."""

    def test_move_until_basic(self, test_sprite):
        """Test basic MoveUntil functionality."""
        sprite = test_sprite
        start_x = sprite.center_x

        condition_met = False

        def condition():
            nonlocal condition_met
            return condition_met

        action = move_until(sprite, velocity=(100, 0), condition=condition, tag="test_basic")

        # Update for one frame - sprite should have velocity applied
        Action.update_all(0.016)
        assert sprite.change_x == 100
        assert sprite.change_y == 0

        # Let it move for a bit
        for _ in range(10):
            sprite.update()  # Apply velocity to position
            Action.update_all(0.016)

        assert sprite.center_x > start_x

        # Trigger condition
        condition_met = True
        Action.update_all(0.016)

        # Velocity should be zeroed
        assert sprite.change_x == 0
        assert sprite.change_y == 0
        assert action.done

    def test_rotate_until_basic(self, test_sprite):
        """Test basic RotateUntil functionality."""
        sprite = test_sprite

        target_reached = False

        def condition():
            return target_reached

        action = rotate_until(sprite, angular_velocity=90, condition=condition, tag="test_basic")

        Action.update_all(0.016)

        # RotateUntil uses degrees per frame at 60 FPS semantics
        assert sprite.change_angle == 90

        # Trigger condition
        target_reached = True
        Action.update_all(0.016)

        assert action.done
```

## Testing Easing Actions

Test easing functionality that provides smooth acceleration/deceleration for continuous actions:

```python
from actions import Action, MoveUntil, Ease, infinite
from arcade import easing

class TestEase(ActionTestBase):
    """Test suite for Ease wrapper."""

    def test_ease_continuous_movement(self, test_sprite):
        """Test Ease wrapper with continuous movement action."""
        sprite = test_sprite
        
        # Create continuous movement action (never stops on its own)
        continuous_move = MoveUntil((100, 0), infinite)
        easing_wrapper = Ease(continuous_move, duration=2.0, ease_function=easing.ease_in_out)
        
        easing_wrapper.apply(sprite, tag="test_ease")
        
        # Test initial state (should start with reduced velocity)
        Action.update_all(0.016)
        assert 0 < sprite.change_x < 100  # Eased start
        
        # Test mid-easing (should reach full velocity)
        easing_wrapper._elapsed = 1.0  # Halfway through easing
        Action.update_all(0.016)
        assert sprite.change_x == 100  # Full velocity at midpoint
        
        # Test easing completion (action continues at full velocity)
        easing_wrapper._elapsed = 2.0  # Easing complete
        Action.update_all(0.016)
        assert sprite.change_x == 100  # Continues at full velocity
        assert easing_wrapper._easing_complete

    def test_ease_factor_scaling(self, test_sprite):
        """Test that Ease properly scales wrapped action velocity."""
        sprite = test_sprite
        move = MoveUntil((100, 0), infinite)
        ease_action = Ease(move, duration=1.0)
        
        ease_action.apply(sprite, tag="test")
        
        # Test various easing factors
        ease_action.set_factor(0.5)  # Half speed
        Action.update_all(0.016)
        assert sprite.change_x == 50
        
        ease_action.set_factor(1.0)  # Full speed
        Action.update_all(0.016)
        assert sprite.change_x == 100
```

## Testing Action Composition

Test sequences and parallel actions using the current API:

```python
from actions import Action, sequence, parallel, DelayUntil, MoveUntil, RotateUntil, duration

class TestSequenceFunction:
    """Test suite for sequence() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_execution_order(self, test_sprite):
        """Test that sequence executes actions in order."""
        sprite = test_sprite
        
        action1 = DelayUntil(duration(0.1))
        action2 = MoveUntil((100, 0), duration(0.1))
        seq = sequence(action1, action2)
        
        seq.apply(sprite, tag="test_sequence")
        
        # First action should be active
        assert seq.current_index == 0
        assert seq.current_action == action1
        
        # After first action completes, second should start
        Action.update_all(0.11)  # Complete first action
        Action.update_all(0.016) # Start second action
        
        assert seq.current_index == 1
        assert seq.current_action == action2
        assert sprite.change_x == 100

class TestParallelFunction:
    """Test suite for parallel() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_simultaneous_execution(self, test_sprite):
        """Test that parallel actions execute simultaneously."""
        sprite = test_sprite
        
        move_action = MoveUntil((50, 0), duration(1.0))
        rotate_action = RotateUntil(180, duration(1.0))
        par = parallel(move_action, rotate_action)
        
        par.apply(sprite, tag="test_parallel")
        Action.update_all(0.016)
        
        # Both actions should be active simultaneously
        assert sprite.change_x == 50
        assert sprite.change_angle == 180
        assert len(par.sub_actions) == 2
        assert all(action._is_active for action in par.sub_actions)
```

## Testing Boundary Interactions

Test boundary detection and callbacks using the current edge-triggered API:

```python
from actions import Action, MoveUntil, infinite

class TestBoundaryCallbacks:
    """Test boundary enter/exit callbacks."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_boundary_enter_callback(self, test_sprite):
        """Test boundary enter event for right boundary."""
        sprite = test_sprite
        sprite.center_x = 195  # Near right boundary
        events = []

        def on_boundary_enter(sprite_obj, axis, side):
            events.append(("enter", axis, side))

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

        assert len(events) == 1
        assert events[0] == ("enter", "x", "right")

    def test_boundary_enter_exit_cycle(self, test_sprite):
        """Test complete enter/exit cycle."""
        sprite = test_sprite
        sprite.center_x = 195
        events = []
        state = {"velocity": 10}

        def on_boundary_enter(sprite_obj, axis, side):
            events.append(("enter", axis, side))
            if side == "right":
                state["velocity"] = -10  # Reverse direction

        def on_boundary_exit(sprite_obj, axis, side):
            events.append(("exit", axis, side))

        def velocity_provider():
            return (state["velocity"], 0)

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

        # Move away from boundary
        Action.update_all(0.016)
        sprite.update()

        assert len(events) == 2
        assert events[0] == ("enter", "x", "right")
        assert events[1] == ("exit", "x", "right")
```

## Testing Velocity Providers

Test dynamic velocity provision for complex movement patterns:

```python
from actions import Action, MoveUntil, infinite

class TestVelocityProvider:
    """Test velocity_provider functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_velocity_provider_basic(self, test_sprite):
        """Test basic velocity_provider functionality."""
        sprite = test_sprite
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

        assert len(velocity_calls) == 2  # Called in apply_effect and update_effect
        assert sprite.change_x == 5
        assert sprite.change_y == 0

    def test_velocity_provider_prevents_action_loops(self, test_sprite):
        """Test that velocity_provider prevents per-frame action creation loops."""
        sprite = test_sprite
        call_count = 0

        def velocity_provider():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                return (10, 0)
            else:
                return (0, 0)  # Stop after a few frames

        action = MoveUntil(
            velocity=(0, 0),
            condition=infinite,
            velocity_provider=velocity_provider,
        )
        action.apply(sprite, tag="test")

        initial_action_count = len(Action._active_actions)

        # Run multiple frames
        for _ in range(10):
            Action.update_all(0.016)

        # Should not create additional actions
        assert len(Action._active_actions) == initial_action_count
        assert call_count == 11  # 1 from apply + 10 from updates
```

## Testing BlinkUntil with Visibility Callbacks

Test BlinkUntil callback functionality for collision management and game state synchronization:

```python
from actions import Action, blink_until, infinite, duration

class TestBlinkUntilCallbacks:
    """Test BlinkUntil visibility callback functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_blink_visibility_callbacks_basic(self, test_sprite):
        """Test basic on_blink_enter and on_blink_exit callback functionality."""
        sprite = test_sprite
        sprite.visible = True  # Start visible
        
        enter_calls = []
        exit_calls = []
        
        def on_enter(sprite_arg):
            enter_calls.append(sprite_arg)
            
        def on_exit(sprite_arg):
            exit_calls.append(sprite_arg)

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=on_enter,
            on_blink_exit=on_exit,
            tag="test_callbacks"
        )

        # Initial state - sprite visible, no callbacks yet
        assert sprite.visible
        assert len(enter_calls) == 0
        assert len(exit_calls) == 0

        # First blink (to invisible) - exit callback
        Action.update_all(0.06)  # More than 0.05 seconds
        assert not sprite.visible
        assert len(exit_calls) == 1
        assert exit_calls[0] == sprite
        assert len(enter_calls) == 0

        # Second blink (back to visible) - enter callback
        Action.update_all(0.06)
        assert sprite.visible
        assert len(enter_calls) == 1
        assert enter_calls[0] == sprite
        assert len(exit_calls) == 1

    def test_blink_edge_triggered_callbacks(self, test_sprite):
        """Test that callbacks are edge-triggered (only fire on state changes)."""
        sprite = test_sprite
        sprite.visible = True
        
        callback_count = {"enter": 0, "exit": 0}
        
        def count_enter(sprite_arg):
            callback_count["enter"] += 1
            
        def count_exit(sprite_arg):
            callback_count["exit"] += 1

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=count_enter,
            on_blink_exit=count_exit,
            tag="test_edge_triggered"
        )

        # Multiple updates within same blink period - no callbacks
        for _ in range(3):
            Action.update_all(0.01)  # Less than 0.05 threshold
        
        assert callback_count["enter"] == 0
        assert callback_count["exit"] == 0
        assert sprite.visible  # Still visible

        # Cross threshold to invisible - one exit callback
        Action.update_all(0.03)  # Total now > 0.05
        assert callback_count["exit"] == 1
        assert callback_count["enter"] == 0
        assert not sprite.visible

        # Multiple updates while invisible - no additional callbacks
        for _ in range(3):
            Action.update_all(0.01)
        assert callback_count["exit"] == 1  # Still just one
        assert callback_count["enter"] == 0

    def test_blink_callback_exception_safety(self, test_sprite):
        """Test that callback exceptions don't break blinking system."""
        sprite = test_sprite
        sprite.visible = True
        
        def failing_enter(sprite_arg):
            raise RuntimeError("Enter callback failed!")
            
        def failing_exit(sprite_arg):
            raise RuntimeError("Exit callback failed!")

        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=failing_enter,
            on_blink_exit=failing_exit,
            tag="test_exception_handling"
        )

        # Should not crash despite callback exceptions
        Action.update_all(0.06)  # Trigger exit callback exception
        assert not sprite.visible
        
        Action.update_all(0.06)  # Trigger enter callback exception  
        assert sprite.visible
        
        # Blinking should continue working normally
        Action.update_all(0.06)
        assert not sprite.visible

    def test_blink_sprite_list_callbacks(self, test_sprite_list):
        """Test BlinkUntil callbacks work with sprite lists."""
        sprite_list = test_sprite_list
        for sprite in sprite_list:
            sprite.visible = True
            
        callback_sprites = {"enter": [], "exit": []}
        
        def track_enter(sprite_arg):
            callback_sprites["enter"].append(sprite_arg)
            
        def track_exit(sprite_arg):
            callback_sprites["exit"].append(sprite_arg)

        action = blink_until(
            sprite_list,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=track_enter,
            on_blink_exit=track_exit,
            tag="test_sprite_list_callbacks"
        )

        # First blink (all go invisible) - exit callbacks for each sprite
        Action.update_all(0.06)
        for sprite in sprite_list:
            assert not sprite.visible
            assert sprite in callback_sprites["exit"]
        assert len(callback_sprites["exit"]) == len(sprite_list)
        assert len(callback_sprites["enter"]) == 0

        # Second blink (all go visible) - enter callbacks for each sprite
        Action.update_all(0.06)
        for sprite in sprite_list:
            assert sprite.visible
            assert sprite in callback_sprites["enter"]
        assert len(callback_sprites["enter"]) == len(sprite_list)

    def test_blink_collision_management_pattern(self, test_sprite):
        """Test real-world collision management pattern with BlinkUntil."""
        sprite = test_sprite
        sprite.visible = True
        
        # Simulate collision sprite list
        collision_sprites = []
        
        def enable_collisions(sprite_obj):
            """Add sprite to collision detection when visible."""
            if sprite_obj not in collision_sprites:
                collision_sprites.append(sprite_obj)
                sprite_obj.can_collide = True
                
        def disable_collisions(sprite_obj):
            """Remove sprite from collision detection when invisible."""
            if sprite_obj in collision_sprites:
                collision_sprites.remove(sprite_obj)
                sprite_obj.can_collide = False

        action = blink_until(
            sprite,
            seconds_until_change=0.1,
            condition=duration(1.0),
            on_blink_enter=enable_collisions,
            on_blink_exit=disable_collisions,
            tag="invulnerability_blink"
        )

        # Initially visible - should be in collision detection
        assert sprite.visible
        assert sprite in collision_sprites
        assert sprite.can_collide

        # Blink to invisible - should be removed from collision detection
        Action.update_all(0.11)
        assert not sprite.visible
        assert sprite not in collision_sprites
        assert not sprite.can_collide

        # Blink back to visible - should be re-added to collision detection
        Action.update_all(0.11)
        assert sprite.visible
        assert sprite in collision_sprites
        assert sprite.can_collide

    def test_blink_partial_callbacks(self, test_sprite):
        """Test BlinkUntil with only one callback (enter or exit)."""
        sprite = test_sprite
        sprite.visible = True
        
        enter_calls = []
        
        def on_enter(sprite_arg):
            enter_calls.append(sprite_arg)

        # Test with only enter callback
        action = blink_until(
            sprite,
            seconds_until_change=0.05,
            condition=infinite,
            on_blink_enter=on_enter,  # Only enter callback
            tag="test_only_enter"
        )

        # Go invisible (no callback)
        Action.update_all(0.06)
        assert not sprite.visible
        assert len(enter_calls) == 0
        
        # Go visible (enter callback)
        Action.update_all(0.06)
        assert sprite.visible
        assert len(enter_calls) == 1
```

## Testing Formation Functions

Test formation functions for proper sprite positioning:

```python
from actions import arrange_triangle, arrange_hexagonal_grid, arrange_arc, arrange_concentric_rings, arrange_cross, arrange_arrow

def test_formation_positioning():
    # Test triangle formation
    triangle = arrange_triangle(count=6, apex_x=400, apex_y=500, row_spacing=50, lateral_spacing=60)
    assert len(triangle) == 6
    assert triangle[0].center_x == 400  # Apex
    assert triangle[0].center_y == 500
    
    # Test hexagonal grid
    hex_grid = arrange_hexagonal_grid(rows=2, cols=3, start_x=100, start_y=200, spacing=50)
    assert len(hex_grid) == 6
    assert hex_grid[0].center_x == 100  # First sprite
    
    # Test arc formation
    arc = arrange_arc(count=5, center_x=400, center_y=300, radius=100, start_angle=0, end_angle=180)
    assert len(arc) == 5
    # Verify sprites are at correct distance from center
    for sprite in arc:
        distance = math.hypot(sprite.center_x - 400, sprite.center_y - 300)
        assert abs(distance - 100) < 0.1
    
    # Test concentric rings
    rings = arrange_concentric_rings(radii=[50, 100], sprites_per_ring=[4, 8], center_x=300, center_y=300)
    assert len(rings) == 12  # 4 + 8
    
    # Test cross formation
    cross = arrange_cross(count=9, center_x=400, center_y=300, arm_length=80, spacing=40)
    assert len(cross) == 9
    assert cross[0].center_x == 400  # Center sprite
    assert cross[0].center_y == 300
    
    # Test arrow formation
    arrow = arrange_arrow(count=7, tip_x=400, tip_y=500, rows=3, spacing_along=50, spacing_outward=40)
    assert len(arrow) == 7
    assert arrow[0].center_x == 400  # Tip sprite
    assert arrow[0].center_y == 500

    # Zero-allocation: arrange existing sprites
    sprites = [arcade.Sprite(":resources:images/items/star.png") for _ in range(9)]
    v_formation = arrange_v_formation(sprites, apex_x=400, apex_y=300, spacing=50)
    assert len(v_formation) == 9

    # Grid rule: len(sprites) must equal rows * cols
    sprites = [arcade.Sprite(":resources:images/items/star.png") for _ in range(6)]
    grid = arrange_grid(sprites, rows=2, cols=3, start_x=100, start_y=100)
    assert len(grid) == 6

def test_formation_visibility():
    # Test that formations respect visibility parameter
    invisible_triangle = arrange_triangle(count=6, apex_x=100, apex_y=100, visible=False)
    for sprite in invisible_triangle:
        assert not sprite.visible
    
    visible_triangle = arrange_triangle(count=6, apex_x=100, apex_y=100, visible=True)
    for sprite in visible_triangle:
        assert sprite.visible

def test_formation_parameter_validation():
    # Test parameter validation
    with pytest.raises(ValueError):
        arrange_triangle(count=-1, apex_x=100, apex_y=100)
    
    with pytest.raises(ValueError):
        arrange_arc(count=5, center_x=100, center_y=100, radius=50, start_angle=180, end_angle=90)
    
    with pytest.raises(ValueError):
        arrange_concentric_rings(radii=[50, 100], sprites_per_ring=[4])  # Mismatched lengths
```

## Testing Best Practices

1. **Use ActionTestBase and pytest fixtures:**
```python
from tests.conftest import ActionTestBase

class TestYourAction(ActionTestBase):
    """Test suite for your action."""
    
    def test_your_action(self, test_sprite):
        sprite = test_sprite  # Use provided fixture
        # Your test logic here
```

2. **Test action lifecycle with global update system:**
```python
def test_action_lifecycle(self, test_sprite):
    sprite = test_sprite
    action = move_until(sprite, velocity=(5, 0), condition=duration(1.0), tag="test")
    
    # Test initial state
    assert not action.done
    assert sprite.change_x == 0
    
    # Test after global update
    Action.update_all(0.016)
    assert sprite.change_x == 5
    assert action._is_active
    
    # Test completion
    action.stop()
    assert action.done
    assert sprite.change_x == 0  # Cleaned up
```

3. **Test edge cases and error handling:**
```python
def test_invalid_parameters(self, test_sprite):
    sprite = test_sprite
    
    # Test invalid velocity tuple
    with pytest.raises(ValueError):
        MoveUntil(velocity=(1,), condition=infinite)  # Wrong length
    
    # Test invalid duration
    with pytest.raises(ValueError):
        Ease(MoveUntil((5, 0), infinite), duration=-1.0)
```

4. **Test callbacks and conditions:**
```python
def test_action_completion_callback(self, test_sprite):
    sprite = test_sprite
    callback_called = False
    callback_data = None
    
    def on_stop(data=None):
        nonlocal callback_called, callback_data
        callback_called = True
        callback_data = data
    
    def condition():
        return {"result": "success"}
    
    action = MoveUntil((5, 0), condition, on_stop=on_stop)
    action.apply(sprite, tag="test")
    
    Action.update_all(0.016)
    
    assert callback_called
    assert callback_data == {"result": "success"}
```

5. **Test action factor scaling:**
```python
def test_action_factor_scaling(self, test_sprite):
    sprite = test_sprite
    action = MoveUntil((100, 0), infinite)
    action.apply(sprite, tag="test")
    
    # Test normal speed
    Action.update_all(0.016)
    assert sprite.change_x == 100
    
    # Test scaled speed
    action.set_factor(0.5)
    assert sprite.change_x == 50
    
    action.set_factor(2.0)
    assert sprite.change_x == 200
```

## Common Testing Patterns

1. **Testing velocity changes with current velocity system:**
```python
def test_velocity_changes(self, test_sprite):
    sprite = test_sprite
    
    # Test positive velocity
    action = MoveUntil((5, 0), infinite)
    action.apply(sprite, tag="test")
    Action.update_all(0.016)
    assert sprite.change_x == 5
    
    # Test velocity update
    action.set_current_velocity((-10, 0))
    assert sprite.change_x == -10
```

2. **Testing custom conditions:**
```python
def test_custom_condition(self, test_sprite):
    sprite = test_sprite
    target_x = 200
    
    def reach_target():
        return sprite.center_x >= target_x
    
    action = MoveUntil((5, 0), reach_target)
    action.apply(sprite, tag="test")
    
    # Run until condition met
    for _ in range(50):  # Prevent infinite loop
        Action.update_all(0.016)
        sprite.update()  # Apply velocity to position
        if action.done:
            break
    
    assert sprite.center_x >= target_x
    assert action.done
```

3. **Testing global action management:**
```python
def test_action_tags(self, test_sprite):
    sprite = test_sprite
    
    # Apply multiple actions with tags
    move_action = MoveUntil((5, 0), infinite)
    rotate_action = RotateUntil(180, infinite)
    
    move_action.apply(sprite, tag="movement")
    rotate_action.apply(sprite, tag="rotation")
    
    Action.update_all(0.016)
    assert sprite.change_x == 5
    assert sprite.change_angle == 180
    
    # Stop specific action by tag
    Action.stop_actions_for_target(sprite, tag="movement")
    Action.update_all(0.016)
    assert sprite.change_x == 0  # Movement stopped
    assert sprite.change_angle == 180  # Rotation continues
```

4. **Testing sprite lists:**
```python
def test_sprite_list_actions(self, test_sprite_list):
    sprite_list = test_sprite_list
    action = MoveUntil((5, 0), infinite)
    action.apply(sprite_list, tag="group_move")
    
    Action.update_all(0.016)
    
    # Test all sprites move together
    for sprite in sprite_list:
        assert sprite.change_x == 5
        assert sprite.change_y == 0
```

5. **Testing action cleanup:**
```python
def test_action_cleanup(self, test_sprite):
    sprite = test_sprite
    action = MoveUntil((5, 0), duration(0.1))
    action.apply(sprite, tag="test")
    
    initial_count = len(Action._active_actions)
    
    # Run until completion
    Action.update_all(0.11)  # Exceed duration
    
    # Action should be automatically removed
    assert len(Action._active_actions) < initial_count
    assert action.done
    assert sprite.change_x == 0  # Velocity cleared
``` 