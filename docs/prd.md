# 📄 ArcadeActions Framework Requirements Document

---

## ✅ Project Overview

The goal is to create a robust, modern **Actions system for the Arcade 3.x Python library (but separate from it)**, inspired by Cocos2D's action system but reimagined to fit Arcade's physics, sprite, and delta-time-based architecture.

This system enables complex sprite behaviors (movement, rotation, scaling, fading, grouping, scheduling) in games like Space Invaders, Galaga, and Asteroids — all using high-level declarative actions.

---

## 📦 What's Included (Features)

| Module / Feature      | Why It's Included                                                    |
|------------------------|---------------------------------------------------------------------|
| `base.py`             | Core `Action` class hierarchy, `ActionSprite` wrapper to manage per-sprite actions |
| `instant.py`          | Instantaneous actions (e.g., Hide, Show, Place, CallFunc) for sprite state changes |
| `interval.py`         | Time-based actions (e.g., MoveBy, MoveTo, RotateBy, RotateTo, ScaleTo, FadeTo, JumpBy, JumpTo) and action modifiers (Accelerate, AccelDecel) that use real delta-time physics and smooth interpolation |
| `move.py`            | Complex movement actions (`Driver`, `WrappedMove`, `BoundedMove`) for arcade-style patterns |
| `group.py`           | `GroupAction` and `SpriteGroup` to coordinate synchronized sprite groups (e.g., Galaga attack waves) |
| `composite.py`       | Composite actions for combining multiple actions (Sequence, Spawn, Loop) with support for empty composites and immediate completion |
| `game.py`            | Game state management and action scheduling integration |
| `game_clock.py`      | Central game clock that manages time and pause state for the entire game, plus a scheduler for sequencing time-based and conditional events |
| Delta-Time Compliance | All actions consume `delta_time` for frame-independent accuracy |
| Test Suite           | Pytest-based unit and integration tests to validate core and edge behavior |
| Demo Game           | Example Space Invaders / Galaga prototype showcasing actions on player, enemies, bullets |

---

## 🔍 In-Scope Items

- High-level declarative action API over Arcade 3.x
- Core actions: Move, Rotate, Scale, Fade, Jump, Lerp, CallFunc
- Action modifiers: Accelerate and AccelDecel for smooth interpolation of any action
- Group actions and SpriteGroup coordination
- Per-sprite action management (`ActionSprite`)
- Game-wide scheduler for coordinating action timelines
- Delta-time based updates across all interval actions
- Composite actions for complex behavior sequences with support for:
  - Empty composites (completing immediately)
  - Immediate completion handling
  - Proper iteration counting for loops
  - Frame-independent timing
- Game state management and action lifecycle
- Unit and integration test coverage for actions and groups
- Example demo game with:
    - Player movement + shooting
    - Enemy wave patterns using `BoundedMove` / `GroupAction`
    - Bullet cleanup and basic collision system
    - Composite action sequences for complex behaviors
    - Smooth acceleration/deceleration using action modifiers

---

## 🚫 Out-of-Scope Items

- Full-featured physics integration (Pymunk, collisions, impulses)
- Advanced pathfinding or AI (A*)
- Asset management, resource loading (images, sounds)
- Visual editor or GUI tools for creating action sequences
- Multiplayer or networking features
- Detailed particle system or visual effects integration
- Arcade's platformer physics, tilemaps, or other unrelated features

---

## ⚙ Tech Stack

| Layer           | Technology                                       |
|-----------------|--------------------------------------------------|
| Core Language   | Python 3.10+                                     |
| Game Engine     | Arcade 3.x                                       |
| Physics Layer (optional) | Arcade built-in or Pymunk (not tightly coupled) |
| Actions Framework | Custom-built `ArcadeActions` library, Cocos2D-inspired |
| Testing        | Pytest                                            |
| Demo Game      | Arcade View + Window, using `ActionSprite` + Action groups |
| Dependencies   | Minimal; self-contained aside from Arcade and optional Pymunk |
| Version Control | Git (recommended)                               |
| Build System   | Makefile for common development tasks            |
| Package Management | uv for dependency management                    |

---

## 💥 Why This Matters

This system:

✅ Makes Arcade as expressive as Cocos2D for animation and behavior  
✅ Works at **frame-independent precision** via delta-time updates  
✅ Supports **group behaviors** critical for arcade shooters  
✅ Provides **clean separation** between logic, physics, and visuals  
✅ Enables rapid prototyping of sophisticated gameplay without low-level math
✅ Offers **composite actions** for complex behavior sequences with robust edge case handling
✅ Integrates with Arcade's game state management

---

## 🌟 Summary

We are delivering a **modern, extensible, production-ready Actions system** for Arcade that empowers indie devs to build complex 2D games faster, with cleaner and more maintainable code, and with an architecture grounded in real-time delta updates. The system includes comprehensive game state management, composite actions for complex behaviors with proper edge case handling, and a robust testing framework.

## 🧪 Testing Requirements

### Test Coverage Requirements

1. **Core Action Testing**
   - All action types must have comprehensive test coverage
   - Edge cases must be explicitly tested
   - Physics integration must be tested when applicable
   - Boundary conditions must be tested for movement actions
   - Composite actions must be tested for all combinations
   - Action modifiers must be tested with different types of actions

2. **Test Categories**
   - Unit tests for individual actions
   - Integration tests for action combinations
   - Edge case tests for boundary conditions
   - Physics integration tests where applicable
   - Performance tests for critical paths
   - Modifier action tests for different interpolation curves

3. **Documentation Requirements**
   - Each test file must have a clear docstring explaining its purpose
   - Each test class must document the specific action being tested
   - Each test method must explain what aspect is being tested
   - Complex test setups must be documented with comments
   - Test fixtures must be documented with their purpose

4. **Quality Requirements**
   - Tests must be deterministic and repeatable
   - Tests must be independent of each other
   - Tests must clean up after themselves
   - Tests must be fast and efficient
   - Tests must be maintainable and readable

For detailed testing patterns, examples, and best practices, see `docs/testing.md`.

# Test Patterns Guide

## Common Test Patterns

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
    action = ActionClass(params)
    action.target = sprite
    
    # Start
    action.start()
    assert initial_conditions
    
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
    action = ActionClass(duration=0)
    
    # Test boundary conditions
    action = ActionClass(param=boundary_value)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        ActionClass(param=invalid_value)
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
    return arcade.SpriteList()
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
