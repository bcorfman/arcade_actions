# ArcadeActions Testing Guide

## Overview

This guide documents the testing architecture and patterns for the ArcadeActions library. The test suite validates all core functionality using conditional actions, global action management, and proper composition patterns.

## Test Suite Structure

### Test Files and Coverage

| Test File | Purpose | Key Patterns Tested |
|-----------|---------|-------------------|
| `test_base.py` | Core Action class and global management | Action lifecycle, global updates, tagging |
| `test_condition_actions.py` | Conditional actions (MoveUntil, FollowPathUntil, etc.) | Condition evaluation, velocity-based updates, path following with rotation |
| `test_composite.py` | Sequential and parallel actions | Function composition, nested actions |
| `test_move.py` | Boundary actions | MoveUntil boundary detection with bounce/wrap |
| `test_formation.py` | Formation arrangement functions | Sprite positioning and layout behavior |
| `test_pattern.py` | Movement pattern functions | Pattern creation and condition helpers |
| `test_easing.py` | Ease wrapper functionality | Smooth acceleration/deceleration, nested easing, edge cases |
| `test_api_sugar.py` | Helper functions and proper usage patterns | Helper functions vs. direct classes |

### Test Organization Principles

1. **Each test file maps to one module** - Direct 1:1 relationship with source files
2. **Global action cleanup** - All tests use `Action.clear_all()` in teardown
3. **Real conditional actions** - No mocks for core functionality [[memory:6042457797249309622]]
4. **Proper composition patterns** - Tests demonstrate correct usage of helpers vs. direct classes
5. **Tag-based organization** - Tests use meaningful tags for action management

## Testing Patterns

### Pattern 1: Helper Function Testing (Simple Actions)

Tests helper functions for immediate, simple actions:

```python
def test_helper_function_immediate_application(self):
    """Test helper functions for simple, immediate actions."""
    from actions import move_until, rotate_until
    from actions.conditional import duration
    
    sprite = create_test_sprite()
    
    # Helper functions apply immediately
    move_action = move_until(sprite, (100, 0), duration(2.0), tag="movement")
    rotate_action = rotate_until(sprite, 90, duration(1.0), tag="rotation")
    
    # Verify actions are applied and registered
    assert move_action in Action._active_actions
    assert rotate_action in Action._active_actions
    
    # Test updates
    initial_x = sprite.center_x
    initial_angle = sprite.angle
    
    Action.update_all(0.1)
    
    assert sprite.center_x > initial_x
    assert sprite.angle != initial_angle
    
    # Verify tagging works
    movement_actions = Action.get_actions_for_target(sprite, "movement")
    rotation_actions = Action.get_actions_for_target(sprite, "rotation")
    
    assert len(movement_actions) == 1
    assert len(rotation_actions) == 1
```

### Pattern 2: Direct Class + Sequence Testing (Complex Behaviors)

Tests direct action classes with sequence composition for complex behaviors:

```python
def test_direct_class_sequence_composition(self):
    """Test direct classes with sequence() for complex behaviors."""
    from actions.conditional import DelayUntil, MoveUntil, RotateUntil, duration
    from actions.composite import sequence, parallel
    
    sprite = create_test_sprite()
    
    # Create complex sequence using direct classes
    complex_behavior = sequence(
        DelayUntil(duration(0.5)),
        MoveUntil((50, 0), duration(1.0)),
        parallel(
            RotateUntil(180, duration(0.5)),
            FadeUntil(-50, duration(0.8))
        )
    )
    
    # Apply the sequence
    complex_behavior.apply(sprite, tag="complex")
    
    # Verify sequence is registered as a single action
    complex_actions = Action.get_actions_for_target(sprite, "complex")
    assert len(complex_actions) == 1
    assert isinstance(complex_actions[0], _Sequence)
    
    # Test sequence execution
    initial_x = sprite.center_x
    
    # During delay phase
    Action.update_all(0.1)
    assert sprite.center_x == initial_x  # No movement during delay
    
    # After delay, during movement phase
    Action.update_all(0.6)  # Past delay phase
    assert sprite.center_x > initial_x  # Should be moving now
```

### Pattern 3: Anti-Pattern Testing (What NOT to Do)

Tests that demonstrate and document problematic patterns:

```python
def test_avoid_helper_function_operator_mixing(self):
    """Document why mixing helper functions with operators is problematic."""
    from actions import move_until, delay_until
    from actions.conditional import duration
    
    sprite = create_test_sprite()
    
    # This pattern is problematic and should be avoided
    # Helper functions apply immediately, creating conflicts with operator composition
    
    # ❌ PROBLEMATIC: This creates two separate actions that run simultaneously
    # instead of a proper sequence
    move_action = move_until(sprite, (50, 0), duration(1.0), tag="move")
    delay_action = delay_until(sprite, duration(0.5), tag="delay")
    
    # The actions are already applied and running independently
    assert len(Action.get_actions_for_target(sprite)) == 2
    
    # Even if we try to use operators, it doesn't create a proper sequence
    # because the actions are already applied
    try:
        combined = move_action + delay_action  # This might work but is confusing
        # The combined action would be a new sequence, but the original actions
        # are still running independently
    except Exception:
        pass  # This might fail depending on implementation
    
    # ✅ CORRECT: Use direct classes for sequences
    Action.clear_all()
    
    from actions.conditional import DelayUntil, MoveUntil
    from actions.composite import sequence
    
    proper_sequence = sequence(
        DelayUntil(duration(0.5)),
        MoveUntil((50, 0), duration(1.0))
    )
    proper_sequence.apply(sprite, tag="proper_sequence")
    
    # This creates a single sequence action
    assert len(Action.get_actions_for_target(sprite)) == 1
```

### Pattern 4: Path Following with Rotation Testing

Tests FollowPathUntil with automatic sprite rotation functionality:

```python
def test_path_following_with_rotation(self):
    """Test FollowPathUntil with automatic sprite rotation."""
    from actions import follow_path_until
    from actions.conditional import duration
    
    sprite = create_test_sprite()
    sprite.angle = 45  # Start with non-zero angle
    
    # Create curved path
    control_points = [(100, 100), (200, 200), (300, 100)]
    
    # Test without rotation
    follow_path_until(
        sprite, control_points, 150, duration(2.0),
        rotate_with_path=False, tag="no_rotation"
    )
    
    # Store original angle
    original_angle = sprite.angle
    
    # Update several frames
    for _ in range(10):
        Action.update_all(0.016)
    
    # Sprite angle should not have changed
    assert sprite.angle == original_angle
    
    # Clear and test with rotation
    Action.clear_all()
    sprite.center_x = 100  # Reset position
    sprite.center_y = 100
    
    # Test with rotation enabled
    follow_path_until(
        sprite, control_points, 150, duration(2.0),
        rotate_with_path=True, tag="with_rotation"
    )
    
    # Update to get movement and rotation
    Action.update_all(0.016)
    Action.update_all(0.016)
    
    # Sprite should now be rotated to face movement direction
    assert sprite.angle != original_angle
    
    # Test with rotation offset for sprite artwork pointing up
    Action.clear_all()
    sprite.center_x = 100  # Reset position
    sprite.center_y = 100
    
    follow_path_until(
        sprite, control_points, 150, duration(2.0),
        rotate_with_path=True, rotation_offset=-90.0,
        tag="with_offset"
    )
    
    # Update to get movement and rotation
    Action.update_all(0.016)
    Action.update_all(0.016)
    
    # Verify the rotation includes the offset
    # For horizontal movement (0°), with -90° offset, expect -90°
    expected_angle = -90.0
    assert abs(sprite.angle - expected_angle) < 5.0  # Allow some tolerance
```

### Pattern 5: Formation Testing

Tests formation positioning with proper action patterns:

```python
def test_formation_with_proper_action_patterns(self):
    """Test formation functions with proper action usage patterns."""
    from actions.formation import arrange_grid, arrange_diamond
    from actions.conditional import DelayUntil, MoveUntil, FadeUntil, duration
    from actions.composite import sequence, parallel
    from actions import move_until
    
    sprite_list = create_test_sprite_list(6)
    
    # Apply formation pattern
    arrange_grid(sprite_list, rows=2, cols=3, start_x=200, start_y=400, spacing_x=60, spacing_y=50)
    
    # Verify positioning
    assert sprite_list[0].center_x == 200
    assert sprite_list[0].center_y == 400
    assert sprite_list[1].center_x == 260  # 200 + 60 spacing
    assert sprite_list[3].center_y == 350  # 400 - 50 spacing
    
    # ✅ CORRECT: Use helper functions for simple group actions
    move_until(sprite_list, (50, -25), duration(2.0), tag="simple_movement")
    
    # ✅ CORRECT: Use direct classes for complex sequences
    complex_formation_behavior = sequence(
        DelayUntil(duration(1.0)),
        MoveUntil((50, -25), duration(2.0)),
        parallel(
            MoveUntil((0, -50), duration(1.0)),
            FadeUntil(-20, duration(1.5))
        )
    )
    complex_formation_behavior.apply(sprite_list, tag="complex_behavior")
    
    # Verify proper action management
    simple_actions = Action.get_actions_for_target(sprite_list, "simple_movement")
    complex_actions = Action.get_actions_for_target(sprite_list, "complex_behavior")
    
    assert len(simple_actions) == 1  # Single helper function action
    assert len(complex_actions) == 1  # Single sequence action
```

### Pattern 6: Movement Pattern Testing

Tests movement pattern functions with proper composition:

```python
def test_movement_patterns_proper_usage(self):
    """Test movement pattern functions with proper usage patterns."""
    from actions.pattern import (
        create_zigzag_pattern, create_wave_pattern, create_spiral_pattern,
        time_elapsed, sprite_count
    )
    
    sprite = create_test_sprite()
    
    # Movement patterns return sequence actions that should be applied
    zigzag = create_zigzag_pattern(width=100, height=50, speed=150, segments=4)
    assert hasattr(zigzag, 'apply')
    zigzag.apply(sprite, tag="zigzag")
    
    # Verify pattern is applied as a single sequence
    zigzag_actions = Action.get_actions_for_target(sprite, "zigzag")
    assert len(zigzag_actions) == 1
    
    # Test wave pattern
    Action.clear_all()
    wave = create_wave_pattern(amplitude=30, frequency=2, length=400, speed=120)
    wave.apply(sprite, tag="wave")
    
    # Update to start path following
    Action.update_all(0.016)
    initial_pos = (sprite.center_x, sprite.center_y)
    
    Action.update_all(0.5)  # Half second update
    assert sprite.center_x != initial_pos[0] or sprite.center_y != initial_pos[1]
    
    # Test condition helpers
    sprite_list = create_test_sprite_list(5)
    
    # Test time_elapsed condition
    time_condition = time_elapsed(1.0)
    assert not time_condition()  # Should be False initially
    
    # Test sprite_count condition  
    count_condition = sprite_count(sprite_list, 3, "<=")
    assert not count_condition()  # 5 sprites > 3
    
    # Remove sprites to trigger condition
    sprite_list.pop()
    sprite_list.pop()
    sprite_list.pop()  # Now 2 sprites <= 3
    assert count_condition()
```

### Pattern 7: Boundary Action Testing

Tests boundary detection with proper callback integration:

```python
def test_boundary_actions_with_proper_callbacks(self):
    """Test boundary actions with callback integration."""
    from actions import move_until
    from actions.conditional import duration
    
    sprite = create_test_sprite()
    sprite.center_x = 750  # Near right boundary
    
    boundary_hits = []
    
    def on_boundary_hit(hitting_sprite, axis):
        boundary_hits.append((hitting_sprite, axis))
    
    # Create movement with boundary detection using helper function
    bounds = (0, 0, 800, 600)  # left, bottom, right, top
    move_until(
        sprite,
        (100, 0), 
        lambda: False,  # Move indefinitely
        bounds=bounds,
        boundary_behavior="bounce",
        on_boundary=on_boundary_hit,
        tag="boundary_test"
    )
    
    # Move to trigger boundary
    for _ in range(10):
        Action.update_all(0.1)
        sprite.update()  # Apply velocity to position
        if boundary_hits:
            break
    
    assert len(boundary_hits) > 0
    assert boundary_hits[0][1] == 'x'  # Hit x-axis boundary
```

## Test Utilities and Fixtures

### Common Test Fixtures

```python
def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite

def create_test_sprite_list(count=5) -> arcade.SpriteList:
    """Create a SpriteList with test sprites."""
    sprite_list = arcade.SpriteList()
    for i in range(count):
        sprite = create_test_sprite()
        sprite.center_x = 100 + i * 50
        sprite_list.append(sprite)
    return sprite_list
```

### Test Cleanup Pattern

All test classes use consistent cleanup:

```python
class TestActionType:
    """Test suite for specific action type."""
    
    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()
```

## Testing Anti-Patterns to Avoid

### ❌ Don't Use Unnecessary Mocks

Following [[memory:6042457797249309622]], avoid mocking when real objects work:

```python
# BAD: Unnecessary mocking
@patch('arcade.Sprite')
def test_with_mock(self, mock_sprite):
    pass

# GOOD: Use real sprites
def test_with_real_sprite(self):
    sprite = create_test_sprite()
```

### ❌ Don't Test Implementation Details

Test behavior, not internal state:

```python
# BAD: Testing internals
assert action._internal_counter == 5

# GOOD: Testing behavior
assert action.is_complete
assert sprite.center_x == expected_position
```

### ❌ Don't Use Manual Action Tracking

Use global action management:

```python
# BAD: Manual tracking
my_actions = []
action = MoveUntil((100, 0), condition)
my_actions.append(action)

# GOOD: Global management
action = MoveUntil((100, 0), condition)
action.apply(sprite, tag="movement")
Action.update_all(delta_time)
```

## Integration Testing Patterns

### Complete Workflow Tests

Test full game scenarios with multiple systems:

```python
def test_complete_game_scenario_workflow(self):
    """Test complete game scenario with formations, patterns, and actions."""
    from actions.formation import arrange_grid
    from actions.pattern import create_zigzag_pattern
    from actions.conditional import DelayUntil, MoveUntil, FadeUntil, duration
    from actions.composite import sequence, parallel
    from actions import move_until
    
    # Create enemy formation
    sprite_list = create_test_sprite_list(8)
    
    # Apply formation pattern
    arrange_grid(sprite_list, rows=2, cols=4, start_x=100, start_y=500, spacing_x=80, spacing_y=60)
    
    # ✅ CORRECT: Use helper functions for simple group movement
    move_until(sprite_list, (0, -50), duration(2.0), tag="initial_movement")
    
    # ✅ CORRECT: Use direct classes for complex sequences
    complex_behavior = sequence(
        DelayUntil(duration(1.0)),
        MoveUntil((50, -25), duration(2.0)),
        parallel(
            MoveUntil((0, -50), duration(1.0)),
            FadeUntil(-20, duration(1.5))
        )
    )
    complex_behavior.apply(sprite_list, tag="complex_behavior")
    
    # Create movement patterns for individual sprites
    zigzag_pattern = create_zigzag_pattern(width=100, height=50, speed=150, segments=4)
    zigzag_pattern.apply(sprite_list[0], tag="zigzag_leader")
    
    # Verify all systems work together
    assert len(sprite_list) == 8
    
    # Check action registration
    initial_actions = Action.get_actions_for_target(sprite_list, "initial_movement")
    complex_actions = Action.get_actions_for_target(sprite_list, "complex_behavior")
    zigzag_actions = Action.get_actions_for_target(sprite_list[0], "zigzag_leader")
    
    assert len(initial_actions) == 1
    assert len(complex_actions) == 1
    assert len(zigzag_actions) == 1
    
    # Test updates
    Action.update_all(0.1)
    
    # Verify actions are running
    assert len(Action._active_actions) >= 3
```

### Easing Integration Tests

Test easing effects with various action types:

```python
def test_easing_integration_workflow(self):
    """Test easing integration with different action types."""
    from actions import ease, move_until, rotate_until, follow_path_until
    from actions.conditional import duration
    from arcade import easing
    
    sprite = create_test_sprite()
    
    # Test easing with movement
    move_action = move_until(sprite, (200, 0), duration(3.0), tag="move")
    ease(sprite, move_action, seconds=2.0, ease_function=easing.ease_in_out, tag="ease_move")
    
    # Test easing with rotation
    rotate_action = rotate_until(sprite, 360, duration(2.0), tag="rotate")
    ease(sprite, rotate_action, seconds=1.5, ease_function=easing.ease_in, tag="ease_rotate")
    
    # Test easing with path following
    path_points = [(100, 100), (200, 200), (300, 100)]
    path_action = follow_path_until(
        sprite, path_points, 150, duration(4.0),
        rotate_with_path=True, tag="path"
    )
    ease(sprite, path_action, seconds=2.0, ease_function=easing.ease_out, tag="ease_path")
    
    # Verify all easing actions are registered
    move_actions = Action.get_actions_for_target(sprite, "ease_move")
    rotate_actions = Action.get_actions_for_target(sprite, "ease_rotate")
    path_actions = Action.get_actions_for_target(sprite, "ease_path")
    
    assert len(move_actions) == 1
    assert len(rotate_actions) == 1
    assert len(path_actions) == 1
    
    # Test concurrent easing effects
    initial_pos = (sprite.center_x, sprite.center_y)
    initial_angle = sprite.angle
    
    Action.update_all(0.1)
    
    # Verify effects are applied
    assert sprite.center_x != initial_pos[0] or sprite.center_y != initial_pos[1]
    assert sprite.angle != initial_angle
```

## Performance Testing Guidelines

### Action Update Performance

Test that global action management scales properly:

```python
def test_large_action_count_performance(self):
    """Test performance with many active actions."""
    import time
    from actions.conditional import MoveUntil, duration
    
    # Create many sprites with actions
    sprites = [create_test_sprite() for _ in range(100)]
    
    for i, sprite in enumerate(sprites):
        action = MoveUntil((10, 5), duration(10.0))
        action.apply(sprite, tag=f"sprite_{i}")
    
    # Time global update
    start_time = time.time()
    for _ in range(100):
        Action.update_all(0.016)  # 60 FPS
    end_time = time.time()
    
    # Should complete quickly even with many actions
    assert (end_time - start_time) < 1.0
    assert len(Action._active_actions) == 100

def test_sequence_performance(self):
    """Test performance with complex sequence compositions."""
    import time
    from actions.conditional import DelayUntil, MoveUntil, RotateUntil, duration
    from actions.composite import sequence, parallel
    
    sprites = [create_test_sprite() for _ in range(20)]
    
    # Create complex sequences for each sprite
    for i, sprite in enumerate(sprites):
        complex_sequence = sequence(
            DelayUntil(duration(0.1)),
            parallel(
                MoveUntil((50, 25), duration(2.0)),
                RotateUntil(180, duration(1.5))
            ),
            MoveUntil((-25, -25), duration(1.0))
        )
        complex_sequence.apply(sprite, tag=f"complex_{i}")
    
    # Time updates with complex sequences
    start_time = time.time()
    for _ in range(60):  # 1 second at 60 FPS
        Action.update_all(0.016)
    end_time = time.time()
    
    # Should handle complex sequences efficiently
    assert (end_time - start_time) < 2.0
    assert len(Action._active_actions) == 20  # One sequence per sprite

def test_memory_cleanup_performance(self):
    """Test that completed actions are properly cleaned up."""
    from actions.conditional import MoveUntil, duration
    
    sprite = create_test_sprite()
    
    # Create many short-lived actions
    for i in range(50):
        action = MoveUntil((10, 0), duration(0.1))  # Very short duration
        action.apply(sprite, tag=f"short_{i}")
    
    initial_count = len(Action._active_actions)
    assert initial_count == 50
    
    # Run until all actions complete
    for _ in range(100):  # Should be enough time
        Action.update_all(0.016)
        if len(Action._active_actions) == 0:
            break
    
    # Verify cleanup
    assert len(Action._active_actions) == 0
```

## Coverage Requirements

### Minimum Coverage Targets

- **Core Actions**: 100% line coverage for base Action class
- **Conditional Actions**: 95% coverage including edge cases
- **Composite Actions**: 100% coverage for composition functions
- **Formation functions**: 90% coverage including positioning and layout
- **Movement pattern functions**: 85% coverage including pattern creation and condition helpers
- **Boundary Actions**: 85% coverage including callback scenarios

### Critical Test Cases

1. **Action Lifecycle**: Apply, update, complete, cleanup
2. **Global Management**: Multiple actions, tagging, stopping
3. **Proper Usage Patterns**: Helper functions vs. direct classes
4. **Conditional Logic**: Condition evaluation, completion callbacks
5. **Sequence Composition**: Complex nested sequences and parallel actions
6. **Path Following**: Automatic rotation and path completion
7. **Boundary Detection**: Bounce/wrap behaviors and callbacks
8. **Formation Management**: Grid, diamond, circle arrangements
9. **Movement Patterns**: Zigzag, wave, spiral pattern creation
10. **Easing Integration**: Smooth acceleration/deceleration effects
11. **Error Handling**: Invalid conditions, empty sprite lists
12. **Memory Management**: No action leaks, proper cleanup

### Edge Case Testing

Important edge cases to test:

```python
def test_edge_cases(self):
    """Test important edge cases and error conditions."""
    from actions import move_until
    from actions.conditional import duration, MoveUntil
    from actions.composite import sequence
    
    sprite = create_test_sprite()
    
    # Test with empty sprite list
    empty_list = arcade.SpriteList()
    move_until(empty_list, (5, 0), duration(1.0), tag="empty")
    
    # Should not crash
    Action.update_all(0.1)
    
    # Test with very short durations
    move_until(sprite, (100, 0), duration(0.001), tag="short")
    
    # Test with zero velocity
    move_until(sprite, (0, 0), duration(1.0), tag="zero_velocity")
    
    # Test immediate condition satisfaction
    move_until(sprite, (5, 0), lambda: True, tag="immediate")
    
    # Test with None condition (should run forever)
    action = MoveUntil((5, 0), lambda: False)
    action.apply(sprite, tag="forever")
    
    # Update and verify
    Action.update_all(0.1)
    
    # Test empty sequence
    empty_seq = sequence()
    empty_seq.apply(sprite, tag="empty_sequence")
    
    # Should complete immediately
    Action.update_all(0.001)
    empty_actions = Action.get_actions_for_target(sprite, "empty_sequence")
    assert len(empty_actions) == 0  # Should be completed and removed

def test_error_conditions(self):
    """Test error handling and recovery."""
    from actions import move_until
    from actions.conditional import duration
    
    sprite = create_test_sprite()
    
    # Test with invalid bounds
    try:
        move_until(
            sprite, (5, 0), duration(1.0),
            bounds=(800, 600, 0, 0),  # Invalid: left > right, top > bottom
            boundary_behavior="bounce",
            tag="invalid_bounds"
        )
        Action.update_all(0.1)
        # Should handle gracefully
    except Exception as e:
        # Log but don't fail test if error handling is implemented
        print(f"Bounds error handled: {e}")
    
    # Test with invalid velocity values
    move_until(sprite, (float('inf'), 0), duration(1.0), tag="inf_velocity")
    move_until(sprite, (float('nan'), 0), duration(1.0), tag="nan_velocity")
    
    # Should not crash the action system
    Action.update_all(0.1)
    
    # Test stopping non-existent actions
    Action.stop_actions_for_target(sprite, "non_existent_tag")
    
    # Test multiple stop calls
    action = move_until(sprite, (5, 0), duration(1.0), tag="multi_stop")
    action.stop()
    action.stop()  # Should not crash
```

## Running Tests

### Test Execution Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file for formation functions
python -m pytest tests/test_formation.py -v

# Run specific test file for movement patterns
python -m pytest tests/test_pattern.py -v

# Run with coverage
python -m pytest tests/ --cov=actions --cov-report=html

# Run performance tests
python -m pytest tests/ -k "performance" -v
```

### Test Environment Setup

```bash
# Install test dependencies
uv add --group dev pytest pytest-cov

# Run in development environment
uv run pytest tests/ -v
```

### Continuous Integration

The test suite should be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run tests
        run: uv run pytest tests/ --cov=actions --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Documentation Standards

Each test should follow documentation standards:

1. **Clear test names** that describe what is being tested
2. **Docstrings** explaining the test purpose and any complex setup
3. **Comments** for non-obvious assertions or test logic
4. **Pattern examples** showing correct vs. incorrect usage
5. **Edge case coverage** with explanations of why they matter

### Best Practices Summary

1. **Test behavior, not implementation** - Focus on what actions do, not how they do it
2. **Use real sprites and sprite lists** - Avoid unnecessary mocking
3. **Demonstrate correct patterns** - Show proper usage of helpers vs. direct classes
4. **Test edge cases** - Empty lists, zero values, immediate conditions
5. **Verify cleanup** - Ensure no action leaks or memory issues
6. **Performance awareness** - Test that the system scales properly
7. **Clear documentation** - Make tests serve as usage examples

### Testing Checklist

Before submitting code, ensure:

- [ ] All new functionality has corresponding tests
- [ ] Tests demonstrate proper usage patterns (helpers vs. direct classes)
- [ ] Edge cases and error conditions are covered
- [ ] Performance implications are tested
- [ ] Memory cleanup is verified
- [ ] Integration scenarios are tested
- [ ] Documentation examples match test patterns
- [ ] No unnecessary mocks are used
- [ ] Test names clearly describe what is being tested
- [ ] Global action cleanup is performed in teardown

The testing suite provides comprehensive validation of the ArcadeActions library while demonstrating best practices for using the conditional action system in real game scenarios. The tests serve as both validation and documentation, showing developers the correct patterns for different use cases. 