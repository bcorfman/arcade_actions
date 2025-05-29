# Testing Documentation Index

## Overview

This document serves as an index for all testing-related documentation in the ArcadeActions framework.

## Documentation Structure

1. **Project Requirements Document (prd.md)**
   - High-level testing requirements
   - Basic test patterns
   - Coverage requirements
   - ActionSprite usage requirements
   - References to detailed testing documentation

2. **General Testing Guide (testing.md)**
   - Comprehensive test patterns
   - Common test fixtures
   - Test organization
   - Documentation requirements
   - ActionSprite lifecycle management
   - General best practices
   - Test categories
   - Property update testing

3. **Movement Action Testing Guide (testing_movement.md)**
   - Specialized testing for movement actions
   - Boundary condition testing
   - Physics integration testing
   - State management testing
   - Movement-specific test categories
   - Movement-specific best practices
   - References to general testing patterns

## How to Use This Documentation

1. Start with prd.md for high-level testing requirements
2. Use testing.md for general testing patterns and best practices
3. Refer to testing_movement.md when working with movement actions
4. Follow the ActionSprite lifecycle patterns in all tests

## Testing Requirements

All tests must:
- Follow the patterns in testing.md
- Meet coverage requirements in prd.md
- Use appropriate specialized guides for specific action types
- Include proper documentation and comments
- Use ActionSprite for all sprite-based tests
- Use sprite.do(action) and sprite.update() for action lifecycle

## Adding New Tests

When adding new tests:
1. Review prd.md for high-level requirements
2. Follow patterns in testing.md
3. Use specialized guides (e.g., testing_movement.md) for specific action types
4. Ensure proper documentation and coverage
5. Use ActionSprite for all sprite-based tests
6. Use sprite.do(action) and sprite.update() for action lifecycle 