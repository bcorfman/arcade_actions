# ArcadeActions Testing Guide

## Overview

This guide documents the testing architecture and patterns for the ArcadeActions library. The test suite validates all core functionality using conditional actions, global action management, and function composition patterns.

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

### Test Organization Principles

1. **Each test file maps to one module** - Direct 1:1 relationship with source files
2. **Global action cleanup** - All tests use `Action.clear_all()` in teardown
3. **Real conditional actions** - No mocks for core functionality [[memory:6042457797249309622]]
4. **Function usage** - Tests demonstrate `sequence()` and `parallel()` function patterns
5. **Tag-based organization** - Tests use meaningful tags for action management

## Testing Patterns

### Pattern 1: Individual Action Testing

Tests individual conditional actions with real sprites:

```python
def test_move_until_condition(self):
    """Test MoveUntil with position-based condition."""
    sprite = create_test_sprite()
    
    # Create conditional action
    move_action = MoveUntil((100, 0), lambda: sprite.center_x >= 200)
    
    # Apply and verify registration
    returned_action = move_action.apply(sprite, tag="movement")
    assert returned_action == move_action
    assert move_action in Action._active_actions
    
    # Test updates until condition met
    initial_x = sprite.center_x
    Action.update_all(1.0)  # 1 second update
    
    assert sprite.center_x > initial_x
    assert not move_action.is_complete
    
    # Move to trigger completion
    sprite.center_x = 250
    Action.update_all(0.1)
    
    assert move_action.is_complete
    assert move_action not in Action._active_actions
```

### Pattern 2: Function Composition Testing

Tests the `sequence()` and `parallel()` helper functions:

```python
def test_function_composition(self):
    """Test action composition using helper functions."""
    from actions.composite import sequence, parallel
    
    sprite = create_test_sprite()
    
    # Create individual actions
    move = MoveUntil((50, 0), duration(1.0))
    rotate = RotateUntil(90, duration(0.5))
    fade = FadeUntil(-30, duration(1.5))
    
    # Test composition functions
    seq = sequence(move, rotate)         # Sequential
    par = parallel(move, fade)           # Parallel
    nested = sequence(move, parallel(rotate, fade))  # Nested composition
    
    # Apply and verify
    seq.apply(sprite, tag="sequence")
    par.apply(sprite, tag="parallel")
    nested.apply(sprite, tag="nested")
    
    # Check global action management
    sequence_actions = Action.get_tag_actions("sequence")
    parallel_actions = Action.get_tag_actions("parallel")
    nested_actions = Action.get_tag_actions("nested")
    
    assert len(sequence_actions) == 1
    assert len(parallel_actions) == 1
    assert len(nested_actions) == 1

### Pattern 2b: Path Following with Rotation Testing

Tests FollowPathUntil with automatic sprite rotation functionality:

```python
def test_path_following_with_rotation(self):
    """Test FollowPathUntil with automatic sprite rotation."""
    sprite = create_test_sprite()
    sprite.angle = 45  # Start with non-zero angle
    
    # Create curved path
    control_points = [(100, 100), (200, 200), (300, 100)]
    
    # Test without rotation
    no_rotation_action = FollowPathUntil(control_points, 150, duration(2.0))
    no_rotation_action.apply(sprite, tag="no_rotation")
    
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
    rotation_action = FollowPathUntil(
        control_points, 150, duration(2.0),
        rotate_with_path=True
    )
    rotation_action.apply(sprite, tag="with_rotation")
    
    # Update to get movement and rotation
    Action.update_all(0.016)
    Action.update_all(0.016)
    
    # Sprite should now be rotated to face movement direction
    assert sprite.angle != original_angle
    
    # Test with rotation offset for sprite artwork pointing up
    Action.clear_all()
    sprite.center_x = 100  # Reset position
    sprite.center_y = 100
    
    offset_action = FollowPathUntil(
        control_points, 150, duration(2.0),
        rotate_with_path=True,
        rotation_offset=-90.0  # Compensate for upward-pointing artwork
    )
    offset_action.apply(sprite, tag="with_offset")
    
    # Update to get movement and rotation
    Action.update_all(0.016)
    Action.update_all(0.016)
    
    # Verify the rotation includes the offset
    # For horizontal movement (0°), with -90° offset, expect -90°
    expected_angle = -90.0
    assert abs(sprite.angle - expected_angle) < 5.0  # Allow some tolerance
```
```

### Pattern 3: Formation Testing

Tests formation positioning with conditional actions:

```python
def test_formation_conditional_actions(self):
    """Test formation functions with conditional action patterns."""
    from actions.formation import arrange_grid, arrange_diamond
    
    sprite_list = create_test_sprite_list(6)
    
    # Apply formation pattern
    arrange_grid(sprite_list, rows=2, cols=3, start_x=200, start_y=400, spacing_x=60, spacing_y=50)
    
    # Verify positioning
    assert sprite_list[0].center_x == 200
    assert sprite_list[0].center_y == 400
    assert sprite_list[1].center_x == 260  # 200 + 60 spacing
    assert sprite_list[3].center_y == 350  # 400 - 50 spacing
    
    # Test diamond formation with include_center parameter
    diamond_sprites = create_test_sprite_list(5)
    arrange_diamond(diamond_sprites, center_x=300, center_y=200, spacing=40, include_center=True)
    
    # Verify center sprite
    assert diamond_sprites[0].center_x == 300
    assert diamond_sprites[0].center_y == 200
    
    # Verify first layer Manhattan distances
    for sprite in diamond_sprites[1:5]:
        manhattan_dist = abs(sprite.center_x - 300) + abs(sprite.center_y - 200)
        assert abs(manhattan_dist - 40) < 0.1
    
    # Test hollow diamond
    hollow_sprites = create_test_sprite_list(4)
    arrange_diamond(hollow_sprites, center_x=100, center_y=100, spacing=30, include_center=False)
    
    # All sprites should be at layer 1 distance
    for sprite in hollow_sprites:
        manhattan_dist = abs(sprite.center_x - 100) + abs(sprite.center_y - 100)
        assert abs(manhattan_dist - 30) < 0.1
    
    # Create complex action composition
    delay = DelayUntil(duration(1.0))
    move = MoveUntil((50, -25), duration(2.0))
    fade = FadeUntil(-20, duration(1.5))
    
    # Use helper functions for composition
    from actions.composite import sequence, parallel
    
    seq = sequence(delay, move)
    par = parallel(move, fade)
    
    # Apply to group
    seq.apply(sprite_list, tag="sequence_movement")
    par.apply(sprite_list, tag="parallel_effects")
    
    # Verify global action management
    sequence_actions = Action.get_tag_actions("sequence_movement")
    parallel_actions = Action.get_tag_actions("parallel_effects")
    
    assert len(sequence_actions) == 1
    assert len(parallel_actions) == 1

### Pattern 3b: Movement Pattern Testing

Tests movement pattern functions and condition helpers:

```python
def test_movement_pattern_functions(self):
    """Test movement pattern creation and application."""
    from actions.pattern import (
        create_zigzag_pattern, create_wave_pattern, create_spiral_pattern,
        create_figure_eight_pattern, create_orbit_pattern, create_bounce_pattern,
        create_patrol_pattern, time_elapsed, sprite_count
    )
    
    sprite = create_test_sprite()
    
    # Test zigzag pattern creation
    zigzag = create_zigzag_pattern(width=100, height=50, speed=150, segments=4)
    assert hasattr(zigzag, 'apply')
    zigzag.apply(sprite, tag="zigzag")
    
    # Verify pattern is applied
    zigzag_actions = Action.get_tag_actions("zigzag")
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
    
    # Test spiral pattern
    Action.clear_all()
    spiral = create_spiral_pattern(
        center_x=400, center_y=300, max_radius=100, 
        revolutions=2, speed=180, direction="outward"
    )
    spiral.apply(sprite, tag="spiral")
    
    # Test bounce pattern
    Action.clear_all()
    bounce = create_bounce_pattern(
        velocity=(100, 80), bounds=(0, 0, 800, 600)
    )
    bounce.apply(sprite, tag="bounce")
    
    # Test patrol pattern
    Action.clear_all()
    patrol = create_patrol_pattern(
        start_pos=(100, 200), end_pos=(300, 200), speed=120
    )
    patrol.apply(sprite, tag="patrol")
    
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
    
    # Test different comparison operators
    eq_condition = sprite_count(sprite_list, 2, "==")
    assert eq_condition()  # Exactly 2 sprites
    
    gt_condition = sprite_count(sprite_list, 1, ">")
    assert gt_condition()  # 2 sprites > 1
```

### Pattern 4: Conditional Logic Testing

Tests complex conditional behaviors with sprite list management:

```python
def test_conditional_sprite_management(self):
    """Test conditional actions with sprite list management."""
    sprite_list = create_test_sprite_list(5)
    
    # Set up conditional action based on sprite positions
    def move_condition():
        return any(sprite.center_y < 300 for sprite in sprite_list)
    
    # Create conditional movement
    move_action = MoveUntil((0, -50), move_condition)
    move_action.apply(sprite_list, tag="conditional_move")
    
    # Verify action is active
    active_actions = Action.get_tag_actions("conditional_move")
    assert len(active_actions) == 1
    
    # Track condition changes
    condition_met = False
    original_positions = [(s.center_x, s.center_y) for s in sprite_list]
    
    # Trigger condition by updating sprite positions
    for sprite in sprite_list:
        sprite.center_y = 250  # Below threshold
    
    # Update actions until condition is met
    for _ in range(10):
        Action.update_all(0.1)
        if move_condition():
            condition_met = True
            break
    
    # Verify condition was met and action completed
    assert condition_met
    final_actions = Action.get_tag_actions("conditional_move")
    assert len(final_actions) == 0  # Action should be complete
```

### Pattern 5: Boundary Action Testing

Tests boundary detection with callback integration:

```python
def test_move_until_with_boundary_callbacks(self):
    """Test MoveUntil with boundary callbacks."""
    sprite = create_test_sprite()
    sprite.center_x = 750  # Near right boundary
    
    boundary_hits = []
    
    def on_boundary_hit(hitting_sprite, axis):
        boundary_hits.append((hitting_sprite, axis))
    
    # Create movement with boundary detection
    bounds = (0, 0, 800, 600)  # left, bottom, right, top
    move_action = MoveUntil(
        (100, 0), 
        lambda: False,  # Move indefinitely
        bounds=bounds,
        boundary_behavior="bounce",
        on_boundary=on_boundary_hit
    )
    
    # Apply and test
    move_action.apply(sprite, tag="boundary_test")
    
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
def test_complete_formation_workflow(self):
    """Test complete formation workflow with patterns and actions."""
    # Create formation
    sprite_list = create_test_sprite_list(8)
    # Use sprite_list directly for formation management
    
    # Apply formation pattern
    grid_pattern = GridPattern(rows=2, cols=4, spacing_x=80, spacing_y=60)
    grid_pattern.apply(formation, start_x=100, start_y=500)
    
    # Create complex behavior sequence
    phase1 = DelayUntil(duration(1.0))
    phase2 = MoveUntil((0, -50), duration(2.0))
    phase3 = (MoveUntil((100, 0), duration(1.0)) | 
              FadeUntil(-25, duration(1.5)))
    
    # Compose with helper functions
    from actions.composite import sequence
    
    full_sequence = sequence(phase1, phase2, phase3)
    formation.apply(full_sequence, tag="complete_behavior")
    
    # Set up conditional breakaway
    def low_health_condition():
        return formation.sprite_count <= 3
    
    breakaway_sprites = [sprite_list[0], sprite_list[1]]
    formation.setup_conditional_breakaway(
        low_health_condition, breakaway_sprites, tag="breakaway"
    )
    
    # Verify all systems work together
    assert formation.sprite_count == 8
    complete_actions = Action.get_tag_actions("complete_behavior")
    breakaway_actions = Action.get_tag_actions("breakaway")
    
    assert len(complete_actions) == 1
    assert len(breakaway_actions) == 1
```

## Performance Testing Guidelines

### Action Update Performance

Test that global action management scales properly:

```python
def test_large_action_count_performance(self):
    """Test performance with many active actions."""
    import time
    
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
3. **Function Composition**: All composition function combinations
4. **Conditional Logic**: Condition evaluation, completion callbacks
5. **Error Handling**: Invalid conditions, empty sprite lists
6. **Memory Management**: No action leaks, proper cleanup

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

The testing suite provides comprehensive validation of the ArcadeActions library while demonstrating best practices for using the conditional action system in real game scenarios. 