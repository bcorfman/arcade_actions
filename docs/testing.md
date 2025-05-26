# Testing Guide

## Overview

This document provides detailed testing patterns, examples, and best practices for the ArcadeActions framework. It covers all action types and their specific testing requirements, with a focus on proper dependency injection and testability.

## Abstract Method Requirements

All action classes must implement the following abstract methods:
- `start()`: Called when the action begins. Must be implemented by all action classes.

When testing action classes:
1. Use real implementations of dependencies where possible
2. Only use mocks when testing in isolation is necessary
3. Call `start()` before `update()` in all tests
4. Verify that `start()` is called exactly once per action

Example implementation showing proper dependency injection:
```python
class MoveAction(Action):
    def __init__(self, physics_engine: PhysicsEngine):
        """
        Initialize the move action.
        
        Args:
            physics_engine: The physics engine to use for movement calculations
        """
        super().__init__()
        self.physics_engine = physics_engine

    def start(self) -> None:
        """Required abstract method implementation."""
        self.physics_engine.initialize()
```

## Test Structure

### 1. Action Initialization Tests
```python
def test_action_initialization(self):
    """Test action initialization with real dependencies."""
    # Use real physics engine
    physics_engine = PhysicsEngine()
    
    # Test required parameters with real dependencies
    action = MoveAction(physics_engine=physics_engine)
    assert action.physics_engine == physics_engine
    
    # Test parameter validation
    with pytest.raises(ValueError):
        MoveAction()  # Missing required param
```

### 2. Action Lifecycle Tests
```python
def test_action_lifecycle(self, sprite):
    """Test complete action lifecycle with real dependencies."""
    # Use real physics engine
    physics_engine = PhysicsEngine()
    
    # Create action with real dependencies
    action = MoveAction(physics_engine=physics_engine)
    action.target = sprite
    
    # Start - REQUIRED for all actions
    action.start()  # Must be called before update
    assert physics_engine.is_initialized
    
    # Update
    action.update(0.5)
    assert intermediate_conditions
    
    # Complete
    action.update(0.5)
    assert action.done
    assert final_conditions
    
    # Stop and cleanup
    action.stop()
    assert cleanup_conditions
    physics_engine.cleanup()
```

### 3. Edge Case Tests
```python
def test_edge_cases(self, sprite):
    """Test edge cases with real dependencies."""
    physics_engine = PhysicsEngine()
    
    # Test zero duration
    action = MoveAction(
        duration=0,
        physics_engine=physics_engine
    )
    action.start()  # Required before update
    
    # Test boundary conditions
    action = MoveAction(
        param=boundary_value,
        physics_engine=physics_engine
    )
    action.start()  # Required before update
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        MoveAction(
            param=invalid_value,
            physics_engine=physics_engine
        )
```

## Test Fixtures

### Common Fixtures
```python
@pytest.fixture
def physics_engine():
    """Create a real physics engine for testing."""
    engine = PhysicsEngine()
    yield engine
    engine.cleanup()  # Proper cleanup

@pytest.fixture
def sprite(physics_engine):
    """Create a test sprite with real physics engine."""
    sprite = create_test_sprite(physics_engine=physics_engine)
    sprite.position = (0, 0)
    return sprite

@pytest.fixture
def sprite_list(physics_engine):
    """Create a test sprite list with real physics engine."""
    sprites = arcade.SpriteList()
    for _ in range(3):
        sprite = create_test_sprite(physics_engine=physics_engine)
        sprite.position = (0, 0)
        sprites.append(sprite)
    return sprites
```

## Action-Specific Test Patterns

### 1. Movement Actions
```python
def test_continuous_movement(self, sprite, physics_engine):
    """Test that movement continues until stopped."""
    action = MoveAction(
        width=800,
        height=600,
        physics_engine=physics_engine
    )
    action.target = sprite
    action.start()  # Required before update
    action.update(1.0)
    assert sprite.position != (0, 0)
    assert not action.done  # Never done unless stopped
```

### 2. Physics Actions
```python
def test_physics_movement(self, sprite, physics_engine):
    """Test movement with real physics body."""
    sprite.pymunk = physics_engine.create_body()
    sprite.pymunk.position = (0, 0)
    sprite.pymunk.velocity = (100, 100)
    
    action = MoveAction(
        width=800,
        height=600,
        physics_engine=physics_engine
    )
    action.target = sprite
    action.start()  # Required before update
    action.update(1.0)
    assert sprite.pymunk.position != (0, 0)
```

### 3. Composite Actions
```python
def test_sequence_execution(self, sprite, physics_engine):
    """Test action sequence execution with real dependencies."""
    action1 = MoveAction(
        offset=(100, 0),
        duration=1.0,
        physics_engine=physics_engine
    )
    action2 = RotateAction(
        angle=90,
        duration=1.0,
        physics_engine=physics_engine
    )
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

## When to Use Mocks

While we prefer using real implementations, there are cases where mocks are necessary:

1. **External Dependencies**: When testing code that depends on external services or systems
2. **Slow Operations**: When real implementations are too slow for unit tests
3. **Unpredictable Behavior**: When real implementations have non-deterministic behavior
4. **Isolation Testing**: When testing error conditions or edge cases that are hard to reproduce
5. **Resource Constraints**: When real implementations require significant resources

Example of when to use a mock:
```python
def test_network_error_handling(self):
    """Test handling of network errors."""
    # Use mock network client to simulate errors
    mock_network = MockNetworkClient()
    mock_network.simulate_error()
    
    action = NetworkAction(network_client=mock_network)
    with pytest.raises(NetworkError):
        action.start()
```

## Best Practices

1. **Dependency Injection**
   - Pass all dependencies through constructors
   - Use interfaces/abstract classes for dependencies
   - Make dependencies explicit and optional when appropriate
   - Validate dependencies in constructors
   - Clean up resources properly

2. **Test Organization**
   - Group related tests together
   - Use descriptive test names
   - Document test assumptions and dependencies
   - Keep tests focused and atomic

3. **Test Setup**
   - Use real implementations by default
   - Only use mocks when necessary
   - Initialize sprites with known states
   - Set up boundary conditions explicitly
   - Call start() before update() in all tests
   - Clean up after tests

4. **Edge Cases**
   - Test boundary conditions
   - Test zero values
   - Test maximum values
   - Test invalid inputs
   - Test error conditions

5. **Documentation**
   - Document test setup and dependencies
   - Explain test expectations
   - Note any assumptions
   - Document when and why mocks are used
   - Document dependency lifecycle

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

## Mock Objects

### Mock Physics Body
```python
class MockPhysicsBody:
    def __init__(self):
        self.position = (0, 0)
        self.velocity = (0, 0)
        self.acceleration = (0, 0)
``` 