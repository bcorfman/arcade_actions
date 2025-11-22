<!-- coverage-90-percent-plan -->

# Test Coverage Improvement Plan: 85% → 90%

**Current Status:** 85% coverage (4680 statements, 687 missing)

**Target:** ~90% coverage (4212+ statements covered, ~468 missing)

**Gap to Close:** ~219 statements

---

## Strategy Overview

Focus on the **top 10 critical missing areas** that will provide the highest impact for coverage improvement. Prioritize by:

1. **Lowest coverage percentage** (biggest gaps)
2. **Highest absolute missing statements** (most impact)
3. **Core functionality** (critical paths)

---

## Top 10 Critical Areas

### 1. **actions/axis_move.py** - 35% coverage, 68 missing statements ⚠️ CRITICAL

**Priority:** HIGHEST

**Impact:** +68 statements, ~1.5% overall coverage gain

**Missing Coverage:**

- Lines 86-90: `update_effect()` boundary handling path
- Lines 95-129: `_handle_x_boundaries()` - all boundary behaviors (bounce, wrap, limit) for left/right
- Lines 217-221: `update_effect()` boundary handling path  
- Lines 226-260: `_handle_y_boundaries()` - all boundary behaviors (bounce, wrap, limit) for top/bottom

**Test Plan:**

- [ ] Test `MoveXUntil.update_effect()` with bounds and boundary_behavior
- [ ] Test `MoveXUntil._handle_x_boundaries()` with bounce behavior (left and right boundaries)
- [ ] Test `MoveXUntil._handle_x_boundaries()` with wrap behavior (left and right boundaries)
- [ ] Test `MoveXUntil._handle_x_boundaries()` with limit behavior (left and right boundaries)
- [ ] Test `MoveXUntil._handle_x_boundaries()` with `on_boundary_enter` callbacks
- [ ] Test `MoveYUntil.update_effect()` with bounds and boundary_behavior
- [ ] Test `MoveYUntil._handle_y_boundaries()` with bounce behavior (top and bottom boundaries)
- [ ] Test `MoveYUntil._handle_y_boundaries()` with wrap behavior (top and bottom boundaries)
- [ ] Test `MoveYUntil._handle_y_boundaries()` with limit behavior (top and bottom boundaries)
- [ ] Test `MoveYUntil._handle_y_boundaries()` with `on_boundary_enter` callbacks
- [ ] Test boundary callbacks are called with correct (sprite, axis, side) parameters
- [ ] Test velocity_provider integration with boundary handling

**Files to Update:**

- `tests/test_axis_move.py` - Add comprehensive boundary behavior tests

**Estimated Coverage Gain:** +68 statements → **~1.5% overall**

---

### 2. **actions/visualizer/attach.py** - 67% coverage, 141 missing statements

**Priority:** HIGH

**Impact:** +141 statements, ~3.0% overall coverage gain (but visualizer is optional)

**Missing Coverage:**

- Lines 61, 67-69: Error handling paths
- Lines 96, 118-119: Edge cases in attachment logic
- Lines 168-169, 176-178: Conditional branches
- Lines 186, 200-218: Complex attachment scenarios
- Lines 221-222, 229-244: State management edge cases
- Lines 254-255, 258, 261: Callback handling
- Lines 271-296, 306-330: Advanced attachment features
- Lines 341-350, 364-367: Cleanup and teardown
- Lines 379, 458, 467-474: Integration paths
- Lines 480, 483, 497-510: Error recovery
- Lines 532, 588-592: Finalization logic

**Test Plan:**

- [ ] Test error handling when attaching to invalid targets
- [ ] Test attachment edge cases (already attached, multiple attachments)
- [ ] Test conditional branches in attachment logic
- [ ] Test complex attachment scenarios with multiple visualizers
- [ ] Test state management during attach/detach cycles
- [ ] Test callback handling during attachment lifecycle
- [ ] Test advanced attachment features (nested, chained)
- [ ] Test cleanup and teardown paths
- [ ] Test integration with different action types
- [ ] Test error recovery scenarios

**Files to Update:**

- `tests/test_visualizer_attach.py` - Expand coverage

**Estimated Coverage Gain:** +141 statements → **~3.0% overall** (but visualizer is optional, so actual impact may be lower)

---

### 3. **actions/visualizer/renderer.py** - 60% coverage, 117 missing statements

**Priority:** HIGH

**Impact:** +117 statements, ~2.5% overall coverage gain (but visualizer is optional)

**Missing Coverage:**

- Lines 49-50: Initialization edge cases
- Lines 229, 245-250: Rendering paths
- Lines 266-278, 281-358: Complex rendering scenarios
- Lines 367-385: State transitions
- Lines 419, 442-445: Error handling
- Lines 471, 484, 489: Conditional rendering
- Lines 499-500, 511, 514: Edge case rendering
- Lines 529-543, 557-571: Advanced rendering features

**Test Plan:**

- [ ] Test initialization edge cases
- [ ] Test all rendering paths (different action types, states)
- [ ] Test complex rendering scenarios (overlapping, nested)
- [ ] Test state transitions during rendering
- [ ] Test error handling in rendering pipeline
- [ ] Test conditional rendering branches
- [ ] Test edge case rendering (empty states, invalid data)
- [ ] Test advanced rendering features

**Files to Update:**

- `tests/test_visualizer_renderer.py` - Expand coverage

**Estimated Coverage Gain:** +117 statements → **~2.5% overall** (but visualizer is optional)

---

### 4. **actions/pattern.py** - 79% coverage, 111 missing statements

**Priority:** HIGH

**Impact:** +111 statements, ~2.4% overall coverage gain

**Missing Coverage:**

- Lines 70-71: Edge case in zigzag pattern calculation
- Line 294: Conditional branch
- Line 351: Error path
- Lines 375-377: Edge case handling
- Lines 395-452: Large block of missing coverage (likely pattern creation/validation)
- Line 456, 459: Conditional branches
- Line 497, 502-505: Pattern execution paths
- Line 543: Edge case
- Lines 592-609: Pattern state management
- Line 632, 651-655: Pattern completion logic
- Lines 695-696, 713: Error handling
- Lines 854-855, 879: Pattern validation
- Lines 927-960: Complex pattern scenarios
- Line 1028, 1036: Edge cases
- Line 1118, 1201, 1252: Finalization logic

**Test Plan:**

- [ ] Test edge cases in zigzag pattern calculation (seg_idx = segments - 1)
- [ ] Test conditional branches in pattern creation
- [ ] Test error paths (invalid parameters, edge cases)
- [ ] Test pattern creation/validation (lines 395-452)
- [ ] Test pattern execution paths with different conditions
- [ ] Test pattern state management during execution
- [ ] Test pattern completion logic
- [ ] Test error handling in pattern execution
- [ ] Test pattern validation edge cases
- [ ] Test complex pattern scenarios (nested, chained)
- [ ] Test finalization logic

**Files to Update:**

- `tests/test_pattern_smoke.py` - Expand to comprehensive tests
- Consider creating `tests/test_pattern.py` for full coverage

**Estimated Coverage Gain:** +111 statements → **~2.4% overall**

---

### 5. **actions/conditional.py** - 92% coverage, 88 missing statements

**Priority:** MEDIUM-HIGH

**Impact:** +88 statements, ~1.9% overall coverage gain

**Missing Coverage:**

- Lines 86, 99-100, 103: Edge cases in condition evaluation
- Lines 293-295, 301-303: Conditional branches
- Lines 319-321, 327-329: State transitions
- Lines 375, 393-395: Error handling
- Lines 409, 415-417: Edge cases
- Lines 480, 490, 496: Callback handling
- Lines 513, 520: Conditional paths
- Lines 545, 587, 596: State management
- Lines 619-640: Large block (likely complex conditional logic)
- Lines 718, 726: Edge cases
- Lines 892-893, 932: Error paths
- Lines 946, 967: Conditional branches
- Lines 1006-1007: Finalization
- Lines 1139, 1288, 1311: Edge cases
- Lines 1367, 1447, 1489, 1493: State transitions
- Lines 1502-1506, 1514: Conditional logic
- Lines 1538, 1556-1558: Error handling
- Lines 1623-1625, 1635-1636: Edge cases
- Lines 1705-1706: Finalization
- Lines 2035, 2037, 2039: Error paths

**Test Plan:**

- [ ] Test edge cases in condition evaluation
- [ ] Test conditional branches in action lifecycle
- [ ] Test state transitions (apply → update → complete)
- [ ] Test error handling paths
- [ ] Test callback handling edge cases
- [ ] Test complex conditional logic (lines 619-640)
- [ ] Test edge cases in action completion
- [ ] Test error paths in action execution
- [ ] Test finalization logic

**Files to Update:**

- `tests/test_conditional.py` - Add tests for missing lines
- `tests/test_conditional_coverage.py` - Expand coverage tests

**Estimated Coverage Gain:** +88 statements → **~1.9% overall**

---

### 6. **actions/display.py** - 74% coverage, 20 missing statements

**Priority:** MEDIUM

**Impact:** +20 statements, ~0.4% overall coverage gain

**Missing Coverage:**

- Line 58: SDL2 library path candidate handling
- Line 63: Windows platform path
- Line 65: macOS platform path
- Line 101: SDL_GetDisplayBounds success path
- Lines 110-113: SDL centering calculation
- Lines 138-152: `move_to_primary_monitor` implementation
- Line 202: `move_to_primary_monitor` fallback path

**Test Plan:**

- [ ] Test SDL2 library path candidates (Windows, macOS, Linux)
- [ ] Test SDL_GetDisplayBounds success path
- [ ] Test SDL centering calculation with valid rect
- [ ] Test `move_to_primary_monitor` with SDL2
- [ ] Test `move_to_primary_monitor` with screeninfo fallback
- [ ] Test `move_to_primary_monitor` boundary clamping

**Files to Update:**

- `tests/test_display.py` - Add tests for missing paths

**Estimated Coverage Gain:** +20 statements → **~0.4% overall**

---

### 7. **actions/easing.py** - 76% coverage, 11 missing statements

**Priority:** MEDIUM

**Impact:** +11 statements, ~0.2% overall coverage gain

**Missing Coverage:**

- Line 72: ValueError for frames <= 0
- Lines 82-84: Default ease_function assignment
- Line 107: Early return when easing complete
- Lines 131-134: `remove_effect()` implementation
- Lines 139-142: `stop()` implementation
- Line 149: `set_factor()` forwarding
- Line 153: `clone()` property access (easing_duration)
- Line 163: `__repr__()` formatting

**Test Plan:**

- [ ] Test ValueError when frames <= 0
- [ ] Test default ease_function assignment (arcade.easing.ease_in_out)
- [ ] Test early return when easing already complete
- [ ] Test `remove_effect()` callback deactivation
- [ ] Test `stop()` stops both wrapper and wrapped action
- [ ] Test `set_factor()` forwards to wrapped action
- [ ] Test `clone()` with all properties (fix property name if needed)
- [ ] Test `__repr__()` formatting

**Files to Update:**

- Create `tests/test_easing.py` (may not exist)
- Or update existing test file

**Estimated Coverage Gain:** +11 statements → **~0.2% overall**

---

### 8. **actions/base.py** - 91% coverage, 33 missing statements

**Priority:** MEDIUM

**Impact:** +33 statements, ~0.7% overall coverage gain

**Missing Coverage:**

- Lines 28-29: Import/initialization edge cases
- Line 195, 225: Conditional branches
- Lines 317-318: Error handling
- Lines 370-371: State transitions
- Lines 393-404: Complex logic block
- Line 440, 457: Edge cases
- Line 526, 605, 613: Conditional paths
- Lines 636, 642-648: Error handling
- Line 652, 692, 703: State management
- Lines 707-708: Finalization

**Test Plan:**

- [ ] Test import/initialization edge cases
- [ ] Test conditional branches in Action lifecycle
- [ ] Test error handling paths
- [ ] Test state transitions
- [ ] Test complex logic block (lines 393-404)
- [ ] Test edge cases in action management
- [ ] Test conditional paths in update logic
- [ ] Test error handling in action execution
- [ ] Test state management edge cases
- [ ] Test finalization logic

**Files to Update:**

- `tests/test_base.py` - Add tests for missing lines

**Estimated Coverage Gain:** +33 statements → **~0.7% overall**

---

### 9. **actions/composite.py** - 91% coverage, 16 missing statements

**Priority:** MEDIUM

**Impact:** +16 statements, ~0.3% overall coverage gain

**Missing Coverage:**

- Lines 50-51: Edge cases in composition
- Lines 56-58: Conditional branches
- Lines 103-105: Error handling
- Lines 149-150: State transitions
- Lines 236-237: Edge cases
- Lines 253-255: Conditional logic
- Lines 282-284: Finalization

**Test Plan:**

- [ ] Test edge cases in action composition
- [ ] Test conditional branches in parallel/sequence
- [ ] Test error handling in composite actions
- [ ] Test state transitions in composite lifecycle
- [ ] Test edge cases in composite execution
- [ ] Test conditional logic in composite completion
- [ ] Test finalization logic

**Files to Update:**

- `tests/test_composite.py` - Add tests for missing lines

**Estimated Coverage Gain:** +16 statements → **~0.3% overall**

---

### 10. **actions/formation.py** - 95% coverage, 20 missing statements

**Priority:** LOW-MEDIUM

**Impact:** +20 statements, ~0.4% overall coverage gain

**Missing Coverage:**

- Line 66: Edge case
- Lines 219, 307, 324, 329: Conditional branches
- Lines 462, 479, 503: State management
- Lines 526-527: Edge cases
- Lines 623, 761, 778: Error handling
- Lines 877, 883, 890: Conditional logic
- Lines 948, 986: State transitions
- Lines 1049, 1068: Finalization

**Test Plan:**

- [ ] Test edge cases in formation creation
- [ ] Test conditional branches in formation logic
- [ ] Test state management during formation execution
- [ ] Test error handling in formation operations
- [ ] Test conditional logic in formation completion
- [ ] Test state transitions in formation lifecycle
- [ ] Test finalization logic

**Files to Update:**

- `tests/test_formation.py` - Add tests for missing lines

**Estimated Coverage Gain:** +20 statements → **~0.4% overall**

---

## Implementation Priority

### Phase 1: Critical Core Functionality (Highest Impact)

1. **actions/axis_move.py** (+68 statements, ~1.5%) - Core movement functionality
2. **actions/pattern.py** (+111 statements, ~2.4%) - Core pattern system
3. **actions/conditional.py** (+88 statements, ~1.9%) - Core conditional actions

**Total Phase 1:** +267 statements → **~5.7% overall coverage gain**

### Phase 2: Supporting Functionality (Medium Impact)

4. **actions/base.py** (+33 statements, ~0.7%) - Base action system
5. **actions/composite.py** (+16 statements, ~0.3%) - Composite actions
6. **actions/display.py** (+20 statements, ~0.4%) - Display utilities
7. **actions/easing.py** (+11 statements, ~0.2%) - Easing wrapper
8. **actions/formation.py** (+20 statements, ~0.4%) - Formation system

**Total Phase 2:** +120 statements → **~2.6% overall coverage gain**

### Phase 3: Visualizer (Optional, Lower Priority)

9. **actions/visualizer/attach.py** (+141 statements, ~3.0%) - Visualizer attachment
10. **actions/visualizer/renderer.py** (+117 statements, ~2.5%) - Visualizer rendering

**Total Phase 3:** +258 statements → **~5.5% overall coverage gain** (but visualizer is optional)

---

## Recommended Approach

**Focus on Phases 1 & 2 first** to reach ~90% coverage on core functionality:

- **Phase 1 + Phase 2:** +387 statements → **~8.3% overall coverage gain**
- **Current:** 85% → **Target:** ~93% (exceeds goal)

**Phase 3 (Visualizer)** can be tackled separately if needed, but it's optional functionality and may not be critical for the 90% goal.

---

## Testing Guidelines

### For Each Area:

1. **Read the source code** to understand what's missing
2. **Identify edge cases** and error paths
3. **Write tests** following existing patterns in the test suite
4. **Use fixtures** from `conftest.py` where available
5. **Test boundary conditions** (empty inputs, None values, edge cases)
6. **Test error paths** (invalid inputs, exception handling)
7. **Test state transitions** (apply → update → complete)
8. **Test callbacks** (on_stop, on_boundary_enter, etc.)
9. **Verify cleanup** (Action.stop_all() in teardown)

### Test Structure:

```python
class TestFeatureName:
    """Test suite for FeatureName - comprehensive coverage."""
    
    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
    
    def test_feature_basic_usage(self):
        """Test basic feature usage."""
        # Arrange
        # Act
        # Assert
    
    def test_feature_edge_case(self):
        """Test edge case in feature."""
        # Test edge case
    
    def test_feature_error_handling(self):
        """Test error handling in feature."""
        # Test error path
```

---

## Success Metrics

- **Coverage Target:** 90%+ overall
- **Phase 1 Target:** 90%+ on core functionality (axis_move, pattern, conditional)
- **Phase 2 Target:** 90%+ on supporting functionality
- **Test Quality:** All new tests follow project patterns and are maintainable

---

## Next Steps

1. Start with **Phase 1, Area 1: actions/axis_move.py** (highest impact, most critical)
2. Work through Phase 1 systematically
3. Move to Phase 2 once Phase 1 is complete
4. Evaluate Phase 3 based on remaining coverage needs

---

## Notes

- Visualizer tests (Phase 3) are lower priority since visualizer is optional functionality
- Focus on core functionality first to ensure solid foundation
- Some missing lines may be defensive code or error paths that are hard to trigger - document these cases
- Use coverage reports to verify progress after each area is completed
