# Movement Action Testing Guide

## Overview

This document provides detailed guidance for testing the movement actions in the ArcadeActions framework. These actions (`_Move`, `WrappedMove`, `BoundedMove`, `Driver`) have unique characteristics that require specialized testing approaches.

For general testing patterns, fixtures, and best practices, see `testing.md`.

## Key Differences from Standard Actions

Movement actions differ from standard actions in several ways:
- **Action Controllers**: `BoundedMove` and `WrappedMove` work as controllers that modify other actions
- **IntervalAction Integration**: Work with `MoveBy`, `MoveTo`, and eased movements
- **Boundary Conditions**: Handle wrapping/bouncing behavior
- **Composite Actions**: Use the `|` operator to combine movement with boundary handling
- **Complex State Management**: Modify running actions dynamically

## Test Structure

### 1. Action Controller Tests

```python
from actions.base import ActionSprite
from actions.interval import MoveBy
from actions.move import WrappedMove, BoundedMove

class TestWrappedMove:
    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position."""
        sprite = ActionSprite(":resources:images/items/ladderMid.png")
        sprite.position = (0, 0)
        return sprite

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns screen bounds."""
        return lambda: (800, 600)

    def test_wrap_with_move_by(self, sprite, get_bounds):
        """Test wrapping behavior with MoveBy action."""
        # Create movement action to move sprite off right edge
        move_action = MoveBy((200, 0), 0.2)  # Move 200 pixels right over 0.2 seconds
        wrap_action = WrappedMove(get_bounds)

        # Position sprite close to right edge
        sprite.center_x = 750
        sprite.center_y = 300

        # Combine actions
        combined_action = move_action | wrap_action
        sprite.do(combined_action)

        # Update for full duration
        sprite.update(0.2)

        # Verify sprite wrapped to left edge
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged
```

### 2. Boundary Condition Tests

```python
def test_bounce_with_action_reversal(self, sprite):
    """Test bouncing behavior with action reversal."""
    def get_bounds():
        return (0, 0, 800, 600)  # left, bottom, right, top

    # Create movement action to move sprite toward right edge
    move_action = MoveBy((200, 0), 1.0)  # Move right continuously
    bounce_action = BoundedMove(get_bounds)

    # Position sprite close to right edge
    sprite.center_x = 720  # Close to right edge at 800
    sprite.center_y = 300

    # Combine actions
    combined_action = move_action | bounce_action
    sprite.do(combined_action)

    # Update for partial duration to trigger bounce
    sprite.update(0.5)

    # Verify sprite bounced (should be moving left now)
    assert sprite.center_x < 720  # Moved back from edge
```

### 3. Callback Testing

```python
def test_bounce_callback(self, sprite):
    """Test bounce callback with correct axis information."""
    bounces = []

    def on_bounce(sprite, axis):
        bounces.append(axis)

    def get_bounds():
        return (0, 0, 800, 600)

    # Moving toward top-right corner
    move_action = MoveBy((200, 200), 1.0)  # Move diagonally continuously
    bounce_action = BoundedMove(get_bounds, on_bounce=on_bounce)

    # Position sprite close to top-right corner
    sprite.center_x = 720  # Close to right edge at 800
    sprite.center_y = 520  # Close to top edge at 600

    # Combine actions
    combined_action = move_action | bounce_action
    sprite.do(combined_action)

    # Update for partial duration to trigger bounce
    sprite.update(0.5)

    # Verify correct axes were reported
    assert "x" in bounces
    assert "y" in bounces
    assert len(bounces) == 2  # Both axes bounced
```

## Movement-Specific Test Categories

### 1. Action Controller Behavior
- Combining movement with boundary actions using `|`
- Action reversal when boundaries are hit
- Continued movement after boundary events
- Multiple action combinations

### 2. Boundary Handling
- Wrapping behavior at each edge
- Bouncing behavior at each edge
- Corner cases (diagonal movement)
- Boundary callbacks with correct parameters

### 3. IntervalAction Integration
- `MoveBy` action reversal
- `MoveTo` action modification
- Eased movement handling
- Complex composite actions

### 4. Sprite List Handling
- Group movement with individual boundary handling
- List-level boundary checks
- Independent sprite behavior
- List-level callbacks

### 5. State Management
- Action state preservation
- Position correction after boundary events
- Velocity reversal
- Duration and timing preservation

## Movement-Specific Best Practices

1. **Test Setup**
   - Position sprites near boundaries for predictable testing
   - Use appropriate durations for movement actions
   - Set up boundary functions that return consistent values

2. **Action Combination Testing**
   - Test both `move_action | boundary_action` patterns
   - Verify that boundary actions don't interfere with movement
   - Test complex action chains

3. **Edge Cases**
   - Test sprites exactly at boundaries
   - Test zero-duration movements
   - Test very fast movements that might skip boundaries
   - Test corner collisions

4. **Callback Testing**
   - Verify callback parameters are correct
   - Test callback timing (when they're called)
   - Test multiple callbacks in sequence
   - Test callback error handling

5. **Performance Considerations**
   - Test with many sprites for performance
   - Verify boundary detection efficiency
   - Test action reversal overhead

## Example Test Patterns

### Pattern 1: Basic Movement + Boundary
```python
def test_basic_pattern(self, sprite):
    move_action = MoveBy((dx, dy), duration)
    boundary_action = BoundedMove(get_bounds)
    sprite.do(move_action | boundary_action)
    sprite.update(test_duration)
    # Assert expected behavior
```

### Pattern 2: Eased Movement + Boundary
```python
def test_eased_pattern(self, sprite):
    move_action = MoveBy((dx, dy), duration)
    eased_action = Easing(move_action, easing.ease_in_out)
    boundary_action = WrappedMove(get_bounds)
    sprite.do(eased_action | boundary_action)
    sprite.update(test_duration)
    # Assert expected behavior
```

### Pattern 3: Sprite List Testing
```python
def test_sprite_list_pattern(self, sprite_list):
    boundary_action = BoundedMove(get_bounds)
    boundary_action.target = sprite_list
    boundary_action.start()
    
    # Apply individual movement actions
    for sprite in sprite_list:
        move_action = MoveBy((dx, dy), duration)
        sprite.do(move_action)
    
    # Update all
    sprite_list.update(test_duration)
    boundary_action.update(test_duration)
    # Assert expected behavior
```

For general testing best practices, see `testing.md`. 