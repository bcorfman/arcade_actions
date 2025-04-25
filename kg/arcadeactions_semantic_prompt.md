# ArcadeActions: Semantic Use Map
This reference helps guide large language models in choosing the correct Action class for a given sprite behavior.

## `AccelDecel`
**Purpose:** Apply easing effect for acceleration and deceleration
**When to use:** Use when smooth start and stop is desired
**Example:** `sprite.do(AccelDecel(action))`

## `Accelerate`
**Purpose:** Accelerate the timing of another action using a power curve
**When to use:** Use for actions that start slow and speed up
**Example:** `sprite.do(Accelerate(action, rate=2))`

## `Bezier`
**Purpose:** Move a sprite along a curved path defined by control points
**When to use:** Use for arcs, swooping paths, or organic motion
**Example:** `sprite.do(Bezier([p0, p1, p2, p3], duration=2.0))`

## `Blink`
**Purpose:** Toggle visibility repeatedly during duration
**When to use:** Use for blinking or warning animations
**Example:** `sprite.do(Blink(times=5, duration=1.0))`

## `BoundedMove`
**Purpose:** Move the sprite but constrain it within a rectangle
**When to use:** Use for bounce-limited or paddle movement
**Example:** `sprite.do(BoundedMove(bounds))`

## `CallFunc`
**Purpose:** Call a function with no arguments
**When to use:** Use to trigger an event or callback during an action sequence
**Example:** `sprite.do(CallFunc(my_function))`

## `CallFuncS`
**Purpose:** Call a function with the sprite as the first argument
**When to use:** Use when the callback needs access to the acting sprite
**Example:** `sprite.do(CallFuncS(print_sprite))`

## `Delay`
**Purpose:** Wait for a given amount of time before continuing
**When to use:** Use to pause between actions or animations
**Example:** `sprite.do(Delay(1.0))`

## `FadeIn`
**Purpose:** Fade the sprite in to full alpha
**When to use:** Use for spawning, reappearing, or unghosting effects
**Example:** `sprite.do(FadeIn(1.0))`

## `FadeOut`
**Purpose:** Fade the sprite out to zero alpha
**When to use:** Use for death, vanish, or dissolve effects
**Example:** `sprite.do(FadeOut(1.0))`

## `FadeTo`
**Purpose:** Fade the sprite to a target alpha value
**When to use:** Use for partial transparency changes
**Example:** `sprite.do(FadeTo(alpha=128, duration=2.0))`

## `Hide`
**Purpose:** Immediately hide the sprite
**When to use:** Use to disappear without fading
**Example:** `sprite.do(Hide())`

## `JumpBy`
**Purpose:** Move in a parabolic arc repeatedly
**When to use:** Use for character jumping, hopping, or bouncing
**Example:** `sprite.do(JumpBy((100, 0), height=30, jumps=2, duration=1.0))`

## `JumpTo`
**Purpose:** Jump to a target position in a parabolic arc
**When to use:** Use for jumping to a precise location
**Example:** `sprite.do(JumpTo((x, y), height=40, jumps=1, duration=1.0))`

## `Lerp`
**Purpose:** Linearly interpolate an attribute from start to end
**When to use:** Use for simple transitions on arbitrary properties
**Example:** `sprite.do(Lerp('scale', 0.5, 1.5, 1.0))`

## `Loop`
**Purpose:** Repeat an action a fixed number of times
**When to use:** Use for repeating sequences
**Example:** `sprite.do(Loop(action, times=3))`

## `Move`
**Purpose:** Move using velocity, acceleration, gravity and rotation
**When to use:** Use for physics-based motion with acceleration or drift
**Example:** `sprite.do(Move())`

## `MoveBy`
**Purpose:** Move the sprite by a delta over time
**When to use:** Use for relative movement such as walking or scrolling
**Example:** `sprite.do(MoveBy((100, 0), 1.0))`

## `MoveTo`
**Purpose:** Move the sprite to an absolute position
**When to use:** Use for teleportation-style or guided movement
**Example:** `sprite.do(MoveTo((x, y), 1.0))`

## `Place`
**Purpose:** Teleport the sprite to a location instantly
**When to use:** Use for starting position or warping
**Example:** `sprite.do(Place((x, y)))`

## `RandomDelay`
**Purpose:** Wait a random amount of time in a range
**When to use:** Use to create unpredictable delays or idle time
**Example:** `sprite.do(RandomDelay(0.5, 2.0))`

## `Repeat`
**Purpose:** Repeat an action indefinitely
**When to use:** Use for ongoing behavior or looping animation
**Example:** `sprite.do(Repeat(action))`

## `ReversedMove`
**Purpose:** Reverse sprite direction when it hits boundaries
**When to use:** Use for back-and-forth patrol or ricochet
**Example:** `sprite.do(ReversedMove(bounds))`

## `RotateBy`
**Purpose:** Rotate sprite by a relative angle
**When to use:** Use for spin or rotate animations
**Example:** `sprite.do(RotateBy(180, 2.0))`

## `RotateTo`
**Purpose:** Rotate sprite to an absolute angle
**When to use:** Use to aim or orient toward a direction
**Example:** `sprite.do(RotateTo(90, 1.0))`

## `ScaleBy`
**Purpose:** Scale the sprite by a multiplicative factor
**When to use:** Use to shrink or grow proportionally
**Example:** `sprite.do(ScaleBy(2.0, 1.0))`

## `ScaleTo`
**Purpose:** Scale the sprite to an absolute size
**When to use:** Use for grow/shrink to fixed size
**Example:** `sprite.do(ScaleTo(1.0, 1.0))`

## `Sequence`
**Purpose:** Run multiple actions in order, one after the next
**When to use:** Use for animation or logic sequences
**Example:** `sprite.do(action1 + action2 + action3)`

## `Show`
**Purpose:** Immediately show the sprite (if hidden)
**When to use:** Use to reappear from hiding
**Example:** `sprite.do(Show())`

## `SimpleMove`
**Purpose:** Custom example: move in one direction and back
**When to use:** Use for bouncing or patrol effects (demo only)
**Example:** `sprite.do(SimpleMove(100, 0, 2.0))`

## `Spawn`
**Purpose:** Run multiple actions in parallel
**When to use:** Use for simultaneous animations (e.g. move + fade)
**Example:** `sprite.do(action1 | action2)`

## `Speed`
**Purpose:** Modify the speed of an action
**When to use:** Use to slow down or speed up an animation
**Example:** `sprite.do(Speed(action, 2.0))`

## `ToggleVisibility`
**Purpose:** Toggle visibility state of the sprite
**When to use:** Use for flicker or hide/show toggles
**Example:** `sprite.do(ToggleVisibility())`

## `WrappedMove`
**Purpose:** Wrap sprite around screen edges
**When to use:** Use for toroidal maps or Asteroids-style movement
**Example:** `sprite.do(WrappedMove(width, height))`
