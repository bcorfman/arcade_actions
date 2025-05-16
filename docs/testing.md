# Testing Guide

## Overview

This document provides detailed testing patterns, examples, and best practices for the ArcadeActions framework. It covers all action types and their specific testing requirements.

## Abstract Method Requirements

All action classes must implement the following abstract methods:
- `start()`: Called when the action begins. Must be implemented by all action classes.

When testing action classes:
1. Create mock implementations that provide the required abstract methods
2. Call `start()` before `update()` in all tests
3. Verify that `start()` is called exactly once per action

Example mock implementation:
```python
class MockAction(Action):
    def start(self) -> None:
        self.start_called = True
        # Add any initialization needed for the test
```

## Test Structure

### 1. Action Initialization Tests
```python
def test_action_initialization(self):
    """Test action initialization."""
    # Test required parameters
    action = ActionClass(required_param=value)
    assert action.param == value
    
    # Test optional parameters
    assert action.optional_param == default_value
    
    # Test parameter validation
    with pytest.raises(ValueError):
        ActionClass()  # Missing required param
```

### 2. Action Lifecycle Tests
```python
def test_action_lifecycle(self, sprite):
    """Test complete action lifecycle."""
    # Create action with mock implementation of required abstract methods
    action = MockActionClass(params)
    action.target = sprite
    
    # Start - REQUIRED for all actions
    action.start()  # Must be called before update
    assert action.start_called
    
    # Update
    action.update(0.5)
    assert intermediate_conditions
    
    # Complete
    action.update(0.5)
    assert action.done
    assert final_conditions
    
    # Stop
    action.stop()
    assert cleanup_conditions
```

### 3. Edge Case Tests
```python
def test_edge_cases(self, sprite):
    """Test edge cases."""
    # Test zero duration
    action = MockActionClass(duration=0)
    action.start()  # Required before update
    
    # Test boundary conditions
    action = MockActionClass(param=boundary_value)
    action.start()  # Required before update
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        MockActionClass(param=invalid_value)
```

## Test Fixtures

### Common Fixtures
```python
@pytest.fixture
def sprite(self):
    """Create a test sprite."""
    sprite = create_test_sprite()
    sprite.position = (0, 0)
    return sprite

@pytest.fixture
def sprite_list(self):
    """Create a test sprite list."""
    sprites = arcade.SpriteList()
    for _ in range(3):
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        sprites.append(sprite)
    return sprites
```

## Action-Specific Test Patterns

### 1. Movement Actions
```python
def test_continuous_movement(self, sprite):
    """Test that movement continues until stopped."""
    action = MockWrappedMove(800, 600)
    action.target = sprite
    action.start()  # Required before update
    action.update(1.0)
    assert sprite.position != (0, 0)
    assert not action.done  # Never done unless stopped

def test_boundary_handling(self, sprite):
    """Test boundary conditions."""
    action = MockWrappedMove(800, 600)
    action.target = sprite
    action.start()  # Required before update
    sprite.position = (900, 300)
    action.update(1.0)
    assert sprite.left == 0  # Should wrap to left side
```

### 2. Physics Actions
```python
def test_physics_movement(self, sprite):
    """Test movement with physics body."""
    sprite.pymunk = MockPhysicsBody()
    sprite.pymunk.position = (0, 0)
    sprite.pymunk.velocity = (100, 100)
    
    action = MockWrappedMove(800, 600)
    action.target = sprite
    action.start()  # Required before update
    action.update(1.0)
    assert sprite.pymunk.position != (0, 0)
```

### 3. Composite Actions
```python
def test_sequence_execution(self, sprite):
    """Test action sequence execution."""
    action1 = MockMoveBy((100, 0), 1.0)
    action2 = MockRotateBy(90, 1.0)
    sequence = Sequence([action1, action2])
    sequence.target = sprite
    sequence.start()  # Required before update
    
    # First action
    sequence.update(1.0)
    assert sprite.position == (100, 0)
    assert not sequence.done
    
    # Second action
    sequence.update(1.0)
    assert sprite.angle == 90
    assert sequence.done
```

## Test Categories

### 1. Movement Actions
- Test position updates
- Test velocity calculations
- Test boundary handling
- Test physics integration

### 2. Physics Actions
- Test acceleration
- Test gravity
- Test collision response
- Test force application

### 3. Boundary Actions
- Test wrapping behavior
- Test bouncing behavior
- Test boundary callbacks
- Test sprite list handling

### 4. Composite Actions
- Test sequence execution
- Test parallel execution
- Test empty composites
- Test immediate completion

## Best Practices

1. **Test Organization**
   - Group related tests together
   - Use descriptive test names
   - Document test assumptions
   - Keep tests focused and atomic

2. **Test Setup**
   - Initialize sprites with known states
   - Set up boundary conditions explicitly
   - Mock physics bodies when needed
   - Implement required abstract methods in test classes
   - Call start() before update() in all tests
   - Clean up after tests

3. **Edge Cases**
   - Test boundary conditions
   - Test zero values
   - Test maximum values
   - Test invalid inputs

4. **Documentation**
   - Document test setup
   - Explain test expectations
   - Note any assumptions
   - Document physics integration details

## Mock Objects

### Mock Physics Body
```python
class MockPhysicsBody:
    def __init__(self):
        self.position = (0, 0)
        self.velocity = (0, 0)
        self.acceleration = (0, 0)
```

### Mock Action
```python
class MockAction(Action):
    def __init__(self, duration: float = 1.0):
        super().__init__()
        self.duration = duration
        self.start_called = False
        self.update_called = False
        self.stop_called = False

    def start(self) -> None:
        """Required abstract method implementation."""
        self.start_called = True

    def update(self, delta_time: float) -> None:
        self.update_called = True
        super().update(delta_time)
        if self._elapsed >= self.duration:
            self.done = True

    def stop(self) -> None:
        self.stop_called = True
        super().stop()
``` 