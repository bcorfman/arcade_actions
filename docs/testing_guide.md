"""Testing Guide for arcade_actions

This guide covers testing patterns and best practices for the arcade_actions library.
"""

# Testing Guide

## Basic Action Testing

Test basic action functionality using the provided test fixtures:

```python
from arcade_actions import move_until, rotate_until, duration
from .fixtures import create_sprite

def test_basic_movement():
    sprite = create_sprite()
    
    # Test movement
    action = move_until(
        sprite,
        velocity=(5, 0),
        condition=duration(1.0),
        tag="test_move"
    )
    
    # Verify initial state
    assert sprite.change_x == 0
    assert sprite.change_y == 0
    
    # Update and verify movement
    action.update()
    assert sprite.change_x == 5
    assert sprite.change_y == 0
    
    # Stop and verify cleanup
    action.stop()
    assert sprite.change_x == 0
    assert sprite.change_y == 0

def test_basic_rotation():
    sprite = create_sprite()
    
    # Test rotation
    action = rotate_until(
        sprite,
        velocity=180,
        condition=duration(1.0),
        tag="test_rotate"
    )
    
    # Verify initial state
    assert sprite.change_angle == 0
    
    # Update and verify rotation
    action.update()
    assert sprite.change_angle == 180
    
    # Stop and verify cleanup
    action.stop()
    assert sprite.change_angle == 0
```

## Testing Easing Actions

Test easing functionality with different ease functions:

```python
from arcade_actions import ease, move_until, easing

def test_easing():
    sprite = create_sprite()
    
    # Create movement action
    move_action = move_until(
        sprite,
        velocity=(100, 0),
        condition=duration(2.0)
    )
    
    # Apply easing
    ease_action = ease(
        sprite,
        move_action,
        duration=2.0,
        ease_function=easing.ease_in_out,
        tag="ease_move"
    )
    
    # Test initial state
    assert sprite.change_x == 0
    
    # Test acceleration phase
    ease_action.update()
    assert 0 < sprite.change_x < 100
    
    # Test deceleration phase
    ease_action._elapsed = 1.5  # Simulate time passing
    ease_action.update()
    assert 0 < sprite.change_x < 100
    
    # Test completion
    ease_action._elapsed = 2.0
    ease_action.update()
    assert sprite.change_x == 0
```

## Testing Action Composition

Test sequences and parallel actions:

```python
from arcade_actions import sequence, parallel, move_until, rotate_until

def test_sequence():
    sprite = create_sprite()
    
    # Create sequence
    actions = sequence(
        move_until(sprite, velocity=(5, 0), condition=duration(1.0)),
        rotate_until(sprite, velocity=180, condition=duration(1.0))
    )
    
    # Test first action
    actions.update()
    assert sprite.change_x == 5
    assert sprite.change_angle == 0
    
    # Test second action
    actions._elapsed = 1.0  # Complete first action
    actions.update()
    assert sprite.change_x == 0
    assert sprite.change_angle == 180

def test_parallel():
    sprite = create_sprite()
    
    # Create parallel actions
    actions = parallel(
        move_until(sprite, velocity=(5, 0), condition=duration(1.0)),
        rotate_until(sprite, velocity=180, condition=duration(1.0))
    )
    
    # Test simultaneous execution
    actions.update()
    assert sprite.change_x == 5
    assert sprite.change_angle == 180
```

## Testing Complex Patterns

Test more complex action patterns:

```python
from arcade_actions import sequence, parallel, ease, move_until, rotate_until

def test_attack_pattern():
    sprite = create_sprite()
    
    # Create complex pattern
    pattern = sequence(
        # Move to position
        move_until(sprite, velocity=(5, 0), condition=duration(1.0)),
        
        # Attack sequence
        parallel(
            rotate_until(sprite, velocity=360, condition=duration(1.0)),
            move_until(sprite, velocity=(0, 5), condition=duration(1.0))
        ),
        
        # Retreat
        move_until(sprite, velocity=(-5, -5), condition=duration(1.0))
    )
    
    # Apply easing
    ease_action = ease(
        sprite,
        pattern,
        duration=2.0,
        ease_function=easing.ease_in_out,
        tag="ease_pattern"
    )
    
    # Test pattern execution
    ease_action.update()
    assert sprite.change_x > 0  # Moving right
    assert sprite.change_y == 0
    
    # Test attack phase
    ease_action._elapsed = 1.0
    ease_action.update()
    assert sprite.change_angle > 0  # Rotating
    assert sprite.change_y > 0  # Moving up
    
    # Test retreat phase
    ease_action._elapsed = 2.0
    ease_action.update()
    assert sprite.change_x < 0  # Moving left
    assert sprite.change_y < 0  # Moving down
```

## Testing Best Practices

1. Use test fixtures for sprite creation:
```python
from .fixtures import create_sprite, create_sprite_list

def test_action():
    sprite = create_sprite()
    sprite_list = create_sprite_list()
    # Test with fixtures
```

2. Test initial state, updates, and cleanup:
```python
def test_action_lifecycle():
    sprite = create_sprite()
    action = move_until(sprite, velocity=(5, 0), condition=duration(1.0))
    
    # Test initial state
    assert not action.is_running
    
    # Test after apply
    action.apply(sprite)
    assert action.is_running
    
    # Test after update
    action.update()
    assert sprite.change_x == 5
    
    # Test after stop
    action.stop()
    assert not action.is_running
    assert sprite.change_x == 0
```

3. Test edge cases and error conditions:
```python
def test_invalid_parameters():
    sprite = create_sprite()
    
    # Test invalid velocity
    with pytest.raises(ValueError):
        move_until(sprite, velocity=(float('inf'), 0), condition=duration(1.0))
    
    # Test invalid duration
    with pytest.raises(ValueError):
        ease(sprite, move_action, duration=-1.0)
```

4. Test action completion:
```python
def test_action_completion():
    sprite = create_sprite()
    completion_called = False
    
    def on_complete():
        nonlocal completion_called
        completion_called = True
    
    action = move_until(
        sprite,
        velocity=(5, 0),
        condition=duration(1.0),
        on_complete=on_complete
    )
    
    # Run until complete
    action._elapsed = 1.0
    action.update()
    
    assert completion_called
    assert not action.is_running
```

5. Test action scaling:
```python
def test_action_scaling():
    sprite = create_sprite()
    action = move_until(sprite, velocity=(5, 0), condition=duration(1.0))
    
    # Test normal speed
    action.update()
    normal_velocity = sprite.change_x
    
    # Test scaled speed
    action.scale(2.0)
    action.update()
    assert sprite.change_x == normal_velocity * 2
```

## Common Testing Patterns

1. Testing velocity changes:
```python
def test_velocity_changes():
    sprite = create_sprite()
    action = move_until(sprite, velocity=(5, 0), condition=duration(1.0))
    
    # Test positive velocity
    action.update()
    assert sprite.change_x == 5
    
    # Test negative velocity
    action.stop()
    action = move_until(sprite, velocity=(-5, 0), condition=duration(1.0))
    action.update()
    assert sprite.change_x == -5
```

2. Testing conditions:
```python
def test_custom_condition():
    sprite = create_sprite()
    target_x = 100
    
    def reach_target():
        return sprite.center_x >= target_x
    
    action = move_until(sprite, velocity=(5, 0), condition=reach_target)
    
    # Run until condition met
    while not action.done:
        action.update()
        sprite.center_x += sprite.change_x
    
    assert sprite.center_x >= target_x
```

3. Testing callbacks:
```python
def test_callbacks():
    sprite = create_sprite()
    events = []
    
    def on_start():
        events.append("start")
    
    def on_update():
        events.append("update")
    
    def on_complete():
        events.append("complete")
    
    action = move_until(
        sprite,
        velocity=(5, 0),
        condition=duration(1.0),
        on_start=on_start,
        on_update=on_update,
        on_complete=on_complete
    )
    
    # Test callback sequence
    action.apply(sprite)
    assert events == ["start"]
    
    action.update()
    assert "update" in events
    
    action._elapsed = 1.0
    action.update()
    assert events[-1] == "complete"
```

4. Testing sprite lists:
```python
def test_sprite_list():
    sprite_list = create_sprite_list()
    action = move_until(
        sprite_list,
        velocity=(5, 0),
        condition=duration(1.0)
    )
    
    # Test all sprites move together
    action.update()
    for sprite in sprite_list:
        assert sprite.change_x == 5
        assert sprite.change_y == 0
```

5. Testing action tags:
```python
def test_action_tags():
    sprite = create_sprite()
    
    # Apply multiple actions
    move_until(sprite, velocity=(5, 0), condition=duration(1.0), tag="movement")
    rotate_until(sprite, velocity=180, condition=duration(1.0), tag="rotation")
    
    # Stop specific action
    Action.stop_all(tag="movement")
    assert sprite.change_x == 0
    assert sprite.change_angle == 180
``` 