# Named Action Slots

The ArcadeActions library supports **named action slots**, allowing sprites to run multiple orthogonal actions simultaneously while maintaining full backward compatibility.

## Overview

ActionSprite supports both single actions and multiple named action slots. For simple cases, you can use a single action. For complex scenarios with multiple systems, you can use named slots where different game systems can independently control their own behaviors:

```python
# Different systems can work independently
sprite.do(movement_action, slot="ai_movement")      # AI system
sprite.do(damage_flash, slot="combat_effects")      # Combat system  
sprite.do(death_fade, slot="health_effects")        # Health system

# Each system can stop its own effects without affecting others
sprite.clear_action(slot="combat_effects")  # Stop just the damage flash
```

## Backward Compatibility

All single-action usage works exactly as expected:

```python
# Single action usage works perfectly
sprite.do(action)
sprite.clear_actions()
sprite.is_busy()
```

The default slot ("default") is used when no slot is specified, ensuring full compatibility.

## Basic Usage

### Single Actions
```python
sprite = ActionSprite(":resources:images/items/star.png")

# Single action usage
move_action = MoveBy((100, 0), 1.0)
sprite.do(move_action)
```

### Named Slots
```python
sprite = ActionSprite(":resources:images/items/star.png")

# Apply actions to different slots
move_action = MoveBy((100, 0), 2.0)
rotate_action = RotateBy(90, 1.5)

sprite.do(move_action, slot="movement")
sprite.do(rotate_action, slot="rotation")

# Both actions run simultaneously and independently
```

### Clearing Actions
```python
# Clear a specific slot
sprite.clear_action(slot="effects")

# Clear the default slot
sprite.clear_action()  # Same as sprite.clear_action(slot="default")

# Clear all actions in all slots
sprite.clear_actions()
```

## Advanced Examples

### Game Systems Integration
```python
class Player(ActionSprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def start_ai_movement(self, patrol_path):
        """AI system controls movement."""
        self.do(patrol_path, slot="ai_movement")
    
    def take_damage(self):
        """Combat system shows damage effect."""
        flash_effect = loop(sequence(Hide(), Delay(0.1), Show(), Delay(0.1)), 3)
        self.do(flash_effect, slot="combat_effects")
    
    def start_dying(self):
        """Health system handles death animation."""
        death_sequence = sequence(
            FadeTo(100, 1.0),
            ScaleBy(0.5, 0.5),
            FadeTo(0, 0.5)
        )
        self.do(death_sequence, slot="health_effects")
        
    def stop_damage_effect(self):
        """Combat system can stop just the damage effect."""
        self.clear_action(slot="combat_effects")
```

### Powerup Effects
```python
class PowerupSprite(ActionSprite):
    def start_floating(self):
        """Floating movement pattern."""
        float_action = loop(
            sequence(MoveBy((0, 20), 1.0), MoveBy((0, -20), 1.0)), 
            99
        )
        self.do(float_action, slot="movement")
    
    def start_pulsing(self):
        """Scale pulsing effect."""
        pulse_action = loop(
            sequence(ScaleBy(1.2, 0.5), ScaleBy(1/1.2, 0.5)),
            99
        )
        self.do(pulse_action, slot="effects")
    
    def start_spinning(self):
        """Rotation effect."""
        spin_action = loop(RotateBy(360, 2.0), 99)
        self.do(spin_action, slot="rotation")
```

## API Reference

### ActionSprite Methods

#### `do(action: Action, slot: str = "default") -> Action`
Start an action in the specified slot. If another action is running in that slot, it will be stopped first.

#### `clear_action(slot: str = "default") -> None`
Stop and clear the action in the specified slot.

#### `clear_actions() -> None`
Stop and clear all actions in all slots.

#### `has_active_actions() -> bool`
Return True if any action is currently running in any slot.

#### `is_busy() -> bool`
Return True if any action is currently running and not done.

#### `pause() -> None`
Pause all active actions in all slots.

#### `resume() -> None`
Resume all active actions in all slots.

### Properties

#### `_action: Action | None`
Property that accesses the "default" slot for compatibility.

#### `_actions: dict[str, Action | None]`
Dictionary of all action slots. Keys are slot names, values are Action instances or None.

## Best Practices

### Slot Naming Conventions
Use descriptive slot names that indicate which system owns them:

```python
# Good slot names
sprite.do(action, slot="ai_movement")
sprite.do(action, slot="combat_effects")
sprite.do(action, slot="health_effects")
sprite.do(action, slot="powerup_rotation")

# Avoid generic names when using multiple slots
sprite.do(action, slot="action1")  # Not descriptive
```

### System Boundaries
Each game system should only manage its own slots:

```python
class CombatSystem:
    def apply_damage_effect(self, sprite):
        # Combat system only touches "combat_effects" slot
        flash = loop(sequence(Hide(), Delay(0.1), Show(), Delay(0.1)), 3)
        sprite.do(flash, slot="combat_effects")
    
    def clear_damage_effect(self, sprite):
        sprite.clear_action(slot="combat_effects")

class AISystem:
    def set_movement_pattern(self, sprite, pattern):
        # AI system only touches "ai_movement" slot
        sprite.do(pattern, slot="ai_movement")
    
    def stop_movement(self, sprite):
        sprite.clear_action(slot="ai_movement")
```

### When to Use Slots vs Composites

**Use named slots when:**
- Different systems need independent control
- You need to start/stop behaviors independently
- Actions have different lifetimes
- Systems are developed separately

**Use composite actions when:**
- Behaviors are tightly coupled
- All effects should start/stop together
- You have a single, coordinated behavior

```python
# Use slots for independent systems
sprite.do(ai_movement, slot="movement")
sprite.do(damage_flash, slot="effects")

# Use composites for coordinated behaviors  
coordinated_effect = spawn(
    sequence(MoveBy((50, 0), 1.0), MoveBy((-50, 0), 1.0)),
    sequence(FadeOut(0.5), FadeIn(0.5))
)
sprite.do(coordinated_effect)
```

## Usage Patterns

Single action usage requires no changes:

```python
sprite.do(MoveBy((100, 0), 1.0))
sprite.update(delta_time)
sprite.clear_actions()
```

For multiple systems, use named slots:

```python
# Multiple independent actions
sprite.do(movement_action, slot="movement")
sprite.do(effect_action, slot="effects")
```

## Performance Notes

- Named slots have minimal overhead
- Compatibility is achieved through a property, not runtime checks
- Action updates scale linearly with the number of active slots
- Memory usage increases slightly due to the slots dictionary
