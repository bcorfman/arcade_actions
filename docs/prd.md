# 📄 ArcadeActions Extension Library Requirements Document

---

## ✅ Project Overview

The goal is to create a robust, conditional **Actions system for the Arcade 3.x Python library**, inspired by Cocos2D's action system but reimagined to fit Arcade's API.

This system enables complex sprite behaviors (movement, rotation, scaling, fading, grouping, scheduling) in games like Space Invaders, Galaga, and Asteroids — all using high-level declarative actions.

---

## 📦 What's Included (Features)

| Module / Feature      | Why It's Included                                                    |
|------------------------|---------------------------------------------------------------------|
| `base.py`             | Core `Action` class hierarchy |
| `composite.py`        | Composite actions for combining multiple actions (Sequence, Spawn) |
| `conditional.py`      | Composite actions for combining multiple actions (Sequence, Spawn) |
| `group.py`            | `GroupAction` and `SpriteGroup` to coordinate synchronized sprite groups with automatic management (e.g., Space Invaders formations, Galaga attack waves) |
| `move.py`             | Complex movement actions (`WrappedMove`, `BoundedMove`) for arcade-style patterns |
| Delta-Time Compliance | All actions consume `delta_time` for frame-independent accuracy |
| Test Suite            | Pytest-based unit and integration tests to validate core and edge behavior |
| Demo Game             | Example Space Invaders prototype showcasing actions on player, enemies, bullets |

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

These properties are updated by:
1. Arcade's sprite update system
2. Velocity-based movement

---

## 🔍 In-Scope Items

- High-level declarative action API over Arcade 3.x
- Core actions: MoveUntil/MoveWhile, RotateUntil/RotateWhile, ScaleUntil/ScaleWhile, FadeUntil/FadeWhile, 
- Group actions
- Composite actions and Patterns for complex behavior sequences
- Game state management and action lifecycle
- Unit and integration test coverage for actions and groups
- Example demo game with:

---

## 🚫 Out-of-Scope Items

- Full-featured physics integration (Pymunk, collisions, impulses)
- Advanced pathfinding or AI (A*)
- Visual editor or GUI tools for creating action sequences
- Multiplayer or networking features
- Arcade's platformer physics, tilemaps, or other unrelated features

---

## ⚙ Tech Stack

| Layer           | Technology                                       |
|-----------------|--------------------------------------------------|
| Core Language   | Python 3.13+                                     |
| Game Engine     | Arcade 3.x                                       |
| Actions Framework | Custom-built `ArcadeActions` library, loosely Cocos2D-inspired |
| Testing        | Pytest                                            |
| Demo Game      | Slime Invaders example from Arcade, rebuilt with Actions |
| Dependencies   | Minimal; self-contained aside from Arcade |
| Version Control | Git (recommended)                               |
| Build System   | Makefile for common development tasks            |
| Package Management | uv for dependency management                    |

---

## 💥 Why This Matters

This system:

✅ Makes Arcade more high-level and expressive for animation and behavior  
✅ Supports **group behaviors** critical for arcade shooters  
✅ Enables rapid prototyping of sophisticated gameplay without low-level math
✅ Offers **composite actions** for complex behavior sequences with robust edge case handling
✅ Integrates with Arcade's game state management

---

## 🌟 Summary

We are delivering a **modern and extensible Actions system** for Arcade that empowers indie devs to build complex 2D games faster and with cleaner and more maintainable code, along with a robust testing framework.

## 🧪 Testing Requirements

### Test Coverage Requirements

1. **Core Action Testing**
   - All action types must have comprehensive test coverage
   - Edge cases must be explicitly tested
   - Boundary conditions must be tested for movement actions
   - Composite actions must be tested for all combinations
   - Action modifiers must be tested with different types of actions

2. **Property Update Testing**
   - **Arcade Sprite Properties**
     - Test velocity/force calculations in `start()`
     - Verify Arcade's update system applies changes correctly
     - Test pause state handling
     - Test boundary conditions

3. **Test Categories and Mock Usage**
   See `testing.md` for detailed test categories, patterns, and when to use mocks vs real implementations.

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
  - For all component usage patterns and implementation details
  - The definitive guide for ActionSprite vs arcade.Sprite decisions
  - Complete API examples and best practices

### Testing Documentation
- **[testing_index.md](testing_index.md)** - Central testing hub
  - Navigation to all testing documentation
  - Links to component-specific testing patterns
  - Comprehensive testing guide and fixtures reference

### Specialized Implementation Guides
- **[boundary_event.md](boundary_event.md)** - BoundedMove callback patterns
- **[game_loop_updates.md](game_loop_updates.md)** - Game integration patterns

### Documentation Hierarchy
```
PRD.md (this file)           → Architecture & Requirements
├── api_usage_guide.md       → Implementation Patterns (PRIMARY)
├── testing_index.md         → Testing Hub
│   ├── testing.md           → Core Testing Patterns
│   └── testing_movement.md  → Movement Testing
├── boundary_event.md        → Boundary Patterns
└── game_loop_updates.md     → Game Integration
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
2. **Clear protocols** where needed, guaranteeing expected methods/attributes  
3. **Composition patterns** eliminating optional attributes
4. **Unified interfaces** for similar objects 

### Exception: Genuine Decision Points

EAFP is acceptable ONLY for genuine decision points with real fallback logic:

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

### Interface Design Requirements

1. **Type Safety**
   - Use type hints on all public interfaces
   - Define protocols for duck-typed behavior
   - Prefer composition over inheritance for complex behaviors
   - Use Union types for multiple type support

2. **Consistency**
   - All similar objects must have the same interface
   - Required methods/attributes must be guaranteed by design
   - Optional behavior must be handled through composition, not checking

3. **Clarity**
   - Interface contracts must be clear from type signatures
   - No surprise missing attributes or methods
   - Predictable behavior without runtime inspection

### Legacy Code Migration

When refactoring existing code with excessive runtime checking:
1. Identify the root cause (unclear interfaces)
2. Design consistent interfaces for all involved types
3. Use protocols to formalize duck-typed behavior
4. Eliminate optional attributes through composition
5. Replace checking with proper interface design

### Examples in Codebase

For concrete examples of these principles in action, see:
- `actions/move.py` - BoundedMove and WrappedMove class refactoring
