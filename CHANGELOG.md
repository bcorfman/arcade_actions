# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of ArcadeActions library
- Complete port of Cocos2D Actions system to Arcade 3.x
- Time-based animation system with consistent behavior across frame rates
- Action types: Movement, Rotation, Scaling, Composite, and Timing actions
- Group actions for coordinating animations across multiple sprites
- Boundary handling and collision detection
- Game clock with pause/resume functionality
- Comprehensive test suite with 197+ tests
- Detailed documentation and API usage guide

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## [0.1.0] - 2024-01-XX

### Added
- Initial release of arcade-actions library
- Core ActionSprite class with time-based actions
- SpriteGroup with collision detection and group operations
- Complete action system including:
  - Movement actions: MoveBy, MoveTo, WrappedMove, BoundedMove
  - Rotation actions: RotateBy, RotateTo
  - Scaling actions: ScaleBy, ScaleTo
  - Composite actions: Sequence, Spawn, Loop
  - Instant actions: CallFunc, Hide, Show, Place, ToggleVisibility
- Game clock and scheduler with pause support
- Velocity conversion utilities for frame-based and time-based calculations
- Comprehensive documentation and examples
- Full test coverage 