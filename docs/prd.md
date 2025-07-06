# 📄 ArcadeActions Extension Library Requirements Document

---

## ✅ Project Overview

The goal is to create a robust, **conditional Actions system for the Arcade 3.x Python library**, inspired by Cocos2D's action system but reimagined to fit Arcade's API.

This system enables complex sprite behaviors (movement, rotation, scaling, fading, scheduling) in games like Space Invaders, Galaga, and Asteroids — all using high-level declarative **condition-based actions** that work directly with Arcade's native sprites.

---

## 📦 What's Included (Features)

| Module / Feature      | Why It's Included                                                    |
|------------------------|---------------------------------------------------------------------|
| `base.py`             | Core `Action` class with global action management and composition helpers |
| `conditional.py`      | Condition-based actions (MoveUntil, RotateUntil, etc.) |
| `composite.py`        | Composite actions for combining multiple actions (sequential, parallel) |
| `conditional.py`      | Includes boundary handling in `MoveUntil` for arcade-style patterns |
| `pattern.py`          | Formation functions for positioning and layout patterns |
| `easing.py`           | Easing wrapper for smooth acceleration/deceleration effects on any action |
| `helpers.py`          | Convenience wrappers for actions, e.g., `move_until()` |
| Global Action Management | Automatic action tracking, updates, and lifecycle management |
| Test Suite            | Pytest-based unit and integration tests to validate core and edge behavior |
| Operator Overloading  | `+` for sequence and `|` for parallel composition |

## 🔄 Property Update System

The Actions library uses **direct property updates** with Arcade's native sprite system:

### Direct Property Updates
All actions work by directly modifying sprite properties:
- **Position** - Updated via `center_x`, `center_y` 
- **Angle** - Updated via `angle` property
- **Scale** - Updated via `scale` property (supports both float and tuple)
- **Alpha** - Updated via `alpha` property

Actions calculate velocity-based changes and apply them directly:
1. Actions calculate position/angle/scale/alpha changes based on velocity and delta_time
2. Actions apply changes directly to sprite properties
3. Actions check conditions each frame to determine completion
4. Global `Action.update_all()` handles all active actions automatically

### Condition-Based Paradigm
Unlike duration-based actions, ArcadeActions uses **condition-based actions**:
- **MoveUntil** - Move until condition is met
- **RotateUntil** - Rotate until condition is met
- **FadeUntil** - Fade until condition is met
- **DelayUntil** - Wait until condition is met

This enables more flexible, game-state-driven behaviors.

### Pattern 2: Operator-Based Composition
```python
from actions import move_until, rotate_until, fade_until, infinite

# Clean declarative syntax with operators
# Unbound actions can be created by passing `None` as the target
move = move_until(None, velocity=(100, 0), condition=infinite)
rotate = rotate_until(None, velocity=1.5, condition=infinite)

seq = move + rotate
par = move | rotate
complex_action = delay + (move | fade) + final_action

# Apply the composed action to a target
complex_action.apply(sprite)
```

### Pattern 3: Global Management
```python
# Single update handles all actions
def on_update(self, delta_time):
    Action.update_all(delta_time)
```

---

## 🔍 In-Scope Items

- High-level declarative action API over Arcade 3.x
- Core conditional actions: MoveUntil, FollowPathUntil, RotateUntil, ScaleUntil, FadeUntil
- Path following with automatic sprite rotation for smooth curved movement
- Easing wrapper for smooth acceleration/deceleration effects on any conditional action
- Composite actions (sequential, parallel) with composition helpers
- Boundary actions for arcade-style movement patterns
- Formation functions for positioning and layout patterns
- Global action management system
- Unit and integration test coverage for actions and patterns
- Example patterns for common game behaviors

---

## 🚫 Out-of-Scope Items

- Full-featured physics integration (Pymunk, collisions, impulses)
- Advanced pathfinding or AI (A*)
- Visual editor or GUI tools for creating action sequences
- Multiplayer or networking features
- Custom sprite classes (works with standard arcade.Sprite)
- Manual action tracking systems (uses global management)

---

## ⚙ Tech Stack

| Layer           | Technology                                       |
|-----------------|--------------------------------------------------|
| Core Language   | Python 3.13+                                     |
| Game Engine     | Arcade 3.x                                       |
| Actions Framework | Custom-built `ArcadeActions` library, condition-based paradigm |
| Testing        | Pytest                                            |
| Dependencies   | Minimal; self-contained aside from Arcade |
| Version Control | Git (recommended)                               |
| Build System   | Makefile for common development tasks            |
| Package Management | uv for dependency management                    |

---

## 💥 Why This Matters

This system:

✅ Makes Arcade more high-level and expressive for animation and behavior  
✅ Supports **condition-based behaviors** critical for responsive game logic
✅ Enables rapid prototyping of sophisticated gameplay without low-level frame management
✅ Offers **function-based composition** for clean, declarative behavior sequences
✅ Works seamlessly with Arcade's native sprite system
✅ Provides **global action management** eliminating manual tracking overhead

---

## 🌟 Summary

We are delivering a **modern condition-based Actions system** for Arcade that empowers indie devs to build complex 2D games faster with cleaner, more maintainable code through declarative action composition.

## 🧪 Testing Requirements

### Test Coverage Requirements

1. **Core Action Testing**
   - All conditional action types must have comprehensive test coverage
   - Edge cases must be explicitly tested
   - Boundary conditions must be tested for movement actions
   - Composite actions must be tested for all combinations
   - Global action management must be tested

2. **Property Update Testing**
   - Test direct property updates for position, angle, scale, alpha
   - Verify condition evaluation and action completion
   - Test pause/resume functionality
   - Test global action lifecycle management

3. **Test Categories and Patterns**
   - Individual action tests using direct `action.apply()` calls
   - Group action tests applying actions to `arcade.SpriteList`
   - Composite action tests using composition helpers
   - Formation function tests for positioning patterns
   - Boundary action tests for arcade-style patterns

4. **Documentation Requirements**
   - Each test file must have a clear docstring explaining its purpose
   - Each test class must document the specific action being tested
   - Each test method must explain what aspect is being tested
   - Complex test setups must be documented with comments
   - Test fixtures must be documented with their purpose

5. **Quality Requirements**
   - Tests must be deterministic and repeatable
   - Tests must be independent of each other
   - Tests must clean up after themselves using global action management
   - Tests must be fast and efficient
   - Tests must be maintainable and readable

## 📚 Related Documentation

This PRD provides the architectural foundation. For implementation details, consult:

### Essential Implementation Guides
- **[api_usage_guide.md](api_usage_guide.md)** - **Primary implementation reference**
  - Complete API usage patterns and implementation details
  - Comprehensive examples of conditional actions and composition
  - Formation function usage patterns and best practices

### Specialized Implementation Guides
- **[testing_guide.md](testing_guide.md)** - Testing patterns and best practices

### Documentation Hierarchy
```
PRD.md (this file)           → Architecture & Requirements
├── api_usage_guide.md       → Implementation Patterns (PRIMARY)
├── testing_guide.md         → Testing Patterns & Best Practices
├── testing_guide.md         → Testing Patterns
└── README.md                → Quick Start Guide
```

## 🏗️ Code Quality Standards

### Core Design Principle: Zero Tolerance for Runtime Type Checking

**ZERO TOLERANCE for runtime type/attribute checking** - This includes:
- `hasattr()` for type discrimination
- `getattr()` with defaults for missing attributes
- `isinstance()` for runtime type checking
- EAFP with exception silencing (`except AttributeError: pass`)

**The Real Problem**: Unclear interfaces, not the checking pattern.

**The Solution**: Design interfaces so checking isn't needed through:
1. **Consistent base interfaces** with well-defined contracts
2. **Clear protocols** guaranteeing expected methods/attributes exist
3. **Composition patterns** eliminating optional attributes
4. **Unified interfaces** for similar objects (Action base class)

### Implementation Standards

1. **Global Action Management**: All actions must use the global `Action.update_all()` system
2. **Condition-Based Design**: Actions must be condition-based, not duration-based
3. **Native Sprite Compatibility**: Must work with standard `arcade.Sprite` and `arcade.SpriteList`
4. **Function Composition**: Support `sequence()` and `parallel()` for clean action combination
5. **Tag-Based Organization**: Support tagged action management for complex behaviors
6. **Clean API Design**: Minimize wrapper methods and prefer direct action application

### Key Architectural Decisions

1. **No Custom Sprite Classes**: Works directly with `arcade.Sprite` - no ActionSprite needed
2. **Global Management**: Central `Action` class manages all active actions automatically  
3. **Condition-Based**: Actions run until conditions are met, enabling state-driven behavior
4. **Composition Helpers**: Helper functions create composite actions cleanly
5. **Formation Pattern**: Position sprites in organized layouts without replacing core Arcade classes

---

## 🎯 Core Implementation Patterns

### Pattern 1: Direct Action Application
```python
from actions import infinite, move_until

# Works with any arcade.Sprite or arcade.SpriteList
sprite = arcade.Sprite("image.png")
enemies = arcade.SpriteList()

move_until(sprite, velocity=(100, 0), condition=lambda: sprite.center_x > 700)
move_until(enemies, velocity=(100, 0), condition=infinite)
```

### Pattern 2: Operator-Based Composition
```python
from actions import infinite, move_until, rotate_until, fade_until

# Clean declarative syntax with operators
# Unbound actions can be created by passing `None` as the target
move = move_until(None, velocity=(100, 0), condition=infinite)
rotate = rotate_until(None, velocity=1.5, condition=infinite)

seq = move + rotate
par = move | rotate
complex_action = delay + (move | fade) + final_action

# Apply the composed action to a target
complex_action.apply(sprite)
```

### Pattern 3: Global Management
```python
from actions import Action

# Single update handles all actions
def on_update(self, delta_time):
    Action.update_all(delta_time)
```

### Pattern 4: Formation Functions for Layout
```python
from actions import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)
```

This architecture provides a clean, powerful, and maintainable action system that enhances Arcade without replacing its core functionality.
