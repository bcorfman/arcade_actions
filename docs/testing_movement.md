# Movement Action Testing Guide

## Overview

This document provides detailed guidance for testing the movement actions in the ArcadeActions framework. These actions (`_Move`, `WrappedMove`, `BoundedMove`, `Driver`) have unique characteristics that require specialized testing approaches.

For general testing patterns, fixtures, and best practices, see `testing.md`.

## Key Differences from Standard Actions

Movement actions differ from standard actions in several ways:
- No fixed duration - they run continuously until stopped
- Can target both single sprites and sprite lists
- Handle boundary conditions (wrapping/bouncing)
- Optional physics integration
- Complex state management (velocity, acceleration, etc.)

## Test Structure

### 1. Base Movement Tests

```python
class TestWrappedMove:
    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    def test_continuous_movement(self, sprite):
        """Test that movement continues until stopped."""
        action = WrappedMove(800, 600)
        sprite.do(action)
        
        # Movement should continue
        sprite.update(1.0)
        assert sprite.position != (0, 0)
        assert not action.done  # Never done unless stopped
```

### 2. Boundary Condition Tests

```python
def test_wrapping_behavior(self, sprite):
    """Test sprite wrapping at screen boundaries."""
    action = WrappedMove(800, 600)
    sprite.do(action)
    
    # Move beyond right boundary
    sprite.position = (900, 300)
    sprite.update(1.0)
    assert sprite.left == 0  # Should wrap to left side
```

### 3. Physics Integration Tests

```python
def test_physics_movement(self, sprite):
    """Test movement with physics body."""
    # Mock physics body
    sprite.pymunk = MockPhysicsBody()
    sprite.pymunk.position = (0, 0)
    sprite.pymunk.velocity = (100, 100)
    
    action = WrappedMove(800, 600)
    sprite.do(action)
    
    sprite.update(1.0)
    assert sprite.pymunk.position != (0, 0)
```

## Movement-Specific Test Categories

### 1. Movement Behavior
- Continuous movement
- Velocity/acceleration
- Direction changes
- Speed limits

### 2. Boundary Handling
- Wrapping behavior
- Bouncing behavior
- Boundary callbacks
- Edge cases (exactly at boundary)

### 3. Physics Integration
- Physics body updates
- Velocity preservation
- Position synchronization
- Physics state cleanup

### 4. Sprite List Handling
- Group movement
- Individual sprite updates
- List-level boundary checks
- List-level callbacks

### 5. State Management
- Velocity tracking
- Acceleration application
- Speed limits
- Direction changes

## Movement-Specific Best Practices

1. **Test Setup**
   - Initialize sprites with known positions and velocities
   - Set up boundary conditions explicitly
   - Mock physics bodies when needed

2. **Test Organization**
   - Group related tests together
   - Use descriptive test names
   - Document test assumptions

3. **Edge Cases**
   - Test boundary conditions
   - Test zero velocities
   - Test maximum velocities
   - Test physics body edge cases

4. **Documentation**
   - Document test setup
   - Explain test expectations
   - Note any assumptions
   - Document physics integration details

For general testing best practices, see `testing.md`. 