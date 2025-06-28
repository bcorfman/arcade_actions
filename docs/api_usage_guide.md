# ArcadeActions API Usage Guide

## Overview

This guide provides clear guidance on when and how to use the different components of the ArcadeActions framework. Understanding these patterns is crucial for building effective games and demos.

## Core Components



## Usage Patterns

### Pattern 1: Individual Sprite Control
**Use case:** Player character, single enemies, UI elements.


### Pattern 2: Group Coordination
**Use case:** Enemy formations, bullet patterns, particle effects.


### Pattern 3: Boundary Interactions with Groups
**Use case:** Space Invaders-style movement, bouncing formations.

**IMPORTANT:** The boundary system is designed to be SIMPLE. Do not over-engineer it with complex state management, frame tracking, or multi-collision handling. Follow these core principles:

- **Actions move sprites with Arcade's velocity (change_x/change_y) values**
- **Only check boundaries in current movement direction** (left-moving group only checks left boundary)
- **Only edge sprites trigger callbacks** (leftmost when moving left, rightmost when moving right)
- **One callback per axis per frame maximum** to prevent duplicate events

**How Boundary Detection Works (Keep This Simple!):**

**Do NOT add:**

### Pattern 4: Collision Detection with Groups
**Use case:** Bullet vs enemy collisions, player vs powerup collisions.



## Critical Timing Patterns

### Pattern 6: Collision Detection Update Order
**Critical principle:** Always check collisions BEFORE updating sprite positions to prevent multiple hits per frame.

**The Problem:** When collision detection happens after sprite updates, bullets can hit multiple enemies in the same frame because `remove_from_sprite_lists()` doesn't take effect immediately.


### Pattern 7: Complete Game Loop Structure
**Best practice:** Follow this update order for all collision-based games.


**Key Points:**
- **Collision detection must happen before sprite movement**
- **This applies to ALL games with collision-based sprite removal**
- **Order matters more than performance optimizations**
- **One frame delay is better than multiple hits**

## Decision Matrix

| Scenario | Use | Reason |
|----------|-----|--------|
| Complex sequences | Composite actions (`+`, `|`, `*`) | Declarative behavior |
| Organize sprites in formations | Formation patterns (`GridPattern`, etc.) | Structured positioning |
| Game-level group management | `AttackGroup` + patterns | Lifecycle + scheduling |

## Common Mistakes to Avoid

## Advanced Group Management


### 6. AttackGroup  
**When to use:** For complex game scenarios requiring lifecycle management, formations, and scheduled events.


## Testing Patterns

### Testing Individual Actions

### Testing Group Actions

### Testing Boundary Interactions

### Testing Wrapping Interactions

### Testing Collision Detection

### Testing AttackGroup and Patterns

## Performance Considerations

## Summary


Follow these patterns and your ArcadeActions code will be clean, efficient, and maintainable!

## Runtime-checking-free patterns


Key conventions:

4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 
