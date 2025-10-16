<!-- e45c36f9-9f5d-48f2-95d3-5ad5574b9bb4 362fe31a-1e4e-4f4a-ba94-a337ee86f97d -->
# Implement AttackGroup, Group Boundary Coordinator, EmitUntil, and Seek/Steer Helper (Test-First)

## Scope and principles

- Test-first workflow: author failing unit tests first, then implement code to satisfy them, refactor, and document.
- Follow DI/testability rules: accept dependencies via constructors; avoid static singletons; utilities only for pure helpers.
- Prefer composition; add new classes only for ergonomics (AttackGroup, EmitUntil). Group boundary coordinator as a small helper.
- Velocity semantics: pixels/frame at 60 FPS using `sprite.change_x/change_y`.
- Use `infinite` for non-terminating conditions; avoid boolean state flags.

## Workflow (test-first)

1. Write unit tests for each feature with clear behavior specs and mocked deps.
2. Run tests (expect failures).
3. Implement minimal code to pass tests.
4. Refactor for clarity while keeping tests green.
5. Add docs and small examples.

## Files to add/update (tests first)

- Add tests:
  - `tests/test_attack_group.py`
  - `tests/test_group_boundaries.py`
  - `tests/test_emit_until.py`
  - `tests/test_seek_helper.py`
- Add code:
  - `actions/attack_group.py`
  - `actions/group_boundaries.py`
  - `actions/emit.py`
  - Update `actions/helpers.py` (seek/emit helpers)
  - Update `actions/__init__.py` (exports)
- Update docs: `docs/api_usage_guide.md`, `docs/testing_guide.md`

## Test designs (concise behavior specs)

### AttackGroup tests (tests/test_attack_group.py)

- arrange uses provided formation function to position sprites deterministically.
- start applies a composed `Action` to the `SpriteList` with optional `tag`.
- start_for_each invokes factory per sprite; each action is applied to that sprite with `tag`.
- stop(tag) stops only actions with that tag for group members.
- on_update delegates coordinator.update() and does not directly call `Action.update_all()`.
- Boundary wiring: when coordinator raises a boundary event, `on_boundary_hit(axis, side)` is called exactly once per frame.

### GroupBoundaryCoordinator tests (tests/test_group_boundaries.py)

- Detects left/right hits when moving along X; top/bottom when moving along Y.
- Only checks boundary in current movement direction (compare current bbox with previous).
- Emits at most one enter event per axis per frame; fires exit on leaving.
- Respects `threshold` to ignore jitter; does not fire when stationary.

### EmitUntil tests (tests/test_emit_until.py)

- Emits on fixed cadence using mocked `time_source` (e.g., every 0.2s).
- Stops after `condition` becomes truthy; does not emit further.
- Uses `SpritePool` when provided (allocates none; `pool.acquire()` called).
- Calls `on_emit` with the created/acquired sprite each time.
- Helper `emit_until(...)` applies the action to target and returns the instance.

### Seek helper tests (tests/test_seek_helper.py)

- Produces velocity vectors that point toward `get_target_position()` at given `speed`.
- If `max_turn_degrees_per_frame` set, heading change is clamped per frame.
- If `arrive_radius` set, speed scales down within radius and reaches near-zero at the target.
- Works for both single `Sprite` and `SpriteList`.
- Composes via `MoveUntil` with `velocity_provider` (no direct velocity assignment outside action).

## API designs (kept concise)

### AttackGroup (actions/attack_group.py)

```python
class AttackGroup:
    def __init__(
        self,
        sprites: arcade.SpriteList,
        *,
        bounds_provider: Callable[[], tuple[float, float, float, float]] | None = None,
        boundary_coordinator: GroupBoundaryCoordinator | None = None,
        time_source: Callable[[], float] = time_elapsed,
        logger: Callable[[str], None] | None = None,
    ): ...
    def arrange(self, formation_fn: Callable, /, **kwargs) -> arcade.SpriteList: ...
    def start(self, action: Action, *, tag: str | None = None) -> None: ...
    def start_for_each(self, action_factory: Callable[[arcade.Sprite], Action], *, tag: str | None = None) -> None: ...
    def stop(self, *, tag: str | None = None) -> None: ...
    def on_update(self, dt: float) -> None: ...
    def on_boundary_hit(self, axis: str, side: str) -> None: ...
```

### GroupBoundaryCoordinator (actions/group_boundaries.py)

```python
class GroupBoundaryCoordinator:
    def __init__(
        self,
        sprites: arcade.SpriteList,
        *,
        bounds: tuple[float, float, float, float],
        on_enter: Callable[[str, str], None] | None = None,
        on_exit: Callable[[str, str], None] | None = None,
        threshold: float = 0.1,
    ): ...
    def update(self) -> None: ...
```

### EmitUntil (actions/emit.py)

```python
class EmitUntil(Action):
    def __init__(
        self,
        *,
        seconds_between_emits: float,
        condition: Callable[[], Any],
        emitter: arcade.Sprite | arcade.SpriteList,
        create_entity: Callable[[arcade.Sprite], arcade.Sprite],
        pool: SpritePool | None = None,
        on_emit: Callable[[arcade.Sprite], None] | None = None,
        time_source: Callable[[], float] = time_elapsed,
        tag: str | None = None,
    ): ...
```

Helper sugar (in helpers):

```python
def emit_until(target, *, seconds_between_emits, condition, create_entity, pool=None, on_emit=None, tag=None) -> EmitUntil: ...
```

### Seek/Steer helper (helpers)

```python
def seek_until(
    target: arcade.Sprite | arcade.SpriteList,
    *,
    get_target_position: Callable[[], tuple[float, float]],
    speed: float,
    condition: Callable[[], Any] = infinite,
    max_turn_degrees_per_frame: float | None = None,
    arrive_radius: float | None = None,
    tag: str | None = None,
) -> MoveUntil: ...
```

## Docs and examples (post-implementation)

- API Guide: add sections with minimal, runnable snippets for each feature.
- Examples: `examples/attack_group_demo.py`, `examples/emit_seek_demo.py`.
- Debugging: `set_debug_options(level=2, include=["EmitUntil","AttackGroup"])`.

### To-dos

- [ ] Implement AttackGroup orchestrator with DI and arrangement utilities
- [ ] Add GroupBoundaryCoordinator for SpriteList leading-edge boundary events
- [ ] Create EmitUntil Action and emit_until helper sugar
- [ ] Add seek_until helper using MoveUntil with velocity_provider
- [ ] Export new APIs in actions/__init__.py
- [ ] Add unit tests for all new components
- [ ] Update API and testing guides with new features
- [ ] Add examples for group orchestration, emitting, and seeking