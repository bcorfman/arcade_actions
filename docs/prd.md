# 📄 ArcadeActions Extension Library Requirements Document

---

## ✅ Project Overview

The goal is to create a robust, modern **Actions system for the Arcade 3.x Python library**, inspired by Cocos2D's action system but reimagined to fit Arcade's physics, sprite, and delta-time-based architecture.

This system enables complex sprite behaviors (movement, rotation, scaling, fading, grouping, scheduling) in games like Space Invaders, Galaga, and Asteroids — all using high-level declarative actions.

---

## 📦 What's Included (Features)

| Module / Feature      | Why It's Included                                                    |
|------------------------|---------------------------------------------------------------------|
| `base.py`             | Core `Action` class with global action management and operator overloads |
| `conditional.py`      | Condition-based actions (MoveUntil, RotateUntil, etc.) |
| `composite.py`        | Composite actions for combining multiple actions (sequential, parallel) |
| `conditional.py`      | Includes boundary handling in `MoveUntil` for arcade-style patterns |
| `pattern.py`          | Formation functions for positioning and layout patterns |
| Global Action Management | Automatic action tracking, updates, and lifecycle management |
| Test Suite            | Pytest-based unit and integration tests to validate core and edge behavior |
| Operator Composition  | `+` for sequential, `|` for parallel, enabling clean declarative syntax |

## 🔄 Property Update System

The Actions library handles two distinct property update systems:

### 1. ActionSprite Properties
Properties managed by the Actions system through `ActionSprite`:
- Position (direct updates in `update()`)
- Angle (direct updates in `update()`)
- Scale (direct updates in `update()`)
- Alpha (direct updates in `update()`)
- Custom properties

These properties are updated by:
1. Actions calculate changes in `start()`
2. Actions apply changes directly in `update()` using:
   - Elapsed time tracking
   - Rate-based interpolation
   - Proper pause state handling
3. Actions ensure clean completion in `stop()`

Note: `ActionSprite` is designed to manage only one action at a time. To achieve multiple behaviors simultaneously, use composite actions:
- `Spawn` (|) for parallel actions
- `Sequence` (+) for sequential actions
- `Repeat` (*) for repeating actions
- `Loop` for finite repetitions

This design choice simplifies the action management system and makes the behavior more predictable. When a new action is started, any existing action is automatically stopped.

### 2. Arcade Sprite Properties
Properties managed by Arcade's standard sprite system:
- Position (via `change_x`, `change_y`)
- Angle (via `change_angle`)
- Physics properties (via Pymunk integration)

These properties are updated by:
1. Arcade's sprite update system
2. Velocity-based movement
3. Physics integration

### Clear Separation of Concerns
- `ActionSprite` is the only class that can use Actions
- Regular `arcade.Sprite` uses Arcade's standard velocity system
- No mixing of the two systems on the same sprite
- Explicit documentation that Actions only work with `ActionSprite`

### Time Management
All property updates are managed through the `GameClock` system:
- Delta-time based updates for frame independence
- Proper pause state handling
- Consistent timing across all action types
- Support for action modifiers (Easing)

---

## 🔍 In-Scope Items

- High-level declarative action API over Arcade 3.x
- Core conditional actions: MoveUntil, RotateUntil, ScaleUntil, FadeUntil
- Composite actions (sequential, parallel) with operator overloads
- Boundary actions for arcade-style movement patterns
- Formation functions for positioning and layout patterns
- Global action management system
- Unit and integration test coverage for actions and patterns
- Example patterns for common game behaviors

---

## 🚫 Out-of-Scope Items

- Full-featured physics integration (Pymunk, collisions, impulses)
- Advanced pathfinding or AI (A*)
- Asset management, resource loading (images, sounds)
- Visual editor or GUI tools for creating action sequences
- Multiplayer or networking features
- Detailed particle system or visual effects integration
- Arcade's platformer physics, tilemaps, or other unrelated features
- Actions for regular `arcade.Sprite` instances

---

## ⚙ Tech Stack

| Layer           | Technology                                       |
|-----------------|--------------------------------------------------|
| Core Language   | Python 3.10+                                     |
| Game Engine     | Arcade 3.x                                       |
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
✅ Maintains clear boundaries between Action and Arcade sprite systems

---

## 🌟 Summary

We are delivering a **modern, extensible, production-ready Actions system** for Arcade that empowers indie devs to build complex 2D games faster, with cleaner and more maintainable code, and with an architecture grounded in real-time delta updates. The system includes comprehensive game state management, composite actions for complex behaviors with proper edge case handling, and a robust testing framework.

## 🧪 Testing Requirements

### Test Coverage Requirements

1. **Core Action Testing**
   - All action types must have comprehensive test coverage
   - Edge cases must be explicitly tested
   - Boundary conditions must be tested for movement actions
   - Composite actions must be tested for all combinations
   - Action modifiers must be tested with different types of actions

2. **Property Update Testing**
   - Test direct property updates for position, angle, scale, alpha
   - Verify condition evaluation and action completion
   - Test pause/resume functionality
   - Test global action lifecycle management

3. **Test Categories and Patterns**
   - Individual action tests using direct `action.apply()` calls
   - Group action tests applying actions to `arcade.SpriteList`
   - Composite action tests using operator overloads
   - Formation function tests for positioning patterns
   - Boundary action tests for arcade-style patterns

4. **Documentation Requirements**
   - Each test file must have a clear docstring explaining its purpose
   - Each test class must document the specific action being tested
   - Each test method must explain what aspect is being tested
   - Complex test setups must be documented with comments
   - Test fixtures must be documented with their purpose
   - Property update type must be clearly documented

5. **Quality Requirements**
   - Tests must be deterministic and repeatable
   - Tests must be independent of each other
   - Tests must clean up after themselves
   - Tests must be fast and efficient
   - Tests must be maintainable and readable
   - Tests must verify both immediate and time-based updates

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
1. **Consistent base interfaces** with default values
2. **Clear protocols** guaranteeing expected methods/attributes  
3. **Composition patterns** eliminating optional attributes
4. **Unified interfaces** for similar objects (Action base class)

### Implementation Standards

1. **Global Action Management**: All actions must use the global `Action.update_all()` system
2. **Condition-Based Design**: Actions must be condition-based, not duration-based
3. **Native Sprite Compatibility**: Must work with standard `arcade.Sprite` and `arcade.SpriteList`
4. **Operator Composition**: Support `+` for sequential and `|` for parallel operations
5. **Tag-Based Organization**: Support tagged action management for complex behaviors
6. **Clean API Design**: Minimize wrapper methods and prefer direct action application

### Key Architectural Decisions

1. **No Custom Sprite Classes**: Works directly with `arcade.Sprite` - no ActionSprite needed
2. **Global Management**: Central `Action` class manages all active actions automatically  
3. **Condition-Based**: Actions run until conditions are met, enabling state-driven behavior
4. **Operator Overloads**: Mathematical operators create composite actions cleanly
5. **Formation Pattern**: Position sprites in organized layouts without replacing core Arcade classes

---

## 🎯 Core Implementation Patterns

### Pattern 1: Direct Action Application
```python
# ✅ Acceptable - genuine fallback logic
try:
    return expensive_operation()
except ResourceNotAvailable:
    return cached_result()

# ❌ Forbidden - error silencing
try:
    obj.method()
except AttributeError:
    pass  # This is a code smell
```

### Pattern 2: Operator Composition
```python
# Clean declarative syntax
sequence = delay + move + fade
parallel = move | rotate | scale
complex = delay + (move | fade) + final_action
```

### Pattern 3: Global Management
```python
# Single update handles all actions
def on_update(self, delta_time):
    Action.update_all(delta_time)
```

### Pattern 4: Formation Functions for Layout
```python
from actions.pattern import arrange_grid
arrange_grid(enemies, rows=3, cols=5, start_x=100, start_y=400)
pattern.apply(enemies, tag="attack")
```

This architecture provides a clean, powerful, and maintainable action system that enhances Arcade without replacing its core functionality.
