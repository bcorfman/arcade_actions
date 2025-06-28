# ArcadeActions API Usage Guide

## Overview

This guide provides clear guidance on when and how to use the different components of the ArcadeActions framework. Understanding these patterns is crucial for building effective games and demos.

## Core Components

### 1. ActionSprite
**When to use:** For any sprite that needs to perform actions.
**Key principle:** Only `ActionSprite` instances can use the Actions system.

```python
from actions.base import ActionSprite
from actions.interval import MoveBy

# Create an ActionSprite
player = ActionSprite(":resources:images/player.png")
player.center_x = 100
player.center_y = 100

# Apply an action
move_action = MoveBy((200, 0), 2.0)  # Move 200 pixels right over 2 seconds
player.do(move_action)

# Update in game loop
player.update(delta_time)
```

### 2. Individual Actions
**When to use:** For single sprite behaviors, simple movements, or when you need precise control.

```python
# Basic movement
move_action = MoveBy((100, 50), 1.0)
sprite.do(move_action)

# Rotation
rotate_action = RotateBy(360, 2.0)
sprite.do(rotate_action)

# Composite actions for complex behavior
complex_action = MoveBy((100, 0), 1.0) + RotateBy(180, 0.5) + FadeTo(0, 1.0)
sprite.do(complex_action)
```

### 3. SpriteGroup
**When to use:** For managing collections of sprites that need coordinated behavior.
**Key features:** Automatic GroupAction management, collision detection, group operations.

```python
from actions.group import SpriteGroup
from actions.interval import MoveBy

# Create a SpriteGroup
enemies = SpriteGroup()

# Add sprites to the group
for i in range(5):
    enemy = ActionSprite(":resources:images/enemy.png")
    enemy.center_x = 100 + i * 80
    enemy.center_y = 400
    enemies.append(enemy)

# Apply action to entire group (creates GroupAction automatically)
move_action = MoveBy((200, 0), 3.0)
enemies.do(move_action)  # All enemies move together

# Update in game loop (automatically updates GroupActions)
enemies.update(delta_time)
```

### 4. GroupAction
**When to use:** Automatically created by `SpriteGroup.do()`. You rarely create these directly.
**Key principle:** Coordinates the same action across multiple sprites.

```python
# GroupAction is created automatically
group_action = enemies.do(move_action)

# GroupAction manages individual actions for each sprite
assert len(group_action.actions) == len(enemies)

# Automatic cleanup when actions complete
# No manual tracking needed!
```

## Usage Patterns

### Pattern 1: Individual Sprite Control
**Use case:** Player character, single enemies, UI elements.

```python
class Player:
    def __init__(self):
        self.sprite = ActionSprite(":resources:images/player.png")
        self.sprite.center_x = 400
        self.sprite.center_y = 100
    
    def move_to(self, x, y):
        move_action = MoveTo((x, y), 1.0)
        self.sprite.do(move_action)
    
    def update(self, delta_time):
        self.sprite.update(delta_time)
```

### Pattern 2: Group Coordination
**Use case:** Enemy formations, bullet patterns, particle effects.

```python
class EnemyFormation:
    def __init__(self):
        self.enemies = SpriteGroup()
        self._setup_formation()
    
    def _setup_formation(self):
        # Create 3x5 grid of enemies
        for row in range(3):
            for col in range(5):
                enemy = ActionSprite(":resources:images/enemy.png")
                enemy.center_x = 200 + col * 80
                enemy.center_y = 500 - row * 60
                self.enemies.append(enemy)
    
    def move_formation(self, dx, dy, duration):
        move_action = MoveBy((dx, dy), duration)
        self.enemies.do(move_action)  # All enemies move together
    
    def update(self, delta_time):
        self.enemies.update(delta_time)  # Automatically updates GroupActions
```

### Pattern 3: Boundary Interactions with Groups
**Use case:** Space Invaders-style movement, bouncing formations.

```python
from actions.move import BoundedMove

class SpaceInvaders:
    def __init__(self):
        self.enemies = SpriteGroup()
        self._setup_enemies()
        self._setup_movement()
    
    def _setup_movement(self):
        # Define movement boundaries
        def get_bounds():
            return (50, 0, 750, 600)  # left, bottom, right, top
        
        # Callback for when edge enemies hit boundaries
        def on_bounce(sprite, axis):
            if axis == "x":
                # Move all enemies down using GroupAction
                move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
                self.enemies.do(move_down)
                
                # Clear current actions and start new movement
                self.enemies.clear_actions()
                self._start_new_movement()
        
        # Set up boundary detection (only edge sprites trigger callbacks)
        self.boundary_action = BoundedMove(get_bounds, on_bounce=on_bounce)
        self.boundary_action.target = self.enemies
        self.boundary_action.start()
        
        # Start initial movement
        self._start_new_movement()
    
    def _start_new_movement(self):
        # Move horizontally across screen
        move_action = MoveBy((400, 0), 4.0)
        self.enemies.do(move_action)
    
    def update(self, delta_time):
        self.enemies.update(delta_time)
        self.boundary_action.update(delta_time)
```

### Pattern 4: Collision Detection with Groups
**Use case:** Bullet vs enemy collisions, player vs powerup collisions.

```python
class CollisionSystem:
    def __init__(self):
        self.player_bullets = SpriteGroup()
        self.enemies = SpriteGroup()
        self.shields = SpriteGroup()
        
        # Set up collision handlers with method chaining
        self.player_bullets.on_collision_with(
            self.enemies, self._bullet_enemy_collision
        ).on_collision_with(
            self.shields, self._bullet_shield_collision
        )
    
    def _bullet_enemy_collision(self, bullet, hit_enemies):
        bullet.remove_from_sprite_lists()
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()
            # Add explosion effect, score, etc.
    
    def _bullet_shield_collision(self, bullet, hit_shields):
        bullet.remove_from_sprite_lists()
        for shield in hit_shields:
            shield.remove_from_sprite_lists()
    
    def update(self, delta_time):
        self.player_bullets.update(delta_time)
        self.enemies.update(delta_time)
        self.shields.update(delta_time)
        
        # Check collisions
        self.player_bullets.update_collisions()
```

### Pattern 5: Custom Collision Detection
**Use case:** Testing without OpenGL context, custom collision algorithms, performance optimization.

```python
from actions.protocols import BoundingBoxCollisionDetector, MockCollisionDetector

class TestableCollisionSystem:
    def __init__(self, use_mock_collisions=False):
        if use_mock_collisions:
            # For testing - full control over collision results
            collision_detector = MockCollisionDetector()
        else:
            # For testing without OpenGL - simple bounding box collision
            collision_detector = BoundingBoxCollisionDetector()
        
        # Inject collision detector into sprite groups
        self.player_bullets = SpriteGroup(collision_detector=collision_detector)
        self.enemies = SpriteGroup(collision_detector=collision_detector)
        
        if use_mock_collisions:
            # Pre-configure collision results for testing
            self._setup_mock_collisions(collision_detector)
        
        # Set up collision handlers
        self.player_bullets.on_collision_with(self.enemies, self._bullet_enemy_collision)
    
    def _setup_mock_collisions(self, mock_detector):
        """Configure mock collision results for testing."""
        # Example: bullet at (100, 100) collides with specific enemy
        bullet = ActionSprite(":resources:images/bullet.png", center_x=100, center_y=100)
        enemy = ActionSprite(":resources:images/enemy.png", center_x=100, center_y=100)
        mock_detector.set_collision_result(bullet, tuple([enemy]), [enemy])
    
    def _bullet_enemy_collision(self, bullet, hit_enemies):
        bullet.remove_from_sprite_lists()
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()
    
    def update(self, delta_time):
        self.player_bullets.update(delta_time)
        self.enemies.update(delta_time)
        self.player_bullets.update_collisions()
```

## Decision Matrix

| Scenario | Use | Reason |
|----------|-----|--------|
| Single sprite needs to move | `ActionSprite.do(action)` | Simple, direct control |
| Multiple sprites move together | `SpriteGroup.do(action)` | Automatic coordination |
| Sprites need different actions | Individual `ActionSprite.do()` calls | Different behaviors |
| Boundary detection for groups | `BoundedMove` + `SpriteGroup` | Edge detection + callbacks |
| Screen wrapping for groups | `WrappedMove` + `SpriteGroup` | Edge detection + callbacks |
| Collision detection | `SpriteGroup.on_collision_with()` | Efficient group collisions |
| Testing without OpenGL | `BoundingBoxCollisionDetector` | No OpenGL context needed |
| Controlled test collisions | `MockCollisionDetector` | Full control over collision results |
| Production collision detection | `ArcadeCollisionDetector` (default) | Uses Arcade's optimized collision |
| Complex sequences | Composite actions (`+`, `|`, `*`) | Declarative behavior |
| Organize sprites in formations | Formation patterns (`GridPattern`, etc.) | Structured positioning |
| Game-level group management | `AttackGroup` + patterns | Lifecycle + scheduling |
| Inspect group action progress | `GroupAction` (from `SpriteGroup.do()`) | Consistent action interface |

## Common Mistakes to Avoid

### ❌ Don't: Use regular arcade.Sprite with Actions
```python
# WRONG - arcade.Sprite doesn't support actions
sprite = arcade.Sprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # This will fail!
```

### ✅ Do: Use ActionSprite for all action-based sprites
```python
# CORRECT - ActionSprite supports actions
sprite = ActionSprite("image.png")
sprite.do(MoveBy((100, 0), 1.0))  # This works!
```

### ❌ Don't: Manually track GroupActions
```python
# WRONG - Manual tracking is error-prone
group_action = sprite_group.do(move_action)
# ... later in game loop ...
group_action.update(delta_time)  # Easy to forget!
```

### ✅ Do: Let SpriteGroup handle GroupActions automatically
```python
# CORRECT - Automatic management
sprite_group.do(move_action)
# ... later in game loop ...
sprite_group.update(delta_time)  # Automatically updates GroupActions
```

### ❌ Don't: Apply BoundedMove to individual sprites in a group
```python
# WRONG - Causes spacing issues
for sprite in sprite_group:
    bounce_action = BoundedMove(get_bounds)
    sprite.do(move_action | bounce_action)
```

### ✅ Do: Apply BoundedMove to the entire SpriteGroup
```python
# CORRECT - Proper edge detection and coordination
bounce_action = BoundedMove(get_bounds, on_bounce=handle_bounce)
bounce_action.target = sprite_group
bounce_action.start()
sprite_group.do(move_action)
```

### ❌ Don't: Apply WrappedMove to individual sprites in a group
```python
# WRONG - All sprites wrap individually, no coordination
for sprite in sprite_group:
    wrap_action = WrappedMove(get_bounds)
    sprite.do(move_action | wrap_action)
```

### ✅ Do: Apply WrappedMove to the entire SpriteGroup
```python
# CORRECT - Only edge sprites trigger wraps, enables coordination
wrap_action = WrappedMove(get_bounds, on_wrap=handle_wrap)
wrap_action.target = sprite_group
wrap_action.start()
sprite_group.do(move_action)
```

### ❌ Don't: Directly manipulate sprite positions in groups
```python
# WRONG - Direct position manipulation bypasses the action system
def on_bounce(sprite, axis):
    for enemy in enemies:
        enemy.center_y -= 30  # Direct manipulation!
```

### ✅ Do: Use GroupActions for coordinated positioning
```python
# CORRECT - Use MoveBy GroupAction for coordinated movement
def on_bounce(sprite, axis):
    move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
    enemies.do(move_down)  # GroupAction coordinates all sprites
```

## Advanced Group Management

### 5. GroupAction
**When to use:** You rarely create these directly - they're automatically created by `SpriteGroup.do()`.
**Key principle:** Provides batch optimization for movement actions and consistent interface with individual actions.

```python
from actions.group import SpriteGroup, GroupAction
from actions.interval import MoveBy

# GroupAction is created automatically
enemies = SpriteGroup([sprite1, sprite2, sprite3])
group_action = enemies.do(MoveBy((200, 0), 2.0))  # Returns GroupAction

# GroupAction implements the same interface as individual actions
assert not group_action.done  # Check completion status
group_action.pause()          # Pause all sprites in group
group_action.resume()         # Resume all sprites in group

# Batch optimization makes large groups efficient
large_group = SpriteGroup([create_sprite() for _ in range(100)])
large_group.do(MoveBy((50, 0), 1.0))  # Optimized for 100 sprites!
```

### 6. AttackGroup  
**When to use:** For complex game scenarios requiring lifecycle management, formations, and scheduled events.
**Key features:** Built on SpriteGroup with game-oriented additions.

```python
from actions.group import AttackGroup, SpriteGroup, GridPattern
from actions.interval import MoveBy

# Create an AttackGroup for complex enemy behavior
enemies = SpriteGroup([create_enemy() for _ in range(12)])
formation = AttackGroup(enemies, name="wave_1")

# Apply formation patterns
pattern = GridPattern(rows=3, cols=4, spacing_x=80, spacing_y=60)
pattern.apply(formation, start_x=200, start_y=400)

# Schedule delayed attacks
formation.schedule_attack(2.0, formation.do, MoveBy((100, -50), 1.5))
formation.schedule_attack(5.0, formation.do, MoveBy((-200, 0), 2.0))

# Handle breakaway scenarios
def create_breakaway():
    # Some sprites break away to form new attack pattern
    breakaway_sprites = list(formation.sprites)[:3]
    new_formation = formation.breakaway(breakaway_sprites)
    new_formation.do(MoveBy((0, -100), 1.0))

formation.schedule_attack(3.0, create_breakaway)

# Update in game loop (handles all scheduled events)
formation.update(delta_time)
```

### 7. Formation Patterns
**When to use:** For organizing sprites into recognizable formations.
**Key principle:** Separate positioning logic from movement logic.

```python
from actions.group import (
    LinePattern, GridPattern, CirclePattern, VFormationPattern,
    AttackGroup, SpriteGroup
)

# Line formation for horizontal arrangements
line_pattern = LinePattern(spacing=60.0)
line_formation = AttackGroup(SpriteGroup(bullets))
line_pattern.apply(line_formation, start_x=100, start_y=300)

# Grid formation for Space Invaders-style enemies
grid_pattern = GridPattern(rows=5, cols=8, spacing_x=50, spacing_y=40)
enemy_formation = AttackGroup(SpriteGroup(enemies))
grid_pattern.apply(enemy_formation, start_x=150, start_y=500)

# Circle formation for defensive patterns
circle_pattern = CirclePattern(radius=120.0)
shield_formation = AttackGroup(SpriteGroup(shields))
circle_pattern.apply(shield_formation, center_x=400, center_y=300)

# V formation for flying patterns
v_pattern = VFormationPattern(angle=30.0, spacing=50.0)
fighter_formation = AttackGroup(SpriteGroup(fighters))
v_pattern.apply(fighter_formation, apex_x=400, apex_y=500)

# Combine patterns with movement
grid_pattern.apply(enemy_formation, start_x=150, start_y=500)
enemy_formation.do(MoveBy((200, 0), 3.0))  # Move formation as unit
```

## Testing Patterns

### Testing Individual Actions
```python
def test_individual_action(self):
    sprite = ActionSprite(":resources:images/test.png")
    sprite.center_x = 0
    sprite.center_y = 0
    
    move_action = MoveBy((100, 0), 1.0)
    sprite.do(move_action)
    
    sprite.update(0.5)  # Half duration
    assert sprite.center_x == 50  # Halfway there
    
    sprite.update(0.5)  # Complete
    assert sprite.center_x == 100
    assert not sprite.is_busy()
```

### Testing Group Actions
```python
def test_group_action(self):
    sprite_group = SpriteGroup()
    for i in range(3):
        sprite = ActionSprite(":resources:images/test.png")
        sprite.center_x = i * 100
        sprite_group.append(sprite)
    
    move_action = MoveBy((50, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)  # Complete action
    
    # All sprites should have moved
    for i, sprite in enumerate(sprite_group):
        assert sprite.center_x == i * 100 + 50
```

### Testing Boundary Interactions
```python
def test_boundary_with_group(self):
    sprite_group = SpriteGroup()
    # ... setup sprites near boundary ...
    
    bounce_called = False
    def on_bounce(sprite, axis):
        nonlocal bounce_called
        bounce_called = True
    
    bounds = lambda: (0, 0, 800, 600)
    bounce_action = BoundedMove(bounds, on_bounce=on_bounce)
    bounce_action.target = sprite_group
    bounce_action.start()
    
    move_action = MoveBy((200, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)
    bounce_action.update(1.0)
    
    assert bounce_called
```

### Testing Wrapping Interactions
```python
def test_wrapping_with_group(self):
    sprite_group = SpriteGroup()
    # ... setup sprites near screen edge ...
    
    wrap_called = False
    def on_wrap(sprite, axis):
        nonlocal wrap_called
        wrap_called = True
    
    bounds = lambda: (800, 600)  # width, height
    wrap_action = WrappedMove(bounds, on_wrap=on_wrap)
    wrap_action.target = sprite_group
    wrap_action.start()
    
    move_action = MoveBy((200, 0), 1.0)
    sprite_group.do(move_action)
    
    sprite_group.update(1.0)
    wrap_action.update(1.0)
    
    assert wrap_called
```

### Testing Collision Detection
```python
def test_collision_with_mock_detector(self):
    # Use MockCollisionDetector for full control
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
    
    # Set up collision handler
    collisions_detected = []
    def on_collision(bullet, hit_enemies):
        collisions_detected.append((bullet, hit_enemies))
    
    bullets.on_collision_with(enemies, on_collision)
    bullets.update_collisions()
    
    # Verify mock detector was used
    assert len(collisions_detected) == 1
    assert collisions_detected[0][0] is bullet
    assert enemy in collisions_detected[0][1]

def test_collision_with_bounding_box_detector(self):
    # Use BoundingBoxCollisionDetector for testing without OpenGL
    bbox_detector = BoundingBoxCollisionDetector()
    bullets = SpriteGroup(collision_detector=bbox_detector)
    enemies = SpriteGroup()
    
    # Create overlapping sprites
    bullet = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    enemy = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    bullets.append(bullet)
    enemies.append(enemy)
    
    # Set up collision handler
    collisions_detected = []
    def on_collision(bullet, hit_enemies):
        collisions_detected.append((bullet, hit_enemies))
    
    bullets.on_collision_with(enemies, on_collision)
    bullets.update_collisions()
    
    # Should detect collision since sprites overlap
    assert len(collisions_detected) == 1

def test_collision_with_no_detector_specified(self):
    # Default behavior uses ArcadeCollisionDetector
    bullets = SpriteGroup()  # No collision_detector specified
    enemies = SpriteGroup()
    
    # Create overlapping sprites
    bullet = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    enemy = ActionSprite(":resources:images/test.png", center_x=100, center_y=100)
    bullets.append(bullet)
    enemies.append(enemy)
    
    # Set up collision handler
    collisions_detected = []
    def on_collision(bullet, hit_enemies):
        collisions_detected.append((bullet, hit_enemies))
    
    bullets.on_collision_with(enemies, on_collision)
    
    # This would use Arcade's collision detection (requires OpenGL context)
    # bullets.update_collisions()  # Comment out for CI/unit tests
```

### Testing AttackGroup and Patterns
```python
def test_attack_group_with_pattern(self):
    sprites = [ActionSprite(":resources:images/test.png") for _ in range(6)]
    sprite_group = SpriteGroup(sprites)
    formation = AttackGroup(sprite_group, name="test_formation")
    
    # Test pattern application
    pattern = GridPattern(rows=2, cols=3, spacing_x=50, spacing_y=40)
    pattern.apply(formation, start_x=100, start_y=200)
    
    # Verify positions
    assert sprites[0].center_x == 100  # First sprite
    assert sprites[0].center_y == 200
    assert sprites[1].center_x == 150  # Second sprite (one spacing over)
    assert sprites[3].center_y == 160  # Second row (one spacing down)
    
    # Test action application
    move_action = MoveBy((50, 0), 1.0)
    formation.do(move_action)
    
    formation.update(1.0)  # Complete action
    
    # All sprites should have moved
    assert sprites[0].center_x == 150  # Moved from 100
    assert sprites[1].center_x == 200  # Moved from 150

def test_group_action_batch_optimization(self):
    # Create large group to test batch optimization
    large_group = SpriteGroup()
    for i in range(50):
        sprite = ActionSprite(":resources:images/test.png")
        sprite.center_x = i * 10
        large_group.append(sprite)
    
    # Apply movement action
    move_action = MoveBy((100, 0), 2.0)
    group_action = large_group.do(move_action)
    
    # Verify GroupAction was created
    assert isinstance(group_action, GroupAction)
    assert group_action.sprite_count == 50
    
    # Update partway through
    large_group.update(1.0)  # Half duration
    
    # All sprites should be halfway to destination
    for i, sprite in enumerate(large_group):
        expected_x = i * 10 + 50  # Half of 100 pixel movement
        assert abs(sprite.center_x - expected_x) < 1.0  # Allow small floating point error
```

## Performance Considerations

1. **SpriteGroup vs SpriteList**: `SpriteGroup` extends `arcade.SpriteList`, so it has the same performance characteristics plus action management.

2. **GroupAction batch optimization**: Movement actions use batch processing for significant performance gains with large groups (50+ sprites).

3. **AttackGroup overhead**: Minimal additional overhead over SpriteGroup - mainly adds scheduling and lifecycle management.

4. **Formation patterns**: O(n) positioning operations - very fast even for large groups.

5. **Boundary detection**: Only edge sprites are checked, making it efficient for large groups.

6. **Collision detection**: Uses Arcade's optimized collision detection under the hood.

## Summary

- **ActionSprite**: The foundation - only sprites that can use actions
- **SpriteGroup**: For coordinated group behavior with automatic management
- **GroupAction**: Created automatically, handles action coordination with batch optimization
- **AttackGroup**: Game-level group management with lifecycle and scheduling
- **Formation Patterns**: Structured positioning (GridPattern, LinePattern, CirclePattern, VFormationPattern)
- **BoundedMove + SpriteGroup**: Perfect for Space Invaders-style movement
- **WrappedMove + SpriteGroup**: Perfect for asteroid field-style movement
- **Collision detection**: Built into SpriteGroup with method chaining

Follow these patterns and your ArcadeActions code will be clean, efficient, and maintainable!

## Runtime-checking-free patterns

A common temptation is to write:

```python
# ❌ old – forbidden
if isinstance(action, MovementAction):
    dx, dy = action.delta
```

Now you **call the capability method directly**:

```python
# ✅ new – always available
if action.get_movement_delta() != (0, 0):
    dx, dy = action.get_movement_delta()
```

Key conventions:

1. **Capability hooks on `Action`.**
   – `get_movement_delta()` returns `(dx, dy)` or `(0, 0)`.
   – `adjust_for_position_delta(delta)` lets decorators (e.g. `WrappedMove`) tell inner actions about teleports.
2. **Iteration helpers.**  Instead of `isinstance(target, arcade.SpriteList)`, call `for sprite in self._iter_target():` in custom actions.
3. **Group detection.**  Check for the structural attribute `_group_actions` instead of type-checking `SpriteGroup`.
4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 