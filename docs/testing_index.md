# Testing Documentation Index

## Overview

This document serves as a comprehensive index for all testing-related documentation in the ArcadeActions framework.

**For API usage and implementation patterns, see [api_usage_guide.md](api_usage_guide.md)**

## Testing Documentation

### 1. [testing.md](testing.md) - **Core Testing Patterns**
**Comprehensive testing guide covering:**
- Individual action testing with ActionSprite
- Group action testing with SpriteGroup and GroupAction
- Boundary action testing with BoundedMove coordination
- Collision detection testing with method chaining
- Composite action testing (sequences, parallel, loops, repeats)
- Common test fixtures and dependency injection
- Mock object usage and best practices

### 2. [testing_movement.md](testing_movement.md) - **Movement Action Specialization**
**Specialized patterns for complex movement testing:**
- Action controller combinations (`|` operator)
- Advanced boundary condition testing
- Callback testing with proper parameters
- Performance testing for movement actions

*For basic movement testing patterns, see the main testing.md guide*

## Reference Documentation
- **[prd.md](prd.md)** - Testing requirements and architecture standards
- **[api_usage_guide.md](api_usage_guide.md)** - Implementation patterns (consult for usage examples)
- **[boundary_event.md](boundary_event.md)** - Implementation guide for boundary callbacks
- **[game_loop_updates.md](game_loop_updates.md)** - Implementation guide for game integration

## Quick Reference: Testing Patterns by Component

### ActionSprite Testing
```python
def test_action_sprite(self):
    sprite = ActionSprite(":resources:images/test.png")
    sprite.center_x = 0
    
    move_action = MoveBy((100, 0), 1.0)
    sprite.do(move_action)
    
    sprite.update(0.5)  # Half duration
    assert sprite.center_x == 50
    
    sprite.update(0.5)  # Complete
    assert sprite.center_x == 100
    assert not sprite.is_busy()
```

### SpriteGroup + GroupAction Testing
```python
def test_sprite_group(self, sprite_group):
    initial_positions = [s.center_x for s in sprite_group]
    
    move_action = MoveBy((50, 0), 1.0)
    group_action = sprite_group.do(move_action)
    
    # Verify GroupAction creation and tracking
    assert len(group_action.actions) == len(sprite_group)
    assert len(sprite_group._group_actions) == 1
    
    sprite_group.update(1.0)  # Auto-updates GroupActions
    
    # Verify coordinated movement
    for i, sprite in enumerate(sprite_group):
        assert sprite.center_x == initial_positions[i] + 50
    
    # Verify automatic cleanup
    assert len(sprite_group._group_actions) == 0
```

### BoundedMove + SpriteGroup Testing
```python
def test_boundary_with_group(self, sprite_group):
    # Position near boundary
    for i, sprite in enumerate(sprite_group):
        sprite.center_x = 720 + i * 10  # Near right edge
    
    bounce_called = False
    def on_bounce(sprite, axis):
        nonlocal bounce_called
        bounce_called = True
        # Coordinate entire group
        sprite_group.clear_actions()
    
    bounds = lambda: (0, 0, 800, 600)
    bounce_action = BoundedMove(bounds, on_bounce=on_bounce)
    bounce_action.target = sprite_group  # Apply to entire group
    bounce_action.start()
    
    move_action = MoveBy((200, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)
    bounce_action.update(1.0)
    
    assert bounce_called  # Edge sprite triggered callback
```

### Collision Detection Testing
```python
def test_collision_detection(self):
    bullets = SpriteGroup()
    enemies = SpriteGroup()
    
    # Create overlapping sprites
    bullet = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    enemy = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    bullets.append(bullet)
    enemies.append(enemy)
    
    collision_detected = False
    def on_collision(bullet, hit_enemies):
        nonlocal collision_detected
        collision_detected = True
    
    # Method chaining for multiple collision handlers
    bullets.on_collision_with(enemies, on_collision)
    bullets.update_collisions()
    
    assert collision_detected

def test_collision_detection_with_mock_detector(self):
    """Test collision detection using MockCollisionDetector for full control."""
    from actions.protocols import MockCollisionDetector
    
    # Inject mock collision detector
    mock_detector = MockCollisionDetector()
    bullets = SpriteGroup(collision_detector=mock_detector)
    enemies = SpriteGroup()
    
    # Create test sprites
    bullet = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    enemy = ActionSprite(":resources:images/test.png", center_x=200, center_y=200)
    bullets.append(bullet)
    enemies.append(enemy)
    
    # Pre-configure collision result
    mock_detector.set_collision_result(bullet, tuple(enemies), [enemy])
    
    collision_detected = False
    def on_collision(bullet, hit_enemies):
        nonlocal collision_detected
        collision_detected = True
    
    bullets.on_collision_with(enemies, on_collision)
    bullets.update_collisions()
    
    # Should detect collision even though sprites are far apart
    assert collision_detected

def test_collision_detection_without_opengl(self):
    """Test collision detection using BoundingBoxCollisionDetector (no OpenGL needed)."""
    from actions.protocols import BoundingBoxCollisionDetector
    
    # Inject bounding box collision detector
    bbox_detector = BoundingBoxCollisionDetector()
    bullets = SpriteGroup(collision_detector=bbox_detector)
    enemies = SpriteGroup()
    
    # Create overlapping sprites
    bullet = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    enemy = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    bullets.append(bullet)
    enemies.append(enemy)
    
    collision_detected = False
    def on_collision(bullet, hit_enemies):
        nonlocal collision_detected
        collision_detected = True
    
    bullets.on_collision_with(enemies, on_collision)
    bullets.update_collisions()
    
    # Should detect collision since sprites overlap
    assert collision_detected
```

## API Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Single sprite needs actions | `ActionSprite.do(action)` | Only ActionSprite supports actions |
| Multiple sprites move together | `SpriteGroup.do(action)` | Creates coordinated GroupAction |
| Sprites need different actions | Individual `ActionSprite.do()` | Different behaviors per sprite |
| Group boundary detection | `BoundedMove` + `SpriteGroup` | Edge detection + callbacks |
| Group collision detection | `SpriteGroup.on_collision_with()` | Efficient collision handling |
| No actions needed | `arcade.Sprite` + `arcade.SpriteList` | Standard Arcade functionality |

## Common Testing Mistakes to Avoid

### ❌ Wrong Patterns
```python
# DON'T: Use arcade.Sprite with actions
sprite = arcade.Sprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # FAILS!

# DON'T: Manual GroupAction tracking
group_action = sprite_group.do(move_action)
group_action.update(delta_time)  # Easy to forget!

# DON'T: Individual BoundedMove in groups
for sprite in sprite_group:
    sprite.do(move_action | BoundedMove(bounds))  # Spacing issues!
```

### ✅ Correct Patterns
```python
# DO: Use ActionSprite for actions
sprite = ActionSprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # Works!

# DO: Let SpriteGroup handle GroupActions
sprite_group.do(move_action)
sprite_group.update(delta_time)  # Automatic management!

# DO: Apply BoundedMove to entire group
bounce_action = BoundedMove(bounds, on_bounce=callback)
bounce_action.target = sprite_group
bounce_action.start()
sprite_group.do(move_action)
```

## Test Fixtures Reference

```python
@pytest.fixture
def sprite():
    """Individual ActionSprite for basic testing."""
    sprite = ActionSprite(":resources:images/test.png")
    sprite.position = (0, 0)
    return sprite

@pytest.fixture
def sprite_group():
    """SpriteGroup with 3 positioned sprites."""
    group = SpriteGroup()
    for i in range(3):
        sprite = ActionSprite(":resources:images/test.png")
        sprite.center_x = i * 100
        sprite.center_y = 100
        group.append(sprite)
    return group

@pytest.fixture
def get_bounds():
    """Bounds function for boundary testing."""
    return lambda: (0, 0, 800, 600)  # left, bottom, right, top
```

## Integration Testing Examples

### Space Invaders Pattern
```python
def test_space_invaders_integration(self):
    enemies = SpriteGroup()
    # Create formation, set up BoundedMove with edge detection
    # Test coordinated movement, bouncing, spacing preservation
```

### Collision System Pattern
```python
def test_collision_system_integration(self):
    bullets = SpriteGroup()
    enemies = SpriteGroup()
    shields = SpriteGroup()
    # Test method chaining: bullets.on_collision_with(enemies, cb1).on_collision_with(shields, cb2)
```

## Documentation Usage Flow

1. **Start with [api_usage_guide.md](api_usage_guide.md)** - Understand when to use each component
2. **Reference [testing.md](testing.md)** - Learn testing patterns for each component
3. **Use specialized guides** - [testing_movement.md](testing_movement.md), [boundary_event.md](boundary_event.md)
4. **Check [prd.md](prd.md)** - Verify requirements and architecture decisions
5. **Follow examples** - Use the patterns shown in this index

## Best Practices Summary

1. **ActionSprite is required** for all action-based sprites
2. **SpriteGroup manages GroupActions** automatically
3. **BoundedMove + SpriteGroup** provides edge detection and coordination
4. **Method chaining** simplifies collision detection setup
5. **Test both individual and group behaviors**
6. **Verify automatic cleanup** of completed actions
7. **Use dependency injection** for testable code
8. **Follow the documented patterns** consistently

This index provides the roadmap for understanding and testing the ArcadeActions framework effectively. Start with the API usage guide and follow the patterns consistently throughout your code and tests. 