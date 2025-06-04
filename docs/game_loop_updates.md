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

## Group Actions with SpriteList

`ActionSprite` works seamlessly with Arcade's `SpriteList` for efficient group updates. Here's a Space Invaders style example:

```python
class Game(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Space Invaders Style")
        
        # Create sprite list for enemies
        self.enemies = arcade.SpriteList()
        
        # Create a grid of enemies
        for row in range(5):
            for col in range(10):
                enemy = ActionSprite("enemy.png", 0.5)
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 50
                self.enemies.append(enemy)
        
        # Create the marching movement pattern
        self.setup_enemy_movement()

    def setup_enemy_movement(self):
        # Create a sideways march + drop pattern
        march_right = MoveBy((100, 0), 2.0)
        march_left = MoveBy((-100, 0), 2.0)
        drop_down = MoveBy((0, -20), 0.5)
        
        # Combine into a repeating sequence
        movement = march_right + drop_down + march_left + drop_down
        repeated_movement = Repeat(movement)
        
        # Apply to all enemies
        for enemy in self.enemies:
            enemy.do(repeated_movement)

    def update(self, delta_time: float):
        # Update all sprites in the list
        self.enemies.update(delta_time)  # This calls update() on each sprite

    def on_draw(self):
        self.clear()
        self.enemies.draw()
```

## Key Points

* `SpriteList` handles calling `update()` on each sprite efficiently
* All enemies move in sync since they're started with the same action sequence
* The `Repeat` action keeps them moving indefinitely
* You get the benefit of the action system's timing and sequencing

## Adding Variety

You can add variety to group movements by:
* Using `Spawn` to combine movement with other actions (like rotation or scaling)
* Adding slight delays between rows using `RandomDelay`
* Creating different patterns for different rows
* Using `Sequence` to create complex movement patterns
* Combining different easing functions for varied movement styles