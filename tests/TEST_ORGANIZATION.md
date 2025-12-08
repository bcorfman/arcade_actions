# Test Organization: Unit vs Integration Tests

## Summary

The hot-reload and file watcher tests have been reorganized to separate **fast unit tests** from **slow integration tests**.

## Performance Improvement

**Before:**
- File watcher + reload manager tests: ~8-10 seconds
- Many `time.sleep()` calls waiting for file system events

**After:**
- **Unit tests**: 0.85 seconds (53 tests) ⚡
- **Integration tests**: 9 seconds (12 tests) 🐢

**Result:** Unit tests run ~10x faster, improving developer workflow during TDD.

## Directory Structure

```
tests/
├── test_file_watcher.py              # 8 fast unit tests
├── test_reload_manager.py            # 45 fast unit tests
└── integration/
    ├── test_file_watcher_integration.py     # 9 slow integration tests
    └── test_reload_manager_integration.py   # 3 slow integration tests
```

## What Makes a Test "Integration"?

Tests were moved to `tests/integration/` if they:

1. **Wait for real file system events** (0.2-1.0 seconds per test)
2. **Use background threads/timing** (watchdog observer, debouncing)
3. **Perform real I/O operations** (writing files, waiting for changes)
4. **Depend on OS-level behavior** (file system watchers, event delivery)

## Unit Tests (tests/)

These tests are **fast** and test behavior in isolation:

- Constructor/configuration validation
- State preservation logic
- Path-to-module-name conversion
- Queue operations (thread-safe)
- Callback mechanism (without actual file I/O)
- Module reload logic (without watching)
- Context manager protocol
- Indicator flash animations

**Characteristics:**
- No `time.sleep()` calls (except tiny ones for thread safety)
- No waiting for file system events
- Mock-free (prefer real objects with DI)
- Run in < 1 second total

## Integration Tests (tests/integration/)

These tests are **slow** and test end-to-end behavior:

- File change detection with real file writes
- Debouncing multiple rapid changes
- Pattern filtering (*.py vs *.txt)
- Recursive subdirectory watching
- Race condition handling during callbacks
- Full reload workflow (watch → detect → reload → reconstruct)
- Auto-reload vs manual reload modes

**Characteristics:**
- Multiple `time.sleep()` calls (0.2-1.0s each)
- Real file I/O (write, modify, delete)
- Background threads (watchdog observer)
- OS-specific behavior (event timing)
- Run in ~9 seconds total

## Running Tests

### Fast feedback loop (TDD):
```bash
# Run only fast unit tests
uv run pytest tests/test_file_watcher.py tests/test_reload_manager.py
# Result: 53 tests in 0.85 seconds
```

### Full validation:
```bash
# Run all tests including integration
uv run pytest tests/ tests/integration/
```

### Integration tests only:
```bash
# Run slow integration tests (e.g., on CI)
uv run pytest tests/integration/test_file_watcher_integration.py
uv run pytest tests/integration/test_reload_manager_integration.py
```

## CI/CD Strategy

**Recommended approach:**

1. **Pull Request checks**: Run unit tests only (fast feedback)
2. **Merge to main**: Run full test suite including integration
3. **Nightly builds**: Run integration tests with extended timeouts

This ensures:
- Developers get instant feedback during TDD
- Integration tests still run, but don't slow down the development loop
- CI catches integration issues before merge

## Test Coverage

**Unit tests** provide the majority of code coverage:
- State preservation: 100%
- Module reloading: 100%
- Path conversion: 100%
- Queue operations: 100%
- Callback handling: 100%

**Integration tests** validate real-world scenarios:
- File watching with debouncing
- Race conditions during reload
- OS-specific event delivery
- Full hot-reload workflow

Combined, these tests maintain **high coverage** while optimizing for **fast local development**.

