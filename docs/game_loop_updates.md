# Game Loop Updates and Action Timing

## Design Philosophy

The Actions system is inspired by Cocos2D's design philosophy, which separates game loop timing from action timing:

1. Game loop time (`delta_time`) represents actual elapsed time since last frame
2. Actions internally track total elapsed time and convert to normalized 0-1 space
3. This conversion happens in `update()` so that:
   * Individual actions only need to think in terms of "what position should I be at X% through the animation?"
   * The `update()` method handles all the "what portion of the duration has elapsed?" logic
   * Actions work correctly even if frame rates vary

This creates a clean separation of concerns:
* The game loop just tells actions "this much time has passed"
* The action's `update()` method converts that to "this is what percentage through the animation we are"
* The action's implementation just needs to know "at X% through, what state should I be in?"

## Basic Game Loop Implementation

Here's how to implement a basic game loop with actions:

```python
class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Game")
        self.active_actions: list[Action] = []
        self.sprite = arcade.Sprite(...)  # Your sprite setup
        
    def start_some_action(self):
        # Example of starting actions in response to an event
        action = MoveTo((100, 100), 2.0) + RotateBy(360, 1.0)
        action.target = self.sprite
        action.start()
        self.active_actions.append(action)

    def update(self, delta_time: float):  # Game loop, called every 1/60 sec
        # Update all active actions
        for action in self.active_actions[:]:  # Copy list since we'll modify it
            action.update(delta_time)
            if action.done:
                action.stop()
                self.active_actions.remove(action)
```

## Using ActionSprite

The `ActionSprite` class provides a cleaner approach by encapsulating action management:

```python
class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Game")
        self.sprite = ActionSprite(...)  # Uses the action-aware sprite class
        
    def start_some_action(self):
        action = MoveTo((100, 100), 2.0) + RotateBy(360, 1.0)
        self.sprite.do(action)  # Sprite handles tracking the action

    def update(self, delta_time: float):
        self.sprite.update(delta_time)  # Handles action updates internally
```

## Group Actions with SpriteGroup

`SpriteGroup` extends `arcade.SpriteList` and provides automatic GroupAction management for coordinated sprite behavior. Here's a Space Invaders style example:

```python
from actions.group import SpriteGroup
from actions.interval import MoveBy
from actions.move import BoundedMove

class Game(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Space Invaders Style")
        
        # Create SpriteGroup for enemies (extends SpriteList)
        self.enemies = SpriteGroup()
        
        # Create a grid of enemies
        for row in range(5):
            for col in range(10):
                enemy = ActionSprite("enemy.png", 0.5)
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 50
                self.enemies.append(enemy)
        
        # Set up coordinated movement pattern
        self.setup_enemy_movement()

    def setup_enemy_movement(self):
        # Define movement boundaries
        def get_bounds():
            return (50, 0, 750, 600)  # left, bottom, right, top
        
        # Callback for when edge enemies hit boundaries
        def on_bounce(sprite, axis):
            if axis == 'x':
                # Move ALL enemies down using GroupAction (Space Invaders behavior)
                move_down = MoveBy((0, -30), 0.1)  # Quick downward movement
                self.enemies.do(move_down)
                
                # Clear current actions and start new movement
                self.enemies.clear_actions()
                self.start_horizontal_movement()
        
        # Set up boundary detection for the entire group
        self.boundary_action = BoundedMove(get_bounds, on_bounce=on_bounce)
        self.boundary_action.target = self.enemies
        self.boundary_action.start()
        
        # Start initial movement
        self.start_horizontal_movement()
    
    def start_horizontal_movement(self):
        # Move horizontally across screen
        move_action = MoveBy((400, 0), 4.0)
        self.enemies.do(move_action)  # Creates GroupAction automatically

    def update(self, delta_time: float):
        # Update SpriteGroup (automatically updates GroupActions)
        self.enemies.update(delta_time)
        # Update boundary detection
        self.boundary_action.update(delta_time)

    def on_draw(self):
        self.clear()
        self.enemies.draw()
```

## Key Points

* `SpriteGroup` extends `SpriteList` with action management capabilities
* `enemies.do(action)` creates a `GroupAction` that coordinates all sprites
* `enemies.update()` automatically updates both sprites and GroupActions
* Only edge sprites trigger boundary callbacks for efficient group coordination
* `clear_actions()` stops all GroupActions and individual sprite actions
* Perfect for Space Invaders, Galaga, and other formation-flying patterns

## Adding Variety

You can add variety to group movements by:
* Using `Spawn` to combine movement with other actions (like rotation or scaling)
* Adding slight delays between rows using `RandomDelay`
* Creating different patterns for different rows
* Using `Sequence` to create complex movement patterns
* Combining different easing functions for varied movement styles