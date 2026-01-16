Scope: core ArcadeActions implementation.

Before new actions:
- Ask in order: existing action? existing composition? callback/condition? only then new class.

Velocity and movement:
- Velocity is pixels per frame at 60 FPS (not per second).
- MoveUntil uses sprite.change_x/change_y only; never sprite.velocity.

Do-not-change / usage:
- Do not change `infinite()` in `actions/conditional.py` (implementation stays `return False`).
- When using it, reference `infinite` and do not call `infinite()`; see `examples/space_clutter.py`.

Debug logging:
- Use the debug system with levels and filters (`set_debug_options`, `observe_actions`, ARCADEACTIONS_DEBUG*).
