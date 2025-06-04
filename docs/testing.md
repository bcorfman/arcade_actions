# Testing Guide

## Overview

This document provides detailed testing patterns, examples, and best practices for the ArcadeActions framework. It covers all action types and their specific testing requirements, with a focus on proper dependency injection and testability.

## Abstract Method Requirements

All action classes must implement the following abstract methods:
- `start()`: Called when the action begins. Must be implemented by all action classes.

When testing action classes:
1. Use `ActionSprite` for all sprite-based tests
2. Use `sprite.do(action)` instead of setting target and calling start
3. Use `sprite.update()` instead of calling action.update directly
4. Verify that `start()` is called exactly once per action

Example implementation showing proper dependency injection:
```python
class MoveAction(Action):
    def __init__(self, get_bounds: Callable[[], tuple[float, float]]):
        """
        Initialize the move action.
        
        Args:
            get_bounds: Function that returns current screen bounds
        """
        super().__init__()
        self.get_bounds = get_bounds

    def start(self) -> None:
        """Required abstract method implementation."""
        width, height = self.get_bounds()
        # Initialize movement based on bounds
```

## Test Structure

### 1. Action Initialization Tests
```python
def test_action_initialization(self):
    """Test action initialization with dependencies."""
    # Mock bounds function
    get_bounds = lambda: (800, 600)
    
    # Test required parameters
    action = MoveAction(get_bounds=get_bounds)
    assert action.get_bounds == get_bounds
    
    # Test parameter validation
    with pytest.raises(ValueError):
        MoveAction()  # Missing required param
```

### 2. Action Lifecycle Tests
```python
def test_action_lifecycle(self, sprite):
    """Test complete action lifecycle."""
    # Mock bounds function
    get_bounds = lambda: (800, 600)
    
    # Create action with dependencies
    action = MoveAction(get_bounds=get_bounds)
    
    # Use ActionSprite.do() instead of setting target and calling start
    sprite.do(action)
    assert sprite.position == (0, 0)  # Initial position
    
    # Use ActionSprite.update() instead of action.update()
    sprite.update(0.5)
    assert sprite.position != (0, 0)  # Position should change
    
    # Complete
    sprite.update(0.5)
    assert action.done
    assert sprite.position == (100, 100)  # Final position
```

### 3. Edge Case Tests
```python
def test_edge_cases(self, sprite):
    """Test edge cases."""
    get_bounds = lambda: (800, 600)
    
    # Test zero duration
    action = MoveAction(
        duration=0,
        get_bounds=get_bounds
    )
    sprite.do(action)
    assert action.done  # Should complete immediately
    
    # Test boundary conditions
    action = MoveAction(
        get_bounds=get_bounds
    )
    sprite.position = (800, 600)  # At boundary
    sprite.do(action)
    sprite.update(1.0)
    assert sprite.position == (0, 0)  # Should wrap
```

## Test Fixtures

### Common Fixtures
```python
@pytest.fixture
def sprite():
    """Create a test ActionSprite."""
    sprite = ActionSprite(":resources:images/items/star.png")
    sprite.position = (0, 0)
    return sprite

@pytest.fixture
def sprite_list():
    """Create a test sprite list."""
    sprites = arcade.SpriteList()
    for _ in range(3):
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprites.append(sprite)
    return sprites
```

## When to Use Mocks

While we prefer using real implementations, there are cases where mocks are necessary:

1. **External Dependencies**
   - Screen bounds functions
   - Random number generators
   - Time-based functions
   Example:
   ```python
   def test_wrapped_movement(self, sprite):
       """Test movement with wrapped boundaries."""
       # Mock bounds function
       get_bounds = lambda: (800, 600)
       action = WrappedMove(get_bounds=get_bounds)
       sprite.do(action)
       # Test wrapping behavior
   ```

2. **Slow Operations**
   - Complex calculations
   - File operations
   - Network requests
   Example:
   ```python
   def test_complex_path(self, sprite):
       """Test movement along a complex path."""
       # Mock path calculation
       get_path = lambda: [(0, 0), (100, 100), (200, 0)]
       action = FollowPath(get_path=get_path)
       sprite.do(action)
       # Test path following
   ```

3. **Unpredictable Behavior**
   - Random number generation
   - Time-based operations
   - User input
   Example:
   ```python
   def test_random_movement(self, sprite):
       """Test random movement pattern."""
       # Mock random number generator
       get_random = lambda: 0.5  # Always return 0.5 for testing
       action = RandomMove(get_random=get_random)
       sprite.do(action)
       # Test movement pattern
   ```

4. **Isolation Testing**
   - Error conditions
   - Edge cases
   - Boundary conditions
   Example:
   ```python
   def test_boundary_conditions(self, sprite):
       """Test behavior at screen boundaries."""
       # Mock bounds function
       get_bounds = lambda: (800, 600)
       action = BoundedMove(get_bounds=get_bounds)
       sprite.position = (800, 600)  # At boundary
       sprite.do(action)
       # Test bouncing behavior
   ```

5. **Resource Constraints**
   - Memory-intensive operations
   - CPU-intensive calculations
   - File system operations
   Example:
   ```python
   def test_large_sprite_list(self, sprite):
       """Test action with large sprite list."""
       # Mock sprite list with 1000 sprites
       sprites = [ActionSprite() for _ in range(1000)]
       action = GroupAction(sprites, MoveBy((100, 0), 1.0))
       # Test group movement
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
   - Always use `ActionSprite` for sprite-based tests
   - Use `sprite.do(action)` instead of setting target and calling start
   - Use `sprite.update()` instead of calling action.update directly
   - Initialize sprites with known states
   - Set up boundary conditions explicitly
   - Clean up after tests

4. **Edge Cases**
   - Test boundary conditions
   - Test zero durations
   - Test maximum values
   - Test invalid inputs
   - Test error conditions

For detailed testing patterns for specific action types, see:
- `testing_movement.md` for movement actions
- `testing_index.md` for a complete list of test files

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